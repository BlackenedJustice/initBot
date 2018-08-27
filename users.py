from peewee import *
from enum import IntEnum
from config import db


class Role(IntEnum):
    NONE = 0
    PLAYER = 1
    KP = 2
    ADMIN = 3
    GOD = 4


class Race(IntEnum):
    NONE = 0
    EXPLORER = 1
    WEREWOLF = 2
    DWARF = 3
    ELF = 4
    ORK = 5
    PIXIE = 6
    GOBLIN = 7
    TROLL = 8
    GIANT = 9
    DEMON = 10


class RoleField(Field):
    field_type = 'smallint'

    def db_value(self, value):
        return int(value)

    def python_value(self, value):
        return Role(value)


class RaceField(Field):
    field_type = 'smallint'

    def db_value(self, value):
        return int(value)

    def python_value(self, value):
        return Race(value)


class User(Model):
    tg_id = IntegerField(unique=True)
    name = CharField(null=True)
    username = CharField(null=True)
    role = RoleField(default=Role.NONE)
    challenge = DeferredForeignKey('Challenge',
                                   default=None,
                                   null=True,
                                   backref='kp')

    class Meta:
        database = db


class Player(User):
    race = RaceField(default=Race.NONE)
    energy = IntegerField(default=0)
    time = DoubleField(default=0)
    currentPurpose = IntegerField(default=0)


class Challenge(Model):
    name = CharField()
    admin = ForeignKeyField(User, backref='own_challenge', null=False)
    finished = BooleanField(default=False)

    class Meta:
        database = db
