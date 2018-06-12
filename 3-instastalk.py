import requests
from bs4 import BeautifulSoup
import json
import datetime
import os
import sys
import getpass

BASE_URL = "https://www.instagram.com/"
LOGIN_URL = BASE_URL + 'accounts/login/ajax/'
LOGOUT_URL = BASE_URL + 'accounts/logout/'
API_URL = BASE_URL + 'graphql/query/?' + \
	      'query_hash={query_hash}&' + \
	      'variables=%7B"id"%3A"{id}"%2C"first"%3A{first}%2C"after"%3A"{after}"%7D'
STORIES_API_URL = BASE_URL + 'graphql/query/?' + \
                  'query_hash={query_hash}&' + \
                  'variables=%7B%22reel_ids%22%3A%5B%22{id}%22%5D%2C%22' + \
                  'tag_names%22%3A%5B%5D%2C%22location_ids%22%3A%5B%5D%2C%22highlight_reel_ids%22%3A%5B%5D%2C%22precomposed_overlay%22%3Afalse%7D'
STORIES_QUERY_HASH = '45246d3fe16ccc6577e0bd297a5db1ab'
TARGETID = 0
TOTALPOSTS = 0
NUM = 12
QUERY_HASH = '42323d64886122307be10013ad2dcc44'
null = None
true = True
false = False

session = requests.session()
session.headers = {}
session.headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'
session.headers['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
session.headers['accept-encoding'] = 'gzip, deflate, br'
session.headers['language'] = 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6'
session.headers['cache-control'] = 'max-age=0'
session.headers['content-type'] = 'application/x-www-form-urlencoded'
session.cookies.set('ig_pr','1')

def cookiesToDict(c):
    '''
        c : cookies
    '''
    c = c.replace('Path=/, ', '')
    c = c.replace('Path=/; ', '')
    c = c.replace('Secure, ', '')
    pairs = c.split('; ')
    dic = {}
    #print(pairs)
    for i in range(len(pairs)):
        eachPair = pairs[i].split('=')
        dic[eachPair[0]] = eachPair[1]
    return dic

def updateBaseHeader():
    '''
        update basic header and cookie 
    '''
    r = session.get(BASE_URL)
    # set-cookie from response header 
    set_cookies = r.headers['set-cookie']
    set_cookies = cookiesToDict(set_cookies)
    session.headers['x-csrftoken'] = set_cookies['csrftoken']
   
def login():
    '''
        Login to get access to stories and private profiles
    '''
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    login_data = {'username': username, 'password': password, 'queryParams': {}}
    session.headers['referer'] = 'https://www.instagram.com/accounts/login/'
    session.headers['origin'] = 'https://www.instagram.com'
    session.headers['x-instagram-ajax'] = '1'
    #print(session.headers)
    #print(session.cookies)
    r = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
    #print(r.status_code)
    #print(r.text)
    response = json.loads(r.text)
    if response['authenticated']:
        print('Login successfully')
        return True
    else:
        print('Login failed')
        return False

def logout():
    '''
        Logout 
    '''
    logout_data = {'csrfmiddlewaretoken': session.headers['x-csrftoken']}
    r = session.post(LOGOUT_URL, data=logout_data, allow_redirects=True)
    if r.status_code == 200:
        print('Successfully logged out')

def downloadFile(url, filename):
	'''
		to download image or video from url
	'''
	r = session.get(url, stream=True)
	if r.status_code == 200:
	    with open(filename, 'wb') as f:
	        for chunk in r:
	            f.write(chunk)

def getLatestFilename():
	'''
		to get the latest file (prevent redundant download)
		assume that you are the directory
	'''
	fileList = os.listdir()
	fileList.sort(reverse=True)
	# can use comparison directly
	# >>> fileList[1] < fileList[0]
	# >>> True
	for i in range(len(fileList)):
		if 'stories' not in fileList[i]:
			print(fileList[i])
			return fileList[i]

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
			endIndex = stringResponse.find("</script>") - 1 # to remove the semicolon
			return json.loads(stringResponse[startIndex:endIndex])
	# if not found		
	return

def getAPIData(url):
	'''
		Parse JSON (API_URL)
	'''
	apiData = session.get(url)
	apiData = apiData.text

	return json.loads(apiData)


def getIDandTotalPosts():
    '''
    	To get ID and totalposts
    '''
    webData = getWebData(BASE_URL + TARGETUSER)
    global TARGETID
    TARGETID = webData['entry_data']['ProfilePage'][0]['graphql']['user']['id']
    global TOTALPOSTS
    TOTALPOSTS = webData['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['count']

def getDataEdges(end_cursor):
	'''
		get edges based on end_cursor (starting end_cursor is empty string '')
	'''
	apiurl = API_URL.format(query_hash=QUERY_HASH, id=TARGETID, first=NUM, after=end_cursor)
	apiData = getAPIData(apiurl)
	apiData = apiData['data']['user']['edge_owner_to_timeline_media']
	return apiData['page_info']['end_cursor'], apiData['edges']

def downloadPostByType(dataNode, time, typename):
	try:
		if typename == "GraphImage":
			# if it is GraphImage, easy, just download
			downloadFile(dataNode['display_url'], '{0}.jpg'.format(time))
		else:
			# need to get data from another web api
			shortcode = dataNode['shortcode']
			# webdata
			data = getWebData(BASE_URL + 'p/' + shortcode)
			if typename == "GraphVideo":
				downloadFile( \
					data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['video_url'], \
					'{0}.mp4'.format(time))	
			elif typename == "GraphSidecar":
				sidecarEdges = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
				for i in range(len(sidecarEdges)):
					if sidecarEdges[i]['node']['__typename'] == 'GraphImage':
						downloadFile(sidecarEdges[i]['node']['display_url'], '{0}-{1}.jpg'.format(time,i))
					elif sidecarEdges[i]['node']['__typename'] == 'GraphVideo':
						downloadFile(sidecarEdges[i]['node']['video_url'], '{0}-{1}.mp4'.format(time,i))
	except Exception as e:
		print(e)
		print("error, retrying")
		return downloadPostByType(dataNode, time, typename)

def getLatestStoriesFilename():
	'''
		to get the latest file (prevent redundant download)
		assume that you are the directory
	'''
	fileList = os.listdir()
	fileList.sort(reverse=True)
	# we get the latest stories
	for i in range(len(fileList)):
		if 'stories' in fileList[i]:
			return fileList[i]
	return '-999'

def downloadStories():
    '''
        This will download stories
    '''
    latestStory = getLatestStoriesFilename()
    url = STORIES_API_URL.format(query_hash=STORIES_QUERY_HASH, id=TARGETID)
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
                print('Downloading stories @{0}'.format(time))
                downloadFile(url,filename)

def main():
    getIDandTotalPosts()
    # TARGETID, TOTALPOSTS
    end_cursor = ""
    counter = 0
    if not os.path.exists(TARGETUSER):
        os.mkdir(TARGETUSER)
        os.chdir(TARGETUSER)
        while counter < TOTALPOSTS:
            end_cursor, dataEdges = getDataEdges(end_cursor)
            counter += NUM
            i = len(dataEdges) - 1
            while i >= 0:
                time = dataEdges[i]['node']['taken_at_timestamp']
                time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
                print("downloading post at {0}".format(time))
                downloadPostByType(dataEdges[i]['node'], time, dataEdges[i]['node']['__typename'])
                i -= 1
    else:
        os.chdir(TARGETUSER)
        while counter < TOTALPOSTS:
            end_cursor, dataEdges = getDataEdges(end_cursor)
            counter += NUM
            latestTime = getLatestFilename()
            i = 0
            while i < len(dataEdges):
                time = dataEdges[i]['node']['taken_at_timestamp']
                time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
                if time > latestTime:
                    print("downloading post at {0}".format(time))
                    downloadPostByType(dataEdges[i]['node'], time, dataEdges[i]['node']['__typename'])
                    i += 1
                else:
                    return

if __name__ == '__main__':
    updateBaseHeader()
    isLoggedIn = login()
    global TARGETUSER
    TARGETUSER = sys.argv[1]
    print("User: {0}".format(TARGETUSER))
    main()
    downloadStories()
    if isLoggedIn:
        logout()

