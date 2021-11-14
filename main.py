import urllib.parse
import socket
from http.cookies import SimpleCookie
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import re
import json
import uuid
import db
import local
from datetime import datetime


class MyHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        my_cookies = SimpleCookie(self.headers.get('Cookie'))
        if not self.path == '/favicon.ico':
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

        if invalid_cookie and not self.path.startswith('/check_email'):
            self.get_email()
        else:
            try:
                if self.path == '/':
                    self.opinions_page()
                elif self.path == '/favicon.ico':
                    self.send_response(404)
                    self.end_headers()
                elif self.path.startswith('/check_email'):
                    self.check_email()
                elif self.path == '/about_the_senate':
                    self.about_the_senate_page()
                elif self.path == '/current_issues':
                    self.current_issues_page()
                elif self.path == '/meet_the_senators':
                    self.meet_the_senators_page()
                elif self.path.startswith('/submit_opinion'):
                    self.submit_opinion()
                elif self.path.startswith('/vote'):
                    self.vote()
            except invalidCookie as error:
                print(str(error))
                

    def identify_user(self):
        my_cookies = SimpleCookie(self.headers.get('Cookie'))
        if 'code' in my_cookies:
            my_code = my_cookies['code'].value
            if my_code in db.user_cookies:
                return db.user_cookies[my_code]
            else:
                raise ValueError(f'CODE NOT IN USER_COOKIES DATABASE FOUND! {my_code=}')
        else:
            return

    def get_email(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html>
<body>
<form method='GET' action='/check_email'>
Enter your school email (must end in @lexingtonma.org):
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
            if url_arguments['email'][0].endswith('@lexingtonma.org'):
                #send confirmation email
                #record email + create account
                my_uuid = uuid.uuid1().hex
                email_address = url_arguments['email'][0]
                db.user_cookies_lock.acquire()
                try:
                    while my_uuid in db.user_cookies:
                        my_uuid = uuid.uuid1().hex
                    db.user_cookies[my_uuid] = User(url_arguments['email'][0], my_uuid)
                    db.user_cookies.sync()
                    self.send_response(302)
                    self.send_header('Location', '/')
                    self.send_header('Set-Cookie', f'code={my_uuid}; path=/')
                    self.end_headers()
                finally:
                    db.user_cookies_lock.release()

    def opinions_page(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html>
<head>
<style>
div.unselected {
    color : black;
}
div.selected {
    color : red;
}
</style>
</head>
<body>'''.encode('utf8'))
        self.wfile.write('<table>'.encode('utf8'))
        for opinion_ID, opinion in db.opinions_database.items():
            self.wfile.write(f'''<tr><td>{opinion.text}</td><td><div id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div></td></tr>'''.encode('utf8'))
        self.wfile.write('</table>'.encode('utf8'))
        self.wfile.write('''<br />
<input id='opinion_text' type='text'/>
<button onclick='submit_opinion()'>SUBMIT</button>
<script>
function submit_opinion() {
    var xhttp = new XMLHttpRequest();
    const opinion_text = document.getElementById('opinion_text').value;
    xhttp.open('GET', '/submit_opinion?opinion_text=' + opinion_text, true);
    xhttp.send();
    document.getElementById('opinion_text').value = '';
    alert('Your opinion was submitted. Thank you!');
}
function vote(element_ID) {
    var xhttp = new XMLHttpRequest();
    var split_ID = element_ID.split(' ');
    const opinion_ID = split_ID[0];
    const my_vote = split_ID[1];
    xhttp.open('GET', '/vote?opinion_ID=' + opinion_ID + '&my_vote=' + my_vote, true);
    xhttp.send();
    
    let arrow = document.getElementById(element_ID);
    arrow.style = 'color : red';

    if (my_vote == 'up') {
        let other_arrow = document.getElementById(opinion_ID + ' down');
        other_arrow.style = 'color : black';
    }
    else if (my_vote == 'down') {
        let other_arrow = document.getElementById(opinion_ID + ' up');
        other_arrow.style = 'color : black';
    }
    else {
        arrow.style = 'color : black';
    }
}
</script>
<br />'''.encode('utf8'))
        self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/about_the_senate'>About the Student Faculty Senate</a><br /><a href='/current_issues'>View Current Issues</a><br /><a href='/meet_the_senators'>Meet the Senators</a>'''.encode('utf8'))
        self.wfile.write('</body></html>'.encode('utf8'))

    def about_the_senate_page(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html><body>'''.encode('utf8'))
        self.wfile.write('''<h2>About the Senate</h2>
Welcome to the Lexington High School Student-Faculty Senate! The Senate convenes at 3:15pm on Wednesdays in the Library Media Center.
We implement school-wide policies on a number of issues, from things as mundane as placing extra benches around the school to changes as significant as eliminating the community service requirement for open campus, allowing students to eat in the Quad, or determining what information will be printed on transcripts.<br />
All meetings are open to the public! If you want to change something about the school, we would love to hear and discuss your ideas.'''.encode('utf8'))
        self.wfile.write('''<br /><br /><a href='/'>Voice Your Opinions</a><br /><a href='/about_the_senate'>About the Student Faculty Senate</a><br /><a href='/current_issues'>View Current Issues</a><br /><a href='/meet_the_senators'>Meet the Senators</a>'''.encode('utf8'))
        self.wfile.write('''</body></html>'''.encode('utf8'))

    def current_issues_page(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html><body>'''.encode('utf8'))
        self.wfile.write('''You have reached the current issues page.'''.encode('utf8'))
        self.wfile.write('''<br /><br /><a href='/'>Voice Your Opinions</a><br /><a href='/about_the_senate'>About the Student Faculty Senate</a><br /><a href='/current_issues'>View Current Issues</a><br /><a href='/meet_the_senators'>Meet the Senators</a>'''.encode('utf8'))
        self.wfile.write('''</body></html>'''.encode('utf8'))

    def meet_the_senators_page(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html><body>'''.encode('utf8'))
        self.wfile.write(f'''<h2>Meet the Senators</h2>
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

        self.wfile.write('''<br /><br /><a href='/'>Voice Your Opinions</a><br /><a href='/about_the_senate'>About the Student Faculty Senate</a><br /><a href='/current_issues'>View Current Issues</a><br /><a href='/meet_the_senators'>Meet the Senators</a>'''.encode('utf8'))
        self.wfile.write('''</body></html>'''.encode('utf8'))

    def submit_opinion(self):
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        my_account = self.identify_user()
        if 'opinion_text' in url_arguments and not my_account == False:
            opinion_text = url_arguments['opinion_text'][0]
            db.opinions_database_lock.acquire()
            try:
                opinion_ID = len(db.opinions_database)
                assert str(opinion_ID) not in db.opinions_database
                db.opinions_database[str(opinion_ID)] = Opinion(opinion_ID, opinion_text, [(my_account.cookie_code, datetime.now())])
                db.opinions_database.sync()
            finally:
                db.opinions_database_lock.release()
            self.send_response(200)
            self.end_headers()

    def vote(self):
        my_account = self.identify_user()
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'opinion_ID' in url_arguments and 'my_vote' in url_arguments:
            opinion_ID = url_arguments['opinion_ID'][0]
            my_vote = url_arguments['my_vote'][0]
            if opinion_ID in my_account.votes:
                my_account.votes[opinion_ID].append((my_vote, datetime.now()))
            else:
                my_account.votes[opinion_ID] = [(my_vote, datetime.now())]
            db.user_cookies_lock.acquire()
            try:
                db.user_cookies[my_account.cookie_code] = my_account
                db.user_cookies.sync()
            finally:
                db.user_cookies_lock.release()
                
            self.send_response(200)
            self.end_headers()

        
class ReuseHTTPServer(HTTPServer):    
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
    
class User:

    def __init__(self, email, cookie_code, activity=[], votes={}, confirmed_email=False):
                 
        self.email = email
        self.cookie_code = cookie_code
        self.activity = activity
        self.votes = votes
        self.confirmed_email = confirmed_email

class Opinion:

    def __init__(self, ID, text, activity):

        self.ID = ID
        self.text = text
        self.activity = activity

class invalidCookie(ValueError):
    def __init__(self, message):
        super().__init__(message)
    

def main():
    print('Student Change Web App... running...')

    print(f'\n{db.user_cookies=}')
    for cookie, user in db.user_cookies.items():
        print(f'  {cookie} : User({user.email}, {user.cookie_code}, {user.activity}, {user.votes}, {user.confirmed_email})')

    print(f'\n{db.opinions_database=}')
    for ID, opinion in db.opinions_database.items():
        print(f'  {ID} : Opinion({opinion.ID}, {opinion.text}, {opinion.activity})')
        
    httpd = ReuseHTTPServer(('0.0.0.0', 8888), MyHandler)
    httpd.serve_forever()
    

if __name__ == '__main__':
    main()
