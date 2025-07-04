# ---------------------------------------------------
# File Name: db.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# ---------------------------------------------------

from devgagan.core.mongo import client  # or wherever your MongoDB client is defined
from config import MONGO_DB
from motor.motor_asyncio import AsyncIOMotorClient as MongoCli
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import re
import os
import asyncio
import string
import random

# ✅ Use your actual database name
db = client.user_data  # or client.users

# ✅ Collection where sessions will be saved
sessions_collection = db.sessions  # You can rename this based on what Compass shows

# ✅ Function to save session
async def set_session(user_id, string_session):
    await sessions_collection.update_one(
        {"user_id": user_id},
        {"$set": {"string_session": string_session}},
        upsert=True
    )

mongo = MongoCli(MONGO_DB)
db = mongo.user_data.users_data_db

app = Client("my_bot")

VIDEO_EXTENSIONS = {
    'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm',
    'mpeg', 'mpg', '3gp'
}
SET_PIC = 'settings.jpg'
MESS = 'Customize settings for your files...'

active_conversations = {}

async def get_data(user_id):
    return await db.find_one({"_id": user_id})

async def save_user_data(user_id, key, value):
    await db.update_one(
        {"_id": user_id},
        {"$set": {key: value}},
        upsert=True
    )

async def get_user_data_key(user_id, key, default=None):
    data = await get_data(user_id)
    return data.get(key, default) if data else default

@app.on_message(filters.command("settings"))
async def settings_command(client, message):
    user_id = message.from_user.id
    buttons = [
        [
            InlineKeyboardButton('📝 Set Chat ID', callback_data='setchat'),
            InlineKeyboardButton('🏷️ Set Rename Tag', callback_data='setrename')
        ],
        [
            InlineKeyboardButton('📋 Set Caption', callback_data='setcaption'),
            InlineKeyboardButton('🔄 Replace Words', callback_data='setreplacement')
        ],
        [
            InlineKeyboardButton('🗑️ Remove Words', callback_data='delete'),
            InlineKeyboardButton('🔄 Reset Settings', callback_data='reset')
        ],
        [
            InlineKeyboardButton('🔑 Session Login', callback_data='addsession'),
            InlineKeyboardButton('🚪 Logout', callback_data='logout')
        ],
        [
            InlineKeyboardButton('🖼️ Set Thumbnail', callback_data='setthumb'),
            InlineKeyboardButton('❌ Remove Thumbnail', callback_data='remthumb')
        ]
    ]
    await message.reply_text(MESS, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    user_id = callback_query.from_user.id
    
    callback_actions = {
        'setchat': {
            'message': """Send me the ID of that chat(with -100 prefix): 
__👉 **Note:** if you are using custom bot then your bot should be admin that chat if not then this bot should be admin.__
👉 __If you want to upload in topic group and in specific topic then pass chat id as **-100CHANNELID/TOPIC_ID** for example: **-1004783898/12**__"""
        },
        'setrename': {
            'message': 'Send me the rename tag:'
        },
        'setcaption': {
            'message': 'Send me the caption:'
        },
        'setreplacement': {
            'message': "Send me the replacement words in the format: 'WORD(s)' 'REPLACEWORD'"
        },
        'addsession': {
            'message': 'Send Pyrogram V2 session string:'
        },
        'delete': {
            'message': 'Send words separated by space to delete them from caption/filename...'
        },
        'setthumb': {
            'message': 'Please send the photo you want to set as the thumbnail.'
        }
    }
    
    action = callback_query.data
    if action in callback_actions:
        await callback_query.message.edit_text(f"{callback_actions[action]['message']}\n\n(Send /cancel to cancel this operation)")
        active_conversations[user_id] = action
    elif action == 'logout':
        result = await db.update_one(
            {'_id': user_id},
            {'$unset': {'session': ''}}
        )
        await callback_query.answer('Logged out successfully' if result.modified_count > 0 else 'No session found')
    elif action == 'reset':
        try:
            await db.update_one(
                {'_id': user_id},
                {'$unset': {
                    'clean_words': '',
                    'replace_txt': '',
                    'to_replace': '',
                    'rename_tag': '',
                    'caption': '',
                    'chat_id': ''
                }}
            )
            thumbnail_path = f'{user_id}.jpg'
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            await callback_query.answer('✅ All settings reset successfully')
        except Exception as e:
            await callback_query.answer(f'Error: {e}')
    elif action == 'remthumb':
        try:
            os.remove(f'{user_id}.jpg')
            await callback_query.answer('Thumbnail removed successfully!')
        except FileNotFoundError:
            await callback_query.answer('No thumbnail found')

@app.on_message(filters.command("cancel"))
async def cancel_conversation(client, message):
    user_id = message.from_user.id
    if user_id in active_conversations:
        del active_conversations[user_id]
    await message.reply_text('Operation cancelled')

# Fixed filter syntax - properly handles non-command messages
@app.on_message(
    filters.private & 
    filters.text & 
    ~filters.command(["settings", "cancel"])  # Explicitly exclude commands
)
async def handle_conversation_input(client, message):
    user_id = message.from_user.id
    if user_id not in active_conversations:
        return
        
    conv_type = active_conversations[user_id]
    
    handlers = {
        'setchat': handle_setchat,
        'setrename': handle_setrename,
        'setcaption': handle_setcaption,
        'setreplacement': handle_setreplacement,
        'addsession': handle_addsession,
        'delete': handle_deleteword,
        'setthumb': handle_setthumb
    }
    
    if conv_type in handlers:
        await handlers[conv_type](client, message, user_id)
    
    if user_id in active_conversations:
        del active_conversations[user_id]

async def handle_setchat(client, message, user_id):
    try:
        chat_input = message.text.strip()
        raw_id = chat_input.split('/')[0]

        try:
            # 👉 Support both @usernames and numeric IDs like -1001234567890
            if raw_id.lstrip("-").isdigit():
                chat = await app.get_chat(int(raw_id))
            else:
                if not raw_id.startswith("@"):
                    raw_id = "@" + raw_id
                chat = await app.get_chat(raw_id)

            # ✅ Ensure the bot is an admin
            member = await app.get_chat_member(chat.id, "me")
            if member.status not in ["administrator", "creator"]:
                return await message.reply("❌ Bot needs admin rights in the channel first")

        except Exception as e:
            return await message.reply(f"❌ Channel verification failed: {e}")

        # ✅ Save resolved chat ID
        await save_user_data(user_id, 'chat_id', str(chat.id))
        await message.reply('✅ Chat ID set successfully!')

    except Exception as e:
        await message.reply(f'❌ Error: {e}')

async def handle_setrename(client, message, user_id):
    rename_tag = message.text.strip()
    await save_user_data(user_id, 'rename_tag', rename_tag)
    await message.reply(f'✅ Rename tag set to: {rename_tag}')

async def handle_setcaption(client, message, user_id):
    caption = message.text
    await save_user_data(user_id, 'caption', caption)
    await message.reply('✅ Caption set successfully!')

async def handle_setreplacement(client, message, user_id):
    match = re.match("'(.+)' '(.+)'", message.text)
    if not match:
        await message.reply("❌ Invalid format. Usage: 'WORD(s)' 'REPLACEWORD'")
    else:
        word, replace_word = match.groups()
        delete_words = await get_user_data_key(user_id, 'clean_words', [])
        if word in delete_words:
            await message.reply(f"❌ The word '{word}' is in the delete list and cannot be replaced.")
        else:
            replacements = {
                'replace_txt': word,
                'to_replace': replace_word
            }
            await save_user_data(user_id, 'replace_txt', word)
            await save_user_data(user_id, 'to_replace', replace_word)
            await message.reply(f"✅ Replacement saved: '{word}' → '{replace_word}'")

async def handle_addsession(client, message, user_id):
    session_string = message.text.strip()
    await save_user_data(user_id, 'session', session_string)
    await message.reply('✅ Session string added successfully!')

async def handle_deleteword(client, message, user_id):
    words_to_delete = message.text.split()
    delete_words = await get_user_data_key(user_id, 'clean_words', [])
    delete_words = list(set(delete_words + words_to_delete))
    await save_user_data(user_id, 'clean_words', delete_words)
    await message.reply(f"✅ Words added to delete list: {', '.join(words_to_delete)}")

async def handle_setthumb(client, message, user_id):
    if message.photo:
        temp_path = await message.download()
        try:
            thumb_path = f'{user_id}.jpg'
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            os.rename(temp_path, thumb_path)
            await message.reply('✅ Thumbnail saved successfully!')
        except Exception as e:
            await message.reply(f'❌ Error saving thumbnail: {e}')
    else:
        await message.reply('❌ Please send a photo')

def generate_random_name(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def rename_file(file, sender, edit):
    try:
        delete_words = await get_user_data_key(sender, 'clean_words', [])
        custom_rename_tag = await get_user_data_key(sender, 'rename_tag', '')
        replace_txt = await get_user_data_key(sender, 'replace_txt', '')
        to_replace = await get_user_data_key(sender, 'to_replace', '')
        
        last_dot_index = str(file).rfind('.')
        if last_dot_index != -1 and last_dot_index != 0:
            ggn_ext = str(file)[last_dot_index + 1:]
            if ggn_ext.isalpha() and len(ggn_ext) <= 9:
                if ggn_ext.lower() in VIDEO_EXTENSIONS:
                    original_file_name = str(file)[:last_dot_index]
                    file_extension = 'mp4'
                else:
                    original_file_name = str(file)[:last_dot_index]
                    file_extension = ggn_ext
            else:
                original_file_name = str(file)[:last_dot_index]
                file_extension = 'mp4'
        else:
            original_file_name = str(file)
            file_extension = 'mp4'
        
        for word in delete_words:
            original_file_name = original_file_name.replace(word, '')
        
        if replace_txt and to_replace:
            original_file_name = original_file_name.replace(replace_txt, to_replace)
        
        new_file_name = f'{original_file_name} {custom_rename_tag}.{file_extension}'
        
        os.rename(file, new_file_name)
        return new_file_name
    except Exception as e:
        print(f"Rename error: {e}")
        return file

@app.on_message(filters.channel)
async def handle_channel(client, message):
    try:
        chat_id = str(message.chat.id)
        # Check if this channel is set by any user
        user_data = await db.find_one({"chat_id": chat_id})
        if not user_data:
            return
            
        # Forward media or text to the same channel
        if message.media:
            await message.copy(chat_id)
        elif message.text:
            await client.send_message(chat_id, message.text)
    except Exception as e:
        print(f"Channel interaction error: {e}")

if __name__ == "__main__":
    app.run()