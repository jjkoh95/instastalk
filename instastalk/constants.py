QUERY_HASH = '42323d64886122307be10013ad2dcc44'
STORIES_QUERY_HASH = '45246d3fe16ccc6577e0bd297a5db1ab'
SHORTCODE_QUERY_HASH = 'fead941d698dc1160a298ba7bec277ac'

BASE_URL = "https://www.instagram.com"
LOGIN_REFERER = f'{BASE_URL}/accounts/login'
LOGIN_URL = f'{BASE_URL}/accounts/login/ajax/'
LOGOUT_URL = f'{BASE_URL}/accounts/logout/'
QUERY_URL = f'{BASE_URL}/graphql/query/'

QUERY_POST_URL = f'{QUERY_URL}?' + \
    f'query_hash={QUERY_HASH}&' + \
    'variables=%7B"id"%3A"{id}"%2C"first"%3A{first}%2C"after"%3A"{after}"%7D'

SHORTCODE_URL = f'{QUERY_URL}?' + \
    f'query_hash={SHORTCODE_QUERY_HASH}&' + \
    'variables=%7B"shortcode"%3A"{shortcode}"%2C"child_comment_count"%3A{child_comment_count}%2C"fetch_comment_count"%3A{fetch_comment_count}%2C"parent_comment_count"%3A{parent_comment_count}%2C"has_threaded_comments"%3A{has_threaded_comments}%7D'

STORIES_API_URL = BASE_URL + '/graphql/query/?' + \
    f'query_hash={STORIES_QUERY_HASH}&' + \
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
