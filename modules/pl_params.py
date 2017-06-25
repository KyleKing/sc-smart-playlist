import re
import json
import pprint
import random
from termcolor import colored as cld

import utils
import mongo
import configure_db


class parse_config():

    """
    Load smart playlist parameters from static JSON file
    """

    def __init__(self, debug=False, path='../pl_config.json'):
        self.idx = 0  # default to first playlist
        self.path = path
        self.debug = debug
        with open(self.path) as config:
            # Load json config file into name space
            self.data = json.load(config)
        self.default = self.data["Defaults"]
        self.PL = self.data["Playlists"]
        self._p('Curr PL = {}'.format(self.PL[self.idx]))
        # self._p(pp=self.data)

    def _p(self, info='', pp=''):
        """Internal print method if debug is active"""
        if self.debug:
            try:
                if pp:
                    pprint(pp)
                else:
                    print info
            except UnicodeEncodeError:
                print "Error: Can't display something...carry on"

    def _try_parse(self, this, key):
        """See if playlist-specific settings or revert to default"""
        try:
            return this[key]
        except(AttributeError, KeyError):
            return self._get_default(key)

    def _get_default(self, key):
        """Fall back to default value"""
        return self.default[key]

    # --------------------------------------------------------------------------
    # Externally available functions

    def info(self):
        """Return dict of full title name and index"""
        return {
            # FIXME: not used
            # "title": self.get("title_prefix") + self.get("title"),
            "title": self.get("title"),
            "shuffle": self.get("shuffle"),
            "idx": self.idx
        }

    def set_idx(self, idx):
        """Update the ID used for each playlist configuration"""
        if type(idx) is not int:
            raise ValueError('Error: idx `{}` is not int'.format(idx))
        elif idx > len(self.PL):
            raise ValueError("Index out of bounds (idx > PL's)")
        else:
            self.idx = idx

    def len_idx(self):
        """Number of playlists"""
        return len(self.PL)

    def get(self, key):
        """Try to return a value from the pl_config"""
        return self._try_parse(self.PL[self.idx], key)

    def getattrs(self, cb=False):
        """Fetch all attributes from a given dictionary"""
        attrs = []
        for key, value in self.PL[self.idx].iteritems():
            attrs.append(key)
            self._p('Pair: {} = {}'.format(key, value))
            if cb:
                cb(key)
        return attrs

    # --------------------------------------------------------------------------
    # Make logic comparison of attribute against some value

    def if_(self, key, value, logic=False):
        """Parse config file value for logical argument
            key (str) pl_config key to get logic test
            value (?) value to test against from SoundCloud track
            logic (?) Direct
        """
        if not logic:
            logic = self.get(key)
        # print 'logic', logic, '-value', value
        # print 't(logic)', type(logic), '-t(value)', type(value)
        # self._p('logic={} & value={} ({})'.format(logic, value, type(value)))

        # (Regex) Compare logic against a list of values
        if type(value) is list:
            regex = ur'.*%s.*' % logic
            for val in value:
                print cld('val', 'red'), val, 'regex', regex
                if re.match(regex, val):
                    print 'Matched `{}` with `{}`'.format(val, regex)
                    return True
            else:
                return False
        # (Str comp.) Cycle through a list of logic against value
        elif type(logic) is list:
            for test in logic:
                if test and value and test.lower() in value.lower():
                    self._p('List match with {}'.format(test))
                    return True
            self._p('*** Failed to make list match')
            return False

        # Boolean comparison
        elif type(logic) is bool:
            self._p('Bool match of `{}`'.format(logic is value))
            return (logic is value)

        # String based comparison
        elif type(logic) is str or type(logic) is unicode:
            # String could be a csv list
            logic = logic.replace(',', '').replace(' ', '')
            # Convert symbols to logical operators
            if '-' in logic:
                # Range "XX-XX"
                vals = logic.split('-')
                gt = int(vals[0])
                lt = int(vals[1])
                self._p('Range Match {} > {} ({}) and {} < {} ({})'.format(
                    value, gt, value > gt, value, lt, value < lt))
                return value > int(vals[0]) and value < int(vals[1])
            elif '>' in logic:
                # Greater Than (or equal to) ">=XX"
                self._p('G(>) Match {}'.format(int(logic[1:])))
                return value >= int(logic[1:])
            elif '<' in logic:
                # Less Than (or equal to) "<=XX"
                self._p('L(<) Match {}'.format(int(logic[1:])))
                return value <= int(logic[1:])
            elif '%' in logic:
                # Random song selected XX out of 100 (i.e. "XX%")
                percent, __ = logic.split('%')
                rr = random.random()
                result = (rr * 100) <= float(percent)
                self._p('Rand Match: {} > {} ?{} '.format(percent, rr, result))
                return result
            else:
                print cld('Failed to parse: {}'.format(logic), 'red')
                return False

        else:
            raise Exception('Could not interpret: {}'.format(logic))

    # --------------------------------------------------------------------------
    # Choose which parameter to compare against with the if_() function

    def check_attr(self, trk, attr):
        """Compare song against each attribute"""
        attr = attr.strip().lower()
        # Custom rules relate attribute type to song key-value pair
        if attr == 'plays':
            if 'playback_count' in trk:
                return self.if_(attr, trk['playback_count'])
            else:
                print 'not attr', attr, 'in', utils._dir(trk)
                print '\tFull:', trk
                return False
        #
        elif attr == 'likes':
            if 'likes_count' in trk:
                metric = trk['likes_count']  # V1
            else:
                metric = trk['favoritings_count']  # V2
            return self.if_(attr, metric)
        #
        elif attr == 'comments':
            if 'comment_count' in trk:
                return self.if_(attr, trk['comment_count'])
            else:
                print 'not attr', attr, 'in', utils._dir(trk)
                print '\tFull:', trk
                return False
        #
        elif attr == 'random':
            return self.if_(attr, 'N/A b/c random test')
        #
        elif attr == 'reposts':
            return self.if_(attr, trk['reposts_count'])
        #
        elif attr == 'keyword_match':
            #
            # for genre in trk['genre']:
            #     print 'genre', genre
            #     if self.if_(attr, genre):
            #         return True
            # else:
            #     return False
            #
            # FIXME / TODO
            # attr = attr if attr is list else [attr]
            for logic in self.get(attr):
                logic = [logic]
                a = self.if_(False, trk['title'], logic)
                trk_pub = trk['publisher_metadata']
                if trk_pub and 'artist' in trk_pub:
                    b = self.if_(False, trk_pub['artist'], logic)
                else:
                    b = False
                c = self.if_(False, trk['tag_list'], logic)
                d = self.if_(False, trk['description'], logic)
                e = self.if_(False, trk['genre'], logic)
                # TODO: Check other things?
                if a or b or c or d or e:
                    return True
            else:
                return False
        #
        elif attr == 'artists':
            # FIXME: This works?
            if 'publisher_metadata' in trk:
                trk_pub = trk['publisher_metadata']
                if trk_pub and 'artist' in trk_pub:
                    return self.if_(attr, trk_pub['artist'])
            print 'not attr', attr, 'in', utils._dir(trk)
            print '\tFull:', trk
            return False
        #
        elif attr == 'genres':
            # Search the list of genres against the track genre string
            if 'genre' in trk:
                return self.if_(attr, trk['genre'])
            else:
                print 'not attr', attr, 'in', utils._dir(trk)
                print '\tFull:', trk
                return False
        #
        elif attr == 'sources':
            # Check for each matching href source
            sources_dict = configure_db.fetch_songs().sources
            for source_type in self.get(attr):
                print 'source_type', source_type
                # Use the lookup table for a list of v1/v2 sources
                sources = sources_dict[source_type]
                print 'sources', sources
                for source in sources:
                    print 'source', source, 'href', trk['href']
                    if self.if_(False, trk['href'], logic=source):
                        return True
            else:
                return False
        #
        elif attr == 'go':
            # If False, ignore any songs shorter than 30 sec (i.e. "go")
            duration = '<31,000' if self.get(attr) else '>30,000'
            return self.if_(False, trk['duration'], duration)
        #
        elif attr == 'duration':
            return self.if_(attr, trk['duration'])
        #
        elif attr == 'shuffle' or attr == 'title':
            # Shuffle applied in aggregate
            # Title is just the playlist title and not relevant for sorting
            return True
        #
        else:
            print 'Attr `{}` was not parsed'.format(attr)
            return False


if __name__ == "__main__":
    db_songs = mongo.MongoDB("test_database", "test_collection")
    trk = db_songs.find_one()
    print 'trk:', trk, '\n'
    p_cg = parse_config(debug=True)
    # attrs = ['keyword_match', 'artists', 'genres', 'go', 'duration']
    attrs = ['sources']
    for attr in attrs:
        res = p_cg.check_attr(trk, attr)
        print cld('attr', 'blue'), attr, '=', res

#     # Example Code:
#     #
#     # Fetch an example song:
#     f_sngs = configure_db.fetch_songs()
#     db_songs = f_sngs.db_songs
#     for song in db_songs.find({'id': 192828855}):
#         print 'Parsing:', song["title"]

#     # Load config
#     p_cg = parse_config(path='../pl_config.json')

#     # Test all playlists listed in config file
#     for idx in range(p_cg.len_idx()):
#         p_cg.set_idx(idx)
#         attrs = p_cg.getattrs()
#         print '\nTitle:', p_cg.get("title")
#         print 'PL[{}]: {}'.format(idx, p_cg.info())
#         print 'attrs', attrs
#         # For certain types of attributes, check a value from the song
#         #   Below is test development of _make_pl.py
#         for attr in attrs:
#             base = '> attr: {}'.format(attr)
#             if 'source' in attr:
#                 src = 'repost'
#                 print '{} >> Source ({}) = {}'.format(
#                     base, src, p_cg.if_(attr, src))
#             elif 'shuffle' in attr:
#                 t_val = True
#                 print '{} >> Bool ({}) = {}'.format(
#                     base, t_val, p_cg.if_(attr, t_val))
#             else:
#                 t_val = 10000
#                 print '{} >> Else ({}) = {}'.format(
#                     base, t_val, p_cg.if_(attr, t_val))
