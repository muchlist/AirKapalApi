from bson.objectid import ObjectId

from db import mongo


def get_water(id_water: str) -> dict:
    result = mongo.db.waters.find_one(
        {'_id': ObjectId(id_water)})
    return result


def get_water_by_job_number(job_number: str) -> dict:
    result = mongo.db.waters.find_one(
        {"job_number": job_number}, {"job_number": 1})
    return result


def get_waters_with_filter(branch_arg: str,
                           agent_arg: str,
                           search_arg: str,
                           page_arg: str,
                           ) -> list:

    # SETUP PAGGING START
    LIMIT = 30
    page_number = 1
    if page_arg:
        page_number = int(page_arg)
    # SETUP PAGGING END

    # SETUP DATA FIND START
    find = {}

    if branch_arg:
        find["branch"] = branch_arg
    if agent_arg:
        find["vessel.agent"] = agent_arg
    if search_arg:
        find["vessel.vessel_name"] = {'$regex': f'.*{search_arg}.*'}

    water_cursor = mongo.db.waters.find(find).skip(
        (page_number - 1) * LIMIT).limit(LIMIT).sort("_id", -1)

    water_list = []

    for water in water_cursor:
        water_list.append(water)

    return water_list
