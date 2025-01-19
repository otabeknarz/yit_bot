import urllib.parse
import re


class LinksChecker(object):
    def __init__(self, video_link):
        self.video_link = video_link

    def get_instagram_link(self):
        result = None
        compile = re.compile(
            "^((?:https?://)?((?:www)\.)?(?:instagr\.am|instagram.com)[^\s]+)"
        )
        for text in self.video_link.split():
            match = compile.match(text)
            if match:
                result = match.group()
                break

        return result

    def get_tiktok_link(self):
        result = None
        compile = re.compile("^((?:https?://)?((?:www|vt|vm)\.)?(?:tiktok.com)[^\s]+)")
        for text in self.video_link.split():
            match = compile.match(text)
            if match:
                result = match.group()
                break

        return result

    def get_pinterest_link(self):
        result = None
        self.video_link = " http".join(self.video_link.split("http"))

        compile = re.compile("^(?:(?:https?://)?((?:www)\.)?(?:pin|pinterest)[^\s]+)")
        for text in self.video_link.split():
            match = compile.match(text)
            if match:
                result = match.group()
                break

        return result

    def get_likee_link(self):
        result = None
        compile = re.compile("^((?:https?://)?((?:www|l)\.)?(?:likee.video)[^\s]+)")
        for text in self.video_link.split():
            match = compile.match(text)
            if match:
                result = match.group()
                break

        return result

    def get_youtube_link(self):
        result = None
        compile = re.compile(
            "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
        )

        for letter in self.video_link.split():
            matching = compile.match(letter)
            if matching:
                result = matching.group()
                break

        return result.strip()

    def is_shorts_video(self):
        path = urllib.parse.urlparse(self.video_link).path
        if path.split("/")[1] == "shorts":
            return True
        else:
            return False
