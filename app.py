from config import config as cf
from flask import Flask
from flask import Blueprint
from flask_jwt_extended import JWTManager

from routes.user_route import bp as user_bp

from db import mongo
from utils.my_encoder import JSONEncoder
from utils.my_bcrypt import bcrypt

app = Flask(__name__)

#app.config.from_object('config.Config')
app.config['MONGO_URI'] = cf.get('mongo_uri')
app.config['JWT_SECRET_KEY'] = cf.get('jwt_secret_key')

mongo.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

app.json_encoder = JSONEncoder

# @jwt.user_claims_loader
# def add_claims_to_jwt(identity):
#     user = mongo.db.users.find_one({"username" : identity})
#     return {"user_name": user["name"]}

app.register_blueprint(user_bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
