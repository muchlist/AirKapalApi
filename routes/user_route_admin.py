from datetime import timedelta

from flask import Blueprint, request, jsonify
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

from validations import role_validation as valid
from utils.my_bcrypt import bcrypt
from dao import (dd_user_query,
                 dd_user_update)


bp = Blueprint('user_admin_bp', __name__, url_prefix='/admin')


def user_eksis(username):
    if dd_user_query.get_one_without_password(username):
        return True
    return False


"""
------------------------------------------------------------------------------
register
------------------------------------------------------------------------------
"""
@bp.route('/register', methods=['POST'])
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
    dd_user_update.insert_user(data)
    return {"message": "data berhasil disimpan"}, 201


"""
------------------------------------------------------------------------------
Merubah dan mendelete user
------------------------------------------------------------------------------
"""
@bp.route('/users/<string:username>', methods=['PUT', 'DELETE'])
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

        if not user_eksis(username):
            return {"message": f"user {username} tidak ditemukan"}, 404

        dd_user_update.update_user(username, data)
        return {"message": f"user {username} berhasil diubah"}, 201

    if request.method == 'DELETE':
        if not user_eksis(username):
            return {"message": f"user {username} tidak ditemukan"}

        dd_user_update.delete_user(username)
        return {"message": f"user {username} berhasil dihapus"}, 201


"""
------------------------------------------------------------------------------
Reset Password
------------------------------------------------------------------------------
"""
@bp.route('/reset/<string:username>', methods=['GET'])
@jwt_required
def reset_password_by_admin(username):

    if not valid.isAdmin(get_jwt_claims()):
        return {"message": "user tidak memiliki authorisasi"}, 403

    if request.method == 'GET':
        if not user_eksis(username):
            return {"message": f"user {username} tidak ditemukan"}, 404

        # hash password
        pw_hash = bcrypt.generate_password_hash("Pelindo3").decode("utf-8")

        dd_user_update.put_password(username, pw_hash)

        return {"message": f"Password user {username} berhasil direset"}, 201
