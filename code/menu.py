import pygame
from settings import *

class Menu:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        # call the menu
        self.create_buttons()

    def create_buttons(self):

        # create menu area
        size = 180
        margin = 6
        # create a tuple for the top left corner of menu box
        topleft = (WINDOW_WIDTH - size - margin, WINDOW_HEIGHT - size - margin)
        # create a tuple of size of the menu box because we need 2 tuples for rect or 4 plain numbers
        box_size = (size, size)
        # use a rectangle from pygame, use this as positioning box for the other buttons
        self.rect = pygame.Rect(topleft, box_size)

        # button areas
        # all buttons have same size -> using pattern
        button_margin = 5
        button_margin_tuple = (-button_margin, -button_margin)
        button_size = (self.rect.width / 2, self.rect.height / 2)
        generic_button_rect = pygame.Rect(self.rect.topleft, button_size)
        # create 4 different button areas
        # inflate is used to shrink the button rect with margin
        self.tile_button_rect = generic_button_rect.copy().inflate(button_margin_tuple)
        # draw coin menu
        self.coin_button_rect = generic_button_rect.move(self.rect.width / 2, 0).inflate(button_margin_tuple)
        # draw enemy menu
        self.enemy_button_rect = generic_button_rect.move(self.rect.width / 2, self.rect.width / 2).inflate(button_margin_tuple)
        # draw palm menu
        self.palm_button_rect = generic_button_rect.move(0, self.rect.width / 2).inflate(button_margin_tuple)


    def display(self):
        # draw the outer box of the menu box using for positioning
        # pygame.draw.rect(self.display_surface, 'red', self.rect)
        pygame.draw.rect(self.display_surface, 'green', self.tile_button_rect)
        pygame.draw.rect(self.display_surface, 'blue', self.coin_button_rect)
        pygame.draw.rect(self.display_surface, 'black', self.enemy_button_rect)
        pygame.draw.rect(self.display_surface, 'yellow', self.palm_button_rect)