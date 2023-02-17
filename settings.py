from decouple import config

CLIENT_ID = config('CLIENT_ID')
CLIENT_SECRET = config('CLIENT_SECRET')

AUTH_URI_PORT = int(config('AUTH_URI_PORT', default=3000))
EVENTSUB_URI_PORT = int(config('EVENTSUB_URI_PORT', default=8080))

APP_TOKEN = config('APP_TOKEN')
USER_TOKEN = config('USER_TOKEN')

INITIAL_CHANNELS = config('INITIAL_CHANNELS').split(',')

CMD_ALLOW_LIST = ['aux', 'cat', 'cd', 'echo', 'grep', 'id', 'ifconfig', 'ls', 'man', 'netstat', 'nslookup', 'pwd',
                  'top', 'who', 'whoami']
