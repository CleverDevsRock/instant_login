#Clever Instant Login Demo

#---------------Python Modules-----------------------------
import urllib
import urllib2
import json
import base64
import webapp2

#-----------------Environemnt Variables--------------------
client_secret = '' #Your app's client_secret here.  This can be found in your Clever Developer account under Settings > Application > View/Edit your application
client_id = '' #Your app's client_id here.  You can find it in the same place as your client_secret
district_id = '' #district id for the your sandbox district.  Instructions on sandbox district setup at https://dev.clever.com/guides/creating-district-sandboxes
redirect_uri = 'http://localhost:8080/oauth' #Where should Clever redirect users who click on Instant Login for your app?  Instructions on setting up redirect_uris at https://dev.clever.com/instant-login/implementation#configuring-redirect-urls
                                             #Default value of 'http://localhost:8080/oauth' used for Google App Engine Python dev server.
#--------------CSS and HTML Layouts for the web app--------

#define CSS styling for web app
CSS = '<html><head><link rel="stylesheet" href="//d2uaiq63sgqwfs.cloudfront.net/8.0.0/oui.css"><link rel="stylesheet" href="//d2uaiq63sgqwfs.cloudfront.net/8.0.0/oui-extras.css"></head><body style="padding-left:50px;padding-top:30px">'

#define HTML templates for pages in the web app
MAIN_PAGE_TEMPLATE = CSS + """\
    <div><h1>Welcome to the Clever Instant Login Demo!</h1></div>
    <div>
    %s
    </div>
  </body>
</html>
"""

OAUTH_PAGE_TEMPLATE = CSS + """\
<html>
    <body>
    %s
    <a href='/'>Go back and try it again!</a>
    </body>
</html>
"""

#-------------------API Methods-----------------------------

#This method POSTs the access code received from instant login. Clever will respond with a bearer token.
#Note the use of the Basic Authorization header as described in https://dev.clever.com/instant-login/bearer-tokens#2-your-application-requests-an-access-token-from-clever-by-exchanging-the-code-
def post(url, code):
    api_request = urllib2.Request(url)
    api_request.add_header("Authorization", "Basic " + base64.b64encode(client_id+":"+client_secret))
    api_request.add_header("Content-type", "application/json")
    data = {"code":code,"grant_type":"authorization_code","redirect_uri":redirect_uri}
    api_response = urllib2.urlopen(api_request, json.dumps(data))
    response_data = json.loads(api_response.read())
    return response_data

#This method GETs data from Clever endpoints.  An authorized Bearer token is required.
#Note the use of the Bearer Authoriztion header as described in https://dev.clever.com/instant-login/bearer-tokens#2-your-application-requests-an-access-token-from-clever-by-exchanging-the-code-
def get(url, token):
    api_request = urllib2.Request(url)
    api_request.add_header("Authorization", "Bearer "+token)
    api_response = urllib2.urlopen(api_request)
    response_data = json.loads(api_response.read())
    return response_data

#-----------------Web App Page Request Handlers--------------

class MainPage(webapp2.RequestHandler):
    def get(self):
        #Instant Login URI syntax is described in https://dev.clever.com/instant-login/log-in-with-clever#log-in-with-clever-buttons-are-just-links
        oauth_url = "https://clever.com/oauth/authorize?response_type=code&redirect_uri=%s&client_id=%s&district_id=%s" % (urllib.quote(redirect_uri), client_id, district_id)
        self.response.write(MAIN_PAGE_TEMPLATE % ("<a href="+ oauth_url +"><img src='https://s3.amazonaws.com/assets.clever.com/sign-in-with-clever/sign-in-with-clever-full.png'></img></a>"))

class OAuthPage(webapp2.RequestHandler):
    def get(self):
        if "code" in self.request.query_string:
            code = self.request.query_string.split("code=")[1].split("&")[0]
            #POST the code returned from instant login to the Clever oauth/tokens endpoint
            response = post("https://clever.com/oauth/tokens", code)
            #retrieve the Bearer token from the response received from the Clever ouath/tokens endpoint
            bearer_token = response['access_token']
            #GET data from the Clever /me endpoint, which contains information about the authenticated user.  Requires an authenticated Bearer token
            response = get("https://api.clever.com/me", bearer_token)
            self.response.write(OAUTH_PAGE_TEMPLATE % ("<h1>Hooray, you're authenticated!</h1><h2>Here is the response from the /me endpoint:</h2><div>%s</div>") % (json.dumps(response)))
        else:
            self.response.write(OAUTH_PAGE_TEMPLATE % ("Uh oh, you aren't authenticated!"))
#-------------------------------------------------------------

#Instantiate the app and define our path mappings
app = webapp2.WSGIApplication([('/', MainPage),('/oauth', OAuthPage)], debug=True)