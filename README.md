# TwitchRCE
Twitch Chat Bot that allows viewers to run arbitrary code on broadcasters machine

## Commands
* !exec OR !cmd - *Runs any bash command (if it's in the allow list)*
* !killmyshell - *Finds open terminal windows and closes the most recently opened*

### Environment Variables
Update the .env file with your IRC and TWITCH API tokens, and your broadcaster ID to use this script:
* CLIENT_ID=XXXXXX
* CLIENT_SECRET=XXXXXX
* CHAT_OAUTH=XXXXXX
* CLIENT_ID=XXXXXX
* ACCESS_TOKEN=XXXXXX
* REFRESH_TOKEN=XXXXXX
* BROADCASTER_ID=XXXXXX

Comma separated list of linux binaries that you will allow to run:
* CMD_ALLOW_LIST = ['aux', 'cat', 'cd', 'echo', 'grep', 'id', 'ipconfig', 'ls', 'netstat', 'nslookup', 'pwd', 'top',
                  'who', 'whoami']
