from config import config as cf
from flask import Flask
from flask import Blueprint
from flask_jwt_extended import JWTManager
from flask_uploads import configure_uploads, patch_request_class

from routes.user_route import bp as user_bp
from routes.user_route_admin import bp as user_bp_admin
from routes.vessel_route import bp as vessel_bp
from routes.water_route import bp as water_bp
from routes.image_route import bp as image_bp
from routes.water_tonase_route_admin import bp as tonase_admin_bp
from routes.water_approval_route import bp as water_approval_bp

from db import mongo
from utils.my_encoder import JSONEncoder
from utils.my_bcrypt import bcrypt
from utils.image_helper import IMAGE_SET

app = Flask(__name__)

app.config['MONGO_URI'] = cf.get('mongo_uri')
app.config['JWT_SECRET_KEY'] = cf.get('jwt_secret_key')
app.config["UPLOADED_IMAGES_DEST"] = cf.get('uploaded_image_dest')
patch_request_class(app, 6 * 1024 * 1024)  # 6MB max upload.
configure_uploads(app, IMAGE_SET)

mongo.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)

app.json_encoder = JSONEncoder


@jwt.user_claims_loader
def add_claims_to_jwt(identity):
    user = mongo.db.users_ak.find_one({"username": identity})
    return {"name": user["name"],
            "branch": user["branch"],
            "isAdmin": user["isAdmin"],
            "isAgent": user["isAgent"],
            "isTally": user["isTally"],
            "isManager": user["isManager"]}


app.register_blueprint(user_bp)
app.register_blueprint(user_bp_admin)
app.register_blueprint(vessel_bp)
app.register_blueprint(water_bp)
app.register_blueprint(water_approval_bp)
app.register_blueprint(tonase_admin_bp)
app.register_blueprint(image_bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
