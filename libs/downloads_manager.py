import asyncio
import uuid
from json import loads
from math import ceil

import aiofiles
import aiohttp
import yt_dlp

from data.config import CLIENT_ID, SERVER_IP, ACCESS_TOKEN
from libs.SyncToAsync import ToAsync
from libs.url_checker import LinksChecker
import random


@ToAsync(executor=None)
def download_youtube_video(video_url: str, user_id: str) -> dict | None:
    seed = random.randint(10, 100)
    yt_dlp_options = {
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "format": "mp4[height<=720]",
        "outtmpl": f"downloaded_videos/{user_id}-{seed}.mp4",
    }
    try:
        with yt_dlp.YoutubeDL(yt_dlp_options) as ydl_opts:
            extracted_details = ydl_opts.extract_info(video_url)
            details = {
                "title": extracted_details["title"],
                "width": extracted_details["width"],
                "height": extracted_details["height"],
                "duration": extracted_details["duration"],
                "path": f"downloaded_videos/{user_id}-{seed}.mp4",
            }
    except Exception as e:
        print(f"Download_youtube_video error: {e}")
        return None

    return details


class VideoDownloader:
    def __init__(self, video_url, user_id, upload=False):
        self.video_url = video_url
        self.user_id = str(user_id)
        self.upload = upload
        self.download_url = None
        self.error = "not_found"

    async def download_video(self):
        res = None
        insta_res = None
        try:
            if self.download_url == "youtube":
                links_checker = LinksChecker(video_link=self.video_url)
                if links_checker.is_shorts_video():
                    await self.download_shorts()
                    res = None
                else:
                    details = await download_youtube_video(self.video_url, self.user_id)
                    return details

            elif self.download_url == "pinterest":
                res = await self.download_pinterest()

            elif self.download_url == "instagram":
                insta_res = await self.download_instagram_media_group()

            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=self.download_url) as response:
                        file_size = round(
                            (int(response.headers["Content-Length"]) / 1024) / 1024, 2
                        )

                        if file_size > 50 and self.upload:
                            self.error = "file-is-too-big"
                            return {"status": "ERROR"}

                        data = await response.read()
                        async with aiofiles.open(self.user_id + ".mp4", "wb") as file:
                            await file.write(data)

        except Exception as e:
            print(f"Download_video error: {e}")
            return {"status": "ERROR"}

        return {"status": "SUCCESS", "res": res, "insta_res": insta_res}

    async def download_pinterest(self):
        try:
            async with aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            ) as session:
                async with session.get(
                    f"http://{SERVER_IP}/api/pinterest/{CLIENT_ID}?video_url="
                    + self.video_url
                ) as response:
                    request = await response.json()
                    if request["status"]:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url=request["url"]) as response:
                                file_size = round(
                                    (int(response.headers["Content-Length"]) / 1024)
                                    / 1024,
                                    2,
                                )

                                if file_size > 50 and self.upload:
                                    self.error = "file-is-too-big"
                                    return {"status": False}

                                data = await response.read()
                                if request["type"] == "video":
                                    async with aiofiles.open(
                                        self.user_id + ".mp4", "wb"
                                    ) as file:
                                        await file.write(data)
                                    request["url"] = self.user_id + ".mp4"
                                elif request["type"] == "image/gif":
                                    async with aiofiles.open(
                                        self.user_id + ".gif", "wb"
                                    ) as file:
                                        await file.write(data)
                                    request["url"] = self.user_id + ".gif"
                                elif request["type"] == "photo":
                                    async with aiofiles.open(
                                        self.user_id + ".jpg", "wb"
                                    ) as file:
                                        await file.write(data)
                                    request["url"] = self.user_id + ".jpg"
                                return request
        except Exception as e:
            print(f"Download pinterest error: {e}")
            return {"status": False}

    async def download_instagram_media_group(self):
        try:
            reel_url = self.video_url.replace("reels", "reel")
            async with aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            ) as session:
                async with session.get(
                    f"http://194.99.22.21:8000/v1/get_info?url=" + reel_url
                ) as response:
                    request = await response.json()
                    result = []
                    if request["status"] == "success":
                        for x in request["contents"]:
                            id = uuid.uuid4().hex[-16]
                            try:
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url=x["url"]) as response:
                                        file_size = round(
                                            (
                                                int(response.headers["Content-Length"])
                                                / 1024
                                            )
                                            / 1024,
                                            2,
                                        )

                                        if file_size > 50 and self.upload:
                                            self.error = "file-is-too-big"
                                            return {"status": False}

                                        data = await response.read()
                                        if x["type"] == "image":
                                            async with aiofiles.open(
                                                self.user_id + id + ".jpg", "wb"
                                            ) as file:
                                                await file.write(data)
                                            result.append(
                                                dict(
                                                    type="image",
                                                    path=self.user_id + id + ".jpg",
                                                    thumb=None,
                                                )
                                            )
                                        elif x["type"] == "video":
                                            async with aiofiles.open(
                                                self.user_id + id + ".mp4", "wb"
                                            ) as file:
                                                await file.write(data)
                                                video_info = await self.get_infos(
                                                    self.user_id + id + ".mp4"
                                                )
                                                thumb_type = self.user_id + id + ".jpg"
                                                await self.get_thumbnail(
                                                    video_path=self.user_id + id,
                                                    video_duration=video_info[
                                                        "duration"
                                                    ],
                                                )
                                            result.append(
                                                dict(
                                                    type="video",
                                                    path=self.user_id + id + ".mp4",
                                                    thumb=thumb_type,
                                                    duration=video_info["duration"],
                                                    width=video_info["width"],
                                                    height=video_info["height"],
                                                )
                                            )
                                        else:
                                            pass
                            except:
                                continue
                        if result != []:
                            print(result)
                            return {"status": True, "results": result}
                        else:
                            return False
                    else:
                        return False
        except Exception as e:
            return False

    @ToAsync(executor=None)
    def download_shorts(self):
        try:
            ydl_opts = yt_dlp.YoutubeDL(
                {
                    "cookiefile": "/root/cookies.txt",
                    "quiet": True,
                    "noprogress": True,
                    "no_warnings": True,
                    "format": "mp4",
                    "outtmpl": str(self.user_id) + ".mp4",
                }
            )
            ydl_opts.download(self.video_url)
            return True
        except Exception as e:
            print(f"Download shorts error: {e}")
            return False

    async def get_thumbnail(self, video_path, video_duration):
        try:
            result = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-y",
                "-ss",
                str(ceil(video_duration / 2)),
                "-i",
                str(video_path) + ".mp4",
                "-vf",
                "scale=320:320:force_original_aspect_ratio=decrease",
                "-vframes",
                "1",
                video_path + ".jpg",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()
        except:
            return None

    async def get_infos(self, video_path):
        try:
            result = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "quiet",
                "-show_streams",
                "-select_streams",
                "v:0",
                "-of",
                "json",
                video_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            json_result = loads(stdout)["streams"][0]

            return {
                "duration": ceil(float(json_result["duration"])),
                "width": json_result["width"],
                "height": json_result["height"],
            }
        except Exception as e:
            print(f"Get_infos error: {e}")
            return {"duration": None, "width": 0, "height": 0}

    async def get_download_link(self):
        try:
            async with aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            ) as session:
                if "tiktok.com" in self.video_url:
                    async with session.get(
                        f"http://{SERVER_IP}/api/tiktok/{CLIENT_ID}?video_url="
                        + self.video_url
                    ) as response:
                        request = await response.json()

                    if request["status"]:
                        self.download_url = request["download_url"]

                elif "pin.it" in self.video_url or "pinterest.com" in self.video_url:
                    self.download_url = "pinterest"

                elif "likee.video" in self.video_url:
                    async with session.get(
                        f"http://{SERVER_IP}/api/likee/{CLIENT_ID}?video_url="
                        + self.video_url
                    ) as response:
                        request = await response.json()

                    if request["status"]:
                        self.download_url = request["download_url"]

                elif "youtu.be" in self.video_url or "youtube.com" in self.video_url:
                    self.download_url = "youtube"

                elif "instagram.com" in self.video_url:
                    # reel_url = self.video_url.replace('reels', 'reel')
                    #
                    # async with session.get(f"http://194.99.22.21:8000/v1/get_info?url=" + reel_url) as response:
                    #     request = await response.json()
                    #
                    # if request['status'] == 'success':
                    #     if len(request['contents']) == 1 and request['contents'][0]['type'] == 'video':
                    #         self.download_url = request['contents'][0]['url']
                    #     else:
                    self.download_url = "instagram"
                    # else:
                    #     self.error = 'link-is-not-supported'

        except Exception as e:
            print(f"Get_download_link error: {e}")

    async def final_download(self):
        await self.get_download_link()
        if self.download_url is not None:
            details = await self.download_video()
            if details:
                return {
                    "ok": True,
                    "instagram": False,
                    "path": details['path'],
                    "title": details['title'],
                    "width": details['width'],
                    "height": details['height'],
                    "duration": details['duration'],
                    "type": "video",
                }
        #     elif downloaded_video["insta_res"]:
        #         return {
        #             "instagram": True,
        #             "results": downloaded_video["insta_res"]["results"],
        #         }
        #     elif downloaded_video["status"] == "SUCCESS":
        #         video_info = await self.get_infos(self.user_id + ".mp4")
        #         await self.get_thumbnail(
        #             video_path=self.user_id, video_duration=video_info["duration"]
        #         )
        #         return {
        #             "ok": False,
        #             "instagram": False,
        #             "status": "SUCCESS",
        #             "path": self.user_id + ".mp4",
        #             "duration": video_info["duration"],
        #             "width": video_info["width"],
        #             "height": video_info["height"],
        #             "thumbnail": self.user_id + ".jpg",
        #         }
        #     else:
        #         return {"ok": False, "instagram": False, "status": "ERROR"}
        # else:
        #     return {"ok": False, "instagram": False, "status": "ERROR"}
