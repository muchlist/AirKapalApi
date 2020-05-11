from config import config as cf
from flask import Flask
from flask import Blueprint
from flask_jwt_extended import JWTManager

from routes.user_route import bp as user_bp
from routes.user_route_admin import bp as user_bp_admin

from db import mongo
from utils.my_encoder import JSONEncoder
from utils.my_bcrypt import bcrypt

app = Flask(__name__)

app.config['MONGO_URI'] = cf.get('mongo_uri')
app.config['JWT_SECRET_KEY'] = cf.get('jwt_secret_key')

mongo.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

app.json_encoder = JSONEncoder


@jwt.user_claims_loader
def add_claims_to_jwt(identity):
    user = mongo.db.users_ak.find_one({"username": identity})
    return {"username": user["name"],
            "isAdmin": user["isAdmin"],
            "isAgent": user["isAgent"],
            "isTally": user["isTally"],
            "isManager": user["isManager"]}


app.register_blueprint(user_bp)
app.register_blueprint(user_bp_admin)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
