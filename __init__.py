from telebot import types
from telebot import apihelper
import telebot
import config


bot = telebot.TeleBot(token=config.token)
# using proxy in Russia
apihelper.proxy = {
    'http': 'http://178.32.51.234:8080',
    'https': 'https://178.32.51.234:8080'
}


@bot.message_handler(content_types=['text'])
def foo(message):
    bot.send_message(message.chat.id, message.text)



@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.id == config.creatorID:
        bot.send_message(message.chat.id, 'Hello, Yury!')
    else:
        bot.send_message(message.chat.id, 'Hi!')


if __name__ == '__main__':
    bot.polling(none_stop=True)
