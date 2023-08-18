import pygame, sys
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_position
from settings import *


class Editor:
    def __init__(self):

        # main setup
        self.display_surface = pygame.display.get_surface()

        # navigation / vector imported by pygame.math
        self.origin = vector()
        self.pan_active = False
        self.pan_offset = vector()
        # support lines - draw lines on a new surface to be able to change transparency
        self.support_line_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        # remove the green color of the support surface
        self.support_line_surface.set_colorkey('green')
        # change transparency of support surface
        self.support_line_surface.set_alpha(30)
        # input

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            self.pan_input(event)

    def pan_input(self, event):
        # middle mouse button was pressed or released
        # mouse_buttons() imported at the top returns a tuple of possible button events and [1] is middle
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
            self.pan_active = True
            # offset is distance between origin and mouse position as vector
            # this get movement from mouse when button is pressed without setting point to mouse position
            self.pan_offset = vector(mouse_position()) - self.origin
            print('middle mouse button')
        if not mouse_buttons()[1]:
            self.pan_active = False

        if event.type == pygame.MOUSEWHEEL:
            # move y position when ctrl is pressed and mousewheel up or down is pressed
            if pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.origin.y -= event.y * 50
                # move the x position otherwise
            else:
                self.origin.x -= event.y * 50

        if self.pan_active:
            # get position from mouse was imported on top -> mouse position
            self.origin = mouse_position()
        # panning update
        if self.pan_active:
            # convert self.origin as vector to access x and y position
            self.origin = vector(mouse_position()) - self.pan_offset

    # drawing

    # draw a infinite grid for orientation and tile placing reasons over the screen
    def draw_tile_lines(self):
        # amount of columns
        cols = WINDOW_WIDTH // TILE_SIZE
        # amount of rows
        rows = WINDOW_HEIGHT // TILE_SIZE

        # to not run out of lines place a vector always in front of the origin the actual origin for the grid
        origin_offset = vector(
            x=self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
            y=self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE
        )
        self.support_line_surface.fill('green')
        # draw lines for all columns
        for col in range(cols + 1):
            # distance between cols is the size of the tiles
            x = origin_offset.x + col * TILE_SIZE
            # draw on support surface
            pygame.draw.line(self.support_line_surface, LINE_COLOR, (x, 0), (x, WINDOW_HEIGHT))

        for row in range(rows + 1):
            y = origin_offset.y + row * TILE_SIZE
            # draw on support surface
            pygame.draw.line(self.support_line_surface, LINE_COLOR, (0, y), (WINDOW_WIDTH, y))
        # place the green support surface on display surface
        self.display_surface.blit(self.support_line_surface, (0, 0))

    def run(self, dt):

        self.event_loop()

        # drawing
        self.display_surface.fill('white')
        self.draw_tile_lines()
        pygame.draw.circle(self.display_surface, 'red', self.origin, 10)
