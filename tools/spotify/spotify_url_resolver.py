from song import Song
from audio.AudioProvider_youtube import YouTube
from audio.AudioProvider_soundcloud import SoundCloud
from client import SpotifyClient
import os
import logging
import re

class NoUrl(Exception):
    pass

class InvalidArgs(Exception):
    pass

class InvalidUrls(Exception):
    pass

URL_REGEX = re.compile("https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}[-a-zA-Z0-9()@:%_+.~#?&/=]*")

class Spotify_Worker:
    def __init__(self):
        SpotifyClient.init(client_id=os.environ.get('SPOTIFY_CLIENT_ID'), client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'))
        self.client = SpotifyClient()
        self.youtube_client = YouTube()
        self.soundcloud_client = SoundCloud()


    @staticmethod
    def get_song(url: str) -> Song:
        return Song.from_url(url)

    @staticmethod
    def _run(client, query) -> str | None:
        songData = client.get_results(query)
        return songData[0].url if len(songData) > 0 else None

    def search_song(self, query: str):

        result = self.client.search(q=query, limit=1)

        if not result['tracks']['items']:
            logging.warning(f"No song for query: {query}")
            return None

        return self.resolve_url(result['tracks']['items'][0]['external_urls']['spotify'])

    def resolve_url(self, url: str = None, force_use_sc: bool = False, force_use_yt: bool = False) -> str | None:
        if not url:
            raise NoUrl("No Url found!")

        if force_use_sc and force_use_yt:
            raise InvalidArgs("Only one `force_use_sc` or `force_use_yt` can be use at once!")

        # if not URL_REGEX.match(url):
        #     raise InvalidUrls("Invalid Urls")

        song = self.get_song(url)

        if force_use_sc:
            logging.warning("This client may return `None`, so you need to handle carefully")
            songData = self._run(self.soundcloud_client, song.name)
            return songData

        if force_use_yt:
            logging.warning("This client may NOT work perfectly and return `None`, so you need to handling carefully")
            songData = self._run(self.youtube_client, song.name)
            return songData

        songData = self._run(self.soundcloud_client, song.name)

        if songData:
            return songData
        else:
            logging.warning(f"Seem SoundCloud didn't return anything, falling back to youtube")
            return self._run(self.youtube_client, song.name)


# TESTING / Debug only
if __name__ == '__main__':
    import utils.logger
    import dotenv
    import time
    dotenv.load_dotenv()
    utils.logger.setup_logger()
    query = "チルノのパーフェクトさんすう教室"
    url_test = 'https://open.spotify.com/track/2C7DrdqoU4U7Wc0vZRVi21?si=f4e1782335a74b8d' # Blend-S op / ぼなぺてぃーと▽S

    worker: Spotify_Worker = Spotify_Worker()
    logging.info("Testing in progress...")
    start = time.time()
    data = {"url": worker.resolve_url(url_test), "query": worker.search_song(query)}
    end = time.time()
    run_time = end - start
    logging.info(f"Finished... (url): {data['url']}")
    logging.info(f"Finished... (query): {data['query']}")
    logging.info(f"Runtime: {run_time:.6f} seconds")
    """
    Run results:
    [28-04-2025 16:42:24] [root:89] [<module>] [✅] [INFO] - Tesing in progress...
    [28-04-2025 16:42:56] [root:94] [<module>] [✅] [INFO] - Finished... (url): https://soundcloud.com/user-278546453/shappyhardcore-remix 
        #   ❌ Seem SoundCloud return the wrong song type (the remix one) so we need to use youtube here..?
    [28-04-2025 16:42:56] [root:95] [<module>] [✅] [INFO] - Finished... (query): https://soundcloud.com/ragethunder/8kqyvdynzc59
    [28-04-2025 16:42:56] [root:96] [<module>] [✅] [INFO] - Runtime: 32.024596 seconds

    """
