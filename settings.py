from decouple import config

CLIENT_ID = config('CLIENT_ID')
CLIENT_SECRET = config('CLIENT_SECRET')

VIRUS_TOTAL_API_KEY = config('VIRUS_TOTAL_API_KEY')
BARD_SECURE_1PSID = config('BARD_SECURE_1PSID')
BARD_SECURE_1PSIDTS = config('BARD_SECURE_1PSIDTS')

DATABASE_FILENAME = config('DATABASE_FILENAME', default='twitchrce.sqlite')

AUTH_URI_PORT = int(config('AUTH_URI_PORT', default=3000))
EVENTSUB_URI_PORT = int(config('EVENTSUB_URI_PORT', default=8080))

BOT_USERNAME = config('BOT_USERNAME')
BOT_JOIN_CHANNEL = config('BOT_JOIN_CHANNEL')
MAX_VIP_SLOTS = int(config('MAX_VIP_SLOTS', default=10))

CMD_ALLOW_LIST = ['aux', 'cat', 'echo', 'grep', 'id', 'ifconfig', 'ls', 'netstat', 'nslookup', 'ping', 'pwd', 'which', 'who', 'whoami']
