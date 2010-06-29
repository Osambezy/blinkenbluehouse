import time, random
import text

def main(blthread):
  blthread.controls = ["Up", "Down", "Left", "Right"]
  delay = 0.5
  while True:
    blthread.snake = [(0,0),(0,0)]
    blthread.direction = (1,0)
    blthread.zuckerl = (random.randrange(blthread.width), random.randrange(blthread.height))
    starttime = time.time()
    while True:
      now = time.time()
      if now < starttime+delay: key = blthread.waitforanykey(starttime+delay-now)
      else: key = 0
      if key == 1:
        if blthread.direction!=(0,1): blthread.direction = (0,-1)
      elif key == 2:
        if blthread.direction!=(0,-1): blthread.direction = (0,1)
      elif key == 3:
        if blthread.direction!=(1,0): blthread.direction = (-1,0)
      elif key == 4:
        if blthread.direction!=(-1,0): blthread.direction = (1,0)
      elif key == 0:
        if move_snake(blthread): break
        starttime = time.time()

def move_snake(blthread):
  newx = blthread.snake[-1][0] + blthread.direction[0]
  newy = blthread.snake[-1][1] + blthread.direction[1]
  if newx >= blthread.width: newx -= blthread.width
  if newy >= blthread.height: newy -= blthread.height
  if newx < 0:  newx += blthread.width
  if newy < 0:  newy += blthread.height

  # auf sich selbst gefahren?
  if (newx,newy) not in blthread.snake[1:]:
    if (newx,newy) == blthread.zuckerl:
      blthread.snake = blthread.snake + [(newx,newy)]
      blthread.zuckerl = (random.randrange(blthread.width), random.randrange(blthread.height))
    else:
      blthread.snake = blthread.snake[1:] + [(newx,newy)]
    draw_snake(blthread)
    return False
  else:
    for i in range(4):
      blthread.send(blthread.width*blthread.height*"\x00")
      blthread.wait(0.2)
      draw_snake(blthread)
      blthread.wait(0.2)
    text.showtext(blthread, str(len(blthread.snake)), spacing=0)
    blthread.wait(3)
    return True

def draw_snake(blthread):
  data = blthread.width * blthread.height * "\x00"
  for pixel in blthread.snake:
    n = pixel[1] * blthread.width + pixel[0]
    data = data[0:n] + "\x01" + data[n+1:]
  n = blthread.zuckerl[1] * blthread.width + blthread.zuckerl[0]
  data = data[0:n] + "\x01" + data[n+1:]
  blthread.send(data)
