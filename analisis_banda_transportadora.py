# Importamos las librerías necesarias
import numpy as np
import cv2
import time
import RPi.GPIO as GPIO
from tblib import Frame
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#Imports webserver
import argparse
import os
import io

import tornado.ioloop
import tornado.web
import tornado.websocket

from PIL import Image

from datetime import datetime

#para red neuronal
import matplotlib.pyplot as plt

from PIL import Image

#Generar argumentos por defecto

parser = argparse.ArgumentParser(description='Start the PyImageStream server.')

parser.add_argument('--port', default=8888, type=int, help='Web server port (default: 8888)')
parser.add_argument('--camera', default=0, type=int, help='Camera index, first camera is 0 (default: 0)')
parser.add_argument('--width', default=640, type=int, help='Width (default: 640)')
parser.add_argument('--height', default=480, type=int, help='Height (default: 480)')
parser.add_argument('--quality', default=60, type=int, help='JPEG Quality 1 (worst) to 100 (best) (default: 70)')
parser.add_argument('--stopdelay', default=7, type=int, help='Delay in seconds before the camera will be stopped after '
                                                             'all clients have disconnected (default: 7)')
args = parser.parse_args()

class Camera:

    def __init__(self, index, width, height, quality, stopdelay):
        print("Initializing camera...")
        # Cargamos el vídeo
        camara = cv2.VideoCapture(0)
        #bajamos el tamaño de la captura
        #ret = camara.set(3,1920)#160
        #ret = camara.set(4,1080)#120
        ret = camara.set(3,480)#160 #version 9 800
        ret = camara.set(4,320)#120 #version 9 600
        ret = camara.set(5,60)#120

        self._cam = camara
        # Inicializamos el primer frame a vacío.
        # Nos servirá para obtener el fondo
        self.fondo = None
        #contador para tomar un nuevo fondo
        self.contador = 0
        self.contador_elementos = 0
        self.habilitar_cuenta = True
        a = datetime.now()
        a = int(a.strftime('%H%M%S'))
        self.ultimo_archivo = a

        print("Camera initialized")
        self.is_started = False
        self.stop_requested = False
        self.quality = quality
        self.stopdelay = stopdelay

    def request_start(self):
        if self.stop_requested:
            print("Camera continues to be in use")
            self.stop_requested = False
        if not self.is_started:
            self._start()

    def request_stop(self):
        if self.is_started and not self.stop_requested:
            self.stop_requested = True
            print("Stopping camera in " + str(self.stopdelay) + " seconds...")
            tornado.ioloop.IOLoop.current().call_later(self.stopdelay, self._stop)

    def _start(self):
        print("Starting camera...")
        #self._cam.start()
        print("Camera started")
        self.is_started = True

    def _stop(self):
        if self.stop_requested:
            print("Stopping camera now...")
            #self._cam.stop()
            print("Camera stopped")
            self.is_started = False
            self.stop_requested = False

    def get_jpeg_image_bytes(self):
        enMovimiento = False
        conElementos = False
        msg = "-"
        msg2 = "-"

        # Obtenemos el frame
        (grabbed, frame) = self._cam.read()
     
        # Si hemos llegado al final del vídeo salimos
        if not grabbed:
            print ('not grabbed')
            return
        
        #frame = frame[160:520,290:550]
        frame = frame[30:400,200:400]
        # Convertimos a escala de grises
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
     
        # Aplicamos suavizado para eliminar ruido
        #gris = cv2.GaussianBlur(gris, (5, 5), 0)

        gris_para_mov = gris[0:30,0:200]
        gris_cuerpo = gris[40:400,0:200]
        #frame_cuerpo = frame[40:340,0:200]

        # Si todavía no hemos obtenido el fondo, lo obtenemos
        # Será el primer frame que obtengamos
        if self.fondo is None:
            self.fondo = gris_para_mov
        resta = cv2.absdiff(self.fondo, gris_para_mov)
        self.fondo = gris_para_mov
        maximo1 = np.max(resta)
        if maximo1 < 50:
            #print("X")
            msg = "Detenido"
            enMovimiento = False
        else:
            #print(".")
            msg = "Movimiento"
            enMovimiento = True


        maximo_cuerpo = np.max(gris_cuerpo)
         
        if  maximo_cuerpo > 150:
            print(maximo_cuerpo)
            # Aplicamos suavizado para eliminar ruido
            #gris_cuerpo_gb = cv2.GaussianBlur(gris_cuerpo, (5, 5), 0)
            #aplicacion de umbral en la imagen
            umbral = cv2.threshold(gris_cuerpo, 25, 255, cv2.THRESH_OTSU)[1]
            # Dilatamos el umbral para tapar agujeros
            #umbral_d = cv2.dilate(umbral, None, iterations=2)
            # Copiamos el umbral para detectar los contornos
            #contornosimg = umbral_d.copy() 
            # Buscamos contorno en la imagen
            #contornos, hierarchy = cv2.findContours(contornosimg,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            contornos, hierarchy = cv2.findContours(umbral,cv2.RETR_TREE,cv2.CHAIN_APPROX_TC89_L1)
            #contornos, hierarchy = cv2.findContours(contornosimg,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
            print(len(contornos))
            #cv2.drawContours(frame_cuerpo, contornos, -1, (0,255,0), 3)

            for c in contornos:
                if len(c) > 30:
                    print(len(c))
                    area = cv2.contourArea(c)
                    if area > 2500 and area < 6000:
                        #cv2.polylines(frame, c, True, (0,255,0),3)
                        #print("x ")
                        #if self.habilitar_cuenta: 
                        #print(area)
                        #    self.habilitar_cuenta = False
                        self.contador_elementos = self.contador_elementos + 1
                            #print(self.contador_elementos)
        else:
            self.habilitar_cuenta = True
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        color = (255, 255, 255)
        thickness = 2
        org = (10, 20)
        frame = cv2.putText(frame, msg, org, font, fontScale, color, thickness, cv2.LINE_AA)
        org = (20, 60)
        frame = cv2.putText(frame, f'N= {self.contador_elementos}', org, font, fontScale, color, thickness, cv2.LINE_AA)
        imgRGB=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        pimg = Image.fromarray(imgRGB)
        with io.BytesIO() as bytesIO:
            pimg.save(bytesIO, "JPEG", quality=self.quality, optimize=True)
            return bytesIO.getvalue()

camera = Camera(args.camera, args.width, args.height, args.quality, args.stopdelay)


class ImageWebSocket(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):
        # Allow access from every origin
        return True

    def open(self):
        ImageWebSocket.clients.add(self)
        print("WebSocket opened from: " + self.request.remote_ip)
        camera.request_start()

    def on_message(self, message):
        jpeg_bytes = camera.get_jpeg_image_bytes()
        self.write_message(jpeg_bytes, binary=True)

    def on_close(self):
        ImageWebSocket.clients.remove(self)
        print("WebSocket closed from: " + self.request.remote_ip)
        if len(ImageWebSocket.clients) == 0:
            camera.request_stop()

class RestHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(self.request.url)


script_path = os.path.dirname(os.path.realpath(__file__))
static_path = script_path + '/static/'

app = tornado.web.Application([
        (r"/websocket", ImageWebSocket),
        (r"/(.*)", tornado.web.StaticFileHandler, {'path': static_path, 'default_filename': 'index.html'}),
    ])
app.listen(args.port, address='0.0.0.0')

print("Starting server: http://localhost:" + str(args.port) + "/")

tornado.ioloop.IOLoop.current().start()






# Recorremos todos los frames