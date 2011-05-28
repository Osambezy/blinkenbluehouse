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
          self.wfile.write("<style type=\"text/css\">body{background-color:#ccc;font-size:2.5em;}a,a:hover,a:visited{color:black;text-decoration:none;}table{border-spacing:0}td{border:1px solid black;padding:10px;}</style></head>")
          self.wfile.write("<body>")
          if "a" in params.keys() and "rid" in params.keys():
            self.server.playlist.lock.acquire()
            if int(params["rid"][0])==self.server.playlist.request_id:
              if params["a"][0][0]=="D": self.server.playlist.move_down(int(params["a"][0][1:]))
              elif params["a"][0][0]=="P": self.server.playlist.inc_repeats(int(params["a"][0][1:]))
              elif params["a"][0][0]=="M": self.server.playlist.dec_repeats(int(params["a"][0][1:]))
              elif params["a"][0][0]=="X": self.server.playlist.remove(int(params["a"][0][1:]))
              elif params["a"][0][0]=="A": self.server.playlist.add(int(params["a"][0][1:]))
            else:
              self.wfile.write("Error in playlist change: playlist was changed by another client.<br>")
            self.server.playlist.lock.release()
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
              self.server.playlist.lock.acquire()
              self.server.playlist.updateAvailable()
              self.wfile.write("<table>")
              rid = self.server.playlist.request_id
              for i in range(len(self.server.playlist.list)):
                anim = self.server.playlist.list[i]
                if anim[0][1] == "": comment = "&nbsp;"
                else: comment = anim[0][1]
                self.wfile.write("<tr><td>" + anim[0][0] + "</td><td>" + comment + "</td><td>" + str(anim[1]) + "</td>")
                for act in (("D","&darr;"),("P","+"),("M","-"),("X","X")):
                  self.wfile.write("<td><a href=\"?p=%s&amp;s=a&amp;a=%s%d&amp;rid=%d\">%s</a></td>" % (PASSWORD,act[0],i,rid,act[1]))
                self.wfile.write("</tr>")
              self.wfile.write("</table><p>Available animations:</p><table>")
              for i in range(len(self.server.playlist.available)):
                anim = self.server.playlist.available[i]
                if anim[1] == "": comment = "&nbsp;"
                else: comment = anim[1]
                self.wfile.write("<tr><td>" + anim[0] + "</td><td>" + comment + "</td><td><a href=\"?p=%s&amp;s=a&amp;a=A%d&amp;rid=%d\">add</a></td></tr>" % (PASSWORD,i,rid))
              self.wfile.write("</table>")
              self.server.playlist.lock.release()
            self.wfile.write("<p><a href=\"?p=%s\">&lt;- back</a></p>" % (PASSWORD,))
          else:
            for command in [("&Ouml;FF", "OF"), ("&Ouml;N", "ON"), ("Animation", "AN"), ("VU-Meter", "VU"), ("UV-Meter", "UV")]:
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

