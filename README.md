# TwitchRCE
Twitch Chat Bot that allows viewers to run arbitrary code on broadcasters machine

## Commands | [TwitchIO Commands Docs](https://twitchio.dev/en/latest/exts/commands.html)
| Command                                             | Outcome                                                                                                                                                 | Condition           |
|-----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|
| `!hello`                                            | Says hello to author                                                                                                                                    | -                   |
| `!lurk`                                             | let the streamer know you're lurking                                                                                                                    | -                   |
| `!raids <@username>`                                | displays how many raids you've received from the user                                                                                                   | -                   |
| `!shoutout <@username>` <br/>_OR_ `!so <@username>` | Sends a shoutout announcement message                                                                                                                   | -                   |
| `!redemptions`                                      | Creates custom channel point rewards _(The same outcome as stream_start event just incase the bot wasn't active when the stream_start event occurred.)_ | -                   |
| `!add_channel_subs`                                 | Adds current channel subscribers to sub database table                                                                                                  | -                   |
| `!kill_everyone` `**NOT IMPLEMENTED**`              | invoke skynet                                                                                                                                           | John Connor is dead |
| `!virustotal <hash>` `**NOT IMPLEMENTED**`          | lookup a hash on virustotal                                                                                                                             | -                   |
| `!chatgpt <query>` `**NOT IMPLEMENTED**`            | ask chatgpt a question                                                                                                                                  | -                   |

### RCE Cog Commands
| Command                                      | Outcome                                                               | Condition                                                                               |
|----------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `!exec <command>` <br/>_OR_ `!cmd <command>` | Runs any bash command (if it's in the allow list)                     | Streaming in `Science & Technology` <br/>_OR_ `Software and Game Development` category. |
| `killmyshell` _**[REDEMPTION]**_             | Closes the last opened [qterminal](https://github.com/lxqt/qterminal) | A qterminal window is already open                                                      |

### VIP Cog Commands
| Command                              | Outcome                                                     | Condition                                                                                        |
|--------------------------------------|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `add_channel_vip` _**[REDEMPTION]**_ | Adds the redeemer as a VIP, and auto-fulfill the redemption | Broadcaster has spare VIP slots <br/>_AND_ Redeemer does not have a `Moderator` or a `VIP` role. |

### User Specific Commands
| Command    | Outcome                                                                          | Condition |
|------------|----------------------------------------------------------------------------------|-----------|
| `!ohlook`  | Sends a shoutout to [StairsTheTrashman](https://www.twitch.tv/stairsthetrashman) |           |

## Redemptions | [Managing Channel Point Rewards](https://help.twitch.tv/s/article/channel-points-guide?language=en_US#managing)
| Reward          | Cost  | Outcome                                                                                                                                                                                                                 | Condition                                                                                        |
|-----------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `Kill My Shell` | 6666  | Immediately closes the last [qterminal](https://github.com/lxqt/qterminal) window that was opened without warning! Confirms success in a chat announcement.                                                             | Streaming in `Science & Technology` <br/>_OR_ `Software and Game Development` category.          |
| `VIP`           | 80085 | If you have spare VIP slots it will automatically grant the redeemer the VIP role. VIPs have the ability to equip a special chat badge and bypass the chat limit in slow mode! Confirms success in a chat announcement. | Broadcaster has spare VIP slots <br/>_AND_ Redeemer does not have a `Moderator` or a `VIP` role. |

## Publish Subscriptions | [TwitchIO PubSub Docs](https://twitchio.dev/en/latest/exts/pubsub.html)
| Topic                                                | Response                                                                                                                             |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| *pubsub.channel_points(user_token)[user_channel_id]* | This topic listens for channel point redemptions on the given channel. This topic dispatches the pubsub_channel_points client event. |


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

| env key              | type   | env value                                                                                  |
|----------------------|--------|--------------------------------------------------------------------------------------------|
| CLIENT_ID=           | string | *[From Twitch Developer Application](https://dev.twitch.tv/console/apps)*                  |
| CLIENT_SECRET=       | string | *[From Twitch Developer Application](https://dev.twitch.tv/console/apps)*                  |
| VIRUS_TOTAL_API_KEY= | string | *[From VirusTotal Community](https://developers.virustotal.com/reference/getting-started)* |
| AUTH_URI_PORT=       | int    | 3000                                                                                       |
| EVENTSUB_URI_PORT=   | int    | 8080                                                                                       |
| BOT_USERNAME=        | string | msec_bot                                                                                   |
| BOT_JOIN_CHANNEL=    | string | msec                                                                                       |
| MAX_VIP_SLOTS=       | int    | 20                                                                                         |

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
