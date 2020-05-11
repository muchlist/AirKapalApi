from marshmallow import Schema, fields


class VesselRegisterSchema(Schema):
    ship_name = fields.Str(required=True)
    agent = fields.Str(required=True)
    isInternational = fields.Bool(required=True)
    isActive = fields.Bool(required=False)
