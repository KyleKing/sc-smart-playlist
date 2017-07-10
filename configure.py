from modules import configure_db

# Make sure a MongoDB instance is running or you will see a:
# pymongo.errors.ServerSelectionTimeoutError: localhost ... Connection refused
# To solve, run `mongod` in a new terminal window

# Step 1 - Fetch and store all song data
configure_songs = configure_db.fetch_songs()
configure_songs.purge()
configure_songs.parse_sources()
