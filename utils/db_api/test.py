import aiohttp
import asyncio


async def fetch_youtube_mp3(url):
    api_url = "https://youtube-mp3-downloader5.p.rapidapi.com/"
    querystring = {"url": url}
    headers = {
        "x-rapidapi-key": "3a001c87b0msha96030bed16d3d7p1d422ajsnd64578e91d82",
        "x-rapidapi-host": "youtube-mp3-downloader5.p.rapidapi.com",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            api_url, headers=headers, params=querystring
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {
                    "error": f"Failed to fetch data, status code: {response.status}"
                }


async def main():
    url = "https://youtu.be/LvVz-hgTObk"
    result = await fetch_youtube_mp3(url)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
