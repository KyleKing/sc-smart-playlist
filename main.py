import sys

from modules import configure_db, playlists, utils

lgr = utils.create_logger(__name__, "__log.log", True)
lgr.debug("Initialized: {}".format(sys.argv))

configure_songs = configure_db.fetch_songs()

# Step 2 - Generate Playlists
create_playlists = playlists.generate(configure_songs)
create_playlists.main()
