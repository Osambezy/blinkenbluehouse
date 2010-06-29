import time, random
import text

def main(blthread):
  blthread.controls = ["Left", "Right", "Down", "space", "Up", "Prior", "Next"]
  #blthread.blocks = (((-1,0),(0,0),(1,0),(2,0)),  ((0,-1),(0,0),(1,0),(1,1)),  ((0,-1),(0,0),(-1,0),(-1,1)),  ((0,-1),(0,0),(0,1),(1,1)),  ((0,-1),(0,0),(0,1),(-1,1)),  ((0,0),(1,0),(0,1),(1,1)),  ((-1,0),(0,0),(1,0),(0,1)))
  blthread.blocks = \
  ((((0,0),(0,1)),((0,0),(1,0))), \
  (((0,0),(0,1),(1,0)),((0,0),(1,0),(1,1)),((1,0),(1,1),(0,1)),((1,1),(0,1),(0,0))), \
  (((0,0),),), \
  (((0,0),(1,1)),((0,1),(1,0))), \
  (((-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)),), \
  (((-1,-1), (1,-1), (1,1), (-1,1), (0,0)),))
  blthread.blocksprob = (10, 10, 6, 10, 0, 0)
  newgame(blthread)
  starttime = time.time()
  while True:
    now = time.time()
    if now < starttime+blthread.falldelay: key = blthread.waitforanykey(starttime+blthread.falldelay-now)
    else: key = 0
    if key == 1:
      if test_block(blthread,blthread.blockx-1,blthread.blocky,blthread.blockframe): blthread.blockx -= 1
    elif key == 2:
      if test_block(blthread,blthread.blockx+1,blthread.blocky,blthread.blockframe): blthread.blockx += 1
    elif key == 4:
      if test_block(blthread,blthread.blockx,blthread.blocky,(blthread.blockframe + 1) % len(blthread.blocks[blthread.blocktyp])): blthread.blockframe = (blthread.blockframe + 1) % len(blthread.blocks[blthread.blocktyp])
    elif key == 3:
      if blthread.falldelay>0: blthread.falldelay = 0.05
    elif key == 5: blthread.forceblock = 2  # admin mode ;-)
    elif key == 6: blthread.forceblock = 4
    elif key == 7: blthread.forceblock = 5
    elif key == 0:
      fall(blthread)
      starttime = time.time()
    draw(blthread)

def newgame(blthread):
  blthread.delay = 0.6
  blthread.falldelay = blthread.delay
  blthread.rows = 0
  blthread.canvas = blthread.height * [blthread.width * [0]]
  blthread.forceblock = -1
  neuer_block(blthread)

def neuer_block(blthread):
  blthread.blockx = int(blthread.width / 2)
  blthread.blocky = -1
  if blthread.forceblock==-1:
    totalprob = 0
    for prob in blthread.blocksprob: totalprob += prob
    x = random.randrange(totalprob)
    for i in range(len(blthread.blocks)):
      if x<blthread.blocksprob[i]:
        blthread.blocktyp = i
        break
      else:
        x -= blthread.blocksprob[i]
  else:
    blthread.blocktyp = blthread.forceblock
    blthread.forceblock = -1
  blthread.blockframe = random.randrange(len(blthread.blocks[blthread.blocktyp]))

def fall(blthread):
  if test_block(blthread,blthread.blockx,blthread.blocky+1,blthread.blockframe):
    blthread.blocky += 1
  else:  # festsetzen
    for pixel in blthread.blocks[blthread.blocktyp][blthread.blockframe]:
      #pixel = rotate(pixel, blthread.blockframe)
      blthread.canvas[blthread.blocky + pixel[1]] = blthread.canvas[blthread.blocky + pixel[1]][0:blthread.blockx + pixel[0]] + [1] + blthread.canvas[blthread.blocky + pixel[1]][blthread.blockx + pixel[0] + 1:]
    blthread.blocky = -20
    for i in range(0, len(blthread.canvas)):
      if blthread.canvas[i] == blthread.width * [1]:
        blink(blthread, i)
        blthread.canvas = [blthread.width * [0]] + blthread.canvas[0:i] + blthread.canvas[i+1:]
        blthread.rows += 1
        blthread.delay -= 0.02
    neuer_block(blthread)
    blthread.falldelay = blthread.delay
    if not test_block(blthread,blthread.blockx,blthread.blocky,blthread.blockframe):
      blink(blthread,-1,0.2)
      text.showtext(blthread, str(blthread.rows), spacing=0)
      blthread.wait(3)
      newgame(blthread)

'''def rotate(point, rotation):
  rotation_matrix = ((1,0,0,1),(0,-1,1,0),(-1,0,0,-1),(0,1,-1,0))
  return (point[0] * rotation_matrix[rotation][0] + point[1] * rotation_matrix[rotation][1], point[0] * rotation_matrix[rotation][2] + point[1] * rotation_matrix[rotation][3])'''

def test_block(blthread, newx,newy,newframe):
  test = True
  for pixel in blthread.blocks[blthread.blocktyp][newframe]:
    #pixel = rotate(pixel, newrotation)
    nx = pixel[0] + newx
    ny = pixel[1] + newy
    if ny < 0: ny = 0
    if nx<0 or nx>=blthread.width or ny>=blthread.height: test = False  # Block im Aus
    elif blthread.canvas[ny][nx] != 0: test = False  # Zeug im Weg, Block liegt irgendwo auf
  return test

def draw(blthread):
  data = ""
  # canvas zeichnen
  for i in range(0,blthread.height):
    for j in range(0,blthread.width): data += chr(blthread.canvas[i][j])
  # Block reinsetzen
  for pixel in blthread.blocks[blthread.blocktyp][blthread.blockframe]:
    #pixel = rotate(pixel, blthread.blockframe)
    if blthread.blocky + pixel[1] >= 0:
      pos = (blthread.blocky + pixel[1]) * blthread.width + blthread.blockx + pixel[0]
      data = data[0:pos] + "\x01" + data[pos+1:]
  blthread.send(data)

def blink(blthread, row, delay = 0.1):
  if row == -1: # alles blinken
    for i in range(0,6):
      blthread.clear()
      blthread.wait(delay)
      draw(blthread)
      blthread.wait(delay)
  elif row>=0 and row<blthread.height:
    for i in range(0,3):
      blthread.canvas[row] = blthread.width * [0]
      draw(blthread)
      blthread.wait(delay)
      blthread.canvas[row] = blthread.width * [1]
      draw(blthread)
      blthread.wait(delay)

