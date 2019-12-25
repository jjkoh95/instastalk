import requests
from datetime import (
    datetime,
)
from bs4 import BeautifulSoup
import json
import time
import random
import pickle
from instastalk.constants import (
    BASE_URL,
    QUERY_POST_URL,
    SHORTCODE_URL,
)


class BaseStalker():
    def __init__(self):
        ''' constructor '''
        self.session = requests.session()
        self.session.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
        }
        self.session.get(BASE_URL)
        self.history = {}

    def download_user(self, username: str, download_timestamp: int = int(time.time()), multiprocessing: bool = False, timesleep_factor: int = 60):
        ''' this is the most important io - download all posts/stories related to user '''

        # handle this in a stupid way for now
        if username not in self.history:
            self.history[username] = 0
        resp = BeautifulSoup(self.session.get(
            f'{BASE_URL}/{username}').text, 'html.parser')
        scripts = resp.find_all('script')
        def find_shared_data(x): return x.text.find('window._sharedData') != -1
        shared_data_script = next(filter(find_shared_data, scripts), None)
        # guaranteed to have response
        if shared_data_script is None:
            raise Exception(f'Unable to extract data from user - {username}')
        # basically the length of "window._sharedData = "
        shared_data = json.loads(shared_data_script.text[21:-1])

        # first iteration should get from window._sharedData
        user_data = shared_data['entry_data']['ProfilePage'][0]['graphql']['user']
        user_id = user_data['id']
        end_cursor = user_data['edge_owner_to_timeline_media']['page_info']['end_cursor']
        edges = user_data['edge_owner_to_timeline_media']['edges']

        self._download_user_stories(username, user_id)

        # this is a flag to determine if a post has been downloaded or not
        should_continue = True

        while end_cursor != None:
            for edge in edges:
                self._sleep(timesleep_factor)
                should_continue = self._download_by_shortcode(
                    edge['node']['shortcode'], username)
                if not should_continue:
                    return
            self._sleep(timesleep_factor)
            query_url = QUERY_POST_URL.format(
                id=user_id, first=12, after=end_cursor)
            query_response = json.loads(self.session.get(query_url).text)
            timeline_media = query_response['data']['user']['edge_owner_to_timeline_media']
            end_cursor = timeline_media['page_info']['end_cursor']
            edges = timeline_media['edges']

        # This is useful for the app to pick up last downloaded datetime
        self.history[username] = download_timestamp

    def _sleep(self, timesleep_factor: int):
        ''' sleep function to outsmart instagram rate limiting '''
        return time.sleep(random.random()*timesleep_factor)

    def _download_by_shortcode(self, shortcode: str, username: str) -> bool:
        ''' essentially every post has a shortcode associated,
        this is mostly useful in `nested` edges/nodes/posts - GraphSidecar,
        this should return a flag if app should continue
        '''
        shortcode_url = SHORTCODE_URL.format(
            shortcode=shortcode,
            child_comment_count=3,
            fetch_comment_count=40,
            parent_comment_count=24,
            has_threaded_comments='true',
        )
        query_response = self.session.get(shortcode_url)
        # retry mechanism
        if query_response.status_code != 200:
            self.session = requests.session()
            self.session.get(BASE_URL)
            return self._download_by_shortcode(shortcode, username)
        query_response = json.loads(query_response.text)
        time_taken_unix_timestamp = query_response['data']['shortcode_media']['taken_at_timestamp']
        if (time_taken_unix_timestamp < self.history[username]):
            # if time_taken < last action - meaning already saved stop
            return False
        time_taken_timestamp = datetime.fromtimestamp(
            time_taken_unix_timestamp).strftime('%Y-%m-%d--%H-%M-%S')
        self._download_node(
            query_response['data']['shortcode_media'], username, time_taken_timestamp)
        return True

    def _download_node(self, node, username: str, time_taken_timestamp: str, count: int = 0):
        ''' a more `generic` function to download each node '''
        if node['__typename'] == 'GraphImage':
            self._download_file(node['display_url'],
                                f'{username}/{time_taken_timestamp}-{count}.jpg')
            return

        if node['__typename'] == 'GraphVideo':
            self._download_file(node['video_url'],
                                f'{username}/{time_taken_timestamp}-{count}.mp4')
            return

        if node['__typename'] == 'GraphSidecar':
            for i, edge in enumerate(node['edge_sidecar_to_children']['edges']):
                # NOTE: This is to prevent rate-limiting
                self._sleep(random.random()*i*0.5)
                self._download_node(
                    edge['node'], username, time_taken_timestamp, i)
            return

    def _download_file(self, url: str, filename: str):
        ''' download file from `url` to `filaname` '''
        r = self.session.get(url, stream=True)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            return
        raise Exception('Failed to download file')

    def to_pickle(self, filename: str):
        ''' save `self` as pickle '''
        with open(filename, 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def _download_user_stories(self, username: str, user_id: str):
        ''' not implemented '''
        pass
