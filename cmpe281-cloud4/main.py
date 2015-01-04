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
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

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

class MainHandler(BaseHandler):
    def get(self):
        params = {}
        params['time'] = self.request.get("time")                 # seconds
        params['algorithm'] = self.request.get("algorithm")       # anthill or hollybee
        params['request_type'] = self.request.get("request_type") # types 1-5, 0 for random
        params['request_rate'] = self.request.get("request_rate") # 1-low, 2-medium, 3-high

        #if not params['time'] or not params['algorithm'] or not params['request_type'] or not params['request_rate']:
        #    self.write("All 4 params are required: <br>")
        #    self.write("time (time in seconds) <br>")
        #    self.write("algorithm ('anthill' or 'hollybee')<br>")
        #    self.write("request_type (types 1-5, 0 for random)<br>")
        #    self.write("request_rate (1-low, 2-medium(default), 3-high)<br>")

        self.write("Request run for 5 seconds.")

app = webapp2.WSGIApplication([
    ('/', MainHandler),
], debug=True)
