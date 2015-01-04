# -*- coding: utf-8 -*-
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
import random
import urllib
import logging
from google.appengine.ext import db
from datetime import datetime
from threading import Thread
from google.appengine.api import urlfetch
from google.appengine.ext import deferred


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

request_types = [
    {}, #placeholder
    {'ram': 50, 'cpu':1000, 'storage':0.005},
    {'ram': 20, 'cpu':3000, 'storage':4},
    {'ram': 10, 'cpu':500, 'storage':10},
    {'ram': 30, 'cpu':100, 'storage':0.5},
    {'ram': 5,  'cpu':300, 'storage':0.1},
]

requests_per_second = [
    0,      # placeholder
    3,      # low
    100,    # medium
    1000,   # high
]

clouds = [
    {},
    {'url':'http://cmpe281­-cloud1.appspot.com'},
    {'url':'http://cmpe281­-cloud2.appspot.com'},
    {'url':'http://cmpe281­-cloud3.appspot.com'},
    {'url':'http://cmpe281­-cloud4.appspot.com'},
    {'url':'http://cmpe281­-cloud5.appspot.com'},
]

capacities = [
    {},
    {'ram':1500, 'cpu':0.5,  'storage':5},
    {'ram':1000, 'cpu':1.5,  'storage':2},
    {'ram':500,  'cpu':0.25, 'storage':10},
    {'ram':750,  'cpu':1,    'storage':20},
    {'ram':500,  'cpu':0.6,  'storage':5},
]


# Data model of Currently used Resources. These will be updated as
# we process requests.
class Resource(db.Model):
    cloud = db.IntegerProperty(required=True)
    ram = db.FloatProperty(required=True) # MB of RAM left
    cpu = db.FloatProperty(required=True) # GHz of CPU 
    storage = db.FloatProperty(required=True) # GB of Storage left


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

def now():
    return time.time() * 1000


class MainHandler(BaseHandler):
    def get(self):
        params = {}
        params['algorithm'] = self.request.get("algorithm")       # anthill or hollybee
        params['request_type'] = int(self.request.get("request_type")) # types 1-5, 0 for random
        if params['request_type'] == 0: # random request
            params['request_type'] = random.randint(1, len(request_types)-1)

        if not params['algorithm'] or not params['request_type']:
            self.write("All 2 params are required: <br>")
            self.write("algorithm ('anthill' or 'hollybee')<br>")
            self.write("request_type (types 1-5, 0 for random)<br>")

        # Function to get resources
        resources = [
            {}, # placeholder for 0
        ]
        resourceQuery = db.GqlQuery("Select * from Resource")
        for resource in resourceQuery.fetch(20):
            resources.append({'ram':resource.ram, 'cpu':resource.cpu, 'storage':resource.storage})

        # Now to access resource for any cloud, run resources[1]['ram'], where 1 is the cloud number
        # Cloud number should be between 1 and 5

        # Rodd: Function to calculate which cloud to select based on algorithm selection
        selected_cloud = 1
        if params['algorithm'] == 'anthill':
            # update selected_cloud here
            pass
        elif params['algorithm'] == 'honeybee':
            # update selected_cloud here
            pass
        else:
            return

        # start deferred task to send request and wait for the response, then return resource
        deferred.defer(sendRequest, selected_cloud, params['request_type'])

def sendRequest(cloud_number, request_type):
    takeResource(cloud_number, request_type)

    params = {}
    params['request_type'] = request_type

    url = clouds[cloud_number]['url']
    url = url + "?" + urllib.urlencode(params)
    #result = urlfetch.fetch(url=url, method=urlfetch.GET)
    time.sleep(0.1) # temporary fake send request to cloud

    returnResource(cloud_number, request_type)

def returnResource(cloud_number, request_type):
    resourceQuery = db.GqlQuery("Select * from Resource WHERE cloud = :cloud", cloud=cloud_number)
    resource = resourceQuery.get()
    resource.ram += request_types[request_type]['ram']
    resource.cpu += (request_types[request_type]['cpu'])/1000000
    resource.storage += request_types[request_type]['storage']
    resource.put()

def takeResource(cloud_number, request_type):
    resourceQuery = db.GqlQuery("Select * from Resource WHERE cloud = :cloud", cloud=cloud_number)
    resource = resourceQuery.get()
    resource.ram -= request_types[request_type]['ram']
    resource.cpu -= (request_types[request_type]['cpu'])//1000000
    resource.storage -= request_types[request_type]['storage']
    resource.ram = max(0.0, resource.ram)
    resource.cpu = max(0.0, resource.cpu)
    resource.storage = max(0.0, resource.storage)
    resource.put()


class InitHandler(BaseHandler):
    def get(self):
        resourceQuery = db.GqlQuery("Select * from Resource")
        for resource in resourceQuery.fetch(20):
            resource.delete()

        for i in range(1,len(capacities)):
            capacity = capacities[i]
            newResource = Resource(cloud=i, ram=float(capacity['ram']), cpu=float(capacity['cpu']), storage=float(capacity['storage']))
            newResource.put()

app = webapp2.WSGIApplication([
    ('/', MainHandler), # Serves Requests and delegates to respective cloud to process
    ('/init', InitHandler), # Initializes the initial tables, called before starting to serve requests
], debug=True)
