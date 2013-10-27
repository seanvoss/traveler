import tornado.web
import os
import time
import datetime
from math import *
from tornado import escape 
from tornado import template
from _foursquare import FoursquareMixin
import exifread
from get_lat_lon_exif_pil import *
import StringIO

class LoginHandler(tornado.web.RequestHandler):
    pass

class MainHandler(tornado.web.RequestHandler):

    def get_current_user(self):

        user = self.get_secure_cookie('user')
        print user
        user = escape.json_decode(user)
        print user
        session = self.get_secure_cookie('user_token')
        session = escape.json_decode(session)
        #user['token'] = session['access_token']
        return session['access_token']


    def get(self):
        loader = template.Loader("templates/")
        self.write(loader.load("index.html").generate(myvalue="XXX"))


class UploadHandler(MainHandler):


    def get(self):
        loader = template.Loader("templates/")
        self.write(loader.load("upload.html").generate(myvalue="XXX"))


class FileHandler(MainHandler):
    def post(self):
        # get post data
        file_body = self.request.files['file'][0]['body']
        f = open("img/%s" % self.request.files['file'][0]['filename'], 'wb')  
        f.write(file_body)
        f.close()
        #img = Image.open(StringIO.StringIO(file_body))
        #img.save("img/%s" % self.request.files['file'][0]['filename'], img.format)



class FoursquareLoginHandler(MainHandler,FoursquareMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument('code', False):
            self.get_authenticated_user(
                redirect_uri=redirect_uri,
                client_id=self.settings["foursquare_client_id"],
                client_secret=self.settings["foursquare_client_secret"],
                code=self.get_argument("code"),
                callback=self.async_callback(self._on_login)
            )
            return

        self.authorize_redirect(
            redirect_uri=redirect_uri,
            client_id=self.settings['foursquare_client_id']
        )

    def _on_login(self, user):
        # Do something interesting with user here. See: user['access_token']
        print user
        self.set_secure_cookie('user', escape.json_encode(user['response']['user']))

        self.redirect('/upload')


class ExifHandler(MainHandler, FoursquareMixin):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        access_token = self.current_user
        # Open image file for reading (binary mode)
        image = Image.open('img/%s' % self.get_argument('file'))
        # Return Exif tags
        exif = get_exif_data(image)
        geo = get_lat_lon(exif)
        d = exif['DateTime']
        timestamp = time.mktime(datetime.datetime.strptime(d, "%Y:%m:%d %H:%M:%S").timetuple())
        self.foursquare_request(
            path="/venues/search",
            callback=self.async_callback(self.tagged, timestamp, access_token),
            access_token=access_token,
            ll=",".join(geo)
        )

    def tagged(self, d, access_token, response):
        response = response['response']
        self.content_type = 'application/json'
        self.write(escape.json_encode({'date': d, 'venues':response['venues']}))
        venues = response['venues']
        print venues[0]
        self.finish()
        return
        
class CheckinHandler(MainHandler,FoursquareMixin):
    @tornado.web.asynchronous
    def get(self):
        access_token = self.current_user
        venueId = self.get_argument('venueid');
        d = self.get_argument('timestamp');
        post_args = {
            'venueId':venueId,
            'datetime':str(int(d))
            }
        self.foursquare_request(
            path="/checkins/add",
            callback=self.done,
            access_token=access_token,
            post_args=post_args
            
        )

    def done(self, response):
        print response
        self.content_type = 'application/json'
        self.write(escape.json_encode(response))
        self.finish()
       





options = {
    'foursquare_client_id': 'CKZVNZQOR35PP0RMK3THUH51HLNZNPWUVOYDZZGPKASF0RAC',
    'foursquare_client_secret': 'RGLCJH4GCXXCUN3ZVA4FKJEKLLB1FNO0UHXPOYQDSYXOP5JJ'
}
routes = [
        (r"/", MainHandler),
        (r"/image_upload", FileHandler),
        (r"/upload", UploadHandler),
        (r"/exif", ExifHandler),
        (r"/check_in", CheckinHandler),
        (r"/static/(.*)" , tornado.web.StaticFileHandler, dict(path='./static/')),
        (r"/foursquare", FoursquareLoginHandler),
    ]

redirect_uri = 'http://tc_europe.seanvoss.com/foursquare'


class Application(tornado.web.Application):
    def __init__(self):

        tornado.web.Application.__init__(self, routes, **dict(
            foursquare_client_id    = options['foursquare_client_id'],
            foursquare_client_secret= options['foursquare_client_secret'],
            cookie_secret = 'geioaeoh',
            login_url = '/foursquare',
            static_path = os.path.join(os.path.dirname(__file__), "static"),
        ))

Application().listen(9999)
tornado.ioloop.IOLoop.instance().start()
