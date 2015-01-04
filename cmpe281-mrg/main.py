#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import re
import cgi
import os
import string
import jinja2
import time
import urllib
from google.appengine.ext import db
from google.appengine.api import urlfetch
from datetime import datetime
from threading import Thread

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

requests_per_second = [
    0,      # placeholder
    3,      # low
    100,    # medium
    1000,   # high
]

MASTER_URL = "http://localhost:13080/"
#MASTER_URL = "http://cmpe281-master.appspot.com"

MASTER_INIT_PATH = "init"

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    
def escape(text):
    return cgi.escape(text, quote=True)

def now():
    return time.time() * 1000

MAX_REQUESTS_PER_THREAD = 15

class MainHandler(BaseHandler):
    def get(self):
        params = {}
        params['time'] = self.request.get("time")                 # seconds
        params['algorithm'] = self.request.get("algorithm")       # anthill or honeybee
        params['request_type'] = self.request.get("request_type") # types 1-5, 0 for random
        params['request_rate'] = self.request.get("request_rate") # 1-low, 2-medium, 3-high

        if not params['time'] or not params['algorithm'] or not params['request_type'] or not params['request_rate']:
            self.write("All 4 params are required: <br>")
            self.write("time (time in seconds) <br>")
            self.write("algorithm ('anthill' or 'hollybee')<br>")
            self.write("request_type (types 1-5, 0 for random)<br>")
            self.write("request_rate (1-low, 2-medium(default), 3-high)<br>")

        self.initMaster()

        request_type = int(params['request_type'])
        rps = requests_per_second[int(params['request_rate'])]

        self.write(str(request_type) + "<br>")
        self.write(str(rps) + "<br>")

        for _ in range(int(params['time'])):
            threads = []
            remaining = rps
            while remaining > 0:
                requests_this_thread = min(remaining, MAX_REQUESTS_PER_THREAD)
                t = Thread(target=self.generateRequestsOverOneSecond, args=[request_type, requests_this_thread, params['algorithm']])
                t.start()
                threads.append(t)
                remaining -= requests_this_thread

            for thread in threads:
                thread.join()
        
    def generateRequestsOverOneSecond(self, request_type, num, algorithm):
        start = now()
        totalRequestTime = 0
        numRequests = 0
        while(numRequests < num):
            if (now() - start) > 1000:
                break
            startRequest = now()
            self.sendRequest(algorithm, request_type)
            numRequests += 1
            requestTime = now() - startRequest
            totalRequestTime += requestTime
            averageRequestTime = totalRequestTime/numRequests
            timeTakenDuringRequests = 1000 - (num*averageRequestTime)
            timeForWaiting = timeTakenDuringRequests/num 
            time.sleep(max(0,timeForWaiting/1000))

        return numRequests

    def initMaster(self):
        url = MASTER_URL + MASTER_INIT_PATH
        result = urlfetch.fetch(url=url, method=urlfetch.GET)

    def sendRequest(self, algorithm, request_type):
        params = {}
        params['request_type'] = request_type
        params['algorithm'] = algorithm

        self.write("Sending Request to Master: "+MASTER_URL)

        url = MASTER_URL
        url = url + "?" + urllib.urlencode(params)
        result = urlfetch.fetch(url=url, method=urlfetch.GET)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
], debug=True)
