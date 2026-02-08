import mongoengine as me
from datetime import datetime

class Auth(me.Document):
    email = me.EmailField(required=True)
    password = me.StringField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {"email": self.email,  "role": self.role, "created_at": self.created_at, "updated_at": self.updated_at}

