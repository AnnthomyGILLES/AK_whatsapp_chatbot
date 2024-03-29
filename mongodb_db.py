import datetime
import logging
import os

import pymongo
from pymongo import ReturnDocument

from utils import load_config

load_config()
database_uri = os.getenv("DATABASE_URI")


class DuplicateUser(Exception):
    pass


class NoUserPhoneNumber(Exception):
    pass


MONGODB_HOSTNAME = os.getenv("MONGODB_HOSTNAME")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

client = pymongo.MongoClient(
    database_uri.format(
        MONGODB_USERNAME=MONGODB_USERNAME,
        MONGODB_PASSWORD=MONGODB_PASSWORD,
        MONGODB_HOSTNAME=MONGODB_HOSTNAME,
        MONGODB_DATABASE=MONGODB_DATABASE,
    )
)


class UserCollection:
    def __init__(self, collection_name):
        self.db = client["mydatabase"]
        self.collection = self.db[collection_name]

    def delete_document(self, query):
        return self.collection.delete_one(query)

    def increment_nb_tokens_messages(self, doc, amount):
        # increment the field by the specified amount for the specified document
        timestamp = datetime.datetime.utcnow()
        self.collection.update_one(
            {"_id": doc["_id"]},
            {
                "$inc": {"nb_tokens": amount, "nb_messages": 1},
                "$set": {"timestamp_last_messages": timestamp},
            },
        )

    def reset_tokens(self):
        # get today's date
        today_timestamp = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        # reset nb_tokens field to 0 for all documents where current_period_end is older than today
        result = self.collection.update_many(
            {"current_period_end": {"$lt": today_timestamp}}, {"$set": {"nb_tokens": 0}}
        )
        logging.info(f"{result.modified_count} tokens resetted.")

    def update_user_history(self, phone_number, message=None):
        query = {"phone_number": phone_number}
        update = {"$set": {"history": message}}
        self.collection.find_one_and_update(
            query, update, upsert=True, return_document=ReturnDocument.AFTER
        )

    def find_document(self, field_name, field_value):
        # search for a document with a specific field value
        doc = self.collection.find_one({field_name: field_value})
        return doc

    def get_user_id_with_phone_number(self, phone_number):
        doc = self.find_document("phone_number", phone_number)
        if doc:
            return doc["_id"]

    def add_user(self, phone_number, current_period_end=None, history=None):
        if history is None:
            history = []

        if phone_number is None:
            raise NoUserPhoneNumber("Provide a valid phone number.")
        if current_period_end is not None:
            current_period_end = datetime.datetime.utcfromtimestamp(current_period_end)
        user_id = self.get_user_id_with_phone_number(phone_number)
        user = {
            "phone_number": phone_number,
            "history": history,
            "current_period_end": current_period_end,
            "nb_tokens": 0,
            "nb_messages": 0,
            "is_blocked": False,
            "datetime_created": datetime.datetime.utcnow(),
        }

        try:
            if user_id is None:
                result = self.collection.insert_one(user)
                return result.inserted_id
            else:
                self.collection.update_one(
                    {"_id": user_id},
                    {"$set": user},
                )

        except pymongo.errors.DuplicateKeyError:
            raise DuplicateUser(f"Following user already exist: {phone_number}")

    def get_user(self, user_id):
        return self.collection.find_one({"_id": user_id})

    # TODO run on a daily basis
    def delete_ended_subsciption(self):
        # Get today's date and time as a datetime object
        # today_timestamp = datetime.datetime.timestamp(
        #     datetime.datetime.today() - datetime.timedelta(hours=24)
        # )
        today_timestamp = datetime.datetime.utcnow().timestamp()
        # Delete documents where the current_period_end field is older than today's date
        result = self.collection.delete_many(
            {"current_period_end": {"$lt": today_timestamp}}
        )
        logging.info(f"Deleted {result.deleted_count} documents.")

    def list_all_users(self):
        return list(self.collection.find({}))

    def block_user(self, user_id):
        self.collection.update_one(
            {"_id": user_id},
            {"$set": {"is_blocked": True}},
        )


if __name__ == "__main__":
    # Initialize the UserCollection with the specified collection name
    users = UserCollection("users")

    # Add user
    user = {
        "phone_number": "1234567890",
        "current_period_end": 1682564177,
        "history": None,
    }
    _ = users.add_user(**user)

    user_id = users.get_user_id_with_phone_number("1234567890")

    # call the add_history function to update the user's history field
    users.update_user_history(user_id, "User created")
    users.update_user_history(user_id, "User logged in")

    res = users.get_user(user_id)
    print(res)
