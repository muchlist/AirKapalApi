from marshmallow import Schema, fields


class WaterCreateSchema(Schema):
    job_number = fields.Str(required=True)
    locate = fields.Str(required=True)
    tonase_ordered = fields.Int(required=True)
    vessel_name = fields.Str(required=True)
    vessel_id = fields.Str(required=True)
    int_dom = fields.Str(required=True)
    agent = fields.Str(required=True)
    created_at = fields.DateTime(required=True)
    # updated_at = fields.DateTime(required=True)


    # #auto
    # agent = fields.Str(required=True) #auto dari kapal
    # branch #auto dari user
    # tonase_begin
    # tonase_end

class WaterEditSchema(Schema):
    job_number = fields.Str(required=True)
    locate = fields.Str(required=True)
    tonase_ordered = fields.Int(required=True)
    vessel_name = fields.Str(required=True)
    vessel_id = fields.Str(required=True)
    int_dom = fields.Str(required=True)
    agent = fields.Str(required=True)
    created_at = fields.DateTime(required=True)

    updated_at = fields.DateTime(required=True)