import time
import json
from urllib import urlencode
from urllib2 import Request, urlopen, URLError, HTTPError


class ScrobbleException(Exception):

    pass


class ScrobbleServer(object):

    def __init__(self, server_name, sk, api_key, debug=False, username=False):
        if server_name[:7] != "http://":
            server_name = "http://%s" % (server_name,)
        self.api_key = api_key
        self.name = server_name
        self.post_data = []
        self.sk = sk
        self.submit_url = server_name + '/2.0/'
        self.debug = debug
        self.log = None
        if debug:
            self.log = open(username + '.response.log', 'w+');

    def submit(self, sleep_func=time.sleep):
        if len(self.post_data) == 0:
            return
        i = 0
        data = []
        for track in self.post_data:
            data += track.get_tuples(i)
            i += 1
        data += [('method', 'track.scrobble'),('sk', self.sk),('api_key', self.api_key),('format', 'json')]
        last_error = None
        for timeout in (1, 2, 4, 8, 16, 32):
            try:
                req = Request(self.submit_url, urlencode(data))
                response = urlopen(req)
            except (URLError, HTTPError), e:
                last_error = str(e)
                print('Scrobbling error: %s, will retry in %ss' % (last_error, timeout))
            else:
                jsonresponse = json.load(response)

                if jsonresponse.has_key('scrobbles'): # we're just checking if key exists
                    if self.debug:
                        for v in jsonresponse['scrobbles']['scrobble']:
                            self.log.write(str(v)+"\n")
                    break
                elif jsonresponse.has_key('error'):
                    last_error = 'Bad server response: %s' % jsonresponse['error']
                    print('%s, will retry in %ss' % (last_error, timeout))
                else:
                    last_error = 'Bad server response: %s' % response.read()
                    print('%s, will retry in %ss' % (last_error, timeout))
            time.sleep(timeout)
        else:
            raise ScrobbleException('Cannot scrobble after multiple retries. Last error: %s' % last_error)

        self.post_data = []
        sleep_func(1)

    def add_track(self, scrobble_track, sleep_func=time.sleep):
        i = len(self.post_data)
        if i > 49:
            self.submit(sleep_func)
            i = 0
        self.post_data.append(scrobble_track)


class ScrobbleTrack(object):

    def __init__(self, timestamp, trackname, artistname, albumname=None,
                 trackmbid=None, tracklength=None, tracknumber=None):
        self.timestamp = timestamp
        self.trackname = trackname
        self.artistname = artistname
        self.albumname = albumname
        self.trackmbid = trackmbid
        self.tracklength = tracklength
        self.tracknumber = tracknumber

    def get_tuples(self, i):
        data = []
        data += [('timestamp[%d]' % i, self.timestamp), ('track[%d]' % i, self.trackname),
                 ('artist[%d]' % i, self.artistname)]
        if self.albumname is not None:
            data.append(('album[%d]' % i, self.albumname))
        if self.trackmbid is not None:
            data.append(('mbid[%d]' % i, self.trackmbid))
        if self.tracklength is not None:
            data.append(('duration[%d]' % i, self.tracklength))
        if self.tracknumber is not None:
            data.append(('tracknumber[%d]' % i, self.tracknumber))
        return data
