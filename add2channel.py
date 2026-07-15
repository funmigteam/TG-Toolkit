from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import configparser
import os
import sys
import csv
import traceback
import time
import random
import json

re = "\033[1;31m"
gr = "\033[1;32m"
cy = "\033[1;36m"

def banner():
    print(f"""
{re}╔╦╗{cy}┌─┐┬  ┌─┐{re}╔═╗  ╔═╗{cy}┌─┐┬─┐┌─┐┌─┐┌─┐┬─┐
{re} ║ {cy}├┤ │  ├┤ {re}║ ╦  ╚═╗{cy}│  ├┬┘├─┤├─┘├┤ ├┬┘
{re} ╩ {cy}└─┘┴─┘└─┘{re}╚═╝  ╚═╝{cy}└─┘┴└─┴ ┴┴  └─┘┴└─
            Add Members to Channel
        """)

def load_invite_log(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}

def save_invite_log(path, data):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2, sort_keys=True)
    os.replace(tmp_path, path)

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
    print(re + '[!] اعضا پیدا نشد: ' + input_file)
    print(re + '[!] Usage: python3 add2channel.py members.csv')
    sys.exit(1)

users = []
with open(input_file, encoding='UTF-8') as f:
    rows = csv.reader(f, delimiter=",", lineterminator="\n")
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
    print(re + '[!] هیچ کانالی برای انتخاب پیدا نشد.')
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

invite_log_path = "channel_invite_log.json"
invite_log = load_invite_log(invite_log_path)
channel_key = str(target_channel.id)
seen_ids = set(invite_log.get(channel_key, []))

n = 0
for user in users:
    if user['id'] in seen_ids:
        print(gr + "[=] Skipping already attempted id: {}".format(user['id']))
        continue
    n += 1
    if n % 50 == 0:
        time.sleep(60)
    try:
        print("Adding {}".format(user['id']))
        if mode == 1:
            user_to_add = InputPeerUser(user['id'], user['access_hash'])
        elif mode == 2:
            if user['username'] == "":
                continue
            user_to_add = client.get_input_entity(user['username'])
        else:
            sys.exit(re + "[!] Invalid Mode Selected. Please Try Again.")
        client(InviteToChannelRequest(target_channel_entity, [user_to_add]))
        print(gr + "[+] Waiting for 5-15 sec ...")
        time.sleep(random.randrange(5, 15))
        seen_ids.add(user['id'])
        invite_log[channel_key] = sorted(seen_ids)
        save_invite_log(invite_log_path, invite_log)
    except PeerFloodError:
        print(re + "[!] Getting Flood Errors from Telegram. \n[!] Script is stopping for now. \n[!] Please try again after some time.")
        invite_log[channel_key] = sorted(seen_ids)
        save_invite_log(invite_log_path, invite_log)
        break
    except UserPrivacyRestrictedError:
        print(re + "[!] The user's privacy settings do not allow you to do this. Skipping ...")
        seen_ids.add(user['id'])
        invite_log[channel_key] = sorted(seen_ids)
        save_invite_log(invite_log_path, invite_log)
    except Exception:
        traceback.print_exc()
        print(re + "[!] Unexpected Error ...")
        continue
