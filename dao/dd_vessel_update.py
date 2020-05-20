from bson.objectid import ObjectId

from db import mongo


def insert_vessel(data: dict):
    data_insert = {
        "ship_name": data["ship_name"].upper(),
        "agent": data["agent"].upper(),
        "isInternational": data["isInternational"],
        "isActive": data["isActive"]
    }
    mongo.db.vessel.insert_one(data_insert)


def change_vessel(data: dict) -> dict:
    data_to_change = {
        "ship_name": data["ship_name"].upper(),
        "agent": data["agent"].upper(),
        "isInternational": data["isInternational"],
        "isActive": data["isActive"]
    }
    mongo.db.vessel.update_one({'_id': ObjectId(vessel_id)}, {
        '$set': data_to_change})
    data_to_change["_id"] = vessel_id

    return data_to_change
