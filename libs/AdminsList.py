from data import config
from loader import dp, db


async def admins_list():
    admins = []
    get_admins = await db.select_all_admins()
    if get_admins:
        for admin in get_admins:
            admins.append(admin["user_id"])

    admins.extend(config.ADMINS)
    return admins
