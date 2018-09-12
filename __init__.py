from telebot import types
from telebot import apihelper
from peewee import DoesNotExist
from functools import wraps
import logging
import pickle

import telebot
import config
from mwt import MWT
from config import db
from users import User, Player, Challenge, Role
from timing import Timer

timer = Timer(name='Round')
timer.set_duration(12*60)

saveTimer = Timer(name='saver')
saveTimer.set_duration(1 * 60)

currentRound = 0
FILENAME = 'time.dat'

logger = logging.getLogger('bot')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger.setLevel(logging.DEBUG)

# To store chosen groups. Group: recipient
transfers = {}

bot = telebot.TeleBot(token=config.token)

# using proxy in Russia
apihelper.proxy = {
    # 'http': 'http://46.101.149.132:3128',
    # 'https': 'https://46.101.149.132:3128'
    # 'http': 'http://79.138.99.254:8080',
    # 'https': 'https://79.138.99.254:8080'
     'http': 'http://5.148.128.44:80',
     'https': 'https://5.148.128.44:80'
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
    exists = True
    try:
        user = User.get(User.tg_id == message.chat.id)
    except DoesNotExist:
        exists = False
    if exists:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы')
        return
    bot.send_message(message.chat.id, "SYSTEM:\nЕсли вы не участник квеста введите команду /reg чтобы продолжить")
    bot.send_message(message.chat.id, config.greetings)
    bot.send_message(message.chat.id, config.collectGroupNumber)
    bot.register_next_step_handler(message, get_group_number)


def get_group_number(message):
    if not check_text(message, get_group_number):
        return
    if message.text == '/reg':
        reg_cmd(message)
        return
    s = message.text
    if not s.isdecimal():
        logger.warning("Not a digit in <get_group_number> by {}".format(message.from_user.username))
        bot.send_message(message.chat.id, config.warningGroupNumber)
        bot.register_next_step_handler(message, get_group_number)
        return
    a = int(s)
    if (a < 101 or a > 118) and a != 141 and a != 646:
        logger.warning("Wrong number in <get_group_number> by {}".format(message.from_user.username))
        bot.send_message(message.chat.id, config.warningTooLarge)
        bot.register_next_step_handler(message, get_group_number)
        return
    (race, r) = config.get_race(s)
    user = User.create(tg_id=message.chat.id, name=s, username=message.from_user.username, role=Role.PLAYER)
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
@restricted(Role.GOD)
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
    kp_username = l[3]
    try:
        kp = User.get(User.username == kp_username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    # with db.atomic() as txn
    challenge = Challenge.create(name=challenge_name, round=r)
    kp.role = Role.KP
    kp.challenge = challenge
    kp.save()

    logger.info("Challenge '{}' has been made. KP: {} - {}".format(challenge_name, kp.name, kp_username))
    bot.send_message(message.chat.id, 'Success!')
    bot.send_message(kp.tg_id, "You became an admin of " + challenge_name)


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


@bot.message_handler(commands=['reload'])
@restricted(Role.GOD)
def reload_cmd(message):
    # TODO: restarting timer
    config.load()
    load()


@bot.message_handler(commands=['time'])
def time_cmd(message):
    t = timer.get_time()
    msg = 'Текущее время с момента начала раунда: {} мин {} сек'.format(int(t // 60), int(t % 60))
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
        bot.register_next_step_handler(message, transfer3)
        return
    amount = int(message.text)
    if amount <= 0:
        bot.send_message(message.chat.id, config.warningWrongAmount)
        bot.register_next_step_handler(message, transfer3)
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
    code = message.text.upper()
    try:
        player = Player.get(Player.tg_id == message.chat.id)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'Не могу найти вас в списках игроков. Напишите @yury_zh')
        logger.error("Can't find user - {} in players database!".format(message.from_user.username))
        return
    if config.secondaryArtifacts.count(code):
        # TODO: Delete artifact
        config.secondaryArtifacts.remove(code)  # Deleting artifact
        config.dump()
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
        if player.currentPurpose >= len(config.purposes[player.race - 1]):
            player.finish = True
            if currentRound >= 10:
                player.time += timer.get_time()
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
    bot.send_message(message.chat.id, "Group number: {}\nUsername: @{}\nRace: {}\nType: {}\nEnergy: {}\n"
                                      "Current time: {} min {} sec\nCurrent purpose: {}\n"
                                      "Current round: {}\nFinished: {}".format(
        player.name, player.username, player.race, player.round, player.energy, int(player.time // 60),
        int(player.time % 60), player.currentPurpose, player.currentRound, player.finish
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
    config.dump()
    timing.autosave()
    global currentRound
    for player in Player.select().where(Player.currentRound == currentRound):
        bot.send_message(player.tg_id, 'Ваша первая КПшка - {}'.format(
            config.kp[player.race - 1][player.currentRound]))
    for kp in User.select().where(User.role == Role.KP):
        kp.currentTeamName = set_next_team(kp, currentRound)
        kp.save()
        bot.send_message(kp.tg_id, 'Текущая группа - {}'.format(kp.currentTeamName))
    timer.start(next_round)
    everyone('Квест начался! Удачи!')
    logger.info('Quest has been started by @{}'.format(message.from_user.username))


@bot.message_handler(commands=['stop'])
@restricted(Role.GOD)
def stop_cmd(message):
    ending()
    logger.info('Quest has been stopped by @{}'.format(message.from_user.username))


@bot.message_handler(commands=['set_round'])
@restricted(Role.GOD)
def set_round_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2 or not l[1].is_decimal():
        bot.send_message(message.chat.id, "Wrong format!\n/set_round <num>")
    n = int(l[1])
    global currentRound
    currentRound = n


def next_round():
    global currentRound
    for player in Player.select().where(Player.currentRound == currentRound):
        player.time += timer.get_duration()  # Maximal time
        player.currentRound += 1
        bot.send_message(player.tg_id, config.endingOfRound)
        bot.send_message(player.tg_id, 'Ваша следующая КПшка - {}'.format(
            config.kp[player.race - 1][player.currentRound]))
        player.save()
        try:
            kp = User.get(User.currentTeamName == player.name)
        except DoesNotExist:
            logger.critical("Can't find active kp for {} - @{}".format(player.name, player.username))
            bot.send_message(config.creatorID, "Can't find active kp for {} - @{}".format(player.name, player.username))
            kp = None
        if kp is not None:
            bot.send_message(kp.tg_id, 'Раунд закончился, пожалуйста введите комманду /add <num> чтобы добавить '
                                       'энергию команде. Если энергии не полагается введите /add 0')
    currentRound += 1
    if currentRound < 10:
        timer.start(next_round)
    else:
        timer.set_duration(30*60)
        timer.start(ending)


def ending():
    # TODO: Ending
    everyone('Квест завершен! Всем спасибо за участие!\nИтоги квеста будут объявлены после окончания посвята')
    for player in Player.select().where(not Player.finish):
        player.time += timer.get_duration()
        player.save()
    msg = ''
    for player in Player.select().order_by(Player.time.desc()):
        t = player.time
        msg += '{}: {} min {} sec\n'.format(player.name, int(t // 60), t % 60)
    bot.send_message(config.creatorID, msg)


@bot.message_handler(commands=['add'])
@restricted(Role.KP)
def add_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2 or not l[1].is_decimal():
        bot.send_message(message.chat.id, 'Wrong format!\n/add <num>')
        return
    try:
        kp = User.get(User.tg_id == message.chat.id)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'Не могу найти вас в базе пользователей')
        logger.error("Can't find @{} - {} in database".format(message.from_user.username, message.chat.id))
        return
    if kp.role != Role.KP:
        bot.send_message(kp.tg_id, 'Вы не КПшник!')
        logger.info("Unauthorized access to <add> cmd by @{}".format(kp.username))
        return
    try:
        player = Player.get(Player.name == kp.currentTeamName)
    except DoesNotExist:
        bot.send_message(kp.tg_id, 'Что-то пошло не так! Напишите @{}'.format(config.creatorUsername))
        logger.critical('No active team for @{} - {}'.format(kp.username, kp.tg_id))
        set_next_team(kp, currentRound)
        return
    player.energy += int(l[1])
    player.save()
    kp.currentTeamName = set_next_team(kp, currentRound)
    kp.save()
    bot.send_message(kp.tg_id, 'Следующая группа - {}'.format(kp.currentTeamName))


def set_next_team(kp, round):
    name = kp.challenge.name
    r = kp.challenge.round
    for player in Player.select().where(Player.round == r):
        if config.kp[player.race - 1][round] == name:
            return player.name
    logger.critical("Can't find next group for {} {} - @{}".format(name, r, kp.username))
    bot.send_message(config.creatorID, "Can't find next group for {} {} - @{}".format(
        name, r, kp.username
    ))
    return '-1'


@bot.message_handler(commands=['release'])
@restricted(Role.KP)
def release_cmd(message):
    t = timer.get_time()
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2 or not l[1].isdecimal():
        bot.send_message(message.chat.id, 'Wrong format!\n/release <num>')
        return
    n = int(l[1])
    try:
        kp = User.get(User.tg_id == message.chat.id)
    except DoesNotExist:
        logger.error("Can't find @{} - {} in database".format(message.from_user.username, message.chat.id))
        bot.send_message(message.chat.id, 'Что-то пошло не так. Напишите номер группы и текущее время @{}'.format(
            config.creatorUsername))
        return
    try:
        player = Player.get(Player.name == kp.currentTeamName)
    except DoesNotExist:
        logger.error("Can't find player")
        bot.send_message(message.chat.id, 'Что-то пошло не так. Напишите номер группы и текущее время @{}'.format(
            config.creatorUsername))
        return
    player.energy += n
    player.time += t
    player.currentRound += 1
    player.save()
    kp.currentTeamName = set_next_team(kp, player.currentRound)
    kp.save()
    bot.send_message(kp.tg_id, 'Следующая группа - {}'.format(kp.currentTeamName))
    bot.send_message(player.tg_id, 'Ваша следующая КПшка - {}'.format(config.kp[player.race - 1][player.currentRound]))


@bot.message_handler(commands=['help'])
def help_cmd(message):
    try:
        user = User.get(User.tg_id == message.chat.id)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'Это бот посвята ВМК МГУ 2018. Зарегистрируйтесь чтобы использовать его.\n'
                                          'Введите команду /start чтобы начать')
        return
    bot.send_message(user.tg_id, config.commands[user.role])


@bot.message_handler(content_types=['sticker'])
def echo_sticker(message):
    bot.send_message(message.chat.id, 'Классный стикер!')


@bot.message_handler(content_types=['text'])
def echo_text(message):
    bot.send_message(message.chat.id, message.text)


def save():
    with open(FILENAME, 'wb') as file:
        pickle.dump(timer, file)
        pickle.dump(currentRound, file)


def load():
    logger.info("Timer loaded")
    global timer
    global currentRound
    with open(FILENAME, 'rb') as file:
        timer = pickle.load(file)
        currentRound = pickle.load(file)
        timer.resume()


def autosave():
    save()
    logger.info("Autosave done!")
    saveTimer.start(autosave)


if __name__ == '__main__':
    bot.polling(none_stop=True)
