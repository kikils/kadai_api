import os
import re

from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from peewee import *
from playhouse.postgres_ext import PostgresqlExtDatabase


db = PostgresqlExtDatabase(
    database=os.environ.get('POSTGRES_DB'),
    user=os.environ.get('POSTGRES_USER'),
    password=os.environ.get('POSTGRES_PASSWORD'),
    host=os.environ.get('POSTGRES_HOST'),
    port=os.environ.get('POSTGRES_PORT'),
    register_hstore=False)

class Product(Model):
    class Meta:
        database = db

    name = CharField()
    amount = IntegerField()
    price = BigIntegerField(null=True)
    sales = BigIntegerField(null=True, default=0)

db.create_tables([Product])


app = Flask(__name__)
auth = HTTPBasicAuth()
USERS = {
    'name': os.environ.get('BASIC_AUTH_NAME'),
    'password': os.environ.get('BASIC_AUTH_PW')
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

@app.route('/secret/')
@auth.login_required
def auth():
    context = 'SUCCESS'
    return context

@app.route('/calc')
def calc():
    formula = request.query_string.decode('utf-8', '')
    if formula is None:
        return 'ERROR'
    if re.match(r'[0-9\+\-\*\(\)\/]', formula) is None:
        return 'ERROR'
    return str(int(eval(formula)))

@app.route('/stocker')
def stocker():
    function = request.args.get('function')
    def addstock(request):
        name = request.args.get('name')
        if name is None:
            return 'ERROR'
        amount = request.args.get('amount', '1')
        if re.search(r'[^0-9]', amount):
            return 'ERROR'
        Product.create(name=name, amount=int(amount))
        return ''

    def checkstock(request):
        name = request.args.get('name')
        if name is None:
            context = ''
            for instance in Product.select().order_by(Product.name):
                if instance.amount == 0:
                    continue
                context += '{}: {}\n'.format(instance.name, instance.amount)
            return context
        else:
            instance = Product.select().where(Product.name == name).first()
            if instance is None:
                return ''
            return '{}: {}\n'.format(instance.name, instance.amount)

    def sell(request):
        name = request.args.get('name')
        amount = request.args.get('amount', '1')
        price = request.args.get('price')
        if name is None or amount is None:
            return 'ERROR'
        if re.search(r'[^0-9]', str(amount)):
            return 'ERROR'
        if int(amount) <= 0:
            return 'ERROR'

        sales = 0
        if (price is not None
                and re.search(r'[0-9]', str(price))
                and int(price) > 0):
            sales  = int(amount) * int(price)
        query = Product.update(amount=Product.amount - amount, sales=Product.sales + sales).where(Product.name == name)
        query.execute()
        return ''

    def checksales(request):
        query = Product.select(fn.Sum(Product.sales).alias('total')).first()
        return 'sales: {}'.format(query.total)

    def deleteall(request):
        query = Product.delete()
        query.execute()
        return ''
    
    if function is None:
        return 'ERROR'
    if function == 'addstock':
        return addstock(request)
    if function == 'checkstock':
        return checkstock(request)
    if function == 'sell':
        return sell(request)
    if function == 'checksales':
        return checksales(request)
    if function == 'deleteall':
        return deleteall(request)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
