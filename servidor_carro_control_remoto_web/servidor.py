from flask import Flask, render_template
import datetime
import time
import threading
import RPi.GPIO as GPIO
app = Flask(__name__)

GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.OUT) ## derecha
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP) ## direccion centrada
GPIO.setup(26, GPIO.OUT) ## izquierda
GPIO.setup(16, GPIO.OUT) ## adelante
GPIO.setup(12, GPIO.OUT) ## atras

cuenta_seguir = 0
direccion = 0

class ThreadAdelante ( threading.Thread ):
   def run ( self ):
      try:
           print ("ir adelante")
           global cuenta_seguir
           cuenta_seguir = 0
           while cuenta_seguir < 10:
              print (cuenta_seguir)
              GPIO.output(16, False) ## apagado el GPIO
	      GPIO.output(12, True) ## Enciendo el GPIO
              time.sleep(0.2) ## Esperamos 1 segundo
              ##GPIO.output(16, False) ## apagado el GPIO
              ##time.sleep(0.1) ## Esperamos 1 segundo
              cuenta_seguir = cuenta_seguir + 1
           print ("finalizada ir adelante")
           GPIO.output(12, False) ## apagado el GPIO
      except:
           GPIO.output(12, False) ## apagado el GPIO
           print ("Error en adelante()")

@app.route("/")
def hello():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   templateData = {
      'title' : 'HELLO!',
      'time': timeString
      }
   return render_template('index.html', **templateData)

@app.route("/izquierda")
def izquierda():
   try:
        print ("ir a la izquierda")
        global direccion
        direccion = 1
        GPIO.output(26, True) ## Enciendo el GPIO
        time.sleep(0.04) ## Esperamos 1 segundo
        GPIO.output(26, False) ## apagado el GPIO
        print ("finalizada ir a la izquierda")
   except:
      print ("Error en izquierda()")
   return "OK"

@app.route("/derecha")
def derecha():
   try:
        print ("ir a la derecha")
        global direccion
        direccion = 2
        GPIO.output(19, True) ## Enciendo el GPIO
        time.sleep(0.04) ## Esperamos 1 segundo
        GPIO.output(19, False) ## apagado el GPIO
        print ("finalizada ir a la derecha")
   except:
      print ("Error en derecha()")
   return "OK"

@app.route("/centrar")
def centrar():
   try:
        print ("regresar al centro")
        global direccion
        iteracion = 0
        while iteracion < 10: ## Segundos que durara la funcion
                if GPIO.input(13):
                        iteracion = 20
                        print ("Alto")
                else:
                        print ("bajo")
                        if direccion == 1:
                           GPIO.output(19, True) ## Enciendo el 21
                           time.sleep(0.02) ## Esperamos 1 segundo
                           GPIO.output(19, False) ## Enciendo el 21
                        if direccion == 2:
                           GPIO.output(26, True) ## Enciendo el 21
                           time.sleep(0.02) ## Esperamos 1 segundo
                           GPIO.output(26, False) ## Enciendo el 21
                time.sleep(0.2) ## Esperamos 1 segundo
                iteracion = iteracion + 1
        direccion = 0
        print ("finalizada ir a la derecha")
   except:
      print ("Error en derecha()")
   return "OK"

@app.route("/detener")
def detener():
   try:
        print ("ir detener")
        global cuenta_seguir
        print (cuenta_seguir)
        cuenta_seguir = 30
        GPIO.output(12, False) ## apagado el GPIO
        GPIO.output(16, False) ## apagado el GPIO
        print ("finalizada ir detener")
   except:
        print ("Error en detener()")
   return "OK"

@app.route("/adelante")
def adelante():
   ThreadAdelante().start()
   return "OK"

@app.route("/atras")
def atras():
   try:
        print ("ir atras")
        GPIO.output(12, False) ## apagado el GPIO
        GPIO.output(16, True) ## Enciendo el GPIO
        time.sleep(1) ## Esperamos 1 segundo
        GPIO.output(16, False) ## apagado el GPIO time.sleep(0.2) ## Esperamos 1 segundo
        print ("finalizada ir atras")
   except:
      print ("Error en atras()")
      GPIO.output(16, False) ## apagado el GPIO
   return "OK"


if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)
