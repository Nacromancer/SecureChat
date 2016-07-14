from SocketServer import TCPServer, BaseRequestHandler, ThreadingMixIn
import sys
from Crypto.PublicKey import RSA
import time
import sqlite3
import socket

def create_db_file():
	try:
		conn = sqlite3.connect(database_path)
		c = conn.cursor()

		conn.execute('''CREATE TABLE IF NOT EXISTS USERS
		       (ID INTEGER PRIMARY KEY,
		       USERNAME           TEXT    NOT NULL,
		       PASSWORD            INT     NOT NULL);''')

		conn.close()
		return 1
	except:
		print 'Database file creation FAILED'
		return 0

def find_database_entry(username):
    try:
        conn = sqlite3.connect(database_path)
        c = conn.cursor()

        t = (username,)
        c.execute('SELECT * FROM USERS WHERE USERNAME=?', t)
        try:
            return c.fetchone()
        except:
            return 'None'
        conn.close()

    except Exception as e:
        print e

def add_database_entry(username,password):
    try:
        conn = sqlite3.connect(database_path)
        c = conn.cursor()

        t = (username,)
        c.execute('SELECT * FROM USERS WHERE USERNAME=?', t)
        if str(c.fetchone()) == 'None':
            print 'Creating new entry..'
            c.execute("INSERT INTO USERS(USERNAME,PASSWORD) VALUES (?, ?)",(username,password));
            conn.commit()
        else:
            print 'Modifying existing entry..'
            t1 = (password,username,)
            c.execute('UPDATE USERS SET PASSWORD=? WHERE USERNAME=?', t1)
            conn.commit()

        conn.close()
        print 'Entry handled successfully!'
    except Exception as e:
        print e

def find_all_users_in_db():
    try:
        conn = sqlite3.connect(database_path)
        c = conn.cursor()
        users = []
        c.execute('SELECT * FROM USERS')
        entries = c.fetchall()
        for item in entries:
            users.append(str(item[1]))
        conn.close()
        return users

    except Exception as e:
        print e

class chatHandler(BaseRequestHandler):
	"""
	The request handler class for our server.

	It is instantiated once per connection to the server, and must
	override the handle() method to implement communication to the
	client.
	"""

	timeout = 2

	def handle(self):
		self.request.settimeout(self.timeout)
		self.data = str(self.request.recv(1024))
		if self.data == 'HANDSHAKE protocol initiated':
			self.do_HANDSHAKE()
		else:
			print 'BAD REQUEST'
			self.request.send('The request was inappropriate.. That\'s all we know!')
			return 0


	def do_HANDSHAKE(self):
		print 'Handshaking with client..'
		c = self.request
		public_key = ''
		try:
			print('Fetching the client public key...')
			while True:     
			    data = c.recv(4096)
			    public_key = public_key + str(data)
			    if '-----END PUBLIC KEY-----' in str(data):
			        break
			print 'Public key fetched SUCCESSFULLY'
		except:
		    print 'Something went wrong...'
		    return 0

		print 'Sharing the public key with the client...'
		try:
		    f = open(self.public_key_path,'rb')
		    l = f.read(4096)
		    while l:
		       c.send(l)
		       l = f.read(4096)
		    f.close()
		    print 'Server key shared SUCCESSFULLY'
		except:
		    print 'Something went wrong...'
		    return 0

		public_key = RSA.importKey(public_key)
		self.client_key = public_key
		check = str(self.new_key.decrypt(c.recv(4096)))
		if check == 'LOGIN protocol initiated':
			self.do_LOGIN()
		elif check == 'REGISTRATION protocol initiated':
			self.do_REGISTRATION()
		elif check == 'PASS_CH protocol initiated':
			self.do_PASS_CH()
		else:
			print 'BAD REQUEST'
			self.request.send('The request was inappropriate.. That\'s all we know!')
		return 1

	def do_PASS_CH(self):
		c = self.request
		name = self.new_key.decrypt(c.recv(4096))
		welcome_string = 'Hello %s, you are now successfully connected to the server..'%name
		welcome_string_enc = self.client_key.encrypt(welcome_string,32)[0]
		c.send(welcome_string_enc)
		old_password = self.new_key.decrypt(c.recv(4096))
		new_password = self.new_key.decrypt(c.recv(4096))
		password_db = str(find_database_entry(name)[2])
		if password_db == 'None':
			string_enc = self.client_key.encrypt('noName', 32)[0]
			c.send(string_enc)
		elif password_db == old_password:
			add_database_entry(name,new_password)
			string_enc = self.client_key.encrypt('done', 32)[0]
			c.send(string_enc)
		else:
			string_enc = self.client_key.encrypt('oldPassWrong', 32)[0]
			c.send(string_enc)
		return 1

	def do_REGISTRATION(self):
		c = self.request
		name = self.new_key.decrypt(c.recv(4096))
		welcome_string = 'Hello %s, you are now successfully connected to the server..'%name
		welcome_string_enc = self.client_key.encrypt(welcome_string,32)[0]
		c.send(welcome_string_enc)
		password = self.new_key.decrypt(c.recv(4096))
		if str(find_database_entry(name)) == 'None':
			add_database_entry(name,password)
			self.saved_messages[name] = []
			string_enc = self.client_key.encrypt('done', 32)[0]
			c.send(string_enc)
		else:
			string_enc = self.client_key.encrypt('name', 32)[0]
			c.send(string_enc)
		return 1

	def do_LOGIN(self):
		c = self.request
		self.name = self.new_key.decrypt(c.recv(4096))
		print 'Got connection from', self.name, '[ IP:', self.client_address[0],']'
		welcome_string = 'Hello %s, you are now successfully connected to the server..'%self.name
		welcome_string_enc = self.client_key.encrypt(welcome_string,32)[0]
		c.send(welcome_string_enc)
		password = self.new_key.decrypt(c.recv(4096))
		if str(find_database_entry(self.name)) != 'None':
			password_db = find_database_entry(self.name)[2]
			if password == password_db:
				c.send('y')
				self.online_users.append(self.name)
				self.connections[self.name] = c
				self.public_key_dict[self.name] = self.client_key
				for user in self.users:
					c.send(self.client_key.encrypt(user,32)[0])
					time.sleep(0.1)
				c.send(self.client_key.encrypt('END OF USERS',32)[0])
				print self.name, 'is SUCCESSFULLY logged in..'
				self.keep_alive()
		else:
			c.send('n')
			c.close()


	def data_out_func(self,intended,data):
		c = self.request
		try:
			if intended in self.online_users:
				c = self.connections[intended]
				key = self.public_key_dict[intended]
				data_enc = key.encrypt(data,32)[0]
				c.send(data_enc)
			else:
				try:
					self.saved_messages[intended].append(data)
				except:
					self.saved_messages[intended] = []
					self.saved_messages[intended].append(data)

		except Exception as e:
			print 'Something went wrong in threaded communication..'
			print e

	def keep_alive(self):
		self.request.settimeout(None)
		c = self.request
		try:
			while self.name in self.online_users:
				for item in self.saved_messages[self.name]:
					self.data_out_func(self.name,item)
				self.saved_messages[self.name] = []
				data_in = str(self.new_key.decrypt(str(c.recv(8192))))
				if 'DISCONNECTED' in data_in:
					print self.name, data_in
					self.online_users.remove(self.name)
					del self.connections[self.name]
					c.close()
					break
				self.intended = data_in.split()[0]
				if self.intended == 'Self':
					self.intended = self.name
				split = data_in.split()
				data_in = ''
				for item in split[1:]:
					data_in = data_in + str(item) + ' '
				data_in = str(self.name) + ': ' + str(data_in)       
				self.data_out_func(self.intended,data_in)
			c.close()
		except Exception as e:
			print 'Something went wrong in threaded communication..'
			print e



class chatServer(ThreadingMixIn, TCPServer):

	def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
		TCPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate=True)
		self.public_key_path = r'D:\public_key_server.pem'
		self.gen_keys()
		create_db_file()
		self.connections = {}
		self.public_key_dict = {}
		self.online_users = []
		self.saved_messages = {}
		self.RequestHandlerClass.public_key_path = self.public_key_path
		self.RequestHandlerClass.saved_messages = self.saved_messages
		self.RequestHandlerClass.connections = self.connections
		self.RequestHandlerClass.public_key_dict = self.public_key_dict
		self.RequestHandlerClass.online_users = self.online_users
		self.RequestHandlerClass.new_key = self.new_key
		self.users = find_all_users_in_db()
		for name in self.users:
			self.saved_messages[name] = []
		self.RequestHandlerClass.users = self.users

	def gen_keys(self):
		print 'Generating the private and public key for encryption...'
		try:
			self.new_key = RSA.generate(2048, e=65537) 
			self.public_key = self.new_key.publickey().exportKey("PEM") 
			self.private_key = self.new_key.exportKey("PEM") 

			f = open(self.public_key_path,'w')
			f.write(self.public_key)
			f.close()
			print 'Key generation SUCCESSFUL'
		except Exception as e:
			print 'Key generation FAILED'
			print 'exiting...'
			sys.exit()


def main_func(HandlerClass=chatHandler, ServerClass=chatServer):
	try:
		hostname = socket.gethostname()
		print 'Host name: %s' %hostname
		port = int(raw_input("Port: "))
		server_address = (hostname, port)
		chat_server = ServerClass(server_address, HandlerClass)	
		addr = chat_server.socket.getsockname()
		print "Serving on", addr[0], "port", addr[1], "..."
		try:
			chat_server.serve_forever()
		except KeyboardInterrupt:
			print 'User requested interrupt..'
			print 'Server is going down.. Waiting for online users to disconnect (if any)..'
			chat_server.shutdown()
			chat_server.server_close()
	except Exception as e:
		print 'Can\'t initiate socket with the given host and port..'


if __name__ == '__main__':
	database_path = r'D:\python_practice\chat_database.db'
	main_func()