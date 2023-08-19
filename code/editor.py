import pygame, sys
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_position
from settings import *

from menu import Menu


class Editor:
    def __init__(self, land_tiles):

        # main setup
        self.display_surface = pygame.display.get_surface()
        self.canvas_data = {}

        # imports
        self.land_tiles = land_tiles

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

    # SUPPORT

    # gets the current cell which was clicked
    def get_current_cell(self):
        # calculate the distance between mouse click and origin using vectors
        distance_to_origin = vector(mouse_position()) - self.origin
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
                self.canvas_data[cell].terrain_neighbors = []
                # do this for all neighbors in the cluster clockwise
                for name, side in NEIGHBOR_DIRECTIONS.items():
                    neighbor_cell = (cell[0] + side[0], cell[1] + side[1])
                    # check if the neighbors are in data
                    # choose images depending on letter occurrence A,B,C ...
                    if neighbor_cell in self.canvas_data:
                        if self.canvas_data[neighbor_cell].has_terrain:
                            self.canvas_data[cell].terrain_neighbors.append(name)

    # INPUT
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            self.pan_input(event)
            # call selection index key behavior
            self.selection_hotkeys(event)
            # check mouse clicks on menu buttons
            self.menu_click(event)
            # check mouse clicks for position
            self.canvas_add()

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
        if mouse_buttons()[0] and not self.menu.rect.collidepoint(mouse_position()):
            current_cell = self.get_current_cell()

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

    def draw_level(self):
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
                test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill('blue')
                self.display_surface.blit(test_surf, pos)

            # coins
            if tile.coin:
                test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill('yellow')
                self.display_surface.blit(test_surf, pos)

            # enemies
            if tile.enemy:
                test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                test_surf.fill('red')
                self.display_surface.blit(test_surf, pos)

    # UPDATE
    def run(self, dt):

        self.event_loop()

        # drawing
        self.display_surface.fill('grey')
        # draw the level
        self.draw_level()
        # draw lines for grid
        self.draw_tile_lines()
        # draw origin position
        pygame.draw.circle(self.display_surface, 'red', self.origin, 10)
        # draw menu
        self.menu.display(self.selection_index)


# class / object to store all information stored inside tiles
class CanvasTile:
    def __init__(self, tile_id):

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

        self.add_id(tile_id)

    def add_id(self, tile_id):
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
