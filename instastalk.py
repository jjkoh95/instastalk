import urllib
from bs4 import BeautifulSoup
import json
import datetime
import os
import sys

# js to py
null = None
true = True
false = False

# CONSTANT
URL = 'https://www.instagram.com/'
QUERYID = 17888483320059182
AJAXURL = URL + 'graphql/query/?query_id={0}&variables=%7B"id"%3A"{1}"%2C"first"%3A{2}%2C"after"%3A"{3}"%7D'


def getWebData(url):
	response = urllib.request.urlopen(url)
	response = response.read()
	response = response.decode('utf-8')

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
	fl = sorted(fileList, reverse=True)
	# can use comparison directly
	# >>> fileList[1] < fileList[0]
	# >>> True
	return fl[0]

def getAPIData(url):
	apiData = urllib.request.urlopen(url)
	apiData = apiData.read()
	apiData = apiData.decode('utf-8')
	return json.loads(apiData)

def getDataEdges():
	webData = getWebData(URL + TARGETUSER)
	TARGETID = webData['entry_data']['ProfilePage'][0]['user']['id']
	totalPosts = webData['entry_data']['ProfilePage'][0]['user']['media']['count']
	global AJAXURL
	AJAXURL = AJAXURL.format(QUERYID, TARGETID, totalPosts, "")
	apiData = getAPIData(AJAXURL)
	return apiData['data']['user']['edge_owner_to_timeline_media']['edges']

def downloadPostByType(dataNode, time, typename):
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

def main():
	dataEdges = getDataEdges()
	if not os.path.exists(TARGETUSER):
		# if does not exist, download all from the beginning
		os.mkdir(TARGETUSER)
		os.chdir(TARGETUSER)
		i = len(dataEdges) - 1
		while i >= 0:
			time = dataEdges[i]['node']['taken_at_timestamp']
			time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
			try:
				print("downloading post at {0}".format(time))
				downloadPostByType(dataEdges[i]['node'], time, dataEdges[i]['node']['__typename'])
				i -= 1
			except Exception:
				print("Error, retrying")
	else:
		# else UPDATE as necessary
		os.chdir(TARGETUSER)
		latestTime = getLatestFilename()
		i = 0
		while i < len(dataEdges):
			time = dataEdges[i]['node']['taken_at_timestamp']
			time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
			if time > latestTime:
				print("downloading post at {0}".format(time))
				try:
					downloadPostByType(dataEdges[i]['node'], time, dataEdges[i]['node']['__typename'])
					i += 1
				except Exception:
					print("Incomplete Read, retrying")
			else:
				return

if __name__ == '__main__':
	global TARGETUSER
	TARGETUSER = sys.argv[1]
	main()











