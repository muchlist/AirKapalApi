from db import mongo


def insert_user(data: dict):
    data_insert = {
        "username": data["username"].upper(),
        "password": data["password"],
        "email": data["email"],
        "name": data["name"].upper(),
        "isAdmin": data["isAdmin"],
        "isManager": data["isManager"],
        "isTally": data["isTally"],
        "isAgent": data["isAgent"],
        "branch": data["branch"].upper(),
        "company": data["company"].upper(),
    }

    mongo.db.users_ak.insert_one(data_insert)


def put_password(username: str, new_password: str):
    query = {"username": username}
    update = {'$set': {"password": new_password}}

    mongo.db.users_ak.update_one(query, update)


def update_user(username: str, data: dict):
    find = {"username": username}
    update = {
        "name": data["name"].upper(),
        "email": data["email"],
        "isAdmin": data["isAdmin"],
        "isAgent": data["isAgent"],
        "isTally": data["isTally"],
        "isManager": data["isManager"],
        "branch": data["branch"].upper(),
        "company": data["company"].upper(),
    }

    mongo.db.users_ak.update_one(find, {'$set': update})


def delete_user(username: str):
    mongo.db.users_ak.remove({"username": username})
