## Credentials

This directory is used to store credentials needed for production.

  - `crowdinkeys.env`: sets the ENV variable `KA_CROWDIN_SECRET_KEY`
    which is used to download title/descriptino translations.
  - `proxy_list.env`: list of HTTP proxy servers currently in use (needs to be updated periodically)
  - `channeladmin.token`: the Studio API token for the user Channel Admin user 


Not used:
  - `youtube_api_key.env`: API Key for getting YouTube > Data API > Captions.list
    to check what subtitles languages are available on youtube for a given video.




