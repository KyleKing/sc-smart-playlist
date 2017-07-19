import pprint

import pymongo
from tinydb import TinyDB


class Tiny(object):
    """TinyDB Tools"""

    def __init__(self, pth):
        """Create database file"""
        self.db = TinyDB(pth)

    def purge(self):
        """Clear out all db entries"""
        self.db.purge()

    def insert(self, _obj):
        """Insert into database with additional checks"""
        if '_id' in _obj:
            _obj['_id'] = 'N/A'  # Remove non-ascii MongoDB '_id'
        self.db.insert(_obj)

    def upsert(self, _obj, _query):
        """Insert to TinyDB if new -or- update if already present"""
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

    def __init__(self, db_name="ita_analysis", collection_name="ecl_data"):
        """Use default client (27017) - `mongod` instance must be running"""
        self.client = pymongo.MongoClient("localhost", 27017)
        # Set Database Name, then Collection Name
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def purge(self):
        """Purge all db entries"""
        self.collection.remove()
        print 'Cleared', self.db.name, 'in col:', self.collection

    # --------------------------------------------------------------------------
    # Debugging

    def info(self):
        for name in self.client.database_names():
            if name not in ['admin', 'local']:
                print('DB Name: {}'.format(name))
                for col in self.client[name].collection_names():
                    _c = self.client[name][col].count()
                    print('- C: {:04} N: {}'.format(_c, col))

    def debug(self, obj={}, log=True):
        db = Tiny('./db_dump.json')
        db.purge()
        for idx, match in enumerate(self.collection.find(obj)):
            match["0_debug"] = idx
            db.insert(match)
            if log:
                pprint.pprint(match)
            if idx > 5:
                break

    # --------------------------------------------------------------------------
    # Create/Update/Delete Operations

    def insert_one(self, obj):
        return self.collection.insert_one(obj)

    def set(self, query, obj):
        return self.collection.update(query, {'$set': obj})

    def delete_many(self, obj):
        return self.collection.delete_many(obj)

    def delete_one(self, obj):
        return self.collection.delete_one(obj)

    # Other Update Operations:
    # https://docs.mongodb.com/manual/reference/operator/update/

    # --------------------------------------------------------------------------
    # Read operations

    def find_one(self):
        item = self.collection.find_one()
        # pprint.pprint(item)
        return item

    def find(self, query={}):
        # self.debug(query)
        items = self.collection.find(query)
        return items

    def count(self, query):
        num_items = self.collection.count(query)
        print("{} items matched {}".format(num_items, query))
        return num_items

    def _k_v(self, query, key):
        values = self.find(query)
        for value in values:
            print value[key]
        return values


if __name__ == "__main__":
    db_songs = MongoDB("test_database", "test_collection")
    db_songs.debug(log=False)
