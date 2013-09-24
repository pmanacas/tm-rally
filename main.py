#!/usr/bin/env python
import os
import webapp2
import jinja2
from google.appengine.api import urlfetch
import json
import datetime
from collections import defaultdict
import logging
import urlparse

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class LandingPage(webapp2.RequestHandler):

    def get(self):
     
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())
    
    
    def post(self):
        url = self.request.get('query')
        logging.info(url)
        url = urlparse.urlsplit(url).query
        logging.info(url)
        url = '/rally/?' + url
        self.redirect(url)
        pass
        
        
class RallyPage(webapp2.RequestHandler):

    def get(self):

        qs = self.request.query_string
        title = self.request.get('trackname') or self.request.get('author')+'\'s Rally' or 'Rally Incognito'
        
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
                
                if len(tracks)==len(recs):
                # if len(recs)> 2:
                    
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

        template = JINJA_ENVIRONMENT.get_template('rally.html')
        self.response.write(template.render(template_values))
    
    

app = webapp2.WSGIApplication(
    [
        ('/', LandingPage),
        ('/rally/', RallyPage),
    ],
    debug = os.environ['SERVER_SOFTWARE'].startswith('Dev')
 )
