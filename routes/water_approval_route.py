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
    WaterApprovalSchema,
    WaterApprovalWitnessNameSchema,
    WaterApprovalWitnessSchema
)

from datetime import datetime

# Set up a Blueprint
bp = Blueprint('water_approval_bp', __name__, url_prefix='/api')


"""
-------------------------------------------------------------------------------
APPROVAL mengganti nama Saksi
-------------------------------------------------------------------------------
"""
@bp.route('/water-approval/name/<water_id>', methods=['POST'])
@jwt_required
def check_to_ready_doc(water_id):

    # VALIDATE START
    claims = get_jwt_claims()

    if not valid.isTally(claims):
        return {"message": "User tidak memiliki hak akses untuk menyetujui dokumen ini"}, 403

    schema = WaterApprovalWitnessNameSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400
    # VALIDATE END

    query = {
        '_id': ObjectId(water_id),
        # less than 3 artinya masih dalam approval saksi
        "doc_level": {"$lt": 3},
        "branch": claims["branch"],
    }
    update = {
        '$set': {"approval.witness_name": data["name"].upper(),
                 "approval.created_by": get_jwt_claims()["name"],
                 "approval.created_by_id": get_jwt_identity(),

                 "updated_at": datetime.now()}
    }

    # DATABASE
    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    if water is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402

    return jsonify(water), 201


"""
-------------------------------------------------------------------------------
APPROVAL Saksi dari lvl 1 ke lvl 2
memasukkan nama sebelum memencet tombol di android
-------------------------------------------------------------------------------
"""
@bp.route('/water-approval/sign/<water_id>', methods=['POST'])
@jwt_required
def witness_approved(water_id):

    # VALIDATE START
    claims = get_jwt_claims()

    if not valid.isTally(claims):
        return {"message": "User tidak memiliki hak akses untuk menyetujui dokumen ini"}, 403

    schema = WaterApprovalWitnessSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400
    # VALIDATE END

    query = {
        '_id': ObjectId(water_id),
        "updated_at": data["updated_at"],
        "doc_level": 1,
        "branch": claims["branch"],
    }
    update = {
        '$set': {"doc_level": 2,
                 "approval.created_by": get_jwt_claims()["name"],
                 "approval.created_by_id": get_jwt_identity(),
                 "approval.witness_name": data["name"].upper(),
                 "updated_at": datetime.now()}
    }

    # DATABASE
    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    if water is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402

    return jsonify(water), 201


"""
-------------------------------------------------------------------------------
APPROVAL Tally dari lvl 2 ke lvl 3
-------------------------------------------------------------------------------
"""
@bp.route('/water-approval/ready/<water_id>', methods=['POST'])
@jwt_required
def tally_approved(water_id):

    # VALIDATE START
    claims = get_jwt_claims()

    if not valid.isTally(claims):
        return {"message": "User tidak memiliki hak akses untuk menyetujui dokumen ini"}, 403

    schema = WaterApprovalSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400
    # VALIDATE END

    # DATABASE WATER START
    query = {
        '_id': ObjectId(water_id),
        "updated_at": data["updated_at"],
        "doc_level": 2,
        "branch": claims["branch"],
    }
    update = {
        '$set': {"doc_level": 3,
                 "approval.created_by": get_jwt_claims()["name"],
                 "approval.created_by_id": get_jwt_identity(),
                 "updated_at": datetime.now()}
    }

    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    if water is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402
    # DATABASE WATER END

    # CALCULATE REAL TONASE
    suspicious = False  # perlu dimasukkan ke database
    suspicious_note = ""  # perlu dimasukkan ke database
    end_tonase = water["volume"]["tonase_end"]
    start_tonase = water["volume"]["tonase_start"]
    ordered_tonase = water["volume"]["tonase_ordered"]
    real_tonase = end_tonase - start_tonase  # perlu dimasukkan ke database
    different_tonase = water["volume"]["tonase_difference"]

    if water["photos"]["start_photo"] == "" or water["photos"]["end_photo"] == "":
        suspicious = True
        suspicious_note = suspicious_note + \
            "Foto meteran tidak dilampirkan\n"
    if real_tonase < 0:  # kemungkinan kesalahan input
        suspicious = True
        suspicious_note = suspicious_note + \
            "Ada kemungkinan kesalahan input sehingga realisasi tonase minus\n"
    if different_tonase > 5:  # tonase pada kegiatan sebelumnya ada selisih lebih dari 5 ton
        suspicious = True
        suspicious_note = suspicious_note + \
            f"Ada selisih dari meteran awal air dengan kegiatan sebelumnya sebesar {different_tonase} ton\n"
    if ordered_tonase != real_tonase:
        suspicious_note = suspicious_note + \
            f"Terdapat perbedaan Jumlah air yang dipesan dan yang diisi sebesar {real_tonase - ordered_tonase} ton\n"
    # CALCULATE REAL TONASE END

    # DATABASE WATER START 2ND
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
    # DATABASE WATER END 2ND

    # DATABASE STATE METER START
    query = {
        "branch": water["branch"],
        "locate": water["locate"],
    }
    update = {
        '$set': {
            "end_tonase": water["volume"]["tonase_end"],
        }
    }
    mongo.db.water_state.update_one(query, update)
    # DATABASE STATE METER END

    return jsonify(water), 201


"""
-------------------------------------------------------------------------------
APPROVAL Manager dari lvl 3 ke lvl 4
akan mengupdate state di db water_state
-------------------------------------------------------------------------------
"""
@bp.route('/water-approval/finish/<water_id>', methods=['POST'])
@jwt_required
def foreman_approved(water_id):

    # VALIDATE START
    claims = get_jwt_claims()

    if not valid.isManager(claims):
        return {"message": "User tidak memiliki hak akses untuk menyetujui dokumen ini"}, 403

    schema = WaterApprovalSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400
    # VALIDATE END

    # DATABASE WATER START
    query = {
        '_id': ObjectId(water_id),
        "updated_at": data["updated_at"],
        "doc_level": 3,
        "branch": claims["branch"],
    }
    update = {
        '$set': {"doc_level": 4,
                 "approval.approval_name": get_jwt_claims()["name"],
                 "approval.approval_id": get_jwt_identity(),
                 "approval.approval_time": datetime.now(),
                 "updated_at": datetime.now()}
    }

    water = mongo.db.waters.find_one_and_update(
        query, update, return_document=True
    )

    if water is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402
    # DATABASE WATER END


    return jsonify(water), 201
