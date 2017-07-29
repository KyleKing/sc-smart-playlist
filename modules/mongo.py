import pprint

import pymongo
import utils
from tinydb import TinyDB


class Tiny(object):
    """TinyDB Tools"""

    def __init__(self, pth):
        """Create database file
            pth (str): TinyDB filename
        """
        self.db = TinyDB(pth)

    def purge(self):
        """Clear out all db entries"""
        self.db.purge()

    def close(self):
        """Release db file"""
        self.db.close()

    def insert(self, _obj):
        """Insert into database with additional checks
            _obj (dict): new object to insert
        """
        if "_id" in _obj:
            _obj["_id"] = "N/A"  # Remove non-ascii MongoDB "_id"
        self.db.insert(_obj)

    def upsert(self, _obj, _query):
        """Insert to TinyDB if new -or- update if already present
            _obj (dict): new object to update/insert
            _query (dict): TinyDB query syntax
        """
        if _query and self.db.contains(_query):
            # Attempt to update the existing entry
            if self.db.count(_query) > 1:
                raise ValueError("Multiple matches with `{}`".format(_query))
            self.db.update(_obj, _query)
        else:
            # Insert new, unique entry
            self.db.insert(_obj)


class MongoDB(object):
    """MongoDB Tools"""

    def __init__(self, db_name, collection_name):
        """Use default client (27017) - `mongod` instance must be running
            db_name (str): MongoDB Databse Name
            collection_name (str): MongoDB Collection Name w/in database
        """
        self.client = pymongo.MongoClient("localhost", 27017)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def purge(self):
        """Purge all db entries"""
        self.collection.remove()
        print "Cleared", self.db.name, "in col:", self.collection

    # --------------------------------------------------------------------------
    # Debugging

    def info(self):
        """Print a short table of all collections and db's within client"""
        for name in self.client.database_names():
            if name not in ["admin", "local"]:
                print("DB Name: {}".format(name))
                for col in self.client[name].collection_names():
                    _c = self.client[name][col].count()
                    print("- C: {:04} N: {}".format(_c, col))

    def debug(self, query={}, log=True):
        """Log database entries to TinyDB file
            query (dict): MongoDB search parameters
            log (bool): optionally print information to console
        """
        db = Tiny(utils.check_tmp_dir("../tmp/db_dump.json"))
        db.purge()
        for idx, match in enumerate(self.collection.find(query)):
            match["0_debug"] = idx
            db.insert(match)
            if log:
                pprint.pprint(match)
            if idx > 5:
                break
        db.close()

    # --------------------------------------------------------------------------
    # Create/Update/Delete Operations

    def insert_one(self, obj):
        """Insert a single db entry
            obj (dict): dictionary to insert
        """
        return self.collection.insert_one(obj)

    def set(self, query, obj):
        """Update a field of a db entry
            query (dict): MongoDB search parameters
            obj (dict): parameters to update
        """
        return self.collection.update(query, {"$set": obj})

    def delete_many(self, query):
        """Delete all matching db entries
            query (dict): MongoDB search parameters
        """
        return self.collection.delete_many(query)

    def delete_one(self, query):
        """Delete a single matching db entry
            query (dict): MongoDB search parameters
        """
        return self.collection.delete_one(query)

    # Other Update Operations:
    # https://docs.mongodb.com/manual/reference/operator/update/

    # --------------------------------------------------------------------------
    # Read operations

    def find_one(self):
        """Return the first db entry"""
        item = self.collection.find_one()
        return item

    def find(self, query={}):
        """Return all matching db entries
            query (dict): MongoDB search parameters
        """
        # self.debug(query)
        items = self.collection.find(query)
        return items

    def count(self, query):
        """Count the number of matching db entries
            query (dict): MongoDB search parameters
        """
        num_items = self.collection.count(query)
        print("{} items matched {}".format(num_items, query))
        return num_items

    def _k_v(self, query, key):
        """Analyze database entries for a single key
            query (dict): MongoDB search parameters
            key (str): dictionary key to parse
        """
        values = self.find(query)
        return [value[key] for value in values]


if __name__ == "__main__":
    """Manual tests"""
    db_songs = MongoDB("smart_pl", "song_collection")
    db_songs.debug(obj={"id": 305264444}, log=False)
