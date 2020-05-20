from db import mongo


def insert(data: dict) -> bool:  # RETURN OK
    query = {
        "branch": data["branch"],
        "locate": data["locate"],
    }
    update = {
        '$set':
        {
            "start_date": data["start_date"],
            "start_tonase": data["start_tonase"],
            "end_tonase": data["start_tonase"],
            "updated_by": get_jwt_claims()["name"],
            "last_update": datetime.now(),
        },
    }
    try:
        mongo.db.water_state.update(query, update, upsert=True)
    except:
        return False

    return True


def update(branch: str, locate: str, end_tonase: int):
    query = {
        "branch": branch,
        "locate": locate,
    }
    update = {
        '$set': {
            "end_tonase": end_tonase,
        }
    }
    mongo.db.water_state.update_one(query, update)
