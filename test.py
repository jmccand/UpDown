from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import local

msg = MIMEMultipart('alternative')
msg['Subject'] = "Add your votes to the count?"
msg['From'] = local.FROM_EMAIL
msg['To'] = local.EMAIL
text = f'Welcome to the Student Representation App for LHS! Your votes will NOT count until you click on the link below:\n{local.DOMAIN_NAME}/verify_email?verification_id=12345'
html = f'''<html>
<body>
<p>
Welcome to the Student Representation App for LHS!
<br />
<br />
Your votes will NOT count until you click on <a href='{local.DOMAIN_PROTOCAL}{local.DOMAIN_NAME}/verify_email?verification_id=12345'>this link</a>.
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
    server.sendmail(local.FROM_EMAIL, local.EMAIL, msg.as_string())
    server.close()

    print(f'Email sent! {msg.as_string()=}')
except:
    print('Something went wrong...')
