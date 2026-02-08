from functools import wraps
from flask_restful import reqparse
from .BasicAuth import BasicAuthenticator # Importing the BasicAuthenticator class from your file

def auth_interceptor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('Authorization', 
                            type=str, 
                            required=True,
                            location='headers',
                            help='Authorization can not be empty!')
        args = parser.parse_args(strict=True)
        token = args['Authorization']
        
        authenticator = BasicAuthenticator()
        if authenticator.authenticate(token):
            result = func(*args, **kwargs)
            return result
        else: 
            return 'Unauthorized', 401 
    return wrapper
