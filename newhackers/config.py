import redis

rdb = redis.Redis(db=8)

HN = "https://news.ycombinator.com/"
HN_LOGIN = HN + "newslogin?whence=news"
HN_LOGIN_POST = HN + 'y'
CACHE_INTERVAL = 60  # seconds
STORIES_PER_PAGE = 30
