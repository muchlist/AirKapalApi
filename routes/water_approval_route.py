from db import mongo
from dao import dd_water_update, dd_tonase_update

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

    data["_id"] = water_id
    data["branch"] = claims["branch"]
    data["approval.created_by"] = claims["name"]
    data["approval.created_by_id"] = get_jwt_identity()

    water = dd_water_update.update_witness_approval(data)

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

    data["_id"] = water_id
    data["branch"] = claims["branch"]
    data["approval.created_by"] = claims["name"]
    data["approval.created_by_id"] = get_jwt_identity()

    # DATABASE WATER START
    water = dd_water_update.update_tally_approval(data)

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
    water = dd_water_update.update_real_tonase(water_id,
                                               real_tonase,
                                               suspicious,
                                               suspicious_note)
    # DATABASE WATER END 2ND

    # DATABASE STATE METER START
    dd_tonase_update.update(water["branch"],
                            water["locate"],
                            water["volume"]["tonase_end"])
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

    data["_id"] = water_id
    data["branch"] = claims["branch"]
    data["approval.approval_name"] = claims["name"]
    data["approval.approval_id"] = get_jwt_identity()
    data["approval.approval_time"] = get_jwt_identity()
    data["new_updated_at"] = datetime.now()

    # DATABASE WATER START
    water = dd_water_update.update_manager_approval(data)

    if water is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402
    # DATABASE WATER END

    return jsonify(water), 201
