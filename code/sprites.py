import pygame

from pygame.math import Vector2 as vector


# parameter = inheritance
# acts as a super class for all sprite objects
class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, group):
        # call super constructor for super class
        super().__init__(group)
        # show sprite image depending on type
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)


# represents the player object - subclass of Generic
class Player(Generic):
    def __init__(self, pos, group):
        super().__init__(pos, pygame.Surface((32, 64)), group)
        self.image.fill('red')

        # store movement of the player
        # store the direction from the player as a vector
        self.direction = vector()
        # store the position from the player as a vector depending on rectangle top left pos
        self.pos = vector(self.rect.topleft)
        # store speed of the player
        self.speed = 300

    # check player related input
    def input(self):
        # get all pressed keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            # right was pressed move on x-axis
            self.direction.x = 1
        elif keys[pygame.K_LEFT]:
            # left was pressed move on x-axis
            self.direction.x = -1
        else:
            # no direction key was pressed do not move either
            self.direction.x = 0

    def move(self, dt):
        # pygame normally only store integers for movement
        # use separate variable to store floating point numbers
        self.pos += self.direction * self.speed * dt
        # move top left of the rectangle to moved position
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))

    # translate movement into updates for screen
    def update(self, dt):
        self.input()
        self.move(dt)
