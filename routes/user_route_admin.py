from db import mongo

from utils.my_bcrypt import bcrypt
from flask import Blueprint, request, jsonify
from validations import role_validation as valid
from marshmallow import ValidationError
from schemas.user import (UserRegisterSchema,
                          UserLoginSchema,
                          UserEditSchema)
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)

from datetime import timedelta


bp = Blueprint('user_admin_bp', __name__)


def user_eksis(username):
    result = mongo.db.users_ak.find_one(
        {"username": username}, {"username": 1})
    if result:
        return True
    return False


"""
------------------------------------------------------------------------------
register
------------------------------------------------------------------------------
"""
@bp.route('/admin/register', methods=['POST'])
@jwt_required
def register_user():

    if not valid.isAdmin(get_jwt_claims()):
        return {"message": "user tidak memiliki authorisasi"}, 403

    schema = UserRegisterSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    # hash password
    pw_hash = bcrypt.generate_password_hash(
        data["password"]).decode("utf-8")
    data["password"] = pw_hash

    # mengecek apakah user exist
    if user_eksis(data["username"]):
        return {"message": "user tidak tersedia"}, 400

    # mendaftarkan ke mongodb
    data_insert = {
        "username": data["username"].upper(),
        "password": pw_hash,
        "email": data["email"],
        "name": data["name"].upper(),
        "isAdmin": data["isAdmin"],
        "isManager": data["isManager"],
        "isTally": data["isTally"],
        "isAgent": data["isAgent"],
        "branch": data["branch"].upper(),
        "company": data["company"].upper(),
    }
    try:
        mongo.db.users_ak.insert_one(data_insert)
    except:
        return {"message": "galat insert register"}, 500

    return {"message": "data berhasil disimpan"}, 201


"""
------------------------------------------------------------------------------
Merubah dan mendelete user
------------------------------------------------------------------------------
"""
@bp.route('/admin/users/<string:username>', methods=['PUT', 'DELETE'])
@jwt_required
def put_delete_user(username):

    if not valid.isAdmin(get_jwt_claims()):
        return {"message": "user tidak memiliki authorisasi"}, 403

    if request.method == 'PUT':
        schema = UserEditSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return err.messages, 400

        if user_eksis(username):
            find = {"username": username}
            update = {
                "name": data["name"].upper(),
                "email": data["email"],
                "isAdmin": data["isAdmin"],
                "isAgent": data["isAgent"],
                "isTally": data["isTally"],
                "isManager": data["isManager"],
                "branch": data["branch"].upper(),
                "company": data["company"].upper(),
            }

            mongo.db.users_ak.update_one(find, {'$set': update})

            return {"message": f"user {username} berhasil diubah"}, 201

        return {"message": f"user {username} tidak ditemukan"}, 404

    if request.method == 'DELETE':
        if user_eksis(username):
            mongo.db.users_ak.remove({"username": username})
            return {"message": f"user {username} berhasil dihapus"}, 201
        return {"message": f"user {username} tidak ditemukan"}


"""
------------------------------------------------------------------------------
Reset Password
------------------------------------------------------------------------------
"""
@bp.route('/admin/reset/<string:username>', methods=['GET'])
@jwt_required
def reset_password_by_admin(username):

    if not valid.isAdmin(get_jwt_claims()):
        return {"message": "user tidak memiliki authorisasi"}, 403

    if request.method == 'GET':
        if not user_eksis(username):
            return {"message": f"user {username} tidak ditemukan"}, 404

        # hash password
        pw_hash = bcrypt.generate_password_hash("Pelindo3").decode("utf-8")

        find = {"username": username}
        update = {
            "password": pw_hash
        }

        mongo.db.users_ak.update_one(find, {'$set': update})

        return {"message": f"Password user {username} berhasil direset"}, 201
