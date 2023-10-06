import pygame

from pygame.math import Vector2 as vector

from settings import *
from timer import Timer
from random import choice, randint


# parameter = inheritance
# acts as a super class for all sprite objects
class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, group, z=LEVEL_LAYERS['main']):
        # call super constructor for super class
        super().__init__(group)
        # show sprite image depending on type
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        # make sure player is always in foreground
        self.z = z


# Class defining custom collisions
class Block(Generic):
    # spawn an invisible block for collision (no sprite)
    def __init__(self, pos, size, group):
        # placeholder surface with a given size
        surf = pygame.Surface(size)
        super().__init__(pos, surf, group)


# Clouds
class Cloud(Generic):
    def __init__(self, pos, surf, group, left_limit):
        super().__init__(pos, surf, group, LEVEL_LAYERS['clouds'])
        # kill clouds when outside level
        self.left_limit = left_limit

        # movement
        self.pos = vector(self.rect.topleft)
        # different movement speed
        self.speed = randint(20, 30)

    def update(self, dt):
        # clouds always move to the left
        self.pos.x -= self.speed * dt
        self.rect.x = round(self.pos.x)
        # destroy cloud outside level limits
        if self.rect.x <= self.left_limit:
            self.kill()


# ANIMATIONS
# represents animated objects -> water - subclass of Generic
class Animated(Generic):
    def __init__(self, assets, pos, group, z=LEVEL_LAYERS['main']):
        # create a list of surfaces
        self.animation_frames = assets
        # used to pick 1 surf from assets list
        self.frame_index = 0
        super().__init__(pos, self.animation_frames[self.frame_index], group, z)

    # animate tiles
    def animate(self, dt):
        # increase index for using different tiles in animation
        self.frame_index += ANIMATION_SPEED * dt
        self.frame_index = 0 if self.frame_index >= len(self.animation_frames) else self.frame_index
        self.image = self.animation_frames[int(self.frame_index)]

    # Update method
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
        # create a mask for proper collision
        self.mask = pygame.mask.from_surface(self.image)


class Tooth(Generic):
    def __init__(self, assets, pos, group, collision_sprites):
        # general setup
        self.animation_frames = assets
        self.frame_index = 0
        self.orientation = 'right'
        surf = self.animation_frames[f'run_{self.orientation}'][self.frame_index]
        super().__init__(pos, surf, group)
        # relocate sprite to set it in correct place in cell (without gap)
        self.rect.bottom = self.rect.top + TILE_SIZE
        # create a mask for proper collision
        self.mask = pygame.mask.from_surface(self.image)

        # movement
        # choice randomize starting left or right side direction
        self.direction = vector(choice((1, -1)), 0)
        # make sure orientation matches direction upon spawn
        self.orientation = 'left' if self.direction.x < 0 else 'right'
        self.pos = vector(self.rect.topleft)
        self.speed = 120
        self.collision_sprites = collision_sprites

        # destroy tooth at start when not on floor using collection comparison
        # check if any point collides below the player - object - if not list is empty
        if not [sprite for sprite in collision_sprites
                if sprite.rect.collidepoint(self.rect.midbottom + vector(0, 10))]:
            self.kill()

    def animate(self, dt):
        current_animation = self.animation_frames[f'run_{self.orientation}']
        self.frame_index += ANIMATION_SPEED * dt
        self.frame_index = 0 if self.frame_index >= len(current_animation) else self.frame_index
        self.image = current_animation[int(self.frame_index)]
        # as the image changes when animation occurs a new mask is needed every time
        self.mask = pygame.mask.from_surface(self.image)

    def move(self, dt):
        # create indicator blocks to change direction when collision happens or no more ground is left
        # check ground right
        right_gap = self.rect.bottomright + vector(1, 1)
        # check collision right
        right_block = self.rect.midright + vector(1, 0)
        # check ground left
        left_gap = self.rect.bottomleft + vector(-1, 1)
        # check collision left
        left_block = self.rect.midleft + vector(-1, 0)

        # moving right
        if self.direction.x > 0:
            # check for collisions
            # floor collision
            floor_sprites = [sprite for sprite in self.collision_sprites
                             if sprite.rect.collidepoint(right_gap)]
            # wall collision
            wall_sprites = [sprite for sprite in self.collision_sprites
                            if sprite.rect.collidepoint(right_block)]
            # a collision happened or no floor - change direction
            if wall_sprites or not floor_sprites:
                self.direction.x *= -1
                self.orientation = 'left'
        # moving left
        if self.direction.x < 0:
            # floor collision
            floor_sprites = [sprite for sprite in self.collision_sprites
                             if sprite.rect.collidepoint(left_gap)]
            # wall collision
            wall_sprites = [sprite for sprite in self.collision_sprites
                            if sprite.rect.collidepoint(left_block)]
            # a collision happened or no floor - change direction
            if wall_sprites or not floor_sprites:
                self.direction.x *= -1
                self.orientation = 'right'

        self.pos.x += self.direction.x * self.speed * dt
        self.rect.x = round(self.pos.x)

    def update(self, dt):
        self.animate(dt)
        self.move(dt)


class Shell(Generic):
    def __init__(self, orientation, assets, pos, group, pearl_surf, damage_sprites):
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

        # pearl
        self.pearl_surf = pearl_surf
        self.has_shot = False
        self.attack_cooldown = Timer(2000)
        self.damage_sprites = damage_sprites

    def animate(self, dt):
        current_animation = self.animation_frames[self.status]
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index >= len(current_animation):
            self.frame_index = 0
            if self.has_shot:
                self.attack_cooldown.activate()
                self.has_shot = False
        self.image = current_animation[int(self.frame_index)]
        # check if 3rd frame of animation (shoot frame)
        if int(self.frame_index) == 2 and self.status == 'attack' and not self.has_shot:
            # goes left (x-axis) when orientation is left
            pearl_direction = vector(-1, 0) if self.orientation == 'left' else vector(1, 0)
            # create a pearl that needs an offset to not "rolL" on floor
            offset = (pearl_direction * 50) + vector(0, -10) if self.orientation == 'left' \
                else (pearl_direction * 20 + vector(0, -10))
            Pearl((self.rect.center + offset), pearl_direction, self.pearl_surf,
                  [self.groups()[0], self.damage_sprites])
            self.has_shot = True

    def get_status(self):
        # if player is close enough
        # get player position and distance to shell position
        if (vector(self.player.rect.center).distance_to(vector(self.rect.center)) < 500
                and not self.attack_cooldown.active):
            self.status = 'attack'
        else:
            self.status = 'idle'

    def update(self, dt):
        self.get_status()
        self.animate(dt)
        self.attack_cooldown.update()


# represents the pearl which is shot by shells
class Pearl(Generic):
    def __init__(self, pos, direction, surf, group):
        super().__init__(pos, surf, group)
        # create a mask for proper collision
        self.mask = pygame.mask.from_surface(self.image)

        # movement
        self.pos = vector(self.rect.topleft)
        self.direction = direction
        self.speed = 150

        # self destruct
        self.timer = Timer(6000)
        self.timer.activate()

    def update(self, dt):
        # movement
        self.pos.x += self.direction.x * self.speed * dt
        self.rect.x = round(self.pos.x)
        # timer
        self.timer.update()
        if not self.timer.active:
            self.kill()


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
        # create a mask for proper collision
        self.mask = pygame.mask.from_surface(self.image)

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

        # timer make sure damage occurrence is limited
        self.invul_timer = Timer(200)

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

    # damage method if a damage-collision with the player occurred
    def damage(self):
        # player was hit ->
        # implement HP LOGIC here
        # check if invulnerable timer is not active
        if not self.invul_timer.active:
            # start invulnerable timer to limit damage
            self.invul_timer.activate()
            # make player jump on hit -> optical damage indicator
            self.direction.y -= 1.5
            # implement HP logic here
            print('ouch')

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
        # every animation image changes, a new mask is needed for that
        self.mask = pygame.mask.from_surface(self.image)

        # player was damaged -> make it visible by flashing in a color
        if self.invul_timer.active:
            # transform mask to a new surface
            surf = self.mask.to_surface()
            # get rid of black inside the surface
            surf.set_colorkey('black')
            # use this mask as new image
            self.image = surf

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
        self.invul_timer.update()

        # check after movement and gravity important!
        self.get_status()
        self.animate(dt)
