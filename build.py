#start.py

# pip install --upgrade google-api-python-client

import telebot # pip3 install pyTelegramBotAPI
from telebot import types
import datetime
import traceback
import logging
import threading
import time as time

from keyboard import config as config
from keyboard import lang as lang
# from keyboard import con
import functions

import cherrypy

bot = functions.bot
config.bot_name = bot.get_me().username

logging.basicConfig(filename="exeption.log", level = logging.INFO)

finished = False

# class WebhookServer(object):
#     # index равнозначно /, т.к. отсутствию части после ip-адреса (грубо говоря)
#     @cherrypy.expose
#     def index(self):
#         length = int(cherrypy.request.headers['content-length'])
#         json_string = cherrypy.request.body.read(length).decode("utf-8")
#         update = telebot.types.Update.de_json(json_string)
#         bot.process_new_updates([update])
#         return ''


# def timer():
#     print('timer')
#     while not(finished):
#         with con:
#             cur = con.cursor()
#             cur.execute(f"SELECT data, chat_id FROM {config.user_tb}")
#             ls = cur.fetchall()
#         now = datetime.datetime.now()
#         for i in ls:
#             times = datetime.datetime.strptime(i[0], '%Y-%m-%d %H:%M:%S')
#             try:
#                 if now.date() == times.date() and now.hour == times.hour:
#                     bot.send_message(i[1], lang.text_notif_today)
#             except:
#                 print(traceback.format_exc())
#         time.sleep(3600)

# threading.Thread(target=timer, daemon=True).start()

def main():
    print('start')
    try:
    #     # bot.polling(none_stop=True)
    #     cherrypy.config.update({
    #         'server.socket_host': '127.0.0.1',
    #         'server.socket_port': config.WEBHOOK_PORT,
    #         'engine.autoreload.on': False
    #     })
    #     cherrypy.quickstart(WebhookServer(), '/', {'/': {}})
        finished = False
        bot.remove_webhook()
        bot.polling(none_stop=True)
    except Exception as e:
        # print(e)
        # logging.error(str(datetime.datetime.now()), e)
        print(traceback.format_exc())
        main()
    finished = True
    print('stop')

if __name__ == '__main__':
    main()