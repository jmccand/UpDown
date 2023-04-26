import wsgiref
import wsgiref.validate
import wsgiref.simple_server

app = wsgiref.simple_server.demo_app
#app = wsgiref.validate.validator(app)
#with make_server('10.17.4.226', 8888, validator_app) as httpd:
with wsgiref.simple_server.make_server('', 8888, app) as httpd:
    httpd.serve_forever()
