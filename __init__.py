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

# To store chosen groups. Group: recipient
transfers = {}

bot = telebot.TeleBot(token=config.token)

# using proxy in Russia
apihelper.proxy = {
    'http': 'http://46.101.149.132:3128',
    'https': 'https://46.101.149.132:3128'
    # 'http': 'http://79.138.99.254:8080',
    # 'https': 'https://79.138.99.254:8080'
    # 'http': 'http://5.148.128.44:80',
    # 'https': 'https://5.148.128.44:80'
    # 'http': 'http://167.99.242.198:8080',
    # 'https': 'https://167.99.242.198:8080'
}

# create tables in db
db.connect()
db.create_tables([User, Player, Challenge])


# create GOD if not exists
try:
    god = User.get(User.tg_id == config.creatorID)
except DoesNotExist:
    god = User.create(tg_id=config.creatorID, username=config.creatorUsername, name='Yury', role=Role.GOD)


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
    bot.send_message(message.chat.id, "SYSTEM:\nЕсли вы не участник квеста введите команду /reg чтобы продолжить")
    bot.send_message(message.chat.id, config.greetings)
    bot.send_message(message.chat.id, config.collectGroupNumber)
    bot.register_next_step_handler(message, get_group_number)


def get_group_number(message):
    # TODO: make unique group-names
    if not check_text(message, get_group_number):
        return
    s = message.text
    if not s.isdecimal():
        logger.warning("Not a digit in <get_group_number> by {}".format(message.from_user.username))
        bot.send_message(message.chat.id, config.warningGroupNumber)
        bot.register_next_step_handler(message, get_group_number)
        return
    a = int(s)
    if (a < 101 or a > 118) and a != 141 and a != 142:
        logger.warning("Wrong number in <get_group_number> by {}".format(message.from_user.username))
        bot.send_message(message.chat.id, config.warningTooLarge)
        bot.register_next_step_handler(message, get_group_number)
        return
    (race, r) = config.get_race(s)
    player = Player.create(tg_id=message.chat.id, name=s, username=message.from_user.username,
                           role=Role.PLAYER, race=race, round=r)
    if player.race < 0:
        logger.critical("Wrong group name at @{} !".format(message.from_user.username))
        bot.send_message(config.creatorID, "Wrong group name at @{} !".format(message.from_user.username))
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
        bot.send_message(message.chat.id, 'Wrong format!\n/make_god username')
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
        bot.send_message(message.chat.id, 'Wrong format!\n/make_admin username')
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
        bot.send_message(message.chat.id, 'Wrong format!\n/make_kp username challenge_name')
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
    l = message.text.split(' ', maxsplit=3)
    if len(l) < 4:
        bot.send_message(message.chat.id,
                         'Wrong format!\n/make_challenge challenge_name challenge_round(1/2) admin_username')
        return

    challenge_name = l[1]
    if l[2].isdecimal():
        r = int(l[2])
    else:
        r = 1
    admin_username = l[3]
    try:
        admin = User.get(User.name == admin_username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    # with db.atomic() as txn
    challenge = Challenge.create(name=challenge_name, admin=admin, round=r)
    admin.role = Role.ADMIN
    admin.save()

    logger.info("Challenge '{}' has been made. Admin: {} - {}".format(challenge_name, admin.name, admin_username))
    bot.send_message(message.chat.id, 'Success!')
    bot.send_message(admin.tg_id, "You become an admin of " + challenge_name)


@bot.message_handler(commands=['set_duration'])
@restricted(Role.GOD)
def set_duration_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2 or not l[1].isdigit():
        bot.send_message(message.chat.id, 'Wrong format!\n/set_duration time(minutes)')
        return
    m = float(message.text)
    timer.set_duration(m*60)
    logger.info("Reset round's duration to {} mins by {}".format(m, message.from_user.username))
    bot.send_message(message.chat.id, 'Success!')


@bot.message_handler(commands=['pause'])
@restricted(Role.GOD)
def pause_cmd(message):
    t = timer.get_time()
    timer.pause()
    logger.info('Round has been paused by @{}\nCurrent time: {}'.format(message.from_user.username, t))
    everyone('ВНИМАНИЕ!\nКвест был остановлен!\nВремя, прошедшее с начала раунда: {}'.format(t))


@bot.message_handler(commands=['resume'])
@restricted(Role.GOD)
def resume_cmd(message):
    timer.resume()
    logger.info('Round has been resumed by @{}')
    everyone('ВНИМАНИЕ!\nКвест возобновлен!\nУдачи)')


@bot.message_handler(commands=['time'])
def time_cmd(message):
    msg = 'Текущее время с момента начала раунда: {}'.format(timer.get_time())
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['transfer'])
@restricted(Role.PLAYER)
def transfer_cmd(message):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for player in Player.select().where(Player.tg_id != message.chat.id).order_by(Player.name):
        markup.add(types.KeyboardButton(player.name))
    bot.send_message(message.chat.id, config.chooseGroupForTransfer, reply_markup=markup)
    bot.register_next_step_handler(message, transfer2)


def transfer2(message):
    if not check_text(message, transfer2):
        return

    if not message.text.isdecimal():
        bot.send_message(message.chat.id, config.warningWrongDataFormat)
        bot.register_next_step_handler(message, transfer2)
        return

    try:
        recipient = Player.get(Player.name == message.text)
    except DoesNotExist:
        bot.send_message(message.chat.id, config.warningNoSuchGroup, reply_markup=types.ReplyKeyboardRemove())
        return
    transfers[message.from_user.username] = recipient
    bot.send_message(message.chat.id, config.chooseTransferAmount, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, transfer3)


def transfer3(message):
    if not check_text(message, transfer3):
        return
    if not message.text.isdecimal():
        bot.send_message(message.chat.id, config.warningWrongDataFormat)
        bot.register_next_step_handler(transfer3)
        return
    amount = int(message.text)
    if amount <= 0:
        bot.send_message(message.chat.id, config.warningWrongAmount)
        bot.register_next_step_handler(transfer3)
        return
    try:
        payer = Player.get(Player.tg_id == message.chat.id)
    except DoesNotExist:
        logger.critical("Can't find user - {} in database!".format(message.from_user.username))
        bot.send_message(message.chat.id, 'Критическая ошибка! Обратитесь к  организаторам или напишите @{}'.format(
            config.creatorUsername
        ))
        return
    if payer.energy < amount:
        bot.send_message(message.chat.id, config.warningNotEnoughEnergy)
        return
    recipient = transfers.get(message.from_user.username)
    if recipient is None:
        logger.warning("Couldn't found a team! Asked by {}".format(message.from_user.username))
        bot.send_message(message.chat.id, config.warningSmthWentWrongTransfer)
        return
    logger.info("Team {} has transferred {} energy to {} team".format(payer.name, amount, recipient.name))
    payer.energy -= amount
    recipient.energy += amount
    payer.save()
    recipient.save()
    bot.send_message(payer.tg_id, 'Перевод совершен')
    bot.send_message(recipient.tg_id, 'Команда {} перевела вам энергию ({})'.format(payer.name, amount))
    # TODO: Here maybe will be a transition to the main part of the quest


@bot.message_handler(commands=['pay'])
@restricted(Role.PLAYER)
def pay_cmd(message):
    bot.send_message(message.chat.id, config.enterPaySum)
    bot.register_next_step_handler(message, pay2)


def pay2(message):
    if not check_text(message, pay2):
        return
    if not message.text.isdecimal():
        bot.send_message(message.chat.id, config.warningWrongDataFormat)
        bot.register_next_step_handler(message, pay2)
        return
    amount = int(message.text)
    if amount <= 0:
        bot.send_message(message.chat.id, config.warningWrongAmount)
        bot.register_next_step_handler(message, pay2)
        return
    try:
        payer = Player.get(Player.tg_id == message.chat.id)
    except DoesNotExist:
        logger.critical("Can't find user - {} in database!".format(message.from_user.username))
        bot.send_message(message.chat.id, 'Критическая ошибка! Обратитесь к  организаторам или напишите @{}'.format(
            config.creatorUsername))
        return
    if payer.energy < amount:
        bot.send_message(message.chat.id, config.warningNotEnoughEnergy)
        return
    logger.info("Team {} has payed {} energy".format(payer.name, amount))
    payer.energy -= amount
    payer.save()
    bot.send_message(payer.tg_id, 'Успешно!')
    # TODO: Here maybe will be a transition to the main part of the quest (2)


@bot.message_handler(commands=['artifact'])
@restricted(Role.PLAYER)
def artifact_cmd(message):
    bot.send_message(message.chat.id, config.enterArtifactCode)
    bot.register_next_step_handler(message, get_artifact)


def get_artifact(message):
    if not check_text(message, get_artifact):
        return
    # TODO: Handle different artifacts
    code = message.text.upper()
    try:
        player = Player.get(Player.tg_id == message.chat.id)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'Не могу найти вас в списках игроков. Напишите @yury_zh')
        logger.error("Can't find user - {} in players database!".format(message.from_user.username))
        return
    if config.secondaryArtifacts.count(code):
        bot.send_message(player.tg_id, config.artifactSecondary)
        player.energy += config.secondaryEnergyAmount
        player.save()
        return
    exists = False
    artifact_race = 0
    artifact_pos = 0
    while artifact_race < 10:
        if config.artifacts[artifact_race].count(code) > 0:
            exists = True
            artifact_pos = config.artifacts[artifact_race].index(code)
            break
        artifact_race += 1
    if not exists:
        bot.send_message(message.chat.id, config.artifactWrongCode)
        return
    artifact_race += 1  # 0-numeration -> 1-numeration
    if player.race != artifact_race:
        bot.send_message(message.chat.id, config.artifactWrongRace)
        logger.info("Team {} (race: {}) has found artifact of race {}".format(player.name, player.race, artifact_race))
        return
    if player.currentPurpose < artifact_pos:
        bot.send_message(player.tg_id, config.artifactTooEarly)
        logger.info("Team {} (Current purpose: {}) has fond purpose {}".format(
            player.name, player.currentPurpose, artifact_pos
        ))
    elif player.currentPurpose > artifact_pos:
        bot.send_message(player.tg_id, config.artifactUsed)
    else:
        player.currentPurpose += 1
        player.save()
        bot.send_message(player.tg_id, config.purposes[player.race - 1][player.currentPurpose - 1])
        logger.info("Team {} has reached purpose {}".format(player.name, player.currentPurpose - 1))


@bot.message_handler(commands=['everyone'])
@restricted(Role.ADMIN)
def everyone_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message(message.chat.id, 'Wrong format!\n/everyone <message>')
        return
    everyone(l[1])

    bot.send_message(message.chat.id, 'Success!')


def everyone(msg):
    for user in User.select():
        bot.send_message(user.tg_id, msg)


@bot.message_handler(commands=['wall'])
@restricted(Role.ADMIN)
def wall_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message(message.chat.id, 'Wrong format!\n/wall <message>')
        return
    message.text = l[1]

    for user in User.select().where(User.role != Role.PLAYER):
        bot.send_message(user.tg_id, message.text)
    bot.send_message(message.chat.id, 'Success!')


@bot.message_handler(commands=['get_user'])
@restricted(Role.ADMIN)
def get_user_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message(message.chat.id, 'Wrong format!\n/get_user group_number')
        return
    name = l[1]
    try:
        player = Player.get(Player.name == name)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    bot.send_message(message.chat.id, "Group number: {}\nUsername: @{}\nRace: {}\nEnergy: {}\nCurrent time: {}".format(
        player.name, player.username, player.race, player.energy, player.time
    ))


@bot.message_handler(commands=['status'])
@restricted(Role.ADMIN)
def status_cmd(message):
    msg = ''
    for player in Player.select().order_by(Player.name):
        t = player.time
        msg += '{}: {} min {} sec\n'.format(player.name, int(t // 60), t % 60)
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['balance'])
@restricted(Role.PLAYER)
def balance_cmd(message):
    try:
        player = Player.get(Player.tg_id == message.chat.id)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'Не могу найти вас в списках игроков. Напишите @{}'.format(
            config.creatorUsername))
        logger.error("Can't find user - {} in players database!".format(message.from_user.username))
        return
    bot.send_message(player.tg_id, "У вас сейчас {} энергии".format(player.energy))


@bot.message_handler(commands=['begin'])
@restricted(Role.GOD)
def begin_cmd(message):
    # TODO: Beginning of the quest
    # timer.start(func)
    everyone('Квест начался! Удачи!')
    logger.info('Quest has been started by @{}'.format(message.from_user.username))


@bot.message_handler(commands=['stop'])
@restricted(Role.GOD)
def stop_cmd(message):
    # TODO: Ending of the quest
    everyone('Квест завершен! Всем спасибо за участие!\nИтоги квеста будут объявлены после окончания посвята')
    logger.info('Quest has been stopped by @{}'.format(message.from_user.username))


@bot.message_handler(content_types=['sticker'])
def echo_sticker(message):
    bot.send_message(message.chat.id, 'Классный стикер!')


@bot.message_handler(content_types=['text'])
def echo_text(message):
    bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    bot.polling(none_stop=True)
