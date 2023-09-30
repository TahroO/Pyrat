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
        self.coin_sprites = pygame.sprite.Group()
        self.damage_sprites = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group()

        # when level is created
        self.build_level(grid, asset_dict)

        # additional stuff - support variables
        self.particle_surfs = asset_dict['particle']

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
                        Animated(asset_dict['water top'], pos, self.all_sprites)
                    else:
                        # create plain water sprite
                        Generic(pos, asset_dict['water bottom'], self.all_sprites)
                # python switch
                match data:
                    # PLAYER

                    # player object
                    case 0: self.player = Player(pos, self.all_sprites, self.collision_sprites)

                    # COINS

                    # gold
                    case 4: Coin('gold', asset_dict['gold'], pos,
                                 [self.all_sprites, self.coin_sprites])
                    # silver
                    case 5: Coin('silver', asset_dict['silver'], pos,
                                 [self.all_sprites, self.coin_sprites])
                    # diamond
                    case 6: Coin('diamond', asset_dict['diamond'], pos,
                                 [self.all_sprites, self.coin_sprites])

                    # ENEMIES

                    # spikes
                    case 7: Spikes(asset_dict['spikes'], pos, [self.all_sprites, self.damage_sprites])
                    # tooth
                    case 8: Tooth(asset_dict['tooth'], pos, [self.all_sprites, self.damage_sprites])
                    # shell pointing left
                    case 9: Shell('left', asset_dict['shell'], pos,
                                  [self.all_sprites, self.collision_sprites])
                    # shell pointing right
                    case 10: Shell('right', asset_dict['shell'], pos,
                                   [self.all_sprites, self.collision_sprites])

                    # PALMS

                    # palms foreground
                    case 11:
                        Animated(asset_dict['palms']['small_fg'], pos, self.all_sprites)
                        Block(pos, (80, 50), self.collision_sprites)
                    case 12:
                        Animated(asset_dict['palms']['large_fg'], pos, self.all_sprites)
                        Block(pos, (80, 50), self.collision_sprites)
                    case 13:
                        Animated(asset_dict['palms']['left_fg'], pos, self.all_sprites)
                        Block(pos, (80, 50), self.collision_sprites)
                    case 14:
                        Animated(asset_dict['palms']['right_fg'], pos, self.all_sprites)
                        Block(pos + vector(50, 0), (80, 50), self.collision_sprites)
                    # palms background - no collision
                    case 15: Animated(asset_dict['palms']['small_bg'], pos, self.all_sprites)
                    case 16: Animated(asset_dict['palms']['large_bg'], pos, self.all_sprites)
                    case 17: Animated(asset_dict['palms']['left_bg'], pos, self.all_sprites)
                    case 18: Animated(asset_dict['palms']['right_bg'], pos, self.all_sprites)

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
        # update part
        self.event_loop()
        self.all_sprites.update(dt)
        self.get_coins()

        # drawing part
        self.display_surface.fill(SKY_COLOR)
        self.all_sprites.draw(self.display_surface)
        pygame.draw.rect(self.display_surface, 'yellow', self.player.hitbox)