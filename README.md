# sc-smart-playlist

DIY smart playlists for SoundCloud

## Overview

The project breaks down into a couple of parts:

1. Configure the settings.json file with your credentials
2. Run ___.py to create your local MongoDB of SoundCloud tracks
3. Configure the pl_config.json with your smart playlist logic
4. Run ___.py to parse through your PL configuration, your local song database, then generate the playlists on SoundCloud

### 1. Configure settings.json

*FYI: You will need a SoundCloud client ID to continue. If you don't have one, you'll need to [request one here][1], which unfortunately can take a week or two for approval*

Rename `settings.example.json` to `settings.json` and open the file in a text editor. You will need to enter your username, password, then the client_id and client_secret from the [app you registered][1].

### 2. Run ____.py

----

### 3. Configure pl_config.json

The pl_config.json you downloaded with this repository has my entire list of smart playlists. The settings should be fairly intuitive and I added descriptions where possible. For each playlist you append, the .... (What really happens?)

<!-- FIXME -->

### 4. Run ____.py

----

## Hacks and Caveats

The official SoundCloud v1 API has some bugs and here are a few that I've found:

  - Missing Songs: I found that when requesting tracks there would be a few songs missing here and there. I have no idea why, but it could be regional limitations, some sort of publisher setting to be not be available via the API, or that the v1 API has diverged from the SoundCloud v2 API
  - Bad Stats: The returned track from the v1 API often has a different number of comments and likes then the song on SoundCloud

**The "2nd account" hack.** There isn't any support for fetching a user's reposted songs...but you can query a user's activity feed, which is based on other user's reposted songs and promoted songs. If you make a 2nd account who only follows your real, 1st account. You can request the 2nd account's activity feed and carry on. Plus the advantage of the 2nd account is that your primary account feed isn't cluttered with long playlists that repeat songs you've already reposted

<!--

Hi SoundCloud Developers, I played around with the undocumented v2 API and there are some nice features like recommended songs, which are super cool and hopefully should be in the public API

[In the meantime....](https://twitter.com/SoundCloudDev/status/639017606264016896) from [StackOverflow](https://stackoverflow.com/a/37224955/3219667)

 -->

[1]: http://soundcloud.com/you/apps/

<!-- [n]: https://github.com/soundcloud/soundcloud-python -->
<!-- [n]: https://github.com/KyleKing/soundcloud_playlist_maker/issues -->