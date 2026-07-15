from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import configparser
import os, sys
import csv
import traceback
import time
import random

re="\033[1;31m"
gr="\033[1;32m"
cy="\033[1;36m"

def banner():
    print(f"""
{re}╔╦╗{cy}┌─┐┬  ┌─┐{re}╔═╗  ╔═╗{cy}┌─┐┬─┐┌─┐┌─┐┌─┐┬─┐
{re} ║ {cy}├┤ │  ├┤ {re}║ ╦  ╚═╗{cy}│  ├┬┘├─┤├─┘├┤ ├┬┘
{re} ╩ {cy}└─┘┴─┘└─┘{re}╚═╝  ╚═╝{cy}└─┘┴└─┴ ┴┴  └─┘┴└─
            Version: 1.3
     Modified by @saifalisew1508
        """)

cpass = configparser.RawConfigParser()
cpass.read('config.data')

try:
    api_id = cpass['cred']['id']
    api_hash = cpass['cred']['hash']
    phone = cpass['cred']['phone']
    client = TelegramClient(phone, api_id, api_hash)
except KeyError:
    os.system('clear')
    banner()
    print("\033[91m[!] Please run \033[92mpython3 setup.py\033[91m first !!!\n")
    sys.exit(1)

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    os.system('clear')
    banner()
    client.sign_in(phone, input(gr+'[+] Enter the sent code: '+re))

os.system('clear')
banner()
input_file = sys.argv[1]
users = []
with open(input_file, encoding='UTF-8') as f:
    rows = csv.reader(f,delimiter=",",lineterminator="\n")
    next(rows, None)
    for row in rows:
        user = {
            'username': row[0],
            'id': int(row[1]),
            'access_hash': int(row[2]),
            'name': row[3],
        }

        users.append(user)

chats = []
last_date = None
chunk_size = 200
groups=[]

result = client(GetDialogsRequest(
             offset_date=last_date,
             offset_id=0,
             offset_peer=InputPeerEmpty(),
             limit=chunk_size,
             hash = 0
         ))
chats.extend(result.chats)

for chat in chats:
    try:
        if chat.megagroup== True:
            groups.append(chat)
    except:
        continue

print(gr+'[+] Choose a group to add members: '+re)
for i, group in enumerate(groups):
    print(str(i) + '- ' + group.title)
g_index = input(gr+"Enter a Number: "+re)
target_group=groups[int(g_index)]

target_group_entity = InputPeerChannel(target_group.id,target_group.access_hash)

print(gr+"[1] Add member by user ID\n[2] Add member by username ")
mode = int(input(gr+"Input: "+re))
n = 0

for user in users:
    n += 1
    if n % 50 == 0:
        time.sleep(900)
    try:
        print("Adding {}".format(user['id']))
        if mode == 1:
            user_to_add = InputPeerUser(user['id'], user['access_hash'])
        elif mode == 2:
            if user['username'] == "":
                continue
            user_to_add = client.get_input_entity(user['username'])
        else:
            sys.exit(re+"[!] Invalid Mode Selected. Please Try Again.")
        client(InviteToChannelRequest(target_group_entity, [user_to_add]))
        print(gr+"[+] Waiting for 60-180 sec ...")
        time.sleep(random.randrange(60, 180))
    except PeerFloodError:
        print(re+"[!] Getting Flood Errors from Telegram. \n[!] Script is stopping for now. \n[!] Please try again after some time.")
    except UserPrivacyRestrictedError:
        print(re+"[!] The user's privacy settings do not allow you to do this. Skipping ...")
    except:
        traceback.print_exc()
        print(re+"[!] Unexpected Error ...")
        continue
