import copy
from termcolor import colored as cld

import auth
import utils
import mongo


class fetch_songs(object):

    """
    Fetch songs from SoundCloud and log to a local database
    """

    # String comparisons for pl_param.py comparison
    sources = {
        "reposts": ['activities', 'stream'],
        "likes": ['favorites', 'likes'],
        "tracks": ['playlists', 'personalized']
    }

    def __init__(self):
        """Configure MongoDB and Secret Settings"""
        self.db_songs = mongo.MongoDB("test_database", "test_collection")
        # Load secret parameters
        self.connect = auth.connect()

    def db_songs(self):
        """Return database pointer"""
        return self.db_songs

    # --------------------------------------------------------------------------

    def parse_sources(self):
        """V1 API Endpoints"""
        self.client = self.connect.client()
        acount_id = self.connect.secret["some_account_id"]
        hrefs = [
            '/me/activities',  # activity feed
            '/users/{}/favorites'.format(acount_id),
            # '/users/{}/playlists'.format(acount_id),
        ]  # See: https://developers.soundcloud.com/docs/api/reference#me
        return self._pull(hrefs)

    def parse_sources_v2(self):
        """V2 API Endpoints"""
        self.client = self.connect.client_v2()
        acount_id = self.connect.secret["some_account_id"]
        hrefs = [
            '/stream?limit=25',
            '/me/personalized-tracks?limit=5',  # Warn resp is dict of lists
            '/users/{}/likes'.format(acount_id),
        ]
        return self._pull(hrefs)

    # --------------------------------------------------------------------------

    def _pull(self, hrefs):
        """Loop through all responses regardless of API Version"""
        song = {}
        for h_count, next_href in enumerate(hrefs):
            print cld("\n\nNew href", 'red'), next_href, '\n\n'
            cur_href = copy.copy(next_href)
            while next_href is not None:
                # Unwrap response per HREF query request
                resp = self.client.get(next_href)
                obj = resp.collection if hasattr(resp, "collection") else resp
                # "music" could be playlist, song, or list of songs
                for count, music in enumerate(obj):
                    song = self._parse_music(music)
                    self._prep_insert(song, music, cur_href, count)
                print(cld("> Loop complete #{}\n".format(count + 1), 'green'))
                if hasattr(resp, 'next_href'):
                    next_href = resp.next_href
                else:
                    next_href = None
                    print cld("resp missing next_href:", 'red'), resp
                    print cld("resp of type:", 'red'), type(resp)
                    print 'Attrs:', utils._dir(resp)
                    if type(resp) is list:
                        for r_idx, thing in enumerate(resp):
                            print 'resp ({})'.format(r_idx), thing
                            print 'Attrs:', utils._dir(thing)

        print("\nCompleted update of Database, print summary information:")
        self.summary()
        return True

    def _parse_music(self, music):
        # Parse music and assign to new dictionary
        # v1[activities]
        if hasattr(music, "origin"):
            song = copy.deepcopy(music.origin.__dict__)
        # v2[likes] is dict else v2[stream]
        elif hasattr(music, "track"):
            _tmp = music.track
            tmp = _tmp if type(_tmp) is dict else _tmp.__dict__
            song = copy.deepcopy(tmp)
        # v2[personalized]
        elif hasattr(music, "recommended"):
            song = copy.deepcopy(music.recommended)
        # ?
        elif type(music) is dict:
            song = music
        # v1[favorites]
        else:
            song = music.__dict__
        # Miscellaneous extra:
        if "obj" in song:
            song = song["obj"]
        return song

    def _prep_insert(self, song, music, cur_href, count="NA"):
        """Final Preparation for insert to DB"""
        if song:
            if "playlist" not in song:
                if type(song) is list:
                    print(cld("List found...", 'red'))
                    songs = song
                elif type(song) is dict:
                    songs = [song]
                else:
                    songs = []
                    print(cld("Failed to interpret music:", 'red'))
                    print '\tOn counter', count, 'found:', music
                    print '\tMusic has keys:', utils._dir(music)
                    print '\tFull obj:', music.__dict__
                # Need to unwrap list-response from v2[likes]
                for _song in songs:
                    # Duplicated analysis for sub
                    utils.log_activity(_song, 1, True)
                    _song["href"] = [cur_href]  # Reference api request
                    self._insert(_song)
            else:
                print cld("Skipping Pl:", 'red'), song["playlist"]["title"]
        else:
            print cld('Unknown song', 'red'), song
        print ''

    def _insert(self, song):
        """Make sure entry is unique before inserting"""
        query = {"id": song["id"]}
        resp = self.db_songs.find(query)
        for match in resp:
            if song["href"] in match["href"]:
                break  # don't update db if href already listed
            # If existing entry, update with additional href search
            hrefs = copy.deepcopy(song["href"])
            hrefs.extend(match["href"])
            self.db_songs.set(query, {"href": hrefs})
            print(cld('   {}[href]= {}'.format(match["id"], hrefs), 'blue'))
            break
        else:
            self.db_songs.insert_one(song)

    # --------------------------------------------------------------------------

    def purge(self):
        """Only purge when necessary"""
        self.db_songs.purge()

    def summary(self, query={}, log=False):
        """Print database info"""
        self.db_songs.info()
        self.db_songs.debug(query, log)


if __name__ == "__main__":
    # Run the full playlist maker
    fs = fetch_songs()
    # fs.summary()
    # fs.purge()  # leave collection as is for now
    fs.parse_sources()
    fs.parse_sources_v2()
