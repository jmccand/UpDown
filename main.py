import urllib.parse
import socket
from http.cookies import SimpleCookie
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import re
import json

import uuid

import db


class MyHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        print('path: ' + self.path)
        my_cookies = SimpleCookie(self.headers.get('Cookie'))
        print(f'{my_cookies=}')
        if ('code' not in my_cookies) and (not self.path.startswith('/check_email')):
            self.get_email()
        else:
            if self.path == '/':
                self.send_opinions()
            elif self.path.startswith('/check_email'):
                self.check_email()
            

    def get_email(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html><body><form method='GET' action='/check_email'><input type='email' name='email'/><input type='submit'/></form><body><html>'''.encode('utf8'))

    def check_email(self):
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'email' in url_arguments:
            #send confirmation email
            #record email + create account
            my_uuid = uuid.uuid1().hex
            while my_uuid in db.user_cookies:
                my_uuid = uuid.uuid1().hex
            db.user_cookies[my_uuid] = User(url_arguments['email'][0])
            db.user_cookies.sync()
            self.send_response(302)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', f'code={my_uuid}; path=/')
            self.end_headers()

    def send_opinions(self):
        self.send_response(200)
        self.end_headers()
        local_opinions = ('Joel is the best name', 'School sucks', 'This app is rad')
        local_opinions_start = 1
        self.wfile.write('<html><body>'.encode('utf8'))
        for index, opinion in enumerate(local_opinions):
            self.wfile.write(f'''<div id='{local_opinions_start + index}'>{opinion}</div>'''.encode('utf8'))
        self.wfile.write('</body></html>'.encode('utf8'))
        
class ReuseHTTPServer(HTTPServer):    
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
    
class User:

    def __init__(self, email, sessions=[], votes={}, opinions=[], confirmed_email=False):
                 
        self.email = email
        self.sessions = sessions
        self.votes = votes
        self.opinions = opinions
        self.confirmed_email = confirmed_email

def main():
    print('Student Change Web App... running...')
    
    httpd = ReuseHTTPServer(('0.0.0.0', 8888), MyHandler)
    httpd.serve_forever()
    

if __name__ == '__main__':
    main()
