import pymongo

# create a MongoDB client and connect to the database
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mydatabase"]

# define the collection and document structure
users = db["users"]


def add_history(user_id, message):
    query = {"_id": user_id}
    update = {"$set": {"history": message}}
    result = users.find_one_and_update(query, update, upsert=True)
    print("ok")
    # print("Updated", result.modified_count, "document(s)")


# define a function for getting the user id based on phone number
def get_user_id(phone_number):
    query = {"phone_number": phone_number}
    projection = {"_id": 1}
    result = users.find_one(query, projection)
    if result:
        return result["_id"]
    else:
        return None


# define a function for adding a new user document
def add_user(phone_number, is_active=False, history=None):
    if history is None:
        history = []
    user = {
        "phone_number": phone_number,
        "is_active": is_active,
        "history": history,
    }
    result = users.insert_one(user)
    return result.inserted_id


def get_user(user_id):
    return users.find_one({"_id": user_id})


if __name__ == "__main__":
    # Add user
    user = {"phone_number": "1234567890", "is_active": True, "history": None}
    _ = add_user(**user)

    user_id = get_user_id("1234567890")

    # call the add_history function to update the user's history field
    add_history(user_id, "User created")
    add_history(user_id, "User logged in")

    res = get_user(user_id)
    print(res)
