from decouple import config

TWITCH_CLIENT_ID = config('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = config('TWITCH_CLIENT_SECRET')

TWITCH_CHAT_OAUTH = config('TWITCH_CHAT_OAUTH')

ACCESS_TOKEN = config('ACCESS_TOKEN')
REFRESH_TOKEN = config('REFRESH_TOKEN')

BROADCASTER_ID = int(config('BROADCASTER_ID'))

CMD_ALLOW_LIST = ['id', 'whoami', 'echo', 'ipconfig', 'cd', 'ls', 'cat', 'netstat', 'nslookup', 'aux', 'grep']
CMD_REGEX = r"^[a-zA-Z]+(?!=\s)"
