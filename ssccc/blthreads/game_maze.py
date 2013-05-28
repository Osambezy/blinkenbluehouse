import random
from time import time
from itertools import product

from blthreads.threads import Game
import blthreads.text as text


class MazeGame(Game):

    def run(self):
        MAZE_WIDTH = 8  # maze units, not pixels!
        MAZE_HEIGHT = 8
        BLINK_DELAY = 0.3
        self.controls = ['Up', 'Down', 'Left', 'Right']
        while True:
            self.new_maze(MAZE_WIDTH, MAZE_HEIGHT)
            starttime = time()
            blinktime = starttime
            posblink = False
            goalblink = False
            while True:
                now = time()
                if now < blinktime + BLINK_DELAY / 2:
                    key = self.waitforanykey(blinktime + BLINK_DELAY / 2 - now)
                else:
                    key = 0
                if key == 1:
                    newposition = (self.position[0], self.position[1] - 1)
                elif key == 2:
                    newposition = (self.position[0], self.position[1] + 1)
                elif key == 3:
                    newposition = (self.position[0] - 1, self.position[1])
                elif key == 4:
                    newposition = (self.position[0] + 1, self.position[1])
                elif key == 0:
                    newposition = self.position
                    goalblink = not goalblink
                    if goalblink:
                        posblink = not posblink
                    blinktime = time()
                if self.check_pos(newposition):
                    self.position = newposition
                if self.position == self.goal:
                    break
                self.draw(posblink, goalblink)
            seconds = int(time() - starttime)
            self.clear()
            self.wait(1)
            text.showtext(self, str(seconds), spacing=0)
            self.wait(5)
            self.clear()
            self.wait(1)

    def check_pos(self, pos):
        x = pos[0]
        y = pos[1]
        xeven = (x % 2 == 0)
        yeven = (y % 2 == 0)
        if x < 0 or y < 0 or \
                x > len(self.walls[0]) * 2 or y > len(self.walls) * 2:
            return True
        elif xeven and yeven:
            return False
        elif (not xeven) and (not yeven):
            return True
        elif x == 0 or y == 0:
            return False
        elif xeven and (not yeven):
            return not self.walls[(y - 1) / 2][(x - 2) / 2][0]
        elif (not xeven) and yeven:
            return not self.walls[(y - 2) / 2][(x - 1) / 2][1]

    def draw(self, pos_on, goal_on):
        center = ((self.width - 1) // 2, (self.height - 1) // 2)
        data = ''
        for (y, x) in product(range(self.height), range(self.width)):
            if self.check_pos((self.position[0] + x - center[0],
                               self.position[1] + y - center[1])):
                data += '\x00'
            else:
                data += '\x01'
        if pos_on:
            pos = center[1] * self.width + center[0]
            data = data[0:pos] + '\x01' + data[pos + 1:]
        if goal_on:
            x = self.goal[0] - self.position[0] + center[0]
            y = self.goal[1] - self.position[1] + center[1]
            if x >= 0 and x < self.width and y >= 0 and y < self.height:
                pos = y * self.width + x
                data = data[0:pos] + '\x01' + data[pos + 1:]
        self.send(data)

    def new_maze(self, maze_width, maze_height):
        self.status = [[False for i in range(maze_width)] for
                       j in range(maze_height)]
        self.walls = [[[True, True] for i in range(maze_width)] for
                      j in range(maze_height)]
        start = (random.randrange(maze_width), random.randrange(maze_height))
        end = self.fill(start)[1]
        del self.status
        self.position = (start[0] * 2 + 1, start[1] * 2 + 1)
        self.goal = (end[0] * 2 + 1, end[1] * 2 + 1)

    def fill(self, point):
        """Generate the maze recursively and return the longest way.

        Arguments:
        point -- (x, y) of the current point, must not be filled yet

        Return value:
        (distance, point) -- distance in maze units and coordinates of the
                             point most far away from the start
        """
        if self.status[point[1]][point[0]]:
            raise Exception('Point already filled')
        self.status[point[1]][point[0]] = True
        farest_point = (1, point)
        while True:
            directions = ((0, -1), (1, 0), (0, 1), (-1, 0))
            walldirections = ((0, -1, 1), (0, 0, 0), (0, 0, 1), (-1, 0, 0))
            possible_neighbors = []
            corresponding_walls = []
            for dir in range(4):
                x = point[0] + directions[dir][0]
                y = point[1] + directions[dir][1]
                if x >= 0 and x < len(self.status[0]) and y >= 0 and \
                        y < len(self.status) and not self.status[y][x]:
                    possible_neighbors += [(x, y)]
                    corresponding_walls += [(point[0] + walldirections[dir][0],
                                             point[1] + walldirections[dir][1],
                                             walldirections[dir][2])]
            if len(possible_neighbors) == 0:
                return farest_point
            next = random.randrange(len(possible_neighbors))
            self.walls[corresponding_walls[next][1]] \
                      [corresponding_walls[next][0]] \
                      [corresponding_walls[next][2]] = False
            newpoint = self.fill(possible_neighbors[next])
            if newpoint[0] >= farest_point[0]:
                farest_point = (newpoint[0] + 1, newpoint[1])

    def print_maze(self):
        """Print the maze to the console for debugging."""
        width = len(self.walls[0])
        height = len(self.walls)
        print (2 * width + 1) * '##'
        for row in range(height):
            output = '##'
            for col in range(width):
                if self.walls[row][col][0]:
                    output += '  ##'
                else:
                    output += '    '
            print output
            output = '##'
            for col in range(width):
                if self.walls[row][col][1]:
                    output += '####'
                else:
                    output += '  ##'
            print output
