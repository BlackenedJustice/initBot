from peewee import *

token = '605058683:AAHW95wwWBiPd4L3o4Craf0tPG-y3kG4AZc'
creatorID = 144454876
creatorUsername = 'yury_zh'

db = PostgresqlDatabase(  # Heroku
    'dek49hcm75f5mv',
    user='vfwefpaxjbwjtl',
    password='6d020954f2b3f8281051b10b4871f45f41eb2407b65deeffe64496abab8a12ae',
    host='ec2-54-75-251-84.eu-west-1.compute.amazonaws.com'
)
'''
db = PostgresqlDatabase(
    'yury',
    user='yury',
    password='508087yhpR',
    host='localhost'
)
#db = SqliteDatabase('data.db')
'''
races = {
    '101': (1, 1),
    '102': (6, 1),
    '103': (4, 1),
    '104': (3, 1),
    '105': (8, 1),
    '106': (9, 1),
    '107': (10, 1),
    '108': (1, 2),
    '109': (9, 2),
    '110': (7, 1),
    '111': (5, 1),
    '112': (3, 2),
    '113': (2, 1),
    '114': (5, 2),
    '115': (6, 2),
    '116': (4, 2),
    '117': (8, 2),
    '118': (2, 2),
    '141': (10, 2),
    '142': (7, 2)
}

kp = [
    ['Giant', 'Researcher', 'Pixie', 'Elf', 'Werewolf', 'Ork', 'Goblin', 'Dwarf', 'Troll', 'Demon'],  # Researcher
    ['Dwarf', 'Troll', 'Demon', 'Giant', 'Researcher', 'Pixie', 'Elf', 'Werewolf', 'Ork', 'Goblin'],  # Werewolf
    ['Pixie', 'Elf', 'Werewolf', 'Ork', 'Goblin', 'Dwarf', 'Troll', 'Demon', 'Giant', 'Researcher'],  # Dwarf
    ['Researcher', 'Pixie', 'Elf', 'Werewolf', 'Ork', 'Goblin', 'Dwarf', 'Troll', 'Demon', 'Giant'],  # Elf
    ['Werewolf', 'Ork', 'Goblin', 'Dwarf', 'Troll', 'Demon', 'Giant', 'Researcher', 'Pixie', 'Elf'],  # Ork
    ['Elf', 'Werewolf', 'Ork', 'Goblin', 'Dwarf', 'Troll', 'Demon', 'Giant', 'Researcher', 'Pixie'],  # Pixie
    ['Ork', 'Goblin', 'Dwarf', 'Troll', 'Demon', 'Giant', 'Researcher', 'Pixie', 'Elf', 'Werewolf'],  # Goblin
    ['Goblin', 'Dwarf', 'Troll', 'Demon', 'Giant', 'Researcher', 'Pixie', 'Elf', 'Werewolf', 'Ork'],  # Troll
    ['Demon', 'Giant', 'Researcher', 'Pixie', 'Elf', 'Werewolf', 'Ork', 'Goblin', 'Dwarf', 'Troll'],  # Giant
    ['Troll', 'Demon', 'Giant', 'Researcher', 'Pixie', 'Elf', 'Werewolf', 'Ork', 'Goblin', 'Dwarf']   # Demon
]


def get_race(num):
    r = races.get(num)
    if r is None:
        r = (-10, -10)
    return r


greetings = 'Здравствуйте! Добро пожаловать на квест Посвящения в студенты ВМК 2018!\n' \
            'Этот бот будет помогать вам в прохождении квеста\n' \
            'А теперь, давайте познакомимся'
collectGroupNumber = 'Введите номер группы'
successfulRegistration = 'Приятно познакомиться! Квест вот-вот начнется'
adminsGreetings = 'Введите ваше имя'
chooseGroupForTransfer = 'Пожалуйста, выберите группу, которой вы хотите перевести энергию'
chooseTransferAmount = 'Пожалуйста, введите колличество энергии для перевода'
enterArtifactCode = 'Введите код артефакта'
enterPaySum = 'Скажите количество энергии для платежа'

artifactWrongCode = 'Духи меча гневаются, потому что не знают такого кода, попробуйте еще раз!'
artifactWrongRace = 'Духи меча приняли Ваш код, но этот артефакт принадлежит другой расе, меняйтесь!'
artifactTooEarly = 'Духи меча видят, что вы поторопились с этой целью!'
artifactSecondary = 'Духи меча посчитали этот артефакт ненужным, но дарят Вам за него энергию!'
artifactUsed = 'Цель уже была достигнута ранее!'

warningWrongDataFormat = 'Неправильный формат данных!\nПопробуйте еще раз'
warningGroupNumber = 'Номер группы должен быть числом!\nПопробуйте еще раз'
warningTooLarge = 'Слишком неправильное число!\nПопробуйте еще раз'
warningNoSuchGroup = 'Такой группы нет\nВыполните команду /transfer еще раз'
warningWrongAmount = 'Число должно быть положительным!\nПопробуйте еще раз'
warningNotEnoughEnergy = 'У вас недостаточно энергии для перевода'
warningSmthWentWrongTransfer = 'Что-то пошло не так...\nВыполните команду /transfer еще раз'

endingOfRound = 'Время на раунд закончилось, переходите к следующей КПшке'


secondaryArtifacts = ['M224WQ',
                      'HLR6OW',
                      'Y75V93',
                      '6R5FII',
                      'ZSW941',
                      'JL0UX7',
                      '5T3CZD',
                      'AB1DM0',
                      '8Y1P84',
                      'G82KIL']
secondaryEnergyAmount = 100

artifacts = [['GLVH01',
              'TUC6XV'],  # Researchers
             ['62UKOV',
              '0U2OSZ',  # Werewolves
              'IQC3N2'],
             ['G315GW',
              '8RL7QX',  # Dwarfs
              '4IQ1D3'],
             ['S26YQU',
              'S2KUHZ',  # Elves
              'QL2OE2',
              'AJDPFP'],
             ['PHWIQS',
              'KKE5JZ',  # Orks
              '3B1R9U',
              'MTBENF'],
             ['FC8AU5',
              'YPQ7U9',  # Pixies
              'PMYEEJ'],
             ['ZC5HWN',
              'YEGN8X',  # Goblins
              'B6X1U9'],
             ['4WPPPW',
              'DLHYI9',  # Trolls
              'XWWVHY'],
             ['VB5PHV',
              '57AW7P',  # Giants
              'X192KT',
              '5GG8ZP'],
             ['KSL9FK',
              '4I3NYI',  # Demons
              'TGSEU4']]

purposes = [['Вы раздобыли потерянные детали и починили корабль!',
             'Вы собрали информацию об этом мире!'],  # Researchers
            ['Вы нашли чешую дракона и другие ингридиенты для зелья!',
             'Вы прошли обряд инициации!',  # Werewolves
             'Вы нашли информацию о пещере драконов!'],
            ['Вы нашли запчасти для механизма!',
             'Вы освободили из-под завалов великого мастера!',  # Dwarfs
             'Вы вооружились!'],
            ['С помощью хрустального яйца вы смогли найти местоположение похитителя!',
             'Вы определили избранных эльфов для отряда!',  # Elves
             'Вы вернули рубин!',
             'Вы обрели новое пристанище!'],
            ['Вы разузгали рецепт создания молота "Древнее Око"!',
             'Вы нашли ресурсы для создания молота "Древнее Око"!',  # Orks
             'Вы нашли источник энергии!',
             'Вы провели ритуал создания!'],
            ['Вы наладили отношения с другими расами!',
             'Вы выслушали пророчество!',  # Pixies
             'Вы нашли ресурсы на создание временного заменителя пыльцы!'],
            ['Вы заключили договоры с другими расами!',
             'Вы нашли кладку яиц драконов!',  # Goblins
             'Вы нашли пещеру и украли все золото в ней!'],
            ['Вы нашли лидера!',
             'Вы разузнали подробную информацию о нем!',  # Trolls
             'Вы подобрали отряд троллей!'],
            ['Вы нашли вход в исторический архив и сделали новую запись!',
             'Вы нашли источник силы горных драконов!',  # Giants
             'Вы узнали заклинание, которое поможет вам разобраться с горными драконами!',
             'Вы нашли ингридиенты для заклинания!'],
            ['Вы собрали информацию о драконах и нашли их слабые места!',
             'Вы нашли вожака драконов и заполучили его сердце!',  # Demons
             'Вы нашли артефакты для Обряда Подчинения!']]
