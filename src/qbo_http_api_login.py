#!/usr/bin/env python
#
# Software License Agreement (GPLv2 License)
#
# Copyright (c) 2012 Thecorpora, Inc.
#
# This program is free software; you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as 
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, 
# MA 02110-1301, USA.
#
# Authors: Miguel Angel Julian <miguel.a.j@openqbo.com>; 
#          Daniel Cuadrado <daniel.cuadrado@openqbo.com>;

import threading
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

import json

import roslib; roslib.load_manifest('qbo_face_tracking')
#roslib.load_manifest('qbo_listen')
#roslib.load_manifest('qbo_talk')
#roslib.load_manifest('object_recognizer')
roslib.load_manifest('qbo_pymouth')

import rospy
from std_msgs.msg import String

#from qbo_listen.msg import Listened

from lib_qbo_pyarduqbo import qbo_control_client
#from lib_face_traking_py import qbo_face_traking_client
#from lib_qbo_listen_py import qbo_listen_client
from lib_qbo_talk_py import qbo_talk_client
from qbo_pymouth import mouth

#from object_recognizer.srv import *

from time import sleep

from os import environ

from random import *

import string

import time

import signal

import commands

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):

        guestIp = repr(self.request.remote_ip)
        #print ">> "+guestIp
        if guestIp == "'127.0.0.1'":
           #print 'Pass OKK'
           #print ">>>>>>>>>>>>> "+ self.get_argument("username")   
           #self.set_secure_cookie("user", self.get_argument("local"))
           #user_id = self.get_secure_cookie("user")
           user_id='local'
           #print "ok go"
           #self.redirect("/")
           #print "ok go"

        #print 'get_current_user'
        else:
            user_id = self.get_secure_cookie("user")
        #if not user_id: return None
        #print user_id
        return user_id


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        #print 'Main!!'
        name = tornado.escape.xhtml_escape(self.current_user)
        self.write("Hello, " + name)
        self.write("<br><br><a href=\"/auth/logout\">Log out</a>")

passwords={}
passwords['dani1234']='1234'

class AuthHandler(BaseHandler): 
    def get(self):
        print 'get de auth'

        #userid=self.get_current_user()
        #print userid
        #if userid is not None:
        #    self.redirect("/")
        #else:
        #    self.render("login.html")
        self.write('<html><body><form action="/auth/login" method="post">'
                   '<table>'
                   '<tr><td>User name: </td><td><input type="text" name="username" id="username" /></td></tr>'
                   '<tr><td>Password: </td><td><input type="text" name="password" id="password" /></td></tr>'
                   '<tr><td></td><td><input type="submit" value="Submit"/></tr>'
                   '</table>'
                   '</form></body></html>')
    def post(self):
	# We give green light if the requests are comming from localhost
	'''
        guestIp = repr(self.request.remote_ip)
        print ">> "+guestIp
        if guestIp == "'127.0.0.1'":
                print 'Pass OKK'
		print ">>>>>>>>>>>>> "+	self.get_argument("username")	
		
		self.set_secure_cookie("user", self.get_argument("username"))
                print self.get_secure_cookie("user")

		print "ok go"
                self.redirect("/")
		print "ok go"
                return

	'''


        print 'post de auth'
        try:
            username = self.get_argument("username")
            password = self.get_argument("password")
        except:
            print 'Datos no validos'
            self.redirect("/")
            return
	#abrimos el fichero que contiene los nombres de usuario con sus correspondientes pwd
	path = roslib.packages.get_pkg_dir("qbo_http_api_login")
        f = open(path+"/config/users_pwd","r")
	try:
		#miramos cada linea del fichero, buscando que la primera palabra coincida con el nombre
		#y cuando asi sea, que coincida la password.
		for line in f:
			line = line.replace("\n","")
			parts = line.split(" ")
			if parts[0]==username:
				if parts[1] == password:
					print 'Pass OK'
			                self.set_secure_cookie("user", self.get_argument("username")) 
					print self.get_secure_cookie("user")
        	        		self.redirect("/") 
					return
				else:
					print 'Pass FAIL'
		        	        self.redirect("/auth/login")
					return
	
	
	except:			
		print 'Pass FAIL'        		
		self.redirect("/auth/login")
		return

	#si llegamos aqui es que se ha insertado un usuario que no existe
	print 'Pass FAIL'
        self.redirect("/auth/login")
        return






#codigo antiguo
#        if passwords.has_key(username) and passwords[username]==password:
#                print 'Pass OK'
#                self.set_secure_cookie("user", self.get_argument("username")) 
#                self.redirect("/") 
#        else:
#                print 'Pass FAIL'
#                self.redirect("/auth/login")


class LogoutHandler(BaseHandler): 
    def get(self): 
        print 'get de logout'
        self.clear_cookie("user") 
        self.redirect("/")




#va a ser diferente

#URI: /nodo/[status,parametro]/
# /nodos/ devuelve la lista de nodos. Solo get
# /nodo/  devuelve el estado del nodo. Solo get
# /nodo/parametros devuelve la lista de parametros. Solo get
# /nodo/parametro  control del parametro. get para obtenerlo, post para establecerlo

# Comunicacion con representaciones json
class qbo_mouth_web_api():

    def __init__(self):
        self.qbo_mouth_control=mouth()
        self.qbo_mouth_control_params=[]
        self.qbo_mouth_control_get_functions={}
        self.qbo_mouth_control_set_functions={}
        self.qbo_mouth_control_params.append('changeMouth')
        self.qbo_mouth_control_set_functions['changeMouth']=self.qbo_mouth_control.changeMouth


    def get_info(self):
            pass

    def get(self,param):
        print 'Llega un get de mouth'
        if param in self.qbo_mouth_control_get_functions.keys():
            return self.qbo_mouth_control_get_functions[param]()

    def put(self,param,data):
        print 'Llega un post de mouth'
        if param in self.qbo_mouth_control_set_functions.keys():
            return self.qbo_mouth_control_set_functions[param](data['mouth'])

class qbo_talk_web_api():

    def __init__(self):
        self.qbo_talk_control=qbo_talk_client()
        self.qbo_talk_control_params=[]
        self.qbo_talk_control_get_functions={}
        self.qbo_talk_control_set_functions={}
        self.qbo_talk_control_params.append('say')
        self.qbo_talk_control_set_functions['say']=self.qbo_talk_control.say


    def get_info(self):
            pass

    def get(self,param):
        print 'Llega un get de hablar'
        if param in self.qbo_talk_control_get_functions.keys():
            return self.qbo_talk_control_get_functions[param]()

    def put(self,param,data):
        print 'Llega un post de hablar'
        if param in self.qbo_talk_control_set_functions.keys():
            return self.qbo_talk_control_set_functions[param](data)

from syscall import runCmd
class qbo_face_traking_web_api():

    def __init__(self):
#        self.face_traking_control=qbo_face_traking_client()
        self.face_traking_control_params=[]
        self.face_traking_control_get_functions={}
        self.face_traking_control_set_functions={}
#        self.face_traking_control_params.append('face')
#        self.face_traking_control_get_functions['face']=self.face_traking_control.getPosAndSize
        self.face_traking_control_params.append('start')
        self.face_traking_control_set_functions['start']=self.startFaceTraking
        self.face_traking_control_params.append('stop')
        self.face_traking_control_set_functions['stop']=self.stopFaceTraking
        self.started=False

    def startFaceTraking(self,data):
        print 'Face START'
        if not self.started:
            #threading.Thread(target=runCmd,args=('rosrun face_tracking face_tracking',)).start()
            #threading.Thread(target=runCmd,args=('rosrun face_following face_following',)).start()
            #threading.Thread(target=runCmd,args=('roslaunch new_face_recognition face_recognition_android.launch',)).start()
            #threading.Thread(target=runCmd,args=('roslaunch qbo_face_recognition qbo_face_recognition_demo.launch',)).start()
            self.started=True
        #runCmd('echo START')

    def stopFaceTraking(self,data):
        print 'Face STOP'
        #runCmd('echo STOP')
        threading.Thread(target=runCmd,args=('rosnode kill /face_tracking_node',)).start()
        threading.Thread(target=runCmd,args=('rosnode kill /face_following_node',)).start()
        threading.Thread(target=runCmd,args=('rosnode kill /face_recognizer_node',)).start()
        threading.Thread(target=runCmd,args=('rosnode kill /face_recognizer_demo_node',)).start()
        self.started=False

    def get_info(self):
            pass

    def get(self,param):
        if param in self.face_traking_control_get_functions.keys():
            return self.face_traking_control_get_functions[param]()

    def put(self,param,data):
        if param in self.face_traking_control_set_functions.keys():
            return self.face_traking_control_set_functions[param](data)

class qbo_stereo_web_api():

    def __init__(self):
        self.stereo_control_params=[]
        self.stereo_control_get_functions={}
        self.stereo_control_set_functions={}
        self.stereo_control_params.append('start')
        self.stereo_control_set_functions['start']=self.startStereo
        self.stereo_control_params.append('stop')
        self.stereo_control_set_functions['stop']=self.stopStereo
        self.started=False

    def startStereo(self,data):
        print 'Stereo START****************************************************'
        if not self.started:
            threading.Thread(target=runCmd,args=('rosrun stereo_anaglyph red_cyan_anaglyph.py __name:=stereo_anaglyph -c /stereo -d 20 -s',)).start()
            self.started=True
        #runCmd('echo START')

    def stopStereo(self,data):
        print 'Stereo STOP****************************************************'
        #runCmd('echo STOP')
        threading.Thread(target=runCmd,args=('rosnode kill /stereo_anaglyph',)).start()
        #threading.Thread(target=runCmd,args=('rosnode kill /face_following_node',)).start()
        self.started=False

    def get_info(self):
            pass

    def get(self,param):
        if param in self.stereo_control_get_functions.keys():
            return self.stereo_control_get_functions[param]()

    def put(self,param,data):
        if param in self.stereo_control_set_functions.keys():
            return self.stereo_control_set_functions[param](data)
'''
class qbo_listen_web_api():

    def __init__(self):
        self.qbo_listen_control=qbo_listen_client()
        self.qbo_listen_control_params=[]
        self.qbo_listen_control_get_functions={}
        self.qbo_listen_control_set_functions={}
        self.qbo_listen_control_params.append('sentence')
        self.qbo_listen_control_get_functions['sentence']=self.qbo_listen_control.getSentence

    def get_info(self):
        pass

    def get(self,param):
        if param in self.qbo_listen_control_get_functions.keys():
            return self.qbo_listen_control_get_functions[param]()

    def put(self,param,data):
        if param in self.qbo_listen_control_set_functions.keys():
            return self.qbo_listen_control_set_functions[param](data)

'''
import urllib
import urllib2_file
import urllib2
import sys, json
import os
import tarfile
class qbo_test_api():

    def __init__(self):
        #self.qbo_listen_control=qbo_listen_client()
        self.qbo_test_control_params=[]
        self.qbo_test_control_get_functions={}
        self.qbo_test_control_set_functions={}
        self.qbo_test_control_params.append('image')
        self.qbo_test_control_get_functions['image']=self.funcionTest
        self.qbo_test_control_set_functions['image']=self.funcionTest

    def send_image(self,object_name,image_path):
        data = {'image_file' : open(image_path,'rb'),
               #'data' : 'algo',
               'data':json.dumps({'new_image':True}),
           }
    
        req = urllib2.Request('http://localhost:8800/object/'+object_name+'/', data, {})
        u = urllib2.urlopen(req)
        #print u.read()
        return u.read()
    
    def retrain_server(self,):
        data = {'data':json.dumps({'update':True})}
        req = urllib2.Request('http://localhost:8800/object/train/', data, {})
        u = urllib2.urlopen(req)
        #print u.read()
        return u.read()
    
    
    def send_files_to_server(self,path):
        #hay que recorrer la estructura de ficheros
        path=path.rstrip('/')
        files_list=os.listdir(path)
        for object_name in files_list:
            object_path=path+'/'+object_name
            if os.path.isdir(object_path):
                images_list=os.listdir(object_path)
                total_response=True
                for image in images_list:
                    response_data = self.send_image(object_name,object_path+'/'+image)
                    try:
                        response = json.loads(response_data)
                        if response:
                            #borro imagenes
                            os.remove(object_path+'/'+image)
                        else:
                            total_response=False
                    except Exception, e:
                        print e
                        print 'algo malo'
                    print object_name, ' ', image, ' ', response_data
                    #print object_name, ' ', image, ' ', send_image(object_name,object_path+'/'+image)
                    #print send_image(object_name,object_path+'/'+image)
                if total_response:
                    os.removedirs(object_path)


    def funcionTest(self,data=""):
        #print 'Empiezo el test'
        if data=="":
            #retData={}
            #retData['metodo']='metodo get llamado'
            print 'Se va a reconocer el objeto'
            #llamo al servicio que se pondra a capturar imagenes
            try:
                recognizeObject = rospy.ServiceProxy('/object_recognizer/recognize_with_stabilizer', RecognizeObject)
                resp1 = recognizeObject()
                if resp1.recognized:
                    result = resp1.object_name
                else:
                    result = ''
            except rospy.ServiceException, e:
                print "Service call failed: %s"%e
                #result = False
                resutl = ''
            except Exception, e:
                print 'Otro fallo: ', e
                resutl = ''
            print 'creo objeto para devolver'
            retData={}
            retData['object']=result
            print 'Acabo el test'
            return retData
            #return retData
        #if data.has_key("imageData"):
        #    sleep(5.0)
        #    retData={}
        #    retData['longitud']=len(data['imageData'])
        #    return retData
        if data.has_key('wordToLearn'):
            #object_name='test'
            object_name=data['wordToLearn']
            print 'Se va a entrenae el objeto: ', object_name
            #llamo al servicio que se pondra a capturar imagenes
            try:
                learnNewObject = rospy.ServiceProxy('/object_recognizer/learn', LearnNewObject)
                resp1 = learnNewObject(str(object_name))
                result = resp1.learned
            except rospy.ServiceException, e:
                print "Service call failed: %s"%e
                result = False
            except Exception, e:
                print 'Otro fallo: ', e
            ##envio imagenes al servidor
            #full_param_name = rospy.search_param('new_object_images_path')
            #path = rospy.get_param('/object_recognizer/new_object_images_path', '/opt/qbo_learn/objects_to_send')
            #print 'path de nuevas imagenes: ', path
            #self.send_files_to_server(path)
            ##y envio orden de aprender al servidor
            #self.retrain_server()
            ##pido nuevo archivo de reconocimientos al servidor
            #urllib.urlretrieve ("http://localhost:8800/static/training.tar.gz", "training.tar.gz")
            ##descomprimo archivo de reconocimientos nuevo
            #tar = tarfile.open("training.tar.gz")
            #tar.extractall(path='/')
            #tar.close() 
            ##llamo a servicio para recargar la red de reconocimiento
            #try:
                #updateService = rospy.ServiceProxy('/object_recognizer/update', Update)
                #resp1 = updateService()
                #result = resp1.updated
            #except rospy.ServiceException, e:
                #print "Service call failed: %s"%e
                #result = False
            retData={}
            retData['status']=result
            print 'Acabo el test'
            return retData
        else:
            #print 'Acabo el test'
            return False

    def get_info(self):
        pass

    def get(self,param):
        if param in self.qbo_test_control_get_functions.keys():
            return self.qbo_test_control_get_functions[param]()

    def put(self,param,data):
        if param in self.qbo_test_control_set_functions.keys():
            return self.qbo_test_control_set_functions[param](data)
        else:
            return False

import subprocess
class qbo_webcams_test_web_api():
    def __init__(self):
        self.qbo_webcams_test_params=[]
        self.qbo_webcams_test_get_functions={}
        self.qbo_webcams_test_set_functions={}
        self.qbo_webcams_test_params.append('check')
        self.qbo_webcams_test_get_functions['check']=self.testCams

    def testCams(self):
        testCamsDict={}
        testCamsDict['leftCamera']=False
        testCamsDict['rightCamera']=False
        cmd = "rosnode list"
        process = subprocess.Popen(cmd.split(),stdout=subprocess.PIPE)
        for line in process.stdout:
            elements=line.strip().split('/')
            if('uvc_camera_stereo' in elements):
                testCamsDict['leftCamera']=True
                testCamsDict['rightCamera']=True
        return testCamsDict

    def get_node_list(self):
        print 'obtener lista de nodos'

    def get_node_status(self, node):
        print 'obtener estado nodos. nodo: ', node

    def get_node_params(self, node, params):
        print 'obtener parametros del nodo. nodo: ', node
        print 'parametros: ', params
        if node=='qbo_webcams_test':
            ret_params={}
            for param in params:
                if param in self.qbo_arduqbo_params:
                  pass

    def set_node_params(self, node, params):
        print 'establecer parametros del nodo. .keys()nodo: ', node
        print 'parametros: ', params

    def get_info(self):
        pass

    def get(self,param):
        if param in self.qbo_webcams_test_get_functions.keys():
            return self.qbo_webcams_test_get_functions[param]()

    def put(self,param,data):
        #print 'Llego al nodo. Param: ',param,' Data: ',data
        if param in self.qbo_webcams_test_set_functions.keys():
            #print 'Mando comando a ',param,'. Datos: ',data
            return self.qbo_webcams_test_set_functions[param](data)


class qbo_arduqbo_web_api():

    def __init__(self):
        self.qbo_control=qbo_control_client()

        self.qbo_arduqbo_params=[]
        self.qbo_arduqbo_get_functions={}
        self.qbo_arduqbo_set_functions={}
        #self.qbo_arduqbo_params.append('linearSpeed')
        #self.qbo_arduqbo_get_functions['linearSpeed']=self.qbo_control
        #self.qbo_arduqbo_set_functions['linearSpeed']=self.qbo_control
        #self.qbo_arduqbo_params.append('angularSpeed')
        #self.qbo_arduqbo_get_functions['angularSpeed']=self.qbo_control
        #self.qbo_arduqbo_set_functions['angularSpeed']=self.qbo_control
        self.qbo_arduqbo_params.append('speed')
        self.qbo_arduqbo_get_functions['speed']=self.qbo_control.speedGet
        self.qbo_arduqbo_set_functions['speed']=self.qbo_control.speedPut
        self.qbo_arduqbo_params.append('position')
        self.qbo_arduqbo_get_functions['position']=self.qbo_control.positionGet
        #self.qbo_arduqbo_params.append('robotPosX')
        #self.qbo_arduqbo_get_functions['robotPosX']=self.qbo_control
        #self.qbo_arduqbo_params.append('robotPosY')
        #self.qbo_arduqbo_get_functions['robotPosY']=self.qbo_control
        #self.qbo_arduqbo_params.append('robotPosTheta')
        #self.qbo_arduqbo_get_functions['robotPosTheta']=self.qbo_control
        #self.qbo_arduqbo_params.append('LCDstatus')
        #self.qbo_arduqbo_get_functions['LCDstatus']=self.qbo_control
        #self.qbo_arduqbo_params.append('LCDtext')
        #self.qbo_arduqbo_set_functions['LCDtext']=self.qbo_control
        self.qbo_arduqbo_params.append('LCD')
        #self.qbo_arduqbo_get_functions['LCD']=self.qbo_control
        self.qbo_arduqbo_set_functions['LCD']=self.qbo_control.LCDPut

        #self.qbo_arduqbo_params.append('SRFs')
        #self.qbo_arduqbo_get_functions['SRFs']=self.qbo_control.

        #self.qbo_arduqbo_params.append('SRF0')
        #self.qbo_arduqbo_get_functions['SRF']=self.qbo_control
        #self.qbo_arduqbo_params.append('SRF1')
        #self.qbo_arduqbo_get_functions['SRF1']=self.qbo_control
        #self.qbo_arduqbo_params.append('SRF2')
        #self.qbo_arduqbo_get_functions['SRF2']=self.qbo_control
        #self.qbo_arduqbo_params.append('SRF3')
        #self.qbo_arduqbo_get_functions['SRF3']=self.qbo_control
        #self.qbo_arduqbo_params.append('motorLeftState')
        #self.qbo_arduqbo_get_functions['motorLeftState']=self.qbo_control
        #self.qbo_arduqbo_set_functions['motorLeftState']=self.qbo_control
        #self.qbo_arduqbo_params.append('motorRightState')
        #self.qbo_arduqbo_get_functions['motorRightState']=self.qbo_control
        #self.qbo_arduqbo_set_functions['motorRightState']=self.qbo_control
        #self.qbo_arduqbo_params.append('motors')
        #self.qbo_arduqbo_get_functions['motors']=self.qbo_control
        #self.qbo_arduqbo_set_functions['motors']=self.qbo_control
        self.qbo_arduqbo_params.append('headServos')
        self.qbo_arduqbo_get_functions['headServos']=self.qbo_control.headServosGet
        self.qbo_arduqbo_set_functions['headServos']=self.qbo_control.headServosPut
        self.qbo_arduqbo_params.append('eyesServos')
        self.qbo_arduqbo_get_functions['eyesServos']=self.qbo_control.eyelidServosGet
        self.qbo_arduqbo_set_functions['eyesServos']=self.qbo_control.eyelidServosPut
        #self.qbo_arduqbo_params.append('panServoState')
        #self.qbo_arduqbo_get_functions['panServoState']=self.qbo_control
        #self.qbo_arduqbo_set_functions['panServoState']=self.qbo_control
        #self.qbo_arduqbo_params.append('tiltServoState')
        #self.qbo_arduqbo_get_functions['tiltServoState']=self.qbo_control
        #self.qbo_arduqbo_set_functions['tiltServoState']=self.qbo_control
        #self.qbo_arduqbo_params.append('panServoPosition')
        #self.qbo_arduqbo_get_functions['panServoPosition']=self.qbo_control
        #self.qbo_arduqbo_set_functions['panServoPosition']=self.qbo_control
        #self.qbo_arduqbo_params.append('tiltServoPosition')
        #self.qbo_arduqbo_get_functions['tiltServoPosition']=self.qbo_control
        #self.qbo_arduqbo_set_functions['tiltServoPosition']=self.qbo_control
        #self.qbo_arduqbo_params.append('leftEyelidServoPosition')
        #self.qbo_arduqbo_get_functions['leftEyelidServoPosition']=self.qbo_control
        #self.qbo_arduqbo_set_functions['leftEyelidServoPosition']=self.qbo_control
        #self.qbo_arduqbo_params.append('rightEyelidServoPosition')
        #self.qbo_arduqbo_get_functions['rightEyelidServoPosition']=self.qbo_control
        #self.qbo_arduqbo_set_functions['rightEyelidServoPosition']=self.qbo_control
        #self.qbo_arduqbo_params.append('panServoSpeed')
        #self.qbo_arduqbo_get_functions['panServoSpeed']=self.qbo_control
        #self.qbo_arduqbo_set_functions['panServoSpeed']=self.qbo_control
        #self.qbo_arduqbo_params.append('tiltServoSpeed')
        #self.qbo_arduqbo_get_functions['tiltServoSpeed']=self.qbo_control
        #self.qbo_arduqbo_set_functions['tiltServoSpeed']=self.qbo_control
        #self.qbo_arduqbo_params.append('leftEyelidServoSpeed')
        #self.qbo_arduqbo_get_functions['leftEyelidServoSpeed']=self.qbo_control
        #self.qbo_arduqbo_set_functions['leftEyelidServoSpeed']=self.qbo_control
        #self.qbo_arduqbo_params.append('rightEyelidServoSpeed')
        #self.qbo_arduqbo_get_functions['rightEyelidServoSpeed']=self.qbo_control
        #self.qbo_arduqbo_set_functions['rightEyelidServoSpeed']=self.qbo_control
        self.qbo_arduqbo_params.append('MICs')
        self.qbo_arduqbo_get_functions['MICs']=self.qbo_control.MICsGet
        self.qbo_arduqbo_set_functions['MICs']=self.qbo_control.MICsPut
        #self.qbo_arduqbo_params.append('MIC0')
        #self.qbo_arduqbo_get_functions['MIC0']=self.qbo_control
        #self.qbo_arduqbo_params.append('MIC1')
        #self.qbo_arduqbo_get_functions['MIC1']=self.qbo_control
        #self.qbo_arduqbo_params.append('MIC2')
        #self.qbo_arduqbo_get_functions['MIC2']=self.qbo_control
        #self.qbo_arduqbo_params.append('micsMute')
        #self.qbo_arduqbo_set_functions['micsMute']=self.qbo_control
        self.qbo_arduqbo_params.append('battery')
        self.qbo_arduqbo_get_functions['battery']=self.qbo_control.batteryGet
        #self.qbo_arduqbo_params.append('batLevel')
        #self.qbo_arduqbo_get_functions['batLevel']=self.qbo_control

        self.qbo_arduqbo_params.append('test')
        self.qbo_arduqbo_get_functions['test']=self.qbo_control.testBoards
        #self.qbo_arduqbo_params.append('mouth')
        #self.qbo_arduqbo_set_functions['mouth']=self.qbo_control



        #self.qbo_talk_params=[]
        #self.qbo_talk_get_functions={}
        #self.qbo_talk_set_functions={}
        #self.qbo_talk_params.append('sentence')
        #self.qbo_talk_set_functions['sentence']=self.qbo_control
        #self.qbo_talk_params.append('voice')
        #self.qbo_talk_set_functions['voice']=self.qbo_control

        #self.qbo_listen_params=[]
        #self.qbo_listen_get_functions={}
        #self.qbo_listen_set_functions={}
        #self.qbo_listen_params.append('sentence')
        #self.qbo_listen_get_functions['sentence']=self.qbo_control

        #self.qbo_cameras_params=[]
        #self.qbo_cameras_set_functions={}
        #self.qbo_cameras_get_functions={}
        #self.qbo_cameras_params.append('leftCameraStatus')
        #self.qbo_cameras_params.append('rightCameraStatus')
        #self.qbo_cameras_params.append('leftCameraCalibrationStatus')
        #self.qbo_cameras_params.append('rightCameraCalibrationStatus')
        #self.qbo_cameras_params.append('leftCameraWidth')
        #self.qbo_cameras_params.append('rightCameraWidth')
        #self.qbo_cameras_params.append('leftCameraHeight')
        #self.qbo_cameras_params.append('rightCameraHeight')
        #self.qbo_cameras_params.append('restart')

        #self.qbo_android_control_params=[]
        #self.qbo_android_control_set_functions={}
        #self.qbo_android_control_get_functions={}

        #self.qbo_face_traking_params=[]
        #self.qbo_face_traking_set_functions={}
        #self.qbo_face_traking_get_functions={}
        #self.qbo_face_traking_params.append('faceDistance')
        #self.qbo_face_traking_params.append('faceSizeX')
        #self.qbo_face_traking_params.append('faceSizeY')
        #self.qbo_face_traking_params.append('faceCenterX')
        #self.qbo_face_traking_params.append('faceCenterY')
        ##self.qbo_face_traking_params.append('faceSpeedX')
        ##self.qbo_face_traking_params.append('faceSpeedY')

        #self.qbo_face_recognition_params=[]
        #self.qbo_face_recognition_set_functions={}
        #self.qbo_face_recognition_get_functions={}
        #self.qbo_face_recognition_params.append('detectedPerson')

    def get_node_list(self):
        print 'obtener lista de nodos'

    def get_node_status(self, node):
        print 'obtener estado nodos. nodo: ', node

    def get_node_params(self, node, params):
        print 'obtener parametros del nodo. nodo: ', node
        print 'parametros: ', params
        if node=='qbo_arduqbo':
            ret_params={}
            for param in params:
                if param in self.qbo_arduqbo_params:
                  pass
                    

    def set_node_params(self, node, params):
        print 'establecer parametros del nodo. .keys()nodo: ', node
        print 'parametros: ', params

    def get_info(self):
        pass

    def get(self,param):
        if param in self.qbo_arduqbo_get_functions.keys():
            return self.qbo_arduqbo_get_functions[param]()

    def put(self,param,data):
        #print 'Llego al nodo. Param: ',param,' Data: ',data
        if param in self.qbo_arduqbo_set_functions.keys():
            #print 'Mando comando a ',param,'. Datos: ',data
            return self.qbo_arduqbo_set_functions[param](data)


#controlador=Controlador()

lista_nodos={}
#lista_nodos['webcams_check']=qbo_webcams_test_web_api()
#lista_nodos['qbo_arduqbo']=qbo_arduqbo_web_api()
#lista_nodos['face_traking']=qbo_face_traking_web_api()
#lista_nodos['stereo_anaglyph']=qbo_stereo_web_api()
##lista_nodos['qbo_listen']=qbo_listen_web_api()
#lista_nodos['qbo_talk']=qbo_talk_web_api()
#lista_nodos['test']=qbo_test_api()
#lista_nodos['mouth']=qbo_mouth_web_api()

class QboNodeHandler(BaseHandler):
    #def options(self,node,param):
        #self.set_header('Access-Control-Allow-Origin', '*')
        #self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        #self.set_header('Access-Control-Max-Age', 1000)
        #self.set_header('Access-Control-Allow-Headers', '*')
        #self.set_status(200)
        #headers = self.request.headers
        #if headers.has_key('Access-Control-Request-Method'):
            #method = headers['Access-Control-Request-Method']
            #if method=='GET':
                #self.get(node,param)
            #if method=='POST':
                #self.post(node,param)
        ##print self.get_header('Access-Control-Request-Method')

    @tornado.web.authenticated
    def get(self,node,param): #node y param son strings
        #print "llega un get"
        return_value=''
        if node in lista_nodos.keys():
            return_value=return_value+json.dumps(lista_nodos[node].get(param))
            #self.write(json.dumps(lista_nodos[node].get(param)))
        else:
            return_value=return_value+json.dumps(False)
            #self.write(json.dumps(False))
            #return
        jsoncallback=self.get_argument("jsoncallback", None) #Funcion a ejecutar en el cliente
        if jsoncallback:
            return_value=jsoncallback+'('+return_value+')'
        self.write(return_value)
        return

    @tornado.web.authenticated
    def post(self,node,param):
        #print "llega un post"
        #print 'nodo: ',node,' parametro: ',param,' argumentos: ', self.request.arguments
        return_value=''

        if node in lista_nodos.keys():
            #print "llega un post"
            data=json.loads(self.get_argument("data", None)) #Pasar a objeto desde json
            #print 'data type: ', type(data)
            if not data:
                return_value=return_value+json.dumps(False)
                #print 'No hay datos 1'
                #self.write(json.dumps(False))
                #return
            else:
                #print data
                return_value=return_value+json.dumps(lista_nodos[node].put(param,data))
                #self.write(json.dumps(lista_nodos[node].put(param,data)))
        else:

            return_value=return_value+json.dumps(False)
            #print 'No hay datos 2'
            #self.write(json.dumps(False))
            #return
        jsoncallback=self.get_argument("jsoncallback", None) #Funcion a ejecutar en el cliente
        if jsoncallback:
            return_value=jsoncallback+'('+return_value+')'

        print return_value
        self.write(return_value)
        return

class QboHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,node):
        if node=="nodes":
            lista=[]
            #devolvemos lista de nodos
        else:
            if node not in lista_nodos.keys(): #hay que crear ese objeto
                self.write(json.dumps(False)) #Se retorna codigo de error
                return
            self.write(lista_nodos[node].get_info()) #Ecode en json Diccionario con keys status y params. params es una lista con los parametros del nodo. cada parametro es un diccionario con keys operations(que puede valer input,output,all) y type(que sera el tipo de ros)


class StateMachine(BaseHandler):

    @tornado.web.authenticated
    def post(self):
	print "---------------"
 	try:
            node = self.get_argument("node")
    	    on_off = self.get_argument("on_off")
        except:
            print 'Datos no validos'
            self.redirect("/")
            return

	pub = rospy.Publisher("/listen/en_default",Listened)
	
	msg = Listened()
	msg.msg=""
	msg.not_msg = ""
	msg.total_score = 1.0
	msg.min_score = 1.0
	msg.all_score = ""


	node = node.lower()
	print "en CONCRETO "+node


	if("off" in on_off):
		 msg.msg="THAT'S ALL FOR NOW Q B O"
	elif(node=="follow me"):
		print "que pasaaaasaa"
		msg.msg="CAN YOU FOLLOW ME"
	elif(node=="music player"):
		print "a"
                msg.msg="RUN MUSIC PLAYER"

	elif(node=="run phone services"):
                print "b"
                msg.msg="RUN PHONE SERVICES"

	elif(node=="random move"):
                print "c"
                msg.msg="WHY DON'T YOU TAKE A WALK"

	elif(node=="face recognition"):
                print "d"
                msg.msg="Q B O TAKE A LOOK AT ME"

	elif(node=="object recognition"):
                print "e"
                msg.msg="LETS SEE SOME OBJECTS"

	elif(node=="ask the robot ip"):
                print "f"
                msg.msg="TELL ME YOUR IP"

	elif(node=="face tracking"):
                print "g"
                msg.msg="WHY DON'T YOU LOOK A ROUND"

	elif(node=="read mail"):
                print "h"
                msg.msg="Q B O CHECK MY E MAIL"


	if(msg.msg != ""):
		print "publicamos "+str(msg.msg)
		pub.publish(msg);	


class qbo_sip_functions():

    def __init__(self):
        self.sip_control_params=[]
        self.sip_control_get_functions={}
        self.sip_control_set_functions={}
        self.sip_control_params.append('setIpSip')
        self.sip_control_set_functions['setIpSip']=self.setIpSip
        self.sip_control_params.append('getUserSipId')
        self.sip_control_get_functions['getUserSipId']=self.getUserSipId
        self.sip_control_params.append('getBotSipId')
        self.sip_control_get_functions['getBotSipId']=self.getBotSipId
        self.sip_control_params.append('endCall')
        self.sip_control_get_functions['endCall']=self.endCall
        self.sip_control_params.append('startSIPServer')
        self.sip_control_set_functions['startSIPServer']=self.startSIPServer
        self.sip_control_params.append('stopSIPServer')
        self.sip_control_get_functions['stopSIPServer']=self.stopSIPServer

        self.linphoneRunning = False
        self.auth = "notDefined"
        self.authBot = "notDefined"
        self.envi = ""

        self.processSipd = ""
        self.processSiprtmp = ""
        self.processLinphone = ""
        self.processAudioControl = ""

        self.ecoCancelationId = "notDefined"

    def startSIPServer(self,data):
        print "Start sip server"
        path2webi = roslib.packages.get_pkg_dir("qbo_webi")

        chars = string.ascii_letters + string.digits

        self.envi = environ.copy()
        path = self.envi["PYTHONPATH"]
        self.envi["PYTHONPATH"] = "/opt/ros/electric/stacks/qbo_stack/qbo_webi/src/teleoperation/sip2rtmp/p2p-sip:/opt/ros/electric/stacks/qbo_stack/qbo_webi/src/teleoperation/sip2rtmp/p2p-sip/src:/opt/ros/electric/stacks/qbo_stack/qbo_webi/src/teleoperation/sip2rtmp/p2p-sip/src/app:/opt/ros/electric/stacks/qbo_stack/qbo_webi/src/teleoperation/sip2rtmp/p2p-sip/src/external:/opt/ros/electric/stacks/qbo_stack/qbo_webi/src/teleoperation/sip2rtmp/rtmplite:"+path


        self.auth = "notDefined"
        self.authBot = "notDefined"

        self.auth = "".join(choice(chars) for x in range(randint(4, 4)))
        self.authBot = "".join(choice(chars) for x in range(randint(4, 4)))


        #we check if sipd is already active, if so, we close it        
        cmd = "ps -aux | grep sipd"
        out = runCmd(cmd)
        out = out[0]

        if "sipd.py" in out:
            pid = out.split(" ")[2]
            print ">>>>>>>>>>>>>>>>>>>>>>>>"+pid+" <<<<<<<<<<<<<<<<<<<<<<<< "
            os.kill(int(pid), signal.SIGTERM)


        # the same with siprtmp
        cmd = "ps -aux | grep siprtmp"
        out = runCmd(cmd)
        out = out[0]

        if "siprtmp.py" in out:
            pid = out.split(" ")[2]
            print ">>>>>>>>>>>>>>>>>>>>>>>>"+pid+" <<<<<<<<<<<<<<<<<<<<<<<< "
            os.kill(int(pid), signal.SIGTERM)        


        #launch audio control with sip profile
        cmd = "roslaunch qbo_audio_control audio_control_sip.launch"
        self.processAudioControl = subprocess.Popen(cmd.split(),env=self.envi)

        #launch sipd.py
        cmd = "python "+path2webi+"/src/teleoperation/sip2rtmp/p2p-sip/src/app/sipd.py -u "+self.auth+" -b "+self.authBot
        print "Usuario= "+ self.auth +"     BOT= "+self.authBot
        self.processSipd = subprocess.Popen(cmd.split(),env=self.envi)

        #launch siprtmp.py
        cmd = "python "+path2webi+"/src/teleoperation/sip2rtmp/rtmplite/siprtmp.py"
        self.processSiprtmp = subprocess.Popen(cmd.split(),env=self.envi)

        #we give them sometime to finish the job
        time.sleep(0.5)

        #data ready for the node qbo_linphone, but we still need to know the host
        rospy.set_param("linphone_botName",self.authBot)
        rospy.set_param("linphone_host","waiting for the mobile to know the IP")

        #ECO cancelation on
        if data['ecoCancelation']:
            cmd = "pactl load-module module-echo-cancel"
            out = runCmd(cmd);
            self.ecoCancelationId = out[0].replace("\n","")
            print "ECO cancelation ON "+str(self.ecoCancelationId)

        print "FIn de inicio de sip"

    def stopSIPServer(self):
        try:
            self.processSiprtmp.send_signal(signal.SIGINT)
        except Exception as e:
            print "ERROR when killing a siprtmp. "+str(e)

        try:
            self.processLinphone.send_signal(signal.SIGINT)
        except Exception as e:
            print "ERROR when killing a linphone. "+str(e)

        try:
            self.processSipd.send_signal(signal.SIGINT)
        except Exception as e:
            print "ERROR when killing a sipd. "+str(e)



	#We go back to the default audio control
        cmd = "roslaunch qbo_audio_control audio_control_listener.launch"
        try:
            subprocess.Popen(cmd.split(),env=self.envi)
        except:
            print "ERROR when launching audio_control_listener.launch"+str(e)            

        #ECO cancelation off
        if self.ecoCancelationId != "notDefined":
            print "ECO Cancelation off "+str(self.ecoCancelationId)
            cmd = "pactl unload-module "+self.ecoCancelationId
            out = runCmd(cmd)
            print "salida "+str(out)
            print "Done"

    def setIpSip(self,data):

        if self.linphoneRunning:
            try:
                self.processLinphone.send_signal(signal.SIGINT)
                self.linphoneRunning = False
            except Exception as e:
                print "ERROR when killing a proccess. "+str(e) 

            #we give them sometime to finish the job
            sleep(1)
	

        rospy.set_param("linphone_host",data['ip'])

        #now we know the IP, we can launch the linphone in the robot
        cmd = "roslaunch qbo_linphone launch_on_robot.launch"
        self.processLinphone = subprocess.Popen(cmd.split(),env=self.envi)

        rospy.wait_for_service('autocaller')

        self.linphoneRunning = True

    def getUserSipId(self):
        return self.auth

    def getBotSipId(self):
        return self.authBot

    def endCall(self):
	cmd = "linphonecsh hangup"
        subprocess.Popen(cmd.split(),env=self.envi)
        print "END CALL"

    def get_info(self):
        pass

    def get(self,param):
        if param in self.sip_control_get_functions.keys():
            return self.sip_control_get_functions[param]()
           
    def put(self,param,data):
        if param in self.sip_control_set_functions.keys():
            return self.sip_control_set_functions[param](data)

settings = {
    'auto_reload': True,
    'cookie_secret': '32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
    'login_url': '/auth/login',
}

application = tornado.web.Application([
    (r'/control/([0-9a-zA-Z_]+)/([0-9a-zA-Z_]+)', QboNodeHandler),
    (r'/control/([0-9a-zA-Z_]+)/', QboHandler),
    (r'/', MainHandler),
    (r'/auth/login', AuthHandler),
    (r'/auth/logout', LogoutHandler),
    (r'/stateMachine', StateMachine),	
], **settings)

def myspin():


    #rospy.init_node('qbo_http_control')
    print 'empiezo el spin'


    rospy.spin()
    print 'acabo el spin'
    if tornado.ioloop.IOLoop.instance().running():
        tornado.ioloop.IOLoop.instance().stop()

    lista_nodos['sip'].stopSIPServer()
    
    exit()

if __name__ == "__main__":
        global lista_nodos
    #try:
        rospy.init_node('qbo_http_control')
        lista_nodos['webcams_check']=qbo_webcams_test_web_api()
        lista_nodos['qbo_arduqbo']=qbo_arduqbo_web_api()
        lista_nodos['face_traking']=qbo_face_traking_web_api()
        lista_nodos['stereo_anaglyph']=qbo_stereo_web_api()
        #lista_nodos['qbo_listen']=qbo_listen_web_api()
        lista_nodos['qbo_talk']=qbo_talk_web_api()
        lista_nodos['test']=qbo_test_api()
        lista_nodos['mouth']=qbo_mouth_web_api()
	lista_nodos['sip'] = qbo_sip_functions()
        rospy.sleep(1)
        threading.Thread(target=myspin).start()
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8880)
        tornado.ioloop.IOLoop.instance().start()
        print 'salgo del main'
    #except Exception, e:
        #print 'Excepcion: ', e
        #exit()





















def runCmd(self,cmd, timeout=None):
    '''
    Will execute a command, read the output and return it back.
   
    @param cmd: command to execute
    @param timeout: process timeout in seconds
    @return: a tuple of three: first stdout, then stderr, then exit code
    @raise OSError: on missing command or if a timeout was reached
    '''

    ph_out = None # process output
    ph_err = None # stderr
    ph_ret = None # return code

    p = subprocess.Popen(cmd, shell=True,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     env=self.env)
    # if timeout is not set wait for process to complete
    if not timeout:
        ph_ret = p.wait()
    else:
        fin_time = time.time() + timeout
        while p.poll() == None and fin_time > time.time():
            time.sleep(1)

        # if timeout reached, raise an exception
        if fin_time < time.time():

            # starting 2.6 subprocess has a kill() method which is preferable
            # p.kill()
            os.kill(p.pid, signal.SIGKILL)
            raise OSError("Process timeout has been reached")

        ph_ret = p.returncode


    ph_out, ph_err = p.communicate()

    return (ph_out, ph_err, ph_ret)



