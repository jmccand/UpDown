import smtplib
import local

gmail_user = local.EMAIL
gmail_password = local.PASSWORD

sent_from = gmail_user
to = gmail_user
subject = 'Do you get this?'
body = 'Testing 1 2 3 testing...'

email_text = f'From: {sent_from}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}'

try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_password)
    server.sendmail(sent_from, to, email_text)
    server.close()

    print('Email sent!')
except:
    print('Something went wrong...')
