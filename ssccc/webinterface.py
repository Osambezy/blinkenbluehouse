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
          self.wfile.write("<html><head><title>BlinkenBlueHouse Webinterface</title>")
          self.wfile.write("<style type=\"text/css\">body{background-color:#ccc;}a,a:hover,a:visited{font-size:2.5em;color:black;text-decoration:none;}table{border-spacing:0}td{border:1px solid black;padding:10px;}</style></head>")
          self.wfile.write("<body>")
          if "s" in params.keys():
            if params["s"][0]=="t":
              self.wfile.write("<table>")
              for y in range(self.server.playlist.HEIGHT):
                self.wfile.write("<tr>")
                for x in range(self.server.playlist.WIDTH):
                  self.wfile.write("<td><a href=\"?p=%s&amp;s=t&amp;c=TG%02d\">O</a></td>" % (PASSWORD, y*self.server.playlist.WIDTH+x))
                self.wfile.write("</tr>")
              self.wfile.write("</table>")
            elif params["s"][0]=="a":
              self.wfile.write("<table>")
              for anim in self.server.playlist.list:
                self.wfile.write("<tr><td>" + anim[0][0] + "</td><td>" + anim[0][1] + "</td></tr>")
              self.wfile.write("</table>")
            self.wfile.write("<a href=\"?p=%s\">&lt;- back</a><br>" % (PASSWORD,))
          else:
            for command in [("&Ouml;FF", "OF"), ("&Ouml;N", "ON"), ("Animation", "AN"), ("VU-Meter", "VU")]:
              self.wfile.write("<a href=\"?p=%s&amp;c=%s\">%s</a><br>" % (PASSWORD, command[1], command[0]))
            self.wfile.write("<a href=\"?p=%s&amp;s=t\">Toggle</a><br>" % (PASSWORD,))
            self.wfile.write("<a href=\"?p=%s&amp;s=a\">Edit Playlist</a><br>" % (PASSWORD,))
          self.wfile.write("</body></html>")
        else:
          self.send_error(401)
      else:
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<html><head><title>BlinkenBlueHouse Webinterface Login</title></head>")
        self.wfile.write("<body><form method=\"GET\" action=\"\">")
        self.wfile.write("<input type=\"password\" name=\"p\">")
        self.wfile.write("<input type=\"submit\" value=\"Login\">")
        self.wfile.write("</form></body></html>")

class MyHTTPServer(BaseHTTPServer.HTTPServer):
  def __init__(self, port, queue, playlist):
    BaseHTTPServer.HTTPServer.__init__(self, ('',port), MyHandler)
    self.queue = queue
    self.playlist = playlist

class Server(threading.Thread):
  def __init__(self, port, queue, playlist):
    threading.Thread.__init__(self)
    self.setDaemon(True)
    self.server = MyHTTPServer(port, queue, playlist)
    self.start()

  def run(self):
    self.server.serve_forever()

