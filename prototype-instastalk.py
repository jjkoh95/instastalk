'''
	Prototype instastalk
	This program will automate to download all posts of TARGETUSER
'''
import urllib
from bs4 import BeautifulSoup
import json
import datetime
import os

URL = "https://www.instagram.com/"
# ENTER TARGETUSER
TARGETUSER = ""
TARGETURL = URL + TARGETUSER
AJAXURL = URL + 'graphql/query/?query_id={0}&variables=%7B"id"%3A"{1}"%2C"first"%3A{2}%2C"after"%3A"{3}"%7D'
# format(query id, user id, number of posts to retrieve, end cursor)

# id can be retrieved easily with url

# query_id is fixed (for now?)
QUERY_ID = 17888483320059182

null = None
true = True
false = False

response = urllib.request.urlopen(TARGETURL)
response = response.read()
response = response.decode('utf-8')

# BeautifulSoup instance
bs = BeautifulSoup(response,'html.parser')

scripts = bs.find_all("script")
data = None
for i in range(len(scripts)):
	stringScript = str(scripts[i])
	# this is where instagram stored its data
	found = stringScript.find("window._sharedData")
	if found != -1:
		# parse
		startIndex = stringScript.find("{")
		endIndex = stringScript.find("</script>") - 1
		stringData = stringScript[startIndex:endIndex]
		data = json.loads(stringData)
		break

# data.keys()
# ['activity_counts', 'config', 'country_code', 
# 'language_code', 'locale', 'entry_data', 'gatekeepers', 
# 'qe', 'hostname', 'display_properties_server_guess', 
# 'environment_switcher_visible_server_guess', 'platform', 
# 'nonce', 'zero_data', 'rollout_hash', 'probably_has_app', 'show_app_install']

# to get ID: data['entry_data']['ProfilePage'][0]['user']['id']
TARGETID = data['entry_data']['ProfilePage'][0]['user']['id']

totalPosts = data['entry_data']['ProfilePage'][0]['user']['media']['count']

# end_cursor = data['entry_data']['ProfilePage'][0]['user']['id']['media']['page_info']['end_cursor']
# end_cursor to get data AFTER what we have


# we can easily get a single image using the ajax query
# however, we need to take care of video and GraphSidecar which is a post which multiple images/videos
AJAXURL = AJAXURL.format(QUERY_ID, TARGETID, totalPosts, "")
queryData = urllib.request.urlopen(AJAXURL)
queryData = queryData.read()
queryData = queryData.decode('utf-8')
queryData = json.loads(queryData)

dataEdges = queryData['data']['user']['edge_owner_to_timeline_media']['edges']

# make a directory to store all the images and videos
if os.path.exists(TARGETUSER):
	os.chdir(TARGETUSER)
else:
	os.mkdir(TARGETUSER)
	os.chdir(TARGETUSER)

for i in range(len(dataEdges)):
	time = int(dataEdges[i]['node']['taken_at_timestamp'])
	time = datetime.datetime.fromtimestamp(time).strftime('%Y-%m-%d--%H-%M-%S')
	dataType = dataEdges[i]['node']['__typename']
	print("{0} / {1}".format(i+1,len(dataEdges)))
	if  dataType == "GraphImage":
		urllib.request.urlretrieve(dataEdges[i]['node']['display_url'],"{0}.jpg".format(time))


	elif dataType == "GraphSidecar":
		# GraphSidecar - 
		# 	data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
		#		[i]['node']['display_url']
		#		[i]['node']['video_url']
		# 	for i = 0 to length

		shortcode = dataEdges[i]['node']['shortcode']
		graphUrl = URL + "p/" + shortcode
		r = urllib.request.urlopen(graphUrl)
		r = r.read()
		r = r.decode('utf-8')
		r = BeautifulSoup(r,'html.parser')
		r = r.find_all('script')
		temp = None
		for i in range(len(r)):
			rTemp = str(r[i])
			# this is where instagram stored its data
			found = rTemp.find("window._sharedData")
			if found != -1:
				# parse
				startIndex = rTemp.find("{")
				endIndex = rTemp.find("</script>") - 1
				rData = rTemp[startIndex:endIndex]
				temp = json.loads(rData)
				break

		imageEdges = temp['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
		for i in range(len(imageEdges)):
			if imageEdges[i]['node']['__typename'] == 'GraphImage':
				urllib.request.urlretrieve(imageEdges[i]['node']['display_url'],"{0}-{1}.jpg".format(time,i))
			elif imageEdges[i]['node']['__typename'] == 'GraphVideo':
				urllib.request.urlretrieve(imageEdges[i]['node']['video_url'],"{0}-{1}.mp4".format(time,i))
	
	elif dataType == "GraphVideo":
		# GraphVideo -
		# data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
		shortcode = dataEdges[i]['node']['shortcode']
		graphUrl = URL + "p/" + shortcode
		r = urllib.request.urlopen(graphUrl)
		r = r.read()
		r = r.decode('utf-8')
		r = BeautifulSoup(r,'html.parser')
		r = r.find_all('script')
		temp = None
		for i in range(len(r)):
			rTemp = str(r[i])
			# this is where instagram stored its data
			found = rTemp.find("window._sharedData")
			if found != -1:
				# parse
				startIndex = rTemp.find("{")
				endIndex = rTemp.find("</script>") - 1
				rData = rTemp[startIndex:endIndex]
				temp = json.loads(rData)
				break
		imageEdges = temp['entry_data']['PostPage'][0]['graphql']['shortcode_media']
		urllib.request.urlretrieve(imageEdges['video_url'],"{0}.mp4".format(time))

