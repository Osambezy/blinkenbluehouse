import math
import random
from time import time

from blthreads.threads import Game
import blthreads.text as text


class PongGame(Game):

    def run(self):
        if self.width < 4 and self.height < 4:
            print 'matrix too small for pong'
            return
        elif self.width < 4:
            self.horiz = False
            self.pong1D()
        elif self.height < 4:
            self.horiz = True
            self.pong1D()
        else:
            self.pong2D()

    def pong1D(self):
        self.controls = ['Shift_L', 'Shift_R']
        if self.horiz:
            self.size = self.width
        else:
            self.size = self.height
        direction = 0
        self.wins = [0, 0]
        while True:
            speed = 1.5
            min_speed = 1.0
            max_speed = 5.0
            speed_accel = 0.99
            while True:
                ping = time()
                hit = False
                for i in range(0, self.size + 1):
                    if i == 0:
                        data = self.size * '\x00'
                    else:
                        if direction:
                            h = i
                        else:
                            h = self.size - i + 1
                        data = (h - 1) * '\x00' + '\x01' + \
                               (self.size - h) * '\x00'
                    self.show1D(data)
                    if self.waitforkey(speed / (self.size + 1), direction + 1):
                        pong = time()
                        factor = 1 - ((pong - ping) / speed)
                        if factor < 0:
                            factor = 0
                        speed = min_speed + math.pow(factor, 0.7) * \
                            (max_speed - min_speed)
                        min_speed *= speed_accel
                        max_speed *= speed_accel
                        direction = (direction + 1) % 2
                        hit = True
                        break
                if hit:
                    continue
                else:
                    self.clear()
                    self.wins[direction] += 1
                    self.wait(0.5)
                    self.show_wins(show_lower_first=(direction==1))
                    self.wait(1.5)
                    if self.wins[direction] >= 5:
                        self.wins = [0, 0]
                        self.wait(2)
                    break

    def show1D(self, data):
        output = ''
        for i in range(0, self.height):
            for j in range(0, self.width):
                if self.horiz and i == 0:
                    output += data[j]
                elif not self.horiz and j == self.col:
                    output += data[i]
                else:
                    output += '\x00'
        self.send(output)

    def show_wins(self, show_lower_first):
        data0 = (self.size - self.wins[0]) * '\x00' + self.wins[0] * '\x01'
        data1 = self.wins[1] * '\x01' + (self.size - self.wins[1]) * '\x00'
        if show_lower_first:
            data0, data1 = data1, data0
        for i in range(0, 2):
            self.show1D(data0)
            self.wait(0.3)
            self.clear()
            self.wait(0.3)
            self.show1D(data1)
            self.wait(0.3)
            self.clear()
            self.wait(0.3)

    def pong2D(self):
        # Work in progress
        self.controls = ['a', 'y', 'Up', 'Down']
        pixel_aspect_ratio = 1.0
        width = pixel_aspect_ratio * (self.width - 2)
        height = self.height
        bat_size = 2
        speed = 8.0
        bat1 = (self.height - bat_size) / 2
        bat2 = (self.height - bat_size) / 2
        while True:
            position = (0.0, random.uniform(0.0, height))
            angle = random.uniform(-math.pi / 3, math.pi / 3) % (2 * math.pi)
            pixel = (
                int(math.floor(position[0] / width * self.width)) + 1,
                int(math.floor(position[1] / height * self.height)))
            starttime = time()
            while True:
                self.show2D(pixel, bat1, bat2, bat_size)
                (d, newpixel, newpos, newangle) = self.cross_pixel(
                    pixel, width, height, position, angle)
                delay = d / speed
                now = time()
                if now < starttime + delay:
                    key = self.waitforanykey(starttime + delay - now)
                else:
                    key = 0
                if key == 1:
                    if bat1 > 0:
                        bat1 -= 1
                elif key == 2:
                    if bat1 < self.height - bat_size:
                        bat1 += 1
                elif key == 3:
                    if bat2 > 0:
                        bat2 -= 1
                elif key == 4:
                    if bat2 < self.height - bat_size:
                        bat2 += 1
                elif key == 0:
                    if newpixel[0] < 0 or newpixel[0] > self.width - 1:
                        break
                    (pixel, position, angle) = (newpixel, newpos, newangle)
                    starttime = time()

    def cross_pixel(self, pixel, width, height, position, angle):
        angle = angle % (2 * math.pi)
        pos_bounds = (width * (pixel[0] - 1) / (self.width - 2),
                      width * pixel[0] / (self.width - 2),
                      height * pixel[1] / self.height,
                      height * (pixel[1] + 1) / self.height)
        if angle == 0:
            d = max(0.0, pos_bounds[1] - position[0])
            newpos = (pos_bounds[1], position[1])
            newpixel = (pixel[0] + 1, pixel[1])
        elif angle > 0 and angle < math.pi / 2:
            dr = (pos_bounds[1] - position[0]) / math.cos(angle)
            dt = -(pos_bounds[2] - position[1]) / math.sin(angle)
            if dr < dt:
                d = dr
                newpixel = (pixel[0] + 1, pixel[1])
            else:
                d = dt
                newpixel = (pixel[0], pixel[1] - 1)
        elif angle == math.pi / 2:
            d = max(0.0, position[1] - pos_bounds[2])
            newpos = (position[0], pos_bounds[2])
            newpixel = (pixel[0], pixel[1] - 1)
        elif angle > math.pi / 2 and angle < math.pi:
            dl = (pos_bounds[0] - position[0]) / math.cos(angle)
            dt = -(pos_bounds[2] - position[1]) / math.sin(angle)
            if dl < dt:
                d = dl
                newpixel = (pixel[0] - 1, pixel[1])
            else:
                d = dt
                newpixel = (pixel[0], pixel[1] - 1)
        elif angle == math.pi:
            d = max(0.0, position[0] - pos_bounds[0])
            newpos = (pos_bounds[0], position[1])
            newpixel = (pixel[0] - 1, pixel[1])
        elif angle > math.pi and angle < math.pi * 3 / 2:
            dl = (pos_bounds[0] - position[0]) / math.cos(angle)
            db = -(pos_bounds[3] - position[1]) / math.sin(angle)
            if dl < db:
                d = dl
                newpixel = (pixel[0] - 1, pixel[1])
            else:
                d = db
                newpixel = (pixel[0], pixel[1] + 1)
        elif angle == math.pi * 3 / 2:
            d = max(0.0, pos_bounds[3] - position[1])
            newpos = (position[0], pos_bounds[3])
            newpixel = (pixel[0], pixel[1] + 1)
        elif angle > math.pi * 3 / 2:
            dr = (pos_bounds[1] - position[0]) / math.cos(angle)
            db = -(pos_bounds[3] - position[1]) / math.sin(angle)
            if dr < db:
                d = dr
                newpixel = (pixel[0] + 1, pixel[1])
            else:
                d = db
                newpixel = (pixel[0], pixel[1] + 1)
        newpos = (position[0] + math.cos(angle) * d,
                  position[1] - math.sin(angle) * d)
        newangle = angle
        if newpos[1] <= 0.5:
            newpos = (newpos[0], 1.0 - newpos[1])
            newangle = -angle % (2 * math.pi)
            if newpixel[1] < 0:
                newpixel = (newpixel[0], 1)
        elif newpos[1] >= height - 0.5:
            newpos = (newpos[0], 2 * height - 1.0 - newpos[1])
            newangle = -angle % (2 * math.pi)
            if newpixel[1] > self.height - 1:
                newpixel = (newpixel[0], self.height - 2)
        return (d, newpixel, newpos, newangle)

    def show2D(self, pixel, bat1, bat2, bat_size):
        data = self.width * self.height * '\x00'
        for i in range(bat_size):
            pos = (bat1 + i) * self.width
            data = data[0:pos] + '\x01' + data[pos + 1:]
            pos = (bat2 + i + 1) * self.width - 1
            data = data[0:pos] + '\x01' + data[pos + 1:]
        pos = pixel[1] * self.width + pixel[0]
        data = data[0:pos] + '\x01' + data[pos + 1:]
        self.send(data)
