import urllib.parse
import sys
import socket
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import re
import json
import uuid
import db
db.init()
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
import db_corruption
import math
import requests
from waitress import serve

def application(environ, start_response):
    for key, item in environ.items():
        print(f'{key}       {item}')
    handler_object = MyWSGIHandler(environ, start_response)
    handler_object.do_GET()
    if 'AUTH_TYPE' in environ:
        print(f'{environ["AUTH_TYPE"]}')
        
    return [handler_object.wfile.getvalue()]
    
class MyWSGIHandler(SimpleHTTPRequestHandler):

    DEBUG = 3

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
        if invalid_cookie and not self.path.startswith('/check_email') and not self.path.startswith('/email_taken') and not self.path.startswith('/verification') and self.path not in ('/favicon.ico', '/favicon.png', '/hamburger.png', '/timeline.png', '/manifest.json', '/down_stamp.png', '/up_stamp.png', '/green_icon.png', '/red_icon.png', '/gray_icon.png', '/submit_arrow.png', '/submit_button.png', '/clock.png', '/sign.png'):
            self.path_root = '/get_email'
            self.get_email()
        else:
            try:
                #self.path_root = '/'
                if self.path == '/':
                    self.opinions_page()
                elif self.path in ('/favicon.ico', '/favicon.png', '/hamburger.png', '/timeline.png', '/help.png', '/down_stamp.png', '/up_stamp.png', '/green_icon.png', '/red_icon.png', '/gray_icon.png', '/submit_arrow.png', '/submit_button.png', '/clock.png', '/sign.png'):
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
                elif self.path == '/community_service':
                    self.path_root = '/community_service'
                    self.community_service()
            except ValueError as error:
                print(str(error))
                traceback.print_exc()
                self.start_response('500 SERVER ERROR', [])
                

    def identify_user(self, nocookie=False):
        #print('identify user function called!')
        if 'code' in self.my_cookies:
            my_code = self.my_cookies['code'].value
            if my_code in db.cookie_database and db.cookie_database[my_code][1] != 'blocked':
                self.update_device_info()
                return db.user_ids[db.cookie_database[my_code][0]]
            elif nocookie:
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
                run_and_sync(db.device_info_lock, update_device_info, db.device_info, False)

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
  z-index: 4;
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
        if self.path_root in ('/leaderboard', '/community_service'):
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
#help {
  position: fixed;
  bottom: 10px;
  left: 50%;
  transform: translate(-50%, 0);
  height: 50px;
  z-index: 3;
}
#unverified_warning {
  position: fixed;
  top: 70px;
  width: 100%;
  left: 0;
  padding: 5px;
  box-sizing: border-box;
  text-align: center;
  background-color: red;
  z-index: 1;
  border-bottom: 2px solid black;
}
div.help_box {
  position: fixed;
  z-index: 4;
  left: 50%;
  transform: translate(-50%, 0);
}
div.help_text {
  position: absolute;
  border: 3px dashed black;
  border-radius: 20px;;
  padding: 12px;
  background-color: #e0e0e0;
  font-family: Helvetica, Verdana, 'Trebuchet MS', sans-serif, Arial;
  text-align: center;
}
div.help_up {
  width: 0;
  height: 0;
  border-left: 20px solid transparent;
  border-right: 20px solid transparent;
  border-bottom: 15px solid black;
  position: absolute;
  top: 0;
  left: 50%;
  transform: translate(-50%, 0);
}
div.help_down {
  width: 0;
  height: 0;
  border-left: 20px solid transparent;
  border-right: 20px solid transparent;
  border-top: 15px solid black;
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translate(-50%, 0);
}
</style>'''.encode('utf8'))
        
    def send_links_body(self):
        my_account = self.identify_user(nocookie=True)
        verified_result = 'blocked'
        if my_account != None:
            verified_result = db.cookie_database[self.my_cookies['code'].value][1]
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
                elif self.path_root == '/community_service':
                    title = 'Cmty. Service'
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
            if my_account.email in local.MODERATORS and verified_result == 'verified':
                self.wfile.write('''<a href='/approve_opinions'>Approve</a>'''.encode('utf8'))
            for committee, members in local.COMMITTEE_MEMBERS.items():
                if my_account.email in members and verified_result == 'verified':
                    self.wfile.write(f'''<a href='/view_committee?committee={committee}'>{committee}</a>'''.encode('utf8'))
            if ((my_account.email in local.BETA_TESTERS) or (my_account.email in local.COMMUNITY_SERVICE)) and verified_result == 'verified':
                self.wfile.write('''<a href='/community_service'>Cmty. Service</a>'''.encode('utf8'))
        self.wfile.write('</div>'.encode('utf8'))
        if verified_result != 'verified' and my_account != None:
            self.wfile.write('''<div id='unverified_warning'>WARNING: UNVERIFIED ACCOUNT. CLICK HERE!</div>'''.encode('utf8'))
        self.wfile.write('</header>'.encode('utf8'))
        if my_account != None:
            self.wfile.write('''<img id='help' src='help.png' onclick='manageHelp("h1")'/>'''.encode('utf8'))
        self.wfile.write('''<script>
document.addEventListener('touchstart', () => {}, false);
document.addEventListener('touchend', () => {setTimeout(clearHelp, 50)}, false);
window.addEventListener('load', () => {if (tutorial) {manageHelp('h1', true)}}, false);
let menu_is_open = false;
let open_help = null;
let just_switched = false;'''.encode('utf8'))
        if False and my_account != None and my_account.has_visited(self.path_root):
            self.wfile.write('let tutorial = false;'.encode('utf8'))
        else:
            self.wfile.write('let tutorial = true;'.encode('utf8'))
        self.wfile.write('''function open_menu() {
    menu_is_open = true;
    let menu = document.getElementById('menu').style.width = '250px';
}
function close_menu() {
    menu_is_open = false;
    document.getElementById('menu').style.width = '0';
}
function manageHelp(newId, over_tutorial = false) {
    if ((tutorial && over_tutorial) || (!tutorial)) {
        if (!menu_is_open) {
            if (open_help != null && open_help != newId) {
                document.getElementById(open_help).style.display = 'none';
            }
            if (newId != null && !just_switched) {
                document.getElementById(newId).style.display = 'initial';
                if (!tutorial) {
                    just_switched = true;
                }
            }
            open_help = newId;
        }
        else {
            if (open_help != null) {
                document.getElementById(open_help).style.display = 'none';
            }
        }
    }
}
function clearHelp() {
    if (tutorial) {
        let next = 'h' + (parseInt(open_help.slice(1)) + 1);
        if (document.getElementById(next) != null) {
            manageHelp(next, true);
            return;
        }
        else {
            tutorial = false;
        }
    }
    if (open_help != null && !just_switched) {
        document.getElementById(open_help).style.display = 'none';
        open_help = null;
    }
    just_switched = false;
}
</script>'''.encode('utf8'))

    def log_activity(self, what=[]):
        my_account = self.identify_user()
        activity_unit = [self.path_root, (self.my_cookies['code'].value, self.client_address, user_agents.parse(self.http_user_agent))] + what + [datetime.datetime.now()]
        if datetime.date.today() in my_account.activity:
            my_account.activity[datetime.date.today()].append(tuple(activity_unit))
        else:
            my_account.activity[datetime.date.today()] = [tuple(activity_unit)]

        def update_user_activity():
            db.user_ids[my_account.user_ID] = my_account
        
        run_and_sync(db.user_ids_lock,
                          update_user_activity,
                          db.user_ids)
        logging.info(f'''ip: {self.client_address[0]}; email: {my_account.email}; cookie: {self.my_cookies['code'].value}; user ID: {my_account.user_ID}; activity: {activity_unit}''')
        
    def load_image(self):
        image_type = os.path.splitext(self.path)[1][1:]
        if image_type in ('ico', 'png'):
            image_data = open(self.path[1:], 'rb').read()
            self.start_response('200 OK', [('content-type', f'image/{image_type}'), ('content-length', str(len(image_data))), ('cache-control', 'max-age=126100000')])
            self.wfile.write(image_data)

    def load_file(self):
        if self.path == '/service-worker.js':
            file_data = open(self.path[1:], 'rb').read()
            self.start_response('200 OK', [('content-type', f'text/javascript'), ('content-length', str(len(file_data)))])
            self.wfile.write(file_data)

    def handle_manifest(self):
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
    "start_url": "/",
    "background_color": "#6d9eebff",
    "theme_color": "#6d9eebff",
    "display": "standalone"
}'''
        self.start_response('200 OK', [('content-type', f'application/json'), ('content-length', str(len(manifest)))])
        self.wfile.write(manifest.encode('utf8'))

    def get_email(self):
        self.start_response('200 OK', [])
        self.wfile.write('<html><head>'.encode('utf8'))
        self.wfile.write('''<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/favicon.png">'''.encode('utf8'))
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
        YOGS = valid_yogs()
        self.wfile.write(f'''<form id='email_form' method='GET' action='/check_email'>
Enter your email to join:<br />
<input id='email' type='email' name='email' /><br />
<input id='submit' type='submit' value='I AGREE TO THE TERMS OF SERVICE' disabled='true'/>
</form>
<div id='tos'>
TERMS OF SERVICE:
</div>
<article>
UpDown uses your email to ensure that each student only votes once.<br /><br />
<!--This app was created to channel the focus of the student body. As LHS has over 2000 students, it can be hard to unify our beliefs. By uniting our preferences, we can work with the administration to bring real change to LHS.<br /><br />
Using UpDown, students submit and vote on opinions. In this way, the student body can raise issues that we care about.<br /><br />
The most popular opinions are submitted to the LHS Student-Faculty Senate, a club that negotiates with the administration to bring about change. With the student body backing the LHS Senate, we will be more unified than ever.<br /><br />-->
On UpDown, everything you do is kept anonymous. All that UpDown needs from you is your honest opinions about our school. Your name will not be tied to your votes, nor the opinions that you submit.<br /><br />
That said, everything on UpDown is moderated to ensure that opinions don't get out of hand. The privacy policy is contingent on your following LHS's Code of Conduct which outlaws bullying, cyberbullying, and hate speech. Not-safe-for-work content is also not allowed. Anything that directly violates school rules will be reported. UpDown was created for you to share constructive feedback about the school, not to complain about a particular teacher or how much you hate school.<br /><br />
</form>
</article>

<script>
const exceptionEmails = {list(local.EXCEPTION_EMAILS)};
const YOGS = {YOGS};
const re = /{local.EMAIL_MATCH_RE}/;
setTimeout(checkEmail, 1000);
function checkEmail() {{
    current_email = document.getElementById('email').value;
    if (re.test(current_email) && YOGS.indexOf(current_email[0] + current_email[1]) != -1) {{
        document.getElementById('submit').disabled = false;
    }}
    else if (exceptionEmails.indexOf(current_email) != -1) {{
        document.getElementById('submit').disabled = false;
    }}
    else {{
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
        text = f'Welcome to UpDown LHS! Use the link below to verify your devices:\n{local.DOMAIN_NAME}/verification?verification_id={v_uuid}'
        html = f'''<html>
<body>
<p>
Welcome to UpDown LHS!
<br />
<br />
Use <a href='{local.DOMAIN_PROTOCAL}{local.DOMAIN_NAME}/verification?verification_id={v_uuid}'>this link</a> to verify your devices.
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
            YOGS = valid_yogs()
            if (user_email.endswith('@lexingtonma.org') and email_grad in YOGS) or user_email in local.EXCEPTION_EMAILS:
                # create new account
                new_cookie, new_id, v_link = create_account(user_email)

                # send verification email
                self.send_email(user_email, v_link)
                expiration = None
                try:
                    expiration = calc_expiration(int(email_grad))
                except ValueError:
                    today_date = datetime.date.today()
                    expiration = datetime.date(year=today_date.year + 4, month=today_date.month, day=today_date.day)
                self.start_response('302 MOVED', [('Location', '/'), ('Set-Cookie', f'code={new_cookie}; path=/; expires={expiration.strftime("%a, %d %b %Y %H:%M:%S GMT")}')])
                self.my_cookies['code'] = new_cookie

                #redirect to homepage so they can vote
                self.log_activity()
            else:
                raise ValueError(f"ip {self.client_address[0]} -- check email function got email {user_email}")
        else:
            raise ValueError(f'ip {self.client_address[0]} -- check email function got url arguments {url_arguments}')

    def verification_page(self):
        my_account = self.identify_user(True)
        url_arguments = urllib.parse.parse_qs(self.query_string)
        verification_ID = url_arguments.get('verification_id', [None])[0]
        if verification_ID != None and verification_ID in db.verification_links:
            if my_account == None:
                # create new account
                my_email = db.verification_links[verification_ID]
                email_grad = my_email[:2]                
                new_cookie, new_id, v_link = create_account(my_email)
                # set cookie
                expiration = None
                try:
                    expiration = calc_expiration(int(email_grad))
                except ValueError:
                    today_date = datetime.date.today()
                    expiration = datetime.date(year=today_date.year + 4, month=today_date.month, day=today_date.day)
                self.start_response('200 OK', [('Set-Cookie', f'code={new_cookie}; path=/; expires={expiration.strftime("%a, %d %b %Y %H:%M:%S GMT")}')])
                self.my_cookies['code'] = new_cookie
                self.update_device_info()
            else:
                self.start_response('200 OK', [])
            # verify the device
            verify_device(self.my_cookies['code'].value)
            # handle form submission
            if len(url_arguments) > 1:
                for cookie_key, arg_list in url_arguments.items():
                    if cookie_key != 'verification_id':
                        if arg_list[0] in ('verified', 'blocked', 'unsure'):
                            if '#' in cookie_key:
                                cookie_list = cookie_key.split('#')
                                if arg_list[0] == 'verified':
                                    for cookie_k in cookie_list:
                                        verify_device(cookie_k)
                                elif arg_list[0] == 'blocked':
                                    for cookie_k in cookie_list:
                                        block_device(cookie_k)
                            else:
                                if arg_list[0] == 'verified':
                                    verify_device(cookie_key)
                                elif arg_list[0] == 'blocked':
                                    block_device(cookie_key)
            # send response
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
  top: 20px;
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
div#aggregate_ip {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translate(-50%, 0);
  font-size: 20px;
}
input#aggregate_checkbox {
  position: relative;
  width: 20px;
  height: 20px;
  top: 3px;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write(f'''<form id='form' method='GET' action='/verification'><input type='hidden' name='verification_id' value='{verification_ID}' />'''.encode('utf8'))
            my_email = db.verification_links[verification_ID]
            id_list = []
            for ID, user in db.user_ids.items():
                if user.email == my_email:
                    id_list.append(ID)
            cookie_list = []
            def last_active(cookie):
                latest = datetime.datetime.combine(local.LAUNCH_DATE, datetime.datetime.min.time())
                cookie_account = db.user_ids[db.cookie_database[cookie][0]]
                for active_date, user_activity in cookie_account.activity.items():
                    for activity_unit in user_activity:
                        if activity_unit[1] == cookie and activity_unit[2] not in ('verified', 'blocked'):
                            if latest == None or activity_unit[-1] > latest:
                                latest = activity_unit[-1]
                return latest
            for cookie, secure in db.cookie_database.items():
                ID = secure[0]
                if ID in id_list:
                    cookie_list.append((cookie, last_active(cookie)))
            cookie_list.sort(key=lambda x: x[1], reverse=True)
            aggregate_checkbox = url_arguments.get('aggregate_ip', [None])[0]
            if len(url_arguments) == 1:
                aggregate_checkbox = 'yes'
            if aggregate_checkbox != 'yes':
                for cookie, latest in cookie_list:
                    ip_address, parsed_ua = db.device_info[cookie]
                    ip_address = ip_address[0]
                    my_verified_result = db.cookie_database[cookie][1]
                    ipapi_response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
                    if ipapi_response.get('country_name') != None:
                        self.wfile.write(f'''<table class='device'>
<tr><td class='session_info'>{'THIS DEVICE: ' if cookie==self.my_cookies['code'].value else ''}{parsed_ua}<br />{ipapi_response.get('city')}, {ipapi_response.get('region')}, {ipapi_response.get('country_name')}<br />Last active: {latest.date()}</td><td class='status'>
<select class='status_drop' name='{cookie}' onchange='this.form.submit()'>
<option id='{cookie}_verified' value='verified'>verified</option>
<option id='{cookie}_unsure' value='unsure' disabled='true'>unsure</option>
<option id='{cookie}_blocked' value='blocked'>blocked</option></select></td></tr>
</table>
<script>
document.getElementById('{cookie}_{my_verified_result}').selected = 'true';
</script>'''.encode('utf8'))
                    else:
                        self.wfile.write(f'''<table class='device'>
<tr><td class='session_info'>{'THIS DEVICE: ' if cookie==self.my_cookies['code'].value else ''}{parsed_ua}<br />Last active: {latest.date()}</td><td class='status'>
<select class='status_drop' name='{cookie}' onchange='this.form.submit()'>
<option id='{cookie}_verified' value='verified'>verified</option>
<option id='{cookie}_unsure' value='unsure' disabled='true'>unsure</option>
<option id='{cookie}_blocked' value='blocked'>blocked</option></select></td></tr>
</table>
<script>
document.getElementById('{cookie}_{my_verified_result}').selected = 'true';
</script>'''.encode('utf8'))
                self.wfile.write('''<div id='aggregate_ip'><input id='aggregate_checkbox' type='checkbox' name='aggregate_ip' value='yes' onchange='this.form.submit()'/>
Aggregate IP</div>'''.encode('utf8'))
            else:
                ip_dictionary = {}
                for cookie, latest in cookie_list:
                    ip_address, parsed_ua = db.device_info[cookie]
                    ip_address = ip_address[0]
                    if ip_address in ip_dictionary:
                        ip_dictionary[ip_address].append((cookie, latest))
                    else:
                        ip_dictionary[ip_address] = [(cookie, latest)]
                for ip_address, cookie_latest_list in ip_dictionary.items():
                    parsed_ua = db.device_info[cookie_latest_list[0][0]][1]
                    latest = cookie_latest_list[0][1]
                    cookie_list = list(x[0] for x in cookie_latest_list)
                    cookie_list = '#'.join(cookie_list)
                    compiled_verification = None
                    last_verified_result = None
                    for cookie, latest in cookie_latest_list:
                        my_verified_result = db.cookie_database[cookie][1]
                        if last_verified_result == None:
                            last_verified_result = my_verified_result
                        if my_verified_result != last_verified_result:
                            compiled_verification = 'unsure'
                            break
                    if compiled_verification == None:
                        compiled_verification = last_verified_result
                    ipapi_response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
                    if ipapi_response.get('country_name') != None:
                        self.wfile.write(f'''<table class='device'>
<tr><td class='session_info'>{parsed_ua}<br />{ipapi_response.get('city')}, {ipapi_response.get('region')}, {ipapi_response.get('country_name')}<br />Last active: {latest.date()}</td><td class='status'>
<select class='status_drop' name="{cookie_list}" onchange='this.form.submit()'>
<option id="{cookie_list}_verified" value='verified'>verified</option>
<option id="{cookie_list}_unsure" value='unsure' disabled='true'>unsure</option>
<option id="{cookie_list}_blocked" value='blocked'>blocked</option></select></td></tr>
</table>
<script>
document.getElementById("{cookie_list}_{compiled_verification}").selected = 'true';
</script>'''.encode('utf8'))
                    else:
                        self.wfile.write(f'''<table class='device'>
<tr><td class='session_info'>{parsed_ua}<br />Last active: {latest.date()}</td><td class='status'>
<select class='status_drop' name="{cookie_list}" onchange='this.form.submit()'>
<option id="{cookie_list}_verified" value='verified'>verified</option>
<option id="{cookie_list}_unsure" value='unsure' disabled='true'>unsure</option>
<option id="{cookie_list}_blocked" value='blocked'>blocked</option></select></td></tr>
</table>
<script>
document.getElementById("{cookie_list}_{compiled_verification}").selected = 'true';
</script>'''.encode('utf8'))
                self.wfile.write('''<div id='aggregate_ip'><input id='aggregate_checkbox' type='checkbox' name='aggregate_ip' value='yes' onchange='this.form.submit()' checked='true'/>
Aggregate by IP</div>'''.encode('utf8'))
            self.wfile.write('''</form></body></html>'''.encode('utf8'))
            self.log_activity()
                
    def opinions_page(self):
        reset_cookie = False
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if not 'code' in self.my_cookies:
            if 'cookie_code' in url_arguments:
                self.my_cookies['code'] = url_arguments['cookie_code'][0]
                reset_cookie = True
        my_account = self.identify_user()
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        
        if reset_cookie:
            self.start_response('200 OK', [('Set-Cookie', f'code={url_arguments["cookie_code"][0]}; path=/')])
        else:
            self.start_response('200 OK', [])
        
        see_day = None
        today_date = datetime.date.today()
        print(f'today weekday: {today_date.weekday()}')
        if (today_date.weekday() + 1) % 7 < 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7)
        elif (today_date.weekday() + 1) % 7 > 3:
            see_day = today_date - datetime.timedelta((today_date.weekday() + 1) % 7 - 4)
        else:
            see_day = today_date
        print(f'day of the week that opinions page is viewing: {see_day}')
        if str(see_day) not in db.opinions_calendar or db.opinions_calendar[str(see_day)] == set():
            self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
            self.wfile.write('''<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/favicon.png">'''.encode('utf8'))
            self.send_links_head()
            self.wfile.write('''<style>
article#ballot_label {
  position: fixed;'''.encode('utf8'))
            if verified_result == 'verified':
                self.wfile.write('  top: 70px;'.encode('utf8'))
            else:
                self.wfile.write('  top: 105px;'.encode('utf8'))
            self.wfile.write('''  font-size: 25px;
  padding: 10px;
  width: 96%;
  left: 2%;
  border: 2px solid black;
  border-top: 0px;
  border-radius: 0px 0px 25px 25px;
  box-sizing: border-box;
  text-align: center;
  background-color: #ffef90ff;
}
div#opinion_holder {
  position: fixed;
  top: 220px;
  width: 2000%;
  left: 0;
  bottom: 25%;
  z-index: 1;
}
article.opinion {
  position: absolute;
  top: 0;
  width: 4.8%;
  bottom: 0;
  z-index: 1;
  overflow: scroll;
  border-radius: 30px;
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
section.opinion_text {
  top: 41px;
  bottom: 0;
  width: 100%;
  position: absolute;
  background-color: white;
  box-sizing: border-box;
  font-size: 30px;
  border: 2px solid black;
  border-radius: 0px 0px 27px 27px;
}
p.opinion_p {
  margin: 0;
  position: absolute;
  padding: 10px;
  top: 50%;
  left: 50%;
  margin-right: -50%;
  transform: translate(-50%, -50%);
  text-align: center;
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
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.send_help_box('h1', '''Wednesdays are "off days" as the ballot rotates. On Wednesdays, you can check back in on the week's opinions. Swipe left/right to move between opinions.''', point='bottom', bottom=50, width=300)
            self.wfile.write('''<div id='highlight_title'>
</div>
<footer>
<table>
<tr style='font-family: Garamond'><td id='care_per'>---%</td><td id='agree_per'>---%</td></tr>
<tr style='font-family: "Times New Roman"'><td>care</td><td>agree</td></tr>
</table>
</footer>'''.encode('utf8'))

            self.wfile.write('''<article id='cover'><div id='cover_div'>'''.encode('utf8'))
            highlights = []

            if datetime.date.today().weekday() == 2:
                self.wfile.write('''Middle Wednesday:<br />Ballot Recap'''.encode('utf8'))
                highlights.append(('Middle Wednesday:<br />Ballot Recap',))
            else:
                self.wfile.write('''Off Day:<br />Ballot Recap'''.encode('utf8'))
                highlights.append(('Off Day:<br />Ballot Recap',))
            self.wfile.write('''</div></article><div id='opinion_holder'>'''.encode('utf8'))

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

            opinion_count = 0

            for day in see_old_days:
                def day_to_nice_string(d):
                    return d.strftime('%A %m/%d')
                end_date = day + datetime.timedelta(days=3)
                highlights.append((f'{day_to_nice_string(day)} - {day_to_nice_string(end_date)}',))
                this_list = [db.opinions_database[x] for x in db.opinions_calendar[str(day)]]
                this_list.sort(key=lambda x: -1 * x.care_agree_percent()[0] * x.care_agree_percent()[1])
                for index, opinion in enumerate(this_list):
                    highlights.append((opinion.text,) + opinion.care_agree_percent())
                    self.wfile.write(f'''<article class='opinion' style='left: {.1+5*opinion_count}%'>
<div id='counter'>
Opinion #{index + 1}
</div>
<section class='opinion_text'>
<p class='opinion_p'>{opinion.text}</p>
</section>
</article>'''.encode('utf8'))
                    opinion_count += 1
                    print(f'left: {.1 + 5 * index}')

            # javascript doesn't have tuples
            highlights = [list(x) for x in highlights]
                        
            self.wfile.write(f'''</div><script>
let highlights = {highlights}
let current_index = 0;
let timeElapsed = 0;
let current_translation = 0;

document.addEventListener('touchstart', handleTouchStart, false);
document.addEventListener('touchend', handleTouchEnd, false);
document.addEventListener('touchmove', handleTouchMove, false);
document.addEventListener('keydown', handleKeyDown, false);

var xStart = null;
var yStart = null;
var xEnd = null;
var yEnd = null;

function setX(amount) {{
    if (current_translation + amount < -screen.width * 20) {{
        document.getElementById('opinion_holder').style.transform = 'translateX(' + (screen.width * 20) + 'px)';
    }}
    else if (current_translation + amount > 0) {{
        document.getElementById('opinion_holder').style.transform = '0px';
    }}
    else {{
        document.getElementById('opinion_holder').style.transform = 'translateX(' + (current_translation + amount) + 'px)';
    }}
}}

function getTouches(evt) {{
  return evt.touches ||
         evt.originalEvent.touches;
}}

function handleTouchStart(evt) {{
    const start = getTouches(evt)[0];
    xStart = start.clientX;
    yStart = start.clientY;
}}

function handleTouchEnd(evt) {{
    if (xStart == null || yStart == null || xEnd == null || yEnd == null) {{
        return;
    }}

    var xDiff = xStart - xEnd;
    var yDiff = yStart - yEnd;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {{
        if (Math.abs(xDiff) > 30) {{
            if (xDiff > 0) {{
                change(1);
            }}
            else {{
                change(-1);
            }}
        }}
    }}
    change(0);
    xStart = null;
    yStart = null;
    xEnd = null;
    yEnd = null;
}}
function handleTouchMove(evt) {{
    if (xStart == null || yStart == null) {{
        return;
    }}

    xEnd = evt.touches[0].clientX;
    yEnd = evt.touches[0].clientY;

    var xDiff = xStart - xEnd;
    var yDiff = yStart - yEnd;

    if (highlights[current_index].length == 3) {{
        if (Math.abs(xDiff) > Math.abs(yDiff)) {{
            setX(-xDiff/3);
        }}
        else {{
            return;
        }}
    }}

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
    console.log('new index: ' + newIndex);
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
    if (highlights[current_index].length == 3) {{
        let opinion_number = 0;
        for (var index = 0; index < newIndex; index++) {{
            if (highlights[index].length == 3) {{
                opinion_number++;
            }}
        }}
        console.log('opinion number: ' + opinion_number);
        let target = opinion_number * -screen.width;
        console.log('target: ' + target);
        if (current_translation < target) {{
            for (let currentX = current_translation; currentX < target; currentX++) {{
                    document.getElementById('opinion_holder').style.transform = 'translateX(' + currentX + 'px)';
                    current_translation = currentX;
            }}
        }}
        else if (current_translation > target) {{
            for (let currentX = current_translation; currentX > target; currentX--) {{
                    document.getElementById('opinion_holder').style.transform = 'translateX(' + currentX + 'px)';
                    current_translation = currentX;
            }}
        }}
    }}
    current_index = newIndex;
}}
function cover(text) {{
    document.getElementById('cover_div').innerHTML = text;
    document.getElementById('cover').style.display = 'initial';
}}
function highlight(info) {{
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
  position: fixed;'''.encode('utf8'))
            if verified_result == 'verified':
                self.wfile.write('  top: 70px;'.encode('utf8'))
            else:
                self.wfile.write('  top: 105px;'.encode('utf8'))
            self.wfile.write('''  font-size: 25px;
  padding: 10px;
  width: 96%;
  left: 2%;
  border: 2px solid black;
  border-top: 0px;
  border-radius: 0px 0px 25px 25px;
  box-sizing: border-box;
  text-align: center;
  background-color: #ffef90ff;
}
div#opinion_holder {
  position: fixed;
  top: 220px;
  width: 1000%;
  left: 0;
  bottom: 25%;
  z-index: 1;
}
article.opinion {
  position: absolute;
  top: 0;
  width: 9.6%;
  bottom: 0;
  z-index: 1;
  overflow: scroll;
  border-radius: 30px;
  border: 3px solid black;
  background-color: #ffef90ff;
  box-sizing: border-box;
}
div.counter {
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
  position: absolute;
  background-color: white;
  box-sizing: border-box;
  font-size: 30px;
  border: 2px solid black;
  border-radius: 0px 0px 27px 27px;
}
p#opinion_p {
  margin: 0;
  position: absolute;
  padding: 10px;
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
img.stamp {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 300px;
  transform: translate(-50%, -50%) rotate(-30deg);
  z-index: 2;
  opacity: 0;
}
img.stamp_icon {
  position: fixed;
  top: 150px;
  width: 10%;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write(f'''<article id='ballot_label' onclick='manageHelp("h2")'>
{see_day.strftime('%a %-m/%-d')} - {(see_day + datetime.timedelta(days=2)).strftime('%a %-m/%-d')}
</article>'''.encode('utf8'))
            
            self.wfile.write('''<div id='opinion_holder'>'''.encode('utf8'))

            randomized = list(db.opinions_calendar[str(see_day)])
            random.Random(int(my_account.user_ID)).shuffle(randomized)
            my_votes = []
            opinion_texts = []
            vote_counts = [0, 0]
            for index, opinion_ID in enumerate(randomized):
                assert opinion_ID in db.opinions_database
                opinion = db.opinions_database[opinion_ID]
                assert opinion.approved == True
                opinion_texts.append(opinion.text)
                this_vote = 'abstain'
                if str(opinion_ID) in my_account.votes:
                    this_vote = my_account.votes[str(opinion_ID)][-1][0]
                    my_votes.append(this_vote)
                else:
                    my_votes.append('abstain')
                self.wfile.write(f'''<article class='opinion' style='left: {.2+10*index}%'>
<div class='counter'>
Opinion #{index + 1}
</div>
<section id='opinion_text'>
<p id='opinion_p'>{db.opinions_database[randomized[index]].text}</p>
</section>'''.encode('utf8'))
                self.wfile.write(f"<img id='{index} up' class='stamp' src='up_stamp.png'".encode('utf8'))
                if this_vote == 'up':
                    self.wfile.write(" style='opacity: .4'".encode('utf8'))
                    vote_counts[0] += 1
                self.wfile.write(f"/><img id='{index} down' class='stamp' src='down_stamp.png'".encode('utf8'))
                if this_vote == 'down':
                    self.wfile.write(" style='opacity: .4'".encode('utf8'))
                    vote_counts[1] += 1
                self.wfile.write('/></article>'.encode('utf8'))
            self.wfile.write('</div>'.encode('utf8'))

            assert vote_counts[0] + vote_counts[1] <= 8

            for stamp_number in range(8):
                if stamp_number < vote_counts[0]:
                    self.wfile.write(f'''<img id='stamp {stamp_number}' src='green_icon.png' class='stamp_icon' style='left: {stamp_number * 11 + 6.5}%' onclick='manageHelp("h3")'/>'''.encode('utf8'))
                elif stamp_number >= 8 - vote_counts[1]:
                    self.wfile.write(f'''<img id='stamp {stamp_number}' src='red_icon.png' class='stamp_icon' style='left: {stamp_number * 11 + 6.5}%' onclick='manageHelp("h3")'/>'''.encode('utf8'))
                else:
                    self.wfile.write(f'''<img id='stamp {stamp_number}' src='gray_icon.png' class='stamp_icon' style='left: {stamp_number * 11 + 6.5}%' onclick='manageHelp("h3")'/>'''.encode('utf8'))

            if verified_result == 'verified':
                self.send_help_box('h2', 'The ballot runs in 2 shifts: Sun-Tue and Thu-Sat', top=110, width=300)
            else:
                self.send_help_box('h2', 'The ballot runs in 2 shifts: Sun-Tue and Thu-Sat', top=145, width=300)

            self.send_help_box('h3', 'These stamps keep track of your 8 available votes and how they are spent. Only possessing a max of 5 up or 5 down stamps, these stamps help you prioritize the opinions you care about.', top=180, width=300)
            self.send_help_box('h1', 'Swipe up/down to vote. Swipe left/right to switch between opinions. Double tap to abstain on an opinion.', bottom=50, width=300, point='bottom')
            
            self.wfile.write(f'''<script>
const page_IDs = {randomized};
const opinion_texts = {opinion_texts};
let votes = {my_votes};
let current_index = 0;
let current_translation = 0;
let already_changed = false;

document.addEventListener('touchstart', handleTouchStart, false);
document.addEventListener('touchend', handleTouchEnd, false);
document.addEventListener('touchmove', handleTouchMove, false);
document.addEventListener('dblclick', handleDoubleClick, false);
document.addEventListener('keydown', handleKeyDown, false);

change(0);

let xStart = null;
let yStart = null;
let xEnd = null;
let yEnd = null;

function setX(amount) {{
    if (current_translation + amount < -screen.width * 20 - 20) {{
        document.getElementById('opinion_holder').style.transform = 'translateX(' + (screen.width * 20 - 20) + 'px)';
    }}
    else if (current_translation + amount > 20) {{
        document.getElementById('opinion_holder').style.transform = 'translateX(20px)';
    }}
    else {{
        document.getElementById('opinion_holder').style.transform = 'translateX(' + (current_translation + amount) + 'px)';
    }}
}}

function getTouches(evt) {{
  return evt.touches ||
         evt.originalEvent.touches;
}}

function handleTouchStart(evt) {{
    const start = getTouches(evt)[0];
    xStart = start.clientX;
    yStart = start.clientY;
}}

function handleTouchEnd(evt) {{

    if (xStart == null || yStart == null || xEnd == null || yEnd == null) {{
        return;
    }}

    var xDiff = xStart - xEnd;
    var yDiff = yStart - yEnd;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {{
        if (Math.abs(xDiff) > 30) {{
            if (xDiff > 0) {{
                change(1);
            }}
            else {{
                change(-1);
            }}
        }}
        else {{
            change(0);
        }}
    }}
    else {{
        if (Math.abs(yDiff) > 30) {{
            if (yDiff > 0) {{
                vote('up');
            }}
            else {{ 
                vote('down');
            }}
        }}
        else {{
            change(0);
        }}
    }}
    xStart = null;
    yStart = null;
    xEnd = null;
    yEnd = null;
}}
function handleTouchMove(evt) {{
    if (xStart == null || yStart == null) {{
        return;
    }}
    xEnd = evt.touches[0].clientX;
    yEnd = evt.touches[0].clientY;

    var xDiff = xStart - xEnd;
    var yDiff = yStart - yEnd;

    if (Math.abs(xDiff) > Math.abs(yDiff)) {{
        setX(-xDiff/3);
    }}
    else {{
        return;
    }}

}}
function handleDoubleClick(evt) {{
    vote('abstain');
}}
function vote(my_vote) {{
    var xhttp = new XMLHttpRequest();
    if (checkVoteValidity(my_vote, votes[current_index])) {{
        xhttp.open('GET', '/vote?opinion_ID=' + page_IDs[current_index] + '&my_vote=' + my_vote, true);
        xhttp.send();
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
        if (votes[current_index] != 'abstain') {{
            document.getElementById(current_index + ' ' + votes[current_index]).style.opacity = '0';
            if (votes[current_index] == 'up' && up_count > 0) {{
                document.getElementById('stamp ' + (up_count - 1)).src = 'gray_icon.png';
                up_count--;
            }}
            else if (down_count > 0) {{
                document.getElementById('stamp ' + (8 - down_count)).src = 'gray_icon.png';
                down_count--;
            }}
        }}
        if (my_vote != 'abstain') {{
            document.getElementById(current_index + ' ' + my_vote).style.opacity = '1';
            if (my_vote == 'up') {{
                document.getElementById('stamp ' + up_count).src = 'green_icon.png';
            }}
            else {{
                document.getElementById('stamp ' + (8 - down_count - 1)).src = 'red_icon.png';
            }}
        }}
        votes[current_index] = my_vote;
        already_changed = false;
        setTimeout(() => {{if (!already_changed) {{ change(1)}} }}, 1000);
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
    let newIndex = current_index + i;
    if (newIndex < 0) {{
        newIndex = 0;
    }}
    else if (newIndex >= opinion_texts.length) {{
        newIndex = opinion_texts.length - 1;
    }}
    let target = newIndex * -screen.width;
    let opinion_holder = document.getElementById('opinion_holder');
    opinion_holder.style.transition = '0.4s';
    opinion_holder.style.transform = 'translateX(' + target + 'px)';
    let old_index = current_index;
    function reset() {{
        opinion_holder.style.transition = 'none';
        if (votes[old_index] != 'abstain') {{
            document.getElementById(old_index + ' ' + votes[old_index]).style.opacity = '0.4';
        }}
    }}
    setTimeout(reset, 400);
    current_index = newIndex;
    current_translation = target;
    already_changed = true;
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
</script>'''.encode('utf8'))
        self.wfile.write('</body></html>'.encode('utf8'))
        self.log_activity()
        
    def submit_opinions_page(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(self.query_string)
        if 'opinion_text' in url_arguments:
            self.submit_opinion(False)
        unscheduled_approved = 0
        for opinion_ID, opinion in db.opinions_database.items():
            if opinion.approved == True and not opinion.scheduled:
                unscheduled_approved += 1
        unscheduled_approved = unscheduled_approved // 10
        next_date = datetime.date.today()
        if (next_date.weekday() + 1) % 7 < 3:
            next_date += datetime.timedelta(3 - (next_date.weekday() + 1) % 7)
        elif (next_date.weekday() + 1) % 7 > 3:
            next_date += datetime.timedelta(7 - (next_date.weekday() + 1) % 7)
        else:
            next_date += datetime.timedelta(1)
        while unscheduled_approved > 0:
            if next_date.weekday() == 6:
                next_date += datetime.timedelta(4)
            else:
                assert next_date.weekday() == 3
                next_date += datetime.timedelta(3)
            unscheduled_approved -= 10
                
        self.start_response('200 OK', [])
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
div#opinion_supply {
  position: fixed;
  top: 80px;
  left: 4%;
  width: 66%;
  height: 80px;
  box-sizing: border-box;
  text-align: center;
  z-index: 2;
  padding: 0;
}
div#counter_div {
  position: fixed;
  top: 50px;
  right: 1%;
  width: 140px;
  height: 140px;
  z-index: 0;
}
p#day_count {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  margin: 0;
  font-family: Verdana, Helvetica, 'Trebuchet MS', sans-serif, Arial;
  text-align: center;
}
p#supply_label {
  position: absolute;
  top: 50%;
  left: 45%;
  transform: translate(-50%, -50%);
  z-index: 2;
  margin: 0;
  font-family: Verdana, Helvetica, 'Trebuchet MS', sans-serif, Arial;
  font-size: 20px;
  white-space: nowrap;
}
img.full {
  position: absolute;
  width: 100%;
  height: 100%;
  left: 0;
  top: 0;
}
form {
  position: fixed;
  top: 170px;
  width: 92%;
  height: 36%;
  left: 4%;
  font-size: 25px;
  padding: 6%;
  box-sizing: border-box;
  border: 3px solid black;
  border-radius: 20px;
  text-align: center;
  background-color: #ffef90ff;
}
div#entry_box {
  position: absolute;
  top: 95px;
  width: 92%;
  left: 4%;
  bottom: 15px;
}
textarea#opinion_text {
  position: absolute;
  height: 100%;
  width: 85%;
  left: 0;
  font-size: 20px;
  text-align: center;
  box-sizing: border-box;
  padding: 15px;
  border-radius: 15px 0 0 15px;
}
div#submit_holder {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  width: 15%;
  background-color: #6d9eebff;
  border-radius: 0 15px 15px 0;
}
img#submit_button {
  position: absolute;
  width: 80%;
  left: 10%;
  top: 50%;
  transform: translate(0, -50%);
}
article#similar {
  position: fixed;
  height: 25%;
  width: 92%;
  left: 4%;
  bottom: 80px;
  z-index: 1;
  border-radius: 30px;
  border: 3px solid black;
  box-sizing: border-box;
  font-family: Verdana, Helvetica, 'Trebuchet MS', sans-serif, Arial;
  background-color: white;
}
div#similar_label {
  position: absolute;
  top: 0;
  font-size: 25px;
  padding-top: 15px;
  padding-bottom: 5px;
  border-bottom: 2px solid black;
  width: 100%;
  box-sizing: border-box;
  text-align: center;
  background-color: #ffef90ff;
  border-radius: 27px 27px 0 0;
  line-height: 20px;
}
p#similar_text {
  margin: 0;
  position: absolute;
  padding: 10px;
  top: 50%;
  left: 50%;
  margin-right: -50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
</style>
</head>
<body>'''.encode('utf8'))
        self.send_links_body()
        self.send_help_box('h2', 'This counter shows how long the current number of submitted opinions will be able to fill the ballot, with 10 opinions used bi-weekly.', top=150, width=300, point='top')
        self.send_help_box('h3', 'UpDown tries to promote original opinions to sustain an intriguing ballot for users.', point='top', top=480, width=300)
        self.send_help_box('h1', 'UpDown relies on all users to submit opinions. From small to large issues, your opinions are what makes UpDown special. This is why UpDown maintains your anonymity as you submit opinions.', point='bottom', bottom=50, width=300)
        self.wfile.write(f'''<div id='opinion_supply' onclick='manageHelp("h2")'>
<p id='supply_label'>
Opinion Supply
</p>
<img class='full' src='sign.png' />
</div>
<div id='counter_div' onclick='manageHelp("h2")'>
<p id='day_count'>
<span style='font-size: 36px'>{(next_date - datetime.date.today()).days}</span><br />
<span style='font-size: 14px'>{'day' if (next_date - datetime.date.today()).days == 1 else 'days'}</span>
</p>
<img class='full' src='clock.png' />
</div>
<form method='GET' action='/submit_opinions'>
UpDown needs your help to continue running!<br />
<div id='entry_box'>
<textarea id='opinion_text' name='opinion_text' placeholder='Please enter your opinion here!'>
</textarea>
<div id='submit_holder' onclick='this.parentElement.parentElement.submit()'>
<img id='submit_button' src='submit_button.png'/>
</div>
</div>
</form>
<article id='similar'>
<div id='similar_label' onclick='manageHelp("h3")'>
<span style='font-size: 24px'>Closest Relative</span><br />
<span style='font-size: 16px'>Identical twins may be rejected</span>
</div>
<p id='similar_text'>
</p>
</article>'''.encode('utf8'))
        self.wfile.write('''<script>
var old_opinion;
document.addEventListener('touchend', handleTouchEnd, false);
setInterval(updateSearch, 1000);
function updateSearch() {
    let current_opinion = document.getElementById('opinion_text').value;
    if (current_opinion != old_opinion) {
        if (current_opinion != '') {
            var xhttp = new XMLHttpRequest();
            xhttp.open('GET', '/submit_opinion_search?text=' + current_opinion);
            xhttp.send();
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    var similar_text = JSON.parse(this.responseText);
                    document.getElementById('similar_text').innerHTML = similar_text;
                }
            };
        }
        else {
            document.getElementById('similar_text').innerHTML = '';
        }
    }
    old_opinion = current_opinion;
}
function handleTouchEnd() {
    
}
</script>
</body>
</html>'''.encode('utf8'))

    def approve_opinions_page(self):
        my_account = self.identify_user()
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        if my_account.email in local.ADMINS and verified_result == 'verified':
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
            self.send_help_box('h1', 'Swipe up/down starting on the lock to approve/reject opinions. Think before you swipe!', point='bottom', bottom=50, width=300)
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
document.addEventListener('keydown', handleKeyDown, false);

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
function handleKeyDown(evt) {{
    let key_pressed = event.key;
    const keyDict = {{
        'ArrowUp': 'yes',
        'ArrowDown': 'no',
    }};
    if (keyDict[key_pressed] != null) {{
        vote(keyDict[key_pressed]);
    }}
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
        self.send_help_box('h1', "Check out our school Senate!", point='bottom', bottom=50, width=300)
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
                db.opinions_database[str(opinion_ID)] = updown.Opinion(opinion_ID, opinion_text, [(self.my_cookies['code'].value, datetime.datetime.now())])
            run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)
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
                run_and_sync(db.user_ids_lock, update_user_cookies, db.user_ids)

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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        if my_account.email in local.ADMINS and verified_result == 'verified':
            url_arguments = urllib.parse.parse_qs(self.query_string)
            if 'opinion_ID' in url_arguments and 'my_vote' in url_arguments:
                opinion_ID = url_arguments['opinion_ID'][0]
                my_vote = url_arguments['my_vote'][0]
                if opinion_ID in db.opinions_database and my_vote in ('yes', 'no'):
                    # update databases
                    opinion = db.opinions_database[opinion_ID]
                    if len(opinion.activity) == 1:
                        opinion.activity.append([(self.my_cookies['code'].value, my_vote, datetime.datetime.now())])
                        if my_vote == 'yes':
                            opinion.approved = True
                        else:
                            opinion.approved = False
                    else:
                        opinion.activity[1].append((self.my_cookies['code'].value, my_vote, datetime.datetime.now()))

                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

                    def update_user_cookies():
                        db.user_ids[my_account.user_ID] = my_account
                    run_and_sync(db.user_ids_lock, update_user_cookies, db.user_ids)

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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        url_arguments = urllib.parse.parse_qs(self.query_string)
        see_month_str = url_arguments.get('month', [datetime.date.today().strftime('%Y-%m')])[0]
        if my_account.email in local.ADMINS and verified_result == 'verified':
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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        if my_account.email in local.ADMINS and verified_result == 'verified':
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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        if my_account.email in local.ADMINS and verified_result == 'verified':
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
                        opinion.activity.append([(self.my_cookies['code'].value, True, datetime.datetime.strptime(this_date, '%Y-%m-%d').date(), datetime.datetime.now())])
                    else:
                        opinion.activity[2].append((self.my_cookies['code'].value, True, datetime.datetime.strptime(this_date, '%Y-%m-%d').date(), datetime.datetime.now()))

                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

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
                    run_and_sync(db.opinions_calendar_lock, update_opinions_calendar, db.opinions_calendar)
                    
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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        if my_account.email in local.ADMINS and verified_result == 'verified':
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
                    opinion.activity[2].append((self.my_cookies['code'].value, False, datetime.datetime.strptime(this_date, '%Y-%m-%d'), datetime.datetime.now()))

                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

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
                    run_and_sync(db.opinions_calendar_lock, update_opinions_calendar, db.opinions_calendar)

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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        isSenator = False
        if verified_result == 'verified':
            for committee, members in local.COMMITTEE_MEMBERS.items():
                if my_account.email in members:
                    isSenator = True
        url_arguments = urllib.parse.parse_qs(self.query_string)
        self.start_response('200 OK', [])
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
form {
  position: fixed;
  top: 80px;
  width: 96%;
  left: 2%;
  bottom: 65%;
  border: 3px solid black;
  box-sizing: border-box;
  border-radius: 30px 30px 0 0;
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
  box-sizing: border-box;
  border-radius: 20px;
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
  position: fixed;
  bottom: 10%;
  top: 35%;
  width: 96%;
  left: 2%;
  overflow: scroll;
  border: 3px solid black;
  border-radius: 0 0 30px 30px;
  border-top: 0;
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
  position: fixed;
  top: 80px;
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
  border-radius: 3px 3px 0 0;
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
  padding: 15px;
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
td#circle_td {
  width: 50%;
}
div#circle {
  position: absolute;
  left: 25%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border: 8px solid black;
  border-radius: 50%;
}
div#circle p {
  position: absolute;
  top: 50%;
  left: 50%;
  text-align: center;
  transform: translate(-50%, -50%);
  font-size: 30px;
  margin: 0;
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
        self.send_help_box('h1', 'Track opinions that you care about using the search, sort, and filter options. Clicking on an opinion will give you statistics about it. Find the most popular opinions in UpDown history!', point='bottom', bottom=50, width=300)
        self.send_help_box('h3', 'Committees reserve opinions to signify that they are working on a bill to resolve the opinion.', point='top', top=110, width=300)
        self.send_help_box('h4', 'The automated opinion selection process chooses opinions at random.', point='bottom', bottom=390, width=300)
        self.send_help_box('h5', 'care = voted up or down (did not abstain)<br />agree = voted up given they care<br />overall = care * agree', point='top', top=480, width=300)

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
            if filter_keep(opinion):
                self.wfile.write(f'''<table id='{opinion.ID}' class='result' onclick='openpop(this);'>
<tr><td class='rank'>{index + 1}.</td><td class='opinion'>{opinion.text}</td></tr>
</table>'''.encode('utf8'))
        self.wfile.write('</article></footer>'.encode('utf8'))
        self.wfile.write(f'''<article id='view_popup'>
<div id='reserved_header' onclick='manageHelp("h3")'>'''.encode('utf8'))
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
<table id='development' onclick='manageHelp("h4")'>
<tr><td id='created'>created<br />_/_/_</td><td>--></td><td id='voted'>voted<br />_/_/_</td></tr>
</table>
<table id='stats' onclick='manageHelp("h5")'>
<tr>
<td id='circle_td'>
<div id='circle'>
<p>
20<br />
<span style='font-size: 20px'>VOTERS</span>
</p>
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
        self.wfile.write(f'''<script>
var view_opinion_id;
var response;
function openpop(element) {{
    tutorial = true;
    open_help = 'h2';
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
            document.getElementById('circle').innerHTML = '<p>' + response[4] + '<br /><span style="font-size: 20px">VOTERS</span></p>';
            document.getElementById('care_stat').innerHTML = response[5][0] + '% care (#' + response[5][1] + ')';
            document.getElementById('agree_stat').innerHTML = response[6][0] + '% agree (#' + response[6][1] + ')';
            document.getElementById('overall_stat').innerHTML = response[7][0] + '% overall (#' + response[7][1] + ')';
            document.getElementById('similar_text').innerHTML = response[8][1];
            document.getElementById('view_popup').style.display = 'initial';
        }}
    }};
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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        url_arguments = urllib.parse.parse_qs(self.query_string)
        committee = url_arguments['committee'][0]
        if committee in local.COMMITTEE_MEMBERS.keys():
            if my_account.email in local.COMMITTEE_MEMBERS[committee] and verified_result == 'verified':
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
                self.send_help_box('h1', "Stay up to date on your committee's work by viewing your reserved opinions and submitting updated bills.", point='bottom', bottom=50, width=300)

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
            opinions_text = ''
            if len(opinions) > 0:
                opinions_text = db.opinions_database[str(opinions[0])].text
            self.start_response('200 OK', [])
            self.wfile.write(json.dumps(opinions_text).encode('utf8'))
            
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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        if my_account.email in local.ADMINS and verified_result == 'verified':
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
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
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
                if verified_result == 'verified':
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
                # total # of voters
                response.append(sum(opinion.count_votes()))
                # care, agree, overall percentages and rankings
                care_p, agree_p = opinion.care_agree_percent()
                overall_p = care_p * agree_p / 100
                care_r, agree_r, overall_r = opinion.rankings()
                response.extend([[care_p, care_r], [agree_p, agree_r], [overall_p, overall_r]])
                # similar opinion
                similar_opinions = list(filter(lambda x: x != opinion.ID, search(opinion.text)))
                if len(similar_opinions) != 0:
                    similar_opinion_ID = similar_opinions[0]
                    similar_opinion_text = db.opinions_database[str(similar_opinion_ID)].text
                    response.append([similar_opinion_ID, similar_opinion_text])
                else:
                    response.append([opinion_ID, ''])
                print(response)
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
        opinion_ID = url_arguments.get('opinion_ID', [''])[0]
        if opinion_ID != '':
            opinion = db.opinions_database[opinion_ID]
            if my_account.email in local.COMMITTEE_MEMBERS.get(committee, set()) or (committee == 'unreserved' and my_account.email in local.COMMITTEE_MEMBERS[opinion.reserved_for]):
                if reserve_count(committee) < 2:
                    if len(opinion.activity) == 3:
                        opinion.activity.append([(self.my_cookies['code'].value, committee, datetime.datetime.now())])
                    else:
                        opinion.activity[3].append((self.my_cookies['code'].value, committee, datetime.datetime.now()))
                    if committee == 'unreserved':
                        opinion.reserved_for = None
                    else:
                        opinion.reserved_for = committee
                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

                    self.log_activity([committee, opinion_ID])
                    
                    self.start_response('200 OK', [])

    def edit_bill(self):
        my_account = self.identify_user()
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        url_arguments = urllib.parse.parse_qs(self.query_string)
        opinion_ID = url_arguments.get('opinion_ID', [''])[0]
        new_bill = url_arguments.get('bill', [None])[0]
        mark_resolved = url_arguments.get('mark_resolved', [''])[0]
        if opinion_ID != '' and new_bill != None and mark_resolved in ('yes', 'no'):
            opinion = db.opinions_database[opinion_ID]
            if my_account.email in local.COMMITTEE_MEMBERS[opinion.reserved_for] and verified_result == 'verified':
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
                run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)
                
                self.log_activity()

                self.start_response('200 OK', [])

    def community_service(self):
        my_account = self.identify_user()
        verified_result = db.cookie_database[self.my_cookies['code'].value][1]
        if (my_account.email in local.BETA_TESTERS and verified_result == 'verified') or (my_account.email in local.COMMUNITY_SERVICE and verified_result == 'verified'):
            hour_counts = {}
            for user_id, user_account in db.user_ids.items():
                if not user_account.email in hour_counts:
                    hour_counts[user_account.email] = datetime.timedelta(minutes=0)
                sorted_activity = list(user_account.activity.items())
                sorted_activity.sort(key=lambda x: x[0])
                for day, activity_list in sorted_activity:
                    for index, activity_unit in enumerate(activity_list):
                        if len(activity_list) > index + 1:
                            if activity_list[index+1][-1] - activity_unit[-1] >= datetime.timedelta(minutes=3):
                                hour_counts[user_account.email] += datetime.timedelta(minutes=3)
                            else:
                                hour_counts[user_account.email] += activity_list[index+1][-1] - activity_unit[-1]
            self.start_response('200 OK', [])
            self.wfile.write('''<html><head>'''.encode('utf8'))
            self.send_links_head()
            self.wfile.write('''<style>
span#note {
  position: absolute;
  top: 80px;
  right: 5px;
  font-size: 18px;
}
table#cs {
  position: absolute;
  top: 120px;
  border: 3px solid black;
  width: 100%;
  box-sizing: border-box;
  left: 0;
  font-size: 18px;
}
td {
  padding-bottom: 15px;
}
</style>'''.encode('utf8'))
            self.wfile.write('</head><body>'.encode('utf8'))
            self.send_links_body()
            self.send_help_box('h1', 'This is where you can view your current community service hours. They always round up!', point='bottom', bottom=50, width=300)
            self.wfile.write('''<span id='note'>hour:minute:second --> total hours rounded up</span>'''.encode('utf8'))
            self.wfile.write('''<table id='cs'>'''.encode('utf8'))
            if my_account.email in local.COMMUNITY_SERVICE and verified_result == 'verified':
                for user_email, hour_count in hour_counts.items():
                    t_secs = hour_count.total_seconds()
                    t_hours = t_secs / 3600
                    self.wfile.write(f'''<tr><td>{user_email}</td><td>{int(t_secs//3600):02d}:{int(t_secs//60)%60:02d}:{int(t_secs%60):02d} --> {math.ceil(t_hours)}</td></tr>'''.encode('utf8'))
            else:
                hour_count = hour_counts[my_account.email]
                t_secs = hour_count.total_seconds()
                t_hours = t_secs / 3600
                self.wfile.write(f'''<tr><td>{my_account.email}</td><td>{int(t_secs//3600):02d}:{int(t_secs//60)%60:02d}:{int(t_secs%60):02d} --> {math.ceil(t_hours)}</td></tr>'''.encode('utf8'))
                
            self.wfile.write('</table>'.encode('utf8'))
            self.wfile.write('</body></html>'.encode('utf8'))
            self.log_activity()
        else:
            self.start_response('400 BAD REQUEST', [])

    def send_help_box(self, element_id, text, top=0, width=100, bottom=0, point='top'):
        arrow_height = 15
        if point == 'top':
            self.wfile.write(f'''<div id='{element_id}' class='help_box' style='top: {top}px; width: {width}px; display: none'><div class='help_text' style='top: {arrow_height}px'>{text}</div><div class='help_up'></div></div>'''.encode('utf8'))
        elif point == 'bottom':
            self.wfile.write(f'''<div id='{element_id}' class='help_box' style='bottom: {bottom}px; width: {width}px; display: none'><div class='help_text' style='bottom: {arrow_height}px'>{text}</div><div class='help_down'></div></div>'''.encode('utf8'))

                    
class invalidCookie(ValueError):
    def __init__(self, message):
        super().__init__(message)

def run_and_sync(lock_needed, change, database, check_corrupt=True):
    lock_needed.acquire()
    try:
        returns = change()
        if check_corrupt:
            db_corruption.check_corruption((db.user_ids, db.opinions_database, db.cookie_database, db.verification_links, db.opinions_calendar, db.device_info))
        return returns
    finally:
        lock_needed.release()
            
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
    if MyWSGIHandler.DEBUG == 0:
        print(f'{SEARCH_INDEX}')

    search_index_lock.release()

def search_index_add_opinion(opinion):
    search_index_lock.acquire()
    split_text = simplify_text(opinion.text)
    if MyWSGIHandler.DEBUG == 0:
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
    # print(f'{(set(simplify_text(text1)) & set(simplify_text(text2))) != set()}')
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
        if see_day.weekday() != 2:
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

            def smart_opinion_in(collection, opinion_ID):
                for check_ID in collection:
                    if db.opinions_database[check_ID].text == db.opinions_database[opinion_ID].text:
                        return True
                return False

            if datetime.datetime.now() + datetime.timedelta(seconds=0.5) > next_due_time:
                ages = []
                seconds_sum = 0
                approved_set = set()
                for opinion_ID, opinion in db.opinions_database.items():
                    if opinion.approved == True and not smart_opinion_in(approved_set, opinion_ID):
                        approved_set.add(opinion_ID)
                        if not opinion.scheduled:
                            creation_date = opinion.activity[0][-1]
                            seconds_passed = (datetime.datetime.now() - creation_date).total_seconds()
                            seconds_sum += seconds_passed
                            ages.append((seconds_passed, opinion_ID))
                compiled_set = db.opinions_calendar.get(str(next_due_date), set())
                compiled_set = set(str(x) for x in compiled_set)

                if len(compiled_set) + len(ages) <= 10:
                    for age_secs, opinion_ID in ages:
                        compiled_set.add(opinion_ID)
                    # make sure no infinite loop
                    if len(approved_set) > 10:
                        while len(compiled_set) < 10:
                            new_random = random.choice(list(db.opinions_database.keys()))
                            copy_opinion = db.opinions_database[new_random]
                            if new_random not in compiled_set and copy_opinion.approved == True:
                                def update_opinions_database():
                                    new_opinion = updown.Opinion(len(db.opinions_database), copy_opinion.text, [(-1, datetime.datetime.now()), [(-1, 'yes', datetime.datetime.now())], [(next_due_date, datetime.datetime.now())]], approved=copy_opinion.approved, scheduled=True)
                                    db.opinions_database[str(new_opinion.ID)] = new_opinion
                                    return new_opinion.ID
                                new_opinion_id = run_and_sync(db.opinions_database, update_opinions_database, db.opinions_database_lock)
                                compiled_set.add(str(new_opinion_id))
                    else:
                        for opinion_ID in list(db.opinions_database.keys()):
                            copy_opinion = db.opinions_database[opinion_ID]
                            if not smart_opinion_in(compiled_set, opinion_ID) and copy_opinion.approved == True:
                                def update_opinions_database():
                                    new_opinion = updown.Opinion(len(db.opinions_database), copy_opinion.text, [(-1, datetime.datetime.now()), [(-1, 'yes', datetime.datetime.now())], [(next_due_date, datetime.datetime.now())]], approved=copy_opinion.approved, scheduled=True)
                                    db.opinions_database[str(new_opinion.ID)] = new_opinion
                                    return new_opinion.ID
                                new_opinion_id = run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)
                                compiled_set.add(str(new_opinion_id))

                else:
                    while len(compiled_set) < 10:
                        # reset remaining count
                        remaining = random.random()
                        remaining *= seconds_sum
                        opinion_index = 0
                        while remaining > 0 and opinion_index < len(ages):
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

def verify_device(cookie_code):
    my_account = db.user_ids[db.cookie_database[cookie_code][0]]
    verified_cookie = None
    for this_cookie, this_secure in db.cookie_database.items():
        if db.user_ids[this_secure[0]].email == my_account.email and this_secure[1] == 'verified':
            verified_cookie = this_cookie
            break
    # if there is already a verified cookie, fix my cookie to point to the same verified account
    if verified_cookie != None:
        verified_account = db.user_ids[db.cookie_database[verified_cookie][0]]
        # fix my cookie to point to verified account and be verified
        def update_cookie_database():
            db.cookie_database[cookie_code] = (verified_account.user_ID, 'verified')
        run_and_sync(db.cookie_database_lock, update_cookie_database, db.cookie_database)

        def update_user_ids():
            my_account.obselete = True
            db.user_ids[my_account.user_ID] = my_account

        run_and_sync(db.user_ids_lock, update_user_ids, db.user_ids)

        # manual log activity showing my_account verified email
        what = [cookie_code, 'verified']
        activity_unit = ['/verification'] + what + [datetime.datetime.now()]
        if datetime.date.today() in my_account.activity:
            my_account.activity[datetime.date.today()].append(tuple(activity_unit))
        else:
            my_account.activity[datetime.date.today()] = [tuple(activity_unit)]
        if datetime.date.today() in verified_account.activity:
            verified_account.activity[datetime.date.today()].append(tuple(activity_unit))
        else:
            verified_account.activity[datetime.date.today()] = [tuple(activity_unit)]

        def update_user_activity():
            db.user_ids[my_account.user_ID] = my_account
            db.user_ids[verified_account.user_ID] = verified_account

        run_and_sync(db.user_ids_lock,
                          update_user_activity,
                          db.user_ids)
        logging.info(f'''email: {my_account.email}; cookie: {cookie_code}; user ID: {my_account.user_ID}; activity: {activity_unit}''')

    # if there are no verified cookies, then make my account verified
    else:
        # verify my cookie
        def update_cookie_database():
            db.cookie_database[cookie_code] = (my_account.user_ID, 'verified')
        run_and_sync(db.cookie_database_lock, update_cookie_database, db.cookie_database)
        
        # manual log activity showing my_account verified email
        what = [cookie_code, 'verified']
        activity_unit = ['/verification'] + what + [datetime.datetime.now()]
        if datetime.date.today() in my_account.activity:
            my_account.activity[datetime.date.today()].append(tuple(activity_unit))
        else:
            my_account.activity[datetime.date.today()] = [tuple(activity_unit)]

        def update_user_activity():
            db.user_ids[my_account.user_ID] = my_account

        run_and_sync(db.user_ids_lock,
                          update_user_activity,
                          db.user_ids)
        logging.info(f'''email: {my_account.email}; cookie: {cookie_code}; user ID: {my_account.user_ID}; activity: {activity_unit}''')
    
    if MyWSGIHandler.DEBUG < 2:
        print(f'{cookie_code} just verified their email!')

def block_device(cookie_code):
    my_account = db.user_ids[db.cookie_database[cookie_code][0]]
    # block my cookie
    def update_cookie_database():
        db.cookie_database[cookie_code] = (my_account.user_ID, 'blocked')
    run_and_sync(db.cookie_database_lock, update_cookie_database, db.cookie_database)

    # manual log activity showing my_account verified email
    what = [cookie_code, 'blocked']
    activity_unit = ['/verification'] + what + [datetime.datetime.now()]
    if datetime.date.today() in my_account.activity:
        my_account.activity[datetime.date.today()].append(tuple(activity_unit))
    else:
        my_account.activity[datetime.date.today()] = [tuple(activity_unit)]

    def update_user_activity():
        db.user_ids[my_account.user_ID] = my_account

    run_and_sync(db.user_ids_lock,
                      update_user_activity,
                      db.user_ids)
    logging.info(f'''email: {my_account.email}; cookie: {cookie_code}; user ID: {my_account.user_ID}; activity: {activity_unit}''')    
        
def create_account(user_email):
    def update_user_ids():
        new_id = str(len(db.user_ids))
        db.user_ids[new_id] = updown.User(user_email, new_id)
        new_cookie = uuid.uuid4().hex
        while new_cookie in db.cookie_database:
            new_cookie = uuid.uuid4().hex

        def update_cookie_database():
            db.cookie_database[new_cookie] = (new_id, 'unsure')

        run_and_sync(db.cookie_database_lock, update_cookie_database, db.cookie_database, False)

        def update_verification_links():
            send_v_link = None
            repeat_email = False
            for v_link, v_email in db.verification_links.items():
                if v_email == user_email:
                    repeat_email = True
                    send_v_link = v_link

            if not repeat_email:
                send_v_link = uuid.uuid4().hex
                while send_v_link in db.verification_links:
                    send_v_link = uuid.uuid4().hex
                db.verification_links[send_v_link] = user_email
            return send_v_link

        send_v_link = run_and_sync(db.verification_links_lock, update_verification_links, db.verification_links, check_corrupt=False)
        return new_cookie, new_id, send_v_link
    return run_and_sync(db.user_ids_lock, update_user_ids, db.user_ids, check_corrupt=False)

def calc_expiration(yog):
    century = (datetime.date.today().year // 100) * 100
    return datetime.date(year=century + yog, month=8, day=1)

def valid_yogs():
    if datetime.date.today().month >= 8:
        return [str(x)[-2:] for x in range(int(datetime.date.today().year + 1), int(datetime.date.today().year + 5))]
    else:
        return [str(x)[-2:] for x in range(int(datetime.date.today().year), int(datetime.date.today().year + 4))]

def email_is_valid(email):
    return re.match(email, local.EMAIL_MATCH_RE)

def main():
    print('Student Change Web App... running...')

    if MyWSGIHandler.DEBUG == 0:
        print(f'\n{db.user_ids}')
        for this_user_ID, user in db.user_ids.items():
            # print(f'  {this_user_ID} : User({user.email}, {user.user_ID}, {user.activity}, {user.votes}, {user.obselete})')
            print(f'  {this_user_ID} : User({user.email}, {user.user_ID}, activity, {user.votes}, {user.obselete})')

        print(f'\n{db.cookie_database}')
        for cookie, this_secure in db.cookie_database.items():
            print(f'  {cookie} : {this_secure}')

        print(f'\n{db.verification_links}')
        for link, email in db.verification_links.items():
            print(f'  {link} : {email}')

        print(f'\n{db.opinions_database}')
        for ID, opinion in db.opinions_database.items():
            print(f'  {ID} : Opinion({opinion.ID}, {opinion.text}, {opinion.activity}, {opinion.approved}, {opinion.scheduled}, {opinion.reserved_for}, {opinion.bill}, {opinion.resolved})')

        print(f'\n{db.opinions_calendar}')
        sorted_calendar = list(db.opinions_calendar.keys())
        sorted_calendar.sort()
        for this_date in sorted_calendar:
            ID_set = db.opinions_calendar[this_date]
            print(f'  {this_date} : {ID_set}')

        print(f'\n{db.device_info}')
        for cookie, info in db.device_info.items():
            print(f'  {cookie} : {info}')


    # httpd = make_server('10.17.4.226', 8888, application)
    # httpd.serve_forever()
    serve(application, host='10.17.4.226', port=8888)

logging.basicConfig(filename='UpDown.log', level=logging.DEBUG)

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

print(str(sys.version))

if __name__ == '__main__':
    main()
