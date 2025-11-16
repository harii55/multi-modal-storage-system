import os
from pymongo import MongoClient as PyMongoClient

class MongoClient:
    def __init__(self):
        mongo_user = os.getenv("MONGO_USER", "admin")
        mongo_pass = os.getenv("MONGO_PASS", "password")
        mongo_host = os.getenv("MONGO_HOST", "localhost")
        mongo_port = os.getenv("MONGO_PORT", "27017")
        mongo_db = os.getenv("MONGO_DB", "main")
        
        # Connection string with authentication
        connection_string = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"
        
        self.client = PyMongoClient(connection_string)
        self.db = self.client[mongo_db]
    
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        return self.db[collection_name]
    
    def insert_one(self, collection_name, document):
        """Insert a single document"""
        collection = self.get_collection(collection_name)
        return collection.insert_one(document)
    
    def find_one(self, collection_name, query):
        """Find a single document"""
        collection = self.get_collection(collection_name)
        return collection.find_one(query)
    
    def find_many(self, collection_name, query, limit=None):
        """Find multiple documents"""
        collection = self.get_collection(collection_name)
        cursor = collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def update_one(self, collection_name, query, update):
        """Update a single document"""
        collection = self.get_collection(collection_name)
        return collection.update_one(query, {"$set": update})
    
    def delete_one(self, collection_name, query):
        """Delete a single document"""
        collection = self.get_collection(collection_name)
        return collection.delete_one(query)
    
    def create_validator(self, collection_name, validator):
        """Create or update collection validator for schema validation"""
        try:
            # Try to create collection
            self.db.create_collection(collection_name)
        except Exception:
            # Collection already exists
            pass
        
        try:
            # Apply validator
            cmd = {
                'collMod': collection_name,
                'validator': validator,
                'validationLevel': 'moderate'
            }
            self.db.command(cmd)
        except Exception:
            # Try creating with validator option on create
            try:
                self.db.create_collection(collection_name, validator=validator)
            except Exception:
                pass
    
    def close(self):
        """Close the connection"""
        self.client.close()
