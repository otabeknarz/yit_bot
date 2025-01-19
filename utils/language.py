import logging
import random

from data.config import lang_file
from loader import db


class LangSet:
    def __init__(self, user_id):
        self.lang_file = lang_file
        self.user_id = user_id
        self.lang_dict = None

    async def _get_user_lang(self, user_id):
        try:
            res = await db.get_user_lang(user_id=user_id)

            self.lang_dict = res["lang"]
        except Exception as e:
            logging.error(e)
            self.lang_dict = "uz"

    async def get_translation(self, key):
        await self._get_user_lang(self.user_id)
        if key == "VIDEO_DOWNLOADED_MESSAGE":
            try:
                ret = self.lang_file[self.lang_dict][key]
            except KeyError:
                ret = self.lang_file["uz"][key]

            result = await db.select_all_ads()
            if result:
                data = random.choice(result)
                nm = f"<b>\n\n{data['ads_text']}</b>"
            else:
                nm = ""
            ret += f"{nm}"
        else:
            try:
                ret = self.lang_file[self.lang_dict][key]
            except KeyError:
                ret = self.lang_file["uz"][key]
        return ret

    async def select_lang(self):
        text = ""
        for lang in self.lang_file:
            text += lang_file[lang]["emoji"] + lang_file[lang]["select_lang"] + "\n"
        return text
