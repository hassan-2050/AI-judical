import mongoengine as me
from datetime import datetime

class Filters(me.Document):
    JudgeFilters = me.ListField(me.StringField(), default=list)
    CaseTypeFilters = me.ListField(me.StringField(), default=list)
    LocationFilters = me.ListField(me.StringField(), default=list)
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "JudgeFilters": self.JudgeFilters,
            "CaseTypeFilters": self.CaseTypeFilters,
            "LocationFilters": self.LocationFilters,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
