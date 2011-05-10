import BaseHTTPServer
import cgi
import threading

PASSWORD = "analdenscheiss"

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path=="/robots.txt" or self.path=="/favicon.ico":
      self.send_error(404)
    else:
      params = dict()
      if self.path.find("?") != -1:
        params = cgi.parse_qs(self.path[self.path.find("?")+1:])
      if "p" in params.keys():
        if params["p"][0]==PASSWORD:
          if "c" in params.keys():
            self.server.queue.put(params["c"][0])
          self.send_response(200)
          self.send_header("Content-type", "text/html")
          self.end_headers()
          self.wfile.write("<html><head><title>BlinkenBlueHouse Webinterface</title></head>")
          self.wfile.write("<body>")
          for command in [("&Ouml;FF", "OF"), ("&Ouml;N", "ON"), ("Animation", "AN"), ("VU-Meter", "VU"), ("1", "TG%00"), ("2", "TG%01"), ("3", "TG%02")]:
            self.wfile.write("<a href=\"/?p=%s&amp;c=%s\" style=\"font-size:2.5em\">%s</a><br>" % (PASSWORD, command[1], command[0]))
          self.wfile.write("</body></html>")
        else:
          self.send_error(401)
      else:
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<html><head><title>BlinkenBlueHouse Webinterface Login</title></head>")
        self.wfile.write("<body><form method=\"GET\" action=\"/\">")
        self.wfile.write("<input type=\"text\" name=\"p\">")
        self.wfile.write("<input type=\"submit\" value=\"Login\">")
        self.wfile.write("</form></body></html>")

class MyHTTPServer(BaseHTTPServer.HTTPServer):
  def __init__(self, queue, port):
    BaseHTTPServer.HTTPServer.__init__(self, ('',port), MyHandler)
    self.queue = queue

class Server(threading.Thread):
  def __init__(self, queue, port):
    threading.Thread.__init__(self)
    self.setDaemon(True)
    self.server = MyHTTPServer(queue, port)
    self.start()

  def run(self):
    self.server.serve_forever()

