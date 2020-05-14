from db import mongo

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
    WaterApprovalSchema,
)

from datetime import datetime

# Set up a Blueprint
bp = Blueprint('water_approval_bp', __name__, url_prefix='/api')

