# -*- coding: utf-8 -*-
import os
import pymongo
import hashlib
import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from flask_pymongo import PyMongo

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["MONGO_URI"] = "mongodb://192.168.3.123:27017/Log"
connection = pymongo.MongoClient("mongodb://192.168.3.123:27017/")
database = connection["Log"]

collection = database["Data"]
sensor_collection = database["Sensors"]
mongo = PyMongo(app)

@app.route("/")
def index():
    if 'username' in session:
        locations = []
        sensors = mongo.db.Sensors.find({'username': session['username']})
        current_date = datetime.now().strftime('%d/%m/%Y')
        for sensor in sensors:
            locations.append(sensor['sensor_location'])
        return render_template('show.html', username=session['username'], locations_list=locations, current_date=current_date,result='Chọn ngày và vị trí cảm biến để xem thông tin.')
    return redirect(url_for('login'))

@app.route('/view', methods=['GET', 'POST'])
def view():
    if request.method == 'POST' and 'username' in session:
        sensor_location = ''
        sensor_temp = []
        sensor_hum = []
        sensor_time = []
        locations = []
        warnings = []
        threshold = []

        sensors = mongo.db.Sensors.find({'username': session['username']})
        for sensor in sensors:
            locations.append(sensor['sensor_location'])
            # threshold.append({"sensor_location": sensor['sensor_location'], "temp_max": sensor['temp_max'], "temp_min": sensor['temp_min'], "hum_max": sensor['hum_max'], "hum_min": sensor['hum_min']})
        
        for info in sensor_collection.find({'username': session['username']}):
            threshold.append({"sensor_location": info['sensor_location'], "temp_max": info['temp_max'], "temp_min": info['temp_min'], "hum_max": info['hum_max'], "hum_min": info['hum_min']})

        # print(threshold)
        date = request.form.get('datepicker')
        location = request.form.get('location')

        if date == '':
            date = datetime.now().strftime("%d/%m/%Y")

        for hour in range(0, 24):
            if hour < 10:
                regex = "^0" + str(hour) + ":"
            else:
                regex = "^" + str(hour) + ":"
            sum_temp = 0
            sum_humi = 0
            sum_col = collection.find({"date": date, "location": location, "time": {"$regex": regex}}).count()

            for i in collection.find({"date": date, "location": location, "time": {"$regex": regex}}):
                if i['temperature'] != 0 and i['humidity'] != 0:
                    try:
                        sum_temp += i['temperature']
                        sum_humi += i['humidity']
                    except TypeError:
                        sum_temp += 0
                        sum_humi += 0
                else:
                    sum_temp += 0
                    sum_humi += 0

            text_hour = int(hour)
            if sum_col != 0:
                sensor_temp.append(round(float(sum_temp/sum_col), 2))
                sensor_hum.append(round(float(sum_humi/sum_col), 2))
                sensor_time.append(text_hour)
            else:
                if hour < int(datetime.now().strftime("%H")):
                    sensor_hum.append(0)
                    sensor_temp.append(0)
                    sensor_time.append(text_hour)
                else:
                    sensor_temp.append(text_hour)
            
        results = []

        for info in threshold:
            if location == info['sensor_location']:
                max_temp = mongo.db.Data.find({"username": session['username'], "date": date, "location": location, "temperature": {"$gte": float(info['temp_max'])}})
                # for i in max_temp:
                #     print(i)
                # print(info['temp_max'])
                min_temp = mongo.db.Data.find({"username": session['username'], "date": date, "location": location, "temperature": {"$lte": float(info['temp_min'])}})
                max_hum = mongo.db.Data.find({"username": session['username'], "date": date, "location": location, "humidity": {"$gte": float(info['hum_max'])}})
                min_hum = mongo.db.Data.find({"username": session['username'], "date": date, "location": location, "humidity": {"$lte": float(info['hum_min'])}})

                for _max in max_temp:
                    results.append({'location': _max['location'], 'date': _max['date'], 'time': _max['time'], 'temperature': _max['temperature'], 'humidity': _max['humidity'], 'result': 'Nóng hơn ngưỡng.'})
                for _min in min_temp:
                    results.append({'location': _min['location'], 'date': _min['date'], 'time': _min['time'], 'temperature': _min['temperature'], 'humidity': _min['humidity'], 'result': 'Lạnh hơn ngưỡng.'})
                for _max in max_hum:
                    results.append({'location': _max['location'], 'date': _max['date'], 'time': _max['time'], 'temperature': _max['temperature'], 'humidity': _max['humidity'], 'result': 'Ẩm hơn ngưỡng.'})
                for _min in min_hum:
                    results.append({'location': _min['location'], 'date': _min['date'], 'time': _min['time'], 'temperature': _min['temperature'], 'humidity': _min['humidity'], 'result': 'Khô hơn ngưỡng.'})
                
        # print(results)
        return render_template('show.html', username=session['username'], temperature = sensor_temp, humidity = sensor_hum, time = sensor_time, locations_list=locations, date=date, location=location, results=results, current_date=date)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    users = mongo.db.Users
    login_user = users.find_one({'username': request.form.get('username')})
    passw = str(request.form.get('password'))
    pass_hash = hashlib.sha256(passw.encode())

    if login_user:
        if pass_hash.hexdigest() == login_user['password']:
            session['username'] = request.form.get('username')
            return redirect(url_for('index'))
    return render_template('index.html')
    # return render_template("login.html", message=message)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'username' in session:
        session.pop('username')
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        existing_user = mongo.db.Users.find_one({'username': request.form.get('username')})
        if existing_user is None:
            passw = str(request.form.get('password'))
            pass_hash = hashlib.sha256(passw.encode())
            mongo.db.Users.insert({"username": request.form.get('username'), "password": pass_hash.hexdigest(), "phone": request.form.get('phone'), "address": request.form.get('address')})
            session['username'] = request.form.get('username')
            return redirect(url_for('index'))
        return 'Người dùng đã tồn tại!'
    return render_template('register.html')


@app.route('/sensors', methods=['GET', 'POST'])
def sensors():
    if 'username' in session:
        sensors = mongo.db.Sensors
        existing_sensors = sensors.find({'username': session['username']})

        return render_template('sensors.html', username=session['username'], sensors=existing_sensors)
    return redirect(url_for('login'))

@app.route('/add_sensor', methods=['GET', 'POST'])
def add_sensor():
    if request.method == 'POST':
        if 'username' in session:
            username = ''
            for i in mongo.db.Users.find({'username': session['username']}):
                username = i['username']

            # print(username)
            sensors = mongo.db.Sensors
            existing_sensors = sensors.find({'username': username})

            sensor_ip_list = []
            sensor_location = request.form.get('sensor_location')
            sensor_ip = 'http://' + str(request.form.get('sensor_ip'))
            temp_max = request.form.get('temp_max')
            temp_min = request.form.get('temp_min')
            hum_max = request.form.get('hum_max')
            hum_min = request.form.get('hum_min')
            # sensors.insert({"username": username, "sensor_location": sensor_location, "sensor_ip": sensor_ip})
            
            if temp_max == '':
                temp_max = 100
            if temp_min == '':
                temp_min = 0
            if hum_max == '':
                hum_max = 100
            if hum_min == '':
                hum_min = 0
            
            for sensor in existing_sensors:
                sensor_ip_list.append(sensor['sensor_ip'])
            
            if sensor_ip in sensor_ip_list:
                sensors.update_one({"sensor_ip": sensor_ip}, {"$set": {"sensor_location": sensor_location, "temp_max": temp_max, "temp_min": temp_min, "hum_max": hum_max, "hum_min": hum_min}})
            else:
                sensors.insert_one({"username": username, "sensor_location": sensor_location, "sensor_ip": sensor_ip, "temp_max": temp_max, "temp_min": temp_min, "hum_max": hum_max, "hum_min": hum_min})

            return redirect(url_for('sensors'))
        return redirect(url_for('login'))
    return render_template("sensors.html")


@app.route('/delete_sensor', methods=['GET', 'POST'])
def delete_sensor():
    if request.method == 'POST' and 'username' in session:
        sensor_ip = request.form.get('delete_bin')
        sensor = mongo.db.Sensors.find({'username': session['username'], 'sensor_ip': sensor_ip})
        sensor_location = ''
        for i in sensor:
            sensor_location = i['sensor_location']
        
        # print(sensor_location)
        mongo.db.Sensors.remove({'username': session['username'], 'sensor_ip': sensor_ip})

        mongo.db.Data.remove({'username': session['username'], 'location': sensor_location})

        return redirect(url_for('sensors'))
    return redirect(url_for('login'))


@app.route('/user', methods=['GET', 'POST'])
def user():
    if 'username' in session:
        users = mongo.db.Users.find({'username': session['username']})

        return render_template('user.html', users=users)
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST' and 'username' in session:
        old_password = str(request.form.get('old_password'))
        old_password_hash = hashlib.sha256(old_password.encode())
        new_password = str(request.form.get('new_password'))
        new_password_hash = hashlib.sha256(new_password.encode())

        users = mongo.db.Users.find({'username': session['username']})
        for user in users:
            if old_password_hash.hexdigest() == user['password']:
                mongo.db.Users.update_one({'username': session['username']}, {'$set': {'password': new_password_hash.hexdigest()}})
                return redirect(url_for('login'))
        return render_template('user.html', users=users)
    return redirect(url_for('login'))

@app.route('/forgot')
def forgot():
    return render_template('forgot.html')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)