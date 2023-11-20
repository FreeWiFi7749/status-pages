import os
import subprocess
import requests
import time
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv('PAGE_RELOAD_API_KEY')
PAGE_ID = os.getenv('PAGE_ID')
SERVER_IPS = os.getenv('SERVER_IPS').split(',')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def send_discord_embed(webhook_url, title, description, color=0x00ff00):
    data = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color
        }]
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("Discord埋め込み通知成功")
    else:
        print("Discord埋め込み通知失敗: " + response.text)

STATUS_FILE = 'status_history.json'

def load_status_history():
    try:
        with open(STATUS_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_status_history(history):
    with open(STATUS_FILE, 'w') as file:
        json.dump(history, file, indent=4)

def update_status(api_key, page_id, component_name, component_id, new_status):
    history = load_status_history()
    current_status = history.get(component_id)

    # URL定義を条件分岐の外に移動
    url = f"https://api.statuspage.io/v1/pages/{page_id}/components/{component_id}"

    if current_status != new_status:
        headers = {
            'Authorization': f'OAuth {api_key}',
            'Content-Type': 'application/json',
        }
        data = {
            "component": {
                "status": new_status
            }
        }
        response = requests.patch(url, json=data, headers=headers)

        if response.status_code == 200:
            print(f"ステータス更新成功: {component_name} to {new_status}")
            embed_title = f"{component_name} ステータス更新"
            embed_description = f"ステータスが {new_status} に更新されました。\n詳しいステータス情報は 》https://status.the-seed.games"
            send_discord_embed(DISCORD_WEBHOOK_URL, embed_title, embed_description)
            history[component_id] = new_status
            save_status_history(history)
        else:
            print(f"ステータス更新失敗: {response.content}")

def ping_server(ip_address):
    try:
        subprocess.check_output(['ping', '-c', '1', ip_address])
        return True
    except subprocess.CalledProcessError:
        return False

def monitor_servers(api_key, page_id, server_ips):
    for ip_address in server_ips:
        component_id_env_var = f"COMPONENT_ID_{ip_address.replace('.', '_')}"
        component_name_env_var = f"COMPONENT_NAME_{ip_address.replace('.', '_')}"
        
        component_id = os.getenv(component_id_env_var)
        component_name = os.getenv(component_name_env_var)
        
        if not component_id or not component_name:
            print(f"コンポーネントIDまたは名前が見つかりません: {ip_address}")
            continue
        
        if ping_server(ip_address):
            update_status(api_key, page_id, component_name, component_id, "operational")
        else:
            update_status(api_key, page_id, component_name, component_id, "major_outage")
while True:
    monitor_servers(API_KEY, PAGE_ID, SERVER_IPS)
    time.sleep(10)