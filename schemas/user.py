from marshmallow import Schema, fields

class UserRegisterSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    email = fields.Email(required=True)
    name = fields.Str(required=True)
    isAdmin = fields.Bool(required=True)
    isAgent = fields.Bool(required=True)
    isTally = fields.Bool(required=True)
    isForeman = fields.Bool(required=True)
    branch = fields.Str(required=True)