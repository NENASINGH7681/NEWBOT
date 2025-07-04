# devgagan
# Note if you are trying to deploy on vps then directly fill values in ("")

from os import getenv

# VPS --- FILL COOKIES 🍪 in """ ... """ 

INST_COOKIES = """
# wtite up here insta cookies
"""

YTUB_COOKIES = """
# write here yt cookies
"""

API_ID = int(getenv("API_ID", "21966020"))
API_HASH = getenv("API_HASH", "cb0e5ee22c346db5ef573a895374e2bd")
BOT_TOKEN = getenv("BOT_TOKEN", "7278695883:AAGq8NvkG4U1xnnZ_lKYx2AHvp4aQyGeILE")
OWNER_ID = list(map(int, getenv("OWNER_ID", "8082024139" "1898405489").split()))
MONGO_DB = "mongodb+srv://nenasingh00899:mjcX3omJfKhTZ8Vz@cluster0.v56a7fv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
LOG_GROUP = getenv("LOG_GROUP", "-1002882606244")
CHANNEL_ID = int(getenv("CHANNEL_ID", "-1002684220073"))
FREEMIUM_LIMIT = int(getenv("FREEMIUM_LIMIT", "0"))
PREMIUM_LIMIT = int(getenv("PREMIUM_LIMIT", "100000"))
WEBSITE_URL = getenv("WEBSITE_URL", "")
AD_API = getenv("AD_API", "")
STRING = getenv("STRING", None)
YT_COOKIES = getenv("YT_COOKIES", YTUB_COOKIES)
DEFAULT_SESSION = getenv("DEFAUL_SESSION", None)  # added old method of invite link joining
INSTA_COOKIES = getenv("INSTA_COOKIES", INST_COOKIES)
