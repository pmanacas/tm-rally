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

def IsNotNull(value):
    return value is not None and len(value) > 0    
    
class LandingPage(webapp2.RequestHandler):

    def get(self):
     
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())
    
    
    def post(self):
        url = self.request.get('query')
        url = urlparse.urlsplit(url).query
        url = '/rally/?' + url
        self.redirect(url)

        
        
class RallyPage(webapp2.RequestHandler):

    def get(self):

        qs = self.request.query_string
        track_name = self.request.get('trackname')
        track_author = self.request.get('author')
        
        # title = self.request.get('trackname') or self.request.get('author')+'\'s Rally' or 'Rally Incognito'
        
        if IsNotNull(track_name) and IsNotNull(track_author):
            title = track_name + ' by ' + track_author
        elif IsNotNull(track_author):
             title = track_author + '\'s Rally'
        elif IsNotNull(track_name):
             title = track_name     
        else:
            title = 'ERROR: Please include Track Name AND / OR Author in your search'
            
        
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
                        time = time.encode('UTF-8')[2:-3]
                        replays[idex][u'Record'] = time
                        
                        usr = replay['Username']
                        rec = replay['ReplayTime']

                        records[usr].append(rec)
                        
                    tracks[idx][u'Replays'] = replays
            totals = []
            for usr, recs in records.iteritems():
                
                # if len(tracks)==len(recs):
                if len(recs)> 0:
                    
                    total_ms = sum(recs)
                    total_hr = str(datetime.timedelta(milliseconds = total_ms)).encode('UTF-8')[2:-3]
                    totals.append([usr, total_ms, total_hr])
                    
            totals.sort(key=lambda i: i[1])
            for i, tot in enumerate(totals):
                if i == 0:
                    tot.append('+00')
                    tot.append('+00')
                else:
                    diff_prev = '+' + str(datetime.timedelta(milliseconds = tot[1] - totals[i-1][1])).encode('UTF-8')[2:-3]
                    tot.append(diff_prev)
                    diff_first = '+' + str(datetime.timedelta(milliseconds = tot[1] - totals[0][1])).encode('UTF-8')[2:-3]
                    tot.append(diff_first)
                    
            
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
