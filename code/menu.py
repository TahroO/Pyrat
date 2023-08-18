import pygame
from settings import *
from pygame.image import load


class Menu:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        # create data needs to be called before creating buttons to load images
        self.create_data()
        # call the menu
        self.create_buttons()

    # imports data for item images, sprites and more
    # using the path to create an actual surface for later use
    def create_data(self):
        self.menu_surfaces = {}
        for key, value in EDITOR_DATA.items():
            # check if there is a surface
            if value['menu']:
                if not value['menu'] in self.menu_surfaces:
                    # if there is no previous entry create a new collection
                    # [(key, load(value['menu_surf']))] creates a tuple of key, value pair
                    self.menu_surfaces[value['menu']] = [(key, load(value['menu_surf']))]
                else:
                    # if there is already a matching entry append the next to this collection
                    self.menu_surfaces[value['menu']].append((key, load(value['menu_surf'])))

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
        self.enemy_button_rect = generic_button_rect.move(self.rect.width / 2, self.rect.width / 2).inflate(
            button_margin_tuple)
        # draw palm menu
        self.palm_button_rect = generic_button_rect.move(0, self.rect.width / 2).inflate(button_margin_tuple)

        # create the buttons with matching tiles
        # create a group first
        self.buttons = pygame.sprite.Group()
        # create individual buttons
        Button(self.tile_button_rect, self.buttons, self.menu_surfaces['terrain'])
        Button(self.coin_button_rect, self.buttons, self.menu_surfaces['coin'])
        Button(self.enemy_button_rect, self.buttons, self.menu_surfaces['enemy'])
        Button(self.palm_button_rect, self.buttons, self.menu_surfaces['palm fg'], self.menu_surfaces['palm bg'])

    def click(self, mouse_pos, mouse_button):
        # check if we are clicking on any button
        for sprite in self.buttons:
            if sprite.rect.collidepoint(mouse_pos):
                if mouse_button[1]: # middle mouse click
                    # if the sprite has alternative items switch main mode / else just set true
                    if sprite.items['alt']:
                        sprite.main_active = not sprite.main_active
                if mouse_button[2]: # right click
                    sprite.switch()
                return sprite.get_id()

    # highlight the selected button
    def highlight_indicator(self, index):
        if EDITOR_DATA[index]['menu'] == 'terrain':
            pygame.draw.rect(self.display_surface, BUTTON_LINE_COLOR, self.tile_button_rect.inflate(4, 4),
                             5, 4)
        if EDITOR_DATA[index]['menu'] == 'coin':
            pygame.draw.rect(self.display_surface, BUTTON_LINE_COLOR, self.coin_button_rect.inflate(4, 4),
                             5, 4)
        if EDITOR_DATA[index]['menu'] == 'enemy':
            pygame.draw.rect(self.display_surface, BUTTON_LINE_COLOR, self.enemy_button_rect.inflate(4, 4),
                             5, 4)
        if EDITOR_DATA[index]['menu'] in ('palm fg', 'palm bg'):
            pygame.draw.rect(self.display_surface, BUTTON_LINE_COLOR, self.palm_button_rect.inflate(4, 4),
                             5, 4)

    def display(self, index):
        # draw the outer box of the menu box using for positioning
        # pygame.draw.rect(self.display_surface, 'red', self.rect)
        # pygame.draw.rect(self.display_surface, 'green', self.tile_button_rect)
        # pygame.draw.rect(self.display_surface, 'blue', self.coin_button_rect)
        # pygame.draw.rect(self.display_surface, 'black', self.enemy_button_rect)
        # pygame.draw.rect(self.display_surface, 'yellow', self.palm_button_rect)

        self.buttons.update()
        self.buttons.draw(self.display_surface)
        self.highlight_indicator(index)


# button class will be a sprite - parameter for inheritance
class Button(pygame.sprite.Sprite):
    # items = foreground palm , items_alt = background palm / switch with middle mouse on sprite
    def __init__(self, rect, group, items, items_alt=None):
        super().__init__(group)
        self.image = pygame.Surface(rect.size)
        self.rect = rect

        # items
        self.items = {'main': items, 'alt': items_alt}
        self.index = 0
        self.main_active = True

    # get the id of the clicked button tile
    def get_id(self):
        # get the index from a new list with images, either main or alternative
        return self.items['main' if self.main_active else 'alt'][self.index][0]

    # switches images for buttons
    def switch(self):
        self.index += 1
        # setting self index initial to 0 if the index is greater or equal to the length of the image list
        # if not just use self index - removes len error for lists
        self.index = 0 if self.index >= len(self.items['main' if self.main_active else 'alt']) else self.index

    # display the actual sprite as button
    def update(self):
        self.image.fill(BUTTON_BG_COLOR)
        # return a tuple with index of graphic and graphic
        surface = self.items['main' if self.main_active else 'alt'][self.index][1]
        # choose local distance to center of button to place image correct
        rectangle = surface.get_rect(center = (self.rect.width / 2, self.rect.height / 2))
        # pack image on top of the surface
        self.image.blit(surface, rectangle)