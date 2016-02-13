import threading
import jinja2
import json
import random
import string
import os

GLOBAL_LOCK = threading.Lock()
SITES_ENABLED = '/etc/nginx/sites-enabled/'
SITES_AVAILABLE = '/etc/nginx/sites-available/'
CONFIG_FILE = """
# WebSocket Proxy
#
# Simple forwarding of unencrypted HTTP and WebSocket to a different host
# (you can even use a different host instead of localhost:8080)

server {
    listen 80;

    # host name to respond to
    server_name {{name}}.spoc.courses;

    location / {
        # switch off logging
        access_log off;

        # redirect all HTTP traffic to localhost:8080
        proxy_pass http://{{target_url}};
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # WebSocket support (nginx 1.4)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
"""
template = Template(CONFIG_FILE)

def GenerateProxy(target_url):
    name = random_string()
    while not check_availablity(name):
        name = random_string()
    config_file = generate_config_file(name, target_url)
    save_config_file(target_url.replace(':','.'), config_file)
    return json.dumps({'proxy':name}, 200)

def RemoveProxy(target_url):
    file_name = target_url.replace(':','.')
    try:
        GLOBAL_LOCK.acquire()
        os.system('rm {}/{}'.format(SITES_ENABLED, file_name))
        os.system('rm {}/{}'.format(SITES_AVAILABLE, file_name))
    finally:
        GLOBAL_LOCK.release()
    restart_nginx()

def check_availablity(name):
    GLOBAL_LOCK.acquire()
    try:
        flag = name in os.listdir(SITES_AVAILABLE)
    finally:
        GLOBAL_LOCK.release()
    return flag

def generate_config_file(name, target_url):
    return template.render(name=name, target_url=target_url)

def save_config_file(file_name, content):
    try:
        GLOBAL_LOCK.acquire()
        with open("{}/{}".format(SITES_ENABLED, file_name), 'r') as f_out:
            f_out.write(content)
        os.system("ln -s {}/{} {}/{}".format(SITES_AVAILABLE, file_name, SITES_ENABLED, file_name))
    finally:
        GLOBAL_LOCK.release()

def restart_nginx():
    try:
        GLOBAL_LOCK.acquire()
        os.system("service nginx restart")
    finally:
        GLOBAL_LOCK.release()

def random_string():
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(20))
