from decouple import config

TWITCH_CLIENT_ID = config('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = config('TWITCH_CLIENT_SECRET')

TWITCH_CHAT_OAUTH = config('TWITCH_CHAT_OAUTH')

ACCESS_TOKEN = config('ACCESS_TOKEN')
REFRESH_TOKEN = config('REFRESH_TOKEN')

BROADCASTER_ID = int(config('BROADCASTER_ID'))
CHANNEL_NAME = config('CHANNEL_NAME')

CMD_ALLOW_LIST = ['aux', 'cat', 'cd', 'echo', 'grep', 'id', 'ipconfig', 'ls', 'man', 'netstat', 'nslookup', 'pwd',
                  'top', 'who', 'whoami']
