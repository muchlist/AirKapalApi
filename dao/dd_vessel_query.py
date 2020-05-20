from bson.objectid import ObjectId

from db import mongo


def search_vessel(name: str) -> list:
    query_string = {'$regex': f'.*{search}.*'}
    vessel_collection = mongo.db.vessel.find(
        {"ship_name": query_string}
    )

    vessels = []
    for vessel in vessel_collection:
        vessels.append(vessel)

    return vessels


def get_vessel(vessel_id: str):
    ship = mongo.db.vessel.find_one({'_id': ObjectId(vessel_id)})
    return ship


def get_vessel_list() -> list:

    vessel_collection = mongo.db.vessel.find()
    vessels = []
    for vessel in vessel_collection:
        vessels.append(vessel)

    return vessels
