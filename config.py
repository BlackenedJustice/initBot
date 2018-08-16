from peewee import *
from random import randrange

token = '605058683:AAHW95wwWBiPd4L3o4Craf0tPG-y3kG4AZc'
creatorID = 144454876
creatorUsername = 'yury_zh'

db = SqliteDatabase('data.db')

races = [1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10]


def get_race():
    return races.pop(randrange(0, len(races)))


greetings = 'Здравствуйте! Добро пожаловать на квест Посвящения в студенты ВМК 2018!\n' \
            'Этот бот будет помогать вам в прохождении квеста\n' \
            'А теперь, давайте познакомимся'
collectGroupNumber = 'Введите номер группы'
successfulRegistration = 'Приятно познакомиться! Квест вот-вот начнется'
adminsGreetings = 'Введите ваше имя'
chooseGroupForTransfer = 'Пожалуйста, выберите группу, которой вы хотите перевести энергию'
chooseTransferAmount = 'Пожалуйста, введите колличество энергии для перевода'

warningWrongDataFormat = 'Неправильный формат данных!\nПопробуйте еще раз'
warningGroupNumber = 'Номер группы должен быть числом!\nПопробуйте еще раз'
warningTooLarge = 'Слишком неправильное число!\nПопробуйте еще раз'
warningNoSuchGroup = 'Такой группы нет\nВыполните команду /transfer еще раз'
warningWrongAmount = 'Число должно быть положительным!\nПопробуйте еще раз'
warningNotEnoughEnergy = 'У вас недостаточно энергии для перевода'
warningSmthWentWrongTransfer = 'Что-то пошло не так...\nВыполните команду /transfer еще раз'
