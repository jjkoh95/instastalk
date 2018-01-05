#import urllib
from bs4 import BeautifulSoup
import json
import datetime
import os
import sys
import requests

# js to py
null = None
true = True
false = False

URL = 'https://www.instagram.com/'
QUERYID = 17888483320059182
APIURL = URL + 'graphql/query/?query_id={0}&variables=%7B"id"%3A"{1}"%2C"first"%3A{2}%2C"after"%3A"{3}"%7D'
TARGETID = 0
TOTALPOSTS = 0
NUM = 100


def getWebData(url):
	response = requests.get(url)
	response = response.text

	#response = urllib.request.urlopen(url)
	#response = response.read()
	#response = response.decode('utf-8')

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
	return fileList[0]


def getAPIData(url):
	apiData = requests.get(url)
	apiData = apiData.text

	#apiData = urllib.request.urlopen(url)
	#apiData = apiData.read()
	#apiData = apiData.decode('utf-8')
	
	return json.loads(apiData)


def getIDandTotalPosts():
	webData = getWebData(URL + TARGETUSER)
	global TARGETID
	TARGETID = webData['entry_data']['ProfilePage'][0]['user']['id']
	global TOTALPOSTS
	TOTALPOSTS = webData['entry_data']['ProfilePage'][0]['user']['media']['count']


def getDataEdges(end_cursor):
	apiurl = APIURL.format(QUERYID, TARGETID, NUM, end_cursor)
	apiData = getAPIData(apiurl)
	apiData = apiData['data']['user']['edge_owner_to_timeline_media']
	return apiData['page_info']['end_cursor'], apiData['edges']


def downloadPostByType(dataNode, time, typename):
	try:
		if typename == "GraphImage":
			urllib.request.urlretrieve(dataNode['display_url'], '{0}.jpg'.format(time))
		else:
			shortcode = dataNode['shortcode']
			# webdata
			data = getWebData(URL + 'p/' + shortcode)
			if typename == "GraphVideo":
				urllib.request.urlretrieve( \
					data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['video_url'], \
					'{0}.mp4'.format(time))	
			elif typename == "GraphSidecar":
				sidecarEdges = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
				for i in range(len(sidecarEdges)):
					if sidecarEdges[i]['node']['__typename'] == 'GraphImage':
						urllib.request.urlretrieve(sidecarEdges[i]['node']['display_url'], '{0}-{1}.jpg'.format(time,i))
					elif sidecarEdges[i]['node']['__typename'] == 'GraphVideo':
						urllib.request.urlretrieve(sidecarEdges[i]['node']['video_url'], '{0}-{1}.mp4'.format(time,i))
	except Exception as e:
		print(e)
		print("error, retrying")
		return downloadPostByType(dataNode, time, typename)

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
	global TARGETUSER
	TARGETUSER = sys.argv[1]
	main()






