from termcolor import colored as cld


class safe_attr(object):

    """
    Sometimes attribute doesn't exist, so return placeholder
    """

    def __init__(self, key):
        self.key = key

    def r(self, value):
        """Try to return value or print debug info"""
        try:
            if type(self.key) is dict:
                return self.key[value]
            return getattr(self.key, value)
        except (AttributeError, KeyError):
            print(cld("Error: Failed to get `{}`".format(value), 'red'))
            print self.key
            return 'FAILED'

    def rr(self, value1, value2):
        """Variant for values beyond one level"""
        try:
            _key = self.r(value1)
            return _key[value2]
        except (AttributeError, KeyError):
            print 'Error: Failed to do `{}/{}`'.format(value1, value2)
            return False


# ------------------------------------------------------------------------------


def pt(raw_title):
    """Solve: UnicodeEncodeError: 'ascii' codec can't encode...
        from: http://stackoverflow.com/a/5146914/3219667"""
    return raw_title.encode('ascii', 'ignore')


def print_title(raw_title, extra='Title: ', color='blue'):
    """Print title name"""
    try:
        title = pt(raw_title)
        print(cld("{}{}".format(extra, title), color))
    except UnicodeEncodeError:
        print "Error: Can't display track title"


def log_activity(track, code, debug=False):
    """Print out debugging information based on a particular debug level"""
    SA = safe_attr(track)
    if code == 1 or code == 2 or code == 3:
        print_title(SA.r("title"))
        print(cld("> ID: {}".format(SA.r("id")), 'blue'))
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

# ------------------------------------------------------------------------------


def dump(obj):
    """
    Dump out all attributes
        From: http://blender.stackexchange.com/a/1880
    """
    for attr in dir(obj):
        if hasattr(obj, attr):
            print "obj.{} = {}".format(attr, getattr(obj, attr))


def _dir(obj, debug=False):
    """
    Print out the object attributes
        From: https://stackoverflow.com/a/61522/3219667
    """
    attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
    if debug:
        print "attrs:", attrs
    return attrs


if __name__ == "__main__":
    print 'Run Basic Tests...'
