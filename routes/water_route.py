from db import mongo

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)
from marshmallow import ValidationError
from bson.objectid import ObjectId
from validations import role_validation as valid

from schemas.water import (
    WaterCreateSchema,
    WaterEditSchema,
)

from datetime import datetime

# Set up a Blueprint
bp = Blueprint('water_bp', __name__, url_prefix='/api')


"""
-------------------------------------------------------------------------------
Mengecek apakah job number sudah ada
-------------------------------------------------------------------------------
"""


def job_number_exist(job_number):
    result = mongo.db.waters.find_one(
        {"job_number": job_number}, {"job_number": 1})
    if result:
        return True
    return False


"""
-------------------------------------------------------------------------------
Memunculkan water list , dan membuat water order
-------------------------------------------------------------------------------
"""
@bp.route('/waters', methods=['GET', 'POST'])
@jwt_required
def waters():
    """
    -------------------------------------------------------------------------------
    POST membuat water order
    -------------------------------------------------------------------------------
    """
    if request.method == 'POST':

       # VALIDASI START
        if not valid.isTally(get_jwt_claims()):
            return {"message": "user tidak memiliki hak akses untuk menambahkan data"}, 403

        schema = WaterCreateSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400
        # VALIDASI END

        # Mengecek apakah job number sudah pernah dibuat
        if job_number_exist(data["job_number"].strip().upper()):
            return {"message": "Nomer job ini sudah terpakai"}, 404

        # SETUP DATA INSERT START
        volume_embed = {
            "tonase_ordered": data["tonase_ordered"],
            "tonase_begin": None,
            "tonase_begin_time": None,
            "tonase_end": None,
            "tonase_end_time": None,
            "tonase_real": None,
            "tonase_wrong": None,
        }
        vessel_embed = {
            "vessel_name": data["vessel_name"].upper(),
            "vessel_id": data["vessel_id"],
            "agent": data["agent"].upper(),
            "int_dom": data["int_dom"],
        }
        photo_embed = {
            "begin_photo": "",
            "end_photo": "",
            "witness_photo": "",
        }
        approval_embed = {
            "approval_name": "",
            "approval_id": "",
            "approval_time": None,
            "created_by": get_jwt_claims()["name"],
            "created_by_id": get_jwt_identity(),
        }
        data_insert = {
            "job_number": data["job_number"].strip().upper(),
            "locate": data["locate"].upper(),
            "branch": get_jwt_claims()["branch"],
            "created_at": data["created_at"],
            "updated_at": datetime.now(),
            "doc_level": 1,
            "suspicious": False,
            "photos": photo_embed,
            "vessel": vessel_embed,
            "approval": approval_embed,
            "volume": volume_embed,
        }
        # SETUP DATA INSERT END

        # DATABASE START
        try:
            id = mongo.db.waters.insert_one(data_insert).inserted_id
        except:
            return {"message": "galat ketika memasukkan ke database"}, 500
        # DATABASE END

        return {"message": id}, 201

    """
    -------------------------------------------------------------------------------
    GET Memunculkan water list
            ?branch=SAMPIT
            &  agent=MERATUS 
            &  page=1
            &  search=""
    -------------------------------------------------------------------------------
    """
    if request.method == 'GET':

        branch = request.args.get("branch")
        agent = request.args.get("agent")
        search = request.args.get("search")

        # SETUP PAGGING START
        page_number = 1
        page = request.args.get("page")
        LIMIT = 30
        if page:
            page_number = int(page)
        # SETUP PAGGING END

        # SETUP DATA FIND START
        find = {}

        if branch:
            find["branch"] = branch
        if agent:
            find["vessel.agent"] = agent
        if search:
            find["vessel.vessel_name"] = {'$regex': f'.*{search}.*'}
        # SETUP DATA FIND END

        water_cursor = mongo.db.waters.find(find).skip(
            (page_number - 1) * LIMIT).limit(LIMIT).sort("_id", -1)

        water_list = []

        for water in water_cursor:
            water_list.append(water)

        return {"waters": water_list}, 200


"""
-------------------------------------------------------------------------------
Detail , Mengubah dan Menghapus
-------------------------------------------------------------------------------
"""
@bp.route('/waters/<id_water>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required
def get_water_detail(id_water):

    if not ObjectId.is_valid(id_water):
        return {"message": "Object ID tidak valid"}, 400

    """
    -------------------------------------------------------------------------------
    Get , Detail water
    -------------------------------------------------------------------------------
    """
    if request.method == 'GET':
        water = mongo.db.waters.find_one(
            {'_id': ObjectId(id_water)})
        return jsonify(water), 200

    """
    -------------------------------------------------------------------------------
    Put , merubah air
    -------------------------------------------------------------------------------
    """
    if request.method == 'PUT':

        # VALIDASI INPUT START
        schema = WaterEditSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if not valid.isTally(get_jwt_claims()):
            return {"message": "User tidak memiliki hak akses untuk mengedit"}, 403
        # VALIDASI INPUT END

        # SET UP DATA TO CHANGE START
        data_to_change = {
            "job_number": data["job_number"],
            "locate": data["locate"].upper(),
            "created_at": data["created_at"],
            "updated_at": datetime.now(),

            "vessel.vessel_name": data["vessel_name"].upper(),
            "vessel.vessel_id": data["vessel_id"],
            "vessel.agent": data["agent"].upper(),
            "vessel.int_dom": data["int_dom"],

            "approval.created_by": get_jwt_claims()["name"],
            "approval.created_by_id": get_jwt_identity(),

            "volume.tonase_ordered": data["tonase_ordered"],
        }
        # SET UP DATA TO CHANGE END

        # DATABASE START
        query = {'_id': ObjectId(id_water),
                 # Memastikan dokumen tidak diedit orang sebelumnya
                 "updated_at": data["updated_at"],
                 'branch': get_jwt_claims()["branch"],
                 "doc_level": 1}  # Hanya document lvl 1 yang bisa diubah
        update = {'$set': data_to_change}

        water = mongo.db.waters.find_one_and_update(
            query, update, return_document=True)
        # DATABASE END

        if water is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap muat ulang data terbaru!"}, 402

        return jsonify(water), 201

    """
    -------------------------------------------------------------------------------
    Delete , menghapus water
    hanya dapat dilakukan oleh tally dan di doc_level 1
    -------------------------------------------------------------------------------
    """
    if request.method == 'DELETE':

        if not valid.isTally(get_jwt_claims()):
            return {"message": "Tidak memiliki hak akses untuk menghapus"}, 403

        query = {'_id': ObjectId(id_water),
                 'branch': get_jwt_claims()["branch"],
                 'doc_level': 1}

        water = mongo.db.waters.find_one_and_delete(query)

        if water is None:
            return {"message": "Dokumen yang sudah disetujui tidak dapat dihapus"}, 406
        return {"message": "Dokumen berhasil di hapus"}, 204
