import sys
import time
from PySide import QtGui, QtCore
import socket               # Import socket module
from threading import Thread
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
import hashlib, uuid
import os, errno

class OutLog:
    def __init__(self, edit, out=None, color=None):
        """(edit, out=None, color=None) -> can write stdout, stderr to a
        QTextEdit.
        edit = QTextEdit
        out = alternate stream ( can be the original sys.stdout )
        color = alternate color (i.e. color stderr a different color)
        """
        self.edit = edit
        self.out = None
        self.color = color

    def write(self, m):
        self.edit.moveCursor(QtGui.QTextCursor.End)
        self.edit.setTextColor(self.color)
        self.edit.insertPlainText(m)


class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        screen = str(QtGui.QDesktopWidget.availableGeometry(QtGui.QApplication.desktop())).split(',')
        screen_width = int(screen[-2])
        screen_height = int((str(screen[-1]).split(')'))[0])
        width = 0.5*screen_width
        height = 0.5*screen_height
        self.setGeometry(50, 50, width, height)
        self.move(QtGui.QApplication.desktop().screen().rect().center()- self.rect().center())
        self.setWindowTitle("SecureChat")
        # self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        extractAction = QtGui.QAction("&Exit", self)
        extractAction.setShortcut("Ctrl+Q")
        extractAction.setStatusTip('Leave SecureChat')
        extractAction.triggered.connect(self.close_application)

        regAction = QtGui.QAction("&Register", self)
        regAction.setShortcut("Ctrl+R")
        regAction.setStatusTip('Register for a new account')
        regAction.triggered.connect(self.register)

        paswAction = QtGui.QAction("&Change Password", self)
        paswAction.setShortcut("Ctrl+P")
        paswAction.setStatusTip('Change your password')
        paswAction.triggered.connect(self.changePasswordPage)

        self.statusBar()

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        accMenu = mainMenu.addMenu('&Account Management')
        fileMenu.addAction(extractAction)
        accMenu.addAction(regAction)
        accMenu.addAction(paswAction)

        self.salt = 'hdwuhdfwqhflwj92ue49821ue2uje90du29urn1ro8y:SD":WW{D"WRE#<fojoejq763812uedhyu82h'
        
        self.LoginPage()

    def LoginPage(self):
        self.main_widget = QtGui.QWidget()
    
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setSpacing(5)
        self.leftLayout = QtGui.QFormLayout()
        self.rightLayout = QtGui.QFormLayout()

    
        self.e3 = QtGui.QLineEdit()
        self.rightLayout.addRow("Host IP",self.e3)

        self.e1 = QtGui.QLineEdit()
        self.e1.setValidator(QtGui.QIntValidator())
        self.e1.setMaxLength(4)
        self.rightLayout.addRow("Port No.", self.e1)
    
        self.e4 = QtGui.QLineEdit()
        self.rightLayout.addRow("Name",self.e4)
    
        self.e5 = QtGui.QLineEdit()
        self.e5.setEchoMode(QtGui.QLineEdit.Password)
        self.rightLayout.addRow("Password",self.e5)

        self.e20 = QtGui.QCheckBox('I would like to see my chat history')
        self.rightLayout.addWidget(self.e20)

        self.e21 = QtGui.QCheckBox('I would like to retain my chat history for this session')
        self.rightLayout.addWidget(self.e21)

        self.connect_btn = QtGui.QPushButton("Connect", self)
        self.connect_btn.clicked.connect(self.connect_btnHandle)
        self.connect_btn.resize(self.connect_btn.minimumSizeHint())

        self.rightLayout.addRow(self.connect_btn)

        self.logOutput = QtGui.QTextEdit(self)
        self.logOutput.setReadOnly(True)
        self.logOutput.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        font = self.logOutput.font()
        font.setFamily("Courier")
        font.setPointSize(8)
        # color = QtGui.QColor(150, 0, 150)
        self.logOutput.moveCursor(QtGui.QTextCursor.End)
        self.logOutput.setCurrentFont(font)
        # self.logOutput.setTextColor(color)
        self.logOutput.insertPlainText('Log window..\n')
        sb = self.logOutput.verticalScrollBar()
        sb.setValue(sb.maximum())

        sys.stdout = OutLog( self.logOutput, sys.stdout, QtGui.QColor(150,0,150))
        sys.stderr = OutLog( self.logOutput, sys.stderr, QtGui.QColor(255,0,0))


        self.leftLayout.addWidget(self.logOutput)

        self.users_list = QtGui.QListWidget()
        self.users_list.addItem('Self')


        # self.gridLayout.addLayout(self.leftLayout,0,0,2,1)
        # self.gridLayout.addLayout(self.rightLayout,0,1,2,1)

        self.gridLayout.addWidget(self.logOutput,0,0)
        self.gridLayout.addLayout(self.rightLayout,0,1)

        
        self.main_widget.setLayout(self.gridLayout)
        self.main_widget.setWindowTitle("SecureChat Login")
        self.setCentralWidget(self.main_widget)

        self.connected = 0

        self.show()

    def connect_btnHandle(self):
        if self.connected == 1:
            self.disconnect()
            self.connect_btn.setText('Connect')
            return 1
        self.host = str(self.e3.text())
        self.port = int(self.e1.text())
        self.name = str(self.e4.text())
        password = str(self.e5.text())
        self.password = hashlib.sha512(password + self.salt).hexdigest()
        self.chat_hist_enable = int(self.e20.isChecked())
        self.chat_hist_save_enable = int(self.e21.isChecked())
        self.connected = 0
        a = self.gen_keys()
        if a:
            c = self.establish_connection()
            if c != 0:
                d = self.transfer_keys()
                if d == 0:
                    print 'Please try connecting again..'
                    self.disconnect()
                else:
                    b = self.login()
                    if b == 0:
                        print 'Please try connecting again..'
                        self.disconnect()
                    else:
                        self.connected = 1
                        self.connect_btn.setText('Disconnect')
                        self.chat_hist_path = 'D:\SecureChat_hist_' + self.name + '.txt' 
                        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
                        try:
                            file_handle = os.open(self.chat_hist_path, flags)
                        except OSError as e:
                            if e.errno == errno.EEXIST:  # Failed as the file already exists.
                                pass
                            else:  # Something unexpected went wrong so reraise the exception.
                                raise
                        self.chatPage()
                        if self.chat_hist_enable:
                            self.printChatHistory()
                        Thread(target=self.data_in_handle, args=()).start()
        else:
            print 'Aborting..'
        return 1

    def printChatHistory(self):
        file = open(self.chat_hist_path)
        for line in file:
            sender = line.split()[0]
            intended = line.split()[1]
            text = line.split()[2:]
            chatData = ' '.join(text)
            if self.name == intended:
                chatData = sender + ': ' + chatData
                try:
                    self.messages[sender].append(chatData)
                except:
                    pass
            if self.name == sender:
                chatData = 'You: ' + chatData
                try:
                    self.messages[intended].append(chatData)
                except:
                    pass
        file.close()
        return 1


    def send_btnHandle(self):
        chatData = str(self.chatInput.toPlainText())
        out_string = 'You: ' + chatData + '\n'
        self.chatOutput.insertPlainText(out_string)
        sb1 = self.chatOutput.verticalScrollBar()
        sb1.setValue(sb1.maximum())
        self.chatInput.clear()
        if self.connected == 1:
            server_key = RSA.importKey(self.server_key)
            if self.chat_hist_save_enable:
                with open(self.chat_hist_path, 'a') as writeFile:
                    writeFile.write('%s %s %s\n'%(self.name,self.intended,chatData))
            string = 'You: ' + chatData
            self.messages[self.intended].append(string)
            chatData = str(self.intended) + ' ' + str(chatData)
            data_enc = server_key.encrypt(chatData,32)[0]
            self.s.send(data_enc)
        return 1

    def chatPage(self):
        self.chat_widget = QtGui.QWidget()

        self.chatPage_Layout = QtGui.QGridLayout()

        self.users_list.itemClicked.connect(self.changeIntended)

        self.chatPage_Layout.addWidget(self.users_list,0,0,2,1)

        self.chatOutput = QtGui.QTextEdit(self)
        self.chatOutput.setReadOnly(True)
        self.chatOutput.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        font = self.logOutput.font()
        font.setPointSize(8)
        # color = QtGui.QColor(150, 0, 150)
        self.chatOutput.moveCursor(QtGui.QTextCursor.End)
        self.chatOutput.setCurrentFont(font)
        # self.logOutput.setTextColor(color)
        self.chatOutput.insertPlainText('Chat window..\n\n')
        sb1 = self.chatOutput.verticalScrollBar()
        sb1.setValue(sb1.maximum())

        self.chatPage_Layout.addWidget(self.chatOutput,0,1,1,2)

        self.chatInput = QtGui.QTextEdit(self)
        font = self.logOutput.font()
        font.setPointSize(8)
        # color = QtGui.QColor(150, 0, 150)
        self.chatInput.moveCursor(QtGui.QTextCursor.End)
        self.chatInput.setCurrentFont(font)
        # self.logOutput.setTextColor(color)
        sb = self.chatInput.verticalScrollBar()
        sb.setValue(sb.maximum())

        self.chatPage_Layout.addWidget(self.chatInput,1,1,1,1)

        self.send_btn = QtGui.QPushButton("Send", self)
        self.send_btn.clicked.connect(self.send_btnHandle)
        self.send_btn.resize(self.send_btn.minimumSizeHint())

        self.chatPage_Layout.addWidget(self.send_btn,1,2,1,1)
        
        self.chat_widget.setLayout(self.chatPage_Layout)
        self.chat_widget.setWindowTitle("SecureChat")

        self.chat_widget.show()
        return 1

    def changeIntended(self):
        self.intended = self.users_list.currentItem().text()
        print 'Chatting with:', self.intended
        items = self.users_list.findItems(self.intended,QtCore.Qt.MatchExactly)
        font = items[0].font()
        font.setBold(False)
        items[0].setFont(font)
        self.chatOutput.clear()
        self.chatOutput.insertPlainText('Chat window..\n\n')
        for item in self.messages[self.intended]:
            out_string = item + '\n'
            self.chatOutput.insertPlainText(out_string)
        sb1 = self.chatOutput.verticalScrollBar()
        sb1.setValue(sb1.maximum())

        return 1


    def changePasswordPage(self):
        self.pasw_widget = QtGui.QWidget()

        Layout = QtGui.QFormLayout()

        self.e11 = QtGui.QLineEdit()
        Layout.addRow("Host IP",self.e11)
    
        self.e12 = QtGui.QLineEdit()
        self.e12.setValidator(QtGui.QIntValidator())
        self.e12.setMaxLength(4)
        Layout.addRow("Port No.", self.e12)
    
        self.e13 = QtGui.QLineEdit()
        Layout.addRow("Name",self.e13)
    
        self.e14 = QtGui.QLineEdit()
        self.e14.setEchoMode(QtGui.QLineEdit.Password)
        Layout.addRow("Old Password",self.e14)

        self.e15 = QtGui.QLineEdit()
        self.e15.setEchoMode(QtGui.QLineEdit.Password)
        Layout.addRow("New Password",self.e15)

        self.pasw_btn = QtGui.QPushButton("Change Password", self)
        self.pasw_btn.clicked.connect(self.pasw_btnHandle)
        self.pasw_btn.resize(self.pasw_btn.minimumSizeHint())

        Layout.addRow(self.pasw_btn)
        
        self.pasw_widget.setLayout(Layout)
        self.pasw_widget.setWindowTitle("SecureChat Change Password")

        self.pasw_widget.show()
        return 1

    def pasw_btnHandle(self):
        self.host = str(self.e11.text())
        self.port = int(self.e12.text())
        self.name = str(self.e13.text())
        old_password = str(self.e14.text())
        new_password = str(self.e15.text())
        self.old_password = hashlib.sha512(old_password + self.salt).hexdigest()
        self.new_password = hashlib.sha512(new_password + self.salt).hexdigest()
        a = self.gen_keys()
        if a:
            c = self.establish_connection()
            if c != 0:
                d = self.transfer_keys()
                if d == 0:
                    print 'Please try again..'
                    self.disconnect()
                else:
                    b = self.changePassword()
                    if b == 0:
                        print 'Please try again..'
                        self.disconnect()
                    else:
                        print 'Password changed SUCCESSFULLY.'
        else:
            print 'Aborting..'
        return 1

    def changePassword(self):
        private_key = RSA.importKey(self.private_key)
        server_key = RSA.importKey(self.server_key)
        string_enc = server_key.encrypt('PASS_CH protocol initiated',32)[0]
        self.s.send(string_enc)
        name_enc = server_key.encrypt(self.name, 32)[0]
        self.s.send(name_enc)
        print private_key.decrypt(self.s.recv(4096))
        old_password_enc = server_key.encrypt(self.old_password, 32)[0]
        self.s.send(old_password_enc)
        time.sleep(0.1)
        new_password_enc = server_key.encrypt(self.new_password, 32)[0]
        self.s.send(new_password_enc)
        status = str(private_key.decrypt(self.s.recv(4096)))
        if status == 'done':
            self.pasw_widget.hide()
            return 1
        elif status == 'oldPassWrong':
            print 'The old password is incorrect..'
            return 0
        elif status == 'noName':
            print 'The user name isn\'t registered..'
            return 0

    def register(self):
        self.register_widget = QtGui.QWidget()

        Layout = QtGui.QFormLayout()

        self.e6 = QtGui.QLineEdit()
        self.e6.setValidator(QtGui.QIntValidator())
        self.e6.setMaxLength(4)

        self.e7 = QtGui.QLineEdit()
        Layout.addRow("Host IP",self.e7)
    
        Layout.addRow("Port No.", self.e6)
    
        self.e8 = QtGui.QLineEdit()
        Layout.addRow("Name",self.e8)
    
        self.e9 = QtGui.QLineEdit()
        self.e9.setEchoMode(QtGui.QLineEdit.Password)
        Layout.addRow("Password",self.e9)

        self.register_btn = QtGui.QPushButton("Register", self)
        self.register_btn.clicked.connect(self.register_btnHandle)
        self.register_btn.resize(self.register_btn.minimumSizeHint())

        Layout.addRow(self.register_btn)
        
        self.register_widget.setLayout(Layout)
        self.register_widget.setWindowTitle("SecureChat Registration")

        self.register_widget.show()
        return 1

    def register_btnHandle(self):
        self.host = str(self.e7.text())
        self.port = int(self.e6.text())
        self.name = str(self.e8.text())
        password = str(self.e9.text())
        self.password = hashlib.sha512(password + self.salt).hexdigest()
        a = self.gen_keys()
        if a:
            c = self.establish_connection()
            if c != 0:
                d = self.transfer_keys()
                if d == 0:
                    print 'Please try again..'
                    self.disconnect()
                else:
                    b = self.registration()
                    if b == 0:
                        print 'Please try connecting again..'
                        self.disconnect()
                    else:
                        print 'Registration is done SUCCESSFULLY.'
        else:
            print 'Aborting..'
        return 1

    def registration(self):
        private_key = RSA.importKey(self.private_key)
        server_key = RSA.importKey(self.server_key)
        string_enc = server_key.encrypt('REGISTRATION protocol initiated',32)[0]
        self.s.send(string_enc)
        name_enc = server_key.encrypt(self.name, 32)[0]
        self.s.send(name_enc)
        print private_key.decrypt(self.s.recv(4096))
        password_enc = server_key.encrypt(self.password, 32)[0]
        self.s.send(password_enc)
        status = str(private_key.decrypt(self.s.recv(4096)))
        if status == 'done':
            self.register_widget.hide()
            return 1
        if status == 'name':
            print 'Username already exists!'
            return 0

    def establish_connection(self):
        try:
            self.s = socket.socket()         # Create a socket object
            self.s.connect((self.host, self.port))
            print 'Connected to the server..'
            return 1
        except:
            print 'Connection denied..'
            return 0

    def disconnect(self):
        try:
            if self.connected == 1:
                conn_close = 'DISCONNECTED'
                server_key = RSA.importKey(self.server_key)
                conn_close_enc = server_key.encrypt(conn_close,32)[0]
                self.s.send(conn_close_enc)
            self.s.close()
            self.connected = 0
            self.chat_widget.hide()
            self.messages = {}
            print 'Disconnected from server..'
        except:
            print 'Error while disconnecting..'

    def generate_RSA(self):
        '''
        Generate an RSA keypair with an exponent of 65537 in PEM format
        param: bits The key length in bits
        Return private key and public key
        ''' 
        new_key = RSA.generate(2048, e=65537) 
        self.public_key = new_key.publickey().exportKey("PEM") 
        self.private_key = new_key.exportKey("PEM")
        return 1

    def gen_keys(self):
        print 'Generating keys for encryption..'
        try:
            self.generate_RSA()
            # self.private_key_path = r'D:\python_practice\resources\private_key.pem'
            self.public_key_path = r'D:\public_key.pem'
            # f = open(self.private_key_path,'w')
            # f.write(self.private_key)
            # f.close()
            f = open(self.public_key_path,'w')
            f.write(self.public_key)
            f.close()
            print 'Key generation SUCCESSFUL'
            return 1
        except:
            print 'Key generation FAILED'
            return 0

    def transfer_keys(self):
        try:
			data = 'HANDSHAKE protocol initiated'
			self.s.send(data)
			print 'Sending local public key..'
			f = open(self.public_key_path,'rb')
			l = f.read(4096)
			while l:
			   self.s.send(l)
			   l = f.read(4096)
			f.close()
			print 'Local public key sent!'

			public_key = ''
			while True:
			    print('Fetching the server public key...')
			    data = self.s.recv(4096)
			    public_key = public_key + str(data)
			    if '-----END PUBLIC KEY-----' in str(data):
			        break

			print 'Server\'s public key fetched SUCCESSFULLY'
			self.server_key = public_key
			return 1

        except:
            print 'Key transfer failed..'
            return 0

    def login(self):
        public_key = RSA.importKey(self.server_key)
        private_key = RSA.importKey(self.private_key)
        string_enc = public_key.encrypt('LOGIN protocol initiated',32)[0]
        self.s.send(string_enc)
        time.sleep(0.3)
        name_enc = public_key.encrypt(self.name, 32)[0]
        self.s.send(name_enc)
        print private_key.decrypt(self.s.recv(4096))
        print 'User verification process started..'
        password_enc = public_key.encrypt(self.password, 32)[0]
        self.s.send(password_enc)
        if self.s.recv(4096) == 'y':
            print 'You are successfully logged in..'
            self.messages = {}
            self.intended = 'Self'
            self.users = ['Self']
            self.users_list = QtGui.QListWidget()
            self.users_list.clear()
            self.users_list.addItem('Self')
            self.messages['Self'] = []
            item = self.users_list.item(0)
            item.setSelected(True)
            while True:
                data = private_key.decrypt(self.s.recv(4096))
                if 'END OF USERS' in str(data):
                    break
                if str(data) == self.name:
                    continue
                self.users.append(str(data))
                self.users_list.addItem(str(data))
                self.messages[str(data)] = []
            return 1
        else:
            print 'User credentials are incorrect..'
            return 0

    def data_in_handle(self):
        while self.connected:
            private_key = RSA.importKey(self.private_key)
            data_in = self.s.recv(4096)
            data_in = str(private_key.decrypt(data_in))
            self.sender = data_in.split(':')[0]
            chatData = ''
            for item in data_in.split(':')[1:]:
                chatData = chatData + item + ' '
            if self.chat_hist_save_enable:
                with open(self.chat_hist_path, 'a') as writeFile:
                    writeFile.write('%s %s %s\n'%(self.sender,self.name,chatData))
            if (self.intended == 'Self') and (self.sender == self.name):
                out_string = str(data_in) + '\n'
                self.chatOutput.insertPlainText(out_string)
                sb1 = self.chatOutput.verticalScrollBar()
                sb1.setValue(sb1.maximum())
                try:
                    self.messages['Self'].append(data_in)
                except:
                    pass
            elif self.intended == self.sender:
                out_string = str(data_in) + '\n'
                self.chatOutput.insertPlainText(out_string)
                sb1 = self.chatOutput.verticalScrollBar()
                sb1.setValue(sb1.maximum())
                try:
                    self.messages[self.sender].append(data_in)
                except:
                    pass
            else:
                try:
                    self.messages[self.sender].append(data_in)
                    items = self.users_list.findItems(self.sender,QtCore.Qt.MatchExactly)
                    font = items[0].font()
                    font.setBold(True)
                    items[0].setFont(font)
                except:
                    pass

        return 1

        

    def close_application(self):
        choice = QtGui.QMessageBox.question(self, 'SecureChat',
                                            "Are you sure to close SecureChat?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            sys.exit()
        else:
            pass
        
        

    
def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())


run()