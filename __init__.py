from telebot import types
from telebot import apihelper
from peewee import DoesNotExist

import telebot
import config
from config import db
from users import User, Player, Role


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


@bot.message_handler(commands=['start'])
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
