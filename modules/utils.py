import logging

from termcolor import colored as cld

# DEBUG, INFO, WARNING, ERROR, CRITICAL
logging_level = logging.DEBUG


class safe_attr(object):
    """Sometimes attribute doesn't exist, so return placeholder"""

    def __init__(self, key):
        """key (dict/obj): target data structure"""
        self.key = key

    def r(self, value):
        """Try to return attr value or print debug info"""
        try:
            # Evaluate as dictionary or as an object
            if type(self.key) is dict:
                return self.key[value]
            return getattr(self.key, value)
        except (AttributeError, KeyError):
            print(cld("Error: Failed to get `{}`".format(value), "red"))
            print(cld("\tfor key: `{}`".format(self.key), "red"))
            return "FAILED"

    def rr(self, value1, value2):
        """Recursive variant for values nested one level"""
        try:
            _key = self.r(value1)
            return _key[value2]
        except (AttributeError, KeyError):
            print "Error: Failed `[{}][{}]`".format(value1, value2)
            return False


# ------------------------------------------------------------------------------
# Debugging Tools


def pt(raw_title):
    """Solve: UnicodeEncodeError: "ascii" codec can"t encode...
        from: http://stackoverflow.com/a/5146914/3219667
        raw_title (str): song title
    """
    return raw_title.encode("ascii", "ignore")


def print_title(raw_title, preposition="Title: ", color="blue"):
    """Safely print title names
        raw_title (str): song title
        preposition (str): extra str to print before title
        color (str): termcolor color
    """
    try:
        title = pt(raw_title)
        print(cld("{}{}".format(preposition, title), color))
    except UnicodeEncodeError:
        print "Error: Can't display track title"


def log_activity(track, code, debug=False):
    """Print out debugging information based on debug integer"""
    SA = safe_attr(track)
    if code == 1 or code == 2 or code == 3:
        print_title(SA.r("title"), "ID={}: ".format(SA.r("id")))
    if code == 2:
        print("tag_list: {}".format(SA.r("tag_list")))
        print("user_playback_count: {}".format(SA.r("user_playback_count")))
        if debug:
            print("genre: {}".format(SA.r("genre")))
            print("created_at: {}".format(SA.r("created_at")))
            print("User: {}".format(SA.r("user")["username"]))
            print("favoritings_count: {}".format(SA.r("favoritings_count")))
            print("comment_count: {}".format(SA.r("comment_count")))
            print("playback_count: {}".format(SA.r("playback_count")))
            print("reposts_count: {}".format(SA.r("reposts_count")))
            print("likes_count: {}".format(SA.r("likes_count")))
    if code == 3:
        print(" ---------------------- ")
        dump(track)
        print(" ---------------------- ")
        print(" ")


def dump(obj):
    """Dump all attributes
        From: http://blender.stackexchange.com/a/1880
    """
    for attr in dir(obj):
        if hasattr(obj, attr):
            print "obj.{} = {}".format(attr, getattr(obj, attr))


def _dir(obj, debug=False):
    """Return list of non-private object attributes
        From: https://stackoverflow.com/a/61522/3219667
    """
    attrs = [attr for attr in dir(obj) if not attr.startswith("_")]
    if debug:
        print "attrs:", attrs
    return attrs


def create_logger(name, fn, overwrite=False):
    """Create logger
        name (__name__): from source file
        fn (str): filename to write to
        overwrite (bool): optionally erase log last file
    """
    global logging_level
    logger = logging.getLogger(name)
    logger.setLevel(logging_level)
    # Wipe then link file to handler
    if overwrite:
        open(fn, "w").close()
    fh = logging.FileHandler(fn)
    fh.setLevel(logging.DEBUG)
    # Format default logged line
    ln = ">>%(filename)s:%(lineno)d> %(message)s"
    fh.setFormatter(logging.Formatter(ln))
    # Link handler to global logger
    logger.addHandler(fh)
    return logger
