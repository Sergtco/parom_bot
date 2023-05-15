from tracker import Tracker
from time import time, sleep
import os
from dotenv import load_dotenv
import threading
from telebot import TeleBot

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from PIL import Image

import io


TIME_DELTA = 5
ids_to_send = {}
commands = {
    "start": {"desc": "Начать работу с ботом"},
    "help": {"desc": "Получить все команды"},
    "get": {"desc": "Получить состояние сайта"},
    "begin": {"desc": "Начать получать оповещение о состоянии каждые n минут/часов  '/begin n(м/ч)', если n = 0, то получать только уведомление об изменении сайта"},
    "end": {"desc": "Перестать получать оповещения."}

}


def check_notification(bot, tracker):
    global ids_to_send
    minute_count = 0

    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.get('https://imex-service.ru/booking/')

# Получаем начальный скриншот страницы
    sleep(5)
    screenshot1 = Image.open(io.BytesIO(driver.get_screenshot_as_png()))

    while True:
        # Обновляем страницу
        driver.refresh()
        sleep(5)
        # Получаем новый скриншот страницы
        screenshot2 = Image.open(io.BytesIO(driver.get_screenshot_as_png()))
        result_screenshot = io.BytesIO(driver.get_screenshot_as_png())

        # Сравниваем скриншоты
        # Если скриншоты не совпадают, значит произошло изменение
        # отправляем уведомление и обновляем скриншот
        res = screenshot1.tobytes() != screenshot2.tobytes()
        for idx in ids_to_send:
            delta = ids_to_send[idx]
            if delta != 0:
                if minute_count % delta == 0:
                    if res:
                        bot.send_message(idx, "Что-то поменялось!")
                        bot.send_photo(idx, result_screenshot)
                    else:
                        bot.send_message(
                            idx, "Ничего не поменялось")
            else:
                if res:
                    bot.send_message(idx, "Что-то поменялось!")
                    bot.send_photo(idx, result_screenshot)

        sleep(60)
        minute_count += 1


def get_commands_string():
    global commands
    s = ""
    for command in commands:
        s += "/" + command + " - " + commands[command]["desc"] + "\n"
    return s


def main():
    global ids_to_send, commands
    tracker = Tracker("https://imex-service.ru/online-form/",
                      "Приём заявок временно приостановлен, по причине отсутствия свободных мест.")

    bot = TeleBot(os.environ["TOKEN"])

    @bot.message_handler(commands=['start', 'help'])
    def start(message):
        bot.send_message(message.from_user.id, "Привет, список доступных команд:\n{}".format(
            get_commands_string()))

    @bot.message_handler(commands=['get'])
    def get(message):
        status = tracker.search()
        bot.send_message(
            message.from_user.id, "Ничего не поменялось" if not status else "Что-то поменялось")

    @bot.message_handler(commands=['begin'])
    def begin(message):
        args = message.text.split()[1:]
        if len(args) != 1:
            bot.send_message(message.from_user.id,
                             "Комманда должна быть типа '/begin n(м/ч)'")
        else:
            if args[0][-1].lower() == "ч" or args[0][-1].lower() == "м":
                ids_to_send[message.from_user.id] = int(
                    args[0][:-1]) * 60 if args[0][-1].lower == "ч" else int(args[0][:-1])
                if args[0][0] != "0":
                    bot.send_message(
                        message.from_user.id, f"Теперь вы будете получать сообщения каждые {args[0]}")
                else:
                    bot.send_message(
                        message.from_user.id, "Теперь придет сообщение, когда сайт изменится!")

    @bot.message_handler(commands=['end'])
    def end(message):
        idx = message.from_user.id
        try:
            ids_to_send.pop(message.from_user.id)
        except KeyError:
            pass
        bot.send_message(message.from_user.id,
                         "Теперь вам не будут приходить оповещения!")

    t = threading.Thread(
        name="Notifier", target=check_notification, args=[bot, tracker])
    t.start()

    bot.polling(non_stop=True, interval=0)


if __name__ == "__main__":
    load_dotenv()
    main()
