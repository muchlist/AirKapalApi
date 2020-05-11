from db import mongo

from utils.my_bcrypt import bcrypt
from flask import Blueprint, request, jsonify
from validations import role_validation as valid
from marshmallow import ValidationError
from schemas.user import (UserRegisterSchema,
                          UserLoginSchema,
                          UserChangePassSchema)
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    get_jwt_claims,
)

from datetime import timedelta


bp = Blueprint('user_bp', __name__)

EXPIRED_TOKEN = 15


"""
------------------------------------------------------------------------------
login
------------------------------------------------------------------------------
"""
@bp.route('/login', methods=['POST'])
def login_user():

    schema = UserLoginSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    # mendapatkan data user termasuk password
    user = mongo.db.users_ak.find_one({"username": data["username"]})

    # Cek apakah hash password sama
    if not (user and bcrypt.check_password_hash(user["password"], data["password"])):
        return {"message": "user atau password salah"}, 400

    # Membuat akses token menggunakan username di database
    access_token = create_access_token(
        identity=user["username"],
        expires_delta=timedelta(days=EXPIRED_TOKEN),
        fresh=True)

    response = {
        'access_token': access_token,
        'name': user['name'],
        'isAdmin': user['isAdmin'],
        'isTally': user['isTally'],
        'isManager': user['isManager'],
        'isAgent': user['isAgent'],
        "branch": user["branch"],
        "company": user["company"],
    }, 200

    return response


"""
------------------------------------------------------------------------------
Detail user by username
------------------------------------------------------------------------------
"""
@bp.route("/users/<string:username>", methods=['GET'])
@jwt_required
def user(username):
    result = mongo.db.users_ak.find_one(
        {"username": username}, {"password": 0})
    return jsonify(result), 200


"""
------------------------------------------------------------------------------
Detail user by name
------------------------------------------------------------------------------
"""
@bp.route("/getuser/<name>", methods=['GET'])
@jwt_required
def user_by_name(name):
    query_string = {'$regex': f'.*{name.upper()}.*'}
    user_collection = mongo.db.users_ak.find(
        {"name": query_string}, {"password": 0})
    user_list = []
    for user in user_collection:
        user_list.append(user)
    return {"users": user_list}, 200


"""
------------------------------------------------------------------------------
Detail user by self profil
------------------------------------------------------------------------------
"""
@bp.route("/profile", methods=['GET'])
@jwt_required
def show_profile():
    result = mongo.db.users_ak.find_one(
        {"username": get_jwt_identity()}, {"password": 0})
    return jsonify(result), 200


"""
------------------------------------------------------------------------------
List User
------------------------------------------------------------------------------
"""
@bp.route("/users", methods=['GET'])
@jwt_required
def user_list():
    user_list = []
    result = mongo.db.users_ak.find({}, {"password": 0})
    for user in result:
        user_list.append(user)

    return jsonify(user_list), 200


"""
------------------------------------------------------------------------------
Self Change Password
------------------------------------------------------------------------------
"""
@bp.route('/change-password', methods=['POST'])
@jwt_required
def change_password():
    schema = UserChangePassSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return err.messages, 400

    user_username = get_jwt_identity()

    user = mongo.db.users_ak.find_one(
        {"username": user_username}, {"password": 1})

    # Cek apakah hash password inputan sama
    if not bcrypt.check_password_hash(user["password"], data["password"]):
        return {'message': "password salah"}, 400

    # menghash password baru
    inputan_new_password_hash = bcrypt.generate_password_hash(
        data["new_password"]).decode("utf-8")

    query = {"username": user_username}
    update = {'$set': {"password": inputan_new_password_hash}}

    mongo.db.users_ak.update_one(query, update)
    return {'message': "password berhasil di ubah"}, 200


"""
------------------------------------------------------------------------------
Mengembalikan list semua company/agent
------------------------------------------------------------------------------
"""
@bp.route('/companies', methods=['GET'])
@jwt_required
def get_agent_list():
    all_company_array = mongo.db.users_ak.distinct('company')
    return jsonify(company=all_company_array), 200
