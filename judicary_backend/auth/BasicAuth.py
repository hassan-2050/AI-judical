import rsa
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BasicAuthenticator:
    def login(self, username: str, password: str):
        if username != "dummy" or password != "password":
            return 'Unauthorized', 401

        usernameAndPassword = username + '_' + password
        security_key = os.getenv('public_key')
        if security_key:
            token = rsa.encrypt(usernameAndPassword.encode(encoding='utf-8'), security_key)
            return {'token': token.hex()}
        else:
            return 'Security key not found', 500
    
    def authenticate(self, token: str):

        if self.is_hex(token):
            bytesFromHex = bytes.fromhex(token)
            try:
                security_key = os.getenv('public_key')
                usernameAndPassword = rsa.decrypt(bytesFromHex, security_key).decode()
            except:
                return False
        
            userName = usernameAndPassword.split('_')[0]
            password = usernameAndPassword.split('_')[1]
        
            if userName != "dummy" or password != "password":
                return False
            else: 
                return True
        else:
            return False

    def is_hex(self, s) -> bool:
        try:
            bytes.fromhex(s)
            return True
        except ValueError:
            return False
