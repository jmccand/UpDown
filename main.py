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

class MyHandler(SimpleHTTPRequestHandler):

    DEBUG = 3
    
    def do_GET(self):
        print('\n')
        my_cookies = SimpleCookie(self.headers.get('Cookie'))
        if MyHandler.DEBUG == 0:
            print('\npath: ' + self.path)
            print(f'{my_cookies=}')

        invalid_cookie = True
        if 'code' in my_cookies:
            if my_cookies['code'].value in db.user_cookies:
                invalid_cookie = False
            else:
                if not self.path == '/favicon.ico':
                    print(f'INVALID COOKIE FOUND: {self.path=} and {my_cookies["code"].value=}\n')
        else:
            if not self.path == '/favicon.ico':
                print(f'INVALID COOKIE FOUND: {self.path =}\n')

        if invalid_cookie and not self.path.startswith('/check_email') and not self.path.startswith('/email_taken') and not self.path.startswith('/verify_email'):
            self.get_email()
        else:
            try:
                self.path_root = '/'
                if self.path == '/':
                    self.opinions_page()
                elif self.path == '/favicon.ico':
                    return self.load_image()
                elif self.path == '/hamburger.png':
                    return self.load_image()
                elif self.path.startswith('/check_email'):
                    self.path_root = '/check_email'
                    self.check_email()
                elif self.path.startswith('/email_taken'):
                    self.path_root = '/email_taken'
                    self.email_taken()
                elif self.path == '/about_the_senate':
                    self.path_root = '/about_the_senate'
                    self.about_the_senate_page()
                elif self.path == '/current_issues':
                    self.path_root = '/current_issues'
                    self.current_issues_page()
                elif self.path == '/meet_the_senators':
                    self.path_root = '/meet_the_senators'
                    self.meet_the_senators_page()
                elif self.path.startswith('/submit_opinion'):
                    self.path_root = '/submit_opinion'
                    self.submit_opinion()
                elif self.path.startswith('/vote'):
                    self.path_root = '/vote'
                    self.vote()
                elif self.path.startswith('/verify_email'):
                    self.path_root = '/verify_email'
                    self.verify_email()
                elif self.path == '/approve_opinions':
                    self.path_root = '/approve_opinions'
                    self.approve_opinions_page()
                elif self.path.startswith('/approve'):
                    self.path_root = '/approve'
                    self.approve()
                elif self.path == '/senate':
                    self.path_root = '/senate'
                    self.senate_page()
                elif self.path == '/schedule_opinions':
                    self.path_root = '/schedule_opinions'
                    self.schedule_opinions_page()
                elif self.path.startswith('/schedule_date'):
                    self.path_root = '/schedule_date'
                    self.schedule_date_page()
                elif self.path.startswith('/schedule'):
                    self.path_root = '/schedule'
                    self.schedule()
                elif self.path.startswith('/unschedule'):
                    self.path_root = '/unschedule'
                    self.unschedule()
                elif self.path.startswith('/track_opinions'):
                    self.path_root = '/track_opinions'
                    self.track_opinions_page()
                elif self.path == '/forward_opinions':
                    self.path_root = '/forward_opinions'
                    self.forward_opinions_page()
                elif self.path.startswith('/forward'):
                    self.path_root = '/forward'
                    self.forward()
                elif self.path.startswith('/view_committee'):
                    self.path_root = '/view_committee'
                    self.view_committee_page()
            except ValueError as error:
                print(str(error))
                

    def identify_user(self, nocookie=False):
        my_cookies = SimpleCookie(self.headers.get('Cookie'))
        if 'code' in my_cookies:
            my_code = my_cookies['code'].value
            if my_code in db.user_cookies:
                return db.user_cookies[my_code]
            else:
                raise ValueError(f'ip {self.client_address[0]} -- identify user function got code {my_code}')
        else:
            if nocookie:
                return None
            else:
                raise ValueError(f'ip {self.client_address[0]} -- identify user function got no code in cookies')

    def send_links_head(self):
        self.wfile.write('''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UpDown</title>
<style>
body {
  background-color: #1155ccff;
  margin: 0;
  padding: 0;
}
header {
  position: fixed;
  top: 0;
  width: 100%;
  height: 45px;
  z-index: 2;
}
#hamburger {
  position: absolute;
  top: 0;
  left: 0;
  width: 50px;
  height: 100%;
  z-index: 1;
}
#title {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  text-align: center;
  background-color: #f1c232ff;
  font-size: 30px;
  font-family: 'Times New Roman';
}
#logo {
  position: absolute;
  width: 50px;
  height: 100%;
  top: 0;
  right: 0;
  z-index: 1;
}
/*article {
  position: absolute;
  top: 9%;
  width: 100%;
  height: 90%;
  z-index: 1;
  overflow: scroll;
}*/
#menu {
  width: 0;
  height: 100%;
  position: fixed;
  z-index: 2;
  top: 0;
  left: 0;
  overflow-x: hidden;
  background-color: #f1c232ff;
  /*background-color: #1155ccff;*/
  transition: 0.5s;
}
#menu a {
  position: relative;
  top: 20px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
}
#menu #x_menu {
  position: absolute;
  top: 0;
  right: 0;
  width: 50px;
  height: 45px;
  z-index: 1;
}
</style>'''.encode('utf8'))

    def send_links_head_senate(self):
        self.wfile.write('''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UpDown</title>
<style>
body {
  background-color: #f3f1cfff;
  margin: 0;
  padding: 0;
}
header {
  position: fixed;
  top: 0;
  width: 100%;
  height: 45px;
  z-index: 2;
}
#hamburger {
  position: absolute;
  top: 0;
  left: 0;
  width: 50px;
  height: 100%;
  z-index: 1;
}
#title {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  text-align: center;
  background-color: #ffef90ff;
  color: #37443fff;
  font-size: 30px;
  font-family: 'Times New Roman';
}
#logo {
  position: absolute;
  width: 50px;
  height: 100%;
  top: 0;
  right: 0;
  z-index: 1;
}
/*article {
  position: absolute;
  top: 9%;
  width: 100%;
  height: 90%;
  z-index: 1;
  overflow: scroll;
}*/
#menu {
  width: 0;
  height: 100%;
  position: fixed;
  z-index: 2;
  top: 0;
  left: 0;
  overflow-x: hidden;
  background-color: #f1c232ff;
  /*background-color: #1155ccff;*/
  transition: 0.5s;
}
#menu a {
  position: relative;
  top: 20px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
}
#menu #x_menu {
  position: absolute;
  top: 0;
  right: 0;
  width: 50px;
  height: 45px;
  z-index: 1;
}
</style>'''.encode('utf8'))
        
    def send_links_body(self):
        my_account = self.identify_user()
        title = ''
        if self.path_root == '/':
            title = 'Vote!'
        elif self.path_root == '/track_opinions':
            title = 'Track!'
        elif self.path_root == '/senate':
            title = 'Senate'
        elif self.path_root == '/approve_opinions':
            title = 'Approve'
        elif self.path_root == '/schedule_opinions':
            title = 'Schedule'
        elif self.path_root == '/forward_opinions':
            title = 'Forward'
        elif self.path_root == '/view_committee':
            url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            title = url_arguments['committee'][0]
        self.wfile.write(f'''<header>
<img id='hamburger' src='hamburger.png' onclick='open_menu();'/>
<span id='title'>
{title}
</span>
<img id='logo' src='favicon.ico'/>'''.encode('utf8'))
        self.wfile.write('''<div id='menu'>'''.encode('utf8'))
        self.wfile.write('''<div onclick='close_menu();'><img id='x_menu' src='hamburger.png'/></div>'''.encode('utf8'))
        self.wfile.write('''<a href='/'>Voice Your Opinions</a>
<a href='/track_opinions'>Track an Opinion</a>
<a href='/senate'>The Student Faculty Senate</a>'''.encode('utf8'))
        if my_account.email in local.MODERATORS and my_account.verified_email:
            self.wfile.write('''<a href='/approve_opinions'>Approve Opinions</a>'''.encode('utf8'))
        if my_account.email in local.ADMINS and my_account.verified_email:
            self.wfile.write('''<a href='/schedule_opinions'>Schedule Opinions</a>'''.encode('utf8'))
            self.wfile.write('''<a href='/forward_opinions'>Forward Opinions</a>'''.encode('utf8'))
        for committee, members in local.COMMITTEE_MEMBERS.items():
            if my_account.email in members and my_account.verified_email:
                self.wfile.write(f'''<a href='/view_committee?committee={committee}'>{committee}</a>'''.encode('utf8'))
        self.wfile.write('''</div></header>'''.encode('utf8'))
        self.wfile.write('''<script>
function open_menu() {
    document.getElementById('menu').style.width = '200px';
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
            db.user_cookies[my_account.cookie_code] = my_account
        
        self.run_and_sync(db.user_cookies_lock,
                          update_user_activity,
                          db.user_cookies)
        logging.info(f'{my_account.email} with {my_account.cookie_code} did {activity_unit}')
        
    def run_and_sync(self, lock_needed, change, database):
        lock_needed.acquire()
        try:
            change()
        finally:
            lock_needed.release()

    def load_image(self):
        return SimpleHTTPRequestHandler.do_GET(self)

    def get_email(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f'''<!DOCTYPE HTML>
<html>
<body>
<form method='GET' action='/check_email'>
Enter your school email (must end in @lexingtonma.org):
<input id='email_box' type='email' name='email'/>
<input id='submit' type='submit' disabled='true'/>
</form>

<script>
exceptionEmails = {list(local.EXCEPTION_EMAILS)}
setTimeout(checkEmail, 1000);
function checkEmail() {{
    current_email = document.getElementById('email_box').value;
    console.log('email: ' + current_email);
    if (current_email.endsWith('@lexingtonma.org')) {{
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

    def check_email(self):
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'email' in url_arguments:
            user_email = url_arguments['email'][0]
            if user_email.endswith('@lexingtonma.org') or user_email in local.EXCEPTION_EMAILS:
                email_taken = False
                existing_uuid = None
                existing_code = None
                for cookie, user in db.user_cookies.items():
                    if user.email == user_email:
                        email_taken = True
                        assert user.cookie_code == cookie
                        existing_code = user.cookie_code
                for v_code, c_code in db.verification_links.items():
                    if c_code == existing_code:
                        existing_uuid = v_code

                if email_taken:
                    # send email
                    email_address = user_email
                    gmail_user = local.EMAIL
                    gmail_password = local.PASSWORD
                    sent_from = local.FROM_EMAIL
                    to = email_address
                    subject = 'Add your votes to the count?'
                    body = f'Welcome to the Student Rep App for LHS! Your votes will NOT count until you click on the link below:\n{local.DOMAIN_NAME}/verify_email?verification_id={existing_uuid}'
                    email_text = f'From: {sent_from}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}'
                    try:
                        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                        server.ehlo()
                        server.login(gmail_user, gmail_password)
                        server.sendmail(sent_from, to, email_text)
                        server.close()
                        if MyHandler.DEBUG < 2:
                            print(f'New user with email {email_address}!')
                    except:
                        raise RuntimeError(f'Something went wrong with sending an email to {email_address}.')
                    
                    self.send_response(302)
                    self.send_header('Location', f'/email_taken?email={user_email}')
                    self.end_headers()
                else:
                    #set up uuids so that they are unique
                    my_uuid = uuid.uuid4().hex
                    while my_uuid in db.user_cookies or my_uuid in db.verification_links:
                        my_uuid = uuid.uuid4().hex

                    link_uuid = uuid.uuid4().hex
                    while link_uuid in db.user_cookies or link_uuid in db.verification_links or link_uuid == my_uuid:
                        link_uuid = uuid.uuid4().hex
                    if MyHandler.DEBUG < 2:
                        print(f'{my_uuid=} {link_uuid=}')
                    assert(link_uuid not in db.user_cookies and link_uuid not in db.verification_links)

                    # send email
                    email_address = user_email
                    gmail_user = local.EMAIL
                    gmail_password = local.PASSWORD
                    sent_from = local.FROM_EMAIL
                    to = email_address
                    subject = 'Add your votes to the count?'
                    body = f'Welcome to the Student Rep App for LHS! Your votes will NOT count until you click on the link below:\n{local.DOMAIN_NAME}/verify_email?verification_id={link_uuid}'
                    email_text = f'From: {sent_from}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}'
                    try:
                        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                        server.ehlo()
                        server.login(gmail_user, gmail_password)
                        server.sendmail(sent_from, to, email_text)
                        server.close()
                        if MyHandler.DEBUG < 2:
                            print(f'New user with email {email_address}!')
                    except:
                        raise RuntimeError(f'Something went wrong with sending an email to {email_address}.')

                    # change the databases
                    assert(my_uuid not in db.user_cookies and my_uuid not in db.verification_links)
                    def update_verification_links():
                        db.verification_links[link_uuid] = my_uuid
                    self.run_and_sync(db.verification_links_lock, update_verification_links, db.verification_links)
                    def update_user_cookies():
                        db.user_cookies[my_uuid] = User(user_email, my_uuid)
                    self.run_and_sync(db.user_cookies_lock, update_user_cookies, db.user_cookies)

                    #redirect to homepage so they can vote
                    self.send_response(302)
                    self.send_header('Location', '/')
                    self.send_header('Set-Cookie', f'code={my_uuid}; path=/')
                    self.end_headers()
                    self.log_activity()
            else:
                raise ValueError(f"ip {self.client_address[0]} -- check email function got email {user_email}")
        else:
            raise ValueError(f'ip {self.client_address[0]} -- check email function got url arguments {url_arguments}')

    def email_taken(self):
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'email' in url_arguments:
            user_email = url_arguments['email'][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f'''<!DOCTYPE HTML><html><body>Another device already has the  email {user_email}. If you want to use this email on this device, click on the link sent to {user_email} using this device.</body></html>'''.encode('utf8'))
        else:
            raise ValueError(f"ip {self.client_address[0]} -- email taken function got url_arguments {url_arguments}")

    def verify_email(self):
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        my_account = self.identify_user(True)
        if 'verification_id' in url_arguments:
            link_uuid = url_arguments['verification_id'][0]
            if my_account == None:
                print(f'warning non-viewed user is using verification link! {db.user_cookies[db.verification_links[link_uuid]].email}')
            #if db.verification_links[link_uuid] == my_account.cookie_code:
            # change the account locally
            my_account = db.user_cookies[db.verification_links[link_uuid]]
            my_account.verified_email = True

            # update the database
            def update_user_cookies():
                db.user_cookies[my_account.cookie_code] = my_account
            self.run_and_sync(db.user_cookies_lock, update_user_cookies, db.user_cookies)

            # send success page
            self.send_response(200)
            self.send_header('Set-Cookie', f'code={my_account.cookie_code}; path=/')
            self.end_headers()
            self.wfile.write('''<!DOCTYPE HTML>
<html>
<body>
Thank you for verifying. Your votes are now counted.<br />
<a href='/'>Return to homepage</a>
</body>
</html>'''.encode('utf8'))
            if MyHandler.DEBUG < 2:
                print(f'{my_account.email} just verified their email!')
            self.log_activity()
            #else:
                #raise ValueError(f'ip {self.client_address[0]} -- insecure gmail account: {db.user_cookies[db.verification_links[link_uuid]].email}, their link ({link_uuid}) was opened by {my_account.email}')
        else:
            raise ValueError(f"ip {self.client_address[0]} -- verify email function got link_uuid {link_uuid}")

    def opinions_page(self):
        my_account = self.identify_user()
        self.send_response(200)
        self.end_headers()
        day_of_the_week = datetime.date.today().weekday()
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
article {
  position: absolute;
  top: 50px;
  width: 100%;
  bottom: 0;
  z-index: 1;
  overflow: scroll;
}
section {
  width: 98%;
  height: 50px;
  margin: 1%;
  position: relative;
  background-color: #cfe2f3ff;
  z-index: 1;
  border-radius: 6px;
}
div#end_block {
  width: 100%;
  height: 55px;
  z-index: 1;
}
div.unselected_up {
  color: black;
  width: 20%;
  position: absolute;
  right: 0;
  top: 0;
  text-align: center;
  font-size: 22px;
}
div.unselected_down {
  color: black;
  width: 20%;
  position: absolute;
  right: 0;
  bottom: 0;
  text-align: center;
  font-size: 22px;
}
div.selected_up {
  color : green;
  width: 20%;
  position: absolute;
  right: 0;
  top: 0;
  text-align: center;
  font-size: 22px;
}
div.selected_down {
  color : red;
  width: 20%;
  position: absolute;
  right: 0;
  bottom: 0;
  text-align: center;
  font-size: 22px;
}
span.left {
  width: 75%;
  height: 80%;
  position: absolute;
  left: 5%;
  top: 10%;
}
footer {
  position: fixed;
  bottom: 0;
  width: 100%;
  height: 55px;
  z-index: 1; 
}
button.submit {
  position: absolute;
  left: 2.5%;
  width: 95%;
  height: 90%;
  border-radius: 25px;
  background-color: #f1c232ff;
  z-index: 1;
}
</style>
</head>
<body>'''.encode('utf8'))
        self.send_links_body()
        if str(datetime.date.today()) not in db.opinions_calendar or db.opinions_calendar[str(datetime.date.today())] == set():
            if datetime.date.today().weekday() == 2:
                self.wfile.write('''<article>
Middle Wednesday!<br />
A recap of the week is shown below:<br />
'''.encode('utf8'))
            else:
                self.wfile.write('''<article>Sorry, today's off.<br />See you soon!<br />'''.encode('utf8'))
        else:
            self.wfile.write('<article>'.encode('utf8'))
            randomized = list(db.opinions_calendar[str(datetime.date.today())])
            random.shuffle(randomized)
            for opinion_ID in randomized:
                assert opinion_ID in db.opinions_database
                opinion = db.opinions_database[opinion_ID]
                assert opinion.approved == True
                opinion_ID = str(opinion.ID)
                if my_account.email in local.ADMINS and my_account.verified_email:
                    self.send_opinion(opinion_ID, 'vote')
                else:
                    self.send_opinion(opinion_ID, 'vote_admin')
            self.wfile.write(str('''
<div id='end_block'>
</div>
<script>
const page_IDs = %s;
function vote(element_ID) {
    var xhttp = new XMLHttpRequest();
    var split_ID = element_ID.split(' ');
    const opinion_ID = split_ID[0];
    let old_vote = '';
    if (document.getElementById(opinion_ID + ' up').className.startsWith('selected')) {
        old_vote = 'up';
    }
    else if (document.getElementById(opinion_ID + ' down').className.startsWith('selected')) {
        old_vote = 'down';
    }
    else {
        old_vote = 'abstain';
    }
    const my_click = split_ID[1];
    let my_vote = '';
    if (my_click != old_vote) {
        my_vote = my_click;
    }
    else {
        my_vote = 'abstain';
    }
    
    if (checkVoteValidity(my_vote, old_vote)) {
        xhttp.open('GET', '/vote?opinion_ID=' + opinion_ID + '&my_vote=' + my_vote, true);
        xhttp.send();
        if (my_vote == old_vote) {
            document.getElementById(element_ID).className = 'unselected_' + my_vote;
        }
        else {
            if (old_vote != 'abstain') {
                let other_arrow = document.getElementById(opinion_ID + ' ' + old_vote);
                other_arrow.className = 'unselected_' + old_vote;
            }
            if (my_vote != 'abstain') {
                if (my_vote == 'up') {
                    document.getElementById(element_ID).className = 'selected_up';
                }
                else {
                    document.getElementById(element_ID).className = 'selected_down';
                }
            }
        }
    }
}
function checkVoteValidity(new_vote, old_vote) {
    let up_count = 0;
    let down_count = 0;
    for (let index = 0; index < page_IDs.length; index++) {
        if (document.getElementById(page_IDs[index] + ' up').className.startsWith('selected')) {
            up_count++;
        }
        else if (document.getElementById(page_IDs[index] + ' down').className.startsWith('selected')) {
            down_count++;
        }
    }
    let valid = true;
    if (up_count == 5 && new_vote == 'up') {
        alert('You cannot vote up more than 5 times a day. Prioritize the opinions that you feel more strongly about and leave the others unvoted.');
        valid = false;
    }
    else if (down_count == 5 && new_vote == 'down') {
        alert('You cannot vote down more than 5 times a day. Prioritize the opinions that you feel more strongly about and leave the others unvoted.');
        valid = false;
    }
    if (old_vote == 'abstain') {
        if (up_count + down_count == 8 && new_vote != 'abstain') {
            alert('You cannot vote more than 8 times a day. Prioritize the opinions that you feel more strongly about and leave the others unvoted.');
            valid = false;
        }
    }
    return valid;
}
</script>
</article>''' % (list(db.opinions_calendar[str(datetime.date.today())]))).encode('utf8'))
        self.wfile.write('''<footer>
<!--<input id='opinion_text' type='text'/>-->
<button class='submit' onclick='submit_opinion()'>Enter a new Opinion</button>
<script>
function submit_opinion() {
    var xhttp = new XMLHttpRequest();
    const opinion_text = prompt('Thank you for your input. Please enter your opinion below:');
    if (opinion_text != '' && opinion_text != null) {
        xhttp.open('GET', '/submit_opinion?opinion_text=' + opinion_text, true);
        xhttp.send();
        //alert('Your opinion was submitted. Thank you!');
    }
}
</script>
</footer>'''.encode('utf8'))
        self.wfile.write('</body></html>'.encode('utf8'))
        self.log_activity()

    def approve_opinions_page(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
            self.send_response(200)
            self.end_headers()
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
div.unselected {
    color : black;
}
div.selected {
    color : red;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write('<article><table>'.encode('utf8'))
            for opinion_ID, opinion in db.opinions_database.items():
                if opinion.approved == None:
                    self.wfile.write(f'''<tr id={opinion_ID}><td>{opinion.text}</td><td><div class='unselected' id='{opinion_ID} yes' onclick='vote(this.id)'>&#10003;</div><div class='unselected' id='{opinion_ID} no' onclick='vote(this.id)'>&#10005;</div></td></tr>'''.encode('utf8'))
            self.wfile.write('</table></article>'.encode('utf8'))
            self.wfile.write('''<script>
function vote(element_ID) {
    var xhttp = new XMLHttpRequest();
    var split_ID = element_ID.split(' ');
    const opinion_ID = split_ID[0];

    const my_vote = split_ID[1];

    xhttp.open('GET', '/approve?opinion_ID=' + opinion_ID + '&my_vote=' + my_vote, true);
    xhttp.send();

    document.getElementById(opinion_ID).style = 'display : none;';
}
</script>'''.encode('utf8'))
            self.wfile.write('</body></html>'.encode('utf8'))
            self.log_activity()

    def senate_page(self):
        my_account = self.identify_user()
        self.send_response(200)
        self.end_headers()
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
article {
  position: absolute;
  top: 80px;
  bottom: 0;
  width: 100%;
  z-index: 1;
  overflow: scroll;
  background-color: #cfe2f3ff;
}
#back_to_top {
  position: absolute;
  top: 50px;
  width: 100%;
  border: 2px solid black;
  background-color: lightGray;
}
</style>'''.encode('utf8'))
        self.wfile.write('</head><body>'.encode('utf8'))
        self.send_links_body()
        self.wfile.write('''<div id='back_to_top'><a href='/senate#top'>Back to the top</a></div>'''.encode('utf8'))
        self.wfile.write('''<article>Click <a name='top' href='https://senate.lex.ma/constitution/'>here</a> to see the Senate's website!'''.encode('utf8'))
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
        
    def submit_opinion(self):
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        my_account = self.identify_user()
        if 'opinion_text' in url_arguments and not my_account == False:
            opinion_text = url_arguments['opinion_text'][0]
            opinion_ID = len(db.opinions_database)
            assert str(opinion_ID) not in db.opinions_database
            def update_opinions_database():
                db.opinions_database[str(opinion_ID)] = Opinion(opinion_ID, opinion_text, [(my_account.cookie_code, datetime.datetime.now())])
            self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)
            self.send_response(200)
            self.end_headers()
            self.log_activity([opinion_ID])
        else:
            raise ValueError(f'ip {self.client_address[0]} -- submit opinion function got url arguments {url_arguments}')

    def vote(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'opinion_ID' in url_arguments and 'my_vote' in url_arguments:
            opinion_ID = url_arguments['opinion_ID'][0]
            my_vote = url_arguments['my_vote'][0]
            if opinion_ID in db.opinions_database and my_vote in ('up', 'down', 'abstain'):
                if opinion_ID in my_account.votes:
                    my_account.votes[opinion_ID].append((my_vote, datetime.datetime.now()))
                else:
                    my_account.votes[opinion_ID] = [(my_vote, datetime.datetime.now())]
                for other_opinion_ID in db.opinions_calendar[str(datetime.date.today())]:
                    if other_opinion_ID != opinion_ID and other_opinion_ID not in my_account.votes:
                        my_account.votes[other_opinion_ID] = [('abstain', datetime.datetime.now())]

                def update_user_cookies():
                    db.user_cookies[my_account.cookie_code] = my_account                    
                self.run_and_sync(db.user_cookies_lock, update_user_cookies, db.user_cookies)

                self.send_response(200)
                self.end_headers()
                if MyHandler.DEBUG < 2:
                    print(f'{my_account.email=} has voted {my_vote=}')

                self.log_activity([my_vote, opinion_ID])
            else:
                raise ValueError(f'ip {self.client_address[0]} -- vote function got opinion ID {opinion_ID} and vote {my_vote}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- vote function got url arguments {url_arguments}')

    def approve(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
            url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
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
                        db.user_cookies[my_account.cookie_code] = my_account
                    self.run_and_sync(db.user_cookies_lock, update_user_cookies, db.user_cookies)

                    self.send_response(200)
                    self.end_headers()
                    
                    self.log_activity([my_vote, opinion_ID])
                    
                else:
                    raise ValueError(f'ip {self.client_address[0]} -- approval function got opinion ID {opinion_ID} and vote {my_vote}')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- approval function got url arguments {url_arguments}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- approval function got user {user.email}, who is not a moderator.')

    def schedule_opinions_page(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
            self.send_response(200)
            self.end_headers()
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
  border-color : black;
  border-style : solid;
  border-width : 2px;
  padding : 5px;
  width : 80px;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write('''<article>CALENDAR:
<table>
<tr>'''.encode('utf8'))
            today_date = datetime.date.today()
            for day_of_week in range(7):
                self.wfile.write(f'<td>{calendar.day_name[day_of_week]}</td>'.encode('utf8'))
            self.wfile.write('</tr><tr>'.encode('utf8'))
            for day in range(calendar.monthrange(today_date.year, today_date.month)[0]):
                self.wfile.write('<td></td>'.encode('utf8'))
            for day_number in range(1, calendar.monthrange(today_date.year, today_date.month)[1] + 1):
                this_date = datetime.date(today_date.year, today_date.month, day_number)
                already_selected = 0
                if str(this_date) in db.opinions_calendar:
                    already_selected = len(db.opinions_calendar[str(this_date)])
                if this_date.weekday() == 0 and not day_number == 1:
                    self.wfile.write('</tr>'.encode('utf8'))
                    if not day_number == calendar.monthrange(today_date.year, today_date.month)[1]:
                        self.wfile.write('<tr>'.encode('utf8'))
                self.wfile.write(f'''<td onclick='document.location.href="/schedule_date?date={this_date}"'>{day_number}<br />{already_selected}/10</td>'''.encode('utf8'))
            for day in range(35 - (calendar.monthrange(today_date.year, today_date.month)[1]) - calendar.monthrange(today_date.year, today_date.month)[0]):
                self.wfile.write('<td></td>'.encode('utf8'))
            self.wfile.write('</tr>'.encode('utf8'))
            self.wfile.write('</table></article>'.encode('utf8'))
            self.wfile.write('</body></html>'.encode('utf8'))

            self.log_activity()
            
        else:
            raise ValueError(f'ip {self.client_address[0]} -- schedule_opinions function got user {user.email}, who is not an admin.')

    def schedule_date_page(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
            url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if 'date' in url_arguments:
                this_date = url_arguments["date"][0]
                try:
                    datetime.datetime.strptime(this_date, '%Y-%m-%d')
                except ValueError:
                    raise ValueError(e + f'ip {self.client_address[0]} -- schedule date function got date {url_arguments["date"][0]}')
                self.send_response(200)
                self.end_headers()
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
        if my_account.email in local.ADMINS and my_account.verified_email:
            url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
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
                    if MyHandler.DEBUG < 2:
                        print(f'selected originally: {selected}')
                    selected.add(opinion_ID)
                    if MyHandler.DEBUG < 2:
                        print(f'selected after: {selected}')
                        
                    def update_opinions_calendar():
                        db.opinions_calendar[this_date] = selected
                    self.run_and_sync(db.opinions_calendar_lock, update_opinions_calendar, db.opinions_calendar)
                    
                    self.send_response(200)
                    self.end_headers()

                    self.log_activity([this_date, opinion_ID])
                    
                else:
                    raise ValueError(f'ip {self.client_address[0]} -- schedule function got opinion ID {opinion_ID}, not in the database')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- schedule function got url arguments {url_arguments}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- schedule date function got user {user.email}, who is not an admin.')

    def unschedule(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
            url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
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
                    if MyHandler.DEBUG < 2:
                        print(f'selected originally: {selected}')
                    selected.remove(opinion_ID)
                    if MyHandler.DEBUG < 2:
                        print(f'selected after: {selected}')

                    def update_opinions_calendar():
                        db.opinions_calendar[this_date] = selected
                    self.run_and_sync(db.opinions_calendar_lock, update_opinions_calendar, db.opinions_calendar)

                    self.send_response(200)
                    self.end_headers()

                    self.log_activity([this_date, opinion_ID])
                    
                else:
                    raise ValueError(f'ip {self.client_address[0]} -- unschedule function got opinion ID {opinion_ID}, not in the database')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- unschedule function got url arguments {url_arguments}')
        else:
            raise ValueError(f'ip {self.client_address[0]} -- unschedule date function got user {user.email}, who is not an admin.')

    def track_opinions_page(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        self.send_response(200)
        self.end_headers()
        self.wfile.write('<!DOCTYPE HTML><html><head>'.encode('utf8'))
        self.send_links_head()
        self.wfile.write('''<style>
article {
  position: absolute;
  top: 50px;
  width: 100%;
  height: 41%;
  z-index: 1;
  overflow: scroll;
}
div#timeline_line {
  position: absolute;
  height: 100%;
  width: 10px;
  left: 20px;
  background-color: gray;
}
div#timeline {
  position: absolute;
  right: 0;
  left: 50px;
  height: 100%;
}
div.element {
  position: absolute;
  right: 20px;
  left: 0;
  height: 8%;
}
div.label {
  position: absolute;
  left: 0;
  width: 60%;
}
div.stat {
  position: absolute;
  right: 0;
  width: 40%;
  text-align: right;
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
span.left {
  height: 80%;
  top: 10%;
  position: absolute;
  left: 5px;
  right: 100px;
}
span.status {
  width: 100px;
  height: 100%;
  position: absolute;
  right: 0;
}
</style>'''.encode('utf8'))
        self.wfile.write('</head><body>'.encode('utf8'))
        self.send_links_body()
        self.wfile.write('<article>'.encode('utf8'))
        self.wfile.write('''<div id='timeline_line'>
</div>
<div id='timeline'>
<div class='element' style='top: 0;'>
<div class='label'>
Creation
</div>
<div class='stat'>
Stat
</div>
</div>
<div class='element' style='top: 16.6%;'>
<div class='label'>
Approval
</div>
<div class='stat'>
Stat
</div>
</div>
<div class='element' style='top: 33.2%;'>
<div class='label'>
Scheduling
</div>
<div class='stat'>
Stat
</div>
</div>
<div class='element' style='top: 49.8%;'>
<div class='label'>
Voting
</div>
<div class='stat'>
Stat
</div>
</div>
<div class='element' style='top: 66.4%;'>
<div class='label'>
Senate
</div>
<div class='stat'>
Stat
</div>
</div>
<div class='element' style='top: 83%;'>
<div class='label'>
Bill or Resolution
</div>
<div class='stat'>
Stat
</div>
</div>'''.encode('utf8'))
        self.wfile.write('</article>'.encode('utf8'))
        self.wfile.write('''<footer><form method='GET' action='/track_opinions'><input id='search_bar' type='text' name='words' placeholder='search...'/></form><div id='results'>'''.encode('utf8'))

        if 'words' in url_arguments:
            for opinion_ID in search(url_arguments['words'][0]):
                opinion = db.opinions_database[str(opinion_ID)]
                # timeline: creation, approval, scheduled (vote), successful (passed to senate), expected bill draft date, date of senate hearing
                # timeline: creation, approval, scheduled (vote), unsuccessful (failed)
                message = None
                if len(opinion.activity) == 1:
                    message = 'PRE-APPROVAL'
                elif len(opinion.activity) == 2:
                    #assert opinion.activity[1][1] in ('yes', 'no')
                    #assert len(opinion.activity[1]) == 3
                    assert opinion.approved in (True, False)
                    if opinion.approved:
                        message = f'APPROVED'
                    else:
                        message = f'REJECTED'
                elif len(opinion.activity) == 3:
                    #assert len(opinion.activity[2]) == 4
                    if datetime.date.today() < opinion.activity[2][0][2]:
                        message = 'SCHEDULED'
                    elif datetime.date.today() > opinion.activity[2][0][2]:
                        message = 'PRE-SENATE'
                    else:
                        message = 'VOTING'
                elif len(opinion.activity) == 4:
                    #assert len(opinion.activity[3]) == 3, f'{opinion.activity}'
                    assert opinion.activity[3][0][1] in local.COMMITTEE_MEMBERS, f'{opinion.activity[3][1]}'
                    if opinion.activity[3][0][1] != 'no':
                        message = f'{opinion.activity[3][0][1].upper()}'
                    else:
                        message = 'UNSUCCESSFUL'
                elif len(opinion.activity) == 5:
                    #assert len(opinion.activity[4]) == 3
                    message = 'PRE-BILL'
                self.wfile.write(f'''<div class='result'>
<span class='left'>
{opinion.text}
</span>
<span class='status'>
{message}
</span>
</div>'''.encode('utf8'))
            
        else:
            for opinion_ID, opinion in db.opinions_database.items():
                # timeline: creation, approval, scheduled (vote), successful (passed to senate), expected bill draft date, date of senate hearing
                # timeline: creation, approval, scheduled (vote), unsuccessful (failed)
                message = None
                if len(opinion.activity) == 1:
                    message = 'PRE-APPROVAL'
                elif len(opinion.activity) == 2:
                    #assert opinion.activity[1][1] in ('yes', 'no')
                    #assert len(opinion.activity[1]) == 3
                    assert opinion.approved in (True, False)
                    if opinion.approved:
                        message = f'APPROVED'
                    else:
                        message = f'REJECTED'
                elif len(opinion.activity) == 3:
                    #assert len(opinion.activity[2]) == 4
                    if datetime.date.today() < opinion.activity[2][0][2]:
                        message = 'SCHEDULED'
                    elif datetime.date.today() > opinion.activity[2][0][2]:
                        message = 'PRE-SENATE'
                    else:
                        message = 'VOTING'
                elif len(opinion.activity) == 4:
                    #assert len(opinion.activity[3]) == 3, f'{opinion.activity}'
                    assert opinion.activity[3][0][1] in local.COMMITTEE_MEMBERS, f'{opinion.activity[3][1]}'
                    if opinion.activity[3][0][1] != 'no':
                        message = f'{opinion.activity[3][0][1].upper()}'
                    else:
                        message = 'UNSUCCESSFUL'
                elif len(opinion.activity) == 5:
                    #assert len(opinion.activity[4]) == 3
                    message = 'PRE-BILL'
                self.wfile.write(f'''<div class='result'>
<span class='left'>
{opinion.text}
</span>
<span class='status'>
{message}
</span>
</div>'''.encode('utf8'))
            self.wfile.write('</div></footer>'.encode('utf8'))
            self.wfile.write('''</body></html>'''.encode('utf8'))

        self.log_activity()

    def forward_opinions_page(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
            self.send_response(200)
            self.end_headers()
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
td.up {
  color: limegreen;
}
td.care {
  color: black;
}
tr.selected {
  background-color: yellow;
}
tr.unselected {
  background-color: white;
}
</style>
</head>
<body>'''.encode('utf8'))
            self.send_links_body()
            self.wfile.write('''<article>
<table>
<tr>
<td>
<table>'''.encode('utf8'))
            sorted_dates = list(db.opinions_calendar.keys())
            sorted_dates.sort()
            opinion_ID_list = []
            for this_date in sorted_dates[::-1]:
                if datetime.datetime.strptime(this_date, '%Y-%m-%d').date() < datetime.date.today():
                    opinion_set = db.opinions_calendar[this_date]
                    self.wfile.write(f'''<tr><td colspan='3'>{this_date}</td></tr>'''.encode('utf8'))
                    for opinion_ID in list(opinion_set):
                        opinion = db.opinions_database[opinion_ID]
                        if opinion.committee_jurisdiction == None:
                            up_votes, down_votes, abstains = opinion.count_votes()
                            up_percent = 'N/A'
                            if up_votes + down_votes != 0:
                                up_percent = up_votes / (up_votes + down_votes) * 100
                            care_percent = 'N/A'
                            if up_votes + down_votes + abstains != 0:
                                care_percent = up_votes / (up_votes + down_votes + abstains) * 100
                            self.wfile.write(f'''<tr id='{opinion_ID}' onclick='select(this);' class='unselected'><td>{opinion.text}</td><td class='care'>{care_percent}%</td><td class='up'>{up_percent}%</td></tr>'''.encode('utf8'))
                            opinion_ID_list.append(opinion_ID)
            self.wfile.write('''</table></td><td>
<button id='Executive' onclick='forward(this);'>EXECUTIVE</button><br />
<button id='Oversight' onclick='forward(this);'>OVERSIGHT</button><br />
<!--<button id='Communications' onclick='forward(this);'>COMMUNICATIONS</button><br />-->
<!--<button id='Policy' onclick='forward(this);'>POLICY</button><br />-->
<!--<button id='Social_action' onclick='forward(this);'>SOCIAL ACTION</button><br />-->
<!--<button id='Climate' onclick='forward(this);'>CLIMATE</button><br />-->
</td></tr></table></article>'''.encode('utf8'))
            self.wfile.write(f'''<script>
opinionList = {opinion_ID_list};
let selected = opinionList[0];
document.getElementById(selected).className = 'selected';
function select(element) {{
    document.getElementById(selected).className = 'unselected';
    element.className = 'selected';
    selected = element.id;
}}
function forward(element) {{
    var xhttp = new XMLHttpRequest();
    xhttp.open('GET', '/forward?committee=' + element.id + '&opinion_ID=' + selected, true);
    xhttp.send();
    document.getElementById(selected).style = 'display: none;';
}}

</script>'''.encode('utf8'))
            self.wfile.write('''</body></html>'''.encode('utf8'))
            
            self.log_activity()
        else:
            raise ValueError(f'ip {self.client_address[0]} -- unschedule date function got user {user.email}, who is not an admin.')

    def forward(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
            url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if 'opinion_ID' in url_arguments and 'committee' in url_arguments:
                opinion_ID = url_arguments['opinion_ID'][0]
                opinion = db.opinions_database[opinion_ID]
                committee = url_arguments['committee'][0]
                if committee in ('Executive', 'Oversight'):
    
                    self.log_activity([committee, opinion_ID])

                    if len(opinion.activity) == 3:
                        opinion.activity.append([(my_account.email, committee, datetime.datetime.now())])
                    else:
                        opinion.activity[3].append((my_account.email, committee, datetime.datetime.now()))

                    opinion.committee_jurisdiction = committee
                    def update_opinions_database():
                        db.opinions_database[opinion_ID] = opinion
                    self.run_and_sync(db.opinions_database_lock, update_opinions_database, db.opinions_database)

                    self.send_response(200)
                    self.end_headers()

    def view_committee_page(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        committee = url_arguments['committee'][0]
        if committee in ('Executive', 'Oversight'):
            if my_account.email in local.COMMITTEE_MEMBERS[committee] and my_account.verified_email:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f'<!DOCTYPE HTML><html><head>'.encode('utf8'))
                self.send_links_head()
                self.wfile.write('''<style>
article {
  position: absolute;
  top: 50px;
  width: 100%;
  height: 91%;
  z-index: 1;
  overflow: scroll;
}
td.up {
  color: limegreen;
}
td.care {
  color: black;
}
</style>
</head>
<body>'''.encode('utf8'))
                self.send_links_body()
                self.wfile.write(f'<article>Committee page: {committee}<br /><table>'.encode('utf8'))
                for opinion_ID, opinion in db.opinions_database.items():
                    if opinion.committee_jurisdiction == committee:
                        up_votes, down_votes, abstains = opinion.count_votes()
                        up_percent = 'N/A'
                        if up_votes + down_votes != 0:
                            up_percent = up_votes / (up_votes + down_votes) * 100
                        care_percent = 'N/A'
                        if up_votes + down_votes + abstains != 0:
                            care_percent = up_votes / (up_votes + down_votes + abstains) * 100
                        self.wfile.write(f'''<tr id='{opinion_ID}' class='unselected'><td>{opinion.text}</td><td class='care'>{care_percent}%</td><td class='up'>{up_percent}%</td></tr>'''.encode('utf8'))
                self.wfile.write('</table></article>'.encode('utf8'))
                self.wfile.write('''</body></html>'''.encode('utf8'))

    def send_opinion(self, opinion_ID, view_type='vote'):
        my_account = self.identify_user()
        opinion = db.opinions_database[opinion_ID]
        up_votes, down_votes, abstains = opinion.count_votes()
        self.wfile.write('<section>'.encode('utf8'))
        if view_type == 'vote':
            if opinion_ID in my_account.votes:
                my_vote = my_account.votes[opinion_ID]
                if my_vote[-1][0] == 'up':
                    #arrow up = &#9650
                    #arrow down = &#9660
                    #thumbs up = &#128077;
                    #thumbs down = &#128078;
                    self.wfile.write(f'''<span class='left'>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</span><div class='selected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='unselected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div>'''.encode('utf8'))
                elif my_vote[-1][0] == 'down':
                    self.wfile.write(f'''<span class='left'>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</span><div class='unselected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='selected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div>'''.encode('utf8'))
                else:
                    self.wfile.write(f'''<span class='left'>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</span><div class='unselected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='unselected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div>'''.encode('utf8'))
            else:
                self.wfile.write(f'''<span class='left'>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</span><div class='unselected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='unselected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div>'''.encode('utf8'))
        elif view_type == 'vote_admin':
            if opinion_ID in my_account.votes:
                my_vote = my_account.votes[opinion_ID]
                if my_vote[-1][0] == 'up':
                    self.wfile.write(f'''<span class='left'>{opinion.text}</span><div class='selected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='unselected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div>'''.encode('utf8'))
                elif my_vote[-1][0] == 'down':
                    self.wfile.write(f'''<span class='left'>{opinion.text}</span><div class='unselected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='selected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div>'''.encode('utf8'))
                else:
                    self.wfile.write(f'''<span class='left'>{opinion.text}</span><div class='unselected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='unselected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div>'''.encode('utf8'))
            else:
                self.wfile.write(f'''<span class='left'>{opinion.text}</span><div class='unselected_up' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='unselected_down' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div>'''.encode('utf8'))
        self.wfile.write('</section>'.encode('utf8'))


class ReuseHTTPServer(ThreadingHTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
    
class User:

    def __init__(self, email, cookie_code, activity={}, votes={}, verified_email=False):

        self.email = email
        self.cookie_code = cookie_code
        self.activity = activity
        self.votes = votes
        self.verified_email = verified_email

class Opinion:

    def __init__(self, ID, text, activity, approved=None, scheduled=False, committee_jurisdiction=None):

        self.ID = ID
        self.text = text
        self.activity = activity
        self.approved = approved
        self.scheduled = scheduled
        self.committee_jurisdiction = committee_jurisdiction

    def count_votes(self):
        up_votes = 0
        down_votes = 0
        abstains = 0
        for user in db.user_cookies.values():
            if user.verified_email and str(self.ID) in user.votes:
                    this_vote = user.votes[str(self.ID)][-1][0]
                    #print(f'{user.email=} has voted {this_vote=}')
                    if this_vote == 'up':
                        up_votes += 1
                    elif this_vote == 'down':
                        down_votes += 1
                    elif this_vote == 'abstain':
                        abstains += 1
                    else:
                        raise ValueError(f'Found a vote other than up, down, or abstain: {this_vote}')
        return up_votes, down_votes, abstains

class invalidCookie(ValueError):
    def __init__(self, message):
        super().__init__(message)

def simplify_text(text):
    split_text = re.split('''\W+''', text)
    if split_text[-1] == '':
        split_text = split_text[:-1]
    for index in range(len(split_text)):
        split_text[index] = split_text[index].lower()
    return split_text

def build_search_index():
    for opinion_ID in range(len(db.opinions_database)):
        opinion = db.opinions_database[str(opinion_ID)]
        split_text = simplify_text(opinion.text)
            
        print(f'{opinion.text} -- {split_text=}')

        for word in split_text:
            if word in SEARCH_INDEX:
                SEARCH_INDEX[word].append(opinion_ID)
            else:
                SEARCH_INDEX[word] = [opinion_ID]

        print(f'{SEARCH_INDEX}')

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
    

def main():
    print('Student Change Web App... running...')

    build_search_index()

    if MyHandler.DEBUG == 0:
        print(f'\n{db.user_cookies=}')
        for cookie, user in db.user_cookies.items():
            print(f'  {cookie} : User({user.email}, {user.cookie_code}, {user.activity}, {user.votes}, {user.verified_email})')

        print(f'\n{db.verification_links=}')
        for link, ID in db.verification_links.items():
            print(f'  {link} : {ID}')

        print(f'\n{db.opinions_database=}')
        for ID, opinion in db.opinions_database.items():
            print(f'  {ID} : Opinion({opinion.ID}, {opinion.text}, {opinion.activity}, {opinion.approved})')

        print(f'\n{db.opinions_calendar=}')
        sorted_calendar = list(db.opinions_calendar.keys())
        sorted_calendar.sort()
        for this_date in sorted_calendar:
            ID_set = db.opinions_calendar[this_date]
            print(f'  {this_date} : {ID_set}')


    logging.basicConfig(filename='UpDown.log', encoding='utf-8', level=logging.DEBUG)
            
    httpd = ReuseHTTPServer(('0.0.0.0', 80), MyHandler)
    httpd.serve_forever()
    

SEARCH_INDEX = {}
    
if __name__ == '__main__':
    main()
