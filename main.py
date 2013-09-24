#!/usr/bin/env python
import os
import webapp2
import jinja2
from google.appengine.api import urlfetch
import json
import logging
import pprint
import datetime
from collections import defaultdict

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])
    
def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input
    
    
class MainPage(webapp2.RequestHandler):

    def get(self):
        logging.info(self.request.query_string)
        qs = self.request.query_string
        title = self.request.get('trackname') or 'Rally Incognito'
        
        tracks_url = "http://tm.mania-exchange.com/tracksearch?api=on&" + qs
        response = urlfetch.fetch(tracks_url)
        if response.status_code == 200:
            data = json.loads(response.content)
            tracks = data
            records = defaultdict(list)
            for idx, track in enumerate(tracks):
                replays_url = "http://api.mania-exchange.com/tm/replays/" + str(track['TrackID'])
                response = urlfetch.fetch(replays_url)
                if response.status_code == 200:
                    replays = json.loads(response.content)
                    for idex, replay in enumerate(replays):
                        time = str(datetime.timedelta(milliseconds = replay['ReplayTime']))
                        time = time.encode('UTF-8')[:-3]
                        replays[idex][u'Record'] = time
                        
                        usr = replay['Username']
                        rec = replay['ReplayTime']

                        records[usr].append(rec)
                        
                    tracks[idx][u'Replays'] = replays
            totals = []
            for usr, recs in records.iteritems():
                
                # if len(tracks)==len(recs):
                if len(recs)> 2:
                    
                    total_ms = sum(recs)
                    total_hr = str(datetime.timedelta(milliseconds = total_ms)).encode('UTF-8')[:-3]
                    totals.append((usr, total_ms, total_hr))
                    
            totals.sort(key=lambda tup: tup[1])
            
        template_values = {
            'title': title,
            'tracks': tracks,
            'records': records,
            'totals': totals,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
    
    

app = webapp2.WSGIApplication(
    [('/', MainPage)],
    debug = os.environ['SERVER_SOFTWARE'].startswith('Dev')
 )
