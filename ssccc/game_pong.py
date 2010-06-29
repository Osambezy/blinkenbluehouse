import text

import time
import math
import random

def main(blthread):
  print "PONG"
  if blthread.width<4 and blthread.height<4:
    print "matrix too small for pong"
    return
  elif blthread.width<4:
    pong1D(blthread, False)
  elif blthread.height<4:
    pong1D(blthread, True)
  else:
    pong2D(blthread)

def pong1D(blthread, horiz):
  blthread.controls = ["Shift_L", "Shift_R"]
  if horiz:
    size = blthread.width
    witdh = blthread.height
  else:
    size = blthread.height
    width = blthread.width
  direction = 0
  wins = [0, 0]
  while True:
    speed = 1.5
    min_speed = 1.0
    max_speed = 5.0
    speed_accel = 0.99
    while True:
      ping = time.time()
      hit = False
      for i in range(0,size+1):
        if i == 0: data = size * "\x00"
        else:
          if direction: h = i
          else: h = size - i + 1
          data = (h-1) * "\x00" + "\x01" + (size-h) * "\x00"
        show1D(blthread, data, horiz)
        if blthread.waitforkey(speed/(size+1), direction+1):
          pong = time.time()
          factor = 1 - ((pong-ping) / speed)
          if factor < 0: factor = 0
          speed = min_speed + math.pow(factor,0.7) * (max_speed - min_speed)
          min_speed *= speed_accel
          max_speed *= speed_accel
          direction = (direction + 1) % 2
          hit = True
          break
      if hit: continue
      else:
        wins[direction] += 1
        data1 = (1-direction) * (size-wins[direction]) * "\x00" + wins[direction] * "\x01" + (direction) * (size-wins[direction]) * "\x00"
        data2 = (direction) * (size-wins[(direction+1)%2]) * "\x00" + wins[(direction+1)%2] * "\x01" + (1-direction) * (size-wins[(direction+1)%2]) * "\x00"
        for i in range(0,2):
          show1D(blthread, data1, horiz)
          blthread.wait(0.3)
          blthread.clear()
          blthread.wait(0.3)
          show1D(blthread, data2, horiz)
          blthread.wait(0.3)
          blthread.clear()
          blthread.wait(0.3)
        blthread.wait(2)
        if wins[direction] >= 5:
          wins = [0,0]
          blthread.wait(3)
        break

def show1D(blthread, data, horiz):
  output = ""
  for i in range (0, blthread.height):
    for j in range (0, blthread.width):
      if horiz and i==0: output += data[j]
      elif (not horiz) and j==0: output += data[i]
      else: output += "\x00"
  blthread.send(output)

def pong2D(blthread):
  blthread.controls = ["a", "y", "Up", "Down"]
  # assume square pixels:
  width =  1.0 * (blthread.width - 2)
  height = 1.0 * blthread.height
  bat_size = 2
  speed = 8.0
  bat1 = (blthread.height - bat_size) / 2
  bat2 = (blthread.height - bat_size) / 2
  while True:
    position = (0.0, random.uniform(0.0, height))
    angle = random.uniform(-math.pi/3, math.pi/3) % (2*math.pi)
    pixel = (int(math.floor(position[0] / width * blthread.width)) + 1, int(math.floor(position[1] / height * blthread.height)))
    starttime = time.time()
    while True:
      show2D(blthread, pixel, bat1, bat2, bat_size)
      (d, newpixel, newpos, newangle) = cross_pixel(blthread, pixel, width, height, position, angle)
      delay = d / speed
      now = time.time()
      if now < starttime+delay: key = blthread.waitforanykey(starttime+delay-now)
      else: key = 0
      if key == 1:
        if bat1 > 0: bat1 -= 1
      elif key == 2:
        if bat1 < blthread.height - bat_size: bat1 += 1
      elif key == 3:
        if bat2 > 0: bat2 -= 1
      elif key == 4:
        if bat2 < blthread.height - bat_size: bat2 += 1
      elif key == 0:
        if newpixel[0]<0 or newpixel[0] > blthread.width-1:
          break
        (pixel, position, angle) = (newpixel, newpos, newangle)
        starttime = time.time()


def cross_pixel(blthread, pixel, width, height, position, angle):
  angle = angle % (2 * math.pi)
  pos_bounds = (width * (pixel[0] - 1) / (blthread.width-2), width * pixel[0] / (blthread.width-2), height * pixel[1] / blthread.height, height * (pixel[1] + 1) / blthread.height)
  if angle==0:
    d = max(0.0, pos_bounds[1]-position[0])
    newpos = (pos_bounds[1], position[1])
    newpixel = (pixel[0] + 1, pixel[1])
  elif angle>0 and angle<math.pi/2:
    dr = (pos_bounds[1]-position[0]) / math.cos(angle)
    dt = -(pos_bounds[2]-position[1]) / math.sin(angle)
    if dr<dt:
      d = dr
      newpixel = (pixel[0] + 1, pixel[1])
    else:
      d = dt
      newpixel = (pixel[0], pixel[1] - 1)
  elif angle==math.pi/2:
    d = max(0.0, position[1]-pos_bounds[2])
    newpos = (position[0], pos_bounds[2])
    newpixel = (pixel[0], pixel[1] - 1)
  elif angle>math.pi/2 and angle<math.pi:
    dl = (pos_bounds[0]-position[0]) / math.cos(angle)
    dt = -(pos_bounds[2]-position[1]) / math.sin(angle)
    if dl<dt:
      d = dl
      newpixel = (pixel[0] - 1, pixel[1])
    else:
      d = dt
      newpixel = (pixel[0], pixel[1] - 1)
  elif angle==math.pi:
    d = max(0.0, position[0]-pos_bounds[0])
    newpos = (pos_bounds[0], position[1])
    newpixel = (pixel[0] - 1, pixel[1])
  elif angle>math.pi and angle<math.pi*3/2:
    dl = (pos_bounds[0]-position[0]) / math.cos(angle)
    db = -(pos_bounds[3]-position[1]) / math.sin(angle)
    if dl<db:
      d = dl
      newpixel = (pixel[0] - 1, pixel[1])
    else:
      d = db
      newpixel = (pixel[0], pixel[1] + 1)
  elif angle==math.pi*3/2:
    d = max(0.0, pos_bounds[3]-position[1])
    newpos = (position[0], pos_bounds[3])
    newpixel = (pixel[0], pixel[1] + 1)
  elif angle>math.pi*3/2:
    dr = (pos_bounds[1]-position[0]) / math.cos(angle)
    db = -(pos_bounds[3]-position[1]) / math.sin(angle)
    if dr<db:
      d = dr
      newpixel = (pixel[0] + 1, pixel[1])
    else:
      d = db
      newpixel = (pixel[0], pixel[1] + 1)

  newpos = (position[0] + math.cos(angle)*d, position[1] - math.sin(angle)*d)
  newangle = angle
  if newpos[1] <= 0.5:
    newpos = (newpos[0], 1.0 - newpos[1])
    newangle = -angle % (2*math.pi)
    if newpixel[1] < 0:
      newpixel = (newpixel[0], 1)
  elif newpos[1] >= height - 0.5:
    newpos = (newpos[0], 2*height - 1.0 - newpos[1])
    newangle = -angle % (2*math.pi)
    if newpixel[1] > blthread.height-1:
      newpixel = (newpixel[0], blthread.height-2)
  return (d, newpixel, newpos, newangle)

def show2D(blthread, pixel, bat1, bat2, bat_size):
  data = blthread.width * blthread.height * "\x00"
  for i in range(bat_size):
    pos = (bat1 + i) * blthread.width
    data = data[0:pos] + "\x01" + data[pos+1:]
    pos = (bat2 + i + 1) * blthread.width - 1
    data = data[0:pos] + "\x01" + data[pos+1:]
  pos = pixel[1] * blthread.width + pixel[0]
  data = data[0:pos] + "\x01" + data[pos+1:]
  blthread.send(data)
