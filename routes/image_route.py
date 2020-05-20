
import os
from datetime import datetime
import string
import random

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_claims,
    get_jwt_identity,
)
from marshmallow import ValidationError
from bson.objectid import ObjectId
from flask_uploads import UploadNotAllowed
from bson.objectid import ObjectId

from utils import image_helper
from validations import role_validation as valid
from schemas.image import ImageSchema
from config import config as cf
from dao import dd_water_update

# Set up a Blueprint
bp = Blueprint('water_image_bp', __name__, url_prefix='/api')


@bp.route('/upload/image/<water_id>/<position>', methods=['POST'])
@jwt_required
def upload_image(water_id, position):
    # static/images/namafolder/namafile

    # VALIDASI START
    if not ObjectId.is_valid(water_id):
        return {"message": "Object ID tidak valid"}, 400

    schema = ImageSchema()
    try:
        data = schema.load(request.files)
    except ValidationError as err:
        return err.messages, 400

    # Cek path posisi gambar, selain witness
    if position not in ["begin", "end", "witness"]:
        return {"message": "path salah"}, 400

    # AUTH
    claims = get_jwt_claims()
    if not valid.isTallyAndManager(claims):
        return {"message": "user ini tidak memiliki hak akses untuk mengupload"}, 403
    # VALIDASI END

    # Cek extensi untuk nama file custom
    extension = image_helper.get_extension(data['image'])
    # Nama file dan ekstensi
    fileName = f"{water_id}-{position}{extension}"
    today = datetime.now()
    folder = str(today.year)+"B"+str(today.month)

    # SAVE IMAGE
    try:
        image_path = image_helper.save_image(
            data['image'], folder=folder, name=fileName)
        basename = image_helper.get_basename(image_path)

        # DATABASE
        # key di database berdasarkan posisi gambar path url
        key = f"photos.{position}_photo"
        water_doc = dd_water_update.update_photo(water_id, key, image_path)

        if water_doc is None:
            return {"message": "water_doc check id salah"}, 400

        return {"message": image_path}, 201

    except UploadNotAllowed:
        extension = image_helper.get_extension(data['image'])
        return {"message": f"extensi {extension} not allowed"}, 406


@bp.route('/upload/profil-image', methods=['POST'])
@jwt_required
def upload_profil_image():
    # static/images/namafolder/namafile
    schema = ImageSchema()
    try:
        data = schema.load(request.files)
    except ValidationError as err:
        return err.messages, 400

    # AUTH
    claims = get_jwt_claims()
    if not valid.isTallyAndManager(claims):
        return {"message": "user ini tidak memiliki hak akses untuk mengupload"}, 403

    # Cek extensi untuk nama file custom
    extension = image_helper.get_extension(data['image'])
    # Nama file dan ekstensi
    fileName = f"{get_jwt_identity()}{extension}"
    folder = "profile"

    # Check If image with same name already exist
    try:
        filepath = os.path.join(
            cf.get("uploaded_image_dest"), folder, fileName)
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        return {"message": "Menghapus image gagal"}, 500

    # SAVE IMAGE
    try:
        image_path = image_helper.save_image(
            data['image'], folder=folder, name=fileName)
        basename = image_helper.get_basename(image_path)

    except UploadNotAllowed:
        extension = image_helper.get_extension(data['image'])
        return {"message": f"extensi {extension} not allowed"}, 406

    return {"message": image_path}, 201
