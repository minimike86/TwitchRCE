# TwitchRCE
Twitch Chat Bot that allows viewers to run arbitrary code on broadcasters machine

## Commands | [TwitchIO Commands Docs](https://twitchio.dev/en/latest/exts/commands.html)
<details><summary>Show/Hide Basic Commands</summary>

| Command                                                                                                                       | Outcome                                                                                                                                                 | Condition                                                 |
|-------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| `!hello`                                                                                                                      | Says hello to author                                                                                                                                    | -                                                         |
| `!lurk`                                                                                                                       | let the streamer know you're lurking                                                                                                                    | -                                                         |
| `!death_counter <+/-/+n/reset>` <br/>_OR_ `!death <+/-/+n/reset>` <br/>_OR_ `!ded <+/-/+n/reset>` <br/>_OR_ `!dc <+/-/reset>` | Increment / decrease death count for each +/- (or reset)                                                                                                | -                                                         |
| `!raids <@username>`                                                                                                          | displays how many raids you've received from the user                                                                                                   | -                                                         |
| `!shoutout <@username>` <br/>_OR_ `!so <@username>`                                                                           | Sends a shoutout announcement message                                                                                                                   | -                                                         |
| `!redemptions`                                                                                                                | Creates custom channel point rewards _(The same outcome as stream_start event just incase the bot wasn't active when the stream_start event occurred.)_ | -                                                         |
| `!infosec_streams` <br/>_OR_ `!streams` <br/>_OR_ `!streams`                                                                  | Creates custom channel point rewards _(The same outcome as stream_start event just incase the bot wasn't active when the stream_start event occurred.)_ | -                                                         |
| `!add_channel_subs`                                                                                                           | Adds current channel subscribers to sub database table                                                                                                  | -                                                         |
| `!kill_everyone` `**NOT IMPLEMENTED**`                                                                                        | Invoke the bots inner skynet                                                                                                                            | John Connor is dead                                       |
| `!virustotal <hash>` <br/>_OR_ `!virustotal <url>`                                                                            | Lookup a hash or url report on virustotal                                                                                                               | 500 requests per day, and a rate of 4 requests per minute |
</details>

### RCE Cog Commands [DISABLED PENDING AWS MIGRATION]
<details><summary>Show/Hide RCE Cog Commands</summary>

| Command                                      | Outcome                                                               | Condition                                                                               |
|----------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `!exec <command>` <br/>_OR_ `!cmd <command>` | Runs any bash command (if it's in the allow list)                     | Streaming in `Science & Technology` <br/>_OR_ `Software and Game Development` category. |
| `killmyshell` _**[REDEMPTION]**_             | Closes the last opened [qterminal](https://github.com/lxqt/qterminal) | A qterminal window is already open                                                      |
</details>

### VIP Cog Commands [DISABLED PENDING AWS MIGRATION]
<details><summary>Show/Hide VIP Cog Commands</summary>

| Command                              | Outcome                                                     | Condition                                                                                        |
|--------------------------------------|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `add_channel_vip` _**[REDEMPTION]**_ | Adds the redeemer as a VIP, and auto-fulfill the redemption | Broadcaster has spare VIP slots <br/>_AND_ Redeemer does not have a `Moderator` or a `VIP` role. |
</details>

### User Specific Cog Commands [DISABLED PENDING AWS MIGRATION]
<details><summary>Show/Hide User Specific Cog Commands</summary>

| Command                                                        | Outcome                                 | Condition                             |
|----------------------------------------------------------------|-----------------------------------------|---------------------------------------|
| `stairs1` <br/>_OR_ `stairsthetrashman1` <br/>_OR_ `ohlook`    | Triggers a user specific sound command  | Author in `stairsthetrashman`, `msec` |
| `stairs2` <br/>_OR_ `stairsthetrashman2` <br/>_OR_ `because`   | Triggers a user specific sound command  | Author in `stairsthetrashman`, `msec` |
| `stairs3` <br/>_OR_ `stairsthetrashman3` <br/>_OR_ `sonofagun` | Triggers a user specific sound command  | Author in `stairsthetrashman`, `msec` |
| `lottie` <br/>_OR_ `lottiekins`                                | Triggers a user specific sound command  | Author in `lottiekins`, `msec`        |
</details>

### Sound Cog Commands [DISABLED PENDING AWS MIGRATION]
<details><summary>Show/Hide Sound Cog Commands</summary>

| Command         | Outcome                                                     | Condition |
|-----------------|-------------------------------------------------------------|-----------|
| `youtube <url>` | Fetches a video from youtube and plays the audio            | -         |
| `later`         | Plays "A few moments later" spongebob narrator sound clip   | -         |
| `ahfuck`        | Plays "I can't believe you've done this" sound clip         | -         |
| `wow`           | Plays "anime wow" meme sound clip                           | -         |
| `bruh`          | Plays "bruh" meme sound clip                                | -         |
| `dialup`        | Plays "dial up modem" sound clip                            | -         |
| `emodmg`        | Plays "emotional damage" meme sound clip                    | -         |
| `buzzer`        | Plays "family fortune fail buzzer" meme sound clip          | -         |
| `fbi`           | PLays "fbi open up" meme sound clip                         | -         |
| `friend`        | Plays "friend" inbetweeners sound clip                      | -         |
| `fthis`         | Plays "fuck this shit i'm out" meme sound clip              | -         |
| `gg`            | Plays "gg" team fortress meme sound clip                    | -         |
| `goforit`       | Plays "go for it" diddy kong racing sound clip              | -         |
| `hackerman`     | Plays "hackerman" meme sound clip                           | -         |
| `hellomf`       | Plays "hello mother f*cker" meme sound clip                 | -         |
| `hexy`          | Plays "hexy" meme sound clip                                | -         |
| `ignore`        | Plays "ignore" meme sound clip                              | -         |
| `wierd`         | Plays "god the internets weird" meme sound clip             | -         |
| `sellwife`      | Plays "i sell my wife for internet" meme sound clip         | -         |
| `heknew`        | Plays "at this moment he knew" meme sound clip              | -         |
| `kerb`          | Plays "kerb" meme sound clip                                | -         |
| `gothim`        | Plays "we got him" meme sound clip                          | -         |
| `leeroy`        | Plays "leeroooyyyyy jenkins" meme sound clip                | -         |
| `lies`          | Plays "lies on the internet" meme sound clip                | -         |
| `mgsalert`      | Plays "metal gear solid alert" meme sound clip              | -         |
| `hellothere`    | Plays "hello there" obi wan kenobi meme sound clip          | -         |
| `order66`       | Plays "execute order 66" general palpatine meme sound clip  | -         |
| `over9000`      | Plays "its over 9000" dragonball meme sound clip            | -         |
| `hackercrap`    | Plays "hate this hacker crap" jurrasic park meme sound clip | -         |
| `sadviolin`     | Plays "sad violin" meme sound clip                          | -         |
| `satan`         | Plays "satan, lucifer" meme sound clip                      | -         |
| `stepbro`       | Plays "what are you doing stepbro" meme sound clip          | -         |
| `surprise`      | Plays "surprise mother f*cker" meme sound clip              | -         |
| `tsdisconnect`  | Plays "teamspeak disconnect" meme sound clip                | -         |
| `trollolol`     | Plays "trollolol" meme sound clip                           | -         |
| `usbconnect`    | Plays "windows 10 usb connection" meme sound clip           | -         |
| `usbdisconnect` | Plays "windows 10 usb disconnect" meme sound clip           | -         |
| `victory`       | Plays "ff7 victory fanfare" meme sound clip                 | -         |
| `shutdown`      | Plays "windows shutdown" meme sound clip                    | -         |
| `wtfinternet`   | Plays "what is the internet" meme sound clip                | -         |
</details>

## Redemptions | [Managing Channel Point Rewards](https://help.twitch.tv/s/article/channel-points-guide?language=en_US#managing)
<details><summary>Show/Hide Channel Point Reward Events</summary>

| Reward          | Cost  | Outcome                                                                                                                                                                                                                 | Condition                                                                                        |
|-----------------|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `Kill My Shell` | 6666  | Immediately closes the last [qterminal](https://github.com/lxqt/qterminal) window that was opened without warning! Confirms success in a chat announcement.                                                             | Streaming in `Science & Technology` <br/>_OR_ `Software and Game Development` category.          |
| `VIP`           | 80085 | If you have spare VIP slots it will automatically grant the redeemer the VIP role. VIPs have the ability to equip a special chat badge and bypass the chat limit in slow mode! Confirms success in a chat announcement. | Broadcaster has spare VIP slots <br/>_AND_ Redeemer does not have a `Moderator` or a `VIP` role. |
</details>

## Publish Subscriptions | [TwitchIO PubSub Docs](https://twitchio.dev/en/latest/exts/pubsub.html)
<details><summary>Show/Hide PubSub Topics</summary>

| Topic                                                | Response                                                                                                                             |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| *pubsub.channel_points(user_token)[user_channel_id]* | This topic listens for channel point redemptions on the given channel. This topic dispatches the pubsub_channel_points client event. |
</details>

## Event Subscriptions | [TwitchIO EventSub Docs](https://twitchio.dev/en/latest/exts/eventsub.html)
<details><summary>Show/Hide Event Subscription Webhooks</summary>

| Event Type                          | Response                                                             |
|-------------------------------------|----------------------------------------------------------------------|
| *follow*                            | Chat message                                                         |
| *cheer*                             | Shoutout & Chat message                                              |
| *subscription*                      | Shoutout & Chat message                                              |
| *raid*                              | Shoutout & Chat message                                              |
| *hypetrain_begin*                   | `**NOT IMPLEMENTED**`                                                |
| *hypetrain_end*                     | `**NOT IMPLEMENTED**`                                                |
| *stream_start*                      | Creates custom channel point rewards & Chat message                  |
| *stream_end*                        | Removes custom channel point rewards & Chat message                  |
| *channel_shoutout_create*           | `**NOT IMPLEMENTED**`                                                |
| *channel_shoutout_receive*          | `**NOT IMPLEMENTED**`                                                |
| *channel_charity_donate*            | Sends chat announcement with the donation amount and link to charity |
</details>

## Environment Variables
<details><summary>Show/Hide Environment Variables</summary>

* [Create an `.env` file](https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1) with your TWITCH API tokens and your channel name to use this script:

| env key              | type   | env value                                                                                  |
|----------------------|--------|--------------------------------------------------------------------------------------------|
| CLIENT_ID=           | string | *[From Twitch Developer Application](https://dev.twitch.tv/console/apps)*                  |
| CLIENT_SECRET=       | string | *[From Twitch Developer Application](https://dev.twitch.tv/console/apps)*                  |
| VIRUS_TOTAL_API_KEY= | string | *[From VirusTotal Community](https://developers.virustotal.com/reference/getting-started)* |
| BOT_USER_ID=         | string | 123456                                                                                     |
| BOT_JOIN_CHANNEL=    | string | msec                                                                                       |
| BOT_JOIN_CHANNEL_ID= | string | 654321                                                                                     |
| MAX_VIP_SLOTS=       | int    | 20                                                                                         |

### RCECog Allow List

The RCECog **attempts** to limit commands to a allow list so update the `settings.py` file to include a comma separated list of linux binaries that you will allow to run:
```
CMD_ALLOW_LIST = ['aux', 'cat', 'echo', 'grep', 'id', 'ifconfig', 'ls', 'netstat', 'nslookup', 'ping', 'pwd', 'which', 'who', 'whoami']
```

Expect some kind of malicious code to make it through if you leave the RCECog enabled! :)

</details>

Please help me expand the bots functionality by forking the repo and submitting a PR!
