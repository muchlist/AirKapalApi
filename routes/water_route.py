from datetime import datetime

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
    WaterInsertTonaseSchema,
)
from dao import dd_water_query, dd_water_update, dd_tonase_query

# Set up a Blueprint
bp = Blueprint('water_bp', __name__, url_prefix='/api')


"""
-------------------------------------------------------------------------------
Mengecek apakah job number sudah ada
-------------------------------------------------------------------------------
"""


def job_number_exist(job_number):
    result = dd_water_query.get_water_by_job_number(job_number)
    if result:
        return True
    return False


def get_last_tonase(branch, locate):
    tonase = dd_tonase_query.get_tonase(branch, locate)
    if tonase:
        return tonase["end_tonase"]
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

        data["created_by"] = get_jwt_claims()["name"]
        data["created_by_id"] = get_jwt_identity()
        data["branch"] = get_jwt_claims()["branch"]
        data["updated_at"] = datetime.now()

        results_id = dd_water_update.insert(data)
        if results_id == None:
            return {"message": "galat ketika memasukkan ke database"}, 500

        return {"message": results_id}, 201

    """
    -------------------------------------------------------------------------------
    GET Memunculkan water list
            ?branch=SAMPIT
            &  agent=MERATUS 
            &  meter=METER_1
            &  lvl=1
            &  page=1
            &  search=""
    -------------------------------------------------------------------------------
    """
    if request.method == 'GET':

        branch = request.args.get("branch")
        agent = request.args.get("agent")
        meter = request.args.get("meter")
        lvl = request.args.get("lvl")
        search = request.args.get("search")
        page = request.args.get("page")

        results = dd_water_query.get_waters_with_filter(branch,
                                                        agent,
                                                        meter,
                                                        lvl,
                                                        search,
                                                        page)

        return {"waters": results}, 200


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
        result = dd_water_query.get_water(id_water)
        return jsonify(result), 200

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

        # SET UP DATA
        data["_id"] = id_water
        data["approval.created_by"] = get_jwt_claims()["name"]
        data["approval.created_by_id"] = get_jwt_identity()
        data["branch"] = get_jwt_claims()["branch"]

        result = dd_water_update.update_water(data)

        if result is None:
            return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap muat ulang data terbaru!"}, 402

        return jsonify(result), 201

    """
    -------------------------------------------------------------------------------
    Delete , menghapus water
    hanya dapat dilakukan oleh tally dan di doc_level 1
    -------------------------------------------------------------------------------
    """
    if request.method == 'DELETE':

        if not valid.isTally(get_jwt_claims()):
            return {"message": "Tidak memiliki hak akses untuk menghapus"}, 403

        result = dd_water_update.find_delete(
            id_water, get_jwt_claims()["branch"])

        if result is None:
            return {"message": "Dokumen yang sudah disetujui tidak dapat dihapus"}, 406
        return {"message": "Dokumen berhasil di hapus"}, 204


"""
-------------------------------------------------------------------------------
Memasukkan tonase air ke start
menghitung selisih antara meteran mulai dengan meteran kegiatan terakhir kali
-------------------------------------------------------------------------------
"""
@bp.route('/tonase-start/<water_id>', methods=['POST'])
@jwt_required
def insert_tonase_start(water_id):

    # VALIDASI START
    if not ObjectId.is_valid(water_id):
        return {"message": "Object ID tidak valid"}, 400

    if not valid.isTally(get_jwt_claims()):
        return {"message": "User tidak memiliki hak akses untuk merubah dokumen ini"}, 403

    schema = WaterInsertTonaseSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400
    # VALIDASI END

    # Perhitungan tonase start
    # mendapatkan tonase terakhir
    last_tonase = get_last_tonase(get_jwt_claims()["branch"], data["locate"])
    if last_tonase is None:
        return {"message": f'tidak dapat menemukan tonase terakhir pada lokasi {data["locate"]}, harap hubungi administrator'}, 400

    # menghitung selisih antara tonase akhir dan meteran awal pengisian yang baru
    tonase_difference = data["tonase"] - last_tonase
    # Perhitungan tonase end

    data["_id"] = water_id
    data["updated_at"] = datetime.now()
    data["volume.tonase_difference"] = tonase_difference
    data["branch"] = get_jwt_claims()["branch"]
    data["approval.created_by"] = get_jwt_claims()["name"]
    data["approval.created_by_id"] = get_jwt_identity()

    results = dd_water_update.insert_tonase_start(data)

    if results is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402

    return jsonify(results), 201


"""
-------------------------------------------------------------------------------
Memasukkan tonase air ke end
-------------------------------------------------------------------------------
"""
@bp.route('/tonase-end/<water_id>', methods=['POST'])
@jwt_required
def insert_tonase_end(water_id):

    # VALIDASI START
    if not ObjectId.is_valid(water_id):
        return {"message": "Object ID tidak valid"}, 400

    if not valid.isTally(get_jwt_claims()):
        return {"message": "User tidak memiliki hak akses untuk merubah dokumen ini"}, 403

    schema = WaterInsertTonaseSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400
    # VALIDASI END

    data["_id"] = water_id
    data["updated_at"] = datetime.now()
    data["branch"] = get_jwt_claims()["branch"]
    data["approval.created_by"] = get_jwt_claims()["name"]
    data["approval.created_by_id"] = get_jwt_identity()

    water = dd_water_update.insert_tonase_end(data)

    if water is None:
        return {"message": "Gagal update. Dokumen ini telah di ubah oleh seseorang sebelumnya. Harap cek data terbaru!"}, 402

    return jsonify(water), 201
