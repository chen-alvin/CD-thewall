from flask import Flask, request, render_template,redirect,flash,session
from flask.ext.bcrypt import Bcrypt
from flask_bootstrap import Bootstrap
from mysqlconnection import MySQLConnector
import re

app = Flask(__name__)
Bootstrap(app)
app.secret_key='blah'
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app, 'thewall') # db we are using for login/reg/The Wall
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PW_REGEX = re.compile(r'^(?=.*\d)(?=.*[A-Za-z])[a-zA-Z0-9\d]{8,}$')

@app.route('/')
def redirect():
    return render_template('index1.html')

@app.route('/users')
def index():
    query = 'select user_id, first_name, last_name, created_at, email from users'
    users = mysql.query_db(query)
    return render_template('index1.html',users = users)

@app.route('/users/new')
def new():
    return 1

@app.route('/users/<id>/edit')
def edit():
    return 1

@app.route('/users/<id>')
def show():
    return 1

@app.route('/users/create', methods=['POST'])
def create():
    return 1

@app.route('/users/<id>/destroy')
def destroy():
    return 1

@app.route('/users/<id>', methods=['POST'])
def update():
    return 1

app.run(debug=True)
