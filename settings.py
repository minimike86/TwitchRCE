from decouple import config

CLIENT_ID = config('CLIENT_ID')
CLIENT_SECRET = config('CLIENT_SECRET')

VIRUS_TOTAL_API_KEY = config('VIRUS_TOTAL_API_KEY')

BOT_USER_ID = config('BOT_USER_ID')

BOT_JOIN_CHANNEL = config('BOT_JOIN_CHANNEL')
BOT_JOIN_CHANNEL_ID = config('BOT_JOIN_CHANNEL_ID')

MAX_VIP_SLOTS = int(config('MAX_VIP_SLOTS', default=10))

CMD_ALLOW_LIST = ['aux', 'cat', 'echo', 'grep', 'id', 'ifconfig', 'ls', 'netstat', 'nslookup', 'ping', 'pwd', 'which', 'who', 'whoami']
