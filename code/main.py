import pygame
from pygame.math import Vector2 as vector

from settings import *
from support import *

# import load function to load images
from pygame.image import load

from editor import Editor
from level import Level


class Main:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.imports()

        # check if editor is active to switch between editor and level updater
        self.editor_active = True
        # transition object when switching between level and editor mode
        self.transition = Transition(self.toggle)
        self.editor = Editor(self.land_tiles, self.switch)

        # mouse cursor replacement
        # load image which should replace cursor
        surface = (load
                   ("/home/brot/Documents/Projects/Phyton/Pyrat_Platformer/graphics/cursors/mouse.png").convert_alpha())
        # clickable area (1 para) is top coord of cursor which interacts when clicked / rest of cursor is just graphic
        cursor = pygame.cursors.Cursor((0, 0), surface)
        pygame.mouse.set_cursor(cursor)

    # import the terrain tiles used for level creation
    def imports(self):
        # TERRAIN
        self.land_tiles = import_folder_dict('../graphics/terrain/land')
        # import a water tile
        self.water_bottom = load('../graphics/terrain/water/water_bottom.png').convert_alpha()
        self.water_top_animation = import_folder('../graphics/terrain/water/animation')

        # COINS
        self.gold = import_folder('../graphics/items/gold')
        self.silver = import_folder('../graphics/items/silver')
        self.diamond= import_folder('../graphics/items/diamond')
        self.particle = import_folder('../graphics/items/particle')

    # switch editor on and off helper method
    def toggle(self):
        self.editor_active = not self.editor_active

    # call transition of game modes
    def switch(self, grid = None):
        # starting animation
        self.transition.active = True
        # we go from editor to level
        if grid:
            # Level object needs to know switch status
            # create a new level everytime a switch happens
            # to not load every graphic on its on pass in a dictionary
            self.level = Level(grid, self.switch, {
                'land': self.land_tiles,
                # water bottom
                'water bottom': self.water_bottom,
                'water top': self.water_top_animation,
                # coins - types
                'gold': self.gold,
                'silver': self.silver,
                'diamond': self.diamond,
                'particle': self.particle,
            })

    def run(self):
        while True:
            dt = self.clock.tick() / 1000

            # run editor only on editor mode
            if self.editor_active:
                self.editor.run(dt)
            else:
                # run level mode
                self.level.run(dt)
            # do transition when change happens
            self.transition.display(dt)
            pygame.display.update()


# Transition object class to make switch between editor and level smoother
class Transition:
    def __init__(self, toggle):
        self.display_surface = pygame.display.get_surface()
        self.toggle = toggle
        self.active = False

        # should be a circle closing and opening to mid
        self.border_width = 0
        self.direction = 1
        self.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        self.radius = vector(self.center).magnitude()
        # make sure the whole window is filled - acts as a reverse point
        self.threshold = self.radius + 100

    def display(self, dt):
        # if transition happens
        if self.active:
            # increase width of border circle -> closing
            self.border_width += 1000 * dt * self.direction
            # reverse the direction to open transition again when fully closed
            if self.border_width >= self.threshold:
                self.direction = -1
                # toggle game modes when transition is active
                self.toggle()

            # stop transition when opening animation is done completely
            if self.border_width < 0:
                # reset all stats to start over
                self.active = False
                self.border_width = 0
                self.direction = 1
            # draw border in defined direction (open - close)
            pygame.draw.circle(self.display_surface, 'black', self.center, self.radius, int(self.border_width))


if __name__ == '__main__':
    main = Main()
    main.run()
