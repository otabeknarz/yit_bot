import shazamio

from loader import bot
from data.config import MEDIA_DIRECTORY
from aiogram.types import InputFile


async def download_file(file_id: str, chat_id: str):
    try:
        file_info = await bot.get_file(file_id=file_id)
        await bot.download_file(
            file_path=file_info.file_path,
            destination=MEDIA_DIRECTORY + chat_id + ".ogg",
        )

        return True
    except:
        return False


async def recognize_voice(voice_path="", track_id=""):
    try:
        shazam = shazamio.Shazam()

        if track_id:
            track = await shazam.track_about(track_id=track_id)
            music_id = track["key"]
            title = track["title"]
            subtitle = track["subtitle"]

            if track.get("images"):
                thumbnail = track["images"]["background"]
            else:
                thumbnail = InputFile("downloaded_musics/thumbnail-original.jpg")

            lyrics = track["sections"][1].get("text")

            return dict(
                status=True,
                track_id=music_id,
                title=title,
                subtitle=subtitle,
                thumbnail=thumbnail,
                lyrics=lyrics,
            )
        else:
            result = await shazam.recognize(voice_path)

            if result:
                music_id = result["track"]["key"]
                title = result["track"]["title"]
                subtitle = result["track"]["subtitle"]

                if result["track"].get("images"):
                    thumbnail = result["track"]["images"]["background"]
                else:
                    thumbnail = InputFile("downloaded_musics/thumbnail-original.jpg")

                lyrics = result["track"]["sections"][1].get("text")

                return dict(
                    status=True,
                    track_id=music_id,
                    title=title,
                    subtitle=subtitle,
                    thumbnail=thumbnail,
                    lyrics=lyrics,
                )
            else:
                return {"status": False}
    except:
        return {"status": False}


# import asyncio
#
# asyncio.run(recognize_voice(voice_path='voice2.ogg'))
