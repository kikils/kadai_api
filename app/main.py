import os

from flask import Flask
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()
USERS = {
    'name': os.environ.get('BASIC_AUTH_NAME'),
    'password': os.environ.get('BASIC_AYTH_PW')
}
ERROR_TEMPLATE_PATH = './templates/401.html'

@auth.verify_password
def verify_password(name, password):
    if (USERS['name'] != name and USERS['password'] != password):
        return False
    return True

@auth.error_handler
def error_handler(status):
    context = ''
    if status in [401, 403]:
        with open(ERROR_TEMPLATE_PATH) as f:
           context = f.read()
    return context, status

@app.route('/')
def index():
    context = 'AMAZON'
    return context

@app.route('/secret')
@auth.login_required
def auth():
    context = 'SUCCESS'
    return context

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
