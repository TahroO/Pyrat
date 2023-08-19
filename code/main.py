import pygame

from settings import *
from support import *

# import load function to load images
from pygame.image import load

from editor import Editor


class Main:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.imports()

        self.editor = Editor(self.land_tiles)

        # mouse cursor replacement
        # load image which should replace cursor
        surface = (load
                   ("/home/brot/Documents/Projects/Phyton/Pyrat_Platformer/graphics/cursors/mouse.png").convert_alpha())
        # clickable area (1 para) is top coord of cursor which interacts when clicked / rest of cursor is just graphic
        cursor = pygame.cursors.Cursor((0, 0), surface)
        pygame.mouse.set_cursor(cursor)

    # import the land terrain tiles
    def imports(self):
        self.land_tiles = import_folder_dict('../graphics/terrain/land')
        print(self.land_tiles)

    def run(self):
        while True:
            dt = self.clock.tick() / 1000

            self.editor.run(dt)
            pygame.display.update()


if __name__ == '__main__':
    main = Main()
    main.run()
