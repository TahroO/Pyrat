import pygame, sys
from pygame.math import Vector2 as vector

from settings import *
from support import *

class Level:
    # constructor
    def __init__(self, grid, switch):
        self.display_surface = pygame.display.get_surface()
        self.switch = switch

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
        self.display_surface.fill('red')