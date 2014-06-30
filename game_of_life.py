import sys, pygame, time, numpy, argparse
pygame.init()

# There is some bounds checking problem with the board, may occur when adding surrounding dead from a cell

class ConwaysGameOfLife(object):
    """An implementation of Conway's Game of Life."""
    DEAD = 0
    ALIVE = 1
    
    def __init__(self, size=(32, 32), tile_size=10, updates_per_second=10):
        """The size must be square and divisible by tile_width."""
        self.green = (0, 255, 0)
        self.gray = (50, 50, 100)
        
        self.size = size
        self.tile_size = tile_size
        self.updates_per_second = updates_per_second
        
        self.screen = pygame.display.set_mode((size[0]*tile_size, size[1]*tile_size))
        self.screen.fill(self.gray)
        self.green_tile = pygame.surface.Surface((tile_size, tile_size))
        self.green_tile.fill(self.green)
        self.gray_tile = pygame.surface.Surface((tile_size, tile_size))
        self.gray_tile.fill(self.gray)
        pygame.display.flip()
        
        self.new_alive_cells = []
        self.new_dead_cells = []
        self.alive_cells = set()
        self.board = numpy.zeros((size[0]+4, size[1]+4))# +2 is so we don't have to bounds check later
    
    def run(self):
        """Start the main game loop, respond to events as needed."""
        ITERATE_EVENT = 25
        from pygame import K_SPACE
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
            event = pygame.event.poll()
            if event.type == ITERATE_EVENT:
                if iterate:
                    self.update()
            elif event.type == KEYUP:
                if event.key == K_SPACE:
                    if iterate:
                        iterate = False
                    else:
                        iterate = True
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
        i = click[0]//self.tile_size
        j = click[1]//self.tile_size
        self.new_alive_cells.append((i,j))
        self.alive_cells.add((i,j))
        self.board[i+1, j+1] = ConwaysGameOfLife.ALIVE
        self.update_screen()
    
    def update_screen(self):
        """Update the screen according to the new dead or alive cells."""
        # Dirty Rectangle approach proved slower
        #~ dirty_rects = []
        #~ for i,j in self.new_alive_cells:
            #~ rect = pygame.Rect(i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
            #~ self.screen.blit(self.green_tile, rect)
            #~ dirty_rects.append(rect)
        #~ self.new_alive_cells = []
        #~ for i,j in self.new_dead_cells:
            #~ rect = pygame.Rect(i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
            #~ self.screen.blit(self.gray_tile, rect)
            #~ dirty_rects.append(rect)
        #~ self.new_dead_cells = []
        #~ pygame.display.update(dirty_rects)
        
        # Full refresh is faster
        self.new_alive_cells = []
        self.new_dead_cells = []
        self.screen.fill(self.gray)
        for i,j in self.alive_cells:
            rect = pygame.Rect(i*self.tile_size, j*self.tile_size, self.tile_size, self.tile_size)
            self.screen.blit(self.green_tile, rect)
        pygame.display.flip()
    
    def update(self):
        """Update each alive cell and any surounding dead cells."""
        start = time.time()
        # determine changes necessary to get to next state
        self.relevant_dead_cells = set()
        for i,j in self.alive_cells:
            self.update_alive_cell(i, j)
        for i,j in self.relevant_dead_cells:
            count = self.count_surrounding_alive(i,j)
            if count == 3:
                self.new_alive_cells.append((i,j))
        
        # update board
        for i,j in self.new_dead_cells:
            self.alive_cells.remove((i,j))
            self.board[i+1, j+1] = ConwaysGameOfLife.DEAD
        for i,j in self.new_alive_cells:
            self.alive_cells.add((i,j))
            self.board[i+1, j+1] = ConwaysGameOfLife.ALIVE
        
        print 'Update:', time.time() - start
        start = time.time()
        
        self.update_screen()
        print 'Udate screen:', time.time() - start
    
    def count_surrounding_alive(self, i, j):
         # count alive neighbors
        i += 1
        j += 1
        alive_neighbors = 0
        for di in [-1, 0, 1]:
            for dj in [-1, 1]:
                if self.board[i+di, j+dj] == ConwaysGameOfLife.ALIVE:
                    alive_neighbors += 1
        for di in [-1, 1]:
            if self.board[i+di, j] == ConwaysGameOfLife.ALIVE:
                alive_neighbors += 1
        return alive_neighbors
    
    def update_alive_cell(self, i, j):
        """Update an alive cell."""
        # count alive neighbors
        i += 1
        j += 1
        alive_neighbors = 0
        for di in [-1, 0, 1]:
            for dj in [-1, 1]:
                if self.board[i+di, j+dj] == ConwaysGameOfLife.ALIVE:
                    alive_neighbors += 1
                else:
                    self.relevant_dead_cells.add((i+di-1, j+dj-1))
        for di in [-1, 1]:
            if self.board[i+di, j] == ConwaysGameOfLife.ALIVE:
                alive_neighbors += 1
            else:
                self.relevant_dead_cells.add((i+di-1, j-1))
        # record changed status of cell
        if alive_neighbors < 2 or alive_neighbors > 3:
            self.new_dead_cells.append((i-1,j-1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start Conway's Game of Life. The space bar starts iterating, clicking the mouse will create live cells.")
    parser.add_argument('-x', type=int, dest='width', action='store', default=64, help='Set the width in tiles of the game board.')
    parser.add_argument('-y', type=int, dest='height', action='store', default=64, help='Set the height in tiles of the game board.')
    parser.add_argument('-t', type=int, dest='tile_size', action='store', default=10, help='Set the tile size in pixels (size x size).')
    parser.add_argument('-u', type=int, dest='updates_per_second', action='store', default=10, help='Set the number of updates per second.')
    args = parser.parse_args()
    
    game = ConwaysGameOfLife((args.width, args.height), args.tile_size, args.updates_per_second)
    game.run()
