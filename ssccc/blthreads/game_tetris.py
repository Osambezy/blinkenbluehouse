import random
from time import time
from itertools import product

from blthreads.threads import Game
import blthreads.text as text


#BLOCKS = (((-1,0),(0,0),(1,0),(2,0)),    ((0,-1),(0,0),(1,0),(1,1)),    ((0,-1),(0,0),(-1,0),(-1,1)),    ((0,-1),(0,0),(0,1),(1,1)),    ((0,-1),(0,0),(0,1),(-1,1)),    ((0,0),(1,0),(0,1),(1,1)),    ((-1,0),(0,0),(1,0),(0,1)))
BLOCKS = \
((((0,0),(0,1)),((0,0),(1,0))), \
(((0,0),(0,1),(1,0)),((0,0),(1,0),(1,1)),((1,0),(1,1),(0,1)),((1,1),(0,1),(0,0))), \
(((0,0),),), \
(((0,0),(1,1)),((0,1),(1,0))), \
(((-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)),), \
(((-1,-1), (1,-1), (1,1), (-1,1), (0,0)),))
BLOCKS_PROB = (10, 10, 6, 10, 0, 0)

class TetrisGame(Game):

    def run(self):
        self.controls = ['Left', 'Right', 'Down', 'space',
                         'Up', 'Prior', 'Next']
        self.newgame()
        starttime = time()
        while True:
            now = time()
            if now < starttime+self.falldelay:
                key = self.waitforanykey(starttime+self.falldelay-now)
            else:
                key = 0
            if key == 1 and self.test_block(self.blockx - 1,
                                            self.blocky, self.blockframe):
                self.blockx -= 1
            elif key == 2 and self.test_block(self.blockx + 1,
                                              self.blocky, self.blockframe):
                self.blockx += 1
            elif key == 4 and self.test_block(self.blockx,
                    self.blocky,(self.blockframe + 1) % len(BLOCKS[self.blocktyp])):
                self.blockframe = (self.blockframe + 1) % len(BLOCKS[self.blocktyp])
            elif key == 3:
                if self.falldelay>0: self.falldelay = 0.05
            elif key == 5: self.forceblock = 2    # admin mode ;-)
            elif key == 6: self.forceblock = 4
            elif key == 7: self.forceblock = 5
            elif key == 0:
                self.fall()
                starttime = time()
            self.draw()

    def newgame(self):
        self.delay = 0.6
        self.falldelay = self.delay
        self.rows = 0
        self.canvas = self.height * [self.width * [0]]
        self.forceblock = -1
        self.new_block()

    def new_block(self):
        self.blockx = int(self.width / 2)
        self.blocky = -1
        if self.forceblock==-1:
            totalprob = 0
            for prob in BLOCKS_PROB: totalprob += prob
            x = random.randrange(totalprob)
            for i in range(len(BLOCKS)):
                if x<BLOCKS_PROB[i]:
                    self.blocktyp = i
                    break
                else:
                    x -= BLOCKS_PROB[i]
        else:
            self.blocktyp = self.forceblock
            self.forceblock = -1
        self.blockframe = random.randrange(len(BLOCKS[self.blocktyp]))

    def fall(self):
        if self.test_block(self.blockx,self.blocky+1,self.blockframe):
            self.blocky += 1
            return
        # Block hits bottom
        for pixel in BLOCKS[self.blocktyp][self.blockframe]:
            self.canvas[self.blocky + pixel[1]] = \
                self.canvas[self.blocky + pixel[1]][0:self.blockx + pixel[0]] + \
                [1] + self.canvas[self.blocky + pixel[1]][self.blockx + pixel[0] + 1:]
        self.blocky = -20
        for i in range(0, len(self.canvas)):
            if self.canvas[i] == self.width * [1]:
                self.blink(i)
                self.canvas = [self.width * [0]] + self.canvas[0:i] + \
                              self.canvas[i+1:]
                self.rows += 1
                self.delay -= 0.02
        self.new_block()
        self.falldelay = self.delay
        if not self.test_block(self.blockx,self.blocky,self.blockframe):
            self.blink(-1,0.2)
            text.showtext(self, str(self.rows), spacing=0)
            self.wait(3)
            self.newgame()

    def test_block(self, newx,newy,newframe):
        test = True
        for pixel in BLOCKS[self.blocktyp][newframe]:
            nx = pixel[0] + newx
            ny = pixel[1] + newy
            if ny < 0:
                ny = 0
            if nx<0 or nx>=self.width or ny>=self.height:
                # Outside game area
                test = False
            elif self.canvas[ny][nx] != 0:
                # Collides with other blocks
                test = False
        return test

    def draw(self):
        data = ''
        # Draw canvas
        for (i, j) in product(range(0,self.height), range(0,self.width)):
            data += chr(self.canvas[i][j])
        # Draw current block
        for pixel in BLOCKS[self.blocktyp][self.blockframe]:
            if self.blocky + pixel[1] >= 0:
                pos = (self.blocky + pixel[1]) * self.width + \
                    self.blockx + pixel[0]
                data = data[0:pos] + '\x01' + data[pos+1:]
        self.send(data)

    def blink(self, row, delay = 0.1):
        if row == -1:
            # Blink everything
            for i in range(0,6):
                self.clear()
                self.wait(delay)
                self.draw()
                self.wait(delay)
        elif row>=0 and row<self.height:
            # Blink row
            for i in range(0,3):
                self.canvas[row] = self.width * [0]
                self.draw()
                self.wait(delay)
                self.canvas[row] = self.width * [1]
                self.draw()
                self.wait(delay)
