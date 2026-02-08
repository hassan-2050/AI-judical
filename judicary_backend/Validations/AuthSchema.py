from marshmallow import Schema, fields, ValidationError, validates
from models.users import User

class AuthSchema(Schema):
    username = fields.Str(required=False)
    firstName = fields.Str(required=False)
    lastName = fields.Str(required=False)
    gender = fields.Str(required=False)
    phone_number = fields.Str(required=False)
    cnic_number = fields.Str(required=True)
    organization = fields.Str(required=True)
    ntn_number = fields.Str(required=True)
    country = fields.Str(required=True)
    province = fields.Str(required=True)
    city = fields.Str(required=True)
    address = fields.Str(required=True)
    email = fields.Email(required=True, error_messages={"required": "Email is required"})
    password = fields.Str(required=True, error_messages={"required": "Password is required"})
    subscription = fields.Str(default='common')

    def handle_error(self, error, data, **kwargs):
        if 'required' in str(error):
            field = str(error).split('.')[0].split()[0]
            return {'error': {field: error.messages}, 'status_code': 400}
        return super().handle_error(error, data, **kwargs)

