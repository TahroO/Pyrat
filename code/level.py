import pygame, sys
from pygame.math import Vector2 as vector

from settings import *
from support import *

from sprites import *
from random import choice, randint

class Level:
    # constructor
    def __init__(self, grid, switch, asset_dict):
        self.display_surface = pygame.display.get_surface()
        self.switch = switch

        # groups of sprites - basic sprite group
        self.all_sprites = CameraGroup()
        self.coin_sprites = pygame.sprite.Group()
        self.damage_sprites = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group()
        self.shell_sprites = pygame.sprite.Group()

        # when level is created
        self.build_level(grid, asset_dict)

        # level limits - dimensions
        self.level_limits = {
            # end of level with offset - player never sees a cloud disappear
            'left': -WINDOW_WIDTH,
            # rightmost terrain tile + 500
            # create a sorted list of all terrain tiles by horizontal position -> last one -> x value
            # gets the right most item + offset to be safe
            'right':  sorted(list(grid['terrain'].keys()), key=lambda pos: pos[0])[-1][0] + 500
        }

        # ADDITIONAL stuff - support variables
        self.particle_surfs = asset_dict['particle']
        # store cloud surface
        self.cloud_surfs = asset_dict['clouds']
        # create a new type of event
        self.cloud_timer = pygame.USEREVENT + 2
        # create a cloud every 2 seconds
        pygame.time.set_timer(self.cloud_timer, 2000)
        self.startup_clouds()

    # build the level - loading layers and graphics
    def build_level(self, grid, asset_dict):
        # go through all layers
        for layer_name, layer in grid.items():
            for pos, data in layer.items():
                if layer_name == 'terrain':
                    # create a generic sprite
                    Generic(pos, asset_dict['land'][data],
                            [self.all_sprites, self.collision_sprites])
                if layer_name == 'water':
                    if data == 'top':
                        # create animated sprite
                        Animated(asset_dict['water top'], pos, self.all_sprites, LEVEL_LAYERS['water'])
                    else:
                        # create plain water sprite
                        Generic(pos, asset_dict['water bottom'], self.all_sprites, LEVEL_LAYERS['water'])
                # python switch
                match data:
                    # PLAYER

                    # player object
                    case 0:
                        self.player = Player(pos, asset_dict['player'], self.all_sprites, self.collision_sprites)

                    # SKY

                    # horizon position
                    case 1:
                        self.horizon_y = pos[1]
                        self.all_sprites.horizon_y = pos[1]

                    # COINS

                    # gold
                    case 4:
                        Coin('gold', asset_dict['gold'], pos,
                             [self.all_sprites, self.coin_sprites])
                    # silver
                    case 5:
                        Coin('silver', asset_dict['silver'], pos,
                             [self.all_sprites, self.coin_sprites])
                    # diamond
                    case 6:
                        Coin('diamond', asset_dict['diamond'], pos,
                             [self.all_sprites, self.coin_sprites])

                    # ENEMIES

                    # spikes
                    case 7:
                        Spikes(asset_dict['spikes'], pos, [self.all_sprites, self.damage_sprites])
                    # tooth - needs to know collision items but is not in that group
                    case 8:
                        Tooth(asset_dict['tooth'], pos, [self.all_sprites, self.damage_sprites],
                              self.collision_sprites)
                    # shell pointing left
                    case 9:
                        Shell(
                            orientation='left',
                            assets=asset_dict['shell'],
                            pos=pos,
                            group=[self.all_sprites, self.collision_sprites, self.shell_sprites],
                            pearl_surf=asset_dict['pearl'],
                            damage_sprites = self.damage_sprites)
                    # shell pointing right
                    case 10:
                        Shell(
                            orientation='right',
                            assets=asset_dict['shell'],
                            pos=pos,
                            group=[self.all_sprites, self.collision_sprites, self.shell_sprites],
                            pearl_surf=asset_dict['pearl'],
                            damage_sprites = self.damage_sprites)

                    # player in range?
                    # PALMS

                    # palms foreground -> block size attribute for movement
                    case 11:
                        Animated(asset_dict['palms']['small_fg'], pos, self.all_sprites)
                        Block(pos, (80, 10), self.collision_sprites)
                    case 12:
                        Animated(asset_dict['palms']['large_fg'], pos, self.all_sprites)
                        Block(pos, (80, 10), self.collision_sprites)
                    case 13:
                        Animated(asset_dict['palms']['left_fg'], pos, self.all_sprites)
                        Block(pos, (80, 10), self.collision_sprites)
                    case 14:
                        Animated(asset_dict['palms']['right_fg'], pos, self.all_sprites)
                        Block(pos + vector(50, 0), (80, 10), self.collision_sprites)
                    # palms background - no collision
                    case 15:
                        Animated(asset_dict['palms']['small_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
                    case 16:
                        Animated(asset_dict['palms']['large_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
                    case 17:
                        Animated(asset_dict['palms']['left_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
                    case 18:
                        Animated(asset_dict['palms']['right_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])

        for sprite in self.shell_sprites:
            sprite.player = self.player

    # method for "picking up" coins by player - also handle particle effect
    def get_coins(self):
        # make sure coins are removed when picked up by player
        collided_coins = pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
        # particle effect when coin was picked up
        for sprite in collided_coins:
            Particle(self.particle_surfs, sprite.rect.center, self.all_sprites)
            # use this if statement for increase gold amount or other functions
            if sprite.coin_type == 'gold':
                print('gold')

    # checks for mask collision
    def get_damage(self):
        collision_sprites = pygame.sprite.spritecollide(self.player, self.damage_sprites,
                                                        False, pygame.sprite.collide_mask)
        # if there is something inside the collection a collision occured
        if collision_sprites:
            self.player.damage()

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

            # cloud creation
            if event.type == self.cloud_timer:
                # pick random surface from clouds
                surf = choice(self.cloud_surfs)
                # scale clouds randomly
                surf = pygame.transform.scale2x(surf) if randint(0, 5) > 3 else surf
                x = self.level_limits['right'] + randint(100, 300)
                # create cloud on top of horizon by default
                # as these are behind the horizon an offset is needed
                y = self.horizon_y - randint(-50, 600)
                # create cloud object
                Cloud((x, y), surf, self.all_sprites, self.level_limits['left'])

    # cloud creation
    def startup_clouds(self):
        for i in range(40):
            # pick random surface from clouds
            surf = choice(self.cloud_surfs)
            # scale clouds randomly
            surf = pygame.transform.scale2x(surf) if randint(0, 5) > 3 else surf
            x = randint(self.level_limits['left'], self.level_limits['right'])
            # create cloud on top of horizon by default
            # as these are behind the horizon an offset is needed
            y = self.horizon_y - randint(-50, 600)
            # create cloud object
            Cloud((x, y), surf, self.all_sprites, self.level_limits['left'])

    def run(self, dt):
        # update part
        self.event_loop()
        self.all_sprites.update(dt)
        self.get_coins()
        self.get_damage()

        # drawing part
        self.display_surface.fill(SKY_COLOR)
        # self.all_sprites.draw(self.display_surface)
        # everything should be drawn related to player
        self.all_sprites.custom_draw(self.player)


# class for camera movement and grouping objects
class CameraGroup(pygame.sprite.Group):

    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        # vector influence the offset of all drawn objects (should be relative to player)
        self.offset = vector()

    # draw the horizon / sky
    def draw_horizon(self):
        # position - offset -> scaling with the player
        horizon_pos = self.horizon_y - self.offset.y

        # check if horizon is somewhere below window height
        # normal level
        if horizon_pos < WINDOW_HEIGHT:
            sea_rect = pygame.Rect(0, horizon_pos, WINDOW_WIDTH, WINDOW_HEIGHT - horizon_pos)
            pygame.draw.rect(self.display_surface, SEA_COLOR, sea_rect)
            # horizon line
            # 3 extra rectangles
            horizon_rect1 = pygame.Rect(0, horizon_pos - 10, WINDOW_WIDTH, 10)
            horizon_rect2 = pygame.Rect(0, horizon_pos - 16, WINDOW_WIDTH, 4)
            horizon_rect3 = pygame.Rect(0, horizon_pos - 20, WINDOW_WIDTH, 2)

            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)

            pygame.draw.line(self.display_surface, HORIZON_COLOR,
                             (0, horizon_pos), (WINDOW_WIDTH, horizon_pos),
                             3)

        # check if horizon is somewhere over window height
        # underwater level
        if horizon_pos < 0:
            self.display_surface.fill(SEA_COLOR)

    def custom_draw(self, player):
        # relative to player offset positioning - "camera" follows player movement
        self.offset.x = player.rect.centerx - WINDOW_WIDTH / 2
        self.offset.y = player.rect.centery - WINDOW_HEIGHT / 2

        # draw clouds in background of horizon first
        for sprite in self:
            if sprite.z == LEVEL_LAYERS['clouds']:
                offset_rect = sprite.rect.copy()
                offset_rect.center -= self.offset
                self.display_surface.blit(sprite.image, offset_rect)

        # draw horizon second
        self.draw_horizon()

        # draw all other elements that are not clouds
        for sprite in self:
            for layer in LEVEL_LAYERS.values():
                if sprite.z == layer and sprite.z != LEVEL_LAYERS['clouds']:
                    # create a copy of the object rect to use it for offset
                    offset_rect = sprite.rect.copy()
                    # use for offset
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)
