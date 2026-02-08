from marshmallow import Schema, fields, ValidationError, validates
from models.users import User

class LoginSchema(Schema):
    email = fields.Email(required=True, error_messages={"required": "Email is required"})
    password = fields.Str(required=True, error_messages={"required": "Password is required"})

    def handle_error(self, error, data, **kwargs):
        if 'required' in str(error):
            field = str(error).split('.')[0].split()[0]
            return {'error': {field: error.messages}, 'status_code': 400}
        return super().handle_error(error, data, **kwargs)

