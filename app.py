from flask import Flask, render_template, url_for, request, redirect, session, flash
from models import User, Pharmacy, Uber
import sys
import json
import os

app = Flask(__name__)
#app.secret_key = 'verytoplevelsecret'

app.secret_key = os.urandom(24)
#port = int(os.environ.get('PORT', 5000))

@app.route('/')
def home():
    session.pop('username', None)
    return render_template('home.html')

@app.route('/requestpickup', methods=['GET','POST'])
def requestpickup(userinfo=None):
    if request.method == 'POST':
        if 'username' in session:
            userinfo = User.populateUserInfo(session["username"])
            return render_template('requestpickup.html', userinfo=userinfo)
    else:
        if 'username' in session:
            userinfo = list(User.populateUserInfo(session["username"]))
            return render_template('requestpickup.html', userinfo=userinfo)
        else:
            data = {"first": 'test',
                "last": None,
                "phone": None,
                "dob": None,
                "address": None,
                "pharmacy": None,
                "rx": None}
            userinfo = list(data)
            return render_template('requestpickup.html', userinfo=userinfo)

@app.route('/requestpickup/placeorder', methods=['GET','POST'])
def placeorder(userinfo=None):
    if request.method == 'POST':
        if 'username' in session:
            userinfo=list(User.populateUserInfo(session["username"]))
            session["userinfo"]=userinfo
            #session["order"]=list(User.placeUserOrder(session["username"]))

            return render_template('placeorder.html', userinfo=userinfo)
        else:
            userinfo = {"first": request.form['first'],
                "last": request.form['last'],
                "phone": request.form['phone'],
                "dob": request.form['dob'],
                "address": request.form['address'],
                "pharmacy": request.form['pharmacy'],
                "rx": request.form['rx']}

            #store in session so user cannot keep sending post at orderinfo page, order# in session will keep displaying
            #session["order"]=User.placeorder(userinfo)
            session["userinfo"]=userinfo

            return render_template('placeorder.html', userinfo=userinfo)

@app.route('/requestpickup/placeorder/orderinfo', methods=['GET','POST'])
def orderinfo(orderNum=None, fullName=None, phone=None):
    if request.method == 'POST':
        if 'username' in session:
            #need to check input for placeUserOrder() from models
            orderNum=User.placeUserOrder(session["username"])
            first = session["userinfo"][0][0]["first"]
            last = session["userinfo"][0][0]["last"]
            phone = session["userinfo"][0][0]["phone"]
            fullName = first + ' ' + last
            return render_template('orderinfo.html', orderNum=orderNum, fullName=fullName, phone=phone)
        else:
            #need to check input for placeorder() from models
            orderNum=User.placeorder(session["userinfo"])
            first = session["userinfo"]["first"]
            last = session["userinfo"]["last"]
            phone = session["userinfo"]["phone"]
            fullName = first + ' ' + last
            return render_template('orderinfo.html', orderNum=orderNum, fullName=fullName, phone=phone)

@app.route('/orderstatus')
def orderstatus(orderinfo=None):
    orderinfo = User.checkOrderStatus()
    return render_template('orderstatus.html', orderinfo=orderinfo)

@app.route('/lookuporder', methods=['GET','POST'])
def lookuporder(orderinfo=None):
    if request.method == 'POST':
        orderinfo = User.lookupOrder(request.form['orderNum'].lower())
        return render_template('lookuporder.html', orderinfo=orderinfo)

@app.route('/pharmacy')
def pharmacydashboard(orderinfo=None):
    orderinfo = Pharmacy.populateOrders()
    return render_template('pharmacy.html', orderinfo=orderinfo)

@app.route('/pharmacy/fillorder', methods=['GET','POST'])
def fillorder(orderinfo=None):
    if request.method == 'POST':
        Pharmacy.completeOrder(request.form['orderNum'].lower())
        orderinfo = Pharmacy.populateOrders()
        return render_template('fillorder.html', orderinfo=orderinfo)

@app.route('/uber')
def uberdashboard(orderinfo=None):
    orderinfo = Uber.populateOrders()
    return render_template('uber.html', orderinfo=orderinfo)

@app.route('/uber/deliver', methods=['GET','POST'])
def deliver(orderinfo=None):
    if request.method == 'POST':
        if request.form['method']=='Start':
            Uber.startOrder(request.form['orderNum'].lower())
            orderinfo = Uber.populateOrders()
            return render_template('deliver.html', orderinfo=orderinfo)
    else:
        if request.args.get('method')=='End':
            Uber.endOrder(request.args.get('orderNum').lower())
            orderinfo = Uber.populateOrders()
            return render_template('deliver.html', orderinfo=orderinfo)

@app.route('/user', methods=['GET','POST'])
def user(orderinfo=None):
    if request.method == 'POST':
        orderinfo = User.populateUserOrders(session["username"])
        return render_template('user.html', orderinfo=orderinfo)
    elif 'username' in session:
        orderinfo = User.populateUserOrders(session["username"])
        return render_template('user.html', orderinfo=orderinfo)
    else:
        orderinfo = User.populateOrders()
        return render_template('user.html', orderinfo=orderinfo)

@app.route('/user/receive', methods=['GET','POST'])
def receive(orderinfo=None):
    if request.method == 'POST':
        if request.form['method']=='Receive':
            User.receiveOrder(request.form['orderNum'].lower(), request.form['phone'])
            orderinfo = User.populateOrders()
            return render_template('receive.html', orderinfo=orderinfo)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 2:
            flash('Your username must be at least one character.')
        elif len(password) < 5:
            flash('Your password must be at least 5 characters.')
        elif User.find(username):
            flash('A user with that username already exists.')
        else:
            session['credentials'] = {"username": username,
                "password": password}
            return redirect(url_for('registration'))
    return render_template('register.html')

@app.route('/register/registration', methods=['GET','POST'])
def registration():
    if request.method == 'POST':
        userinfo = {"username": session["credentials"]["username"],
            "password": session["credentials"]["password"],
            "first": request.form['first'],
            "last": request.form['last'],
            "phone": request.form['phone'],
            "dob": request.form['dob'],
            "address": request.form['address'],
            "pharmacy": request.form['pharmacy']
            }
        User.register(userinfo)
        flash('You are now registered. Please login!')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if len(list(User.verifyPassword(username, password)))!=0:
            session["username"]=username
            return redirect(url_for('user'))
        else:
            flash('Invalid username/password! Pls review and reenter!')
        return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=port)
