from peewee import *
from enum import IntEnum
from config import db


class Role(IntEnum):
    USER = 0
    KP = 1
    ADMIN = 2
    GOD = 3


class RoleField(Field):
    field_type = 'smallint'

    def db_value(self, value):
        return int(value)

    def python_value(self, value):
        return Role(value)


class User(Model):
    tg_id = IntegerField(unique=True)
    name = CharField(null=True)
    username = CharField(null=True)
    role = RoleField(default=Role.USER)

    class Meta:
        database = db
