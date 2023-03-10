# TwitchRCE
Twitch Chat Bot that allows viewers to run arbitrary code on broadcasters machine

## Commands | [TwitchIO Commands Docs](https://twitchio.dev/en/latest/exts/commands.html)
| Command                                             | Outcome                                                                                                                                                 |
|-----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| `!hello`                                            | Says hello to author                                                                                                                                    |
| `!exec <command>` <br/>_OR_ `!cmd <command>`        | Runs any bash command (if it's in the allow list)                                                                                                       |
| `!raids <@username>`                                | displays how many raids you've received from the user                                                                                                   |
| `!shoutout <@username>` <br/>_OR_ `!so <@username>` | Sends a shoutout announcement message                                                                                                                   |
| `!redemptions`                                      | Creates custom channel point rewards _(The same outcome as stream_start event just incase the bot wasn't active when the stream_start event occurred.)_ |

### User Specific Commands
| Command                                             | Outcome                               |
|-----------------------------------------------------|---------------------------------------|
| `!ohlook`                                           | Sends a shoutout to StairsTheTrashman |

## Redemptions | [Managing Channel Point Rewards](https://help.twitch.tv/s/article/channel-points-guide?language=en_US#managing)
| Reward          | Cost  | Outcome                                                                                                                                                                                                                 |
|-----------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Kill My Shell` | 6666  | Immediately closes the last terminal window that was opened without warning! Confirms success in a chat announcement.                                                                                                   |
| `VIP`           | 80085 | If you have spare VIP slots it will automatically grant the redeemer the VIP role. VIPs have the ability to equip a special chat badge and bypass the chat limit in slow mode! Confirms success in a chat announcement. |

## Event Subscriptions | [TwitchIO EventSub Docs](https://twitchio.dev/en/latest/exts/eventsub.html)
| Event Type                          | Response                                              |
|-------------------------------------|-------------------------------------------------------|
| *follow*                            | Chat message                                          |
| *cheer*                             | Shoutout & Chat message                               |
| *subscription*                      | Shoutout & Chat message                               |
| *raid*                              | Shoutout & Chat message                               |
| *hypetrain_begin*                   | `**NOT IMPLEMENTED**`                                 |
| *hypetrain_end*                     | `**NOT IMPLEMENTED**`                                 |
| *stream_start*                      | Creates custom channel point rewards & Chat message   |
| *stream_end*                        | Removes custom channel point rewards & Chat message   |
| *channel_shoutout_create*           | `**NOT IMPLEMENTED**`                                 |
| *channel_shoutout_receive*          | `**NOT IMPLEMENTED**`                                 |
| *channel_charity_campaign_donate*   | `**NOT IMPLEMENTED**`                                 |
| *channel_charity_campaign_start*    | `**NOT IMPLEMENTED**`                                 |
| *channel_charity_campaign_progress* | `**NOT IMPLEMENTED**`                                 |
| *channel_charity_campaign_stop*     | `**NOT IMPLEMENTED**`                                 |

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
