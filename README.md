# sc-smart-playlist

DIY smart playlists for SoundCloud. Use the songs you've liked or reposted on Soundcloud to create new playlists by genre, number of likes, song duration, etc. [See my account as an example][2] which are all playlists [generated based on these settings][3].

## Overview

Get started making your own smart playlists following these four steps:

1. Create the settings.json file with your credentials
2. Run configure.py to create your local MongoDB of SoundCloud tracks
3. Create your smart playlists configuration file, pl_config.json
4. Run main.py to parse through your pl_config, your local song database, then push the smart playlists to SoundCloud

### 1. Configure settings.json

*FYI: You will need a SoundCloud client ID to continue. If you don't have one, you'll need to [request one here][1], which may take up to 1-2 weeks to receive*

Download the Github repository to your local directory. Rename `settings.example.json` to `settings.json` and open the file in a text editor. You will need to enter your user name, password, then the client_id and client_secret from the [app you registered][1].

### 2. Run configure.py

> Create a local database of your liked tracks and activities that will be used to create smart playlists from

1. Install required python packages. In a terminal window, navigate to the directory and run `pip install -r requirements.txt`
2. In a new prompt, run `mongod` to open a mongo db client
3. Configure with `python configure.py`

### 3. Configure pl_config.json

The pl_config.json you downloaded with this repository has my personal smart playlists to get you started. Each playlist is defined in a JSON object and can optionally include a list of default keys, so that all playlists will inherit changes made to the defaults.

### 4. Run main.py

1. In a new prompt, run `mongod` to open a mongo db client
2. Update playlists with `python main.py`

## Hacks and Caveats

The official SoundCloud v1 API has some bugs and here are a few that I've found:

  - Missing Songs: I found that when requesting tracks there would be a few songs missing here and there. I have no idea why, but it could be regional limitations, some sort of publisher setting to be not be available via the API, or that the v1 API has diverged from the SoundCloud v2 API
  - Bad Stats: The returned track from the v1 API often has a different number of comments and likes then the song on SoundCloud

**The "2nd account" hack.** There isn't any support for fetching a user's reposted songs...but you can query a user's activity feed, which is based on other user's reposted songs and promoted songs. If you make a 2nd account who only follows your real, 1st account. You can request the 2nd account's activity feed and carry on. Plus the advantage of the 2nd account is that your primary account feed isn't cluttered with long playlists that repeat songs you've already reposted

<!--

Hi SoundCloud Developers, I played around with the undocumented v2 API and there are some nice features like recommended songs, which are super cool and hopefully should be in the public API

[In the meantime....](https://twitter.com/SoundCloudDev/status/639017606264016896) from [StackOverflow](https://stackoverflow.com/a/37224955/3219667)

V2 API Unofficial Documentation: https://github.com/wb9688/sc-api-v2-docs

Endpoints (Base url: https://api-v2.soundcloud.com/)

- ./me/play-history/tracks
- ./dashbox/stream
- ./users/21434963/track_likes
- ./users/21434963/likes
- ./activities
- ./stream/users/21434963
- ./users/21434963/followings/not_followed_by/237623984
- ./me/personalized-tracks

Rest of URI: ?client_id=<client>&limit=1&offset=0&linked_partitioning=1&app_version=1489574664

Example: https://api-v2.soundcloud.com/users/21434963/likes?client_id=<client>&limit=1&offset=0&linked_partitioning=1&app_version=1489574664

# Other Random Links:

- Pull playlists from Google Music Stations: https://github.com/simon-weber/gmusicapi and https://github.com/DanNixon/PlayMusicCL/blob/master/playmusiccl/playmusiccl.py#L119
- Pull playlists from Spotify: https://play.spotify.com/collection/songs
- Example SoundCloud client https://github.com/0xPr0xy/soundcloud-cli & https://pyspotify.mopidy.com/en/latest/quickstart/

 -->

[1]: http://soundcloud.com/you/apps/
[2]: http://soundcloud.com/users/kyle-the-coder/
[3]: https://github.com/KyleKing/sc-smart-playlist/pl_config.example.json

<!-- [n]: https://github.com/soundcloud/soundcloud-python -->
<!-- [n]: https://github.com/KyleKing/soundcloud_playlist_maker/issues -->