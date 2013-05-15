import BaseHTTPServer
import urlparse
import threading

import config

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path=='/robots.txt' or self.path=='/favicon.ico':
      self.send_error(404)
      return
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write(
'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "http://www.w3.org/TR/html4/loose.dtd">
<html><head><title>BlinkenBlueHouse Webinterface Login</title></head>
<body><form action="" method="POST">
  <input type="password" name="p">
  <input type="submit" value="Login">
</form></body></html>
''')

  def do_POST(self):
    query_string = self.rfile.read(int(self.headers['Content-Length']))
    params = urlparse.parse_qs(query_string)
    if 'p' not in params.keys() or params['p'][0] != config.HTTP_PASSWORD:
      self.send_error(401)
      return
    if 'c' in params.keys():
      self.server.queue.put(params['c'][0])
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    output = ''
    output += \
'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
   "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head><title>BlinkenBlueHouse Webinterface</title>
<style type="text/css">body{background-color:#ccc;font-size:18pt;}a,a:hover,a:visited{color:black;text-decoration:none;}table{border-spacing:0}td{font-size:0.85em;border:1px solid black;padding:0.2em;}</style>
<script type="text/javascript">
function set_param(name, value) {
  var elem = document.createElement('input');
  elem.setAttribute('type', 'hidden');
  elem.setAttribute('name', name);
  elem.setAttribute('value', value);
  var form = document.getElementById('form1');
  form.appendChild(elem);
}
function submit() {
  document.getElementById('form1').submit();
}
</script>
</head>
<body>
'''
    if 'a' in params.keys() and 'rid' in params.keys():
      self.server.playlist.lock.acquire()
      if int(params['rid'][0])==self.server.playlist.request_id:
        if params['a'][0][0]=='D': self.server.playlist.move_down(int(params['a'][0][1:]))
        elif params['a'][0][0]=='P': self.server.playlist.inc_repeats(int(params['a'][0][1:]))
        elif params['a'][0][0]=='M': self.server.playlist.dec_repeats(int(params['a'][0][1:]))
        elif params['a'][0][0]=='X': self.server.playlist.remove(int(params['a'][0][1:]))
        elif params['a'][0][0]=='A': self.server.playlist.add(int(params['a'][0][1:]))
      else:
        output += 'Error in playlist change: playlist was changed by another client.<br>\n'
      self.server.playlist.lock.release()
    if 's' in params.keys():
      if params['s'][0]=='t':
        output += '<table>\n'
        for y in range(self.server.playlist.HEIGHT):
          output += '  <tr>\n'
          for x in range(self.server.playlist.WIDTH):
            output += '''    <td><a href="javascript:;" onclick="set_param('s','t');set_param('c','TG%02d');submit();">O</a></td>\n''' % (y*self.server.playlist.WIDTH+x, )
          output += '  </tr>\n'
        output += '</table>\n'
      elif params['s'][0]=='a':
        self.server.playlist.lock.acquire()
        self.server.playlist.updateAvailable()
        output += '<table>\n'
        rid = self.server.playlist.request_id
        for i in range(len(self.server.playlist.list)):
          anim = self.server.playlist.list[i]
          if anim[0][1] == '': comment = '&nbsp;'
          else: comment = anim[0][1]
          output += '  <tr><td>' + anim[0][0] + '</td><td>' + comment + '</td><td>' + str(anim[1]) + '</td>\n'
          for act in (('D','&darr;'),('P','+'),('M','-'),('X','X')):
            output += '''    <td><a href="javascript:;" onclick="set_param('s','a');set_param('a','%s%d');set_param('rid','%d');submit();">%s</a></td>\n''' % (act[0],i,rid,act[1])
          output += '  </tr>\n'
        output += '</table><p>Available animations:</p><table>\n'
        for i in range(len(self.server.playlist.available)):
          anim = self.server.playlist.available[i]
          if anim[1] == '': comment = '&nbsp;'
          else: comment = anim[1]
          output += '  <tr><td>' + anim[0] + '</td><td>' + comment + '''</td><td><a href="javascript:;" onclick="set_param('s','a');set_param('a','A%d');set_param('rid','%d');submit();">add</a></td></tr>\n''' % (i,rid)
        output += '</table>\n'
        self.server.playlist.lock.release()
      output += '<p><a href="javascript:;" onclick="submit();">&lt;- back</a></p>\n'
    else:
      for command in [('&Ouml;FF', 'OF'), ('&Ouml;N', 'ON'), ('Animation', 'AN'), ('VU-Meter', 'VU'), ('UV-Meter', 'UV')]:
        output += '''<a href="javascript:;" onclick="set_param('c','%s');submit();">%s</a><br>\n''' % (command[1], command[0])
      output += '''<a href="javascript:;" onclick="set_param('s','t');submit();">Toggle</a><br>\n'''
      output += '''<a href="javascript:;" onclick="set_param('s','a');submit();">Edit Playlist</a><br>\n'''
    output += \
'''<form id="form1" action="" method="POST">
<input type="hidden" name="p" value="%s">
</form>
</body></html>''' % config.HTTP_PASSWORD
    self.wfile.write(output)

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

