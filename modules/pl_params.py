import copy
import json
import pprint
import random
import re

import configure_db
import mongo
import utils

# Create debugger
fn = "__log.log"
# fn = "modules/params.log"
lgr = utils.create_logger(__name__, fn, overwrite=False)


class parse_config():
    """Load smart playlist parameters from static JSON file"""

    def __init__(self, debug=False, path="../pl_config.json"):
        """Configure the default playlist configuration to read
            debug (bool): optional argument for additional debugging
            path (str): path to json config file
        """
        self.idx = 0  # default to first playlist
        # Localize arguments
        self.debug = debug
        self.path = path
        # Read config file
        with open(self.path) as config:
            self.data = json.load(config)
        self.default = self.data["Defaults"]
        self.PL = self.data["Playlists"]
        self._p("Curr PL = {}".format(self.PL[self.idx]))
        # self._p(pp=self.data)

    def _p(self, info="", pp=False):
        """Internal print method if debug is active"""
        if self.debug:
            try:
                if pp:
                    lgr.debug(pprint.pformat(pp))
                    # pprint(pp)
                else:
                    lgr.debug("\t{}".format(info))
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
        """Return playlist configuration and index"""
        custom_pl = copy.deepcopy(self.PL[self.idx])
        custom_pl["idx"] = self.idx
        return custom_pl

    def set_idx(self, idx):
        """Update the ID used for each playlist configuration"""
        if type(idx) is not int:
            raise ValueError("Error: idx `{}` is not int".format(idx))
        elif idx > len(self.PL):
            raise ValueError("Index out of bounds (idx > PL's)")
        else:
            self.idx = idx

    def len_idx(self):
        """Return number of playlists"""
        return len(self.PL)

    def get(self, key):
        """Try to return a value from the pl_config"""
        return self._try_parse(self.PL[self.idx], key)

    def getattrs(self, cb=False):
        """Fetch all attributes from a given dictionary"""
        attrs = []
        for key, value in self.PL[self.idx].iteritems():
            attrs.append(key)
            self._p("Pair: {} = {}".format(key, value))
            if cb:
                cb(key)
        return attrs

    # --------------------------------------------------------------------------
    # Make logic comparison of attribute against some value

    def if_(self, key, value="", logic=False):
        """Parse config file value for logical argument
            key (str) pl_config key to get logic test
            value (?) value to test against from SoundCloud track
            logic (?) Optional direct logic value to circumvent "key"
        """
        logic_ = copy.copy(logic)  # Store initial value for debugging
        if not logic:
            logic = self.get(key)
        lgr.debug("Logic: L:{} (L_:{})-V:{} / Types L:{}|V:{}".format(
            utils.pt(logic), utils.pt(logic_), utils.pt(value),
            type(logic), type(value)))

        # (Regex) Compare logic against a *list of values*
        if type(value) is list:
            regex = ur".*%s.*" % logic
            for val in value:
                if re.match(regex, val):
                    lgr.debug("1: Matched regex:`{}` > val:`{}`".format(
                        regex, val))
                    return True
            else:
                lgr.debug("1: Failed match regex:`{}` > (*value):`{}`".format(
                    regex, value))
                return False
        # (Str compare) Compare each *string in list* against value
        elif type(logic) is list:
            for test in logic:
                if (test and value) and test.lower() in value.lower():
                    lgr.debug("2: List match:`{}` > value:`{}`".format(
                        utils.pt(test), utils.pt(value)))
                    return True
            lgr.debug("2: Failed list (*logic):`{}` > value:`{}`".format(
                utils.pt(logic), utils.pt(value)))
            return False

        # Boolean comparison
        elif type(logic) is bool:
            lgr.debug("3: Bool match of `{}` for value:`{}`".format(
                logic is value, value))
            return (logic is value)

        # String based comparison
        elif type(logic) is str or type(logic) is unicode:
            # String could be a csv list
            logic = logic.replace(",", "").replace(" ", "")
            lgr.debug("4: String match:`{}`".format(logic))
            # Convert symbols to logical operators
            if "-" in logic:
                # Range "XX-XX"
                vals = logic.split("-")
                gt = int(vals[0])
                lt = int(vals[1])
                lgr.debug("\tRange Match {} > {} ({}) and {} < {} ({})".format(
                    value, gt, value > gt, value, lt, value < lt))
                return value > int(vals[0]) and value < int(vals[1])
            elif ">" in logic:
                # Greater Than (or equal to) ">=XX"
                lgr.debug("\tG(>) Match {}".format(int(logic[1:])))
                return value >= int(logic[1:])
            elif "<" in logic:
                # Less Than (or equal to) "<=XX"
                lgr.debug("\tL(<) Match {}".format(int(logic[1:])))
                return value <= int(logic[1:])
            elif "%" in logic:
                # Random song selected XX out of 100 (i.e. "XX%")
                percent, __ = logic.split("%")
                rr = random.random()
                result = (rr * 100) <= float(percent)
                lgr.debug("\tRand Match: {} > {} ?{} ".format(
                    percent, rr, result))
                return result
            else:
                lgr.debug("Failed to parse: {}".format(logic))
                return False

        else:
            raise Exception("Could not interpret: {}".format(logic))

    # --------------------------------------------------------------------------
    # Choose which parameter to compare against with the if_() function

    def check_attr(self, trk, attr):
        """Wrapper function to allow "default" list of attr"""
        attr = attr.strip().lower()
        if attr == "defaults":
            defaults = self.get(attr)
            lgr.debug("0: Checking Defaults: `{}`".format(defaults))
            # Check each default parameter from list
            for default in defaults:
                if not self.check_attr_(trk, default):
                    return False
            else:
                return True
        else:
            return self.check_attr_(trk, attr)

    def check_attr_(self, trk, attr):
        """Compare song against each attribute
            trk (dict): song dictionary returned from API
            attr (str): key argument to pass to the pl_config file
        """
        attr = attr.strip().lower()
        # Custom rules relate attribute type to song key-value pair
        if attr == "plays":
            # Check number of plays statistic
            if "playback_count" in trk:
                lgr.debug("[plays]: `{}`".format(trk["playback_count"]))
                return self.if_(attr, trk["playback_count"])
            else:
                lgr.debug("Err: [plays]: `{}`".format(trk["id"]))
                return False
        #
        elif attr == "likes":
            # Check number of likes statistic
            if "likes_count" in trk:
                metric = trk["likes_count"]  # V1
            else:
                metric = trk["favoritings_count"]  # V2
            lgr.debug("[likes]: `{}`".format(metric))
            return self.if_(attr, metric)
        #
        elif attr == "comments":
            # Check number of comments
            if "comment_count" in trk:
                lgr.debug("[comments]: `{}`".format(trk["comment_count"]))
                return self.if_(attr, trk["comment_count"])
            else:
                lgr.debug("Err: [comments]: `{}`".format(trk["id"]))
                return False
        #
        elif attr == "random":
            # Check the random attribute
            return self.if_(attr)
        #
        elif attr == "reposts":
            # Check repost statistic
            lgr.debug("[reposts]: `{}`".format(trk["reposts_count"]))
            return self.if_(attr, trk["reposts_count"])
        #
        elif attr == "keyword_match":
            # Check each keyword against target strings
            for logic in self.get(attr):
                logic = [logic]
                # # Check suite of attributes
                # for sub_attr in ["title", "tag_list",
                #                  "description", "genre"]:
                #     res = self.if_(False, utils.pt(trk[sub_attr]),
                #                    logic=logic)
                #     if res:
                #         return True
                # Check each attribute one-at-a-time to debug
                titleM = self.if_(False, utils.pt(trk["title"]), logic=logic)
                tagM = self.if_(False, trk["tag_list"], logic=logic)
                descM = self.if_(False, trk["description"], logic=logic)
                genreM = self.if_(False, trk["genre"], logic=logic)
                # Safely parse the artist meta data:
                artistM = False
                if "publisher_metadata" in trk:
                    pub_ = trk["publisher_metadata"]
                    if pub_ and ("artist" in pub_):
                        artistM = self.if_(False, pub_["artist"], logic=logic)
                        if artistM:
                            return True
                    else:
                        lgr.debug("Err: no artist: `{}`".format(trk["id"]))
                else:
                    lgr.debug("Err: no p_meta: `{}`".format(trk["id"]))
                # Check if any matches were identified
                if titleM or artistM or tagM or descM or genreM:
                    args = (trk["id"], titleM, artistM, tagM, descM, genreM)
                    lgr.debug("[keyword_match]: (ID:{}) titleM:{}|artistM:{}|tagM:{}|descM:{}|genreM:{}".format(*args))  # noqa
                    return True
            else:
                lgr.debug("X [keyword_match]: (ID:{})".format(trk["id"]))
                return False
        #
        elif attr == "artists":
            # Check the artist name
            if "publisher_metadata" in trk:
                trk_pub = trk["publisher_metadata"]
                if trk_pub and "artist" in trk_pub:
                    return self.if_(attr, trk_pub["artist"])
            lgr.debug("Err: no attr `{}` in `{}`".format(
                attr, utils._dir(trk)))
            lgr.debug("Full trk: {}".format(trk))
            return False
        #
        elif attr == "genres":
            # Search the list of genres against the track genre string
            if "genre" in trk:
                return self.if_(attr, trk["genre"])
            else:
                lgr.debug("Err: no attr `{}` in `{}`".format(
                    attr, utils._dir(trk)))
                lgr.debug("Full trk: {}".format(trk))
                return False
        #
        elif attr == "sources":
            # Check for each matching href source
            sources_dict = configure_db.fetch_songs().sources
            for source_type in self.get(attr):
                # Use the lookup table for a list of v1/v2 sources
                sources = sources_dict[source_type]
                lgr.debug("src:{} | href:{}".format(sources, trk["href"]))
                for source in sources:
                    if self.if_(False, trk["href"], logic=source):
                        return True
                else:
                    lgr.debug("X no source_type `{}`".format(source_type))
            else:
                return False
        #
        elif attr == "go":
            # If False, ignore any songs shorter than 30 sec (i.e. "go")
            duration = "<31,000" if self.get(attr) else ">31,000"
            return self.if_(False, trk["duration"], logic=duration)
        #
        elif attr == "duration":
            # Check duration of track
            return self.if_(attr, trk["duration"])
        #
        elif attr == "shuffle":
            # Check if attr is T/F
            return self.get(attr)
        #
        elif attr == "title":
            # Smart-playlist title is not relevant for sorting
            return True
        #
        else:
            lgr.debug("Err: attr: `{}` not parsed".format(attr))
            return False


if __name__ == "__main__":
    db_songs = mongo.MongoDB("test_database", "test_collection")
    trk = db_songs.find_one()
    p_cg = parse_config(debug=True)
    attrs = [
        # "keyword_match", "artists", "genres", "go", "duration",
        "sources"
    ]
    lgr.debug("trk: {}\n".format(trk))
    for attr in attrs:
        res = p_cg.check_attr(trk, attr)
        lgr.debug("attr: {}={}\n".format(attr, res))
