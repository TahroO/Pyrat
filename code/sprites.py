import pygame

from pygame.math import Vector2 as vector

from settings import *


# parameter = inheritance
# acts as a super class for all sprite objects
class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, group):
        # call super constructor for super class
        super().__init__(group)
        # show sprite image depending on type
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)


# Class defining custom collisions
class Block(Generic):
    # spawn an invisible block for collision (no sprite)
    def __init__(self, pos, size, group):
        # placeholder surface with a given size
        surf = pygame.Surface(size)
        super().__init__(pos, surf, group)


# ANIMATIONS
# represents animated objects -> water - subclass of Generic
class Animated(Generic):
    def __init__(self, assets, pos, group):
        # create a list of surfaces
        self.animation_frames = assets
        # used to pick 1 surf from assets list
        self.frame_index = 0
        super().__init__(pos, self.animation_frames[self.frame_index], group)

    # animate tiles
    def animate(self, dt):
        # increase index for using different tiles in animation
        self.frame_index += ANIMATION_SPEED * dt
        self.frame_index = 0 if self.frame_index >= len(self.animation_frames) else self.frame_index
        self.image = self.animation_frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


# represents the particle objects
class Particle(Animated):
    def __init__(self, assets, pos, group):
        super().__init__(assets, pos, group)
        # align particle and coin pos to center
        self.rect = self.image.get_rect(center=pos)

    # overwrite animate method for this object due to particle should be animated only once
    def animate(self, dt):
        # increase index for using different tiles in animation
        self.frame_index += ANIMATION_SPEED * dt
        # kill object when animation is done once
        if self.frame_index < len(self.animation_frames):
            self.image = self.animation_frames[int(self.frame_index)]
        else:
            self.kill()


# represents the coin objects
class Coin(Animated):
    def __init__(self, coin_type, assets, pos, group):
        super().__init__(assets, pos, group)
        # center all images inside the cells
        self.rect = self.image.get_rect(center=pos)
        self.coin_type = coin_type


# ENEMIES
class Spikes(Generic):
    def __init__(self, surf, pos, group):
        super().__init__(pos, surf, group)


class Tooth(Generic):
    def __init__(self, assets, pos, group):
        self.animation_frames = assets
        self.frame_index = 0
        self.orientation = 'right'
        surf = self.animation_frames[f'run_{self.orientation}'][self.frame_index]
        super().__init__(pos, surf, group)
        # relocate sprite to set it in correct place in cell (without gap)
        self.rect.bottom = self.rect.top + TILE_SIZE


class Shell(Generic):
    def __init__(self, orientation, assets, pos, group):
        self.orientation = orientation
        # to use both directions of shell use assets.copy
        # otherwise shell will point in the same direction as last one
        self.animation_frames = assets.copy()
        # check if to flip animation
        if orientation == 'right':
            for key, value in self.animation_frames.items():
                # overwrite keys with flipped sprites
                self.animation_frames[key] = [pygame.transform.flip(surf, True, False) for surf in value]

        self.frame_index = 0
        self.status = 'idle'
        super().__init__(pos, self.animation_frames[self.status][self.frame_index], group)
        # relocate sprite to set it in correct place in cell (without gap)
        self.rect.bottom = self.rect.top + TILE_SIZE


# represents the player object - subclass of Generic
class Player(Generic):
    def __init__(self, pos, assets, group, collision_sprites):
        # animation - logic
        self.animation_frames = assets
        self.frame_index = 0
        self.status = 'idle'
        self.orientation = 'right'
        # gets the actual surface for key / value pairs using string concatenation to get a list
        surf = self.animation_frames[f'{self.status}_{self.orientation}'][self.frame_index]

        super().__init__(pos, surf, group)

        # store movement of the player
        # store the direction from the player as a vector
        self.direction = vector()
        # store the position from the player as a vector depending on rectangle center pos
        self.pos = vector(self.rect.center)
        # store speed of the player
        self.speed = 300
        # gravity value for falling / jumping
        self.gravity = 4
        # boolean if object is touching a floor to determine possible jump
        self.on_floor = False

        # collision section
        self.collision_sprites = collision_sprites
        # player hit box
        self.hitbox = self.rect.inflate(-50, 0)

    # check player related input
    def input(self):
        # get all pressed keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            # right was pressed move on x-axis
            self.direction.x = 1
            # set orientation for animation
            self.orientation = 'right'
        elif keys[pygame.K_LEFT]:
            # left was pressed move on x-axis
            self.direction.x = -1
            # set orientation for animation
            self.orientation = 'left'
        else:
            # no direction key was pressed do not move either
            self.direction.x = 0

        # jumping mechanic
        # if jump key was pressed and player is on ground (able to jump)
        if keys[pygame.K_SPACE] and self.on_floor:
            # move player up in y direction
            self.direction.y = -2

    # method to determine the actual movement status for player to pick correct animation
    def get_status(self):
        # jumping
        if self.direction.y < 0:
            self.status = 'jump'
        # falling
        # due to collision check every frame player always moves down a bit and gets reset on surface afterward
        # y has to be > 1 because of this fact or player is in constantly falling animation
        elif self.direction.y > 1:
            self.status = 'fall'
        else:
            # moving
            if self.direction.x != 0:
                self.status = 'run'
            # standing still
            else:
                self.status = 'idle'

    def animate(self, dt):
        # list of frames like in __init__ method to get correct sprite
        current_animation = self.animation_frames[f'{self.status}_{self.orientation}']
        # increase index for using different tiles in animation
        self.frame_index += ANIMATION_SPEED * dt
        self.frame_index = 0 if self.frame_index >= len(current_animation) else self.frame_index
        self.image = current_animation[int(self.frame_index)]

    def move(self, dt):
        # horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')
        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')

    # gravity
    def apply_gravity(self, dt):
        # falling down increase y exponential ( 2 * +=)
        self.direction.y += self.gravity * dt
        self.rect.y += self.direction.y

    # check if player is on floor and able to jump
    # (otherwise air jumps are possible)
    def check_on_floor(self):
        floor_rect = pygame.Rect(self.hitbox.bottomleft, (self.hitbox.width, 2))
        floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.colliderect(floor_rect)]
        self.on_floor = True if floor_sprites else False

    # collision
    def collision(self, direction):
        # check all possible sprites to collide with
        for sprite in self.collision_sprites:
            # check if player hit box collide with sprite
            if sprite.rect.colliderect(self.hitbox):
                if direction == 'horizontal':
                    # moving right
                    if self.direction.x > 0:
                        # if collision happens set right site of hit box to left side of obstacle
                        self.hitbox.right = sprite.rect.left
                    # moving left
                    if self.direction.x < 0:
                        # if collision happens set right site of hit box to left side of obstacle
                        self.hitbox.left = sprite.rect.right
                    # update rectangle center when collision happens to draw player correct
                    self.rect.centerx = self.hitbox.centerx
                    self.pos.x = self.hitbox.centerx
                else:  # check vertical collision
                    # player hit a wall while jumping - set player top to bottom side of obstacle
                    self.hitbox.top = sprite.rect.bottom if self.direction.y < 0 else self.hitbox.top
                    # player moving down and overlaps wall with bottom - set position on top of obstacle
                    self.hitbox.bottom = sprite.rect.top if self.direction.y > 0 else self.hitbox.bottom
                    # update rectangle center when collision happens to draw player correct
                    self.rect.centery, self.pos.y = self.hitbox.centery, self.hitbox.centery
                    # player collided with something on the ground reset gravity (fall - speed)
                    self.direction.y = 0

    # translate movement into updates for screen
    def update(self, dt):
        self.input()
        self.apply_gravity(dt)
        self.move(dt)
        self.check_on_floor()

        # check after movement and gravity important!
        self.get_status()
        self.animate(dt)
