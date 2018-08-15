from telebot import types
from telebot import apihelper
from peewee import DoesNotExist
from functools import wraps
import logging

import telebot
import config
from mwt import MWT
from config import db
from users import User, Player, Challenge, Role
from timing import Timer

timer = Timer(name='Round')
timer.set_duration(12*60)

logger = logging.getLogger('bot')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger.setLevel(logging.DEBUG)


bot = telebot.TeleBot(token=config.token)
# using proxy in Russia
apihelper.proxy = {
    'http': 'http://167.99.242.198:8080',
    'https': 'https://167.99.242.198:8080'
}

# create tables in db
db.connect()
db.create_tables([User, Player, Challenge])

'''
# create GOD if not exists
try:
    god = User.get(User.tg_id == config.creatorID)
except DoesNotExist:
    god = User.create(tg_id=config.creatorID, username=config.creatorUsername, name='Yury', role=Role.GOD)
'''


@MWT(timeout=5*60)
def get_privilege_ids(role):
    logger.info("Update list of %s", role)
    return [user.tg_id for user in User.select().where(User.role >= role)]


def restricted(role):

    def wrapper(func):
        @wraps(func)
        def wrapped(message, *args, **kwargs):
            user_id = message.chat.id
            if user_id not in get_privilege_ids(role):
                logger.warning("Unauthorized access to <{}> by {}.".format(func.__name__, message.from_user.username))
                return
            return func(message, *args, **kwargs)
        return wrapped

    return wrapper


def check_text(message, func):
    if message.text is None:
        logger.warning("Wrong data format in <{}> by {}".format(func.__name__, message.from_user.username))
        bot.send_message(message.chat.id, config.warningWrongDataFormat)
        bot.register_next_step_handler(message, func)
        return False
    return True


@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(message.chat.id, "SYSTEM\nЕсли вы не участник квеста введите команду /reg чтобы продолжить")
    bot.send_message(message.chat.id, config.greetings)
    bot.send_message(message.chat.id, config.collectGroupNumber)
    bot.register_next_step_handler(message, get_group_number)


def get_group_number(message):
    if not check_text(message, get_group_number):
        return
    s = message.text
    if not s.isdecimal():
        logger.warning("Not a digit in <get_group_number> by {}".format(message.from_user.username))
        bot.send_message(message.chat.id, config.warningGroupNumber)
        bot.register_next_step_handler(message, get_group_number)
        return
    a = int(s)
    if (a < 101 or a > 118) and a != 141:
        logger.warning("Wrong number in <get_group_number> by {}".format(message.from_user.username))
        bot.send_message(message.chat.id, config.warningTooLarge)
        bot.register_next_step_handler(message, get_group_number)
        return
    player = Player.create(tg_id=message.chat.id, name=s, username=message.from_user.username,
                           role=Role.PLAYER, race=config.get_race())
    # TODO: here will be a transition to quest (maybe)
    logger.info("Group number {} was registered. Race: {}".format(a, player.race))
    bot.send_message(message.chat.id, config.successfulRegistration)


@bot.message_handler(commands=['reg'])
def reg_cmd(message):
    logger.info("Called <reg> by {}".format(message.from_user.username))
    bot.send_message(message.chat.id, config.adminsGreetings)
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    if not check_text(message, get_name):
        return
    s = message.text
    logger.info("New system user - {}".format(message.from_user.username))
    bot.send_message(message.chat.id, 'Приятно познакомиться, ' + s)
    user = User.create(tg_id=message.chat.id, name=s, username=message.from_user.username)


@bot.message_handler(commands=['make_god'])
@restricted(Role.GOD)
def make_god_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message('Wrong format!\n/make_god username')
        return
    username = l[1]
    try:
        user = User.get(User.username == username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    user.role = Role.GOD
    user.save()
    logger.info('User {} - {} become a God'.format(user.name, user.username))
    bot.send_message(message.chat.id, 'Success!')
    bot.send_message(user.tg_id, 'You become a God!')


@bot.message_handler(commands=['make_admin'])
@restricted(Role.ADMIN)
def make_admin_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message('Wrong format!\n/make_admin username')
        return
    username = l[1]
    try:
        user = User.get(User.username == username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    if user.tg_id == config.creatorID:
        bot.send_message(message.chat.id, "This is my creator! I can't do that")
        return
    user.role = Role.ADMIN
    user.save()
    logger.info('User {} - {} become an admin'.format(user.name, user.username))
    bot.send_message(message.chat.id, 'Success!')
    bot.send_message(user.tg_id, 'You become an Admin!')


@bot.message_handler(commands=['make_kp'])
@restricted(Role.ADMIN)
def make_kp_cmd(message):
    request_user = User.get(User.tg_id == message.chat.id)
    try:
        count = request_user.own_challenge.count()
    except:
        count = 0

    l = message.text.split(' ', maxsplit=2)
    if count != 1 and len(l) < 3:
        bot.send_message('Wrong format!\n/make_kp username challenge_name')
        return
    username = l[1]
    if request_user.role == Role.ADMIN:
        if count == 1:
            challenge_name = request_user.own_challenge.get().name
        else:
            challenge_name = l[2]
            allow = False
            for challenge in request_user.own_challenge:
                if challenge.name == challenge_name:
                    allow = True
            if not allow:
                logger.warning("Unauthorized adding kp to '{}' by {}".format(challenge_name, request_user.username))
                bot.send_message(message.chat.id, "It's not your challenge!")
                return
    else:
        challenge_name = l[2]
    try:
        user = User.get(User.username == username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    try:
        challenge = Challenge.get(Challenge.name == challenge_name)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such challenge!')
        return

    user.role = Role.KP
    user.challenge = challenge
    user.save()
    logger.info('User {} - {} become kp of {}'.format(user.name, user.username, challenge_name))
    bot.send_message(message.chat.id, "Success!")
    bot.send_message(user.tg_id, 'You become KP of ' + challenge_name)


@bot.message_handler(commands=['make_challenge'])
@restricted(Role.GOD)
def make_challenge_cmd(message):
    l = message.text.split(' ', maxsplit=2)
    if len(l) < 3:
        bot.send_message('Wrong format!\n/make_kp challenge_name admin_username')
        return

    challenge_name = l[1]
    admin_username = l[2]
    try:
        admin = User.get(User.name == admin_username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    # with db.atomic() as txn
    challenge = Challenge.create(name=challenge_name, admin=admin)
    admin.role = Role.ADMIN
    admin.save()

    logger.info("Challenge '{}' has been made. Admin: {} - {}".format(challenge_name, admin.name, admin_username))
    bot.send_message(message.chat.id, 'Success!')
    bot.send_message(admin.tg_id, "You become an admin of " + challenge_name)


@bot.message_handler(commands=['set_duration'])
@restricted(Role.GOD)
def set_duration_cmd(message):
    if not check_text(message, set_duration_cmd):
        return

    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Wrong format!\n/set_duration time(minutes)')
        return
    m = float(message.text)
    timer.set_duration(m*60)
    logger.info("Reset round's duration to {} mins by {}".format(m, message.from_user.username))
    bot.send_message(message.chat.id, 'Success!')
    

@bot.message_handler(commands=['everyone'])
@restricted(Role.ADMIN)
def everyone_cmd(message):
    if not check_text(message, everyone_cmd):
        return

    for user in User.select():
        bot.send_message(user.tg_id, message.text)
    bot.send_message(message.chat.id, 'Success!')


@bot.message_handler(commands=['wall'])
@restricted(Role.ADMIN)
def wall_cmd(message):
    if not check_text(message, wall_cmd):
        return

    for user in User.select().where(User.role != Role.PLAYER):
        bot.send_message(user.tg_id, message.text)
    bot.send_message(message.chat.id, 'Success!')


@bot.message_handler(content_types=['sticker'])
def echo_sticker(message):
    bot.send_message(message.chat.id, 'Классный стикер!')


@bot.message_handler(content_types=['text'])
def echo_text(message):
    bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    bot.polling(none_stop=True)
