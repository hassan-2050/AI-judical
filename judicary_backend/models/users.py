import mongoengine as me
from datetime import datetime
from models.auth import Auth  

class User(me.Document):
    auth_id = me.ReferenceField(Auth)
    username = me.StringField(required=False)
    firstName = me.StringField(required=True)
    lastName = me.StringField(required=False)  
    gender = me.StringField(required=False)
    phone_number = me.StringField(required=False)
    cnic_number = me.StringField(required=True)
    organization = me.StringField(required=True)
    ntn_number = me.StringField(default='0')
    country = me.StringField(required=True)
    province = me.StringField(required=True)
    city = me.StringField(required=True)
    address = me.StringField(required=True)
    subscription = me.StringField(choices=["common", "premium", "super"], default="common")
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "auth_id": str(self.auth_id),
            "firstName": self.firstName,
            "lastName": self.lastName,
            "gender": self.gender,
            "phone_number": self.phone_number,
            "cnic_number": self.cnic_number,
            "organization": self.organization,
            "ntn_number": self.ntn_number,
            "country": self.country,
            "province": self.province,
            "city": self.city,
            "address": self.address,
            "subscription": self.subscription,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
