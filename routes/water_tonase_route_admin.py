from dao import dd_tonase_update

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
    data["updated_by"] = get_jwt_claims()["name"]
    data["last_update"] = datetime.now()

    ok = dd_tonase_update.insert(data)
    if not ok:
        return {"message": "Galat memasukkan database"}, 500

    return {"message": "data berhasil disimpan"}, 201
