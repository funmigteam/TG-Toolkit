from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, UserBlockedError
from telethon.tl.functions.channels import InviteToChannelRequest
import configparser
import os
import sys
import csv
import traceback
import time
import random

re = "\033[1;31m"
gr = "\033[1;32m"
cy = "\033[1;36m"

def banner():
    print(f"""
{re}╔╦╗{cy}┌─┐┬  ┌─┐{re}╔═╗  ╔═╗{cy}┌─┐┬─┐┌─┐┌─┐┌─┐┬─┐
{re} ║ {cy}├┤ │  ├┤ {re}║ ╦  ╚═╗{cy}│  ├┬┘├─┤├─┘├┤ ├┬┘
{re} ╩ {cy}└─┘┴─┘└─┘{re}╚═╝  ╚═╝{cy}└─┘┴└─┴ ┴┴  └─┘┴└─
            Auto-remove blocked users
        """)

cpass = configparser.RawConfigParser()
cpass.read('config.data')

def pick_session_file():
    sessions = [f for f in os.listdir('.') if f.endswith('.session')]
    if not sessions:
        return None
    if len(sessions) == 1:
        return sessions[0]
    print(gr + '[+] Choose an account session: ' + re)
    for i, name in enumerate(sessions):
        print(str(i) + '- ' + name)
    s_index = input(gr + 'Enter a Number: ' + re)
    try:
        return sessions[int(s_index)]
    except (ValueError, IndexError):
        print(re + '[!] Invalid selection.')
        sys.exit(1)

try:
    api_id = cpass['cred']['id']
    api_hash = cpass['cred']['hash']
    phone = cpass['cred']['phone']
    session_file = pick_session_file()
    if session_file:
        session_name = os.path.splitext(session_file)[0]
        client = TelegramClient(session_name, api_id, api_hash)
        if session_name and session_name[0] in '+0123456789':
            phone = session_name
    else:
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
    client.sign_in(phone, input(gr + '[+] Enter the sent code: ' + re))

os.system('clear')
banner()

if len(sys.argv) > 1:
    input_file = sys.argv[1]
else:
    input_file = 'members.csv'

if not os.path.exists(input_file):
    print(re + '[!] Input file not found: ' + input_file)
    print(re + '[!] Usage: python3 add2channel_clean.py members.csv')
    sys.exit(1)

users = []
header = None
with open(input_file, encoding='UTF-8') as f:
    rows = csv.reader(f, delimiter=",", lineterminator="\n")
    header = next(rows, None)
    for row in rows:
        user = {
            'username': row[0],
            'id': int(row[1]),
            'access_hash': int(row[2]),
            'name': row[3],
            'row': row,
        }
        users.append(user)

if not header:
    print(re + '[!] Empty members file.')
    sys.exit(1)

chats = []
last_date = None
chunk_size = 200
channels = []

result = client(GetDialogsRequest(
    offset_date=last_date,
    offset_id=0,
    offset_peer=InputPeerEmpty(),
    limit=chunk_size,
    hash=0
))
chats.extend(result.chats)

for chat in chats:
    try:
        if getattr(chat, 'broadcast', False) or getattr(chat, 'megagroup', False):
            channels.append(chat)
    except Exception:
        continue

if not channels:
    print(re + '[!] No channels found to select.')
    sys.exit(1)

print(gr + '[+] Choose a channel to add members: ' + re)
for i, channel in enumerate(channels):
    channel_type = 'channel' if getattr(channel, 'broadcast', False) else 'supergroup'
    print(str(i) + '- ' + channel.title + ' [' + channel_type + ']')

c_index = input(gr + 'Enter a Number: ' + re)
try:
    target_channel = channels[int(c_index)]
except (ValueError, IndexError):
    print(re + '[!] Invalid selection.')
    sys.exit(1)

target_channel_entity = InputPeerChannel(target_channel.id, target_channel.access_hash)

print(gr + '[1] Add member by user ID\n[2] Add member by username ')
mode = int(input(gr + 'Input: ' + re))

def save_members(path, header_row, user_list):
    with open(path, 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header_row)
        for u in user_list:
            writer.writerow(u['row'])

n = 0
i = 0
while i < len(users):
    user = users[i]
    n += 1
    if n % 50 == 0:
        time.sleep(60)
    try:
        print("Adding {}".format(user['id']))
        if mode == 1:
            user_to_add = InputPeerUser(user['id'], user['access_hash'])
        elif mode == 2:
            if user['username'] == "":
                i += 1
                continue
            user_to_add = client.get_input_entity(user['username'])
        else:
            sys.exit(re + "[!] Invalid Mode Selected. Please Try Again.")
        client(InviteToChannelRequest(target_channel_entity, [user_to_add]))
        print(gr + "[+] Waiting for 5-15 sec ...")
        time.sleep(random.randrange(5, 15))
        i += 1
    except UserBlockedError:
        print(re + "[!] User blocked. Removing from members file: {}".format(user['id']))
        users.pop(i)
        save_members(input_file, header, users)
        continue
    except PeerFloodError:
        print(re + "[!] Getting Flood Errors from Telegram. \n[!] Script is stopping for now. \n[!] Please try again after some time.")
        break
    except UserPrivacyRestrictedError:
        print(re + "[!] The user's privacy settings do not allow you to do this. Skipping ...")
        i += 1
    except Exception:
        traceback.print_exc()
        print(re + "[!] Unexpected Error ...")
        i += 1
