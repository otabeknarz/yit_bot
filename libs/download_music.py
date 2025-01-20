import asyncio
import logging
import random
from json import loads
from math import ceil

import aiofiles
import aiohttp
import shazamio
import youtubesearchpython
import yt_dlp
from PIL import Image

from libs.SyncToAsync import ToAsync

ips = [
    "46.227.123.",
    "37.110.212.",
    "46.255.69.",
    "62.209.128.",
    "37.110.214.",
    "31.135.209.",
    "37.110.213.",
]


def random_ip():
    return ips[random.randint(0, len(ips) - 1)] + str(random.randint(0, 255))


class SearchMusic(object):
    @staticmethod
    @ToAsync(executor=None)
    def search_music(
        query: str,
        limit: int = 10,
        ignore_results: bool = False,
        searcher: youtubesearchpython.VideosSearch = None,
        next: bool = False,
        with_element: bool = False,
    ):
        if with_element:
            if searcher is None:
                searcher = youtubesearchpython.VideosSearch(query=query, limit=limit)

            if next:
                searcher.next()

            return searcher
        else:
            for_results = []
            results = youtubesearchpython.VideosSearch(
                query=query, limit=(limit if not ignore_results else limit * 2)
            )
            for result in results.result()["result"]:
                duration = result.get("duration").split(":")[::-1]
                if (len(duration) == 1 and int(duration[0]) < 30) or (
                    len(duration) > 2
                ):
                    continue
                elif len(duration) == 2 and (
                    int(duration[0]) + (int(duration[1]) * 60) > 600
                    or int(duration[0]) + (int(duration[1]) * 60) < 30
                ):
                    continue
                else:
                    if len(for_results) != limit:
                        for_results.append(
                            {"title": result.get("title"), "music_id": result.get("id")}
                        )
                    else:
                        break

            return for_results


class Music(object):
    def __init__(self, file_path: str = None, music_id: str = None):
        self.file_path = file_path
        self.youtube_link = f"https://youtu.be/{music_id}"
        self.title = None
        self.duration = 0

    @ToAsync(executor=None)
    def check_availability(self):
        try:
            options = {
                "cookiefile": "www.youtube.com_cookies.txt",
                "quiet": True,
                "noprogress": True,
                "no_warnings": True,
            }
            # options = {
            #     'outtmpl': "file_path",
            #     'format': 'bestvideo+bestaudio/best',
            #     'merge_output_format': 'mp4',
            #     'quiet': True,
            # }
            ydl = yt_dlp.YoutubeDL(options)
            info_video = ydl.extract_info(self.youtube_link, False)

            self.title = str(info_video["fulltitle"]).replace("<", "").replace(">", "")

            duration_string = int(info_video["duration"])
            self.duration = duration_string
        except:
            duration_string = 100

        if duration_string > 2400:
            return False
        else:
            return True

    @ToAsync(executor=None)
    def download_audio(self):
        try:
            ydl = yt_dlp.YoutubeDL(
                {
                    "cookiefile": "www.youtube.com_cookies.txt",
                    "quiet": True,
                    "noprogress": True,
                    "no_warnings": True,
                    "outtmpl": self.file_path,
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        },
                        {
                            "key": "FFmpegMetadata",
                        },
                    ],
                    "extractaudio": True,
                    "audioformat": "mp3",
                }
            )
            ydl.download(self.youtube_link)
            return True
        except Exception as e:
            print(e)
            return False

    async def get_mp3_info(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                "accept": "*/*",
                "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uz;q=0.6",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://v4.mp3youtube.cc",
                "referer": "https://v4.mp3youtube.cc/",
                "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "x-requested-with": "XMLHttpRequest",
                "X-Forwarded-For": random_ip(),
                "X-Client-IP": random_ip(),
                "X-Real-IP": random_ip(),
            }

            payload = {"link": self.youtube_link, "format": "mp3"}
            print(payload)

            async with session.post(
                "https://v4.mp3youtube.cc/api/converter", data=payload, headers=headers
            ) as response:
                print(response)
                response_data = await response.json()
                print("RESPONSE DATA")
                if "error" in response_data:
                    print("ERROR")
                    if (
                        response_data["error"] == True
                        and response_data["errorMsg"] == "Something went wrong"
                    ):
                        print("Something went wrong")
                        return {"downloaded": False}
                    else:
                        return {"downloaded": False}
                else:
                    print("Downloading, nothing went wrong")
                    async with session.get(url=response_data["url"]) as response:
                        data = await response.read()
                        async with aiofiles.open(self.file_path + ".mp3", "wb") as file:
                            await file.write(data)

                    try:
                        data_fprobe = await asyncio.create_subprocess_exec(
                            "ffprobe",
                            "-v",
                            "quiet",
                            "-show_streams",
                            "-select_streams",
                            "a:0",
                            "-of",
                            "json",
                            self.file_path + ".mp3",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )

                        stdout, stderr = await data_fprobe.communicate()
                        json_result = loads(stdout)["streams"][0]
                        duration = ceil(float(json_result["duration"]))
                        # print({'duration': ceil(float(json_result['duration']))})
                    except Exception as e:
                        logging.error(e)
                        return {"downloaded": False}

                    from youtubesearchpython.__future__ import VideosSearch

                    videosSearch = VideosSearch(self.youtube_link, limit=1)
                    result = await videosSearch.next()
                    title = [i["title"] for i in result["result"]]
                    return {
                        "downloaded": True,
                        "audio-path": self.file_path + ".mp3",
                        "audio-duration": duration,
                        "title": title[0],
                    }

        # api_url = 'https://yt5s.io/api/ajaxSearch'
        # data = {
        #     'q': self.youtube_link,
        #     'vt': 'mp3'
        # }
        # try:
        #     async with aiohttp.ClientSession() as session:
        #         async with session.post(api_url, data=data, headers={'X-Requested-With': 'XMLHttpRequest'}) as response:
        #             if response.status == 200:
        #                 result = await response.json()
        #                 mp3_info_dict = {}
        #                 base_url = 'https://ve44.aadika.xyz/download/'
        #                 video_id = result['vid']
        #                 time_expires = result['timeExpires']
        #                 token = result['token']
        #
        #                 for index, (quality, info) in enumerate(result['links']['mp3'].items(), start=1):
        #                     if info['f'] == 'mp3':
        #                         mp3_info = {
        #                             'title': result['title'],
        #                             'format': info['k'],
        #                             'q': info['q'],
        #                             'size': info['size'],
        #                             'key': info['key'],
        #                             'url': f"{base_url}{video_id}/mp3/{info['k']}/{time_expires}/{token}/1?f=yt5s.io"
        #                         }
        #                         mp3_info_dict[index] = mp3_info
        #
        #                 x = mp3_info_dict[len(mp3_info_dict)]
        #
        #                 async with session.get(url=x['url']) as response:
        #                     data = await response.read()
        #                     async with aiofiles.open(self.file_path + '.mp3', 'wb') as file:
        #                         await file.write(data)
        #                 try:
        #                     data_fprobe = await asyncio.create_subprocess_exec(
        #                         'ffprobe', '-v', 'quiet',
        #                         '-show_streams',
        #                         '-select_streams', 'a:0', '-of', 'json',
        #                         self.file_path + '.mp3',
        #                         stdout=asyncio.subprocess.PIPE,
        #                         stderr=asyncio.subprocess.PIPE)
        #
        #                     stdout, stderr = await data_fprobe.communicate()
        #                     json_result = loads(stdout)['streams'][0]
        #                     print({'duration': ceil(float(json_result['duration'])), 'width': json_result['width'],
        #                            'height': json_result['height']})
        #                 except Exception as e:
        #                     logging.error(e)
        #                     return {'downloaded': False}
        #
        #                 video_url = self.youtube_link
        #                 from youtubesearchpython.__future__ import VideosSearch
        #                 videosSearch = VideosSearch(video_url, limit=1)
        #                 result = await videosSearch.next()
        #                 duration = [i['duration'] for i in result['result']]
        #                 return {'downloaded': True, 'audio-path': self.file_path + '.mp3',
        #                         'audio-duration': duration[0].split(':'), 'title': x['title']}
        #             else:
        #                 return {'downloaded': False}
        # except:
        #     return {'downloaded': False}

    async def download_music(self):
        checker = await self.check_availability()
        if checker:
            get_youtube_link = self.youtube_link
        else:
            return {"downloaded": False, "message": "FILE_IS_TOO_BIG"}

        if get_youtube_link:
            # audio_info = await self.get_mp3_info()
            # if audio_info["downloaded"]:
            #     return audio_info
            # else:
            #     await asyncio.sleep(6)
            #     audio_info1 = await self.get_mp3_info()
            #     if audio_info1["downloaded"]:
            #         return audio_info1
            #     else:
            #         await asyncio.sleep(6)
            #         audio_info2 = await self.get_mp3_info()
            #         if audio_info2["downloaded"]:
            #             return audio_info2
            #         else:
            download_audio = await self.download_audio()
            if download_audio:
                return {
                    "downloaded": True,
                    "audio-path": self.file_path + ".mp3",
                    "audio-duration": self.duration,
                    "title": self.title,
                }
            else:
                return {"downloaded": False}
        else:
            return {"downloaded": False}


async def get_top_musics(limit=100, offset=0):
    shazam = shazamio.Shazam()
    for_result = []
    other_country_codes = ["UZ", "RU", "GB", "KZ", "TR", "AZ"]
    for country_code in other_country_codes:
        top_musics_list = await shazam.top_country_tracks(
            country_code=country_code, offset=offset, limit=limit
        )

        for track in top_musics_list["data"]:
            for_result.append(
                (
                    track["attributes"]["artistName"]
                    + " - "
                    + track["attributes"]["name"],
                    track["id"],
                    country_code,
                )
            )
    return for_result


def ResizeThumbnail(path):
    size = 320, 320
    try:
        im = Image.open(path)
        im.thumbnail(size, Image.Resampling.LANCZOS)
        im.save(path.replace("-original", ""), "JPEG")
    except:
        pass
