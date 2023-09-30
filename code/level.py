import pygame, sys
from pygame.math import Vector2 as vector

from settings import *
from support import *

from sprites import *


class Level:
    # constructor
    def __init__(self, grid, switch, asset_dict):
        self.display_surface = pygame.display.get_surface()
        self.switch = switch

        # groups of sprites - basic sprite group
        self.all_sprites = pygame.sprite.Group()

        # when level is created
        self.build_level(grid, asset_dict)

    # build the level - loading layers and graphics
    def build_level(self, grid, asset_dict):
        # go through all layers
        for layer_name, layer in grid.items():
            for pos, data in layer.items():
                if layer_name == 'terrain':
                    # create a generic sprite
                    Generic(pos, asset_dict['land'][data], self.all_sprites)
                # phyton switch
                match data:
                    # player object
                    case 0: self.player = Player(pos, self.all_sprites)

    # loop for actualisation inside the level
    def event_loop(self):
        for event in pygame.event.get():
            # in case game is quited stop the loop
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                # if escape was pressed inside the level -> switch to editor mode calling transition
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.switch()

    def run(self, dt):
        self.event_loop()
        # fill the level background red
        self.display_surface.fill(SKY_COLOR)
        self.all_sprites.update(dt)
        self.all_sprites.draw(self.display_surface)
