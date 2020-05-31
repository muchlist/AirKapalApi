from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    jwt_required,
    get_raw_jwt,
    get_jwt_claims,
)
from marshmallow import ValidationError
from bson.objectid import ObjectId

from validations import role_validation as valid
from schemas.vessel import VesselRegisterSchema
from dao import (dd_vessel_query,
                 dd_vessel_update)


# Set up a Blueprint
bp = Blueprint('vessel_bp', __name__)


"""
------------------------------------------------------------------------------
List kapal dan register
------------------------------------------------------------------------------
"""
@bp.route('/vessels', methods=['GET', 'POST'])  # ?search=
@jwt_required
def get_vessel_list():
    if request.method == 'GET':
        search = request.args.get("search")
        if search:
            vessels = dd_vessel_query.search_vessel(search.upper())
        else:
            vessels = dd_vessel_query.get_vessel_list()
        return {"vessels": vessels}, 200

    if request.method == 'POST':
        schema = VesselRegisterSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if not valid.isTallyAndManager(get_jwt_claims()):
            return {"message": "user tidak memiliki authorisasi"}, 403

        # validasi isActive
        if "isActive" not in data:
            data["isActive"] = True

        dd_vessel_update.insert_vessel(data)
        return {"message": "data berhasil disimpan"}, 201


"""
------------------------------------------------------------------------------
Detail kapal dan merubah detail kapal
------------------------------------------------------------------------------
"""
@bp.route('/vessels/<vessel_id>', methods=['GET', 'PUT'])
@jwt_required
def get_vessel_detail(vessel_id):

    if not ObjectId.is_valid(vessel_id):
        return {"message": "Object Id tidak valid"}, 400

    if request.method == 'GET':
        ship = dd_vessel_query.get_vessel(vessel_id)
        return jsonify(ship), 200

    if request.method == 'PUT':
        if not valid.isAdmin(get_jwt_claims()):
            return {"message": "user tidak memiliki authorisasi"}, 403

        schema = VesselRegisterSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        vessel = dd_vessel_update.change_vessel(data)

        return jsonify(vessel), 200
