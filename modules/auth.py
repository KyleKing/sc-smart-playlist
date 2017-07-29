import json
import os

try:
    import soundcloud  # regular package from pip
    official_SC_package = True
except ImportError:
    import sc_v2 as soundcloud  # modified version of SC package
    official_SC_package = False


class connect(object):
    """Authenticate with SoundCloud API and read secret ini configuration"""

    def __init__(self):
        """Load secret parameters"""
        fn = "settings.json"
        fn = fn if os.path.isfile(fn) else "../" + fn
        with open(fn) as sttngs:
            self.secret_config = json.load(sttngs)

    def secret(self):
        """Return secret tokens"""
        return self.secret_config

    def client(self):
        """V1 API Endpoints"""
        return soundcloud.Client(
            client_id=self.secret_config["client_id"],
            client_secret=self.secret_config["client_secret"],
            username=self.secret_config["username"],
            password=self.secret_config["password"],
        )

    def client_v2(self):
        """V2 API Endpoints"""
        if official_SC_package:
            print """Error: using the official soundcoud-python package.
Will use the v1 API. For v2, additional modification is needed."""
            return self.client()
        return soundcloud.Client(
            client_id=self.secret_config["client_id"],
            client_secret=self.secret_config["client_secret"],
            username=self.secret_config["username"],
            password=self.secret_config["password"],
            host="api-v2.soundcloud.com"
        )
