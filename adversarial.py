from __future__ import division
import sys, pygame, time, numpy, argparse
pygame.init()

# Colors
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

class ConwaysGameOfLife(object):
    """An adversarial version of Conway's Game of Life."""
    
    def __init__(self, size=(12, 12), tile_size=10, updates_per_second=10):
        """The size must be divisible by tile_width."""
        # Used to access all surrounding cells
        self.differences = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
        
        self.size = size
        self.tile_size = tile_size
        self.updates_per_second = updates_per_second
        self.UNCLAIMED = -1
        self.UNCLAIMABLE = -100
        self.teams = [BLUE, RED]
        self.team_nums = []
        for i in range(len(self.teams)):
            self.team_nums.append(i)
        self.turn = 0
        
        self.tiles = []
        for i in range(len(self.teams)):
            screen = pygame.surface.Surface((tile_size, tile_size))
            screen.fill(self.teams[i])
            self.tiles.append(screen)
        self.screen = pygame.display.set_mode((size[0]*tile_size, size[1]*tile_size))
        self.screen.fill(GRAY)
        pygame.display.set_caption("Conway's Game of Life")
        pygame.display.flip() # show a gray screen
        
        self.new_alive_cells = {}
        self.new_dead_cells = set()
        self.alive_cells = {}
        self.health = numpy.zeros((size[0]+2, size[1]+2))# +2 is so we don't have to bounds check later
    
    def run(self):
        """Start the main game loop, respond to events as needed."""
        ITERATE_EVENT = 25 # Create our own event for signalling updating the game state
        from pygame import K_SPACE, K_RIGHT
        from pygame import QUIT, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
        pygame.event.set_allowed([QUIT, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, ITERATE_EVENT])
        milliseconds_to_next_update = 1000//self.updates_per_second
        if milliseconds_to_next_update < 1:
            milliseconds_to_next_update = 1
        pygame.time.set_timer(ITERATE_EVENT, milliseconds_to_next_update)
        pygame.event.pump()
        iterate = False
        add_cell = False
        while 1:
            event = pygame.event.wait()
            if event.type == MOUSEBUTTONUP:
                self.create_cell(event.pos)
            elif event.type == QUIT:
                sys.exit()
    
    def change_turn(self):
        self.turn = (self.turn + 1)%len(self.teams)
        if self.turn == 0:
            self.update()
    
    def create_cell(self, click):
        """Create cell at click location. Or delete it."""
        i = click[0]//self.tile_size + 1
        j = click[1]//self.tile_size + 1
        if (i, j) not in self.alive_cells:
            self.new_alive_cells[(i,j)] = self.turn
            self.alive_cells[(i,j)] = self.turn
            self.health[i,j] = 10
            self.update_screen()
            self.change_turn()
    
    def count(self, i, j, team):
        friends = 0
        enemies = 0
        for di,dj in self.differences:
            if (i+di,j+dj) in self.alive_cells:
                if self.alive_cells[(i+di,j+dj)] == team:
                    friends += 1
                else:
                    enemies += 1
        return friends, enemies
    
    def shade(self, i, j, team):
        r,g,b = self.teams[team]
        return (int((r/2) + (r/2)*self.health[i,j]/10), int((g/2) + (g/2)*self.health[i,j]/10), int((b/2) + (b/2)*self.health[i,j]/10))
    
    def update_screen(self):
        """Update the screen according to the new dead or alive cells."""
        #~ if len(self.new_dead_cells) + len(self.new_alive_cells) < 200:
        dirty_rects = []
        for coords, team in self.alive_cells.items():
            i,j = coords
            rect = pygame.Rect((i-1)*self.tile_size, (j-1)*self.tile_size, self.tile_size, self.tile_size)
            self.screen.fill(self.shade(i,j,team), rect)
            dirty_rects.append(rect)
        self.new_alive_cells = {}
        for i,j in self.new_dead_cells:
            rect = pygame.Rect((i-1)*self.tile_size, (j-1)*self.tile_size, self.tile_size, self.tile_size)
            self.screen.fill(GRAY, rect)
            dirty_rects.append(rect)
        self.new_dead_cells = set()
        pygame.display.update(dirty_rects)
        #~ else:
            #~ self.new_alive_cells = []
            #~ self.new_dead_cells = []
            #~ self.screen.fill(self.gray)
            #~ for i,j in self.alive_cells:
                #~ rect = pygame.Rect((i-1)*self.tile_size, (j-1)*self.tile_size, self.tile_size, self.tile_size)
                #~ self.screen.blit(self.green_tile, rect)
            #~ pygame.display.flip()
    
    def spawn(self, i, j):
        counts = {}
        for di,dj in self.differences:
            if (i+di,j+dj) in self.alive_cells:
                counts[self.alive_cells[(i+di,j+dj)]] = counts.setdefault(self.alive_cells[(i+di,j+dj)], 0) + 1
        if len(counts) == 0:
            return -1,-1
        else:
            m_team = None
            m_count = 0
            for team, count in counts.items():
                if count > m_count:
                    m_team = team
                    m_count = count
            return m_team, m_count
    
    def update(self):
        """Update each alive cell and any surounding dead cells."""
        start = time.time()
        # determine changes necessary to get to next state
        relevant_dead_cells = set()
        for coords, team in self.alive_cells.items():
            i,j = coords
            count_friendly, count_enemy = self.count(i,j,team)
            if count_friendly < 3:
                self.health[i,j] -= (3 - count_friendly)
            elif count_friendly > 6:
                self.health[i,j] -= count_friendly
            self.health[i,j] -= count_enemy*2
            if self.health[i,j] <= 0:
                self.new_dead_cells.add((i, j))
            for di,dj in self.differences:
                if (i+di,j+dj) not in self.alive_cells:
                    relevant_dead_cells.add((i+di,j+dj))
        for i,j in relevant_dead_cells:
            if i < 1 or i > self.size[0] or j < 1 or j > self.size[1]:
                continue
            team, count = self.spawn(i,j)
            if count >= 3:
                self.new_alive_cells[(i,j)] = team
                self.health[i,j] = 10
        
        # update counts and volatile cells
        self.volatile_cells = set()
        for i,j in self.new_dead_cells:
            del self.alive_cells[(i,j)]
        for coords, team in self.new_alive_cells.items():
            self.alive_cells[coords] = team
        
        print 'Update:', time.time() - start
        start = time.time()
        
        self.update_screen()
        print 'Update screen:', time.time() - start

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Conway's Game of Life. The space bar starts iterating, clicking the mouse will create live cells. The right arrow will perform one iteration.")
    parser.add_argument('-x', type=int, dest='width', action='store', default=12, help='Set the width in tiles of the game board.')
    parser.add_argument('-y', type=int, dest='height', action='store', default=12, help='Set the height in tiles of the game board.')
    parser.add_argument('-t', type=int, dest='tile_size', action='store', default=30, help='Set the tile size in pixels (size x size).')
    parser.add_argument('-u', type=int, dest='updates_per_second', action='store', default=10, help='Set the number of updates per second.')
    args = parser.parse_args()
    
    game = ConwaysGameOfLife((args.width, args.height), args.tile_size, args.updates_per_second)
    game.run()
