import random
from time import time

from blthreads.threads import Game
import blthreads.text as text


class SnakeGame(Game):
    def run(self):
        self.controls = ['Up', 'Down', 'Left', 'Right']
        delay = 0.5
        while True:
            self.snake = [(0,0),(0,0)]
            self.direction = (1,0)
            self.new_point_to_eat()
            starttime = time()
            while True:
                now = time()
                if now < starttime+delay:
                    key = self.waitforanykey(starttime+delay-now)
                else:
                    key = 0
                if key == 1:
                    if self.direction!=(0,1): self.direction = (0,-1)
                elif key == 2:
                    if self.direction!=(0,-1): self.direction = (0,1)
                elif key == 3:
                    if self.direction!=(1,0): self.direction = (-1,0)
                elif key == 4:
                    if self.direction!=(-1,0): self.direction = (1,0)
                elif key == 0:
                    if self.move_snake(): break
                    starttime = time()

    def move_snake(self):
        newx = self.snake[-1][0] + self.direction[0]
        newy = self.snake[-1][1] + self.direction[1]
        if newx >= self.width:
            newx -= self.width
        elif newx < 0:
            newx += self.width
        if newy >= self.height:
            newy -= self.height
        elif newy < 0:
            newy += self.height
        # Check if the snake crashed into itself
        if (newx,newy) in self.snake[1:]:
            for i in range(4):
                self.send(self.width*self.height*'\x00')
                self.wait(0.2)
                self.draw_snake()
                self.wait(0.2)
            text.showtext(self, str(len(self.snake)), spacing=0)
            self.wait(3)
            return True
        if (newx,newy) == self.point_to_eat:
            self.snake = self.snake + [(newx,newy)]
            self.new_point_to_eat()
        else:
            self.snake = self.snake[1:] + [(newx,newy)]
        self.draw_snake()
        return False

    def new_point_to_eat(self):
        self.point_to_eat = \
            (random.randrange(self.width), random.randrange(self.height))

    def draw_snake(self):
        data = self.width * self.height * '\x00'
        for pixel in self.snake:
            n = pixel[1] * self.width + pixel[0]
            data = data[0:n] + '\x01' + data[n+1:]
        n = self.point_to_eat[1] * self.width + self.point_to_eat[0]
        data = data[0:n] + '\x01' + data[n+1:]
        self.send(data)
