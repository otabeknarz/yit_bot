from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message, CallbackQuery

from data.config import ADMINS
from loader import db


class IsOwner(BoundFilter):
    key = "is_owner"
    is_owner: bool

    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def check(self, message: Message) -> bool:
        if str(message.from_user.id) in ADMINS:
            return self.is_owner and True

        get_admin = False
        for admin in await db.select_all_admins():
            if str(admin["user_id"]) == str(message.from_user.id):
                get_admin = True
                break

        if get_admin:
            return self.is_owner and True
        else:
            return False


class IsOwnerCall(BoundFilter):
    key = "is_owner"
    is_owner: bool

    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def check(self, message: CallbackQuery) -> bool:
        if str(message.from_user.id) in ADMINS:
            return self.is_owner and True

        get_admin = False
        for admin in await db.select_all_admins():
            if str(admin["user_id"]) == str(message.from_user.id):
                get_admin = True
                break

        if get_admin:
            return self.is_owner and True
        else:
            return False
