# ---------------------------------------------------
# File Name: plans.py
# Description: A Pyrogram bot for premium user management
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-06-23
# Version: 2.0.6
# License: MIT License
# ---------------------------------------------------

import datetime
import pytz
from devgagan import app
from config import OWNER_ID
from devgagan.core.func import get_seconds
from devgagan.core.mongo import plans_db  
from pyrogram import filters 

# Constants
IST = pytz.timezone("Asia/Kolkata")

def format_time_with_emoji(dt, prefix="Time"):
    """Standardized time formatting with emoji support"""
    time_str = dt.strftime("%I:%M:%S %p")
    return f"{dt.strftime('%d-%m-%Y')}\n⏱️ {prefix} : {time_str}"

async def format_premium_info(user, user_id, expiry_date):
    """Generate standardized premium user info string"""
    expiry_ist = expiry_date.astimezone(IST)
    current_time = datetime.datetime.now(IST)
    time_left = expiry_ist - current_time
    
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    return (
        f"⚜️ Premium User Data:\n\n"
        f"👤 User: {user}\n"
        f"⚡ User ID: <code>{user_id}</code>\n"
        f"⏰ Time Left: {days} days, {hours} hours, {minutes} minutes\n"
        f"⌛️ Expiry Date: {format_time_with_emoji(expiry_ist, 'Expiry Time')}"
    )

@app.on_message(filters.command("rem") & filters.user(OWNER_ID))
async def remove_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])  
        user = await client.get_users(user_id)
        data = await plans_db.check_premium(user_id)  
        
        if data and data.get("_id"):
            await plans_db.remove_premium(user_id)
            await message.reply_text("User removed successfully!")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>Hey {user.mention},\n\nYour premium access has been removed.\nThank you for using our service 😊.</b>"
            )
        else:
            await message.reply_text("Unable to remove user!\nAre you sure it was a premium user ID?")
    else:
        await message.reply_text("Usage: /rem user_id")

@app.on_message(filters.command("myplan"))
async def myplan(client, message):
    user_id = message.from_user.id
    user = message.from_user.mention
    data = await plans_db.check_premium(user_id)
    
    if data and data.get("expire_date"):
        expiry = data.get("expire_date")
        info = await format_premium_info(user, user_id, expiry)
        await message.reply_text(info)
    else:
        await message.reply_text(
            f"Hey {user},\n\nYou do not have any active premium plans"
        )

@app.on_message(filters.command("check") & filters.user(OWNER_ID))
async def get_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        data = await plans_db.check_premium(user_id)
        
        if data and data.get("expire_date"):
            info = await format_premium_info(user.mention, user_id, data["expire_date"])
            await message.reply_text(info)
        else:
            await message.reply_text("No premium data found for this user!")
    else:
        await message.reply_text("Usage: /check user_id")

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def give_premium_cmd_handler(client, message):
    if len(message.command) == 4:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        time_str = f"{message.command[2]} {message.command[3]}"
        seconds = await get_seconds(time_str)
        
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            await plans_db.add_premium(user_id, expiry_time)
            
            current_time = format_time_with_emoji(datetime.datetime.now(IST), "Joining Time")
            expiry_str = format_time_with_emoji(expiry_time.astimezone(IST), "Expiry Time")
            
            admin_msg = (
                f"Premium added successfully ✅\n\n"
                f"👤 User: {user.mention}\n"
                f"⚡ User ID: <code>{user_id}</code>\n"
                f"⏰ Premium Access: <code>{time_str}</code>\n\n"
                f"⏳ Joining Date: {current_time}\n\n"
                f"⌛️ Expiry Date: {expiry_str}\n\n"
                f"__**Powered by Team SPY__**"
            )
            
            user_msg = (
                f"👋 Hey {user.mention},\n"
                f"Thank you for purchasing premium.\nEnjoy!! ✨🎉\n\n"
                f"⏰ Premium Access: <code>{time_str}</code>\n"
                f"⏳ Joining Date: {current_time}\n\n"
                f"⌛️ Expiry Date: {expiry_str}"
            )
            
            await message.reply_text(admin_msg, disable_web_page_preview=True)
            await client.send_message(user_id, text=user_msg, disable_web_page_preview=True)
        else:
            await message.reply_text(
                "Invalid time format. Use '1 day', '1 hour', '1 min', '1 month' or '1 year'"
            )
    else:
        await message.reply_text(
            "Usage: /add user_id time (e.g. '1 day')"
        )

@app.on_message(filters.command("transfer"))
async def transfer_premium(client, message):
    if len(message.command) == 2:
        new_user_id = int(message.command[1])
        sender_user_id = message.from_user.id
        sender_user = await client.get_users(sender_user_id)
        new_user = await client.get_users(new_user_id)
        
        data = await plans_db.check_premium(sender_user_id)
        
        if data and data.get("_id"):
            expiry = data.get("expire_date")
            await plans_db.remove_premium(sender_user_id)
            await plans_db.add_premium(new_user_id, expiry)
            
            expiry_str = format_time_with_emoji(expiry.astimezone(IST), "Expiry Time")
            current_time = format_time_with_emoji(datetime.datetime.now(IST), "Transfer Time")
            
            await message.reply_text(
                f"✅ Premium Plan Transferred Successfully!\n\n"
                f"👤 From: {sender_user.mention}\n"
                f"👤 To: {new_user.mention}\n"
                f"⏳ Expiry Date: {expiry_str}\n\n"
                f"__Powered by Team SPY__ 🚀"
            )
            
            await client.send_message(
                chat_id=new_user_id,
                text=(
                    f"👋 Hey {new_user.mention},\n\n"
                    f"🎉 Your Premium Plan has been Transferred!\n"
                    f"🛡️ Transferred From: {sender_user.mention}\n\n"
                    f"⏳ Expiry Date: {expiry_str}\n"
                    f"📅 Transferred On: {current_time}\n\n"
                    f"__Enjoy the Service!__ ✨"
                )
            )
        else:
            await message.reply_text("⚠️ You are not a Premium user!")
    else:
        await message.reply_text("⚠️ Usage: /transfer user_id")

async def premium_remover():
    all_users = await plans_db.premium_users()
    removed_users = []
    not_removed_users = []

    for user_id in all_users:
        try:
            user = await app.get_users(user_id)
            chk_time = await plans_db.check_premium(user_id)

            if chk_time and chk_time.get("expire_date"):
                expiry_date = chk_time["expire_date"]

                if expiry_date <= datetime.datetime.now():
                    name = user.first_name
                    await plans_db.remove_premium(user_id)
                    await app.send_message(
                        user_id, 
                        text=f"Hello {name}, your premium subscription has expired."
                    )
                    removed_users.append(f"{name} ({user_id})")
                else:
                    name = user.first_name
                    current_time = datetime.datetime.now()
                    time_left = expiry_date - current_time

                    days = time_left.days
                    hours, remainder = divmod(time_left.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    if days > 0:
                        remaining_time = f"{days} days, {hours} hours, {minutes} minutes"
                    elif hours > 0:
                        remaining_time = f"{hours} hours, {minutes} minutes"
                    elif minutes > 0:
                        remaining_time = f"{minutes} minutes"
                    else:
                        remaining_time = f"{seconds} seconds"

                    not_removed_users.append(f"{name} ({user_id})")
        except:
            await plans_db.remove_premium(user_id)
            removed_users.append(f"Unknown ({user_id})")

    return removed_users, not_removed_users

@app.on_message(filters.command("freez") & filters.user(OWNER_ID))
async def refresh_users(_, message):
    removed_users, not_removed_users = await premium_remover()
    summary = (
        f"**Premium Users Cleanup Summary**\n\n"
        f"> **Removed Users:**\n{chr(10).join(removed_users) if removed_users else 'None'}\n\n"
        f"> **Active Users:**\n{chr(10).join(not_removed_users) if not_removed_users else 'None'}"
    )
    await message.reply_text(summary)