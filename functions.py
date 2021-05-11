# functions.py

# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
import telebot # pip3 install pyTelegramBotAPI
from telebot import types
import datetime # pip3 install datetime
import psycopg2 as sql # sudo apt-get install postgresql libpq-dev postgresql-client postgresql-client-common   and   pip3 install psycopg2  or  pip3 install psycopg2-binary 
import traceback
import logging
import requests
import json
import os
import socket
# from apiclient import discovery

from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
from googleapiclient.discovery import build
import io

import lang
import config
import keyboard

socket.setdefaulttimeout(30) # 5 minutes

con = keyboard.con

bot = telebot.TeleBot(config.token)

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'token.json'

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
spread_service = build('sheets', 'v4', credentials=credentials)
with con:
    cur = con.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS {config.path_tb} ({config.path_tb_column})")
    cur.execute(f"CREATE TABLE IF NOT EXISTS {config.key_tb} ({config.key_tb_column})")
    con.commit()
    cur.close()

############################################## Functions ####################################################

def check_user(chat_id):
    with con:
        cur = con.cursor()
        cur.execute(f"SELECT key FROM {config.key_tb} WHERE status='{chat_id}'")
        key_ls = cur.fetchall()
    if len(key_ls) != 0 or int(chat_id) in config.admin_ls:
        return True
    else:
        return False

def upl_photo(src, file_info, parent_folder_id):
    try:
        # print(file_info.file_path.split('/')[1])
        folder_id = parent_folder_id
        file_path = 'img/'+file_info.file_path.split('/')[1]
        file_metadata = {
                        'name': file_info.file_path.split('/')[1],
                        'parents': [folder_id]
                        # 'mimeType': 'image/jpeg'
                    }
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        r = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        # print(r)
        return True
    except:
        # print(traceback.format_exc())
        return False

def welcome(message):
    with con:
        cur = con.cursor()
        cur.execute(f"SELECT status, key FROM {config.key_tb} WHERE key='{message.text}'")
        key_ls = cur.fetchall()
        print(key_ls)
        if len(key_ls) != 0 and (key_ls[0][0] == str(message.chat.id) or key_ls[0][0] == ''):
            try:
                cur.execute(f"UPDATE {config.key_tb} SET status='{message.chat.id}' WHERE key='{message.text}'")
                con.commit()
                bot.send_message(message.chat.id, lang.text_hello_message, reply_markup=keyboard.main_kb)
            except:
                print(traceback.format_exc())
        elif message.chat.id in config.admin_ls:
            bot.send_message(message.chat.id, lang.text_hello_message, reply_markup=keyboard.main_kb)
        else:
            bot.send_message(message.chat.id, lang.text_code_404)

def upload(message, cell_id): # , p_folder_id
    try:
        with con:
            cur = con.cursor()
            cur.execute(f"SELECT parent FROM {config.path_tb} WHERE chat_id='{message.chat.id}'")
            p_folder_id = cur.fetchall()[0][0]

        sheet = spread_service.spreadsheets()
        results = drive_service.files().list(
            pageSize=1, 
            fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
            q=f"'{p_folder_id}' in parents and name contains 'Фото'").execute() # and mimeType='application/vnd.google-apps.spreadsheet'

        table_results = drive_service.files().list(
            pageSize=1, 
            fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
            q=f"name contains 'Журнал работы' and '{p_folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'").execute()

        folderName = str(datetime.datetime.now().date())
        parentID = results['files'][0]['id']
        body = {
              'name': folderName,
              'mimeType': "application/vnd.google-apps.folder"
            }
        if parentID:
            body['parents'] = [parentID]

        root_folder = drive_service.files().create(body = body).execute()

        value_input_option = 'RAW'

        range_mass = f'План работ!B{cell_id}:B{cell_id}'
        work = sheet.values().get(spreadsheetId=table_results['files'][0]['id'],
            range=range_mass).execute()['values'][0][0]

        values = [
            [
                folderName, work, '', '', '', f"https://drive.google.com/drive/u/2/folders/{root_folder['id']}"
            ],
        ]
        body = {
            'values': values
        }

        range_mass = f'Журнал работ!A1:F'
        work_cell_id = len(sheet.values().get(spreadsheetId=table_results['files'][0]['id'],
            range=range_mass).execute()['values']) + 1

        with con:
            cur = con.cursor()
            cur.execute(f"UPDATE {config.path_tb} SET workpath='{root_folder['id']}', cell_id='{work_cell_id}' WHERE chat_id='{message.chat.id}'")
            con.commit()

        result = spread_service.spreadsheets().values().update(
            spreadsheetId=table_results['files'][0]['id'], range=f'Журнал работ!A{work_cell_id}:F{work_cell_id}',
            valueInputOption=value_input_option, body=body).execute()
        # cell_id = call.data.split(' ')[1]
        msg = bot.send_message(message.chat.id, lang.text_choose_worker, reply_markup=keyboard.worker_ls(message.chat.id, work_cell_id))
    except:
        print(traceback.format_exc())

def generate_key_get(message):
    if not message.text in lang.Cancel:
        with con:
            cur = con.cursor()
            cur.execute(f"INSERT INTO {config.key_tb} VALUES ('{message.text}', '')")
            con.commit()
        bot.send_message(message.chat.id, f'{lang.text_key_generate[0]} {message.text} {lang.text_key_generate[1]}', reply_markup=keyboard.key_kb)
    else:
        bot.send_message(message.chat.id, lang.Canceled)

def del_key_get(message):
    if not message.text in lang.Cancel:
        with con:
            cur = con.cursor()
            cur.execute(f"DELETE FROM {config.key_tb} WHERE key='{message.text}'")
            con.commit()
        bot.send_message(message.chat.id, f'{lang.text_key_delete[0]} {message.text} {lang.text_key_delete[1]}', reply_markup=keyboard.key_kb)
    else:
        bot.send_message(message.chat.id, lang.Canceled)

############################################## Commands #####################################################

@bot.message_handler(func=lambda message: '/start' in message.text, commands=['start'])
def auth(message):
    msg = bot.send_message(message.chat.id, lang.text_enter_code)
    bot.register_next_step_handler(msg, welcome)

@bot.message_handler(func=lambda message: '/key' == message.text and message.chat.id in config.admin_ls, commands=['key'])
def key_menu(message):
    try:
        bot.send_message(message.chat.id, lang.text_choose_action, reply_markup=keyboard.key_kb)
    except:
        print(traceback.format_exc())

############################################## Messages #####################################################

@bot.message_handler(func=lambda message: message.text == None and check_user(message.chat.id), content_types=['photo'])
def upl_more_photo(message):
    # print(message)
    try:
        with con:
            cur = con.cursor()
            cur.execute(f"SELECT spread, workpath, cell_id FROM {config.path_tb} WHERE chat_id='{message.chat.id}'")
            data = cur.fetchall()[0]
            table_id = data[0]
            parent_folder_id = data[1]
            cell_id = data[2]

        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = 'img/'+file_info.file_path.split('/')[1]
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        if upl_photo(src, file_info, parent_folder_id):
            bot.send_message(message.chat.id, lang.text_photo_upl) #
            os.system(f'rm {src}')
        else:
            if upl_photo(src, file_info, parent_folder_id):
                bot.send_message(message.chat.id, lang.text_photo_upl) #
                os.system(f'rm {src}')
                os.system('exit()')
            else:
                bot.send_message(message.chat.id, lang.text_upl_error)
    except:
        print(traceback.format_exc())

@bot.message_handler(func=lambda message: lang.butt_main_get in message.text and check_user(message.chat.id), content_types=['text'])
def choose_ob(message):
    try:
        with con:
            cur = con.cursor()
            cur.execute(f"DELETE FROM {config.path_tb} WHERE chat_id='{message.chat.id}'")
            con.commit()
        bot.send_message(message.chat.id, lang.text_choose_obj, reply_markup=keyboard.get_adr())
    except:
        print(traceback.format_exc())

@bot.message_handler(func=lambda message: lang.butt_create in message.text and message.chat.id in config.admin_ls, content_types=['text'])
def generate_key(message):
    msg = bot.send_message(message.chat.id, lang.text_enter_new_key, reply_markup=keyboard.cancel_kb)
    bot.register_next_step_handler(msg, generate_key_get)

@bot.message_handler(func=lambda message: lang.butt_del_key in message.text and message.chat.id in config.admin_ls, content_types=['text'])
def generate_key(message):
    msg = bot.send_message(message.chat.id, lang.text_enter_new_key, reply_markup=keyboard.cancel_kb)
    bot.register_next_step_handler(msg, del_key_get)

@bot.message_handler(func=lambda message: land.butt_free_key_list in message.text and message.chat.id in config.admin_ls, content_types=['text'])
def free_key(message):
    with con:
        cur = con.cursor()
        cur.execute(f"SELECT key FROM {config.key_tb} WHERE status=''")
        ls = cur.fetchall()
    text = str()
    if len(ls) != 0:
        for item in ls:
            text = f"{text}\n{item[0]}"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, lang.text_emp_list)

@bot.message_handler(func=lambda message: lang.butt_key_list in message.text and message.chat.id in config.admin_ls, content_types=['text'])
def all_key(message):
    with con:
        cur = con.cursor()
        cur.execute(f"SELECT key FROM {config.key_tb}")
        ls = cur.fetchall()
    text = str()
    if len(ls) != 0:
        for item in ls:
            text = f"{text}\n{item[0]}"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, lang.text_emp_list)

@bot.message_handler(func=lambda message: message.text in lang.Cancel and check_user(message.chat.id), content_types=['text'])
def cancel_f(message):
    bot.send_message(message.chat.id, lang.text_main_menu, reply_markup=keyboard.main_kb)

############################################## Inline #####################################################

@bot.callback_query_handler(func=lambda call: f'id' in call.data and not 'wid' in call.data and check_user(call.message.chat.id))
def choose_work(call):
    try:
        data = call.data.split(' ')
        fid = data[1]
        results = drive_service.files().list(
            pageSize=2, 
            fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
            q=f"'{fid}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and name contains 'Журнал работы'").execute()
        if results['files'] == []:
            bot.send_message(call.message.chat.id, lang.text_no_work)
            folderName = 'Фото'
            parentID = fid
            body = {
                  'name': folderName,
                  'mimeType': "application/vnd.google-apps.folder"
                }
            if parentID:
                body['parents'] = [parentID]
            root_folder = drive_service.files().create(body = body).execute()

            fileName = 'Журнал работы'
            parentID = fid
            body = {
                  'name': fileName,
                  'mimeType': "application/vnd.google-apps.spreadsheet"
                }
            if parentID:
                body['parents'] = [parentID]
            spreadsheet = drive_service.files().create(body = body).execute()
            print(spreadsheet)

            with con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO {config.path_tb} VALUES ('{call.message.chat.id}', '{fid}', '', '', '')")
                con.commit()
            
        elif results['files'][0]['name'] == 'Журнал работы':
            sheet = spread_service.spreadsheets()
            SAMPLE_RANGE_NAME = 'План работ!B2:B2'
            result = sheet.values().get(spreadsheetId=results['files'][0]['id'],
                    range=SAMPLE_RANGE_NAME).execute()
            with con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO {config.path_tb} VALUES ('{call.message.chat.id}', '{fid}', '{results['files'][0]['id']}', '', '')")
                con.commit()
            if result.get('values') != None:
                page = 1
                bot.send_message(call.message.chat.id, lang.text_work_plan, reply_markup=keyboard.get_work(call.message.chat.id, page))
            else:
                bot.send_message(call.message.chat.id, lang.text_no_work)
    except:
        print(traceback.format_exc())

@bot.callback_query_handler(func=lambda call: 'next' in call.data and check_user(call.message.chat.id))
def get_next_page(call):
    try:
        data = call.data.split(' ')
        page = data[1]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard.get_work(call.message.chat.id, page))
    except:
        print(traceback.format_exc())

@bot.callback_query_handler(func=lambda call: 'workn' in call.data and check_user(call.message.chat.id))
def get_photo(call):
    cell_id = int(call.data.split(' ')[1])
    upload(call.message, cell_id)

@bot.callback_query_handler(func=lambda call: 'upl' in call.data and check_user(call.message.chat.id))
def get_more_photo(call):
    msg = bot.send_message(call.message.chat.id, lang.text_upl_photo)
    bot.register_next_step_handler(msg, more_upload)#, table_id, parent_id)

@bot.callback_query_handler(func=lambda call: 'worker' in call.data and check_user(call.message.chat.id))
def get_worker_id(call):
    cell_id = call.data.split(' ')[1]
    msg = bot.send_message(call.message.chat.id, lang.text_choose_worker, reply_markup=keyboard.worker_ls(call.message.chat.id, cell_id))

@bot.callback_query_handler(func=lambda call: 'wid' in call.data and check_user(call.message.chat.id))
def add_worker(call):
    cell_id = call.data.split(' ')[2]

    worker_id = int(call.data.split(' ')[1]) + 2

    sheet = spread_service.spreadsheets()
    value_input_option = 'RAW'

    range_mass = f'Список персонала и подрядчиков!A{worker_id}:A{worker_id}'

    with con:
        cur = con.cursor()
        cur.execute(f"SELECT spread FROM {config.path_tb} WHERE chat_id='{call.message.chat.id}'")
        SPREADSHEET_ID = cur.fetchall()[0][0]
        # cur.execute(f"DELETE FROM {config.path_tb} WHERE chat_id='{call.message.chat.id}'")

    worker_name = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
        range=range_mass).execute()['values'][0][0]

    values = [
        [
            worker_name
        ],
    ]
    body = {
        'values': values
    }

    result = spread_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=f'Журнал работ!D{cell_id}:D{cell_id}',
        valueInputOption=value_input_option, body=body).execute()
    bot.send_message(call.message.chat.id, lang.text_upl_photo)