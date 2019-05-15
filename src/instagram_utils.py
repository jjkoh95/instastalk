import requests
import pickle
from constants import (
    BASE_URL,
    URL,
    LOGIN_URL,
    API_URL,
    QUERY_HASH,
    NUM,
    STORIES_API_URL,
    STORIES_QUERY_HASH,
)
import os
import json
from bs4 import BeautifulSoup
import time
import random
import hashlib
import datetime


class User():
    def __init__(self):
        """constructor"""
        self.interesting_users = {}
        self.session = requests.session()
        self._update_base_headers()
        self._get_interesting_users()
        self._login()

    def _cookies_to_dict(self, c):
        """cookies to dict"""
        c = c.replace('Path=/, ', '')
        c = c.replace('Path=/; ', '')
        c = c.replace('Secure, ', '')
        c = c.replace('HttpOnly; ', '')
        c = c.replace('Secure', '')
        pairs = c.split('; ')
        dic = {}
        for i in range(len(pairs) - 1):
            each_pair = pairs[i].split('=')
            dic[each_pair[0]] = each_pair[1]
        return dic

    def _update_base_headers(self):
        """update cookies/token"""
        self.session.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
        }
        r = self.session.get(URL)
        set_cookies = r.headers['set-cookie']
        set_cookies = self._cookies_to_dict(set_cookies)
        self.session.headers['x-csrftoken'] = set_cookies['csrftoken']

    def _login(self):
        self.username: str = os.getenv('USERNAME')
        self.password: str = os.getenv('PASSWORD')
        if self.username is None or self.password is None:
            raise Exception('USERNAME/PASSWORD not set')
        login_data = {
            'username': self.username,
            'password': self.password,
            'queryParams': {},
        }
        self.session.headers['referer'] = BASE_URL + 'accounts/login'
        self.session.headers['origin'] = BASE_URL

        r = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        response = json.loads(r.text)
        if response['authenticated']:
            print('Login successfully')
        else:
            raise Exception('Login error')

    def scrape(self):
        """this will download all posts/stories of interesting users"""
        for username in self.interesting_users:
            user_id, user_count, _ = self._get_ID_and_total_posts(
                username)
            self._download_posts(username, user_id, user_count)
            self._download_stories(username, user_id)

    def _get_interesting_users(self):
        """get interesting users"""
        for user in os.getenv('INTERESTING_USERS').split(' '):
            if user not in self.interesting_users:
                self.interesting_users[user] = float('-inf')

    def _get_ID_and_total_posts(self, username):
        """to get user ID"""
        web_data = self._get_web_data(BASE_URL + username)
        user_id = web_data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
        user_count = web_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['count']
        user_rhx_gis = web_data['rhx_gis']
        return user_id, user_count, user_rhx_gis

    def _get_web_data(self, url):
        """window._sharedData from profile"""
        response = self.session.get(url)
        response = response.text

        response = BeautifulSoup(response, 'html.parser')
        response = response.find_all('script')
        for i in range(len(response)):
            string_response = str(response[i])
            found = string_response.find('window._sharedData')
            if found != -1:
                start_index = string_response.find('{')
                end_index = string_response.find(
                    '</script>') - 1  # to remove the semicolon
                return json.loads(string_response[start_index:end_index])
        # print('Error retrieving window._sharedData')
        raise Exception('Error retrieving window._sharedData')

    def _get_api_data(self, api_url):
        """parse JSON (API_URL)"""
        return json.loads(self.session.get(api_url).text)

    def _get_data_edges(self, user_id, end_cursor, user_rhx_gis=''):
        """get edges based on end_cursor (starting end_cursor is empty string)"""
        api_url = API_URL.format(
            query_hash=QUERY_HASH, id=user_id, first=NUM, after=end_cursor)
        api_data = self._get_api_data(api_url)
        api_data = api_data['data']['user']['edge_owner_to_timeline_media']
        return api_data['page_info']['end_cursor'], api_data['edges']

    def _download_file(self, url, filename):
        """download image/video from URL"""
        r = self.session.get(url, stream=True)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in r:
                    f.write(chunk)

    def _download_posts(self, username, user_id, user_count, user_rhx_gis=''):
        """download all posts"""
        end_cursor = ''
        counter = 0
        if not os.path.exists(username):
            os.mkdir(username)
            os.chdir(username)
            while counter < user_count:
                timeFactor = 60*random.random()
                time.sleep(timeFactor)
                end_cursor, dataEdges = self._get_data_edges(
                    user_id, end_cursor, user_rhx_gis)
                counter += NUM
                i = len(dataEdges) - 1
                while i >= 0:
                    time_taken = dataEdges[i]['node']['taken_at_timestamp']
                    time_taken = datetime.datetime.fromtimestamp(
                        time_taken).strftime('%Y-%m-%d--%H-%M-%S')
                    print('Downloading post at {0}'.format(time_taken))
                    self._download_post_by_type(
                        dataEdges[i]['node'], time_taken, dataEdges[i]['node']['__typename'])
                    i -= 1
        else:
            os.chdir(username)
            while counter < user_count:
                timeFactor = 60*random.random()
                time.sleep(timeFactor)
                end_cursor, dataEdges = self._get_data_edges(
                    user_id, end_cursor, user_rhx_gis)
                counter += NUM
                latestTime = self.interesting_users[username]
                i = 0
                while i < len(dataEdges):
                    time_taken = dataEdges[i]['node']['taken_at_timestamp']
                    time_taken = datetime.datetime.fromtimestamp(
                        time_taken).strftime('%Y-%m-%d--%H-%M-%S')
                    if time_taken > latestTime:
                        print('Downloading post at {0}'.format(time_taken))
                        self._download_post_by_type(
                            dataEdges[i]['node'], time_taken, dataEdges[i]['node']['__typename'])
                        i += 1
                    else:
                        return

    def _download_post_by_type(self, data_node, time_taken, typename):
        """download post by type"""
        try:
            if typename == 'GraphImage':
                self._download_file(
                    data_node['display_url'], '{0}.jpg'.format(time_taken))
            else:
                shortcode = data_node['shortcode']
                data = self._get_web_data(BASE_URL + 'p/' + shortcode)
                if typename == 'GraphVideo':
                    self._download_file(data['entry_data']['PostPage'][0]['graphql']
                                        ['shortcode_media']['video_url'], '{0}.mp4'.format(time_taken))
                elif typename == 'GraphSidecar':
                    sidecarEdges = data['entry_data']['PostPage'][0]['graphql'][
                        'shortcode_media']['edge_sidecar_to_children']['edges']
                    for i in range(len(sidecarEdges)):
                        if sidecarEdges[i]['node']['__typename'] == 'GraphImage':
                            self._download_file(
                                sidecarEdges[i]['node']['display_url'], '{0}-{1}.jpg'.format(time_taken, i))
                        elif sidecarEdges[i]['node']['__typename'] == 'GraphVideo':
                            self._download_file(
                                sidecarEdges[i]['node']['video_url'], '{0}-{1}.mp4'.format(time_taken, i))
        except Exception as e:
            print(e)
            print('Error, retry download')
            self._download_post_by_type(data_node, time_taken, typename)

    def _download_stories(self, username, user_id):
        """download all stories"""
        url = STORIES_API_URL.format(query_hash=STORIES_QUERY_HASH, id=user_id)
        r2 = self.session.get(url)
        data = json.loads(r2.text)
        if len(data['data']['reels_media']) > 0:
            for i in data['data']['reels_media'][0]['items']:
                time_taken = i['taken_at_timestamp']
                time_taken = datetime.datetime.fromtimestamp(
                    time_taken).strftime('%Y-%m-%d--%H-%M-%S')
                if i['__typename'] == 'GraphStoryVideo':
                    fileformat = '.mp4'
                    url = i['video_resources'][-1]['src']
                else:
                    fileformat = '.jpg'
                    url = i['display_url']
                filename = time_taken + '--stories' + fileformat
                if filename > self.interesting_users['username']:
                    print('Downloading stories at {0}'.format(time))
                    self._download_file(url, filename)
        os.chdir('..')

    def save_myself(self, filename='instagram_user.pickle'):
        """this is to save class - self"""
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
