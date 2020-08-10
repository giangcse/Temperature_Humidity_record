# -*- coding: utf-8 -*-
import requests
import json
import time
import pymongo
from bs4 import BeautifulSoup
from datetime import datetime, date

def send(sensor_ip, sensor_location, mongodb_ip, users):
    connection = pymongo.MongoClient(mongodb_ip) # Ket noi toi mongodb server
    database = connection['Log'] # Database chua collection
    collection = database['Data'] # Collection chua du lieu duoc ghi

    while(True):  
        for user in users:  
            for i in range(len(sensor_ip)):
                try:
                    res = requests.get(sensor_ip[i])
                    html_page = res.content
                    soup = BeautifulSoup(html_page, 'html.parser')
                    json_data = json.loads(str(soup)) # Du lieu tra ve duoc chuyen ve dang json cho de su dung
                    # print(json_data)
                    time_str = datetime.now().strftime("%H:%M:%S")
                    day = str(date.today().strftime('%d/%m/%Y'))
                    print(day, ' ', time_str, ' - ', sensor_location[i], '\tTemperature: ', json_data['variables']['temperature'], '\tHumidity: ', json_data['variables']['humidity'])
                    dataDict = {"username": user, "location": sensor_location[i], "date": day, "time": time_str, "temperature": json_data['variables']['temperature'], "humidity": json_data['variables']['humidity']}
                    collection.insert_one(dataDict)
                except requests.ConnectionError:
                    collection.insert_one({"username": user, "location": sensor_location[i], "date": day, "time": time_str, "temperature": None, "humidity": None})
        time.sleep(60)

if __name__ == "__main__":
    
    mongo_ip = 'mongodb://192.168.3.123:27017/'
    connection = pymongo.MongoClient(mongo_ip)
    database = connection['Log']
    sensors = database['Sensors']
    _users = database['Users']

    users = []
    sensor_ip = []
    sensor_location = []

    for user in _users.find():
        users.append(user['username'])
        for sensor in sensors.find({'username': user['username']}):
            sensor_ip.append(sensor['sensor_ip'])
            sensor_location.append(sensor['sensor_location'])

    send(sensor_ip, sensor_location, mongo_ip, users)