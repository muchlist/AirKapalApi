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
    WaterMeterInitSchema,
)

from datetime import datetime

# Set up a Blueprint
bp = Blueprint('water_tonase_bp', __name__, url_prefix='/admin')

"""
-------------------------------------------------------------------------------
Inisiasi meteran awal aplikasi
-------------------------------------------------------------------------------
"""
@bp.route('/init-meter', methods=['POST', ])
@jwt_required
def init_meters():
    if not valid.isAdmin(get_jwt_claims()):
        return {"message": "user tidak memiliki hak akses"}, 403

    schema = WaterMeterInitSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    # mendaftarkan ke mongodb
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
        return {"message": "galat insert state tonase"}, 500

    return {"message": "data berhasil disimpan"}, 201
