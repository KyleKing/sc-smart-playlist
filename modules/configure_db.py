import copy
from termcolor import colored as cld

import auth
import utils
import mongo


class fetch_songs(object):
    """Fetch songs from SoundCloud and log to a local database"""

    # String comparisons for pl_param.py comparison
    sources = {
        "reposts": ['activities', 'stream'],
        "likes": ['favorites', 'likes'],
        "tracks": ['playlists', 'personalized']
    }

    def __init__(self):
        """Configure MongoDB and Secret Settings"""
        self.db_songs = mongo.MongoDB("test_database", "test_collection")
        self.connect = auth.connect()  # Load secret parameters

    def db_songs(self):
        """Return database pointer"""
        return self.db_songs

    def purge(self):
        """Only purge when necessary"""
        self.db_songs.purge()

    def summary(self, query={}, log=False):
        """Print database info"""
        self.db_songs.info()
        self.db_songs.debug(query, log)

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
            '/me/personalized-tracks?limit=5',  # Warn: resp is dict of lists
            '/users/{}/likes'.format(acount_id),
        ]
        return self._pull(hrefs)

    # --------------------------------------------------------------------------

    def _pull(self, hrefs):
        """Loop through all responses regardless of API Version"""
        song = {}
        for __, next_href in enumerate(hrefs):
            print cld("\n\nNew href", 'red'), next_href, '\n\n'
            cur_href = next_href
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
        print("\nComplete.\n")
        self.summary()
        return True

    def _parse_music(self, music):
        """Return parsed song to assign to new dictionary"""
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
        """Prepare to insert to DB"""
        if song:
            if "playlist" in song:
                print cld("Skipping Pl:", 'red'), song["playlist"]["title"]
            else:
                # A single song
                if type(song) is dict:
                    songs = [song]
                # v2[likes] are returned in list
                elif type(song) is list:
                    songs = song
                # Unknown...
                else:
                    songs = []
                    print(cld("Failed to interpret music:", 'red'))
                    print '\tOn counter', count, 'found:', music
                    print '\tMusic has keys:', utils._dir(music)
                    print '\tFull obj:', music.__dict__
                # Act on the list of songs
                for song_ in songs:
                    utils.log_activity(song_, 1, True)
                    # Reference original request for sorting
                    song_["href"] = [cur_href]
                    self._insert(song_)
        else:
            print cld('Unknown song', 'red'), song
        # print ''  # optional line break

    def _insert(self, song):
        """Make sure entry is unique before inserting"""
        query = {"id": song["id"]}
        for match in self.db_songs.find(query):
            if song["href"] in match["href"]:
                break  # don't update db if href already listed
            # If existing entry, update with additional href search
            hrefs = copy.deepcopy(song["href"])
            hrefs.extend(match["href"])
            self.db_songs.set(query, {"href": hrefs})
            # print cld('   {}[href]= {}'.format(match["id"], hrefs), 'blue')
            break
        else:
            self.db_songs.insert_one(song)


# if __name__ == "__main__":
#     # Run the full playlist maker
#     fs = fetch_songs()
#     # fs.summary()
#     fs.purge()  # leave collection as is for now
#     fs.parse_sources()
#     fs.parse_sources_v2()
