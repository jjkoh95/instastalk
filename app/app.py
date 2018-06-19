from UserModel import User
import UserDALC
from URLS import *
import requests
import getpass
import json
from bs4 import BeautifulSoup
import os
import sqlite3
import datetime
import hashlib

session = requests.session()
session.headers = {}
session.headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'
session.headers['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
session.headers['accept-encoding'] = 'gzip, deflate, br'
session.headers['language'] = 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6'
session.headers['cache-control'] = 'max-age=0'
session.headers['content-type'] = 'application/x-www-form-urlencoded'

def createConnection(db_file='instastalk.db'):
    '''
        create sqlite db
    '''
    try:
        conn = sqlite3.connect(db_file)
    except exception as e:
        print(e)
    finally:
        conn.close()


def cookiesToDict(c):
    '''
        c : cookies
    '''
    c = c.replace('Path=/, ', '')
    c = c.replace('Path=/; ', '')
    c = c.replace('Secure, ', '')
    c = c.replace('HttpOnly; ', '')
    c = c.replace('Secure', '')
    pairs = c.split('; ')
    dic = {}
    #print(pairs)
    for i in range(len(pairs) - 1):
        each_pair = pairs[i].split('=')
        dic[each_pair[0]] = each_pair[1]
    #print(dic)
    return dic

def updateBaseHeader():
    '''
        update cookies/tokens
    '''
    r = session.get(URL)
    set_cookies = r.headers['set-cookie']
    set_cookies = cookiesToDict(set_cookies)
    session.headers['x-csrftoken'] = set_cookies['csrftoken']

def initialiseDB():
    '''
        create local DB
    '''
    createConnection()
    UserDALC.createTable()

def promptBasicMode():
    print('===== Select Mode =====')
    print('1. Run with Login')
    print('2. Run without Login')
    print('9. Exit')
    basic_mode = input('Mode: ')
    if basic_mode == '1':
        # go to login mode
        return promptLoginMode()
    if basic_mode == '2':
        # go to scraper
        # need to have x-instagram-gis in header
        return scraper(login=False)
    if basic_mode == '9':
        return        
    else:
        print('Invalid input!')
        return promptBasicMode()

def promptLoginMode():
    '''
        to login with existing accounts or new account
    '''
    print('===== Login Mode =====')
    allUsers = UserDALC.getAll()
    if(len(allUsers) != 0):
        print('Available accounts:')
        for i in range(len(allUsers)):
            time = datetime.datetime.fromtimestamp(allUsers[i][2]).strftime('%Y-%m-%d--%H-%M-%S') 
            print('ID: {0}, Username: {1}, Last Login: {2}'.format(i, allUsers[i][0], time))
    print('===== ====== ======')
    if(len(allUsers) != 0):
        print('1. Login with existing accounts')
    print('2. Add new account')
    print('9. Return to home page')
    login_mode = input('Mode: ') 
    if(len(allUsers) != 0):
        if login_mode == '1':
            userIndex = int(input('Select Users ID: '))
            try:
                global user
                user = User()
                user.loginOldEmail(allUsers[userIndex][0])
                cookies = json.loads(user.cookie)
                session.headers['x-csrftoken'] = cookies['csrftoken']
                session.cookies.set('csrftoken', cookies['csrftoken'], domain='.instagram.com', path='/')
                session.cookies.set('sessionid', cookies['sessionid'], domain='.instagram.com', path='/')
                return scraper()
            except Exception as e:
                print(e)
                return promptLoginMode()
    if login_mode == '2':
        username = input('Username: ')
        password = getpass.getpass('Password: ')
        login_data = {'username': username, 'password': password, 'queryParams': {}}
        session.headers['referer'] = BASE_URL + 'accounts/login'
        session.headers['origin'] = BASE_URL
        r = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        response = json.loads(r.text)
        if response['authenticated']:
            print('Login successfully')
            cookies = {}
            set_cookies = cookiesToDict(r.headers['set-cookie'])
            cookies['sessionid'] = set_cookies['sessionid']
            cookies['csrftoken'] = set_cookies['csrftoken']
            # need to enter to db
            user = User()
            user.login(username, json.dumps(cookies))
            # go to app
            return scraper()
        else:
            print('Login failed')
            return promptLoginMode()
    if login_mode == '9':
        return promptBasicMode()
    else:
        print('Invalid input')
        return promptLoginMode()

def scraper(login=True):
    print('===== Welcome to Instastalk =====')
    username = input('Enter username or -1 to exit: ')
    while username == '-1':
        if login:
            logoutMode = input('logout? y/n? ')
            if logoutMode == 'n':
                print('Exit without logout')
                return
            else:
                logout()
                return
        else:
            print('Exit')
            return
    # try to get id and count by username
    try:
        if login:
            user_id, user_count = getIDandTotalPosts(username)
            downloadPosts(username, user_id, user_count)
            downloadStories(username, user_id)
        else:
            user_id, user_count, user_rhx_gis = getIDandTotalPosts(username)
            downloadPosts(username, user_id, user_count, user_rhx_gis)
    except Exception as e:
        print(e)
    finally:
        os.chdir('../')
        return scraper(login)

def getWebData(url):
    '''
        window._sharedData from profile
    '''
    response = session.get(url)
    response = response.text

    response = BeautifulSoup(response, 'html.parser')
    response = response.find_all('script')
    for i in range(len(response)):
        stringResponse = str(response[i])
        found = stringResponse.find('window._sharedData')
        if found != -1:
            startIndex = stringResponse.find('{')
            endIndex = stringResponse.find('</script>') - 1 # to remove the semicolon
            return json.loads(stringResponse[startIndex:endIndex])
    print('Error')
    return None

def getIDandTotalPosts(username):
    '''
        to get ID
    '''
    webData = getWebData(BASE_URL + username)
    user_id = webData['entry_data']['ProfilePage'][0]['graphql']['user']['id']
    user_count = webData['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['count']
    user_rhx_gis = webData['rhx_gis']
    print(user_rhx_gis)
    return user_id, user_count, user_rhx_gis

def logout():
    '''
        to logout and remove entry from db
    '''
    logout_data = {'csrfmiddlewaretoken': session.headers['x-csrftoken']}
    r = session.post(LOGOUT_URL, data=logout_data, allow_redirects=True)
    if r.status_code == 200:
        print('Successfully logged out')
    global user
    user.logout()

def downloadFile(url, filename):
    '''
        to download image or video from URL 
    '''
    r = session.get(url, stream=True)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in r:
                f.write(chunk)

def getLatestFilename(stories=False):
    '''
        to get latest filename to prevent redundant download
        assume that you are in the directory
    '''
    fileList = os.listdir()
    fileList.sort(reverse=True)
    if len(fileList) == 0:
        return '-999'
    if not stories:
        for i in range(len(fileList)):
            if 'stories' not in fileList[i]:
                return fileList[i]
    else:
        for i in range(len(fileList)):
            if 'stories' in fileList[i]:
                return fileList[i]

    return '-999'

def getAPIData(url):
    '''
        Parse JSON (API_URL)
    '''
    apiData = session.get(url)
    apiData = apiData.text

    return json.loads(apiData)

def getDataEdges(user_id, end_cursor, user_rhx_gis):
    '''
        get edges based on end_cursor (starting end_cursor is empty string)
    '''
    apiurl = API_URL.format(query_hash=QUERY_HASH, id=user_id, first=NUM, after=end_cursor)
    if user_rhx_gis != '':
        variables = '"id":"{id}","first":12,"after":"{end_cursor}"'.format(id=user_id, end_cursor=end_cursor)
        variables = '{' + variables + '}'
        x_instagram_gis = '{rhx_gis}:{variables}'.format(rhx_gis=user_rhx_gis, variables=variables) 
        x_instagram_gis = hashlib.md5(x_instagram_gis.encode()).hexdigest()
        print(x_instagram_gis)
        session.headers['x-instagram-gis'] = x_instagram_gis
    apiData = getAPIData(apiurl)
    apiData = apiData['data']['user']['edge_owner_to_timeline_media']
    return apiData['page_info']['end_cursor'], apiData['edges']

def downloadPostByType(dataNode, time, typename):
    try:
        if typename == 'GraphImage':
            downloadFile(dataNode['display_url'], '{0}.jpg'.format(time))
        else:
            shortcode = dataNode['shortcode']
            data = getWebData(BASE_URL + 'p/' + shortcode)
            if typename == 'GraphVideo':
                downloadFile(data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['video_url'], '{0}.mp4'.format(time))
            elif typename == 'GraphSidecar':
                sidecarEdges = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
                for i in range(len(sidecarEdges)):
                    if sidecarEdges[i]['node']['__typename'] == 'GraphImage':
                        downloadFile(sidecarEdges[i]['node']['display_url'], '{0}-{1}.jpg'.format(time, i))
                    elif sidecarEdges[i]['node']['__typename'] == 'GraphVideo':
                        downloadFile(sidecarEdges[i]['node']['video_url'], '{0}-{1}.mp4'.format(time, i))
    except Exception as e:
        print(e)
        print('Error, retry download')
        downloadPostByType(dataNode, time, typename)

def downloadPosts(username, user_id, user_count, user_rhx_gis=''):
    '''
        This will download posts
    '''
    latestPost = getLatestFilename()
    end_cursor = ''
    counter = 0
    if not os.path.exists(username):
        os.mkdir(username)
        os.chdir(username)
        while counter < user_count:
            endcursor, dataEdges = getDataEdges(user_id, end_cursor, user_rhx_gis)
            counter += NUM
            i = len(dataEdges) - 1
            while i >= 0:
                time = dataEdges[i]['node']['taken_at_timestamp']
                time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
                print('Downloading post at {0}'.format(time))
                downloadPostByType(dataEdges[i]['node'], time, dataEdges[i]['node']['__typename'])
                i -= 1
    else:
        os.chdir(username)
        while counter < user_count:
            end_cursor, dataEdge = getDataEdges(user_id, end_cursor, user_rhx_gis)
            counter += NUM
            latestTime = getLatestFilename()
            i = 0
            while i < len(dataEdges):
                time = dataEdges[i]['node']['taken_at_timestamp']
                time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
                if time > latestTime:
                    print('Downloading post at {0}'.format(time))
                    downloadPostsByType(dataEdge[i]['node'], time, dataEdges[i]['node']['__typename'])
                    i += 1
                else:
                    return

def downloadStories(username, user_id):
    '''
        This will download stories
    '''
    latestStory = getLatestFilename(stories=True)
    url = STORIES_API_URL.format(query_hash=STORIES_QUERY_HASH, id=user_id)
    r2 = session.get(url)
    data = json.loads(r2.text)
    if len(data['data']['reels_media']) > 0:
        for i in data['data']['reels_media'][0]['items']:
            time = i['taken_at_timestamp']
            time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
            if i['__typename'] == 'GraphStoryVideo':
                fileformat = '.mp4'
                url = i['video_resources'][-1]['src']
            else:
                fileformat = '.jpg'
                url = i['display_url']
            filename = time + '--stories' + fileformat
            if filename > latestStory:
                print('Downloading stories at {0}'.format(time))
                downloadFile(url,filename)

initialiseDB()
updateBaseHeader()
promptBasicMode()
           



