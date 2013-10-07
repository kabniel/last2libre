#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

'''
Submit tracks to a gnu fm server.
Usage: libreimport2.py username --type=scrobbles --file=myscrobbles.txt [--server=SERVER]

'''

import json, sys, urllib, urllib2, hashlib, getpass, time
from scrobble2 import ScrobbleServer, ScrobbleTrack
import argparse

class Importer(object):

    def __init__(self):
        self.api_key = 'thisisthelibreimport2pythonthing'

    def parse_args(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(dest='username', help='User name.')
        self.parser.add_argument('-f', '--file', dest='infile', default=None, required=True,
                                 help='File with tracks to read from.')
        self.parser.add_argument('-s', '--server', dest='server', default='libre.fm',
                                 help='Server to import data into, default is libre.fm.')
        self.parser.add_argument('-t', '--type', dest='datatype', default='scrobbles',
                                 choices=['scrobbles', 'loved', 'banned', 'unloved', 'unbanned'],
                                 help='Type of data to import: scrobbles, loved or banned.')
        self.parser.add_argument('-d', '--debug', action='store_true', dest='debug',
                                 default=False, help='Debug mode.')

        self.parser.parse_args(namespace=self)

        if not 'http' in self.server:
            self.server = 'http://' + self.server


    def auth(self):
        passmd5 = hashlib.md5(self.password).hexdigest()
        token = hashlib.md5(self.username+passmd5).hexdigest()
        getdata = dict(
            method='auth.getMobileSession',
            username=self.username,
            authToken=token,
            format='json',
            api_key=self.api_key
        )
        req = self.server + '/2.0/?' + urllib.urlencode(getdata)
        response = urllib2.urlopen(req)
        try:
            jsonresponse = json.load(response)
            self.session_key = jsonresponse['session']['key']
        except:
            print(jsonresponse)
            sys.exit(1)
    
    def submit(self, trackartist, tracktitle):
    
        if self.datatype == 'loved':
            libremethod = 'track.love'
        elif self.datatype == 'unloved':
            libremethod = 'track.unlove'
        elif self.datatype == 'banned':
            libremethod = 'track.ban'
        elif self.datatype == 'unbanned':
            libremethod = 'track.unban'
        else:
            sys.exit('invalid method')

        postdata = dict(
            method=libremethod,
            artist=trackartist,
            track=tracktitle,
            sk=self.session_key,
            format='json',
            api_key=self.api_key
        )

        req = urllib2.Request(self.server + '/2.0/', urllib.urlencode(postdata))
        response = urllib2.urlopen(req)
        
        try:
            jsonresponse = json.load(response)
            status = jsonresponse['lfm']['status']
    
            if status == "ok":
                return True
        except:
            return False

    def run(self):
        self.parse_args()
        self.password = getpass.getpass()
        self.auth()
    
        if self.datatype == 'scrobbles':
            self.scrobbler = ScrobbleServer(self.server, self.session_key, api_key=self.api_key,
                                            debug=self.debug, username=self.username)
    
            n = 0
            for line in file(self.infile):
                n = n + 1
                timestamp, track, artist, album, trackmbid, artistmbid, albummbid = line.strip("\n").split("\t")
                #submission protocol doesnt specify artist/album mbid, so we dont send them
                self.scrobbler.add_track(ScrobbleTrack(timestamp, track, artist, album, trackmbid))
                print("%d: Adding to post %s playing %s" % (n, artist, track))
            self.scrobbler.submit()
    
        else:
            n = 0
            for line in file(self.infile):
                n += 1
                timestamp, track, artist, album, trackmbid, artistmbid, albummbid = line.strip("\n").split("\t")
                if self.submit(artist, track):
                    print("%d: %s %s - %s" % (n, self.datatype, artist, track))
                else:
                    print("FAILED: %s - %s" % (artist, track))
                time.sleep(1)
 
if __name__ == '__main__':
    app = Importer()
    app.run()
