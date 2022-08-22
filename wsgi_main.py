import urllib.parse
import socket
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import re
import json
import uuid
import db
import local
import datetime
import smtplib
import calendar
import random
import logging
from wsgiref.simple_server import make_server
import io
import traceback
import os
import updown
import threading
import time
import shutil
import user_agents
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def application(environ, start_response):
    for key, item in environ.items():
        print(f'{key}       {item}')
    handler_object = MyWSGIHandler(environ, start_response)
    handler_object.do_GET()
    if 'AUTH_TYPE' in environ:
        print(f'{environ["AUTH_TYPE"]}')
        
    return [handler_object.wfile.getvalue()]
    
class MyWSGIHandler(SimpleHTTPRequestHandler):

    DEBUG = 5

    def __init__(self, environ, start_response):
        self.headers = {}
        self.path = environ['PATH_INFO']
        self.client_address = (environ['REMOTE_ADDR'],)
        self.query_string = environ['QUERY_STRING']
        self.my_cookies = SimpleCookie(environ.get('HTTP_COOKIE', ''))
        self.http_user_agent = environ['HTTP_USER_AGENT']
        print(self.my_cookies)
        self.wfile = io.BytesIO()

        self.start_response = start_response
        
    
    def do_GET(self):
        print('\n')
        if MyWSGIHandler.DEBUG == 0:
            print('\npath: ' + self.path)
            print(f'{self.my_cookies}')

        invalid_cookie = self.identify_user(nocookie=True) == None and self.path != 'favicon.ico'

        self.path_root = '/'
        if invalid_cookie and not self.path.startswith('/check_email') and not self.path.startswith('/email_taken') and not self.path.startswith('/verify_email') and self.path not in ('/favicon.ico', '/favicon.png', '/hamburger.png', '/timeline.png', '/speed_right.png', '/speed_left.png', '/arrow_right.png', '/arrow_left.png'):
            url_arguments = urllib.parse.parse_qs(self.query_string)
            if self.path == '/' and 'cookie_code' in url_arguments:
                self.path_root = '/'
                self.opinions_page()
            else:
                self.path_root = '/get_email'
                self.get_email()
        else:
            try:
                #self.path_root = '/'
                if self.path == '/':
                    self.opinions_page()
                elif self.path in ('/favicon.ico', '/favicon.png', '/hamburger.png', '/timeline.png', '/speed_right.png', '/speed_left.png', '/arrow_right.png', '/arrow_left.png'):
                    return self.load_image()
                elif self.path == '/manifest.json':
                    self.path_root = '/manifest.json'
                    return self.handle_manifest()
                elif self.path == '/service-worker.js':
                    return self.load_file()
                elif self.path.startswith('/check_email'):
                    self.path_root = '/check_email'
                    self.check_email()
                elif self.path.startswith('/email_taken'):
                    self.path_root = '/email_taken'
                    self.email_taken()
                elif self.path == '/about_the_senate':
                    self.path_root = '/about_the_senate'
                    self.about_the_senate_page()
                elif self.path.startswith('/vote'):
                    self.path_root = '/vote'
                    self.vote()
                elif self.path.startswith('/verify_email'):
                    self.path_root = '/verify_email'
                    self.verify_email()
                elif self.path.startswith('/verification'):
                    self.path_root = '/verification'
                    self.verification_page()
                elif self.path == '/approve_opinions':
                    self.path_root = '/approve_opinions'
                    self.approve_opinions_page()
                elif self.path.startswith('/approve_opinion_search'):
                    self.path_root = '/approve_opinion_search'
                    self.approve_opinion_search()
                elif self.path.startswith('/approve'):
                    self.path_root = '/approve'
                    self.approve()
                elif self.path == '/senate':
                    self.path_root = '/senate'
                    self.senate_page()
                elif self.path.startswith('/view_committee'):
                    self.path_root = '/view_committee'
                    self.view_committee_page()
                elif self.path == '/submit_opinions':
                    self.path_root = '/submit_opinions'
                    self.submit_opinions_page()
                elif self.path.startswith('/submit_opinion_search'):
                    self.path_root = '/submit_opinion_search'
                    self.submit_opinion_search()
                elif self.path.startswith('/already_scheduled'):
                    self.path_root = '/already_scheduled'
                    self.already_scheduled()
                elif self.path.startswith('/leaderboard_lookup'):
                    self.path_root = '/leaderboard_lookup'
                    self.handle_leaderboard_lookup()
                elif self.path.startswith('/leaderboard'):
                    self.path_root = '/leaderboard'
                    self.leaderboard_page()
                elif self.path.startswith('/reserve'):
                    self.path_root = '/reserve'
                    self.reserve()
                elif self.path.startswith('/edit_bill'):
                    self.path_root = '/edit_bill'
                    self.edit_bill()
            except ValueError as error:
                print(str(error))
                traceback.print_exc()
                self.start_response('500 SERVER ERROR', [])
                

    def identify_user(self, nocookie=False):
        #print('identify user function called!')
        if 'code' in self.my_cookies:
            my_code = self.my_cookies['code'].value
            if my_code in db.cookie_database:
                self.update_device_info()
                return db.user_ids[db.cookie_database[my_code]]
            else:
                raise ValueError(f'ip {self.client_address[0]} -- identify user function got code {my_code}')
        else:
            if nocookie:
                return None
            else:
                raise ValueError(f'ip {self.client_address[0]} -- identify user function got no code in cookies')

    def update_device_info(self):
        if 'code' in self.my_cookies:
            my_code = self.my_cookies['code'].value
            if my_code in db.cookie_database:
                parsed_ua = user_agents.parse(self.http_user_agent)
                def update_device_info():
                    db.device_info[my_code] = [self.client_address, parsed_ua]
                self.run_and_sync(db.device_info_lock, update_device_info, db.device_info)

    def send_links_head(self):
        self.wfile.write('''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UpDown</title>
<style>
body {
  background-color: #6d9eebff;
  margin: 0;
  padding: 0;
}
header {
  position: fixed;
  top: 0;
  width: 100%;
  height: 70px;
  z-index: 3;
}
#hamburger {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  z-index: 1;
  border-right: 2px solid black;
  border-bottom: 2px solid black;
  box-sizing: border-box;
}'''.encode('utf8'))
        if self.path_root == '/leaderboard':
            self.wfile.write('''#title {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  text-align: center;
  background-color: #ffef90ff;
  font-size: 40px;
  padding: 10px;
  font-family: 'Times New Roman';
  border-bottom: 2px solid black;
  box-sizing: border-box;
}'''.encode('utf8'))
        else:
            self.wfile.write('''#title {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  text-align: center;
  background-color: #ffef90ff;
  font-size: 50px;
  padding: 5px;
  font-family: 'Times New Roman';
  border-bottom: 2px solid black;
  box-sizing: border-box;
}'''.encode('utf8'))
        self.wfile.write('''#logo {
  position: absolute;
  height: 100%;
  top: 0;
  right: 0;
  z-index: 1;
  border-left: 2px solid black;
  border-bottom: 2px solid black;
  box-sizing: border-box;
}
#menu {
  width: 0;
  height: 100%;
  position: fixed;
  z-index: 2;
  top: 0;
  left: 0;
  overflow-x: hidden;
  background-color: #ffef90ff;
  transition: 0.5s;
}
#menu a {
  position: relative;
  top: 70px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  padding: 15px;
  color: black;
  font-size: 25px;
  text-decoration: none;
}
#menu #x_menu {
  position: absolute;
  top: 0;
  right: 0;
  height: 70px;
  z-index: 2;
}
</style>'''.encode('utf8'))

    def send_links_body(self):
        my_account = self.identify_user(nocookie=True)
        title = ''
        if self.path_root == '/verification':
            title = 'Verify'
        else:
            if my_account == None:
                title = 'Welcome'
            else:
                if self.path_root == '/':
                    title = 'Ballot'
                elif self.path_root == '/submit_opinions':
                    title = 'Submit'
                elif self.path_root == '/senate':
                    title = 'Senate'
                elif self.path_root == '/approve_opinions':
                    title = 'Approve'
                elif self.path_root == '/leaderboard':
                    title = 'Leaderboard'
                elif self.path_root == '/view_committee':
                    url_arguments = urllib.parse.parse_qs(self.query_string)
                    title = url_arguments['committee'][0]
        self.wfile.write(f'''<header>
<img id='hamburger' src='hamburger.png' onclick='open_menu();'/>
<span id='title'>
{title}
</span>
<img id='logo' src='favicon.ico'/>'''.encode('utf8'))
        self.wfile.write('''<div id='menu'>'''.encode('utf8'))
        self.wfile.write('''<div onclick='close_menu();'><img id='x_menu' src='hamburger.png'/></div>'''.encode('utf8'))
        if my_account != None:
            self.wfile.write('''<a href='/'>Ballot</a>
<a href='/submit_opinions'>Submit</a>
<a href='/leaderboard'>Leaderboard</a>
<a href='/senate'>The Senate</a>'''.encode('utf8'))
            if my_account.email in local.MODERATORS and my_account.verified_result == True:
                self.wfile.write('''<a href='/approve_opinions'>Approve</a>'''.encode('utf8'))
            for committee, members in local.COMMITTEE_MEMBERS.items():
                if my_account.email in members and my_account.verified_result == True:
                    self.wfile.write(f'''<a href='/view_committee?committee={committee}'>{committee}</a>'''.encode('utf8'))
        self.wfile.write('''</div></header>'''.encode('utf8'))
        self.wfile.write('''<script>
function open_menu() {
    let menu = document.getElementById('menu').style.width = '250px';
}
function close_menu() {
    document.getElementById('menu').style.width = '0';
}
</script>'''.encode('utf8'))

    def log_activity(self, what=[]):
        my_account = self.identify_user()
        activity_unit = [self.path_root] + what + [datetime.datetime.now()]
        if datetime.date.today() in my_account.activity:
            my_account.activity[datetime.date.today()].append(tuple(activity_unit))
        else:
            my_account.activity[datetime.date.today()] = [tuple(activity_unit)]

        def update_user_activity():
            db.user_ids[my_account.user_ID] = my_account
        
        self.run_and_sync(db.user_ids_lock,
                          update_user_activity,
                          db.user_ids)
        logging.info(f'ip {self.client_address[0]} with {my_account.email} with {my_account.user_ID} did {activity_unit}')
        
    def run_and_sync(self, lock_needed, change, database):
        lock_needed.acquire()
        try:
            change()
        finally:
            lock_needed.release()

    def load_image(self):
        image_type = os.path.splitext(self.path)[1][1:]
        if image_type in ('ico', 'png'):
            image_data = open(self.path[1:], 'rb').read()
            self.start_response('200 OK', [('content-type', f'image/{image_type}'), ('content-length', str(len(image_data)))])
            self.wfile.write(image_data)

    def load_file(self):
        if self.path == '/service-worker.js':
            file_data = open(self.path[1:], 'rb').read()
            self.start_response('200 OK', [('content-type', f'text/javascript'), ('content-length', str(len(file_data)))])
            self.wfile.write(file_data)

    def handle_manifest(self):
        my_account = self.identify_user()
        manifest = '''{
    "short_name": "UpDown",
    "name": "UpDown",
    "icons": [
	{
	    "src": "/favicon.ico",
	    "sizes": "512x512",
	    "type": "image/png"
	},
	{
	    "src": "/favicon.png",
	    "sizes": "192x192",
	    "type": "image/png"
	},
	{
	    "src": "/favicon512x512.png",
	    "sizes": "512x512",
	    "type": "image/png"
	}
    ],
    "start_url": "/?cookie_code=%s",
    "background_color": "#f1c232",
    "theme_color": "#1155cc",
    "display": "standalone"
}''' % (my_account.cookie_code)
        self.start_response('200 OK', [('content-type', f'application/json'), ('content-length', str(len(manifest)))])
        self.wfile.write(manifest.encode('utf8'))
        self.log_activity()

    def get_email(self):
        self.start_response('200 OK', [])
        self.wfile.write('<html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
form#email_form {
  position: absolute;
  top: 100px;
  width: 92%;
  left: 4%;
  bottom: 55%;
  border: 4px solid black;
  border-radius: 12px;
  background-color: white;
  box-sizing: border-box;
  padding: 5%;
  font-size: 25px;
  text-align: center;
}
input#email {
  position: relative;
  top: 20px;
  width: 90%;
  border: 2px solid black;
  font-size: 15px;
  padding: 5px;
}
input#submit {
  position: relative;
  top: 40px;
  font-size: 15px;
}
div#tos {
  position: absolute;
  top: 47%;
  width: 100%;
  font-size: 30px;
  text-align: center;
}
article {
  position: absolute;
  top: 53%;
  width: 92%;
  left: 4%;
  padding: 3%;
  bottom: 5%;
  z-index: 1;
  overflow: scroll;
  font-family: Helvetica, Verdana, 'Trebuchet MS', sans-serif, Arial;
  box-sizing: border-box;
  border: 1px solid black;
  border-radius: 6px;
}
</style>'''.encode('utf8'))
        self.wfile.write('</head><body>'.encode('utf8'))
        self.send_links_body()
        YOGS = [str(x)[-2:] for x in range(int(datetime.date.today().year), int(datetime.date.today().year + 4))]
        self.wfile.write(f'''<form id='email_form' method='GET' action='/check_email'>
Enter your email to vote:<br />
<input id='email' type='email' name='email' /><br />
<input id='submit' type='submit' value='I AGREE TO THE TERMS OF SERVICE' disabled='true'/>
</form>
<div id='tos'>
TERMS OF SERVICE:
</div>
<article>
UpDown uses your email to ensure that each student only votes once.<br /><br />
This app was created to channel the focus of the student body. As LHS has over 2000 students, it can be hard to unify our beliefs. By uniting our preferences, we can work with the administration to bring real change to LHS.<br /><br />
Using UpDown, students submit and vote on opinions. In this way, the student body can raise issues that we care about.<br /><br />
The most popular opinions are submitted to the LHS Student-Faculty Senate, a club that negotiates with the administration to bring about change. With the student body backing the LHS Senate, we will be more unified than ever.<br /><br />
On UpDown, everything you do is kept anonymous. All that UpDown needs from you is your honest opinions about our school. Your name will not be tied to your votes, nor the opinions that you submit.<br /><br />
That said, everything on UpDown is moderated to ensure that opinions don't get out of hand. The privacy policy is contingent on your following LHS's Code of Conduct which outlaws bullying, cyberbullying, and hate speech. Not-safe-for-work content is also not allowed. Anything that directly violates school rules will be reported. UpDown was created for you to share constructive feedback about the school, not to complain about a particular teacher or how much you hate school.<br /><br />
</form>
</article>

<script>
const exceptionEmails = {list(local.EXCEPTION_EMAILS)};
const YOGS = {YOGS};
setTimeout(checkEmail, 1000);
function checkEmail() {{
    current_email = document.getElementById('email').value;
    console.log('email: ' + current_email);
    if (current_email.endsWith('@lexingtonma.org') && YOGS.indexOf(current_email[0] + current_email[1]) != -1) {{
        console.log('PROPER EMAIL');
        document.getElementById('submit').disabled = false;
    }}
    else if (exceptionEmails.indexOf(current_email) != -1) {{
        console.log('EXCEPTION EMAIL');
        document.getElementById('submit').disabled = false;
    }}
    else {{
        console.log('IMPROPER EMAIL');
        document.getElementById('submit').disabled = true;
    }}
    setTimeout(checkEmail, 1000);
}}
</script>

</body>
</html>'''.encode('utf8'))
        
    def send_email(self, to_email, v_uuid):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Add your votes to the count?"
        msg['From'] = local.FROM_EMAIL
        msg['To'] = to_email
        text = f'Welcome to the Student Representation App for LHS! Your votes will NOT count until you click on the link below:\n{local.DOMAIN_NAME}/verify_email?verification_id={v_uuid}'
        html = f'''<html>
<body>
<p>
Welcome to the Student Representation App for LHS!
<br />
<br />
Your votes will NOT count until you click on <a href='{local.DOMAIN_PROTOCAL}{local.DOMAIN_NAME}/verify_email?verification_id={v_uuid}'>this link</a>.
</p>
</body>
</html>'''

        part1 = MIMEText(text, 'plain') 
        part2 = MIMEText(html, 'html')

        msg.attach(part1) 
        msg.attach(part2)

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(local.EMAIL, local.PASSWORD)
            server.sendmail(local.FROM_EMAIL, to_email, msg.as_string())
            server.close()

            print(f'Email sent! {msg.as_string()}')
        except:
            print('Something went wrong...')

    def check_email(self):
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if 'email' in url_arguments:
            user_email = url_arguments['email'][0]
            email_grad = user_email[:2]
            YOGS = [str(x)[-2:] for x in range(int(datetime.date.today().year), int(datetime.date.today().year + 4))]
            if (user_email.endswith('@lexingtonma.org') and email_grad in YOGS) or user_email in local.EXCEPTION_EMAILS:
                def update_user_ids():
                    new_id = str(len(db.user_ids))
                    db.user_ids[new_id] = updown.User(user_email, new_id)
                    new_cookie = uuid.uuid4().hex
                    while new_cookie in db.cookie_database:
                        new_cookie = uuid.uuid4().hex

                    def update_verification_links():
                        send_v_link = None
                        repeat_email = False
                        for v_link, this_user_ID in db.verification_links.items():
                            if db.user_ids[this_user_ID].email == user_email:
                                repeat_email = True
                                send_v_link = v_link

                        if not repeat_email:
                            send_v_link = uuid.uuid4().hex
                            while send_v_link in db.verification_links:
                                send_v_link = uuid.uuid4().hex
                            db.verification_links[send_v_link] = new_id

                        self.send_email(user_email, send_v_link)

                    self.run_and_sync(db.verification_links_lock, update_verification_links, db.verification_links)
                    
                    def update_cookie_database():
                        db.cookie_database[new_cookie] = new_id
                        
                    self.run_and_sync(db.cookie_database_lock, update_cookie_database, db.cookie_database)

                    expiration = datetime.date.today() + datetime.timedelta(days=10)
                    self.start_response('302 MOVED', [('Location', '/'), ('Set-Cookie', f'code={new_cookie}; path=/; expires={expiration.strftime("%a, %d %b %Y %H:%M:%S GMT")}')])
                    self.my_cookies['code'] = new_cookie

                self.run_and_sync(db.user_ids_lock, update_user_ids, db.user_ids)
                
                #redirect to homepage so they can vote
                self.log_activity()
            else:
                raise ValueError(f"ip {self.client_address[0]} -- check email function got email {user_email}")
        else:
            raise ValueError(f'ip {self.client_address[0]} -- check email function got url arguments {url_arguments}')

    def verification_page(self):
        url_arguments = urllib.parse.parse_qs(self.query_string)
        verification_ID = url_arguments.get('verification_id', [None])[0]
        if verification_ID != None and verification_ID in db.verification_links:
            self.start_response('200 OK', [])
            self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
            self.send_links_head()
            self.wfile.write('''<style>
form {
  position: absolute;
  top: 70px;
  width: 100%;
  bottom: 0;
}
table.device {
  position: relative;
  top: 50px;
  width: 90%;
  left: 5%;
  box-sizing: border-box;
  border: 3px solid black;
  border-radius: 20px;
}
td.session_info {
  padding: 5px;
  border-right: 3px solid black;
  width: 60%;
  background-color: #ffef90ff;
  border-radius: 17px 0 0 17px;
  padding: 10px;
  font-size: 18px;
}
td.status {
  width: 40%;
  text-align: center;
  background-color: lightBlue;
  border-radius: 0 17px 17px 0;
}
select.status_drop {
  font-size: 20px;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write('''<input type='hidden' name='verification_id' value='{verification_ID}' /><form method='GET' action='/verification'>'''.encode('utf8'))
            my_email = db.user_ids[db.verification_links[verification_ID]].email
            id_list = []
            for ID, user in db.user_ids.items():
                if user.email == my_email:
                    id_list.append(ID)
            for cookie, ID in db.cookie_database.items():
                if ID in id_list:
                    if cookie in db.device_info:
                        ip_address, parsed_ua = db.device_info[cookie]
                        my_verified_result = db.user_ids[db.cookie_database[cookie]].verified_result
                        self.wfile.write(f'''<table class='device'>
<tr><td class='session_info'>{parsed_ua}</td><td class='status'>
<select class='status_drop' name='{cookie}'>
<option id='{cookie}_True' value='yes'>logged in</option>
<option id='{cookie}_None' value='unverified' disabled='true'>unverified</option>
<option id='{cookie}_False' value='no'>logged out</option></select></td></tr>
</table>
<script>
document.getElementById('{cookie}_{my_verified_result}').selected = 'true';
</script>'''.encode('utf8'))
            self.wfile.write('''</form></body></html>'''.encode('utf8'))
        
    def verify_email(self):
        url_arguments = urllib.parse.parse_qs(self.query_string)
        my_account = self.identify_user(True)
        if 'verification_id' in url_arguments:
            link_uuid = url_arguments['verification_id'][0]
            if link_uuid in db.verification_links:
                verified_account = db.user_ids[db.verification_links[link_uuid]]
                if my_account != None:
                    if my_account != verified_account:
                        # print(f'warning non-viewed user is using verification link! {db.user_ids[db.verification_links[link_uuid]].email}')
                        if verified_account.verified_result == True:
                            def update_cookie_database():
                                db.cookie_database[self.my_cookies['code'].value] = verified_account.user_ID
                            self.run_and_sync(db.cookie_database_lock, update_cookie_database, db.cookie_database)

                            def update_user_ids():
                                my_account.obselete = True
                                db.user_ids[my_account.user_ID] = my_account

                            self.run_and_sync(db.user_ids_lock, update_user_ids, db.user_ids)
                        else:
                            
                            def update_verification_links():
                                db.verification_links[link_uuid] = my_account.user_ID
                                
                            self.run_and_sync(db.verification_links_lock, update_verification_links, db.verification_links)

                            def update_user_ids():
                                my_account.verified_result = True
                                db.user_ids[my_account.user_ID] = my_account

                            self.run_and_sync(db.user_ids_lock, update_user_ids, db.user_ids)
                                
                            
                    else:
                        def update_user_ids():
                            my_account.verified_result = True
                            db.user_ids[my_account.user_ID] = my_account

                        self.run_and_sync(db.user_ids_lock, update_user_ids, db.user_ids)
                    expiration = datetime.date.today() + datetime.timedelta(days=10)
                    self.start_response('200 OK', [])
                        
                else:
                    def update_cookie_database():
                        new_cookie = uuid.uuid4().hex
                        while new_cookie in db.cookie_database:
                            new_cookie = uuid.uuid4().hex
                            
                        db.cookie_database[new_cookie] = verified_account.user_ID
                        
                        expiration = datetime.date.today() + datetime.timedelta(days=10)
                        self.start_response('200 OK', [('Set-Cookie', f'code={new_cookie}; path=/; expires={expiration.strftime("%a, %d %b %Y %H:%M:%S GMT")}')])
                        self.my_cookies['code'] = new_cookie

                    self.run_and_sync(db.cookie_database_lock, update_cookie_database, db.cookie_database)
                    
                self.log_activity()                    
                # send success page
                self.wfile.write('''<!DOCTYPE HTML>
<html>
<body>
Thank you for verifying. Your votes are now counted.<br />
<a href='/?prompt_add=True'>Return to homepage</a>
</body>
</html>'''.encode('utf8'))
                if MyWSGIHandler.DEBUG < 2:
                    print(f'{my_account.email} just verified their email!')

            else:
                raise ValueError(f"ip {self.client_address[0]} -- verify email function got link_uuid {link_uuid}, which is not in the verification database")
        else:
            raise ValueError(f"ip {self.client_address[0]} -- verify email function got url_arguments {url_arguments}")
        
    def opinions_page(self):
        reset_cookie = False
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if not 'code' in self.my_cookies:
            if 'cookie_code' in url_arguments:
                self.my_cookies['code'] = url_arguments['cookie_code'][0]
                reset_cookie = True
        my_account = self.identify_user()
        
        if reset_cookie:
            self.start_response('200 OK', [('Set-Cookie', f'code={url_arguments["cookie_code"][0]}; path=/')])
        else:
            self.start_response('200 OK', [])
        
        see_day = None
        today_date = datetime.date.today()
        if (today_date.weekday() + 1) % 7 < 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7)
        elif (today_date.weekday() + 1) % 7 > 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7 - 4)
        else:
            see_day = today_date
        print(f'day of the week that opinions page is viewing: {see_day}')
        if str(see_day) not in db.opinions_calendar or db.opinions_calendar[str(see_day)] == set():
            self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
            self.wfile.write('''<link rel="manifest" href="/manifest.json" crossorigin='use-credentials'>
<link rel="apple-touch-icon" href="/favicon.png">'''.encode('utf8'))
            self.send_links_head()
            self.wfile.write('''<style>
article#opinion {
  position: absolute;
  top: 70px;
  width: 100%;
  bottom: 30%;
  overflow: scroll;
}
footer {
  position: absolute;
  bottom: 0;
  height: 30%;
  width: 100%;
  z-index: 1;
}
footer table {
  position: absolute;
  text-align: center;
  font-size: 30px;
  width: 50%;
  left: 25%;
  top: 20%;
  border-collapse: collapse;
}
article#cover {
  position: absolute;
  top: 70px;
  width: 100%;
  bottom: 0;
  background-color: #6d9eebff;
  z-index: 2;
}
article#cover div {
  position: absolute;
  left: 50%;
  top: 30%;
  margin-right: -50%;
  transform: translate(-50%, 0);
  text-align: center;
  padding: 0;
  font-size: 40px;
  font-family: Georgia;
}
section {
  top: 25%;
  bottom: 35%;
  width: 96%;
  left: 2%;
  padding: 15px;
  position: fixed;
  background-color: white;
  border-radius: 6px;
  border: 3px solid #595959;
  color: black;
  box-sizing: border-box;
  font-size: 30px;
  cursor: default;
}
article#opinion div {
  font-size: 50px;
}
section p {
  margin: 0;
  position: absolute;
  top: 50%;
  left: 50%;
  margin-right: -50%;
  transform: translate(-50%, -50%);
  text-align: center;
  font-family: Verdana;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write('''<article id='opinion'>
<div id='highlight_title'>
</div>
<section>
<p id='opinion_text'>
</p>
</section>
</article>
<footer>
<table>
<tr style='font-family: Garamond'><td id='care_per'>---%</td><td id='agree_per'>---%</td></tr>
<tr style='font-family: "Times New Roman"'><td>care</td><td>agree</td></tr>
</table>
</footer>'''.encode('utf8'))

            highlights = []

            self.wfile.write('''<article id='cover'><div id='cover_div'>'''.encode('utf8'))

            if datetime.date.today().weekday() == 2:
                self.wfile.write('''Middle Wednesday:<br />Ballot Recap'''.encode('utf8'))
                highlights.append(('Middle Wednesday:<br />Ballot Recap',))
            else:
                self.wfile.write('''Off Day:<br />Ballot Recap'''.encode('utf8'))
                highlights.append(('Off Day:<br />Ballot Recap',))
            self.wfile.write('''</div></article>'''.encode('utf8'))
            
            see_old_days = []
            check_day = see_day
            if check_day.weekday() not in (3, 6):
                check_day = check_day - datetime.timedelta(days=3)
            while len(see_old_days) < 2 and check_day > local.LAUNCH_DATE:
                # check_day.weekday is either 3 or 6
                assert check_day.weekday() in (3, 6)
                if db.opinions_calendar.get(str(check_day), set()) != set():
                    see_old_days.append(check_day)
                if check_day.weekday() == 3:
                    check_day = check_day - datetime.timedelta(days=4)
                else:
                    check_day = check_day - datetime.timedelta(days=3)
            # reorder so most recent is last
            see_old_days = see_old_days[::-1]
            print(f'{see_old_days}')

            for day in see_old_days:
                def day_to_nice_string(d):
                    return d.strftime('%A %m/%d')
                end_date = day + datetime.timedelta(days=3)
                highlights.append((f'{day_to_nice_string(day)} - {day_to_nice_string(end_date)}',))
                this_list = [db.opinions_database[x] for x in db.opinions_calendar[str(day)]]
                this_list.sort(key=lambda x: -1 * x.care_agree_percent()[0] * x.care_agree_percent()[1])
                for opinion in this_list:
                    highlights.append((opinion.text,) + opinion.care_agree_percent())

            # javascript doesn't have tuples
            highlights = [list(x) for x in highlights]
                        
            self.wfile.write(f'''<script>
let highlights = {highlights}
let current_index = 0;
let timeElapsed = 0;

document.addEventListener('touchstart', handleTouchStart, false);
document.addEventListener('touchmove', handleTouchMove, false);
document.addEventListener('keydown', handleKeyDown, false);

var xStart = null;
var yStart = null;

setInterval(increaseTimeElapsed, 200, 200);

function getTouches(evt) {{
  return evt.touches ||
         evt.originalEvent.touches;
}}

function handleTouchStart(evt) {{
    const start = getTouches(evt)[0];
    xStart = start.clientX;
    yStart = start.clientY;
}}

function handleTouchMove(evt) {{
    if (xStart == null || yStart == null) {{
        return;
    }}

    var xEnd = evt.touches[0].clientX;
    var yEnd = evt.touches[0].clientY;

    var xDiff = xStart - xEnd;
    var yDiff = yStart - yEnd;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {{
        if (xDiff > 0) {{
            change(1);
        }}
        else {{
            change(-1);
        }}
    }}
    else {{
        return;
    }}
    xStart = null;
    yStart = null;
}}
function handleKeyDown(evt) {{
    let key_pressed = event.key;
    const keyDict = {{
        'ArrowRight': [change, 1],
        'ArrowLeft': [change, -1]
    }};
    if (keyDict[key_pressed] != null) {{
        var func_arg_list = keyDict[key_pressed];
        func_arg_list[0](func_arg_list[1]);
    }}
}}
function increaseTimeElapsed(time) {{
    timeElapsed += time;
    if (highlights[current_index].length == 1) {{
        if (timeElapsed > 3000) {{
            change(1);
        }}
    }}
    else {{
        if (timeElapsed > 4500) {{
            change(1);
        }}
    }}
}}
function change(i) {{
    let newIndex = current_index + i;
    if (newIndex < 0) {{
        newIndex = 0;
    }}
    else if (newIndex >= highlights.length) {{
        newIndex = highlights.length - 1;
    }}
    if (highlights[newIndex].length == 1) {{
        cover(highlights[newIndex][0]);
    }}
    else {{
        highlight(highlights[newIndex]);
    }}
    current_index = newIndex;
    timeElapsed = 0;
}}
function cover(text) {{
    document.getElementById('cover_div').innerHTML = text;
    document.getElementById('cover').style.display = 'initial';
}}
function highlight(info) {{
    document.getElementById('opinion_text').innerHTML = info[0];
    document.getElementById('care_per').innerHTML = info[1] + '%';
    document.getElementById('agree_per').innerHTML = info[2] + '%';
    document.getElementById('cover').style.display = 'none';
}}
</script>
'''.encode('utf8'))
        else:
            self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
            self.wfile.write('''<link rel="manifest" href="/manifest.json" crossorigin='use-credentials'>
<link rel="apple-touch-icon" href="/favicon.png">'''.encode('utf8'))
            self.send_links_head()
            self.wfile.write('''<style>
article#ballot_label {
  position: absolute;
  top: 120px;
  font-size: 25px;
  padding: 10px;
  width: 96%;
  left: 2%;
  border: 2px solid black;
  border-radius: 25px;
  box-sizing: border-box;
  text-align: center;
  background-color: #ffef90ff;
}
article#opinion {
  position: absolute;
  top: 220px;
  width: 96%;
  left: 2%;
  bottom: 25%;
  z-index: 1;
  overflow: scroll;
  border-radius: 6px;
  border: 3px solid black;
  background-color: #ffef90ff;
  box-sizing: border-box;
}
div#counter {
  position: absolute;
  top: 0;
  font-size: 25px;
  padding: 5px;
  border-bottom: 2px solid black;
  width: 100%;
  box-sizing: border-box;
  text-align: center;
}
section#opinion_text {
  top: 41px;
  bottom: 0;
  width: 100%;
  padding: 15px;
  position: absolute;
  background-color: white;
  box-sizing: border-box;
  font-size: 30px;
  border: 2px solid black;
}
p#opinion_p {
  margin: 0;
  position: absolute;
  top: 50%;
  left: 50%;
  margin-right: -50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
div#banner {
  top: 70px;
  position: absolute;
  left: 2%;
  font-size: 25px;
  padding: 2%;
  width: 96%;
  border-radius: 3px;
  border: 2px solid black;
  background-color: lightBlue;
  box-sizing: border-box;
  z-index: 1;
  display: none;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            randomized = list(db.opinions_calendar[str(see_day)])
            random.shuffle(randomized)
            my_votes = []
            opinion_texts = []
            for opinion_ID in randomized:
                assert opinion_ID in db.opinions_database
                opinion = db.opinions_database[opinion_ID]
                assert opinion.approved == True
                opinion_texts.append(opinion.text)
                if str(opinion_ID) in my_account.votes:
                    this_vote = my_account.votes[str(opinion_ID)][-1][0]
                    my_votes.append(this_vote)
                else:
                    my_votes.append('abstain')
            self.wfile.write(f'''<article id='ballot_label'>
Ballot {see_day.strftime('%a %-m/%-d')} - {(see_day + datetime.timedelta(days=2)).strftime('%a %-m/%-d')}
</article>
<article id='opinion'>
<div id='counter'>
</div>
<section id='opinion_text'>
<p id='opinion_p'>{db.opinions_database[randomized[0]].text}</p>
</section>
</article>'''.encode('utf8'))
            self.wfile.write(f'''<script>
const page_IDs = {randomized};
const opinion_texts = {opinion_texts};
let votes = {my_votes};
let current_index = 0;

document.addEventListener('touchstart', handleTouchStart, false);
document.addEventListener('touchmove', handleTouchMove, false);
document.addEventListener('dblclick', handleDoubleClick, false);
document.addEventListener('keydown', handleKeyDown, false);

change(0);

var xStart = null;
var yStart = null;

function getTouches(evt) {{
  return evt.touches ||
         evt.originalEvent.touches;
}}

function handleTouchStart(evt) {{
    const start = getTouches(evt)[0];
    xStart = start.clientX;
    yStart = start.clientY;
}}

function handleTouchMove(evt) {{
    if (xStart == null || yStart == null) {{
        return;
    }}

    var xEnd = evt.touches[0].clientX;
    var yEnd = evt.touches[0].clientY;

    var xDiff = xStart - xEnd;
    var yDiff = yStart - yEnd;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {{
        if (xDiff > 0) {{
            change(1);
        }}
        else {{
            change(-1);
        }}
    }}
    else {{
        if (yDiff > 0) {{
            vote('up');
        }}
        else {{ 
            vote('down');
        }}
    }}
    xStart = null;
    yStart = null;
}}
function handleDoubleClick(evt) {{
    vote('abstain');
}}
function vote(my_vote) {{
    var xhttp = new XMLHttpRequest();
    if (checkVoteValidity(my_vote, votes[current_index])) {{
        xhttp.open('GET', '/vote?opinion_ID=' + page_IDs[current_index] + '&my_vote=' + my_vote, true);
        xhttp.send();
        votes[current_index] = my_vote;
        let opinion_box = document.getElementById('opinion_text');
        if (my_vote == 'up') {{
            opinion_box.style.borderColor = '#00ff00ff';
        }}
        else if (my_vote == 'down') {{
            opinion_box.style.borderColor = '#ff0000ff';
        }}
        else {{
            opinion_box.style.borderColor = '#595959';
        }}
        setTimeout(() => {{change(1)}}, 1000);
    }}
}}
function checkVoteValidity(new_vote, old_vote) {{
    let up_count = 0;
    let down_count = 0;
    for (let index = 0; index < votes.length; index++) {{
        if (votes[index] == 'up') {{
            up_count++;
        }}
        else if (votes[index] == 'down') {{
            down_count++;
        }}
    }}
    let valid = true;
    if (up_count == 5 && new_vote == 'up') {{
        alert('You cannot vote up more than 5 times a day. Prioritize the opinions that you feel more strongly about and leave the others unvoted.');
        valid = false;
    }}
    else if (down_count == 5 && new_vote == 'down') {{
        alert('You cannot vote down more than 5 times a day. Prioritize the opinions that you feel more strongly about and leave the others unvoted.');
        valid = false;
    }}
    if (old_vote == 'abstain') {{
        if (up_count + down_count == 8 && new_vote != 'abstain') {{
            alert('You cannot vote more than 8 times a day. Prioritize the opinions that you feel more strongly about and leave the others unvoted.');
            valid = false;
        }}
    }}
    return valid;
}}
function handleKeyDown(evt) {{
    let key_pressed = event.key;
    const keyDict = {{
        'ArrowUp': [vote, 'up'],
        'ArrowDown': [vote, 'down'],
        ' ': [vote, 'abstain'],
        'ArrowRight': [change, 1],
        'ArrowLeft': [change, -1]
    }};
    if (keyDict[key_pressed] != null) {{
        var func_arg_list = keyDict[key_pressed];
        func_arg_list[0](func_arg_list[1]);
    }}
}}
function change(i) {{
    let opinion_text = document.getElementById('opinion_p');
    let opinion_box = document.getElementById('opinion_text');
    let counter = document.getElementById('counter');
    if (current_index + i < page_IDs.length && current_index + i >= 0) {{
        current_index += i;
        opinion_text.innerHTML = opinion_texts[current_index];
        counter.innerHTML = current_index + 1 + '/' + page_IDs.length;
        if (votes[current_index] == 'up') {{
            opinion_box.style.borderColor = '#00ff00ff';
        }}
        else if (votes[current_index] == 'down') {{
            opinion_box.style.borderColor = '#ff0000ff';
        }}
        else {{
            opinion_box.style.borderColor = '#595959';
        }}
    }}
}}
</script>
'''.encode('utf8'))
            self.wfile.write('''<div id='banner'></div>
<script>
function banner(text) {
    document.getElementById('banner').innerHTML = text;
    document.getElementById('banner').style.display = 'table-cell';
    setTimeout(function close() {
document.getElementById('banner').style.display = 'none';
}, 3000);
}
</script>'''.encode('utf8'))
        self.wfile.write(f'''</footer>
<script>
if ('serviceWorker' in navigator) {{
    window.addEventListener('load', function() {{
        navigator.serviceWorker.register('service-worker.js').then(function(registration) {{
        console.log('Registered!');
        }}, function(err) {{
            console.log('ServiceWorker registration failed: ', err);
        }}).catch(function(err) {{
            console.log(err);
        }});
    }});
}} else {{
  console.log('service worker is not supported');
}}
self.addEventListener('install', function() {{
  console.log('Install!');
}});
self.addEventListener("activate", event => {{
  console.log('Activate!');
}});
self.addEventListener('fetch', function(event) {{
  console.log('Fetch!', event.request);
}});
</script>'''.encode('utf8'))
        self.wfile.write('</body></html>'.encode('utf8'))
        self.log_activity()
        
    def submit_opinions_page(self):
        print('submit opinions page')
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if 'opinion_text' in url_arguments:
            self.submit_opinion(False)
        self.start_response('200 OK', [])
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
form {
  position: absolute;
  top: 100px;
  width: 92%;
  height: 130px;
  left: 4%;
  font-size: 25px;
  padding: 6%;
  box-sizing: border-box;
  border: 3px solid black;
  border-radius: 20px;
  text-align: center;
  background-color: #ffef90ff;
}
input {
  position: relative;
  top: 15px;
  width: 97%;
  font-size: 20px;
}
div#similar_message {
  position: absolute;
  top: 250px;
  height: 45px;
  font-size: 25px;
  width: 100%;
  padding: 3%;
  box-sizing: border-box;
}
article {
  position: absolute;
  top: 305px;
  bottom: 0;
  width: 100%;
  font-size: 25px;
  padding: 3%;
  box-sizing: border-box;
}
section {
  width: 98%;
  margin: 1%;
  margin-bottom: 4%;
  padding: 3%;
  position: relative;
  background-color: #cfe2f3ff;
  z-index: 1;
  border-radius: 6px;
  box-sizing: border-box;
}
</style>
</head>
<body>'''.encode('utf8'))
        self.send_links_body()
        self.wfile.write('''<form method='GET' action='/submit_opinions'>
Enter your opinion below:<br />
<input type='text' id='opinion' name='opinion_text'/>
</form>
<div id='similar_message'>
Similar opinions
<span style='font-size: 12px; width: 100%; text-align: center'>* identical ones will be rejected *</span>
</div>
<article id='results'>
Similar opinions will display here.
</article>
<script>
var old_opinion;
setInterval(updateSearch, 1000);
function updateSearch() {
    let current_opinion = document.getElementById('opinion').value;
    if (current_opinion != old_opinion) {
        let results = document.getElementById('results');
        if (current_opinion == '') {
            results.innerHTML = 'Similar opinions will display here.';
        }
        else {
            var xhttp = new XMLHttpRequest();
            xhttp.open('GET', '/submit_opinion_search?text=' + current_opinion);
            xhttp.send();
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    var response = JSON.parse(this.responseText);
                    let search_results = response;
                    if (search_results.length == 0) {
                        results.innerHTML = 'No similar opinions.';
                    }
                    else {
                        results.innerHTML = '';
                        for (var index = 0; index < search_results.length; index++) {
                            results.innerHTML += '<section>' + search_results[index] + '</section>';
                        }
                    }
                }
            };
        }
    }
    old_opinion = current_opinion;
}
</script>
</body>
</html>'''.encode('utf8'))

    def approve_opinions_page(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_result == True:
            self.start_response('200 OK', [])
            self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
            self.send_links_head()
            self.wfile.write('''<style>
article {
  position: absolute;
  top: 70px;
  width: 100%;
  bottom: 55%;
  z-index: 1;
  overflow: scroll;
}
div#counter {
  position: absolute;
  width: 30%;
  left: 35%;
  top: 10%;
  border: 2px solid black;
  font-size: 25px;
  box-sizing: border-box;
  border-radius: 12px;
  background-color: lightGray;
  text-align: center;
  padding: 5px;
  height: 35px;
}
div#opinion {
  position: absolute;
  height: 61%;
  width: 90%;
  top: 30%;
  left: 5%;
  border: 2px solid black;
  border-radius: 4px;
  box-sizing: border-box;
  background-color: white;
  font-size: 20px;
  text-align: center;
  padding: 2%;
}  
section {
  width: 98%;
  margin: 1%;
  margin-bottom: 4%;
  padding: 3%;
  position: relative;
  background-color: #cfe2f3ff;
  z-index: 1;
  border-radius: 6px;
  box-sizing: border-box;
}
div#lock {
  position: absolute;
  top: 45%;
  height: 8%;
  padding: 1%;
  box-sizing: border-box;
  width: 90%;
  left: 5%;
  border: 2px solid black;
  border-radius: 6px;
  text-align: center;
  background-color: lightBlue;
}
div#similar_message {
  position: absolute;
  top: 58%;
  font-size: 25px;
  padding: 0;
  left: 50%;
  margin-right: -50%;
  transform: translate(-50%, 0);
}
footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 37%;
  z-index: 1;
  padding: 3%;
  box-sizing: border-box;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            unapproved_list = []
            for opinion_ID, opinion in db.opinions_database.items():
                if opinion.approved == None:
                    unapproved_list.append((opinion_ID, opinion.text))
            unapproved_list = [list(x) for x in unapproved_list]
            self.wfile.write(f'''<article>
<div id='counter'>'''.encode('utf8'))
            if len(unapproved_list) > 0:
                self.wfile.write(f'1/{len(unapproved_list)}'.encode('utf8'))
            self.wfile.write('''</div>
<div id='opinion'>'''.encode('utf8'))
            if len(unapproved_list) > 0:
                self.wfile.write(f'{unapproved_list[0][1]}'.encode('utf8'))
            self.wfile.write(f'''</div>
</article>
<div id='lock'>
APPROVAL LOCK<br />
START SWIPE HERE TO APPROVE
</div>
<div id='similar_message'>
Similar opinions
<span style='font-size: 16px; width: 100%; text-align: center'>* reject identical ones *</span>
</div>
<footer id='results'>
</footer>'''.encode('utf8'))
            self.wfile.write(f'''<script>
const opinionList = {unapproved_list};
let current_index = 0;
var old_opinion;
let unlocked = false;

updateSearch();
setInterval(updateSearch, 1000);

document.addEventListener('touchstart', handleTouchStart, false);
document.addEventListener('touchmove', handleTouchMove, false);

var xStart = null;
var yStart = null;

function getTouches(evt) {{
  return evt.touches ||
         evt.originalEvent.touches;
}}

function handleTouchStart(evt) {{
    const start = getTouches(evt)[0];
    xStart = start.clientX;
    yStart = start.clientY;
    let lock_p = document.getElementById('lock').getBoundingClientRect();
    if (xStart > lock_p.left && xStart < lock_p.right) {{
        if (yStart > lock_p.top && yStart < lock_p.bottom) {{
            unlocked = true;
        }}
    }}
}}

function handleTouchMove(evt) {{
    if (xStart == null || yStart == null) {{
        return;
    }}

    var xEnd = evt.touches[0].clientX;
    var yEnd = evt.touches[0].clientY;

    var xDiff = xStart - xEnd;
    var yDiff = yStart - yEnd;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {{
        return;
    }}
    else {{
        if (unlocked) {{
            if (yDiff > 0) {{
                vote('yes');
            }}
            else {{ 
                vote('no');
            }}
        }}
    }}
    xStart = null;
    yStart = null;
    unlocked = false;
}}
function vote(my_vote) {{
    if (opinionList.length > 0) {{
        var xhttp = new XMLHttpRequest();
        const opinion_ID = opinionList[current_index][0];
        let opinion_box = document.getElementById('opinion');

        xhttp.open('GET', '/approve?opinion_ID=' + opinion_ID + '&my_vote=' + my_vote, true);
        xhttp.send();
        
        current_index++;
        if (current_index < opinionList.length) {{
            opinion_box.innerHTML = opinionList[current_index][1];
            document.getElementById('counter').innerHTML = current_index + 1 + '/' + opinionList.length;
        }}
        else {{
            opinion_box.innerHTML = '';
            document.getElementById('counter').innerHTML = '';
        }}
    }}
}}
function updateSearch() {{
    let current_opinion = document.getElementById('opinion').innerHTML;
    if (current_opinion != old_opinion) {{
        let results = document.getElementById('results');
        if (current_opinion == '') {{
            results.innerHTML = 'Similar opinions will display here.';
        }}
        else {{
            var xhttp = new XMLHttpRequest();
            xhttp.open('GET', '/approve_opinion_search?text=' + current_opinion + '&opinion_ID=' + opinionList[current_index][0]);
            xhttp.send();
            xhttp.onreadystatechange = function() {{
                if (this.readyState == 4 && this.status == 200) {{
                    var response = JSON.parse(this.responseText);
                    let search_results = response;
                    if (search_results.length == 0) {{
                        results.innerHTML = 'No similar opinions.';
                    }}
                    else {{
                        results.innerHTML = '';
                        for (var index = 0; index < search_results.length; index++) {{
                            results.innerHTML += '<section>' + search_results[index] + '</section>';
                        }}
                    }}
                }}
            }};
        }}
    }}
    old_opinion = current_opinion;
}}
</script>'''.encode('utf8'))
            self.wfile.write('</body></html>'.encode('utf8'))
            self.log_activity()

    def senate_page(self):
        my_account = self.identify_user()
        self.start_response('200 OK', [])
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
article {
  position: absolute;
  top: 105px;
  bottom: 0;
  width: 100%;
  z-index: 1;
  overflow: scroll;
  background-color: #cfe2f3ff;
  padding: 2%;
  box-sizing: border-box;
}
#back_to_top {
  position: absolute;
  top: 75px;
  width: 100%;
  border: 2px solid black;
  background-color: lightGray;
}
</style>'''.encode('utf8'))
        self.wfile.write('</head><body>'.encode('utf8'))
        self.send_links_body()
        self.wfile.write('''<div id='back_to_top'><a href='/senate#TOC'>Back to the top</a></div>'''.encode('utf8'))
        self.wfile.write('''<article>'''.encode('utf8'))
        self.wfile.write('''<h2><a name='TOC'>Table of Contents</a></h2>
<ul>
<li><a href='/senate#welcome'>Welcome!</a></li>
<li><a href='/senate#meet'>Meet the Senators</a></li>
<!--<li><a href='/senate#about'>About the Senate</a></li>-->
<li><a href='/senate#constitution'>Constitution</a></li>
<li><a href='/senate#bills'>Senate Bills</a></li>
<li><a href='/senate#minutes'>Minutes</a></li>
<li><a href='/senate#attendance'>Senate Attendance</a></li>
<li><a href='/senate#FAQ'>Frequently Asked Questions!</a></li>
</ul>'''.encode('utf8'))
        self.wfile.write('''<h2><a name='welcome'>Welcome!</a></h2>
Welcome to the Lexington High School Student-Faculty Senate! The Senate convenes at 3:15pm on Wednesdays in the Library Media Center.<br />
We implement school-wide policies on a number of issues, from things as mundane as placing extra benches around the school to changes as significant as eliminating the community service requirement for open campus, allowing students to eat in the Quad, or determining what information will be printed on transcripts.<br />
All meetings are open to the public! If you want to change something about the school, we would love to hear and discuss your ideas.<br />'''.encode('utf8'))
        #self.wfile.write('''<h2><a name='about'>About the Senate</a></h2>'''.encode('utf8'))
        self.wfile.write(f'''<h2><a name='meet'>Meet the Senators</a></h2>
Executive<br />
{local.EXECUTIVE}

Communications' job is to let the student body know about the different actions Senate is doing! That includes running our Instagram, advertising events, and maintaining our Suggestions Box. This year, we also organized the Trash Can Giveaway for students to paint the LHS trash cans, social-distancing dots in the quad, and Course Advice for rising high schoolers. <br />
{local.COMMUNICATIONS}

Oversight looks at past legislation for review, which can then be reintroduced for edits or to be removed! We are focused on the school administration and student senate's accountability and efficiency. We are also responsible for maintaining the Senate website. This year, we've been passing resolutions to make vaccination resources available to the student body!<br />
{local.OVERSIGHT}

The Policy Committee works to discuss preliminary policies before they appear in front of the entire senate. In the past we have worked on Mental Health day as well as Brain Breaks, both of which are currently in the process of being passed. Through negotiation and communication, we aim to create and organize welcoming events for our school in order to maintain the community. Come join us >:D<br />
{local.POLICY}

The Social Action Committee is concerned primarily with student activism and relations between LHS and the surrounding community. It monitors community service programs and enforces volunteerism, improving life as a LHS student/faculty and solving problems important to our school.<br />
{local.SOCIAL_ACTION}

The Climate Committee is dedicated to creating a welcoming and vibrant community, and has strived to do so this year by organizing the LHS Mural Project. Climate has been working on assembling a team of artists to create a mural in the freshman mods so that all future classes will be able to enjoy the work of art on their way to class.<br />
{local.CLIMATE}'''.encode('utf8'))
        self.wfile.write('''<h2><a name='constitution'>Constitution</a></h2>
<div style='width:90%; height:200px; overflow:scroll; border:2px solid black; padding:5px;'>
Article I: Philosophy<br />
<br />
All members of the school community should have a meaningful voice in determining the policies of the school, in promoting a positive school climate, and in shaping the future of the school. It is essential that each member be kept informed through effective communications and have the power to influence decisions made at Lexington High School. For this purpose the Lexington High School Senate is established.<br />
<br />
<br />
Article II: Membership<br />
<br />
Section 1 The Senate shall consist of two elected groups. The first shall include one certified staff representative for every ten members of the certified high school staff. The second shall include one student representative for every fifty members of the student body. The number of student representatives shall be determined each April 1 and be based on the current enrollment in grades eight through eleven.<br />
<br />
Section 2 Nine students shall be elected at-large from and by each class. If the total number of student representatives falls below thirty-six, then the number of representatives from each class shall be determined by dividing the total number of student representatives by four, with the first remainder allotted to the senior class, the second to the junior class, and the third to the sophomore class, in that order.<br />
<br />
Section 3 One faculty representative shall be elected from each building and one from the science building and one from the combined members of the music, art, industrial technology, and physical education departments. The remaining faculty representatives shall be elected from the faculty at large.<br />
<br />
Section 4 There will be up to five places open for groups who feel that they are not represented in the above election plan. These groups must petition the Senate for such representation.<br />
<br />
<br />
Article III: Organization<br />
<br />
Section 1 The Senate shall have a Moderator, an Assistant Moderator, and a Secretary.<br />
<br />
Section 2 There shall be standing committees in the following areas: Executive, Social Action, Communications, Elections, Policy, School Climate.<br />
<br />
Section 3 Standing committees shall contain not fewer than four nor more than twelve members and shall approximate the student-faculty ratio of the Senate.<br />
<br />
Section 4 All members of the Senate shall serve on at least one standing committee.<br />
<br />
Section 5 The executive committee shall consist of the moderator, assistant moderator, secretary, and the Student Activities Coordinator. Members of the executive committee shall not serve on any other standing committees with the exception of the secretary, who shall chair the standing committee on communications.<br />
<br />
Section 6 In addition to the standing committees listed in Section 2, others may be established according to need by a simple majority vote of the Senate.<br />
<br />
<br />
Article IV: Elections and Tenure of Office<br />
<br />
Section 1 The student members shall be elected by or on the third Friday in May. Freshman class representatives shall be elected by or on the second Friday in October. Faculty representatives shall be elected by the third Friday in May.<br />
<br />
Section 2 There shall be a moderator elected by and from the Senate for a one year term. If the moderator elected in any given year is a student, then the assistant moderator elected by the Senate shall be a faculty member; conversely, if the moderator is a faculty member, the assistant moderator shall be a student.<br />
<br />
Section 3 The moderator, the assistant moderator, and the secretary shall be elected by the full Senate at its first meeting following the May elections, but no later than the first day of June.<br />
<br />
Section 4 Each representative shall assume office one week after the conclusion of elections and shall serve until the next year's election.<br />
<br />
<br />
Article V: Roles of the Officers and Standing Committees<br />
<br />
Section 1 Moderator<br />
<br />
A. The moderator shall preside over all meetings of the Senate as specified in Article VII.<br />
B. The moderator shall be responsible for maintaining an orderly meeting and shall have the right to dismiss anyone disrupting a meeting.<br />
<br />
C. The moderator shall chair executive committee.<br />
<br />
D. The moderator and the assistant moderator shall meet weekly with the principal.<br />
<br />
E. The moderator shall facilitate and coordinate the work and efforts of the standing committees.<br />
<br />
<br />
Section 2 Assistant Moderator<br />
<br />
A. The assistant moderator shall preside over the meetings of the Senate in the absence of the moderator.<br />
B. The assistant moderator shall be a member of the executive committee.<br />
<br />
C. The assistant moderator and the moderator shall meet weekly with the principal.<br />
<br />
D. The assistant moderator shall facilitate and coordinate the work and efforts of the standing committees.<br />
<br />
<br />
Section 3 Secretary<br />
<br />
A. The secretary shall record Senate attendance, make public minutes of Senate sessions, and carry on correspondence as may be directed by the moderator or the assistant moderator.<br />
B. The secretary shall preside over Senate meetings in the absence of both the moderator and the assistant moderator.<br />
<br />
C. The secretary shall be a member of the executive committee.<br />
<br />
D. The secretary shall chair the standing committee on communications.<br />
<br />
Section 4 Student Activities Coordinator<br />
<br />
A. The Student Activities Coordinator shall act as advisor to the officers and to the Senate.<br />
B. The Student Activities Coordinator shall serve as an exofficio and non-voting member of the Senate.<br />
<br />
C. The Student Activities Coordinator shall serve as a non-voting member of the executive committee.<br />
<br />
D. The Student Activities Coordinator shall assist the Senate by facilitating the various activities of the Senate.<br />
<br />
E. The Student Activities Coordinator, in the absence of all officers, shall preside over a meeting of the Senate and shall appoint a secretary for that particular meeting.<br />
<br />
<br />
Section 5 Standing Committees<br />
<br />
A. The standing committees shall perform tasks as directed by the moderator and/or assistant moderator.<br />
B. The standing committees shall meet to investigate issues within the scope of their charge and report their findings to the Senate for discussion and vote.<br />
<br />
C. The executive committee shall set agendas for the Senate meetings and shall appoint Senate members to standing committees in accordance with these by-laws.<br />
<br />
<br />
Article VI: Scope and Jurisdiction<br />
<br />
Section 1 All matters of concern to the school community are appropriate for consideration by the Lexington High School Senate.<br />
<br />
Section 2 Any matter formulated as a bill and passed by the Senate in accordance with the provisions of Article VII, Section 4, shall be submitted to the administration in accordance with Article VII, Section 4, unless any portion of the bill:<br />
<br />
A. Contradicts state or federal law;<br />
B. Interferes with the allotment of school department funds;<br />
<br />
C. Interferes with collective bargaining agreements;<br />
<br />
D. Impinges upon individual administrative and teacher evaluation;<br />
<br />
E. Impinges upon individual teachers' course organization and evaluation of students.<br />
<br />
<br />
Article VII: Procedures<br />
<br />
Section 1 The Lexington High School Senate shall operate as a representative town meeting.<br />
<br />
Section 2 The Lexington High School Senate shall employ Robert's Rules of Order Newly Revised as the parliamentary reference for its deliberations.<br />
<br />
Section 3 For the transaction of business to occur within the Senate, a quorum of two-thirds of the Senate shall be required.<br />
<br />
Section 4 Voting Procedures with respect to bills<br />
<br />
A. Bills must have been submitted to the secretary at least five school days before a Senate meeting at which the bill may be considered.<br />
B. Bills must have been published at least four school days before a Senate meeting day at which the bill may be considered.<br />
<br />
C. By a two-thirds vote of those members present and voting, the Senate may consider a late-filed bill.<br />
<br />
D. The Senate shall establish standing rules for the receipt and publication of bills.<br />
<br />
E. The executive committee shall place a bill on the agenda or assign the bill to a standing committee of the Senate for research, discussion, and recommendation of the Senate.<br />
<br />
F. Majority of the Senate present and voting shall be required to pass a bill.<br />
<br />
G. Following an affirmative Senate vote on a bill:<br />
<br />
i. The principal may give his written approval to the bill, in which case the bill shall take effect.<br />
ii. The principal may decline to approve the bill, offer his objections to the same in writing, and then return the bill to the Senate.<br />
<br />
iii. The Senate may accept the principal's disapproval and the bill is then lost, or Senate may reinstitute the bill by a three-fourths majority of the members present and voting.<br />
<br />
iv. If the Senate votes to reinstitute, the Secretary shall transmit the bill to the Lexington School Committee. After ten school days and in the absence of a recorded vote of the School Committee, the bill shall take effect.<br />
<br />
v. If the principal allows a bill to remain on his desk for ten school days without a response, the bill should take effect.<br />
<br />
<br />
Article VIII: Meetings<br />
<br />
Section 1 The Senate shall meet once each week when school is in session.<br />
<br />
Section 2 All meetings of the Senate are open.<br />
<br />
Section 3 Exclusivity of Senate meeting times.<br />
<br />
A.The Senate shall meet once each week at a designated and specific time during normal school hours.<br />
B. This time shall be reserved by the entire Lexington High School community exclusively for Senate meetings.<br />
<br />
C. The scheduling of practices, rehearsals, and other required meetings is strictly prohibited during Senate meeting time.<br />
<br />
D. Senate meetings shall in no way impinge upon or interfere with regular class meeting times.<br />
<br />
E. No teacher shall be assigned any involuntary professional duty while the Senate is in session.<br />
<br />
Section 4 Each spring the Senate shall evaluate its meeting time and establish specific meeting times for the next school year.<br />
<br />
<br />
Article IX: Senate Attendance<br />
<br />
Dismissal and reinstatement of Senate members<br />
<br />
A.The secretary shall certify the attendance of members at Senate meetings and shall excuse the absence of members for good cause. After December 1, any member whose unexcused absences from Senate meetings shall amount to twenty percent of the total number of Senate meetings since the beginning of the school year shall be deemed to have resigned, and a vacancy shall be declared by the secretary.<br />
B.Within five days following such declaration, the former member may request a hearing before the standing committee on elections.<br />
<br />
C.Following such a hearing the standing committee on elections may reinstate the former Senate member.<br />
<br />
D. If five days elapse without a request for a hearing, or if the standing committee on elections does not reinstate the former Senate member, then the procedures established under Article X for filling vacancies shall take effect.<br />
<br />
<br />
Article X: Senate Vacancies<br />
<br />
Section 1 When any seat in the Senate is declared vacant, the seat shall be filled by the candidate who represents the constituency of the vacated seat and who attained the next highest number of votes in the most recent Senate elections for that seat.<br />
<br />
Section 2 When any office in the Senate is permanently vacated, a successor shall be elected by and from the Senate to serve the unexpired term in accordance with Article IV, Section 2.<br />
<br />
<br />
Article XI: School Elections<br />
<br />
The standing committee on elections, authorized under Article III, Section 2, shall conduct all school elections.<br />
<br />
<br />
Article XII: Bill of Rights<br />
<br />
The Senate shall support and defend the following rights of all members of the school community:<br />
<br />
A. To express freely and peaceably, in speech and in writing, opinions and ideas;<br />
B. To distribute printed materials on school grounds before school, during school, and after school hours;<br />
<br />
C. To assemble freely and peaceably in any manner, before school, during school, and after school, so long as such gatherings do disrupt the educational process;<br />
<br />
D. To defend against an accusation before any discipline, suspension, expulsion, termination, or other major action may occur;<br />
<br />
E. To petition for redress of grievances;<br />
<br />
F. To be free from physical and verbal harassment.<br />
<br />
<br />
Article XIII: Board of Appeals<br />
<br />
Section 1 A board of appeals shall be organized to address student and teacher grievances that arise from Lexington High School policies, rules, regulations, and procedures.<br />
<br />
Section 2 The board of appeals shall consist of student and faculty members in the same proportion as the representatives in the whole Senate. Student and faculty members shall be elected by and from their respective constituencies. No person may serve simultaneously as a member of the Senate and of the board of appeals.<br />
<br />
Section 3 The Senate shall establish procedures and rules for the operation of the board of appeals.<br />
<br />
<br />
Article XIV: Amendments<br />
<br />
Section 1 Amendments to this Constitution may be proposed by a two-thirds majority of the Senate members present and voting.<br />
<br />
Section 2 Amendments to this constitution shall take effect after ratification in separate elections by a majority vote of students and by a majority vote of faculty.<br />
<br />
<br />
Appendix to the Constitution Clarifying Article VIII, Section 3<br />
<br />
In order to implement Article VIII, Section 3 of the Constitution, the following regulations and procedures shall be adopted for the Lexington High School Community:<br />
<br />
A. The weekly school schedule shall be arranged so that on one designated day every week, for the purpose of Senate meetings, school shall end officially one hour earlier than on other days.<br />
B. All students and faculty not participating in the Senate deliberations shall be dismissed at that time.<br />
<br />
C. During this Senate meeting period, school shall have been terminated for the day; hence, there shall be no classes in session and no supervision of non-Senate member students by the faculty.<br />
<br />
D. This arrangement shall not decrease the amount of classroom time currently scheduled.<br />
<br />
E. No student or faculty member participating in Senate deliberations shall be penalized in any way for not participating in athletic, dramatic, debate, or club activities during the time designated for Senate meetings.<br /></div>'''.encode('utf8'))
        self.wfile.write('''<h2><a name='bills'>Senate Bills</a></h2>'''.encode('utf8'))
        self.wfile.write('''<h2><a name='minutes'>Minutes</a></h2>'''.encode('utf8'))
        self.wfile.write('''<h2><a name='attendance'>Senator Attendance</a></h2>'''.encode('utf8'))
        self.wfile.write('''<h2><a name='FAQ'>Frequently Asked Questions</a></h2>
When and where does the Senate meet?<br />
The Senate meets every Wednesday afternoon after school in the Library Media Center.<br />
<br />
What happened to X-Block?<br />
X-Block was originally created as a time for Senate to meet. The Department of Education has found that X-Block did not engage the time of a sufficient number of students to be counted as a Time and Learning hour. The school will be discussing how to restore X-Block to the schedule this year (2014-2015).<br />
<br />
Are Senate meetings open to those who aren't members?<br />
Yes. Anyone who wishes to attend a senate meeting may do so.<br />
<br />
How many Senators are there?<br />
There are up to 10 faculty senators, along with approximately 10 student senators elected per grade. See the Constitution for details.<br />
<br />
What are Senate Committees?<br />
Each senator is assigned to a Committee at the beginning of the year. There are 6 committees: Executive, Community Service, Oversight, Climate, Policy, and Communications. Each committee meets once a week outside of the Senate meeting.'''.encode('utf8'))
        self.wfile.write('</article></body></html>'.encode('utf8'))
        self.log_activity()
        
    def submit_opinion(self, start_response=True):
        url_arguments = urllib.parse.parse_qs(self.query_string)
        my_account = self.identify_user()
        if 'opinion_text' in url_arguments and not my_account == False:
            opinion_text = url_arguments['opinion_text'][0]
            opinion_ID = len(db.opinions_database)
            assert str(opinion_ID) not in db.opinions_database
            def update_opinions_database():
                db.opinions_database[str(opinion_ID)] = updown.Opinion(opinion_ID, opinion_text, [(my_account.user_ID, datetime.datetime.now())])
            self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)
            search_index_add_opinion(db.opinions_database[str(opinion_ID)])
            if start_response:
                self.start_response('200 OK', [])
            self.log_activity([opinion_ID])
        else:
            raise ValueError(f'ip {self.client_address[0]} -- submit opinion function got url arguments {url_arguments}')

    def vote(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if 'opinion_ID' in url_arguments and 'my_vote' in url_arguments:
            opinion_ID = url_arguments['opinion_ID'][0]
            my_vote = url_arguments['my_vote'][0]
            if opinion_ID in db.opinions_database and my_vote in ('up', 'down', 'abstain'):
                if opinion_ID in my_account.votes:
                    my_account.votes[opinion_ID].append((my_vote, datetime.datetime.now()))
                else:
                    my_account.votes[opinion_ID] = [(my_vote, datetime.datetime.now())]
                see_day = None
                today_date = datetime.date.today()
                if (today_date.weekday() + 1) % 7 < 3:
                    see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7)
                elif (today_date.weekday() + 1) % 7 > 3:
                    see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7 - 4)
                else:
                    see_day = today_date

                #for other_opinion_ID in db.opinions_calendar[str(today_date - datetime.timedelta((today_date.weekday() + 1) % 7 % 4))]:
                for other_opinion_ID in db.opinions_calendar[str(see_day)]:
                    if other_opinion_ID != opinion_ID and other_opinion_ID not in my_account.votes:
                        my_account.votes[other_opinion_ID] = [('abstain', datetime.datetime.now())]

                def update_user_cookies():
                    db.user_ids[my_account.user_ID] = my_account
                self.run_and_sync(db.user_ids_lock, update_user_cookies, db.user_ids)

                self.start_response('200 OK', [])
                if MyWSGIHandler.DEBUG < 2:
                    print(f'{my_account.email} has voted {my_vote}')

                self.log_activity([my_vote, opinion_ID])
            else:
                raise ValueError(f'ip {self.client_address[0]} -- vote function got opinion ID {opinion_ID} and vote {my_vote}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- vote function got url arguments {url_arguments}')

    def approve(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_result == True:
            url_arguments = urllib.parse.parse_qs(self.query_string)
            if 'opinion_ID' in url_arguments and 'my_vote' in url_arguments:
                opinion_ID = url_arguments['opinion_ID'][0]
                my_vote = url_arguments['my_vote'][0]
                if opinion_ID in db.opinions_database and my_vote in ('yes', 'no'):
                    # update databases
                    opinion = db.opinions_database[opinion_ID]
                    if len(opinion.activity) == 1:
                        opinion.activity.append([(my_account.email, my_vote, datetime.datetime.now())])
                        if my_vote == 'yes':
                            opinion.approved = True
                        else:
                            opinion.approved = False
                    else:
                        opinion.activity[1].append((my_account.email, my_vote, datetime.datetime.now()))

                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

                    def update_user_cookies():
                        db.user_ids[my_account.user_ID] = my_account
                    self.run_and_sync(db.user_ids_lock, update_user_cookies, db.user_ids)

                    self.start_response('200 OK', [])
                    
                    self.log_activity([my_vote, opinion_ID])
                    
                else:
                    raise ValueError(f'ip {self.client_address[0]} -- approval function got opinion ID {opinion_ID} and vote {my_vote}')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- approval function got url arguments {url_arguments}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- approval function got user {user.email}, who is not a moderator.')

    def schedule_opinions_page(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        see_month_str = url_arguments.get('month', [datetime.date.today().strftime('%Y-%m')])[0]
        if my_account.email in local.ADMINS and my_account.verified_result == True:
            self.start_response('200 OK', [])
            self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
            self.send_links_head()
            self.wfile.write('''
<style>
form {
  position: absolute;
  top: 70px;
  width: 100%;
  text-align: center;
  height: 130px;
}
input {
  position: relative;
  top: 35px;
  width: 40%;
  height: 40px;
}
article {
  position: absolute;
  top: 200px;
  width: 100%;
  bottom: 0;
  z-index: 1;
  overflow: scroll;
}
table {
  position: absolute;
  left: 2%;
  width: 96%;
  padding: 3%;
  box-sizing: border-box;
  border: 1px solid black;
  border-radius: 12px;
  background-color: gray;
}
td {
  border-color : black;
  border-style : solid;
  border-width : 2px;
  border-radius: 6px;
  padding : 5px;
  width : 80px;
  background-color: lightGray;
}
div#popup {
  position: absolute;
  top: 100px;
  bottom: 30px;
  width: 90%;
  left: 5%;
  background-color: grey;
  border: 3px solid black;
  border-radius: 15px;
  z-index: 2;
  display: none;
}
div#count {
  position: absolute;
  top: 0;
  width: 70%;
  left: 15%;
  height: 30px;
  font-size: 25px;
  text-align: center;
  border: 2px solid black;
  border-top: 0;
  background-color: #ffef90ff;
}
div#x {
  position: absolute;
  padding: 3px;
  top: 12px;
  right: 12px;
  border: 1px dotted black;
}
div#selected {
  position: absolute;
  top: 50px;
  bottom: 50%;
  width: 96%;
  left: 2%;
  overflow: scroll;
}
#selected section {
  width: 98%;
  margin: 1%;
  margin-bottom: 4%;
  padding: 3%;
  position: relative;
  background-color: #ffef90ff;
  z-index: 1;
  border-radius: 6px;
  box-sizing: border-box;
}
div#results {
  position: absolute;
  top: 50%;
  bottom: 0;
  width: 96%;
  left: 2%;
  overflow: scroll;
}
#results section {
  width: 98%;
  margin: 1%;
  margin-bottom: 4%;
  padding: 3%;
  position: relative;
  background-color: #cfe2f3ff;
  z-index: 1;
  border-radius: 6px;
  box-sizing: border-box;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write('''<div id='popup'>
<div id='count'>
9/10 selected
</div>
<div id='x' onclick='close_pop()'>
X
</div>
<div id='selected'>
</div>
<div id='results'>
</div>
</div>'''.encode('utf8'))
            self.wfile.write(f'''<form method='GET' action='/schedule_opinions'>
<input type='month' name='month' value='{see_month_str}'/>
<input type='submit'/>
</form>'''.encode('utf8'))
            self.wfile.write('''<article>
<table>
<tr>'''.encode('utf8'))
            for day_of_week in range(7):
                self.wfile.write(f'''<td style='background-color: lightBlue; text-align: center'>{calendar.day_name[(day_of_week + 6) % 7][:3]}</td>'''.encode('utf8'))

            see_month = datetime.datetime.strptime(see_month_str, '%Y-%m')
            month_first = datetime.date(year=see_month.year, month=see_month.month, day=1)
            month_last_day_num = calendar.monthrange(see_month.year, see_month.month)[1]
            month_last = datetime.date(year=see_month.year, month=see_month.month, day=month_last_day_num)
            cal_first = month_first - datetime.timedelta(days=(month_first.weekday() + 1) % 7)
            see_sun = cal_first
            while see_sun <= month_last:
                # 3 first
                self.wfile.write(f'''<tr><td colspan='3' onclick='open_pop("{see_sun}")'>'''.encode('utf8'))
                day_nums = []
                already_selected = len(db.opinions_calendar.get(str(see_sun), set()))
                for day_num in range(3):
                    day_nums.append((see_sun + datetime.timedelta(days=day_num)).day)
                self.wfile.write(str(day_nums)[1:-1].encode('utf8'))
                self.wfile.write(f'''<br />{already_selected}/10</td>'''.encode('utf8'))

                # wed middle
                already_selected = len(db.opinions_calendar.get(str(see_sun + datetime.timedelta(days=3)), set()))
                self.wfile.write(f'''<td onclick='open_pop("{see_sun + datetime.timedelta(days=3)}")'>{(see_sun + datetime.timedelta(days=3)).day}<br />{already_selected}/10</td>'''.encode('utf8'))

                # 3 last
                see_thurs = see_sun + datetime.timedelta(days=4)
                self.wfile.write(f'''<td colspan='3' onclick='open_pop("{see_thurs}")'>'''.encode('utf8'))
                day_nums = []
                already_selected = len(db.opinions_calendar.get(str(see_thurs), set()))
                for day_num in range(3):
                    day_nums.append((see_thurs + datetime.timedelta(days=day_num)).day)
                self.wfile.write(str(day_nums)[1:-1].encode('utf8'))
                self.wfile.write(f'''<br />{already_selected}/10</td>'''.encode('utf8'))
                self.wfile.write('</tr>'.encode('utf8'))
                see_sun += datetime.timedelta(days=7)
                
            # today_date = datetime.date.today()
            # this_sun = today_date 
            
            # self.wfile.write('</tr><tr>'.encode('utf8'))
            # first_day = calendar.monthrange(today_date.year, today_date.month)[0]
            # month_days = calendar.monthrange(today_date.year, today_date.month)[1]
            # self.wfile.write(f'''<td colspan='{(first_day + 1) % 7}'></td>'''.encode('utf8'))
            # for day_number in range(1, month_days + 1):
            #     this_date = datetime.date(today_date.year, today_date.month, day_number)
            #     already_selected = 0
            #     if str(this_date) in db.opinions_calendar:
            #         already_selected = len(db.opinions_calendar[str(this_date)])
            #     if (this_date.weekday() + 1) % 7 == 0 and not day_number == 1:
            #         self.wfile.write('</tr>'.encode('utf8'))
            #         if not day_number == month_days:
            #             self.wfile.write('<tr>'.encode('utf8'))
            #     if day_number == 1:
            #         self.wfile.write(f'''<td onclick='document.location.href="/schedule_date?date={this_date - datetime.timedelta((this_date.weekday() + 1) % 7 % 4)}"' colspan='{3 - ((this_date.weekday() + 1) % 7) % 4}'>{day_number}-{first_day}<br />{already_selected}/10</td>'''.encode('utf8'))
            #     if ((this_date.weekday() + 1) % 7) % 4 == 0:
            #         if day_number + 3 > month_days:
            #             self.wfile.write(f'''<td onclick='document.location.href="/schedule_date?date={this_date}"' colspan='{month_days - day_number}'>{day_number}-{month_days}<br />{already_selected}/10</td>'''.encode('utf8'))
            #         else:
            #             self.wfile.write(f'''<td onclick='document.location.href="/schedule_date?date={this_date}"' colspan='3'>{day_number}, {day_number + 1}, {day_number + 2}<br />{already_selected}/10</td>'''.encode('utf8'))
            #     elif this_date.weekday() == 2:
            #         self.wfile.write(f'''<td onclick='document.location.href="/schedule_date?date={this_date}"'>{day_number}<br />{already_selected}/10</td>'''.encode('utf8'))                        
            # for day in range(35 - month_days - (first_day + 1) % 7):
            #     self.wfile.write('<td></td>'.encode('utf8'))
            # self.wfile.write('</tr>'.encode('utf8'))
            
            self.wfile.write('</table></article>'.encode('utf8'))
            self.wfile.write('''<script>
function open_pop(d_str) {
    var xhttp = new XMLHttpRequest();
    xhttp.open('GET', '/already_scheduled?date=' + d_str);
    xhttp.send();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var response = JSON.parse(this.responseText);
            let scheduled = response[0];
            let unscheduled = response[1];
            let scheduled_cont = document.getElementById('selected');
            let unscheduled_cont = document.getElementById('results');
            scheduled_cont.innerHTML = '';
            for (var index = 0; index < scheduled.length; index++) {
                scheduled_cont.innerHTML += '<section onclick="unselect(this)" id="' + scheduled[index][0] + '">' + scheduled[index][1] + '</section>';
            }
            unscheduled_cont.innerHTML = '';
            for (var index = 0; index < unscheduled.length; index++) {
                unscheduled_cont.innerHTML += '<section onclick="select(this)" id="' + unscheduled[index][0] + '">' + unscheduled[index][1] + '</section>';
            }
            document.getElementById('popup').style.display = 'initial';
       };
    }
 }
function close_pop() {
    document.getElementById('popup').style.display = 'none';
}
</script>'''.encode('utf8'))
            self.wfile.write('</body></html>'.encode('utf8'))

            self.log_activity()
            
        else:
            raise ValueError(f'ip {self.client_address[0]} -- schedule_opinions function got user {user.email}, who is not an admin.')

    def schedule_date_page(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_result == True:
            url_arguments = urllib.parse.parse_qs(self.query_string)
            if 'date' in url_arguments:
                this_date = url_arguments["date"][0]
                try:
                    datetime.datetime.strptime(this_date, '%Y-%m-%d')
                except ValueError:
                    raise ValueError(e + f'ip {self.client_address[0]} -- schedule date function got date {url_arguments["date"][0]}')
                self.start_response('200 OK', [])
                self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
                self.send_links_head()
                self.wfile.write('''
<style>
article {
  position: absolute;
  top: 50px;
  width: 100%;
  height: 91%;
  z-index: 1;
  overflow: scroll;
}
table {
  border-collapse : collapse;
}
td {
  border-style : solid;
  border-width : 2px;
  border-color : black;
  width : 300px;
  padding : 3px;
}
</style>
</head>
<body>'''.encode('utf8'))
                self.send_links_body()
                self.wfile.write('''
<article>
<table>
<tr>
<td>
<table id='unselected'>'''.encode('utf8'))
                for opinion_ID, opinion in db.opinions_database.items():
                    if opinion.approved == True and not opinion.scheduled:
                        self.wfile.write(f'''<tr>
<td id='{opinion_ID}' onclick='handleClick(this);'>
{opinion.text} -- id {opinion_ID}
</td>
</tr>'''.encode('utf8'))
                self.wfile.write('</table></td><td>'.encode('utf8'))
                self.wfile.write('''<table id='selected'>'''.encode('utf8'))
                selected = set()
                if this_date in db.opinions_calendar:
                    selected = db.opinions_calendar[str(this_date)]
                    for opinion_ID in db.opinions_calendar[this_date]:
                        assert opinion_ID in db.opinions_database
                        opinion = db.opinions_database[opinion_ID]
                        self.wfile.write(f'''<tr >
<td id='{opinion_ID}' onclick='handleClick(this);'>
{opinion.text} -- id {opinion_ID}
</td>
</tr>'''.encode('utf8'))
                    #for blank in range(10 - len(db.opinions_calendar[this_date])):
                        #self.wfile.write('<tr><td><br /></td></tr>'.encode('utf8'))
                #else:
                    #for blank in range(10):
                        #self.wfile.write('<tr><td><br /></td></tr>'.encode('utf8'))
                self.wfile.write('</table>'.encode('utf8'))
                self.wfile.write('</td></tr></table></article>'.encode('utf8'))
                self.wfile.write(f'''<script>
const this_date = '{this_date}';
let selected = {list(selected)};
function handleClick(element) {{
    console.log('original selected: ' + selected);
    if (selected.indexOf(element.id) != -1) {{
        unschedule(element);
        update_unselected(element);
    }}
    else {{
        schedule(element);
        update_selected(element);
    }}
    console.log('end selected: ' + selected);
}}
function schedule(element) {{
    var xhttp = new XMLHttpRequest();
    xhttp.open('GET', '/schedule?date=' + this_date + '&opinion_ID=' + element.id, true);
    xhttp.send();
}}
function unschedule(element) {{
    var xhttp = new XMLHttpRequest();
    xhttp.open('GET', '/unschedule?date=' + this_date + '&opinion_ID=' + element.id, true);
    xhttp.send();
}}
function update_selected(element) {{
    selected.push(element.id);
    new_tr = document.createElement('tr');
    new_td = document.createElement('td');
    new_tr.appendChild(new_td);
    new_td.innerHTML = element.innerHTML;
    new_td.onclick = 'handleClick(this);';
    new_td.id = element.id;
    document.getElementById('selected').appendChild(new_tr);
    element.style = 'display: none;';
}}
function update_unselected(element) {{
    selected.splice(selected.indexOf(element.id), 1);
    new_tr = document.createElement('tr');
    new_td = document.createElement('td');
    new_tr.appendChild(new_td);
    new_td.innerHTML = element.innerHTML;
    new_td.onclick = 'handleClick(this);';
    new_td.id = element.id;
    document.getElementById('unselected').appendChild(new_tr);
    element.style = 'display: none;';
}}
</script>'''.encode('utf8'))
                self.wfile.write('</body></html>'.encode('utf8'))

                self.log_activity([this_date])
                
            else:
                raise ValueError(f'ip {self.client_address[0]} -- schedule date function got url arguments {url_arguments}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- schedule date function got user {user.email}, who is not an admin.')

    def schedule(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_result == True:
            url_arguments = urllib.parse.parse_qs(self.query_string)
            if 'date' in url_arguments and 'opinion_ID' in url_arguments:
                this_date = url_arguments["date"][0]
                opinion_ID = url_arguments['opinion_ID'][0]
                try:
                    datetime.datetime.strptime(this_date, '%Y-%m-%d')
                except ValueError:
                    raise ValueError(f'ip {self.client_address[0]} -- schedule function got date {url_arguments["date"][0]}')
                if opinion_ID in db.opinions_database:
                    opinion = db.opinions_database[opinion_ID]
                    opinion.scheduled = True
                    if len(opinion.activity) == 2:
                        opinion.activity.append([(my_account.email, True, datetime.datetime.strptime(this_date, '%Y-%m-%d').date(), datetime.datetime.now())])
                    else:
                        opinion.activity[2].append((my_account.email, True, datetime.datetime.strptime(this_date, '%Y-%m-%d').date(), datetime.datetime.now()))

                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

                    selected = set()
                    if this_date in db.opinions_calendar:
                        selected = db.opinions_calendar[this_date]
                    if MyWSGIHandler.DEBUG < 2:
                        print(f'selected originally: {selected}')
                    selected.add(opinion_ID)
                    if MyWSGIHandler.DEBUG < 2:
                        print(f'selected after: {selected}')
                        
                    def update_opinions_calendar():
                        db.opinions_calendar[this_date] = selected
                    self.run_and_sync(db.opinions_calendar_lock, update_opinions_calendar, db.opinions_calendar)
                    
                    self.start_response('200 OK', [])

                    self.log_activity([this_date, opinion_ID])
                    
                else:
                    raise ValueError(f'ip {self.client_address[0]} -- schedule function got opinion ID {opinion_ID}, not in the database')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- schedule function got url arguments {url_arguments}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- schedule date function got user {user.email}, who is not an admin.')

    def unschedule(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_result == True:
            url_arguments = urllib.parse.parse_qs(self.query_string)
            if 'date' in url_arguments and 'opinion_ID' in url_arguments:
                this_date = url_arguments["date"][0]
                opinion_ID = url_arguments['opinion_ID'][0]
                try:
                    datetime.datetime.strptime(this_date, '%Y-%m-%d')
                except ValueError:
                    raise ValueError(f'ip {self.client_address[0]} -- schedule function got date {url_arguments["date"][0]}')
                if opinion_ID in db.opinions_database:
                    opinion = db.opinions_database[opinion_ID]
                    opinion.scheduled = False
                    assert len(opinion.activity) == 3, f'{len(opinion.activity)}'
                    opinion.activity[2].append((my_account.email, False, datetime.datetime.strptime(this_date, '%Y-%m-%d'), datetime.datetime.now()))

                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

                    selected = set()
                    if this_date in db.opinions_calendar:
                        selected = db.opinions_calendar[this_date]
                    if MyWSGIHandler.DEBUG < 2:
                        print(f'selected originally: {selected}')
                    selected.remove(opinion_ID)
                    if MyWSGIHandler.DEBUG < 2:
                        print(f'selected after: {selected}')

                    def update_opinions_calendar():
                        db.opinions_calendar[this_date] = selected
                    self.run_and_sync(db.opinions_calendar_lock, update_opinions_calendar, db.opinions_calendar)

                    self.start_response('200 OK', [])

                    self.log_activity([this_date, opinion_ID])
                    
                else:
                    raise ValueError(f'ip {self.client_address[0]} -- unschedule function got opinion ID {opinion_ID}, not in the database')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- unschedule function got url arguments {url_arguments}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- unschedule date function got user {user.email}, who is not an admin.')
        
    def track_opinions_page(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        self.start_response('200 OK', [])
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
article {
  position: absolute;
  top: 70px;
  width: 100%;
  bottom: 50%;
  z-index: 1;
  overflow: scroll;
}
footer {
  position: fixed;
  bottom: 0;
  width: 100%;
  height: 50%;
  z-index: 1;
}
#search_bar {
  position: absolute;
  top: 0;
  left: 1%;
  width: 98%;
  height: 26px;
  padding: 2px;
  border: 0;
}
div#results {
  position: absolute;
  bottom: 0;
  top: 32px;
  width: 100%;
  overflow: scroll;
}
div.result {
  width: 99%;
  height: 50px;
  margin: 0.5%;
  position: relative;
  background-color: #cfe2f3ff;
  z-index: 1;
  border-radius: 6px;
}
img#timeline {
  height: 90%;
  position: absolute;
  left: 8%;
  top: 5%;
}
table#stats {
  width: 60%;
  right: 2%;
  position: absolute;
  height: 80%;
  top: 10%;
  font-size: 40px;
  text-align: center;
  border-collapse: collapse;
}
div#line {
  width: 30px;
  height: 4px;
  border: 2px solid black;
  position: absolute;
  left: 6%;
  background-color: green;
  box-sizing: border-box;
}
div#label {
  font-size: 20px;
  position: absolute;
  left: 17%;
}
td.care {
  border-right: 2px solid black;
  width: 50%;
}
td.up {
  border-left: 2px solid black;
}
td#row1 {
  font-size: 20px;
}
td#row4 {
  font-size: 25px;
}
</style>'''.encode('utf8'))
        self.wfile.write('</head><body>'.encode('utf8'))
        self.send_links_body()
        self.wfile.write('<article>'.encode('utf8'))
        self.wfile.write('''<img src='timeline.png' id='timeline'/><div id='line'></div><div id='label'></div>'''.encode('utf8'))
        self.wfile.write('''<table id='stats'>
<tr><td id='row1' colspan='2'></td></tr>
<tr><td id='care_per' class='care'></td><td id='up_per' class='up'></td></tr>
<tr><td class='care'>care</td><td class='up'>agree</td></tr>
<tr><td id='row4' colspan='2'></td></tr>
</table>'''.encode('utf8'))
        self.wfile.write('</article>'.encode('utf8'))
        self.wfile.write(f'''<footer><form method='GET' action='/track_opinions'><input id='search_bar' type='text' name='words' value='{url_arguments.get('words', [''])[0]}' placeholder='search...'/></form><div id='results'>'''.encode('utf8'))

        def to_date(dt):
            return datetime.date(dt.year, dt.month, dt.day)

        json_stats = {}
        search_results = []
        if 'words' in url_arguments:
            search_results = search(url_arguments['words'][0])
        else:
            search_results = list(db.opinions_database.keys())
            search_results.sort(key=lambda x: -int(x))
        if search_results == []:
            self.wfile.write('Sorry, there were no results. Try using different keywords.'.encode('utf8'))
        for opinion_ID in search_results:
            json_stats[opinion_ID] = [None] * 6
            # label, stage, date, care, up, message
            opinion = db.opinions_database[str(opinion_ID)]
            # timeline: creation, approval, scheduled (vote), successful (passed to senate), expected bill draft date, date of senate hearing
            # timeline: creation, approval, scheduled (vote), unsuccessful (failed)
            json_stats[opinion_ID][1] = len(opinion.activity) - 1
            if json_stats[opinion_ID][1] >= 2:
                if datetime.date.today() >= opinion.activity[2][0][0]:
                    json_stats[opinion_ID][1] += 1
            if len(opinion.activity) == 1:
                json_stats[opinion_ID][2] = str(to_date(opinion.activity[0][1]))
                json_stats[opinion_ID][5] = 'onto approval'
                json_stats[opinion_ID][0] = 'created'
            elif len(opinion.activity) == 2:
                json_stats[opinion_ID][2] = str(to_date(opinion.activity[1][0][2]))
                assert opinion.approved in (True, False)
                if opinion.approved:
                    json_stats[opinion_ID][5] = 'onto scheduling'
                else:
                    json_stats[opinion_ID][5] = 'rejected'
                json_stats[opinion_ID][0] = 'approved'
            elif len(opinion.activity) == 3:
                #assert len(opinion.activity[2]) == 4
                if datetime.date.today() < opinion.activity[2][0][0]:
                    json_stats[opinion_ID][5] = 'onto voting'
                    json_stats[opinion_ID][0] = 'scheduled'
                elif datetime.date.today() > opinion.activity[2][0][0]:
                    json_stats[opinion_ID][5] = 'onto forwarding' 
                    json_stats[opinion_ID][0] = 'voted on'
                else:
                    json_stats[opinion_ID][5] = 'currently voting'
                    json_stats[opinion_ID][0] = 'voting'
                if datetime.date.today() >= opinion.activity[2][0][0]:
                    json_stats[opinion_ID][2] = str(to_date(opinion.activity[2][0][0]))
                else:
                    json_stats[opinion_ID][2] = str(to_date(opinion.activity[2][0][1]))
            elif len(opinion.activity) == 4:
                #assert len(opinion.activity[3]) == 3, f'{opinion.activity}'
                assert opinion.activity[3][0][1] in local.COMMITTEE_MEMBERS, f'{opinion.activity[3][1]}'
                if opinion.activity[3][0][1] != 'no':
                    json_stats[opinion_ID][5] = f'onto {opinion.activity[3][0][1]}'
                else:
                    json_stats[opinion_ID][5] = 'unforwarded'
                json_stats[opinion_ID][0] = 'forwarded'
                json_stats[opinion_ID][2] = str(to_date(opinion.activity[3][0][2]))
            # elif len(opinion.activity) == 5:
            #     #assert len(opinion.activity[4]) == 3
            #     json_stats[opinion_ID][5] = 'onto drafting'
            #     json_stats[opinion_ID][0] = ''
            #     json_stats[opinion_ID][2] = str(to_date(opinion.activity[4][0][2]))
            # care and up percent
            json_stats[opinion_ID][3] = '---'
            json_stats[opinion_ID][4] = '---'
            if json_stats[opinion_ID][1] > 2:
                up, down, abstain = opinion.count_votes()
                if up + down + abstain > 0:
                    care_per = (up + down) / (up + down + abstain) * 100
                    json_stats[opinion_ID][3] = care_per
                if up + down > 0:
                    up_per = up / (up + down) * 100
                    json_stats[opinion_ID][4] = up_per
            self.wfile.write(f'''<div id='{opinion_ID}' class='result' onclick='updateStats(this);'>
{opinion.text}
</div>'''.encode('utf8'))
        self.wfile.write('</div></footer>'.encode('utf8'))
        self.wfile.write(f'''<script>
const stats = {json.dumps(json_stats)};
var prev = null;'''.encode('utf8'))
        if len(search_results) > 0:
            self.wfile.write(f'updateStats(document.getElementById({search_results[0]}));'.encode('utf8'))
        self.wfile.write(f'''
function updateStats(element) {{
    const this_ID = element.id;
    document.getElementById('label').innerHTML = stats[this_ID][0];
    document.getElementById('row1').innerHTML = stats[this_ID][0] + ' on ' + stats[this_ID][2];
    document.getElementById('care_per').innerHTML = stats[this_ID][3] + '%';
    document.getElementById('up_per').innerHTML = stats[this_ID][4] + '%';
    document.getElementById('row4').innerHTML = stats[this_ID][5];
    document.getElementById('line').style.top = 22 + 64 * stats[this_ID][1] / 6 + '%';
    document.getElementById('label').style.top = 18 + 64 * stats[this_ID][1] / 6 + '%';
    if (prev != null) {{
        prev.style.backgroundColor = '#cfe2f3ff';
    }}
    element.style.backgroundColor = 'yellow';
    prev = element;
}}
</script>'''.encode('utf8'))
        self.wfile.write('''</body></html>'''.encode('utf8'))

        self.log_activity()
        
    def leaderboard_page(self):
        my_account = self.identify_user()
        isSenator = False
        if my_account.verified_result == True:
            for committee, members in local.COMMITTEE_MEMBERS.items():
                if my_account.email in members:
                    isSenator = True
        url_arguments = urllib.parse.parse_qs(self.query_string)
        self.start_response('200 OK', [])
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
form {
  position: absolute;
  top: 90px;
  width: 96%;
  left: 2%;
  bottom: 65%;
  border: 3px solid black;
  box-sizing: border-box;
  border-radius: 6px;
  background-color: #ffef90ff;
}
#search_bar {
  position: absolute;
  top: 10%;
  left: 4%;
  width: 92%;
  height: 40px;
  font-size: 20px;
  padding: 4px;
  padding-left: 10px;
  padding-right: 10px;
  border: 1px solid black;
  border-radius: 20px;
  box-sizing: border-box;
}
form table {
  position: absolute;
  top: 40%;
  width: 80%;
  left: 10%;
  text-align: center;
  font-size: 25px;
  font-weight: bold;
}
form td {
  width: 50%;
  padding: 5px;
}
article#results {
  position: absolute;
  bottom: 3%;
  top: 38%;
  width: 96%;
  left: 2%;
  overflow: scroll;
  border: 3px solid black;
  border-radius: 6px;
  box-sizing: border-box;
  background-color: gray;
}
table.result {
  width: 90%;
  position: relative;
  left: 5%;
  margin-top: 15px;
  margin-bottom: 15px;
  background-color: white;
  border: 1px solid black;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 18px;
  border-collapse: collapse;
}
td.rank {
  padding-left: 15px;
  padding-right: 15px;
  background-color: #ffef90ff;
  border-right: 2px solid black;
}
td.opinion {
  padding: 15px;
  width: 100%;
}
select {
  font-size: 20px;
}
article#view_popup {
  position: absolute;
  top: 90px;
  bottom: 3%;
  border: 3px solid black;
  border-radius: 6px;
  width: 96%;
  left: 2%;
  box-sizing: border-box;
  background-color: gray;
  display: none;
}
div#close_popup {
  position: absolute;
  top: 0;
  right: 0;
  padding: 3px;
  padding-right: 8px;
  font-size: 25px;
}
div#reserved_header {
  position: absolute;
  top: 0;
  width: 100%;
  padding: 5px;
  font-size: 20px;
  text-align: center;
  background-color: #ffef90ff;
  box-sizing: border-box;
  border-bottom: 2px solid black;
}
#reserved_for {
  padding: 3px;
  font-size: 18px;
  background-color: lightGray;
  border: 1px solid black;
  border-radius: 6px;
}
div#opinion_text {
  position: absolute;
  top: 40px;
  bottom: 70%;
  width: 96%;
  left: 2%;
  border: 2px solid black;
  border-radius: 12px;
  background-color: white;
}
#opinion_text p {
  position: absolute;
  margin: 0;
  top: 50%;
  left: 50%;
  margin-right: -50%;
  transform: translate(-50%, -50%);
  font-size: 25px;
  text-align: center;
}
table#development {
  position: absolute;
  top: 32%;
  width: 96%;
  left: 2%;
  text-align: center;
  font-size: 20px;
  border: 2px solid black;
  border-radius: 20px;
  background-color: #6d9eebff;
}
table#stats {
  position: absolute;
  top: 45%;
  height: 100px;
  padding: 3px;
  border: 2px solid black;
  border-radius: 20px;
  background-color: #6d9eebff;
  width: 96%;
  left: 2%;
  box-sizing: border-box;
}
td#chart_td {
  width: 65%;
}
canvas#chart {
  position: absolute;
  top: 15px;
  left: 40px;
  width: 40%;
}
div#chart_cover {
  position: absolute;
  top: 15px;
  left: 40px;
  width: 40%;
  height: 134px;
}
#chart_cover p {
  position: absolute;
  margin: 0;
  top: 50%;
  left: 50%;
  margin-right: -50%;
  transform: translate(-50%, -50%);
  font-size: 30px;
}
p.stat {
  padding: 8px;
  background-color: #ffef90ff;
  border: 1px solid black;
  border-radius: 12px;
  text-align: center;
  margin-top: 8px;
  margin-bottom: 8px;
  font-size: 18px;
}
div#similar_opinion {
  position: absolute;
  bottom: 3%;
  width: 96%;
  left: 2%;
  height: 18%;
  font-size: 20px;
  text-align: center;
  padding: 5px;
  border: 2px solid black;
  border-radius: 24px;
  box-sizing: border-box;
  background-color: #ffef90ff;
}
div#similar_text {
  position: absolute;
  bottom: 0;
  top: 30px;
  width: 100%;
  left: 0;
  text-align: center;
  font-size: 18px;
  border-top: 1px solid black;
  border-radius: 0 0 24px 24px;
  box-sizing: border-box;
  background-color: white;
}
</style>'''.encode('utf8'))
        self.wfile.write('</head><body>'.encode('utf8'))
        self.send_links_body()

        keywords = url_arguments.get('words', [''])[0]
        sort_method = url_arguments.get('sort', ['overall'])[0]
        filter_for = url_arguments.get('filter', ['no_filter'])[0]

        self.wfile.write(f'''<form method='GET' action='/leaderboard'>
<input id='search_bar' type='text' name='words' value='{keywords}' placeholder='search...'/>
<table>
<tr>
<td>
sort by<br />
<select name='sort' onchange='this.form.submit()'>
<option id='overall' value='overall'>overall</option>
<option id='care' value='care'>care</option>
<option id='agree' value='agree'>agree</option>
</select>
</td>
<td>
filter for<br />
<select name='filter' onchange='this.form.submit()'>
<option id='no_filter' value='no_filter'>no filter</option>
<option id='unreserved' value='unreserved'>unreserved</option>
<option id='unresolved' value='unresolved'>unresolved</option>
<option id='my_opinions' value='my_opinions'>my opinions</option>
</select>
</td>
</tr>
</table>
</form>
<script>
document.getElementById('{sort_method}').selected = 'selected';
document.getElementById('{filter_for}').selected = 'selected';
</script>'''.encode('utf8'))
        self.wfile.write('''<article id='results'>'''.encode('utf8'))
        results = list(db.opinions_database.keys())
        results = [db.opinions_database[str(x)] for x in results]
        results = list(filter(lambda x: x.is_after_voting(), results))
        if sort_method == 'overall':
            results.sort(key=lambda x: -1 * x.care_agree_percent()[0] * x.care_agree_percent()[1])
        elif sort_method == 'care':
            results.sort(key=lambda x: -1 * x.care_agree_percent()[0])
        elif sort_method == 'agree':
            results.sort(key=lambda x: -1 * x.care_agree_percent()[1])
        def filter_keep(opinion):
            if not is_matching(opinion.text, keywords):
                return False
            if filter_for == 'unreserved':
                return opinion.reserved_for == None
            elif filter_for == 'unresolved':
                return not opinion.resolved
            elif filter_for == 'my_opinions':
                return opinion.activity[0][0] == my_account.user_ID
            else:
                return True
        for index, opinion in enumerate(results):
            print('for loop!')
            if filter_keep(opinion):
                self.wfile.write(f'''<table id='{opinion.ID}' class='result' onclick='openpop(this);'>
<tr><td class='rank'>{index + 1}.</td><td class='opinion'>{opinion.text}</td></tr>
</table>'''.encode('utf8'))
        self.wfile.write('</article></footer>'.encode('utf8'))
        self.wfile.write(f'''<article id='view_popup'>
<div id='reserved_header'>'''.encode('utf8'))
        if isSenator:
            self.wfile.write('''reserved for <select id='reserved_for' onchange='reserve(this)'>
<option id='unreserved' value='unreserved'>unreserved</option>'''.encode('utf8'))
            for committee, members in local.COMMITTEE_MEMBERS.items():
                if my_account.email in members:
                    reserved_count = reserve_count(committee)
                    if reserved_count < 2:
                        self.wfile.write(f'''<option id='{committee}' value='{committee}'>{committee} ({reserved_count}/2)</option>'''.encode('utf8'))
                    else:
                        self.wfile.write(f'''<option id='{committee}' value='{committee}' disabled='true'>{committee} ({reserved_count}/2)</option>'''.encode('utf8'))
            self.wfile.write('</select>'.encode('utf8'))
        else:
            self.wfile.write('''reserved for <span id='reserved_for'></span>'''.encode('utf8'))
        self.wfile.write('''</div>
<div id='close_popup' onclick='closepop()'>X</div>
<div id='opinion_text'>
</div>
<table id='development'>
<tr><td id='created'>created<br />_/_/_</td><td>--></td><td id='voted'>voted<br />_/_/_</td></tr>
</table>
<table id='stats'>
<tr>
<td id='chart_td'>
<canvas id='chart'>
</canvas>
<div id='chart_cover' onclick='stepChart()'>
<p></p>
</div>
</td>
<td>
<p class='stat' id='care_stat'>80% care</p>
<p class='stat' id='agree_stat'>90% agree</p>
<p class='stat' id='overall_stat'>70% overall</p>
</td>
</tr>
</table>
<div id='similar_opinion'>
Most similar opinion:
<div id='similar_text'>
</div>
</div>
</article>'''.encode('utf8'))
        self.wfile.write('''<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
var data = {
  labels: ['care', ''],
  datasets: [
    {
      label: 'Dataset 1',
      data: [100, 0],
      backgroundColor: ['black', 'white']
    }
  ]
};
var config = {
  type: 'doughnut',
  data: data,
  options: {
    responsive: false,
    cutout: 50,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: false,
        text: 'Care',
        color: 'black',
        font: {
          size: 18
        }
      }
    }
  },
};
var myChart = null;
</script>'''.encode('utf8'))
        self.wfile.write(f'''<script>
let stepIndex = 0;
var view_opinion_id;
var response;
function openpop(element) {{
    var xhttp = new XMLHttpRequest();
    xhttp.open('GET', '/leaderboard_lookup?opinion_ID=' + element.id);
    xhttp.send();
    view_opinion_id = element.id;
    xhttp.onreadystatechange = function() {{
        if (this.readyState == 4 && this.status == 200) {{
            response = JSON.parse(this.responseText);'''.encode('utf8'))
        if not isSenator:
            self.wfile.write('''
            document.getElementById('reserved_for').innerHTML = response[0][0];'''.encode('utf8'))
        else:
            self.wfile.write('''
            document.getElementById(response[0][0]).selected = 'true';
            for (var index = 1; index < response[0].length; index++) {
                const committee_name = response[0][index][0];
                document.getElementById(committee_name).innerHTML = committee_name + ' (' + response[0][index][1] + '/2)';
            }
'''.encode('utf8'))
        self.wfile.write(f'''
            document.getElementById('opinion_text').innerHTML = '<p>' + response[1] + '</p>';
            document.getElementById('created').innerHTML = 'created<br />' + response[2];
            document.getElementById('voted').innerHTML = 'voted<br />' + response[3];
            document.getElementById('care_stat').innerHTML = response[4][0] + ' care';
            document.getElementById('agree_stat').innerHTML = response[5][0] + ' agree';
            document.getElementById('overall_stat').innerHTML = response[6][0] + ' overall';
            document.getElementById('similar_text').innerHTML = response[7][1];
            document.getElementById('view_popup').style.display = 'initial';
            stepIndex = 0;
            if (myChart == null) {{
                myChart = new Chart(document.getElementById('chart'), config);
            }}
            myChart.data.datasets[0].data = [response[4 + stepIndex][0], 100 - response[4 + stepIndex][0]];
            myChart.update();

            document.getElementById('chart_cover').innerHTML = '<p>' + response[4 + stepIndex][1] + '</p>';
        }}
    }};
}}
function stepChart() {{
    stepIndex++;
    stepIndex = stepIndex % 3;
    myChart.data.datasets[0].data = [response[4 + stepIndex][0], 100 - response[4 + stepIndex][0]];
    myChart.update();
    document.getElementById('chart_cover').innerHTML = '<p>' + response[4 + stepIndex][1] + '</p>';
}}
function closepop() {{
    document.getElementById('view_popup').style.display = 'none';
}}
</script>'''.encode('utf8'))
        if isSenator:
            self.wfile.write('''<script>
function reserve(element) {
    var xhttp = new XMLHttpRequest();
    xhttp.open('GET', '/reserve?opinion_ID=' + view_opinion_id + '&committee=' + element.value);
    xhttp.send();
}
</script>'''.encode('utf8'))
        self.wfile.write('''</body></html>'''.encode('utf8'))

        self.log_activity()
        
    def view_committee_page(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        committee = url_arguments['committee'][0]
        if committee in local.COMMITTEE_MEMBERS.keys():
            if my_account.email in local.COMMITTEE_MEMBERS[committee] and my_account.verified_result == True:
                self.start_response('200 OK', [])
                self.wfile.write(f'<!DOCTYPE HTML><html><head>'.encode('utf8'))
                self.send_links_head()
                self.wfile.write('''<style>
table#info {
  position: absolute;
  top: 80px;
  width: 100%;
  padding: 10px;
  border: 2px solid black;
  background-color: lightBlue;
  text-align: center;
  font-size: 30px;
  box-sizing: border-box;
}
#info td {
  padding: 3px;
  padding-top: 8px;
}
table#stats {
  height: 100%;
  width: 100%;
  text-align: center;
  font-size: 25px;
  box-sizing: border-box;
}
#stats td {
  width: 50%;
}
td#time_elapsed {
  font-size: 25px;
}
button#submit_bill {
  position: absolute;
  top: 45%;
  width: 98%;
  left: 1%;
  font-size: 30px;
  padding: 10px;
  border: 2px solid black;
  border-radius: 30px;
  text-align: center;
  background-color: #ffef90ff;
}
footer {
  position: absolute;
  bottom: 0;
  width: 96%;
  left: 2%;
  height: 43%;
}
div.reserved {
  width: 98%;
  margin: 1%;
  margin-bottom: 4%;
  padding: 3%;
  position: relative;
  background-color: #cfe2f3ff;
  border: 2px solid #cfe2f3ff;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 20px;
}
article#popup {
  position: absolute;
  width: 94%;
  left: 3%;
  top: 80px;
  bottom: 45%;
  background-color: #ffef90ff;
  border: 3px solid black;
  border-radius: 30px;
  box-sizing: border-box;
  display: none;
}
textarea#resolution {
  position: absolute;
  width: 94%;
  left: 3%;
  top: 3%;
  bottom: 60px;
  padding: 10px;
  font-size: 18px;
  border: 1px solid black;
  border-radius: 20px;
  box-sizing: border-box;
}
table#save {
  position: absolute;
  padding: 20px;
  bottom: 0;
  width: 100%;
  box-sizing: border-box;
}
button.savebtn {
  width: 100%;
  padding: 3px;
  box-sizing: border-box;
  font-size: 18px;
}
</style>
</head>
<body>'''.encode('utf8'))
                self.send_links_body()

                data = []
                for opinion_ID, opinion in db.opinions_database.items():
                    if opinion.reserved_for == committee and not opinion.resolved:
                        # start new list
                        data.append([opinion.ID])
                        # opinion text
                        data[-1].append(opinion.text)
                        # voted date
                        data[-1].append(opinion.activity[2][-1][0].strftime('%-m/%-d/%Y'))
                        # reserved date
                        data[-1].append(opinion.activity[3][-1][2].strftime('%-m/%-d/%Y'))
                        # voting stats
                        data[-1].append(list(opinion.care_agree_percent()))
                        # time elapsed since reservation
                        data[-1].append((datetime.datetime.today() - opinion.activity[3][-1][2]).days)
                        # resolution
                        data[-1].append(opinion.bill)
                        
                self.wfile.write('''
<table id='info'>
<tr><td id='voted'>voted<br />_/_/_</td><td id='reserved'>reserved<br />_/_/_</td></tr>
<tr><td><table id='stats'><tr><td id='care'>65%<br />care</td><td id='agree'>75%<br />agree</td></tr></table></td><td id='time_elapsed'>time elapsed:<br />2 weeks</td></tr>
</table>
<button id='submit_bill' onclick='openpop()'>UPDATE RESOLUTION</button>
<footer>'''.encode('utf8'))
                for index, opinion_info in enumerate(data):
                    self.wfile.write(f'''<div id='{opinion_info[0]}' class='reserved' onclick='updateInfo({index})'>{opinion_info[1]}</div>'''.encode('utf8'))
                self.wfile.write('</footer>'.encode('utf8'))
                self.wfile.write('''<article id='popup'>
<textarea id='resolution'></textarea>
<table id='save'>
<tr><td><button class='savebtn' onclick='editBill("no")'>SAVE AS DRAFT</button></td><td><button class='savebtn' onclick='editBill("yes")'>SAVE AS FINAL</button></td></tr>
</table>
</article>'''.encode('utf8'))
                self.wfile.write(f'''<script>
let data = {data};
var cur_index;
if (data.length > 0) {{
    updateInfo(0);
}}
function updateInfo(op_index) {{
    document.getElementById('voted').innerHTML = 'voted:<br />' + data[op_index][2];
    document.getElementById('reserved').innerHTML = 'reserved:<br />' + data[op_index][3];
    document.getElementById('care').innerHTML = data[op_index][4][0] + '%<br />care';
    document.getElementById('agree').innerHTML = data[op_index][4][1] + '%<br />agree';
    document.getElementById('time_elapsed').innerHTML = 'time elapsed:<br />' + data[op_index][5] + ' days';
    if (cur_index != null) {{
        document.getElementById(data[cur_index][0]).style.borderColor = '#cfe2f3ff';
    }}
    document.getElementById(data[op_index][0]).style.borderColor = 'black';
    cur_index = op_index;
}}
function openpop() {{
    document.getElementById('resolution').innerHTML = data[cur_index][6];
    document.getElementById('popup').style.display = 'initial';
}}
function editBill(mark_resolved) {{
    let new_bill = document.getElementById('resolution').value;
    var xhttp = new XMLHttpRequest();
    xhttp.open('GET', '/edit_bill?opinion_ID=' + data[cur_index][0] + '&bill=' + new_bill + '&mark_resolved=' + mark_resolved);
    xhttp.send();
    data[cur_index][6] = new_bill;
    if (mark_resolved == 'yes') {{
        document.getElementById(data[cur_index][0]).style.display = 'none';
    }}
    document.getElementById('popup').style.display = 'none';
}}
</script>'''.encode('utf8'))
                self.wfile.write('''</body></html>'''.encode('utf8'))
                self.log_activity()

                
    def submit_opinion_search(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if 'text' in url_arguments:
            opinions = search(url_arguments['text'][0])
            opinions_text = [db.opinions_database[str(opinion_ID)].text for opinion_ID in opinions]
            self.start_response('200 OK', [])
            self.wfile.write(json.dumps(opinions_text[:5]).encode('utf8'))
            
    def approve_opinion_search(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if 'text' in url_arguments and 'opinion_ID' in url_arguments:
            target_ID = url_arguments['opinion_ID'][0]
            opinions = search(url_arguments['text'][0])
            opinions_simplified = [db.opinions_database[str(opinion_ID)] for opinion_ID in opinions]
            opinions_simplified = filter(lambda x: str(x.ID) != target_ID, opinions_simplified)
            opinions_simplified = [x.text for x in opinions_simplified]
            self.start_response('200 OK', [])
            self.wfile.write(json.dumps(opinions_simplified[:4]).encode('utf8'))

    def already_scheduled(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_result == True:
            url_arguments = urllib.parse.parse_qs(self.query_string)
            if 'date' in url_arguments:
                see_date = url_arguments['date'][0]
                selected = db.opinions_calendar.get(see_date, set())
                selected = [(x, db.opinions_database[x].text) for x in selected]
                unselected = []
                for opinion_ID, opinion in db.opinions_database.items():
                    if opinion.approved == True and not opinion.scheduled:
                        unselected.append((opinion_ID, opinion.text))
                unselected.sort(key=lambda x: int(x[0]))
                selected = list(selected)
                unselected = [list(x) for x in unselected]
                response = [selected, unselected[:20]]
                self.start_response('200 OK', [])
                self.wfile.write(json.dumps(response).encode('utf8'))

    def handle_leaderboard_lookup(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if 'opinion_ID' in url_arguments:
            opinion_ID = url_arguments['opinion_ID'][0]
            opinion = db.opinions_database[opinion_ID]
            if opinion.is_after_voting():
                response = [[]]

                assert opinion.reserved_for in [None] + list(local.COMMITTEE_MEMBERS.keys())
                if opinion.reserved_for == None:
                    response[0].append('unreserved')
                else:
                    response[0].append(opinion.reserved_for)
                    
                # dropdown
                isSenator = False
                if my_account.verified_result == True:
                    for committee, members in local.COMMITTEE_MEMBERS.items():
                        if my_account.email in members:
                            isSenator = True
                            response[0].append((committee, reserve_count(committee)))
                            
                # text
                response.append(opinion.text)
                # creation date
                response.append(opinion.activity[0][1].strftime('%-m/%-d/%Y'))
                # voting date
                response.append(opinion.activity[2][0][0].strftime('%-m/%-d/%Y'))
                # care, agree, overall percentages and rankings
                care_p, agree_p = opinion.care_agree_percent()
                overall_p = care_p * agree_p / 100
                care_r, agree_r, overall_r = opinion.rankings()
                response.extend([[care_p, care_r], [agree_p, agree_r], [overall_p, overall_r]])
                # similar opinion
                similar_opinion_ID = list(filter(lambda x: x != opinion.ID, search(opinion.text)))[0]
                similar_opinion_text = db.opinions_database[str(similar_opinion_ID)].text
                response.append([similar_opinion_ID, similar_opinion_text])
                self.start_response('200 OK', [])
                self.wfile.write(json.dumps(response).encode('utf8'))
            else:
                self.start_response('400 BAD REQUEST', [])
        else:
            self.start_response('400 BAD REQUEST', [])
            
    def reserve(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        committee = url_arguments.get('committee', [''])[0]
        if my_account.email in local.COMMITTEE_MEMBERS.get(committee, set()):
            if reserve_count(committee) < 2:
                opinion_ID = url_arguments.get('opinion_ID', [''])[0]
                if opinion_ID != '':
                    opinion = db.opinions_database[opinion_ID]
                    if len(opinion.activity) == 3:
                        opinion.activity.append([(my_account.email, committee, datetime.datetime.now())])
                    else:
                        opinion.activity[3].append((my_account.email, committee, datetime.datetime.now()))

                    opinion.reserved_for = committee
                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

                    self.log_activity([committee, opinion_ID])
                    
                    self.start_response('200 OK', [])

    def edit_bill(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        opinion_ID = url_arguments.get('opinion_ID', [''])[0]
        new_bill = url_arguments.get('bill', [None])[0]
        mark_resolved = url_arguments.get('mark_resolved', [''])[0]
        if opinion_ID != '' and new_bill != None and mark_resolved in ('yes', 'no'):
            opinion = db.opinions_database[opinion_ID]
            if my_account.email in local.COMMITTEE_MEMBERS[opinion.reserved_for] and my_account.verified_result == True:
                opinion.bill = new_bill
                if len(opinion.activity) == 4:
                    opinion.activity.append([(my_account.user_ID, new_bill, datetime.datetime.now())])
                else:
                    opinion.activity[4].append((my_account.user_ID, new_bill, datetime.datetime.now()))
                if mark_resolved == 'yes':
                    opinion.resolved = True
                    if len(opinion.activity) == 5:
                        opinion.activity.append([(my_account.user_ID,)])
                    else:
                        opinion.activity[5].append((my_account.user_ID,))
                def update_opinions_database():
                    db.opinions_database[opinion_ID] = opinion
                self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)
                
                self.log_activity()

                self.start_response('200 OK', [])
                        

                    
class invalidCookie(ValueError):
    def __init__(self, message):
        super().__init__(message)

def simplify_text(text):
    split_text = re.split('''\W+''', text)
    if split_text[-1] == '':
        split_text = split_text[:-1]
    for index in range(len(split_text)):
        split_text[index] = split_text[index].lower()
        split_text[index] = stem(split_text[index])
    return split_text

def build_search_index():
    search_index_lock.acquire()
    for opinion_ID in range(len(db.opinions_database)):
        opinion = db.opinions_database[str(opinion_ID)]
        search_index_add_opinion(opinion)
    print(f'{SEARCH_INDEX}')

    search_index_lock.release()

def search_index_add_opinion(opinion):
    search_index_lock.acquire()
    split_text = simplify_text(opinion.text)

    print(f'{opinion.text} -- {split_text}')

    for word in split_text:
        if word in SEARCH_INDEX:
            SEARCH_INDEX[word].append(opinion.ID)
        else:
            SEARCH_INDEX[word] = [opinion.ID]
    search_index_lock.release()

def search(input_text):
    split_text = simplify_text(input_text)
    results = {}
    for word in split_text:
        if word in SEARCH_INDEX:
            matching_IDs = SEARCH_INDEX[word]
            for opinion_ID in matching_IDs:
                if opinion_ID in results:
                    results[opinion_ID] += 1
                else:
                    results[opinion_ID] = 1

    tuple_results = list(results.items())
    tuple_results.sort(key=lambda x: -x[1])
    ordered_results = [x[0] for x in tuple_results]
    
    return ordered_results

def is_matching(text1, text2):
    print(f'{(set(simplify_text(text1)) & set(simplify_text(text2))) != set()=}')
    return text1 == '' or text2 == '' or (set(simplify_text(text1)) & set(simplify_text(text2))) != set()

# poached from Lucene’s EnglishMinimalStemmer, Apache Software License v2
def stem(word):
    if word.endswith("'s"):
        word = word[:-2]
    if len(word) < 3 or word[-1] != 's':
        return word
    if word[-2] in ('u', 's'):
        return word
    if word[-2] == 'e':
        if len(word) > 3 and word[-3] == 'i' and word[-4] not in ('a', 'e'):
            word[-3] = 'y'
            return word[:-2]
        if word[-3] in ('i', 'a', 'o', 'e'):
            return word
    return word[:-1]

def thread_backup():
    while True:
        time.sleep(local.DB_SLEEP_DELAY)
        dirname = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S.new')
        with db.user_ids_lock:
            with db.cookie_database_lock:
                with db.opinions_database_lock:
                    with db.verification_links_lock:
                        with db.opinions_calendar_lock:
                            shutil.copytree(local.DIRECTORY_PATH, f'{local.BACKUP_DIRECTORY}/{dirname}')
        os.rename(f'{local.BACKUP_DIRECTORY}/{dirname}',f'{local.BACKUP_DIRECTORY}/{dirname[:-4]}')

def auto_schedule():
    while True:
        # sleep time in seconds
        time.sleep(0.5)
        see_day = None
        today_date = datetime.date.today()
        if (today_date.weekday() + 1) % 7 < 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7)
        elif (today_date.weekday() + 1) % 7 > 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7 - 4)
        else:
            see_day = today_date
        next_due_date = None
        if len(db.opinions_calendar.get(str(see_day), set())) < 10:
            next_due_date = see_day
        else:
            if (see_day.weekday() + 1) % 7 < 3:
                next_due_date = see_day + datetime.timedelta(days=4)
            else:
                next_due_date = see_day + datetime.timedelta(days=3)
            # convert next due date to datetime
        next_due_time = datetime.datetime.combine(next_due_date, datetime.datetime.min.time())
        if datetime.datetime.now() + datetime.timedelta(seconds=0.5) > next_due_time:
            ages = []
            seconds_sum = 0
            for opinion_ID, opinion in db.opinions_database.items():
                if opinion.approved == True and not opinion.scheduled:
                    creation_date = opinion.activity[0][-1]
                    seconds_passed = (datetime.datetime.now() - creation_date).total_seconds()
                    seconds_sum += seconds_passed
                    ages.append((seconds_passed, opinion_ID))
            compiled_set = db.opinions_calendar.get(str(next_due_date), set())

            if len(compiled_set) + len(ages) <= 10:
                for age_secs, opinion_ID in ages:
                    compiled_set.add(opinion_ID)
            else:
                while len(compiled_set) < 10:
                    remaining = random.random()
                    remaining *= seconds_sum
                    opinion_index = 0
                    while remaining > 0:
                        remaining -= ages[opinion_index][0]
                        opinion_index += 1
                    if ages[opinion_index - 1][1] not in compiled_set:
                        compiled_set.add(ages[opinion_index - 1][1])

            with db.opinions_calendar_lock:
                db.opinions_calendar[str(next_due_date)] = compiled_set
                db.opinions_calendar.sync()

            for opinion_ID in compiled_set:
                opinion = db.opinions_database[opinion_ID]
                if not opinion.scheduled:
                    assert len(opinion.activity) == 2
                    opinion.activity.append([(next_due_date, datetime.datetime.now())])
                    opinion.scheduled = True
                    with db.opinions_database_lock:
                        db.opinions_database[opinion_ID] = opinion
                        db.opinions_database.sync()

def reserve_count(committee):
    cur_count = 0
    for opinion_ID, opinion in db.opinions_database.items():
        if opinion.reserved_for == committee and not opinion.resolved:
            cur_count += 1
    return cur_count

def main():
    print('Student Change Web App... running...')

    if MyWSGIHandler.DEBUG == 0:
        print(f'\n{db.user_ids}')
        for this_user_ID, user in db.user_ids.items():
            print(f'  {this_user_ID} : User({user.email}, {user.user_ID}, {user.activity}, {user.votes}, {user.verified_result}, {user.obselete})')

        print(f'\n{db.cookie_database}')
        for cookie, this_user_ID in db.cookie_database.items():
            print(f'  {cookie} : {this_user_ID}')

        print(f'\n{db.verification_links}')
        for link, ID in db.verification_links.items():
            print(f'  {link} : {ID}')

        print(f'\n{db.opinions_database}')
        for ID, opinion in db.opinions_database.items():
            print(f'  {ID} : Opinion({opinion.ID}, {opinion.text}, {opinion.activity}, {opinion.approved}, {opinion.scheduled}, {opinion.reserved_for}, {opinion.bill}, {opinion.resolved})')

        print(f'\n{db.opinions_calendar}')
        sorted_calendar = list(db.opinions_calendar.keys())
        sorted_calendar.sort()
        for this_date in sorted_calendar:
            ID_set = db.opinions_calendar[this_date]
            print(f'  {this_date} : {ID_set}')


    logging.basicConfig(filename='UpDown.log', encoding='utf-8', level=logging.DEBUG)

    httpd = make_server('10.17.4.17', 8888, application)
    httpd.serve_forever()

SEARCH_INDEX = {}
search_index_lock = threading.RLock()

build_search_index()

backup_thread = threading.Thread(target=thread_backup, args=())
backup_thread.daemon = True
backup_thread.start()
print('backup thread started!')

schedule_thread = threading.Thread(target=auto_schedule, args=())
schedule_thread.daemon = True
schedule_thread.start()
print('schedule thread started!')

if __name__ == '__main__':
    main()
