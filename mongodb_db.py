import configparser
import datetime
import os

import pymongo
from dotenv import load_dotenv
from loguru import logger

ENV = os.getenv("ENV", "DEVELOPMENT")

# Read the configuration file
config = configparser.ConfigParser()
config.read("config.ini")
env_path = config[env]["ENV_FILE_PATH"]
database_uri = config[env]["DATABASE_URI"]

load_dotenv(dotenv_path=env_path)


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
db = client["mydatabase"]

# define the collection and document structure
users = db["users"]


# delete a document
def delete_document(query):
    return users.delete_one(query)


def reset_document(doc):
    # check if a matching document was found
    if doc:
        # add a new "timestamp" field to the document with the current time
        timestamp = datetime.datetime.utcnow()
        users.update_one(
            {"_id": doc["_id"]},
            {"$set": {"history_timestamp": timestamp, "history": []}},
        )
        logger.info(f"Added timestamp {timestamp} to document {doc['_id']}")
    else:
        logger.info("No matching document found.")


def increment_nb_tokens(doc, amount):
    # increment the field by the specified amount for the specified document
    users.update_one({"_id": doc["_id"]}, {"$inc": {"nb_tokens": amount}})


def reset_tokens():
    # get today's date
    today_timestamp = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    # reset nb_tokens field to 0 for all documents where current_period_end is older than today
    result = users.update_many(
        {"current_period_end": {"$lt": today_timestamp}}, {"$set": {"nb_tokens": 0}}
    )
    logger.info(f"{result.modified_count} tokens resetted.")


def update_user_history(phone_number, message=None):
    query = {"phone_number": phone_number}
    update = {"$set": {"history": message}}
    _ = users.find_one_and_update(query, update, upsert=True)


def find_document(field_name, field_value):
    # search for a document with a specific field value
    doc = users.find_one({field_name: field_value})

    # return the document if it was found
    if doc:
        return doc
    return None


# define a function for getting the user id based on phone number
def get_user_id_with_phone_number(phone_number):
    doc = find_document("phone_number", phone_number)
    if doc:
        return doc["_id"]


# define a function for adding a new user document
def add_user(phone_number, current_period_end, history=None):
    if history is None:
        history = []

    if phone_number is None:
        raise NoUserPhoneNumber("Provide a valid phone number.")
    current_period_end = datetime.datetime.utcfromtimestamp(current_period_end)
    user = {
        "phone_number": phone_number,
        "history": history,
        "current_period_end": current_period_end,
        "nb_tokens": 0,
    }
    try:
        result = users.insert_one(user)
        return result.inserted_id
    except pymongo.errors.DuplicateKeyError:
        raise DuplicateUser(f"Following user already exist: {phone_number}")


def get_user(user_id):
    return users.find_one({"_id": user_id})


# TODO run on a daily basis
def delete_ended_subsciption():
    # Get today's date and time as a datetime object
    today_timestamp = datetime.datetime.timestamp(
        datetime.datetime.today() - datetime.timedelta(hours=24)
    )
    # Delete documents where the current_period_end field is older than today's date
    result = users.delete_many({"current_period_end": {"$lt": today_timestamp}})
    logger.info(f"Deleted {result.deleted_count} documents.")


if __name__ == "__main__":
    # Add user
    user = {
        "phone_number": "1234567890",
        "current_period_end": 1682564177,
        "history": None,
    }
    _ = add_user(**user)

    user_id = get_user_id_with_phone_number("1234567890")

    # call the add_history function to update the user's history field
    update_user_history(user_id, "User created")
    update_user_history(user_id, "User logged in")

    res = get_user(user_id)
    print(res)
