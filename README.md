# TwitchRCE
Twitch Chat Bot that allows viewers to run arbitrary code on broadcasters machine

## Commands | [TwitchIO Commands Docs](https://twitchio.dev/en/latest/exts/commands.html)
* `!exec` OR `!cmd` - *Runs any bash command (if it's in the allow list)*
* `!killmyshell` - *Finds open terminal windows and closes the most recently opened*
* `!add_channel_vip` - *Adds user to an available vip slot*

## Event Subscriptions | [TwitchIO EventSub Docs](https://twitchio.dev/en/latest/exts/eventsub.html)
* `event_eventsub_notification_follow`
* `event_eventsub_notification_cheer`
* `event_eventsub_notification_subscription`
* `event_eventsub_notification_raid`
* `event_eventsub_notification_hypetrain_begin`
* `event_eventsub_notification_hypetrain_end`
* `event_eventsub_notification_stream_start`
* `event_eventsub_notification_stream_end`
* `event_eventsub_notification_channel_shoutout_create`
* `event_eventsub_notification_channel_shoutout_receive`

### Environment Variables
* [Create an `.env` file](https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1) with your TWITCH API tokens and your channel name to use this script:

| env key             | type   | env value                                                              |
|---------------------|--------|------------------------------------------------------------------------|
| CLIENT_ID=          | string | *[From developer application](https://dev.twitch.tv/console/apps)*     |
| CLIENT_SECRET=      | string | *[From developer application](https://dev.twitch.tv/console/apps)*     |
| AUTH_URI_PORT=      | int    | 3000                                                                   |
| EVENTSUB_URI_PORT=  | int    | 8080                                                                   |
| APP_TOKEN=          | string | *[Get an access token](https://dev.twitch.tv/docs/cli/token-command/)* |     
| USER_TOKEN=         | string | *[Get an access token](https://dev.twitch.tv/docs/cli/token-command/)* |
| INITIAL_CHANNELS=   | string | channel name                                                           |

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
CMD_ALLOW_LIST = ['aux', 'cat', 'cd', 'echo', 'grep', 'id', 'ipconfig', 'ls', 'netstat', 'nslookup', 'pwd', 'top',
                  'who', 'whoami']
```

Expect some kind of malicious code to make it through if you leave the RCECog enabled! :)
