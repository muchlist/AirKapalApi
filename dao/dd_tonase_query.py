from db import mongo


def get_tonase(branch: str, locate: str) -> dict:
    query = {
        "branch": branch,
        "locate": locate,
    }
    tonase = mongo.db.water_state.find_one(query, {"end_tonase": 1})
    return tonase
