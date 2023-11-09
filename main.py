import os
import subprocess
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
PAGE_ID = os.getenv('PAGE_ID')
SERVER_IPS = os.getenv('SERVER_IPS').split(',')

def update_status(api_key, page_id, component_id, new_status):
    url = f"https://api.statuspage.io/v1/pages/{page_id}/components/{component_id}"
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
        print(f"ステータス更新成功: {component_id} to {new_status}")
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
        component_env_var = f"COMPONENT_ID_{ip_address.replace('.', '_')}"
        component_id = os.getenv(component_env_var)
        
        if not component_id:
            print(f"コンポーネントIDが見つかりません: {ip_address}")
            continue
        
        if ping_server(ip_address):
            update_status(api_key, page_id, component_id, "operational")
        else:
            update_status(api_key, page_id, component_id, "major_outage")

while True:
    monitor_servers(API_KEY, PAGE_ID, SERVER_IPS)
    time.sleep(10)