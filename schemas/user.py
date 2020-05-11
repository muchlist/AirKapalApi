from marshmallow import Schema, fields

class UserRegisterSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)
    email = fields.Email(required=True)
    name = fields.Str(required=True)
    isAdmin = fields.Bool(required=True)
    isAgent = fields.Bool(required=True)
    isTally = fields.Bool(required=True)
    isManager = fields.Bool(required=True)
    branch = fields.Str(required=True)
    company = fields.Str(required=True)


class UserEditSchema(Schema):
    email = fields.Email(required=True)
    isAdmin = fields.Bool(required=True)
    name = fields.Str(required=True)
    isAgent = fields.Bool(required=True)
    isTally = fields.Bool(required=True)
    isManager = fields.Bool(required=True)
    branch = fields.Str(required=True)
    company = fields.Str(required=True)

class UserLoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

class UserChangePassSchema(Schema):
    password = fields.Str(required=True)
    new_password = fields.Str(required=True)