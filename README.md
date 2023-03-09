# TwitchRCE
Twitch Chat Bot that allows viewers to run arbitrary code on broadcasters machine

## Commands | [TwitchIO Commands Docs](https://twitchio.dev/en/latest/exts/commands.html)
* `!exec <command>` OR `!cmd <command>` - *Runs any bash command (if it's in the allow list)*
* `!add_channel_vip` - *Adds user to an available vip slot*
* `!hello` - *Says hello to author*
* `!raids <@username>` - *displays how many raids you've received from the user*
* `!shoutout <@username>` OR `!so <@username>` - *Sends a shoutout announcement message*

## Redemptions | [Managing Channel Point Rewards](https://help.twitch.tv/s/article/channel-points-guide?language=en_US#managing)
* `killmyshell` - *Finds open terminal windows and closes the most recently opened*

## Event Subscriptions | [TwitchIO EventSub Docs](https://twitchio.dev/en/latest/exts/eventsub.html)
| Event Type                          | Response                                     |
|-------------------------------------|----------------------------------------------|
| *follow*                            | Chat message                                 |
| *cheer*                             | Shoutout & Chat message                      |
| *subscription*                      | Shoutout & Chat message                      |
| *raid*                              | Shoutout & Chat message                      |
| *hypetrain_begin*                   | `**NOT IMPLEMENTED**`                        |
| *hypetrain_end*                     | `**NOT IMPLEMENTED**`                        |
| *stream_start*                      | Creates channel point rewards & Chat message |
| *stream_end*                        | Chat message                                 |
| *channel_shoutout_create*           | `**NOT IMPLEMENTED**`                        |
| *channel_shoutout_receive*          | `**NOT IMPLEMENTED**`                        |
| *channel_charity_campaign_donate*   | `**NOT IMPLEMENTED**`                        |
| *channel_charity_campaign_start*    | `**NOT IMPLEMENTED**`                        |
| *channel_charity_campaign_progress* | `**NOT IMPLEMENTED**`                        |
| *channel_charity_campaign_stop*     | `**NOT IMPLEMENTED**`                        |

### Environment Variables
* [Create an `.env` file](https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1) with your TWITCH API tokens and your channel name to use this script:

| env key            | type   | env value                                                          |
|--------------------|--------|--------------------------------------------------------------------|
| CLIENT_ID=         | string | *[From developer application](https://dev.twitch.tv/console/apps)* |
| CLIENT_SECRET=     | string | *[From developer application](https://dev.twitch.tv/console/apps)* |
| AUTH_URI_PORT=     | int    | 3000                                                               |
| EVENTSUB_URI_PORT= | int    | 8080                                                               |
| BOT_USERNAME=      | string | msec_bot                                                           |
| MAX_VIP_SLOTS=     | int    | 20                                                                 |

### Ngrok Config | [Ngrok Tunnel Definition Docs](https://ngrok.com/docs/ngrok-agent/config#tunnel-definitions)
* Add a `auth` and `eventsub` tunnel configuration(s) to your `ngrok.yml` file

```
tunnels:
  auth:
    addr: 3000
    proto: http
  eventsub:
    addr: 8080
    proto: http
```

### RCECog Allow List

The RCECog **attempts** to limit commands to a allow list so update the `settings.py` file to include a comma separated list of linux binaries that you will allow to run:
```
CMD_ALLOW_LIST = ['aux', 'cat', 'echo', 'grep', 'id', 'ifconfig', 'ls', 'netstat', 'nslookup', 'ping', 'pwd', 'which', 'who', 'whoami']
```

Expect some kind of malicious code to make it through if you leave the RCECog enabled! :)
