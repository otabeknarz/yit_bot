import json

from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")  # Bot token
ADMINS = ["5551503420"]  # env.list("ADMINS")  # adminlar ro'yxati
CHANNEL_ID = "-1001851404010"  # env.str("CHANNEL_ID")
DB_USER = "postgres"  # env.str("DB_USER")
DB_PASS = "postgres"  # env.str("DB_PASS")
DB_NAME = "postgres"  # env.str("DB_NAME")
DB_HOST = "localhost"  # env.str("DB_HOST")
lang_path = "lang.json"
lang_file = json.load(open(lang_path, "r", encoding="utf8"))
CLIENT_ID = "NFVfrvkkv9"
SERVER_IP = "94.198.217.85:7768"
ACCESS_TOKEN = "4dY8QJ5O6nsOL43S0IXqdEm78ty8c4uV"
MEDIA_DIRECTORY = "downloaded_musics/"
MESSAGE_SENDER_COMMAND = "send-message"  # env.str("MESSAGE_SENDER_COMMAND")

DATABASE_INFO = {
    "user": DB_USER,
    "password": DB_PASS,
    "database": DB_NAME,
    "host": DB_HOST,
}
