import random, time
import text

def main(blthread):
  MAZE_WIDTH = 8 # maze units, not pixels!
  MAZE_HEIGHT = 8
  BLINK_DELAY = 0.3
  blthread.controls = ["Up", "Down", "Left", "Right"]
  
  global position, goal
  
  while True:
    new_maze(MAZE_WIDTH, MAZE_HEIGHT)
    starttime = time.time()
    blinktime = starttime
    posblink = False
    goalblink = False
    while True:
      now = time.time()
      if now < blinktime+BLINK_DELAY/2: key = blthread.waitforanykey(blinktime+BLINK_DELAY/2-now)
      else: key = 0
      if key == 1: newposition = (position[0], position[1]-1)
      elif key == 2: newposition = (position[0], position[1]+1)
      elif key == 3: newposition = (position[0]-1, position[1])
      elif key == 4: newposition = (position[0]+1, position[1])
      elif key == 0:
        newposition = position
        goalblink = not goalblink
        if goalblink: posblink = not posblink
        blinktime = time.time()
      if checkpos(newposition): position = newposition
      if position==goal: break
      draw(blthread, posblink, goalblink)
    seconds = int(time.time() - starttime)
    blthread.clear()
    blthread.wait(1)
    text.showtext(blthread, str(seconds), spacing=0)
    blthread.wait(5)
    blthread.clear()
    blthread.wait(1)

def checkpos(pos):
  global walls
  x = pos[0]
  y = pos[1]
  xeven = x%2 == 0
  yeven = y%2 == 0
  if x<0 or y<0 or x>len(walls[0])*2 or y>len(walls)*2: return True
  if xeven and yeven: return False
  if (not xeven) and (not yeven): return True
  if x==0 or y==0: return False
  if xeven and (not yeven): return not walls[(y-1)/2][(x-2)/2][0]
  if (not xeven) and yeven: return not walls[(y-2)/2][(x-1)/2][1]

def draw(blthread, pos_on, goal_on):
  global walls, position, goal
  center = ((blthread.width-1)//2, (blthread.height-1)//2)
  data = ""
  for y in range(blthread.height):
    for x in range(blthread.width):
      if checkpos((position[0]+x-center[0],position[1]+y-center[1])): data += "\x00"
      else: data += "\x01"
  if pos_on:
    pos = center[1]*blthread.width+center[0]
    data = data[0:pos] + "\x01" + data[pos+1:]
  if goal_on:
    x = goal[0]-position[0]+center[0]
    y = goal[1]-position[1]+center[1]
    if x>=0 and x<blthread.width and y>=0 and y<blthread.height:
      pos = y*blthread.width+x
      data = data[0:pos] + "\x01" + data[pos+1:]
  blthread.send(data)

def new_maze(width, height):
  global status, walls, position, goal
  status = [[False for i in range(width)] for j in range(height)]
  walls = [[[True, True] for i in range(width)] for j in range(height)]
  start = (random.randrange(width), random.randrange(height))
  end = fill(start)[1]
  #end = (random.randrange(width), random.randrange(height))
  del status
  position = (start[0]*2+1, start[1]*2+1)
  goal = (end[0]*2+1, end[1]*2+1)

def fill(point):
  global status, walls
  if status[point[1]][point[0]]: raise Exception, "Point already filled"
  status[point[1]][point[0]] = True
  farest_point = (1, point)
  while True:
    directions = ((0,-1), (1,0), (0,1), (-1,0))
    walldirections = ((0,-1,1), (0,0,0), (0,0,1), (-1,0,0))
    possible_neighbors = []
    corresponding_walls = []
    for dir in range(4):
      x = point[0]+directions[dir][0]
      y = point[1]+directions[dir][1]
      if x>=0 and x<len(status[0]) and y>=0 and y<len(status) and not status[y][x]:
        possible_neighbors += [(x, y)]
        corresponding_walls += [(point[0]+walldirections[dir][0], point[1]+walldirections[dir][1], walldirections[dir][2])]
    if len(possible_neighbors)==0: return farest_point
    next = random.randrange(len(possible_neighbors))
    walls[corresponding_walls[next][1]][corresponding_walls[next][0]][corresponding_walls[next][2]] = False
    newpoint = fill(possible_neighbors[next])
    if newpoint[0] >= farest_point[0]: farest_point = (newpoint[0]+1, newpoint[1])

"""def print_maze():
  global walls
  width = len(walls[0])
  height = len(walls)
  print (2*width+1)*"##"
  for row in range(height):
    output = "##"
    for col in range(width):
      if walls[row][col][0]: output += "  ##"
      else: output += "    "
    print output
    output = "##"
    for col in range(width):
      if walls[row][col][1]: output += "####"
      else: output += "  ##"
    print output"""
