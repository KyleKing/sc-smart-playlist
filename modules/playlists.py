# import copy
import random
import requests
# from tqdm import tqdm
from termcolor import colored as cld

import auth
import pl_params


class generate(object):

    """
    Make playlists
    """

    def __init__(self, configure_songs):
        self.client = auth.connect().client()
        self._sngs = configure_songs

    def main(self):
        """   do all the things!   """
        # Loop all playlists from config
        p_cg = pl_params.parse_config(path='pl_config.json')
        prev_pls = self._which_pl()
        for idx in range(p_cg.len_idx()):
            print cld('\n\nPL Title: {}'.format(p_cg.get("title")), 'blue')
            print cld('PL[{}]: {}'.format(idx, p_cg.info()), 'blue')
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
        # Localize playlists already on account
        prev_pls = {'id': [], 'title': []}
        prev_pls_res = self.client.get("/me/playlists")
        for prev_pl in prev_pls_res:
            print "Found pl (#{})  {}".format(prev_pl.id, prev_pl.title)
            prev_pls['id'].append(prev_pl.id)
            prev_pls['title'].append(prev_pl.title)
        if len(prev_pls['id']) > 0:
            print 'All prev_pls', prev_pls, '\n'
            return prev_pls
        else:
            return False

    def _filter_songs(self, p_cg, debug=True):
        """Loop the filter all songs from database"""
        pl_songs = []
        # FIXME: TQDM?
        for count, song in (enumerate(self._sngs.db_songs.find({}))):
            # title = utils.pt(song["title"])
            # Compare each song to each playlist attribute
            #   If fail to match, break loop and skip
            #   If no fails, append the song to list of IDs for playlist
            attrs = p_cg.getattrs()
            for attr in attrs:
                if not p_cg.check_attr(song, attr):
                    # if debug:
                    #     print cld('Fail({}):{}'.format(attr, title), 'red')
                    break
            else:
                # if debug:
                #     print cld('Pass: {}'.format(title), 'green')
                pl_songs.append(song['id'])
        # Remove any duplicate entries
        song_ids = list(set(pl_songs))
        # Limit total size of the list to avoid an HTTPError
        max_songs = 465
        if len(song_ids) > max_songs:
            random.shuffle(song_ids)
            return song_ids[:max_songs]
        return song_ids

    def upload_pl(self, new_pl, p_cg, prev_pls):
        """Push the filtered songs to SoundCloud"""
        pl_idx = -1
        # Determine if the playlist title already exists
        if prev_pls and p_cg.get('title') in prev_pls['title']:
            # Clear out existing playlist
            pl_idx = prev_pls['title'].index(p_cg.get('title'))
            prev_pl_id = prev_pls['id'][pl_idx]
            # TODO: no longer necessary, but cleaner implementation
            print 'Clearing old pl: {}'.format(prev_pls['title'][pl_idx])
            self.clear_playlist(prev_pl_id)
            # Re-Fill playlist with songs:
            playlist_uri = self._make_PL_uri(prev_pl_id)

            # Chunks are a good thing to know, but each overwrites old pl...
            # chunks = np.array_split(new_pl, 10)
            # chunks = [new_pl[x:x + 20] for x in xrange(0, len(new_pl), 20)]

            print 'Updating old pl: {} with {} songs'.format(
                prev_pls['title'][pl_idx], len(new_pl))
            # print 'new_pl', new_pl
            try:
                self.client.put(playlist_uri, playlist={'tracks': new_pl})
            except (requests.exceptions.ChunkedEncodingError):
                # Ignore the error b/c playlist is successful anyway..
                print cld('ChunkedEncodingError on updating PL...', 'red')

        # No playlist exists, make a new one!
        elif len(new_pl) != 0:
            print 'Creating new playlist: {} with {}'.format(
                prev_pls['title'][pl_idx], new_pl)
            try:
                self.client.post('/playlists', playlist={
                    'title': p_cg.get('title'),
                    'sharing': 'public',
                    'tracks': new_pl
                })
            except (requests.exceptions.ChunkedEncodingError):
                # Ignore the error b/c playlist is successful anyway..
                print cld('ChunkedEncodingError on making new PL...', 'red')

    def clear_playlist(self, pl_id):
        """Remove all songs in playlist by replacing with empty array
            Tip from: http://stackoverflow.com/a/34592465/3219667"""
        tracks = map(lambda id: dict(id=id), [0])
        playlist_uri = self._make_PL_uri(pl_id)
        self.client.put(playlist_uri, playlist={'tracks': tracks})

    def _make_PL_uri(self, pl_id):
        """Create the proper URI for a specific playlist"""
        return "https://api.soundcloud.com/playlists/{}".format(pl_id)
        # playlist = self.client.get('/playlists/{}'.format(pl_id))
        # return playlist.uri
        # FYI: playlist.tracks
