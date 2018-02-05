import time
import requests
import telebot 
from telebot import types
import os.path as path 
import os
import sqlite3 #Library for database creation 

from biblioteca import Biblioteca
from ishodan import Info_Shodan

#os.system("clear")

def guardar_usuario_BBDD(token,busqueda,idtg):
	conexion = sqlite3.connect('users.db') # We connect to the database users.db (create it if it does not exist)
	cursor = conexion.cursor() # Now we will create a user table to store "id", "message" and "ip token"
	cursor.execute("INSERT INTO users VALUES (null,'{}', '{}', '{}')".format(idtg,busqueda,token))
	conexion.commit() # We save the changes by committing
	conexion.close() # We closed the connections

def eliminar_usuario_BBDD(idtg):
	conexion = sqlite3.connect('users.db')
	cursor = conexion.cursor()
	sql = "DELETE FROM users WHERE idtg='{}'".format(idtg)
	print("sql borrar: ",sql)
	r = cursor.execute(sql)
	print("r:",r)
	conexion.commit()
	conexion.close()

def obtener_usuario_BBDD(idtg):
	conexion = sqlite3.connect('users.db')
	cursor = conexion.cursor()

	sql = "SELECT * FROM users WHERE idtg='{}'".format(idtg)
	#print("sql: ",sql)
	cursor.execute(sql) # We retrieve a record of the user table
	usuario = cursor.fetchone()
	if(usuario == None):
		#print("There is no record of this user")
		conexion.close()
		return False
	else:
		#print("A history of this user has been found:",usuario)
		conexion.close()
		return usuario

def generar_array_key_token_BBDD(token):

	ips = token.split(",") # using a comma to delimit the array
	#print("ips: ", ips)
	token_array = []
	for ip in ips:
		ip_split = ip.split("=") #parto el array por el igual
		diccionario = {'cont':ip_split[0],'ip':ip_split[1]} #creo un diccionario
		token_array.append(diccionario) #creo un array de diccionarios

	#print("Token_array: ",token_array)

	return token_array #Devolvemos un array

def crear_teclado_tl(num):
	markup = types.ReplyKeyboardMarkup(row_width=5)

	mi_array = []
	for i in range(1,num+1):
		mi_array.append(types.KeyboardButton(i)) #creación de botones numericos

	markup.add(*mi_array)

	itembtncancelar = types.KeyboardButton('cancelar')
	markup.row(itembtncancelar) #creación de botón cancelar
	return markup

def obtener_numero_teclado(message):
	if(int(message.text) >=1 and int(message.text) <=20):
		usuario = obtener_usuario_BBDD(message.from_user.id)
		token = usuario[3]
		array_token = generar_array_key_token_BBDD(token)

		indice = int(message.text)-1
		valor = array_token[indice]['ip']
		print("value:",valor)
		return str(valor)

	else:
		return "Sorry, has to be a number from 1 to 20"

TOKEN = open('telegram-key.txt').readline().rstrip('\n') # Ponemos nuestro Token generado con el @BotFather
bot = telebot.TeleBot(TOKEN) # Combinamos la declaración del Token con la función de la API
i = Info_Shodan() #Inicializo la Clase Info_Shodan()

##Comprobamos si existe la BBDD, sino creamos la BBDD##
if path.isfile("users.db") != True:
	print("Creating a database of users")

	conexion = sqlite3.connect('users.db') # Nos conectamos a la base de datos users.db (la crea si no existe)
	cursor = conexion.cursor() # Ahora crearemos una tabla de users para almacenar "id", "mensaje" y "token de ip"
	cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,idtg VARCHAR(100),mensaje VARCHAR(100), tokenip VARCHAR(250))")
	conexion.commit() # Guardamos los cambios haciendo un commit

	#cursor.execute("INSERT INTO users VALUES (null,'188396571', 'apache 5', '1=192.168.1.211,2=192.168.1.209')")

	conexion.commit() # Guardamos los cambios haciendo un commit
	conexion.close() # Cerramos la conexións


@bot.message_handler(func=lambda message: True)
def echo_all(message):

	chat_id = message.from_user.id #ID único de Telegram

	if(obtener_usuario_BBDD(chat_id)!=False):
		print("The user '{}' was found in the database.".format(chat_id))

		if(message.text.isdigit()):
			ip = obtener_numero_teclado(message)
			if(ip!=False):
				print("Here's the info Shodan sent back",ip)
				print()
				cadena = i.host(ip)
				print("dad")
				bot.send_message(chat_id,cadena,parse_mode="HTML")

				posicion=i.localizacion()
				if(posicion!=False):
					print("Position:",posicion)
					lat_log = posicion.split(";") #parto el array por el igual
					lat=float(lat_log[0])
					log=float(lat_log[1])

					bot.send_location(chat_id, lat, log)
			else:
				print("Couldn't find anything.")
				markup = types.ReplyKeyboardRemove(selective=False)
				bot.send_message(chat_id, "CANCELAR", reply_markup=markup)
		else:
			print("Delete the table of the database.")
			eliminar_usuario_BBDD(chat_id) #Eliminamos el usuario de la BBDD
			markup = types.ReplyKeyboardRemove(selective=False)
			bot.send_message(chat_id, "CANCELAR", reply_markup=markup)


	else:
		print("The user '{}' is not in the database".format(chat_id));

		if(message.text.find("shodan")!=-1):
			bi = Biblioteca() #Libreria con funciones propias.
			diccionario = bi.argumentos_validos(message.text)
			if type(diccionario) is not dict:
				cadena="<b>Error: </b>"+diccionario+"\n\n<b>Usage:</b>\n\n"
				cadena+="<b>SHODAN: </b>Shodan is a search engine that allows the user to find the same or different specific types of equipment (routers, servers, etc.) connected to the Internet through a variety of filters.\n"
				cadena+="\n<b>Usage examples:</b>\n\n<code>shodan 'search' 'number of searches'</code>\n\n<code>shodan apache</code>\n<code>shodan apache 5</code>\n"
				cadena+="<code>shodan apache 20</code>.\n\nNota: <b>20</b> is the maximum number of searches"
				bot.send_message(chat_id,cadena,parse_mode="HTML")
			else:
				print("It is a dictionary")

				res=""
				if('n' in diccionario):
					res = i.buscar(diccionario["busqueda"],diccionario["n"])
				else:
					res = i.buscar(diccionario["busqueda"])

				resultados = i.nlimit

				if(res==True):
					array_tl = i.datos_telegram()
					#print("token ip: ",i.obtener_token_array_ip())
					guardar_usuario_BBDD(i.obtener_token_array_ip(),message.text,chat_id)
					print("Saving user({})in the Database".format(chat_id))

					markup = crear_teclado_tl(resultados) #creamos el teclado del telegram

					for datos_tl in array_tl:
						bot.send_message(chat_id,datos_tl,parse_mode="HTML")

					#print("Diccionario_IP:",i.diccionario_ip)
					#diccionario_shodan = i.diccionario_ip
					bot.send_message(chat_id,"<b>Choose an option (1/"+str(resultados)+"): </b>",parse_mode="HTML",reply_markup=markup)

				elif(res==False):
						bot.send_message(chat_id,"No results are available for that search: <b>"+str(diccionario["busqueda"]+"</b>"),parse_mode="HTML")
				else:
					bot.send_message(chat_id,res,parse_mode="HTML")

		elif message.text == "/author":
			texto = "<b>Author:</b> Rubén Gonz. Juan\n"
			texto+= "<b>Github:</b> https://github.com/rubenleon"
			bot.send_message(chat_id, texto,parse_mode="HTML")

		elif message.text == "cancel":
			markup = types.ReplyKeyboardRemove(selective=False)
			bot.send_message(chat_id, "CANCEL", reply_markup=markup)


	#print(message)
	id_tele = str(message.from_user.id)
	nombre = str(message.from_user.first_name)
	apellido = str(message.from_user.last_name)
	mensaje = str(message.text)

	print("")
	print("ID: "+id_tele) #User ID
	print("First Name: "+nombre) #First Name of User
	print("First Name: "+apellido) #Last Name of User
	print("Message: "+mensaje) #Message
	print("")

def inicializar_bot():
	try:
		bot.polling(True,False,True)
	except requests.exceptions.ReadTimeout:
		print("Timeout occurred")
		time.sleep(2)
		print("Two second pause")
		inicializar_bot()
	except requests.exceptions.ConnectionError:
		print("Connection Error")
		time.sleep(2)
		print("Two second pause")
		inicializar_bot()
		#print(except)

inicializar_bot()
