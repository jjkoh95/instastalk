BASE_URL = "https://www.instagram.com/"
URL = 'https://www.instagram.com'
LOGIN_URL = BASE_URL + 'accounts/login/ajax/'
LOGOUT_URL = BASE_URL + 'accounts/logout/'
API_URL = BASE_URL + 'graphql/query/?' + \
    'query_hash={query_hash}&' + \
    'variables=%7B"id"%3A"{id}"%2C"first"%3A{first}%2C"after"%3A"{after}"%7D'
TARGETID = 0
TOTALPOSTS = 0
NUM = 12
QUERY_HASH = '42323d64886122307be10013ad2dcc44'
STORIES_QUERY_HASH = '45246d3fe16ccc6577e0bd297a5db1ab'
STORIES_API_URL = BASE_URL + 'graphql/query/?' + \
                  'query_hash={query_hash}&' + \
                  'variables=%7B%22' + \
                  'reel_ids%22%3A%5B%22{id}%22%5D%2C%22' + \
                  'tag_names%22%3A%5B%5D%2C%22' + \
                  'location_ids%22%3A%5B%5D%2C%22' + \
                  'highlight_reel_ids%22%3A%5B%5D%2C%22' + \
                  'precomposed_overlay%22%3Afalse%7D'
# make my life easy
# think python might already handle this
null = None
true = True
false = False
