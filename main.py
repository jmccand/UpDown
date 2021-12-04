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
import datetime
import smtplib

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
                elif self.path.startswith('/verify_email'):
                    self.verify_email()
                elif self.path == '/approve_opinions':
                    self.approve_opinions_page()
                elif self.path.startswith('/approve'):
                    self.approve()
                elif self.path == '/senate':
                    self.senate_page()
                elif self.path == '/schedule_opinions':
                    self.schedule_opinions_page()
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
                return
            else:
                raise ValueError(f'ip {self.client_address[0]} -- identify user function got no code in cookies')

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
                #set up uuids so that they are unique
                my_uuid = uuid.uuid4().hex
                while my_uuid in db.user_cookies or my_uuid in db.verification_links:
                    my_uuid = uuid.uuid4().hex
                
                link_uuid = uuid.uuid4().hex
                while link_uuid in db.user_cookies or link_uuid in db.verification_links or link_uuid == my_uuid:
                    link_uuid = uuid.uuid4().hex
                print(f'{my_uuid=} {link_uuid=}')

                # send email
                assert(link_uuid not in db.user_cookies and link_uuid not in db.verification_links)
                email_address = url_arguments['email'][0]
                gmail_user = local.EMAIL
                gmail_password = local.PASSWORD
                sent_from = gmail_user
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
                    print(f'New user with email {email_address}!')
                except:
                    raise RuntimeError(f'Something went wrong with sending an email to {email_address}.')

                # change the databases
                assert(my_uuid not in db.user_cookies and my_uuid not in db.verification_links)
                db.verification_links_lock.acquire()
                try:
                    db.verification_links[link_uuid] = my_uuid
                    db.verification_links.sync()
                finally:
                    db.verification_links_lock.release()
                db.user_cookies_lock.acquire()
                try:
                    db.user_cookies[my_uuid] = User(url_arguments['email'][0], my_uuid)
                    db.user_cookies.sync()
                finally:
                    db.user_cookies_lock.release()

                #redirect to homepage so they can vote
                self.send_response(302)
                self.send_header('Location', '/')
                self.send_header('Set-Cookie', f'code={my_uuid}; path=/')
                self.end_headers()
            else:
                raise ValueError(f"ip {self.client_address[0]} -- check email function got email {url_arguments['email'][0]}")
        else:
            raise ValueError(f'ip {self.client_address[0]} -- check email function got url arguments {url_arguments}')

    def verify_email(self):
        url_arguments = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        my_account = self.identify_user()
        if 'verification_id' in url_arguments:
            link_uuid = url_arguments['verification_id'][0]
            if db.verification_links[link_uuid] == my_account.cookie_code:
                # change the account locally
                my_account.verified_email = True

                # update the database
                db.user_cookies_lock.acquire()
                try:
                    db.user_cookies[my_account.cookie_code] = my_account
                    db.user_cookies.sync()
                except:
                    db.user_cookies_lock.release()

                # send success page
                self.send_response(200)
                self.end_headers()
                self.wfile.write('''<html>
<body>
Thank you for verifying. Your votes are now counted.<br />
<a href='/'>Return to homepage</a>
</body>
</html>'''.encode('utf8'))
                    
                print(f'{my_account.email} just verified their email!')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- insecure gmail account: {db.user_cookies[db.verification_links[link_uuid]].email}, their link ({link_uuid}) was opened by {my_account.email}')
        else:
            raise ValueError(f"ip {self.client_address[0]} -- verify email function got link_uuid {link_uuid}")
            
    def opinions_page(self):
        my_account = self.identify_user()
        self.send_response(200)
        self.end_headers()
        day_of_the_week = datetime.date.today().weekday()
        if day_of_the_week in (5, 6):
            self.wfile.write('''<html>
<body>
There is no voting on weekends.<br />
Enjoy your weekend and see you on Monday!<br />'''.encode('utf8'))
        elif str(datetime.date.today()) not in db.opinions_calendar or db.opinions_calendar[str(datetime.date.today())] == set():
            self.wfile.write('''<html>
<body>
Sorry, today's off.<br />
See you soon!<br />'''.encode('utf8'))
        else:
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
            for opinion in db.opinions_calendar[datetime.date.today()]:
                assert opinion.approved == True
                opinion_ID = opinion.ID
                if my_account.email in local.ADMINS and my_account.verified_email:
                    up_votes, down_votes = opinion.count_votes()
                    if opinion_ID in my_account.votes:
                        print(f'{opinion_ID} in my account votes')
                        my_vote = my_account.votes[opinion_ID]
                        if my_vote[-1][0] == 'up':
                            self.wfile.write(f'''<tr><td>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</td><td><div class='selected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='unselected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div></td></tr>'''.encode('utf8'))
                        elif my_vote[-1][0] == 'down':
                            self.wfile.write(f'''<tr><td>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</td><td><div class='unselected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='selected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div></td></tr>'''.encode('utf8'))
                        else:
                            self.wfile.write(f'''<tr><td>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</td><td><div class='unselected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='unselected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div></td></tr>'''.encode('utf8'))
                    else:
                        self.wfile.write(f'''<tr><td>{up_votes+down_votes}&emsp;&emsp;{opinion.text}</td><td><div class='unselected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;{up_votes}</div><div class='unselected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;{down_votes}</div></td></tr>'''.encode('utf8'))
                else:
                    if opinion_ID in my_account.votes:
                        print(f'{opinion_ID} in my account votes')
                        my_vote = my_account.votes[opinion_ID]
                        if my_vote[-1][0] == 'up':
                            self.wfile.write(f'''<tr><td>{opinion.text}</td><td><div class='selected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='unselected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div></td></tr>'''.encode('utf8'))
                        elif my_vote[-1][0] == 'down':
                            self.wfile.write(f'''<tr><td>{opinion.text}</td><td><div class='unselected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='selected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div></td></tr>'''.encode('utf8'))
                        else:
                            self.wfile.write(f'''<tr><td>{opinion.text}</td><td><div class='unselected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='unselected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div></td></tr>'''.encode('utf8'))
                    else:
                        self.wfile.write(f'''<tr><td>{opinion.text}</td><td><div class='unselected' id='{opinion_ID} up' onclick='vote(this.id)'>&#9650;</div><div class='unselected' id='{opinion_ID} down' onclick='vote(this.id)'>&#9660;</div></td></tr>'''.encode('utf8'))
            self.wfile.write('</table>'.encode('utf8'))
            self.wfile.write(str('''<script>
const page_IDs = %s;
function vote(element_ID) {
    var xhttp = new XMLHttpRequest();
    var split_ID = element_ID.split(' ');
    const opinion_ID = split_ID[0];

    let old_vote = '';
    if (document.getElementById(opinion_ID + ' up').className == 'selected') {
        old_vote = 'up';
    }
    else if (document.getElementById(opinion_ID + ' down').className == 'selected') {
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
            document.getElementById(element_ID).className = 'unselected';
        }
        else {
            if (old_vote != 'abstain') {
                let other_arrow = document.getElementById(opinion_ID + ' ' + old_vote);
                other_arrow.className = 'unselected';
            }
            if (my_vote != 'abstain') {
                document.getElementById(element_ID).className = 'selected';
            }
        }
    }
}
function checkVoteValidity(new_vote, old_vote) {
    let up_count = 0;
    let down_count = 0;
    for (let index = 0; index < page_IDs.length; index++) {
        if (document.getElementById(page_IDs[index] + ' up').className == 'selected') {
            up_count++;
        }
        else if (document.getElementById(page_IDs[index] + ' down').className == 'selected') {
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
<br />''' % (list(db.opinions_calendar[datetime.date.today()]))).encode('utf8'))
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
</script>'''.encode('utf8'))
        if my_account.email in local.MODERATORS and my_account.verified_email:
            #self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/about_the_senate'>About the Student Faculty Senate</a><br /><a href='/current_issues'>View Current Issues</a><br /><a href='/meet_the_senators'>Meet the Senators</a><br /><a href='/approve_opinions'>Approve Opinions</a>'''.encode('utf8'))
            self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/senate'>The Student Faculty Senate</a><br /><a href='/approve_opinions'>Approve Opinions</a>'''.encode('utf8'))
        else:
            self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/senate'>The Student Faculty Senate</a>'''.encode('utf8'))
        self.wfile.write('</body></html>'.encode('utf8'))

    def approve_opinions_page(self):
        my_account = self.identify_user()
        if my_account.email in local.ADMINS and my_account.verified_email:
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
                if opinion.approved == None:
                    self.wfile.write(f'''<tr id={opinion_ID}><td>{opinion.text}</td><td><div class='unselected' id='{opinion_ID} yes' onclick='vote(this.id)'>&#10003;</div><div class='unselected' id='{opinion_ID} no' onclick='vote(this.id)'>&#10005;</div></td></tr>'''.encode('utf8'))
            self.wfile.write('</table>'.encode('utf8'))
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
            self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/senate'>The Student Faculty Senate</a><br /><a href='/approve_opinions'>Approve Opinions</a>'''.encode('utf8'))
            self.wfile.write('</body></html>'.encode('utf8'))            

    def senate_page(self):
        my_account = self.identify_user()
        self.send_response(200)
        self.end_headers()
        self.wfile.write('''<html><body>'''.encode('utf8'))
        self.wfile.write('''<h2 id='about'>About the Senate</h2>
Welcome to the Lexington High School Student-Faculty Senate! The Senate convenes at 3:15pm on Wednesdays in the Library Media Center.
We implement school-wide policies on a number of issues, from things as mundane as placing extra benches around the school to changes as significant as eliminating the community service requirement for open campus, allowing students to eat in the Quad, or determining what information will be printed on transcripts.<br />
All meetings are open to the public! If you want to change something about the school, we would love to hear and discuss your ideas.'''.encode('utf8'))
        self.wfile.write(f'''<h2 id='meet'>Meet the Senators</h2>
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
        if my_account.email in local.MODERATORS and my_account.verified_email:
            #self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/about_the_senate'>About the Student Faculty Senate</a><br /><a href='/current_issues'>View Current Issues</a><br /><a href='/meet_the_senators'>Meet the Senators</a><br /><a href='/approve_opinions'>Approve Opinions</a>'''.encode('utf8'))
            self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/senate'>The Student Faculty Senate</a><br /><a href='/approve_opinions'>Approve Opinions</a>'''.encode('utf8'))
        else:
            self.wfile.write('''<br /><a href='/'>Voice Your Opinions</a><br /><a href='/senate'>The Student Faculty Senate</a>'''.encode('utf8'))
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
                db.opinions_database[str(opinion_ID)] = Opinion(opinion_ID, opinion_text, {'created' : (my_account.cookie_code, datetime.datetime.now())})
                db.opinions_database.sync()
            finally:
                db.opinions_database_lock.release()
            self.send_response(200)
            self.end_headers()
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
                db.user_cookies_lock.acquire()
                try:
                    db.user_cookies[my_account.cookie_code] = my_account
                    db.user_cookies.sync()
                finally:
                    db.user_cookies_lock.release()

                self.send_response(200)
                self.end_headers()
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
                    opinion.activity['approved'] = (my_account.email, my_vote, datetime.datetime.now())
                    if my_vote == 'yes':
                        opinion.approved = True
                    else:
                        opinion.approved = False
                    db.opinions_database_lock.acquire()
                    try:
                        db.opinions_database[opinion_ID] = opinion
                        db.opinions_database.sync()
                    finally:
                        db.opinions_database_lock.release()

                    my_account.activity.append((opinion_ID, my_vote, datetime.datetime.now()))
                    db.user_cookies_lock.acquire()
                    try:
                        db.user_cookies[my_account.cookie_code] = my_account
                        db.user_cookies.sync()
                    finally:
                        db.user_cookies_lock.release()

                    self.send_response(200)
                    self.end_headers()
                else:
                    raise ValueError(f'ip {self.client_address[0]} -- approval function got opinion ID {opinion_ID} and vote {my_vote}')
            else:
                raise ValueError(f'ip {self.client_address[0]} -- approval function got url arguments {url_arguments}')

        

        
class ReuseHTTPServer(HTTPServer):    
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
    
class User:

    def __init__(self, email, cookie_code, activity=[], votes={}, verified_email=False):

        self.email = email
        self.cookie_code = cookie_code
        self.activity = activity
        self.votes = votes
        self.verified_email = verified_email

class Opinion:

    def __init__(self, ID, text, activity, approved=None):

        self.ID = ID
        self.text = text
        self.activity = activity
        self.approved = approved

    def count_votes(self):
        up_votes = 0
        down_votes = 0
        for user in db.user_cookies.values():
            if str(self.ID) in user.votes:
                this_vote = user.votes[str(self.ID)][-1][0]
                #print(f'{this_vote=}')
                if this_vote == 'up':
                    up_votes += 1
                elif this_vote == 'down':
                    down_votes += 1
        return up_votes, down_votes

class invalidCookie(ValueError):
    def __init__(self, message):
        super().__init__(message)


def main():
    print('Student Change Web App... running...')

    print(f'\n{db.user_cookies=}')
    for cookie, user in db.user_cookies.items():
        print(f'  {cookie} : User({user.email}, {user.cookie_code}, {user.activity}, {user.votes}, {user.verified_email})')

    print(f'\n{db.opinions_database=}')
    for ID, opinion in db.opinions_database.items():
        print(f'  {ID} : Opinion({opinion.ID}, {opinion.text}, {opinion.activity}, {opinion.approved})')

    print(f'\n{db.verification_links=}')
    for link, ID in db.verification_links.items():
        print(f'  {link} : {ID}')
        
    httpd = ReuseHTTPServer(('0.0.0.0', 8888), MyHandler)
    httpd.serve_forever()
    

if __name__ == '__main__':
    main()
