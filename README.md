# MTProto Uploader — Railway

This is a standalone Telegram MTProto uploader for media that you own or are authorized to redistribute.

## Railway Variables

Set:

- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `ADMIN_ID` — your Telegram numeric user ID
- `TARGET_CHAT_ID` — channel/group/chat where the bot uploads

The same Telegram `API_ID` and `API_HASH` can be used by multiple deployments.

## Commands

`/start`

Send a document/video/audio to the bot privately. If your Telegram ID matches `ADMIN_ID`, the bot downloads it temporarily and re-uploads it to `TARGET_CHAT_ID`.

`/upload /path/to/file`

Uploads an existing file from the container filesystem.

## Deployment

Push the folder to GitHub, create a Railway service from the repository, add the variables above, and deploy.

This package intentionally does not contain Crunchyroll DRM/Widevine extraction or decryption code.
