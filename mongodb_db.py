import os
from pathlib import Path

import pymongo
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(".env"))


class DuplicateUser(Exception):
    pass


class NoUserPhoneNumber(Exception):
    pass


MONGODB_HOSTNAME = os.getenv("MONGODB_HOSTNAME")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

# create a MongoDB client and connect to the database
client = pymongo.MongoClient(
    host=MONGODB_HOSTNAME,
    port=27017,
    username=MONGODB_USERNAME,
    password=MONGODB_PASSWORD,
    authSource=MONGODB_DATABASE,
)
db = client["mydatabase"]

# define the collection and document structure
users = db["users"]


# delete a document
def delete_document(query):
    return users.delete_one(query)


def keep_last_n_records(n=4):
    # Update all documents in the collection
    for document in users.find():
        history = document["history"]
        updated_history = history[-n:]  # Keep only the last three records
        users.update_one(
            {"_id": document["_id"]}, {"$set": {"history": updated_history}}
        )


def update_history(user_id, message):
    query = {"_id": user_id}
    update = {"$set": {"history": message}}
    _ = users.find_one_and_update(query, update, upsert=True)


# define a function for getting the user id based on phone number
def get_user_id_with_phone_number(phone_number):
    query = {"phone_number": phone_number}
    projection = {"_id": 1}
    result = users.find_one(query, projection)
    if result:
        return result["_id"]
    else:
        return None


# define a function for adding a new user document
def add_user(phone_number, current_period_end, history=None):
    if history is None:
        history = []

    if phone_number is None:
        raise NoUserPhoneNumber("Provide a valid phone number.")
    user = {
        "phone_number": phone_number,
        "history": history,
        "current_period_end": current_period_end,
    }
    try:
        result = users.insert_one(user)
        return result.inserted_id
    except pymongo.errors.DuplicateKeyError:
        raise DuplicateUser(f"Following user already exist: {phone_number}")


def get_user(user_id):
    return users.find_one({"_id": user_id})


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
    update_history(user_id, "User created")
    update_history(user_id, "User logged in")

    res = get_user(user_id)
    print(res)
