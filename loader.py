from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# from aiogram.contrib.fsm_storage.redis import RedisStorage2

from data import config
from utils.db_api.postgresql import Database

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# dp = Dispatcher(bot, storage=RedisStorage2(host='127.0.0.1', port=6379, db=1))
db = Database()
