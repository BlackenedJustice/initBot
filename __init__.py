from telebot import types
from telebot import apihelper
from peewee import DoesNotExist
from functools import wraps
import logging

import telebot
import config
from mwt import MWT
from config import db
from users import User, Player, Role


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
db.create_tables([User, Player])

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


@bot.message_handler(commands=['start'])
@restricted(Role.GOD)
def start_cmd(message):

    if message.chat.id == config.creatorID:
        bot.send_message(message.chat.id, 'Hello, Yury!')
    else:
        bot.send_message(message.chat.id, 'Hi!')


@bot.message_handler(content_types=['text'])
def foo(message):
    bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    bot.polling(none_stop=True)
