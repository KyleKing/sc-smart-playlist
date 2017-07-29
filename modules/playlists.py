import random

import auth
import pl_params
import requests
import utils
from termcolor import colored as cld

lgr = utils.create_logger(__name__, "../tmp/__log.log", overwrite=False)


class generate(object):
    """Make playlists"""

    def __init__(self, configure_songs={}):
        """Initialize
            configure_songs (instance): `configure_db.fetch_songs()`
        """
        self.client = auth.connect().client()
        self._sngs = configure_songs

    def main(self):
        """Read playlist configuration then parse the database"""
        p_cg = pl_params.parse_config(path="pl_config.json")
        prev_pls = self._which_pl()
        for idx in range(p_cg.len_idx()):
            lgr.debug(">>Parsing Playlist ({}/{}): {}".format(
                idx, p_cg.get("title"), p_cg.info()))
            p_cg.set_idx(idx)
            pl_songs = self._filter_songs(p_cg)
            # Reformat for format SoundCloud expects:
            #   w/ format [{ id: <id> }, etc..]
            new_pl = map(lambda id: dict(id=id), pl_songs)
            # Shuffle list order for a fresh playlist order every time:
            if p_cg.get("shuffle"):
                random.shuffle(new_pl)
            self.upload_pl(new_pl, p_cg, prev_pls)

    def _which_pl(self):
        """Return a list of all posted playlist names"""
        # Localize playlists already on account
        prev_pls = {"id": [], "title": []}
        prev_pls_res = self.get("/me/playlists")
        for prev_pl in prev_pls_res:
            lgr.debug("Found pl (#{})  {}".format(prev_pl.id, prev_pl.title))
            prev_pls["id"].append(prev_pl.id)
            prev_pls["title"].append(prev_pl.title)
        # Catch if no playlists were posted to this account
        if len(prev_pls["id"]) == 0:
            return False
        else:
            lgr.debug("All prev_pls: {}\n".format(prev_pls))
            return prev_pls

    def _filter_songs(self, p_cg, debug=True):
        """Loop the filter all songs from database
            p_cg (pointer): pl_params.parse_config(...)
            debug (bool): option for extra verbosity
        """
        pl_songs = []
        for song in self._sngs.db_songs.find({}):
            # Compare each song to each playlist attribute
            #   If fail to match, break loop and skip
            #   If none fail, append the song to list of IDs for playlist
            attrs = p_cg.getattrs()
            lgr.debug("Checking ({}): {}".format(song["id"], utils.pt(song["title"])))
            # lgr.debug(" < {} > : {}\n".format(song["id"], song))
            results = {}
            for attr in attrs:
                results[attr] = p_cg.check_attr(song, attr)
                if not results[attr]:
                    lgr.debug("X No Attr({}) in {}".format(attr, song["id"]))
                    break
            else:
                lgr.debug("! All Attrs found in {}".format(song["id"]))
                pl_songs.append(song["id"])
            lgr.debug("> Final ({}) for attrs ({})\n".format(results, attrs))
        # Remove any duplicate entries
        song_ids = list(set(pl_songs))
        # Arbitrarily limit total list length to avoid an HTTPError
        max_songs = 465
        return song_ids[:max_songs] if len(song_ids) > max_songs else song_ids

    def upload_pl(self, new_pl, p_cg, prev_pls):
        """Push the filtered songs to SoundCloud
            new_pl (list): list of SoundCloud track id's
            p_cg (pointer): pl_params.parse_config(...)
            prev_pls (list): list of all existing playlist names
        """
        pl_idx = -1
        # Determine if the playlist title already exists
        if prev_pls and p_cg.get("title") in prev_pls["title"]:
            # Clear out existing playlist
            pl_idx = prev_pls["title"].index(p_cg.get("title"))
            prev_pl_id = prev_pls["id"][pl_idx]
            lgr.debug("Clearing old pl: {}".format(prev_pls["title"][pl_idx]))
            self.clear_playlist(prev_pl_id)

            # Re-Populate playlist with songs
            playlist_uri = self._make_PL_uri(prev_pl_id)
            lgr.debug("Updating old pl: {} with {} songs".format(
                prev_pls["title"][pl_idx], len(new_pl)))
            try:
                self.client.put(playlist_uri, playlist={"tracks": new_pl})
            except (requests.exceptions.ChunkedEncodingError or
                    requests.exceptions.HTTPError):
                # Ignore the error b/c playlist is successful anyway..
                lgr.debug("Ignored Error on updating PL...")
                print cld("Ignored Error on updating PL...", "red")

        # No playlist exists, make a new one!
        elif len(new_pl) != 0:
            lgr.debug("Creating new playlist: `{}` with {} tracks".format(
                p_cg.get("title"), len(new_pl)))
            try:
                self.client.post("/playlists", playlist={
                    "title": p_cg.get("title"),
                    "sharing": "public",
                    "tracks": new_pl
                })
            except (requests.exceptions.ChunkedEncodingError):
                # Ignore error b/c playlist was likely successful
                lgr.debug("ChunkedEncodingError on making new PL...")
                print cld("ChunkedEncodingError on making new PL...", "red")

    def clear_playlist(self, pl_id):
        """Remove all songs in playlist by replacing with empty array
            Tip from: http://stackoverflow.com/a/34592465/3219667
            pl_id (int): SoundCloud playlist identifier
        """
        # Map empty list of song id's
        tracks = map(lambda id: dict(id=id), [0])
        playlist_uri = self._make_PL_uri(pl_id)
        self.client.put(playlist_uri, playlist={"tracks": tracks})

    def _make_PL_uri(self, pl_id):
        """Create the proper URI for a specific playlist
            pl_id (int): SoundCloud playlist identifier
        """
        # return "https://api.soundcloud.com/playlists/{}".format(pl_id)
        playlist = self.get("/playlists/{}".format(pl_id))
        lgr.debug("*WIP Playlist Tracks: {}".format(playlist.tracks))
        return playlist.uri

    def get(self, uri):
        """Return the response from a SoundCloud http request
            uri (str): SoundCloud url
        """
        return self.client.get(uri)
