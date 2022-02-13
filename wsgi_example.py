#web_application.py
from wsgiref.simple_server import make_server

def application(environ, start_response):
    for key, item in environ.items():
        print(f'{key}       {item}')
    path = environ.get('PATH_INFO')
    if path == '/':
        response_body = "Index"
    else:
        response_body = "Hello"
    status = "200 OK"
    response_headers = [("Content-Length", str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body.encode('utf8')]

httpd = make_server(
    '10.17.4.17', 8051, application)

httpd.serve_forever()
