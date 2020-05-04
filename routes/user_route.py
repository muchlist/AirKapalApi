from utils.my_bcrypt import bcrypt
from flask import Blueprint, request, jsonify
from validations import role_validation as valid
from utils import err_message
from marshmallow import ValidationError
from schemas.user import UserRegisterSchema
from repository.user import UserRepo
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    jwt_required,
    get_raw_jwt,
    get_jwt_claims,
)


bp = Blueprint('user_bp', __name__)

@bp.route('/admin/register', methods=['POST'])
#@jwt_required
def register_user():

    # if not valid.isAdmin(get_jwt_claims()):
    #     return {"message": "user tidak memiliki authorisasi"}, 400

    schema = UserRegisterSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    # hash password
    pw_hash = bcrypt.generate_password_hash(
        data["password"]).decode("utf-8")
    data["password"] = pw_hash

    # inisiasi user
    user = UserRepo()

    # mengecek apakah user exist
    if user.isUserExist(data["username"]):
        return {"message": "user tidak tersedia"}, 400

    # mendaftarkan ke mongodb
    # mengembalikan hasil_sukses, code, err
    result = user.register(**data)

    if result[2]:
        return {"message": result[2]}, result[1]
    
    return {"message": result[0]}, result[1]
