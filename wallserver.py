from flask import Flask, request, render_template,redirect,flash,session
from flask.ext.bcrypt import Bcrypt
from mysqlconnection import MySQLConnector
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PW_REGEX = re.compile(r'^(?=.*\d)(?=.*[A-Za-z])[a-zA-Z0-9\d]{8,}$')

app = Flask(__name__)
app.secret_key='blah'
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app, 'thewall') # db we are using for login/reg/The Wall

@app.route('/')
def index():
    if 'user_id' in session: # if the user is already logged in
        if session['user_id'] == -1: # logout the guest user
            session.clear()
        return redirect('/wall') # redirect them to the wall
    else:
        flash('Welcome! Please login or register.')
    return render_template('index.html')

################### Registration/Login routes #####################
@app.route('/create_user', methods=['POST'])
def create_user():
    email = request.form['email']
    if len(request.form['first_name']+request.form['last_name']) < 3:
        flash('Name must be at least one character')
        return redirect('/')
    first_name = request.form['first_name'][0].upper() + request.form['first_name'][1:].lower()
    last_name = request.form['last_name'][0].upper() + request.form['last_name'][1:].lower()
    password = request.form['password']
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': email }
    user = mysql.query_db(user_query, query_data)# user will be returned in a list

    if user[0]['email'] == email:
        flash('Email already registered. Login instead?')
        return redirect('/')
    if not EMAIL_REGEX.match(email):
        flash('Invalid email!')
        return redirect('/')
    if not PW_REGEX.match(password):
        flash('Passwords must be at least 8 characters and contain letters and numbers')
        return redirect('/')
    pw_hash = bcrypt.generate_password_hash(password)
    # now we insert the new user into the database
    insert_query = "INSERT INTO users (first_name,last_name,email,password,created_at)\
                    VALUES            (:first_name,:last_name,:email,:pw_hash,NOW())"
    query_data = {'first_name':first_name, 'last_name':last_name,'email':email,'pw_hash':pw_hash}
    mysql.query_db(insert_query, query_data)
    if '_flashes' in session:
        session.pop('_flashes')
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': email }
    user = mysql.query_db(user_query, query_data)# user will be returned in a list
    session.clear()
    session['user_id'] = user[0]['user_id']
    session['name'] = user[0]['first_name'] +' '+user[0]['last_name']

    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': email }
    user = mysql.query_db(user_query, query_data)# user will be returned in a list
    if user == []:
        flash('Email not found!')
        return redirect('/')
    elif bcrypt.check_password_hash(user[0]['password'], password): # correct password
    # login user
        session.clear()
        session['user_id'] = user[0]['user_id']
        session['name'] = user[0]['first_name'] +' '+user[0]['last_name']
        return redirect('/')
    else:
    # set flash error message and redirect to login page
        flash('Error logging in.')
        return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        session.clear()
        flash('Logged out!')
    else:
        flash('You are not logged in.')
    return redirect('/')

################### Message/Posts Routes ####################
@app.route('/wall')
def wall():
    if 'user_id' not in session:
        flash('error! not logged in.')
        return redirect('/')
    query = "select message_id, message, created_at, first_name, last_name, messages.user_id from messages \
            join (select first_name, last_name, user_id from users) as users \
	            on users.user_id = messages.user_id \
            order by messages.created_at desc"
    posts = mysql.query_db(query)
    #### get a list of all messages
    query = "select message_id from messages"
    message_ids = mysql.query_db(query)
    msgArr = []
    for x in message_ids:
        msgArr.append(x['message_id'])
    commentdictionary = {}
    for message in msgArr:
        query = "select comment_id,message_id, comment, first_name, last_name, comments.created_at,users.user_id from comments \
                join users on users.user_id = comments.user_id where message_id = :id"
        data = {'id':message}
        commentdictionary[message] = mysql.query_db(query,data)
        #print 'message id:',message,str(comments)+'\n'
    #print commentdictionary
    #print type(commentdictionary) # dictionary - message_id:comments
    #print type(commentdictionary[18]) # list - all comments of 18
    #print type(commentdictionary[18][0]) # dictionary first comment of 18
    #print type(commentdictionary[18][0]['comment']) # string - first comment comment of 18
    return render_template('wall.html', all_posts = posts, commentdict = commentdictionary)

@app.route('/create_message', methods=['POST'])
def create_message():
    message = request.form['message']
    user_id = session['user_id']
    # insert the new message into the database
    insert_query = "INSERT INTO messages (message,created_at,updated_at,user_id)\
                    VALUES            (:message,NOW(),NOW(),:user_id)"
    query_data = {'message':message, 'user_id':user_id}
    mysql.query_db(insert_query, query_data)
    return redirect('/wall')

@app.route('/delete_message/<id>', methods=['POST'])
def delete_message(id):
    print id
    print type(id)
    delete_query = "DELETE FROM comments where message_id = :id; \
                    DELETE FROM messages where message_id = :id"
    query_data = {'id':id}
    mysql.query_db(delete_query,query_data)
    return redirect('/wall')

@app.route('/delete_comment/<id>', methods=['POST'])
def delete_comment(id):
    print id
    print type(id)
    delete_query = "DELETE FROM comments where comment_id = :id;"
    query_data = {'id':id}
    mysql.query_db(delete_query,query_data)
    return redirect('/wall')

@app.route('/create_comment', methods=['POST'])
def create_comment():
    comment = request.form['comment']
    user_id = session['user_id']
    message_id = request.form['message_id']
    # insert the new message into the database
    insert_query = "INSERT INTO comments (comment,created_at,updated_at,user_id,message_id)\
                    VALUES            (:comment,NOW(),NOW(),:user_id,:message_id)"
    query_data = {'comment':comment, 'user_id':user_id,'message_id':message_id}
    mysql.query_db(insert_query, query_data)
    return redirect('/wall')

###################  Debugging ####################
@app.route('/soft')
def test():
    mysql.query_db('DELETE FROM `thewall`.`comments`;DELETE FROM `thewall`.`messages`;DELETE FROM `thewall`.`users`;')
    return redirect('/admin')

@app.route('/guest')
def guest():
    if 'user_id' not in session:
        session['user_id'] = -1
        session['name'] = 'Guest'

    return redirect('/wall')

@app.route('/reset') # for debugging
def areyousure():
    queryfile = open('thewall.sql')
    #print queryfile.read()
    mysql.query_db(queryfile.read())
    session.clear()
    flash("Alert: Database has been reset.")
    return redirect('/admin')

@app.route('/admin')
def graball():
    # if 'id' in session:
    #     if session['user_id'] != 1:
    #         redirect('/')
    # else:
    #     redirect('/')
    query="select * from users"
    users = mysql.query_db(query)
    query="select * from messages"
    messages = mysql.query_db(query)
    query="select * from comments"
    comments = mysql.query_db(query)
    return render_template('admin.html', users=users,messages=messages,comments=comments)
app.run(debug=True)
