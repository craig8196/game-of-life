import sys, pygame, time, numpy, argparse
pygame.init()

# Use time to make updates less than desired to keep interactivity.

class ConwaysGameOfLife(object):
    """An implementation of Conway's Game of Life."""
    DEAD = 0
    ALIVE = 1
    
    def __init__(self, size=(32, 32), tile_size=10, updates_per_second=10):
        """The size must be divisible by tile_width."""
        self.green = (0, 255, 0)
        self.gray = (50, 50, 50)
        # Used to access all surrounding cells
        self.differences = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
        
        self.size = size
        self.tile_size = tile_size
        self.updates_per_second = updates_per_second
        
        self.screen = pygame.display.set_mode((size[0]*tile_size, size[1]*tile_size))
        self.screen.fill(self.gray)
        self.green_tile = pygame.surface.Surface((tile_size, tile_size))
        self.green_tile.fill(self.green)
        self.gray_tile = pygame.surface.Surface((tile_size, tile_size))
        self.gray_tile.fill(self.gray)
        pygame.display.set_caption("Conway's Game of Life")
        pygame.display.flip() # show a gray screen
        
        self.new_alive_cells = []
        self.new_dead_cells = []
        self.alive_cells = set()
        self.counts = numpy.zeros((size[0]+2, size[1]+2))# +2 is so we don't have to bounds check later
        for i in xrange(0, size[0]+2):
            self.counts[i,0] = -100
            self.counts[i,size[1]+1] = -100
        for j in xrange(0, size[1]+2):
            self.counts[0,j] = -100
            self.counts[size[0]+1, j] = -100
    
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
            if event.type == ITERATE_EVENT:
                if iterate:
                    self.update()
            elif event.type == KEYUP:
                if event.key == K_SPACE:
                    if iterate:
                        iterate = False
                    else:
                        iterate = True
                if event.key == K_RIGHT:
                    self.update()
            elif event.type == MOUSEBUTTONDOWN:
                add_cell = True
                self.create_cell(event.pos)
            elif event.type == MOUSEBUTTONUP:
                add_cell = False
            elif event.type == MOUSEMOTION:
                if add_cell:
                    self.create_cell(event.pos)
            elif event.type == QUIT:
                sys.exit()
    
    def create_cell(self, click):
        """Create cell at click location. Or delete it."""
        i = click[0]//self.tile_size + 1
        j = click[1]//self.tile_size + 1
        if (i, j) not in self.alive_cells:
            self.new_alive_cells.append((i,j))
            self.alive_cells.add((i,j))
            self.increment_counts(i, j)
            self.update_screen()
    
    def increment_counts(self, i, j):
        for di,dj in self.differences:
            self.counts[i+di, j+dj] += 1
    
    def decrement_counts(self, i, j):
        for di,dj in self.differences:
            self.counts[i+di, j+dj] -= 1
    
    def count_surrounding_alive(self, i, j):
        """Count alive neighbors."""
        alive_neighbors = 0
        for di,dj in self.differences:
            if (i+di, j+dj) in self.alive_cells:
                alive_neighbors += 1
        return alive_neighbors
    
    def update_screen(self):
        """Update the screen according to the new dead or alive cells."""
        if len(self.new_dead_cells) + len(self.new_alive_cells) < 200:
            dirty_rects = []
            for i,j in self.new_alive_cells:
                rect = pygame.Rect(i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
                self.screen.blit(self.green_tile, rect)
                dirty_rects.append(rect)
            self.new_alive_cells = []
            for i,j in self.new_dead_cells:
                rect = pygame.Rect(i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
                self.screen.blit(self.gray_tile, rect)
                dirty_rects.append(rect)
            self.new_dead_cells = []
            pygame.display.update(dirty_rects)
        else:
            self.new_alive_cells = []
            self.new_dead_cells = []
            self.screen.fill(self.gray)
            for i,j in self.alive_cells:
                rect = pygame.Rect((i-1)*self.tile_size, (j-1)*self.tile_size, self.tile_size, self.tile_size)
                self.screen.blit(self.green_tile, rect)
            pygame.display.flip()
    
    def update(self):
        """Update each alive cell and any surounding dead cells."""
        start = time.time()
        # determine changes necessary to get to next state
        relevant_dead_cells = set()
        for i,j in self.alive_cells:
            if self.counts[i,j] < 2 or self.counts[i,j] > 3:
                self.new_dead_cells.append((i, j))
            for di,dj in self.differences:
                if (i+di,j+dj) not in self.alive_cells:
                    relevant_dead_cells.add((i+di,j+dj))
        for i,j in relevant_dead_cells:
            if self.counts[i,j] == 3:
                self.new_alive_cells.append((i,j))
        
        # update counts and volatile cells
        self.volatile_cells = set()
        for i,j in self.new_dead_cells:
            self.alive_cells.remove((i,j))
            self.decrement_counts(i, j)
        for i,j in self.new_alive_cells:
            self.alive_cells.add((i,j))
            self.increment_counts(i, j)
        
        print 'Update:', time.time() - start
        start = time.time()
        
        self.update_screen()
        print 'Update screen:', time.time() - start
    
    def update_cell(self, i, j):
        """Update an alive cell."""
        # record changed status of cell
        if (i,j) in self.alive_cells:
            if self.counts[i,j] < 2 or self.counts[i,j] > 3:
                self.new_dead_cells.add((i, j))
        else:
            if self.counts[i,j] == 3:
                self.new_alive_cells.append((i, j))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Conway's Game of Life. The space bar starts iterating, clicking the mouse will create live cells. The right arrow will perform one iteration.")
    parser.add_argument('-x', type=int, dest='width', action='store', default=64, help='Set the width in tiles of the game board.')
    parser.add_argument('-y', type=int, dest='height', action='store', default=64, help='Set the height in tiles of the game board.')
    parser.add_argument('-t', type=int, dest='tile_size', action='store', default=10, help='Set the tile size in pixels (size x size).')
    parser.add_argument('-u', type=int, dest='updates_per_second', action='store', default=10, help='Set the number of updates per second.')
    args = parser.parse_args()
    
    game = ConwaysGameOfLife((args.width, args.height), args.tile_size, args.updates_per_second)
    game.run()
