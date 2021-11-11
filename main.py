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
        my_cookies = SimpleCookie(self.headers.get('Cookie'))
        if not self.path == '/favicon.ico':
            print('\npath: ' + self.path)
            print(f'{my_cookies=}')

        invalid_cookie = True
        if 'code' in my_cookies:
            if str(my_cookies['code']) in db.user_cookies:
                invalid_cookie = False
            else:
                if not self.path == '/favicon.ico':
                    print(f'INVALID COOKIE FOUND: {self.path=} and {my_cookies=}\n')
        else:
            if not self.path == '/favicon.ico':
                print(f'INVALID COOKIE FOUND: {self.path =}\n')

        
        if invalid_cookie and not self.path.startswith('/check_email'):
            self.get_email()
        else:
            if self.path == '/':
                self.opinions_page()
            elif self.path == '/favicon.ico':
                self.send_response(404)
                self.end_headers()
            elif self.path.startswith('/check_email'):
                self.check_email()
            

    def get_email(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html>
<body>
<form method='GET' action='/check_email'>
<input id='email_box' type='email' name='email'/>
<input id='submit' type='submit' disabled='true'/>
</form>

<script>
setTimeout(checkEmail, 1000);
function checkEmail() {
    current_email = document.getElementById('email_box').value;
    console.log('email: ' + current_email);
    if (current_email.endsWith('@lexingtonma.org')) {
        console.log('PROPER EMAIL');
        document.getElementById('submit').disabled = false;
    }
    else {
        console.log('IMPROPER EMAIL');
        document.getElementById('submit').disabled = true;
    }
    setTimeout(checkEmail, 1000);
}
</script>

</body>
</html>'''.encode('utf8'))

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

    def opinions_page(self):
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

    def __init__(self, email, activity=[], votes={}, opinions=[], confirmed_email=False):
                 
        self.email = email
        self.activity = activity
        self.votes = votes
        self.opinions = opinions
        self.confirmed_email = confirmed_email

class Opinion:

    def __init__(self, ID, text, activity):

        self.ID = ID
        self.text = text
        self.activity = activity
    

def main():
    print('Student Change Web App... running...')

    print(f'\n{db.user_cookies=}')
    for cookie, user in db.user_cookies.items():
        print(f'  {cookie} : User({user.email}, {user.sessions}, {user.votes}, {user.opinions}, {user.confirmed_email})')

    print(f'\n{db.opinions_database=}')
    for ID, opinion in db.opinions_database.items():
        print(f'  {ID} : Opinion()')
        
    httpd = ReuseHTTPServer(('0.0.0.0', 8888), MyHandler)
    httpd.serve_forever()
    

if __name__ == '__main__':
    main()
