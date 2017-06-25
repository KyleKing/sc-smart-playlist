from modules import configure_db, playlists

# Step 1 - Fetch and store all song data
configure_songs = configure_db.fetch_songs()
# configure_songs.parse_sources()
# configure_songs.parse_sources_v2()
configure_songs.summary()

# Step 2 - Generate Playlists
create_playlists = playlists.generate(configure_songs)
create_playlists.main()
