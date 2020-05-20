from datetime import datetime

from bson.objectid import ObjectId

from db import mongo


def insert(data: dict) -> str:
    volume_embed = {
        "tonase_ordered": data["tonase_ordered"],
        "tonase_start": None,
        "tonase_start_time": None,
        "tonase_end": None,
        "tonase_end_time": None,
        "tonase_real": None,
        "tonase_difference": None,
    }
    vessel_embed = {
        "vessel_name": data["vessel_name"].upper(),
        "vessel_id": data["vessel_id"],
        "agent": data["agent"].upper(),
        "int_dom": data["int_dom"],
    }
    photo_embed = {
        "start_photo": "",
        "end_photo": "",
        "witness_photo": "",
    }
    approval_embed = {
        "approval_name": "",
        "approval_id": "",
        "approval_time": None,
        "created_by": data["created_by"],
        "created_by_id": data["created_by_id"],
        "witness_name": "",
    }
    data_insert = {
        "job_number": data["job_number"].strip().upper(),
        "locate": data["locate"].upper(),
        "branch": data["branch"],
        "created_at": data["created_at"],
        "updated_at": datetime.now(),
        "doc_level": 1,
        "suspicious": False,
        "suspicious_note": "",
        "photos": photo_embed,
        "vessel": vessel_embed,
        "approval": approval_embed,
        "volume": volume_embed,
    }

    try:
        id = mongo.db.waters.insert_one(data_insert).inserted_id
    except:
        return None

    return id


def update_water(data: dict) -> dict:
    data_to_change = {
        "job_number": data["job_number"],
        "locate": data["locate"].upper(),
        "created_at": data["created_at"],
        "updated_at": datetime.now(),

        "vessel.vessel_name": data["vessel_name"].upper(),
        "vessel.vessel_id": data["vessel_id"],
        "vessel.agent": data["agent"].upper(),
        "vessel.int_dom": data["int_dom"],

        "approval.created_by": data["approval.created_by"],
        "approval.created_by_id": data["approval.created_by_id"],

        "volume.tonase_ordered": data["tonase_ordered"],
    }

    query = {'_id': ObjectId(data["_id"]),
             # Memastikan dokumen tidak diedit orang sebelumnya
             "updated_at": data["updated_at"],
             'branch': data["branch"],
             "doc_level": 1}  # Hanya document lvl 1 yang bisa diubah
    update = {'$set': data_to_change}

    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True)

    return water


def find_delete(id_water: str, branch: str) -> dict:
    query = {'_id': ObjectId(id_water),
             'branch': branch,
             'doc_level': 1}

    water = mongo.db.waters.find_one_and_delete(query)
    return water


def insert_tonase_start(data: dict) -> dict:
    query = {
        '_id': ObjectId(data['_id']),
        "doc_level": 1,
        "branch": data["branch"],
    }
    update = {
        '$set': {
            "updated_at": datetime.now(),
            "approval.created_by": data["approval.created_by"],
            "approval.created_by_id": data["approval.created_by_id"],
            "volume.tonase_start": data["tonase"],
            "volume.tonase_start_time": data["time"],
            "volume.tonase_difference": data["volume.tonase_difference"],
        }
    }

    # DATABASE
    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    return water


def insert_tonase_end(data: dict) -> dict:
    query = {
        '_id': ObjectId(data['_id']),
        "doc_level": 1,
        "branch": data["branch"],
    }
    update = {
        '$set': {
            "updated_at": datetime.now(),
            "approval.created_by": data["approval.created_by"],
            "approval.created_by_id": data["approval.created_by_id"],
            "volume.tonase_end": data["tonase"],
            "volume.tonase_end_time": data["time"],
        }
    }

    # DATABASE
    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    return water


def update_witness_approval(data: dict) -> dict:
    query = {
        '_id': ObjectId(data["_id"]),
        "updated_at": data["updated_at"],
        "doc_level": 1,
        "branch": data["branch"],
    }
    update = {
        '$set': {"doc_level": 2,
                 "approval.created_by": data["approval.created_by"],
                 "approval.created_by_id": data["approval.created_by_id"],
                 "approval.witness_name": data["name"].upper(),
                 "updated_at": datetime.now()}
    }

    # DATABASE
    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    return water


def update_tally_approval(data: dict) -> dict:
    query = {
        '_id': ObjectId(data["_id"]),
        "updated_at": data["updated_at"],
        "doc_level": 2,
        "branch": data["branch"],
    }
    update = {
        '$set': {"doc_level": 3,
                 "approval.created_by": data["approval.created_by"],
                 "approval.created_by_id": data["approval.created_by_id"],
                 "updated_at": datetime.now()}
    }

    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    return water


def update_manager_approval(data: dict) -> dict:
    query = {
        '_id': ObjectId(data["_id"]),
        "updated_at": data["updated_at"],
        "doc_level": 3,
        "branch": data["branch"],
    }
    update = {
        '$set': {"doc_level": 4,
                 "approval.approval_name": data["approval.approval_name"],
                 "approval.approval_id": data["approval.approval_id"],
                 "approval.approval_time": data["new_updated_at"],
                 "updated_at": datetime.now()}
    }

    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    return water


def update_real_tonase(water_id: str,
                       real_tonase: int,
                       suspicious: bool,
                       suspicious_note: str) -> dict:
    query = {
        '_id': ObjectId(water_id),
    }
    update = {
        '$set': {"doc_level": 3,
                 "volume.tonase_real": real_tonase,
                 "suspicious": suspicious,
                 "suspicious_note": suspicious_note,
                 }
    }

    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    return water


def update_photo(water_id: str, key_image: str, image_path: str) -> dict:
    water_doc = mongo.db.waters.find_one_and_update(
        {'_id': ObjectId(water_id)},
        {'$set': {key_image: image_path}}, {'_id': 1}
    )

    return water_doc
