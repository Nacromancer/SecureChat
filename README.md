# SecureChat
SecureChat is aimed at creating a secure (encrypted) communication environment in any given network.

#Pre-requisites
SecureChat is built with the help of [SocketServer](https://github.com/python/cpython/blob/master/Lib/socketserver.py), [Crypto](https://github.com/golang/crypto), [sqlite3](https://docs.python.org/2/library/sqlite3.html), [socket](https://github.com/python-git/python/blob/master/Lib/socket.py), [time](https://docs.python.org/2/library/time.html),  [sys](https://docs.python.org/2/library/sys.html), [PySide](https://github.com/PySide/PySide), [threading](https://github.com/python-git/python/blob/master/Lib/threading.py), [hashlib](https://github.com/python-git/python/blob/master/Lib/hashlib.py), [uuid](https://github.com/python/cpython/blob/master/Lib/uuid.py), [os](https://docs.python.org/2/library/os.html) and [errno](https://github.com/python-git/python/blob/master/Lib/plat-irix5/ERRNO.py).

So, for seamless operation of the server and the client, the above mentioned packages should be fetched and installed.

#Run
Once, you have all of the above mentioned packages, you have to choose a machine that you would like to run as the server of your network and you can simply run..
```
python SecureChat_server_v1.0.py
```
This will report you the hostname and ask for a port number, at which you would like to set up the service.

And then on a client machine, you can run...
```
python SecureChat_client_v1.0.py
```
Then, a GUI will show up. The GUI is pretty much self explanatory.

#Want to contribute?
SecureChat still has a lot of space to grow. Your help will be highly appreciated.
