import BaseHTTPServer
import Queue
import creds
import json
import requests
import threading


def read_zips():
    json_file = open('zip_codes_states.json')
    zips = json.load(json_file)
    return zips

ZIPCODE_DATA = read_zips()
CLIENT_ID = creds.CLIENT_ID
IG_LOCATION_SEARCH = ('https://api.instagram.com/v1/locations/search'
                      '?lat={lat}&lng={lng}&client_id=%s') % CLIENT_ID
IG_RECENT_LOCATIONS = ('https://api.instagram.com/v1/locations/{location_id}/media/'
                       'recent?client_id=%s&') % CLIENT_ID


queue = Queue.Queue()


class Thread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.results = []

    def run(self):
        while True:
            l_id = self.queue.get()
            media_url = IG_RECENT_LOCATIONS.format(location_id=l_id)
            r_media = requests.get(media_url)
            data = json.loads(r_media.content)['data']
            self.results.extend(data)
            self.queue.task_done()


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        print self.path
        print dir(self)
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(open('index.html').read())
        else:
            zip_code = self.path[1:]
            try:
                zip_data = ZIPCODE_DATA[zip_code]
            except KeyError:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                msg = '%s zip code not found.' % zip_code
                self.wfile.write(msg)
            else:

                location_url = IG_LOCATION_SEARCH.format(lat=zip_data['latitude'],
                                                         lng=zip_data['longitude'])
                r_location = requests.get(location_url)
                location_data = json.loads(r_location.content)['data']
                location_ids = [l['id'] for l in location_data]

                threads = []
                for i in range(5):
                    t = Thread(queue)
                    t.setDaemon(True)
                    threads.append(t)
                    t.start()

                for l_id in location_ids:
                    queue.put(l_id)

                queue.join()
                media_data = []
                for t in threads:
                    media_data.extend(t.results)

                image_links = [m['images']['standard_resolution']['url'] for m in media_data]
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'images': image_links,
                    'zip_data': zip_data
                }))


def main():
    try:
        httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', 8000), Handler)
        httpd.serve_forever()
    except Exception as e:
        print e

if __name__ == '__main__':
    main()
