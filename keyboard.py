#keyboard.py

from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
from googleapiclient.discovery import build
import io
import traceback

from telebot import types
import psycopg2 as sql

import lang
import config

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'token.json'

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
spread_service = build('sheets', 'v4', credentials=credentials)

con = sql.connect(dbname=config.db_name, user=config.db_user, password=config.db_pass, host='localhost')

########################################################## Keyboard ########################################################

# Убрать любую клавиатуру
none_kb = types.ReplyKeyboardRemove()

# Клавиатура в главном меню
main_kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
get_butt = types.KeyboardButton(lang.butt_main_get)
main_kb.add(get_butt)

cancel_kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
cancel_butt = types.KeyboardButton(lang.Cancel[0])
cancel_kb.add(cancel_butt)

key_kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
generate_butt = types.KeyboardButton(lang.butt_create)
free_list_butt = types.KeyboardButton(lang.butt_free_key_list)
all_list_butt = types.KeyboardButton(lang.butt_key_list)
del_key_butt = types.KeyboardButton(lang.butt_del_key)
key_kb.add(generate_butt, free_list_butt, all_list_butt, del_key_butt, cancel_butt)

########################################################### Inline keyboard ################################################################

def upl_more(cell_id): #p_id, t_id
    upl_kb = types.InlineKeyboardMarkup(row_width=2)
    # upl_butt = types.InlineKeyboardButton('Загрузить', callback_data=f"upl")
    worker_butt = types.InlineKeyboardButton(lang.butt_choose_worker, callback_data=f"worker {cell_id}") #{t_id}
    upl_kb.add(worker_butt)# upl_butt, 
    return upl_kb

def get_adr():
    results = drive_service.files().list(pageSize=100,
    fields="nextPageToken, files(id, name, mimeType, parents)",
    q="mimeType='application/vnd.google-apps.folder' and '1Z_lzWgyru0u0MNKsr6td3MoRwnkSFYAc' in parents").execute()
    get_kb = types.InlineKeyboardMarkup(row_width=1)
    for i in results['files']:
        text = i['name']
        get_butt = types.InlineKeyboardButton(text, callback_data=f"id {i['id']}")
        get_kb.add(get_butt)
    return get_kb

def get_work(chat_id, page): # SPREADSHEET_ID, f_id,
    try:
        with con:
            cur = con.cursor()
            cur.execute(f"SELECT spread FROM {config.path_tb} WHERE chat_id='{chat_id}'")
            SPREADSHEET_ID = cur.fetchall()[0][0]
        min_cell = page
        if int(page) == 1:
            min_cell = str(int(page)+1)
        max_cell = str(15+int(page))
        sheet = spread_service.spreadsheets()
        SAMPLE_RANGE_NAME = f'План работ!B{min_cell}:B{max_cell}'
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                range=SAMPLE_RANGE_NAME).execute()
        back_butt = types.InlineKeyboardButton(lang.butt_back, callback_data=f"next {int(page) - 16}")
        work_kb = types.InlineKeyboardMarkup(row_width=2)
        if result.get('values') != None:
            for i in range(len(result['values'])):
                text = result['values'][i][0]
                i_butt = types.InlineKeyboardButton(text, callback_data=f"workn {i + int(page) + 1}")
                work_kb.add(i_butt)
            next_butt = types.InlineKeyboardButton(lang.butt_next, callback_data=f"next {int(max_cell) + 1}")
            if int(page) == 1:
                work_kb.add(next_butt)
            if int(page) != 1:
                work_kb.add(back_butt, next_butt)
        if result.get('values') == None:
            work_kb.add(back_butt)
        return work_kb
    except:
        print(traceback.format_exc())

def worker_ls(chat_id, cell_id): # t_id
    with con:
        cur = con.cursor()
        cur.execute(f"SELECT spread FROM {config.path_tb} WHERE chat_id='{chat_id}'")
        SPREADSHEET_ID = cur.fetchall()[0][0]

    worker_kb = types.InlineKeyboardMarkup(row_width=1)
    sheet = spread_service.spreadsheets()
    worker_range = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
            range='Список персонала и подрядчиков!B2:B').execute()['values']
    for i in range(len(worker_range)):
        i_butt = types.InlineKeyboardButton(worker_range[i][0], callback_data=f"wid {i} {cell_id}")
        worker_kb.add(i_butt)
    return worker_kb

# get_kb = types.InlineKeyboardMarkup(row_width=1)
# get_butt = types.InlineKeyboardButton(lang.butt_get, url="http://wecanshare.ru/CarOwner/Index")
# get_kb.add(get_butt)