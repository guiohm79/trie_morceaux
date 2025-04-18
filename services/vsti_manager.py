import json
import os

VSTI_LIST_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'vsti_list.json')
VSTI_LIST_PATH = os.path.abspath(VSTI_LIST_PATH)

def load_vsti_list():
    if not os.path.exists(VSTI_LIST_PATH):
        return []
    with open(VSTI_LIST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_vsti_list(vsti_list):
    with open(VSTI_LIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(vsti_list, f, ensure_ascii=False, indent=2)

def add_vsti(name):
    vsti_list = load_vsti_list()
    if name not in vsti_list:
        vsti_list.append(name)
        save_vsti_list(vsti_list)

def remove_vsti(name):
    vsti_list = load_vsti_list()
    if name in vsti_list:
        vsti_list.remove(name)
        save_vsti_list(vsti_list)

def update_vsti(old_name, new_name):
    vsti_list = load_vsti_list()
    if old_name in vsti_list:
        idx = vsti_list.index(old_name)
        vsti_list[idx] = new_name
        save_vsti_list(vsti_list)
