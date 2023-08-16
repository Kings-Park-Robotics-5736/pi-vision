from flask import Flask
from flask import request, abort, send_from_directory
#import numpy as np
#import cv2 as cv
import json
import os, time
import traceback
from threading import Thread, Semaphore
import logging

app = Flask(__name__,static_folder='./build/', static_url_path='/')


configFile = "./config.json"

imageFile="./build/Picture1.jpg"



mutex=Semaphore(1)

currentConfig= ""

defaultCurrentConfig="""{"groups": [{"fields": [{"id": "team-color", "items": ["Red", "Blue"], "title": "Team Color", "type": "LIST", "value": "Red"}], "title": "Team Color"}, {"fields": [{"id": "HRedLower1", "max": 180, "min": 0, "step": 1, "title": "H", "type": "NUMBER", "value": "101"}, {"id": "SRedLower1", "max": 255, "min": 0, "step": 1, "title": "S", "type": "NUMBER", "value": "75"}, {"id": "VRedLower1", "max": 255, "min": 0, "step": 1, "title": "V", "type": "NUMBER", "value": "100"}], "title": "HSV Red Control Lower 1"}, {"fields": [{"id": "HRedUpper1", "max": 180, "min": 0, "step": 1, "title": "H", "type": "NUMBER", "value": 100}, {"id": "SRedUpper1", "max": 255, "min": 0, "step": 1, "title": "S", "type": "NUMBER", "value": 75}, {"id": "VRedUpper1", "max": 255, "min": 0, "step": 1, "title": "V", "type": "NUMBER", "value": 60}], "title": "HSV Red Control Upper 1"}, {"fields": [{"id": "HRedLower2", "max": 180, "min": 0, "step": 1, "title": "H", "type": "NUMBER", "value": "101"}, {"id": "SRedLower2", "max": 255, "min": 0, "step": 1, "title": "S", "type": "NUMBER", "value": "75"}, {"id": "VRedLower2", "max": 255, "min": 0, "step": 1, "title": "V", "type": "NUMBER", "value": 60}], "title": "HSV Red Control Lower 2"}, {"fields": [{"id": "HRedUpper2", "max": 180, "min": 0, "step": 1, "title": "H", "type": "NUMBER", "value": "58"}, {"id": "SRedUpper2", "max": 255, "min": 0, "step": 1, "title": "S", "type": "NUMBER", "value": "198"}, {"id": "VRedUpper2", "max": 255, "min": 0, "step": 1, "title": "V", "type": "NUMBER", "value": 60}], "title": "HSV Red Control Upper 2"}, {"fields": [{"id": "HBlueLower1", "max": 180, "min": 0, "step": 1, "title": "H", "type": "NUMBER", "value": "50"}, {"id": "SBlueLower1", "max": 255, "min": 0, "step": 1, "title": "S", "type": "NUMBER", "value": 75}, {"id": "VBlueLower1", "max": 255, "min": 0, "step": 1, "title": "V", "type": "NUMBER", "value": 60}], "title": "HSV Blue Control Lower 1"}, {"fields": [{"id": "HBlueUpper1", "max": 180, "min": 0, "step": 1, "title": "H", "type": "NUMBER", "value": 100}, {"id": "SBlueUpper1", "max": 255, "min": 0, "step": 1, "title": "S", "type": "NUMBER", "value": 75}, {"id": "VBlueUpper1", "max": 255, "min": 0, "step": 1, "title": "V", "type": "NUMBER", "value": 60}], "title": "HSV Blue Control Upper 1"}]}"""


attributeCache={}
@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/get-config' , methods = ['GET'])
def getConfig():
    return json.dumps(currentConfig)

@app.route('/api/get-image-path' , methods = ['GET'])
def getImagePath():
    return "./Picture1.jpg"

@app.route('/api/set-config' , methods = ['POST'])
def setConfig():
    global currentConfig
    global attributeCache
    mutex.acquire()

    currentConfig=request.json
    attributeCache.clear()
    mutex.release()
    writeConfig()
    return """{'status':'ok'}""", 201

@app.route('/<path:path>')
def anyFile(path):
    if path != "" and os.path.exists(app.static_folder + "/" + path):
        return send_from_directory(app.static_folder, path)
    return ''

def getAttribute(attribute, vartype='NUM'):
    global attributeCache
    mutex.acquire()
    if attribute in attributeCache:
        #print(attribute,attributeCache[attribute])
        mutex.release()
        return attributeCache[attribute]


    data = currentConfig
    mutex.release()
    for  value in data['groups']:
        for  value1 in value['fields']:
            if attribute==value1['id']:
                if value1['value']:
                    if vartype=='NUM':
                        attributeCache[attribute]=float(value1['value'])
                        return float(value1['value'])
                    else:
                        attributeCache[attribute]=value1['value']
                        return value1['value']
                else:
                    return 0
    return -1

pic_index = 1
pic_max_index = 10
def getImageFile():
    global pic_index, pic_max_index
    fileName = f"Picture{pic_index}.jpg"
    pic_index += 1
    if pic_index >= pic_max_index:
        pic_index = 1
    return fileName
def writeConfig():
    try:
        f = open( configFile, "w")
        json.dump(currentConfig,f)
        f.close()
    except Exception as e:
            tb = traceback.format_exc()
            print("Critical Error", str(e) + "\n" + str(tb), flush=True)

def readConfig():

    global currentConfig
    try:
        if not os.path.exists(configFile):
            print("Cannot find file to read from")
            currentConfig=json.loads(defaultCurrentConfig)
            return
        f=open( configFile, 'r')
        currentConfig = json.load(f)
        f.close()
    except Exception as e:
           pass


def startServer():
    print("Starting Server")
    readConfig()
    log = logging.getLogger('werkzeug')
    log.disabled = True
    t = Thread(target=startApp)
    t.daemon = True
    t.start()

def startApp():
    app.run(host='0.0.0.0',port=5000,  debug=True, use_reloader=False)
