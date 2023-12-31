import pygame, sys
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_position
from pygame.image import load

from settings import *
from support import *

from menu import Menu
from timer import Timer

from random import choice, randint


class Editor:
    def __init__(self, land_tiles, switch):

        # main setup
        self.display_surface = pygame.display.get_surface()
        self.canvas_data = {}
        self.switch = switch

        # imports
        self.land_tiles = land_tiles
        self.import_tile()

        # clouds
        # create empty list of clouds
        self.current_clouds = []
        # import cloud images
        self.cloud_surfaces = import_folder('../graphics/clouds')
        # create a timer for drawing clouds
        self.cloud_timer = pygame.USEREVENT + 1
        # timer every 2 sec
        pygame.time.set_timer(self.cloud_timer, 2000)
        # create some clouds to have them already when game starts
        self.startup_clouds()

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

        # selection
        # selects tiles for editor out of collection in settings
        # starting from 2 because 1 is player
        self.selection_index = 2
        self.last_selected_cell = None

        # create instance of the menu
        self.menu = Menu()

        # objects
        # all objects (fg & bg) together
        self.canvas_objects = pygame.sprite.Group()
        # foreground objects
        self.foreground = pygame.sprite.Group()
        # background objects
        self.background = pygame.sprite.Group()
        # release object when not clicked anymore
        self.object_drag_active = False
        # timer object to prevent multiple placing objects when button is pressed
        self.object_timer = Timer(400)

        # Player
        # Position 0 to use player
        CanvasObject(
            pos=(200, WINDOW_HEIGHT / 2),
            frames=self.animations[0]['frames'],
            tile_id=0,
            origin=self.origin,
            group=[self.canvas_objects, self.foreground]
        )
        # SKY
        self.sky_handle = CanvasObject(
            pos=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2),
            frames=[self.sky_handle_surface],
            tile_id=1,
            origin=self.origin,
            group=[self.canvas_objects, self.background]
        )

    # SUPPORT

    # gets the current cell which was clicked
    def get_current_cell(self, obj = None):
        # calculate the distance between mouse click and origin using vectors
        distance_to_origin = vector(mouse_position()) - self.origin if not obj \
            else vector(obj.distance_to_origin) - self.origin
        # make sure cells around origin are not all 0,0 (int division would do that for negative values)
        if distance_to_origin.x > 0:
            # calculate cell position by dividing distance to origin by tile size and int it to get full numbers
            col = int(distance_to_origin.x / TILE_SIZE)
        else:
            col = int(distance_to_origin.x / TILE_SIZE) - 1

        if distance_to_origin.y > 0:
            row = int(distance_to_origin.y / TILE_SIZE)
        else:
            row = int(distance_to_origin.y / TILE_SIZE) - 1
        return col, row

    # checks the neighbors around a given cell (selection)
    def check_neighbors(self, cell_position):
        pass
        # create a local cluster - no need to check all tiles in the game later on - check only around selection
        cluster_size = 3
        # calculate all direct neighbors around the selected cell
        local_cluster = [
            (cell_position[0] + col - int(cluster_size / 2), cell_position[1] + row - int(cluster_size / 2))
            for col in range(cluster_size)
            for row in range(cluster_size)
        ]

        # draw neighbors
        # check all neighbors in cluster
        for cell in local_cluster:
            # check if the neighbors are already placed tiles
            if cell in self.canvas_data:
                # create a new empty list for terrain tiles
                self.canvas_data[cell].terrain_neighbors = []
                # everytime remove water on top from neighbors (deleting reasons)
                self.canvas_data[cell].water_on_top = False
                # check for all neighbors in the cluster clockwise
                for name, side in NEIGHBOR_DIRECTIONS.items():
                    neighbor_cell = (cell[0] + side[0], cell[1] + side[1])
                    # check if the neighbors are in data
                    # choose images depending on letter occurrence A,B,C ...

                    if neighbor_cell in self.canvas_data:
                        if self.canvas_data[neighbor_cell].has_terrain:
                            self.canvas_data[cell].terrain_neighbors.append(name)
                        # water top neighbor
                        if self.canvas_data[neighbor_cell].has_water and self.canvas_data[
                            cell].has_water and name == 'A':
                            self.canvas_data[cell].water_on_top = True

    # import tiles
    def import_tile(self):
        # import water
        self.water_bottom = load('../graphics/terrain/water/water_bottom.png').convert_alpha()
        # import sky
        self.sky_handle_surface = load('../graphics/cursors/handle.png').convert_alpha()

        # animation import
        # no sprites are used here because of performance reasons
        # create a dictionary holding the animation tiles rather than sprites
        self.animations = {}
        for key, value in EDITOR_DATA.items():
            if value['graphics']:
                graphics = import_folder(value['graphics'])
                # create entry in dictionary
                self.animations[key] = {
                    'frame index': 0,
                    'frames': graphics,
                    'length': len(graphics)
                }
        # preview tiles using dictionary comprehension for 'preview' type
        self.preview_surfaces = {key: load(value['preview']) for key, value in EDITOR_DATA.items() if value['preview']}

    # updates the frame for animation
    def animation_update(self, dt):
        for value in self.animations.values():
            # multiply with delta time to make it frame independent
            value['frame index'] += ANIMATION_SPEED * dt
            # as we only have 3 images in animation list we need to limit the value
            if value['frame index'] >= value['length']:
                # restart animation
                value['frame index'] = 0

    # returns hovered object
    def mouse_on_object(self):
        # check all sprites and if mouse is on any of those
        for sprite in self.canvas_objects:
            if sprite.rect.collidepoint(mouse_position()):
                return sprite

    def create_grid(self):
        # add objects to tiles
        for tile in self.canvas_data.values():
            tile.objects = []
        for obj in self.canvas_objects:
            current_cell = self.get_current_cell(obj)
            offset = vector(obj.distance_to_origin) - (vector(current_cell) * TILE_SIZE)

            if current_cell in self.canvas_data: # tile exists already so place it
                self.canvas_data[current_cell].add_id(obj.tile_id, offset)
            else: # no tile exists yet, create a new one
                self.canvas_data[current_cell] = CanvasTile(obj.tile_id, offset)


        # create an empty grid (actual data structure needed for the level)
        # all different layers which are used inside the level
        # ORDER IS IMPORTANT! -> key == coordinates , value == tile String
        layers = {
            'water': {},
            'bg palms': {},
            'terrain': {},
            'enemies': {},
            'coins': {},
            'fg objects': {},
        }

        # grid offset
        # canvas_data.keys are the positions -> sort them and get the lowest (first x value) item
        left = sorted(self.canvas_data.keys(), key = lambda tile: tile[0])[0][0]
        # get the same list with y values sorted from lowest to highest get the top most position (y value)
        top = sorted(self.canvas_data.keys(), key = lambda tile: tile[1])[0][1]

        # fill the grid
        for tile_pos, tile in self.canvas_data.items():
            row_adjusted = tile_pos[1] - top
            col_adjusted = tile_pos[0] - left
            # convert grid positions to actual x y coordinates for pixels
            x = col_adjusted * TILE_SIZE
            y = row_adjusted * TILE_SIZE

            # check for different tiles and add them to the grid
            if tile.has_water:
                layers['water'][(x, y)] = tile.get_water()

            if tile.has_terrain:
                # get the terrain graphic only if it exists in the collection else get the placeholder graphic
                layers['terrain'][(x, y)] = tile.get_terrain() if tile.get_terrain() in self.land_tiles else 'X'

            if tile.coin:
                layers['coins'][(x + TILE_SIZE // 2, y + TILE_SIZE // 2)] = tile.coin

            if tile.enemy:
                layers['enemies'][(x, y)] = tile.enemy

            if tile.objects:
                # collection of tuples (obj, offset)
                for obj, offset in tile.objects:
                    # check if background or foreground objects
                    # check using keys from objects - background has 'style' and 'palm_bg' nr 15-18
                    if obj in [key for key, value in EDITOR_DATA.items() if value['style'] == 'palm_bg']:
                        layers['bg palms'][(int(x + offset.x), int(y + offset.y))] = obj
                    else:  # it is a foreground object
                        layers['fg objects'][(int(x + offset.x), int(y + offset.y))] = obj

        return layers

    # INPUT
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                # if enter was pressed switch to game mode and call transition
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.switch(self.create_grid())
            self.pan_input(event)
            # call selection index key behavior
            self.selection_hotkeys(event)
            # check mouse clicks on menu buttons
            self.menu_click(event)
            # place dragging before canvas add to prevent drawing one tile when selecting object
            self.object_drag(event)
            # check mouse clicks for position
            self.canvas_add()
            # method to remove tiles
            self.canvas_remove()
            # create the clouds
            self.create_clouds(event)

    def pan_input(self, event):
        # middle mouse button was pressed or released
        # mouse_buttons() imported at the top returns a tuple of possible button events and [1] is middle
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
            self.pan_active = True
            # offset is distance between origin and mouse position as vector
            # this get movement from mouse when button is pressed without setting point to mouse position
            self.pan_offset = vector(mouse_position()) - self.origin
        if not mouse_buttons()[1]:
            self.pan_active = False

        # mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            # move y position when ctrl is pressed and mousewheel up or down is pressed
            if pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.origin.y -= event.y * 50
                # move the x position otherwise
            else:
                self.origin.x -= event.y * 50

        # panning update
        if self.pan_active:
            # convert self.origin as vector to access x and y position
            self.origin = vector(mouse_position()) - self.pan_offset

            # update every sprite to move it with display movement
            for sprite in self.canvas_objects:
                sprite.pan_position(self.origin)

    def selection_hotkeys(self, event):
        # check if button was pressed
        if event.type == pygame.KEYDOWN:
            # if right was pressed increase index to next tile
            if event.key == pygame.K_RIGHT:
                self.selection_index += 1
            # if left was pressed decrease index to previous tile
            if event.key == pygame.K_LEFT:
                self.selection_index -= 1
            # limit selection_index to 2 till 18
            if self.selection_index < 2:
                self.selection_index = 2
            if self.selection_index > 18:
                self.selection_index = 18

    def menu_click(self, event):
        # check if a mouse button was clicked and if it was inside a button on screen
        if event.type == pygame.MOUSEBUTTONDOWN and self.menu.rect.collidepoint(mouse_position()):
            self.selection_index = self.menu.click(mouse_position(), mouse_buttons())

    # triggered when canvas was clicked
    # starting point
    def canvas_add(self):
        # if it was left-clicked and not at the menu
        if mouse_buttons()[0] and not self.menu.rect.collidepoint(mouse_position()) and not self.object_drag_active:
            current_cell = self.get_current_cell()
            if EDITOR_DATA[self.selection_index]['type'] == 'tile':

                # only run this when a different cell than the last one is selected
                if current_cell != self.last_selected_cell:

                    # check if the current clicked cell is already inside the collection of cells
                    if current_cell in self.canvas_data:
                        # there is already a Canvas Tile, so we could append this one to it with its id
                        self.canvas_data[current_cell].add_id(self.selection_index)
                    else:
                        # there is no Canvas Tile, create a new one with the given cell
                        self.canvas_data[current_cell] = CanvasTile(self.selection_index)
                    # check all neighbors of the current cell to adjust the image properly
                    self.check_neighbors(current_cell)
                    # store actual selected cell to compare it
                    self.last_selected_cell = current_cell
            else:  # object
                if not self.object_timer.active:
                    # divide fg and bg objects into groups
                    groups = [self.canvas_objects, self.background] if (
                            EDITOR_DATA[self.selection_index]['style'] == 'palm_bg') \
                        else [self.canvas_objects, self.foreground]
                    CanvasObject(
                        pos=mouse_position(),
                        frames=self.animations[self.selection_index]['frames'],
                        tile_id=self.selection_index,
                        origin=self.origin,
                        group=groups
                    )
                    self.object_timer.activate()

    # delete tiles - objects
    def canvas_remove(self):
        # only delete tiles when right click and not at menu
        if mouse_buttons()[2] and not self.menu.rect.collidepoint(mouse_position()):

            # delete object
            selected_object = self.mouse_on_object()
            if selected_object:
                # restrict deleting objects to palm tress, exclude player and sky
                if EDITOR_DATA[selected_object.tile_id]['style'] not in ('player', 'sky'):
                    selected_object.kill()

            # delete tiles
            if self.canvas_data:
                current_cell = self.get_current_cell()
                if current_cell in self.canvas_data:
                    self.canvas_data[current_cell].remove_id(self.selection_index)

                    if self.canvas_data[current_cell].is_empty:
                        del self.canvas_data[current_cell]
                    self.check_neighbors(current_cell)

    def object_drag(self, event):
        # check if left-clicking somewhere on the editor
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            # check all objects if clicked
            for sprite in self.canvas_objects:
                # check click with collision
                if sprite.rect.collidepoint(event.pos):
                    sprite.start_drag()
                    self.object_drag_active = True
        # it was something selected and mouse button is released
        if event.type == pygame.MOUSEBUTTONUP and self.object_drag_active:
            for sprite in self.canvas_objects:
                if sprite.selected:
                    sprite.drag_end(self.origin)
                    self.object_drag_active = False

    # DRAWING

    # draw an infinite grid for orientation and tile placing reasons over the screen
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

    # draw the level
    def draw_level(self):
        self.background.draw(self.display_surface)
        for cell_pos, tile in self.canvas_data.items():
            # convert cell pos to a pixel value
            pos = self.origin + vector(cell_pos) * TILE_SIZE

            # terrain
            if tile.has_terrain:
                # convert neighbors to a string using join()
                terrain_string = ''.join(tile.terrain_neighbors)
                # safeguard if a graphic is missing use placeholder / joker which fits everywhere
                terrain_style = terrain_string if terrain_string in self.land_tiles else 'X'
                self.display_surface.blit(self.land_tiles[terrain_style], pos)

            # water
            if tile.has_water:
                if tile.water_on_top:
                    self.display_surface.blit(self.water_bottom, pos)
                else:
                    # separate the frames ( index is always 3 )
                    frames = self.animations[3]['frames']
                    # pick one item from the list
                    index = int(self.animations[3]['frame index'])
                    # create surface from index
                    surface = frames[index]
                    self.display_surface.blit(surface, pos)

            # coins
            if tile.coin:
                frames = self.animations[tile.coin]['frames']
                index = int(self.animations[tile.coin]['frame index'])
                surface = frames[index]
                # place the coins in the middle of the cell not at the top left
                rect = surface.get_rect(center=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))

                self.display_surface.blit(surface, rect)

            # enemies
            if tile.enemy:
                frames = self.animations[tile.enemy]['frames']
                index = int(self.animations[tile.enemy]['frame index'])
                surface = frames[index]
                # place the enemy in the middle and bottom of the cell
                rect = surface.get_rect(midbottom=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE))

                self.display_surface.blit(surface, rect)
        # draw objects (player, trees at the canvas
        self.foreground.draw(self.display_surface)

    # show a preview of the selected tile or object
    def preview(self):
        # the object which is hovered over
        selected_object = self.mouse_on_object()
        # do not show preview when hovering over the menu
        if not self.menu.rect.collidepoint(mouse_position()):
            # draws line around objects when hovered over them
            if selected_object:
                # create a rectangle copy of selected object, inflate it to draw lines around it
                rect = selected_object.rect.inflate(10, 10)
                # color of lines
                color = 'black'
                # width of lines
                width = 3
                # length of lines
                size = 15
                # closed parameter ( should lines be closed )
                # points 3* = start, middle, end point of lines to be drawing
                # top left
                pygame.draw.lines(self.display_surface, color, False,
                                  ((rect.left, rect.top + size), rect.topleft,
                                   (rect.left + size, rect.top)), width)
                # top right
                pygame.draw.lines(self.display_surface, color, False,
                                  ((rect.right, rect.top + size), rect.topright,
                                   (rect.right - size, rect.top)), width)
                # bottom left
                pygame.draw.lines(self.display_surface, color, False,
                                  ((rect.left, rect.bottom - size), rect.bottomleft,
                                   (rect.left + size, rect.bottom)), width)
                # bottom right
                pygame.draw.lines(self.display_surface, color, False,
                                  ((rect.right, rect.bottom - size), rect.bottomright,
                                   (rect.right - size, rect.bottom)), width)
            else:
                # create a dictionary of items / copy 'type'
                type_dict = {key: value['type'] for key, value, in EDITOR_DATA.items()}
                # gets a surface using load method
                surface = self.preview_surfaces[self.selection_index].copy()
                # set transparency for preview
                surface.set_alpha(200)

                # split using 'type'
                # tile
                if type_dict[self.selection_index] == 'tile':
                    # store current cell
                    current_cell = self.get_current_cell()
                    # create rectangle
                    rect = surface.get_rect(topleft=self.origin + vector(current_cell) * TILE_SIZE)
                # object
                else:
                    rect = surface.get_rect(center=mouse_position())
                self.display_surface.blit(surface, rect)

    # SKY

    def display_sky(self, dt):
        self.display_surface.fill(SKY_COLOR)
        # position of the horizon point in the middle of the screen
        # sky handle button following
        y_pos = self.sky_handle.rect.centery

        # horizon lines
        if y_pos > 0:
            horizon_rect1 = pygame.Rect(0, y_pos - 10, WINDOW_WIDTH, 10)
            horizon_rect2 = pygame.Rect(0, y_pos - 16, WINDOW_WIDTH, 4)
            horizon_rect3 = pygame.Rect(0, y_pos - 20, WINDOW_WIDTH, 2)

            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)

            # cloud drawing
            self.display_cloud(dt, y_pos)

        # fill the display with water when no sky is visible
        if 0 < y_pos < WINDOW_HEIGHT:
            # sea - rectangle placed below the horizon line
            sea_rect = pygame.Rect(0, y_pos, WINDOW_WIDTH, WINDOW_HEIGHT)
            pygame.draw.rect(self.display_surface, SEA_COLOR, sea_rect)
            pygame.draw.line(self.display_surface, HORIZON_COLOR, (0, y_pos), (WINDOW_WIDTH, y_pos), 3)
        if y_pos < 0:
            self.display_surface.fill(SEA_COLOR)

    # drawing the clouds
    def display_cloud(self, dt, y_pos):
        # clouds currently existing
        for cloud in self.current_clouds:  # [{surf, pos, speed}]
            cloud['pos'][0] -= cloud['speed'] * dt
            x = cloud['pos'][0]
            # clouds should move up and down following the horizon
            y = y_pos - cloud['pos'][1]
            self.display_surface.blit(cloud['surface'], (x, y))

    def create_clouds(self, event):
        # only create when timer runs
        if event.type == self.cloud_timer:
            # choose one of the existing clouds with choice by random
            surface = choice(self.cloud_surfaces)
            # scale the clouds by 2 to create difference, but only at random occurrences
            surface = pygame.transform.scale2x(surface) if randint(0, 4) < 2 else surface
            # a list of x,y coords for position of clouds - random
            pos = [WINDOW_WIDTH + randint(50, 100), randint(0, WINDOW_HEIGHT)]
            # random speed of cloud movement
            speed = randint(20, 50)
            # create a random list of clouds
            self.current_clouds.append({'surface': surface, 'pos': pos, 'speed': speed})

            # limit amount of clouds created, to not crash performance when game runs longer
            self.current_clouds = [cloud for cloud in self.current_clouds if cloud['pos'][0] > -400]

    # initiate clouds directly so there no need to wait for them to appear
    def startup_clouds(self):
        # create 20 clouds
        for i in range(20):
            surface = pygame.transform.scale2x(
                choice(self.cloud_surfaces)) if randint(0, 4) < 2 else choice(self.cloud_surfaces)
            pos = [randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)]
            speed = randint(20, 50)
            self.current_clouds.append({'surface': surface, 'pos': pos, 'speed': speed})

    # UPDATE
    def run(self, dt):
        self.event_loop()

        # updating
        self.animation_update(dt)
        self.canvas_objects.update(dt)
        self.object_timer.update()

        # drawing
        self.display_surface.fill('grey')
        # display sky first as this is in the background
        self.display_sky(dt)
        # draw the level
        self.draw_level()
        # draw lines for grid
        self.draw_tile_lines()
        # draw origin position
        # pygame.draw.circle(self.display_surface, 'red', self.origin, 10)
        # draw preview of selected object
        self.preview()
        # draw menu
        self.menu.display(self.selection_index)


# class / object to store all information stored inside tiles
class CanvasTile:
    def __init__(self, tile_id, offset = vector()):

        # TERRAIN
        self.has_terrain = False
        # what are the neighbors of the tile
        self.terrain_neighbors = []

        # WATER
        self.has_water = False
        # only top water tile of 2 water tiles need animation
        self.water_on_top = False

        # COIN
        # each tile can only have one coin
        self.coin = None

        # ENEMY
        # each tile can only have on enemy
        self.enemy = None

        # OBJECTS
        self.objects = []

        self.add_id(tile_id, offset = offset)
        self.is_empty = False

    def add_id(self, tile_id, offset = vector()):
        # what dictionary styles are there?
        options = {key: value['style'] for key, value in EDITOR_DATA.items()}
        # check tile id with options - switch - if tile id == 2 ( terrain ) set boolean true ...
        match options[tile_id]:
            case 'terrain':
                self.has_terrain = True
            case 'water':
                self.has_water = True
            # coin and enemy will get overwritten as there could only be one
            case 'coin':
                self.coin = tile_id
            case 'enemy':
                self.enemy = tile_id
            # if none of this cases are true do this
            case _: # append objects to existing collection
                # check if they already exist so no two objects are at the exact same position
                if (tile_id, offset) not in self.objects:
                    self.objects.append((tile_id, offset))

    def remove_id(self, tile_id):
        # what dictionary styles are there?
        options = {key: value['style'] for key, value in EDITOR_DATA.items()}
        # check tile id with options - switch - if tile id == 2 ( terrain ) set boolean true ...
        match options[tile_id]:
            case 'terrain':
                self.has_terrain = False
            case 'water':
                self.has_water = False
            # coin and enemy will get overwritten as there could only be one
            case 'coin':
                self.coin = None
            case 'enemy':
                self.enemy = None
        # check if the tile is empty / if so remove complete tile
        self.check_content()

    def check_content(self):
        if not self.has_terrain and not self.has_water and not self.coin and not self.enemy:
            self.is_empty = True

    def get_water(self):
        # return the correct water tile depending on if there is already one
        return 'bottom' if self.water_on_top else 'top'

    def get_terrain(self):
        return ''.join(self.terrain_neighbors)

# Objects - Sprite that will be animated - trees, sky, player
class CanvasObject(pygame.sprite.Sprite):
    # frames for animation
    def __init__(self, pos, frames, tile_id, origin, group):
        super().__init__(group)
        self.tile_id = tile_id

        # animation
        self.frames = frames
        self.frame_index = 0

        # pick one of the surfaces out of the list frames
        self.image = self.frames[self.frame_index]
        # center of object should be at mouse position
        self.rect = self.image.get_rect(center=pos)

        # movement
        self.distance_to_origin = vector(self.rect.topleft) - origin
        # move objects around
        self.selected = False
        # distance between top left and point that player clicked on
        self.mouse_offset = vector()

    def start_drag(self):
        self.selected = True
        self.mouse_offset = vector(mouse_position()) - vector(self.rect.topleft)

    def drag(self):
        if self.selected:
            self.rect.topleft = mouse_position() - self.mouse_offset

    def drag_end(self, origin):
        self.selected = False
        # prevent porting player when padding display
        self.distance_to_origin = vector(self.rect.topleft) - origin

    # animation
    def animate(self, dt):
        # animate by increasing the index of frames
        # multiply with delta time to avoid performance issues
        self.frame_index += ANIMATION_SPEED * dt
        # limit index of length of list to avoid len error
        self.frame_index = 0 if self.frame_index >= len(self.frames) else self.frame_index
        # cast index to int due to floating point dt
        self.image = self.frames[int(self.frame_index)]
        # if the surface changes too much not move around
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    # move the objects with display when middle mouse is pressed like with origin point
    def pan_position(self, origin):
        self.rect.topleft = origin + self.distance_to_origin

    # update method to animate
    def update(self, dt):
        self.animate(dt)
        self.drag()
