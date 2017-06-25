import os
import json
# import soundcloud  # regular package from pip
import sc_v2 as soundcloud  # modified version of SC package


class connect(object):

    """
    Everything for Authentication
    """

    def __init__(self):
        # Load secret parameters
        fn = 'settings.json'
        fn = fn if os.path.isfile(fn) else '../' + fn
        with open(fn) as sttngs:
            self.secret = json.load(sttngs)

    def secret(self):
        """Secret tokens"""
        return self.secret

    def client(self):
        """V1 API Endpoints"""
        return soundcloud.Client(
            client_id=self.secret["client_id"],
            client_secret=self.secret["client_secret"],
            username=self.secret["username"],
            password=self.secret["password"],
        )

    def client_v2(self):
        """V2 API Endpoints"""
        return soundcloud.Client(
            client_id=self.secret["client_id"],
            client_secret=self.secret["client_secret"],
            username=self.secret["username"],
            password=self.secret["password"],
            host='api-v2.soundcloud.com'
        )
