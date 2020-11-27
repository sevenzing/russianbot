import telebot
from telebot import types
from telebot.types import Message

from pymongo import MongoClient

import contextlib
import os
import time
import json
import random

from tools import pluralForm

import mongotools


def listener(messages):
    for message in messages:
        message_to_log(message)


def message_to_log(message, to_print=None):
    chat_id = message.chat.id
    username = message.from_user.username

    text = str(message.text).replace('\n', ' ')
    if to_print is not None:
        text = to_print

    print(f'[{username}/{chat_id}]: {text}')


def bot_say(chat_id, text, parse_mode=None, to_print=None, reply_markup=None):
    try:
        m = bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
        message_to_log(m)
    except Exception as e:
        print('Error:', e)


def bot_say_with_exit(chat_id, text, parse_mode=None, to_print=None):
    markup = types.ReplyKeyboardMarkup()
    i1 = types.KeyboardButton('/go')
    i2 = types.KeyboardButton('/me')
    i3 = types.KeyboardButton('/help')
    markup.row(i1)
    markup.row(i2, i3)

    m = bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=markup)


def get_random_ask():
    with open('incorrect_words.txt', 'r', encoding='utf-8', errors='ignore') as f:
        incorrect = f.readlines()
    with open('correct_words.txt', 'r', encoding='utf-8', errors='ignore') as f:
        correct = f.readlines()

    words = []
    while words.__len__() < 4:
        word = correct[random.randint(0, 1000) % correct.__len__()].replace('\n', '')
        flag = False
        for _ in words:
            if word.lower() == _.lower():
                flag = True
        if not flag:

            if word[-1] == ' ':
                word = word[:-1]
            if word[0] == ' ':
                word = word[1:]
            words.append(word)
    while words.__len__() < 5:

        ans = incorrect[random.randint(0, 1000) % incorrect.__len__()].replace('\n', '')
        flag = False
        for _ in words:
            if ans.lower() == _.lower():
                flag = True
        if not flag:
            if not ans[0].isalpha():
                ans = ans[1:]
            words.append(ans)

    return (words, ans)


def get_real_name(message: Message):
    realname = ''

    if message.from_user.first_name is not None:
        realname += message.from_user.first_name + ' '
    if message.from_user.last_name is not None:
        realname += message.from_user.last_name

    if realname[-1] == ' ':
        realname = realname[:-1]

    return realname


def get_text_from_file(filename):
    with open(filename, 'r') as f:
        return f.read()



TOKEN = os.getenv('BOT_TOKEN')
mongourl = os.getenv('MONGO_URL')
    
bot = telebot.TeleBot(TOKEN, threaded=False)
mongoClient = MongoClient(mongourl)

TIME_SLEEP = .1  # SECONDS
TIME_TO_BACKUP = 25  # MINUTES
LAST_UPDATE = time.time()
OWNER = 'sevenzing'
OWNER_ID = 339999894

start_message = get_text_from_file('messages/start_message.txt')
help_message = get_text_from_file('messages/help_message.txt')
offer_message = get_text_from_file('messages/offer_message.txt')


# BOT HANDLERS

@bot.message_handler(commands=['start'])
def start(message: Message):
    chat_id = message.chat.id
    username = message.from_user.username
    realname = get_real_name(message)

    if not mongotools.user_in_database(db, chat_id):
        if mongotools.create_new_user(db, chat_id, username, realname):
            print(f'@{username} записан в базу данных')
            bot_say(OWNER_ID, f'@{username}/{realname} записан в базу данных')
        else:
            pass

    bot_say(chat_id, start_message, parse_mode="Markdown", to_print="Выведен start_message для пользователя")


@bot.message_handler(commands=['help'])
def say_help(message: Message):
    chat_id = message.chat.id
    bot_say(chat_id, help_message,
            parse_mode="Markdown",
            to_print="Выведен help_message для пользователя")


@bot.message_handler(commands=['go'])
def go(message: Message):
    chat_id = message.chat.id
    user = mongotools.get_user(db, chat_id)
    if user is None:
        start(message)
        return
    
    if user['game_in_process'] == 1:
        bot_say(chat_id, 'Раунд уже идет!')
        return

    mongotools.update_user(db, chat_id, game_in_process=1)
    ask_q(message)


def ask_q(message: Message):
    chat_id = message.chat.id
    user = mongotools.get_user(db, chat_id)
    if user is None:
        print('ошибка [ask_q()]: user is None')
        start(message)
        return

    words, ans = get_random_ask()
    random.shuffle(words)
    markup = types.ReplyKeyboardMarkup(row_width=3)
    i1 = types.KeyboardButton(words[0])
    i2 = types.KeyboardButton(words[1])
    i3 = types.KeyboardButton(words[2])
    i4 = types.KeyboardButton(words[3])
    i5 = types.KeyboardButton(words[4])
    markup.add(i1, i2, i3, i4, i5)

    reply = f"_Вопрос #{user['count'] + 1}_. Выберите слово, где ударение указано *неверно*:"

    for word in words:
        reply += f'\n{word}'

    bot_say(chat_id, reply, parse_mode='Markdown', reply_markup=markup)
    # m = bot.send_message(chat_id, reply, reply_markup=markup, parse_mode="Markdown")
    # message_to_log(m)
    mongotools.update_user(db, chat_id, current_q=str((words, ans)))


@bot.message_handler(commands=['stop'])
def stop(message: Message):
    chat_id = message.chat.id
    user = mongotools.get_user(db, chat_id)
    if user is None:
        print('ошибка [stop()]: user is None')
        start(message)
        return

    if user['game_in_process'] == 0:
        bot_say(chat_id, 'Раунд еще не начат. /help')
        return

    temp_count = user['count']
    game_in_process = 0
    count = 0
    current_q = '()'

    mongotools.update_user(db, chat_id, game_in_process=game_in_process, count=count, current_q=current_q)

    reply = f"Раунд закончен.\nВы ответили на {temp_count} {pluralForm(temp_count, 'вопрос', 'вопроса', 'вопросов')}" + \
            f" подряд. Неплохо!\nЧтобы начать заново, напишите /go"
    bot_say_with_exit(chat_id, reply)


@bot.message_handler(commands=['top'])
def top(message: Message):
    chat_id = message.chat.id
    user = mongotools.get_user(db, chat_id)
    if user is None:
        print('ошибка [top()]: user is None')
        start(message)
        return

    top_list = mongotools.get_top_users(db, amount=5)

    reply = 'Топ игроков:'
    for user in top_list:
        if user['name'] == 'None' or user['name'] == None:
            name = user['realname']
        else:
            name = '@' + user['name']

        score = user['score']
        reply += f"\n{name}: {score} {pluralForm(score, 'правильный', 'правильных', 'правильных')} " \
            f"{pluralForm(score, 'ответ', 'ответа', 'ответов')}"

    bot_say(chat_id, reply)


@bot.message_handler(commands=['me'])
def about_me(message: Message):
    chat_id = message.chat.id
    user = mongotools.get_user(db, chat_id)
    if user is None:
        print('ошибка [about_me()]: user is None')
        start(message)
        return

    score = user['score']
    questions = user['questions']

    if user['name'] == 'None' or user['name'] == None:
        name = user['realname']
    else:
        name = '@' + user['name']

    reply = f'Ваше имя: {name}\nКоличество правильных ответов: {score}\nКоличество неправильных ответов: {questions - score}'

    bot_say(chat_id, reply)


@bot.message_handler(commands=['delete'])
def delete(message: Message):
    chat_id = message.chat.id
    user = mongotools.get_user(db, chat_id)
    if user is None:
        print('ошибка [delete()]: user is None')
        start(message)
        return
    name = user['name']
    realname = user['realname']
    mongotools.update_user(db, chat_id, game_in_process=0, current_q='()', count=0,
                           name=name, score=0, questions=0, realname=realname)

    bot_say_with_exit(chat_id, 'Данные успешно удалены.')
    about_me(message)


@bot.message_handler(commands=['offer'])
def offer(message: Message):
    chat_id = message.chat.id
    user = mongotools.get_user(db, chat_id)
    if user is None:
        print('ошибка [delete()]: user is None')
        start(message)
        return
    text = message.text
    name = user['name']
    realname = user['realname']

    try:
        words = text.replace('/offer ', '')
        assert words.__len__() > 0
        assert '/' not in words

        bot_say(OWNER_ID, f'@{name}/{realname}/{chat_id} предложил: {words}')
        bot_say(chat_id, 'Заявка отправлена')
    except:
        bot_say(chat_id, offer_message, parse_mode='Markdown')


@bot.message_handler(func=lambda message: '[COMMAND]' in str(message.text))
def do_command(message: Message):
    chat_id = message.chat.id
    text = message.text
    username = message.from_user.username

    if username != OWNER:
        answer_by_text(message)

    if 'make_backup' in text:
        pass


    elif 'get_backup' in text:
        pass

    elif 'send' in text:
        try:
            to_send_chat_id = text.split('|')[1]
            to_send_message = text.split('|')[2]
            bot_say(to_send_chat_id, to_send_message)
            bot_say(chat_id, f'Отправлено.\nКому: {to_send_chat_id}\nЧто: {to_send_message}')

        except Exception as e:
            bot_say(chat_id, f'не получилось {e}')
    else:
        bot_say(chat_id, 'Команда не найдена')


@bot.message_handler(content_types=['text'])
def answer_by_text(message: Message):
    chat_id = message.chat.id
    username = message.from_user.username
    realname = get_real_name(message)
    text = message.text
    user = mongotools.get_user(db, chat_id)
    if user is None:
        print('ошибка [answer_by_text()]: user is None')
        start(message)
        return

    game_in_process = user['game_in_process']
    current_q = user['current_q']
    count = user['count']
    score = user['score']
    questions = user['questions']

    if game_in_process == 0:
        bot_say(chat_id, 'Раунд еще не начат. /help')
        return

    words, ans = eval(current_q)

    if text.lower() not in map(lambda x: x.lower(), words):
        bot_say(chat_id, 'Пожалуйста, выберите один из вариантов ответа. Если что-то пошло не так, закончи раунд /stop')
        return

    if text.lower() == ans.lower():
        count += 1
        score += 1
        questions += 1

        mongotools.update_user(db, chat_id, count=count, score=score, questions=questions,
                               name=username, realname=realname)
        bot_say(chat_id, 'Отлично! Следующий вопрос.')
        ask_q(message)

    else:
        temp_count = count
        count = 0
        current_q = '()'
        game_in_process = 0
        questions += 1

        mongotools.update_user(db, chat_id, game_in_process=game_in_process, count=count,
                               questions=questions, current_q=current_q, name=username, realname=realname)

        reply = f"Неверно :( Правильный ответ был «{ans.lower()}».\nВы ответили на {temp_count} " + \
                f"{pluralForm(temp_count, 'вопрос', 'вопроса', 'вопросов')}" + \
                f" подряд. Неплохо!\nЧтобы начать заново, напишите /go"
        bot_say_with_exit(chat_id, reply)


try:
    print('Загружаю базу данных...')
    db = mongoClient.russianbot.users

    bot.set_update_listener(listener)
    print('Начинаю polling.')
    bot.polling(timeout=60, none_stop=True)

except Exception as error:
    bot_say(OWNER_ID, error)
    raise
