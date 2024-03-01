import os
import pygame
import csv

pygame.init()
tile_size = 32
width, height = 1000, 700
chunk_size = 12
chunk_tile_size = chunk_size * tile_size
tile_raise_amount = 60

chunk_width = chunk_tile_size 
chunk_height = chunk_tile_size//2 + tile_size//2

def load_assets(path: str) -> dict:
    assets = {}
    file_names = os.listdir(path)

    for file_name in file_names:
        asset_info = file_name.split("_")[1]  # Ex: "asset_000.png"
        period_index = asset_info.index(".")
        asset_number = int(asset_info[:period_index])
        asset_image = pygame.image.load(path + file_name).convert_alpha()
        assets[asset_number] = asset_image
    return assets

def chunk_to_iso(chunk_pos) -> tuple:
    grid_x, grid_y = chunk_pos
    iso_x = (grid_x - grid_y) * chunk_width // 2
    iso_y = (grid_x + grid_y) * chunk_width // 4
    return iso_x, iso_y

def iso_to_grid(iso_pos, grid_size=tile_size) -> tuple: # outdated (needs updated)
    iso_x, iso_y = iso_pos
    iso_x -= width // 2
    iso_x += tile_size//2
    iso_y -= height // 4

    grid_x = (2 * iso_y + iso_x) // grid_size
    grid_y = (2 * iso_y - iso_x) // grid_size

    return int(grid_x), int(grid_y)

def grid_to_iso(grid_pos, grid_size=tile_size) -> tuple:
    grid_x, grid_y = grid_pos
    iso_x = (grid_x - grid_y) * grid_size // 2
    iso_y = (grid_x + grid_y) * grid_size // 4
    return iso_x, iso_y

def create_chunk_render_map(screen_chunk_x=4, screen_chunk_y=4) -> list:
    chunk_grid_offsets = []
    for row in range(-screen_chunk_y, screen_chunk_y):
        for col in range(-screen_chunk_x, screen_chunk_x):
            chunk_grid_offsets.append((col, row))
    
    return chunk_grid_offsets

chunk_render_map: list = create_chunk_render_map()

def filter_visible_chunks(chunks: dict, grid_pos: tuple) -> list:
    grid_x, grid_y = grid_pos
    visible_chunks = []
    for col, row in chunk_render_map:
        chunk: Chunk = chunks.get((grid_x+col, grid_y+row))
        if chunk:
            visible_chunks.append(chunk)
    return visible_chunks

class Tile:
    def __init__(self, tile_id, position) -> None:
        super().__init__()
        self.tile_id = tile_id
        self.position = pygame.math.Vector2(position)
        self.flags = {}

    def draw(self, screen: pygame.surface.Surface, chunk_offset: tuple, assets: list) -> tuple:
        offset_x, offset_y = chunk_offset
        iso_x, iso_y = grid_to_iso(self.position, grid_size=tile_size)
        iso_x -= offset_x
        iso_y -= offset_y
        iso_x -= tile_size//2
        iso_x += chunk_width // 2
        image = assets[self.tile_id]

        """
        if self.flags.get('mouse_over_tile'):
            iso_pos.y += tile_raise_amount
            p1 = (iso_pos.x, iso_pos.y) + pygame.math.Vector2(tile_size/2, tile_size/2)
            p2 = (iso_pos.x+tile_size/2, iso_pos.y+tile_size/4) + pygame.math.Vector2(tile_size/2, tile_size/2)
            p3 = (iso_pos.x, iso_pos.y+tile_size/2) + pygame.math.Vector2(tile_size/2, tile_size/2)
            p4 = (iso_pos.x-tile_size/2, iso_pos.y+tile_size/4) + pygame.math.Vector2(tile_size/2, tile_size/2)
            pygame.draw.polygon(screen, (255,255,0), [p1,p2,p3,p4], 1)
        """
        return (image, (iso_x, iso_y))

class Chunk:
    def __init__(self, position) -> None:
        self.position = pygame.math.Vector2(position)
        self.tiles = {}
        self.flags = {}
        self.chunk_surface = pygame.Surface((chunk_width, chunk_height), flags=pygame.SRCALPHA)
        self.chunk_surface.fill((0,0,0,0))

    def update_chunk_surface(self, assets: list) -> None:
        tile: Tile
        tiles = []
        chunk_iso_pos = chunk_to_iso(self.position)
        for tile in self.tiles.values():
            tiles.append(tile.draw(self.chunk_surface, chunk_iso_pos, assets))
        self.chunk_surface.fblits(tiles)

    def draw_chunk(self, camera_offset, screen, debug=False) -> tuple:
        iso_x, iso_y = chunk_to_iso(self.position)
        iso_pos = (iso_x, iso_y)

        return (self.chunk_surface, iso_pos)

class Floor:
    def __init__(self, floor_path, map_path) -> None:
        self.camera_offset = pygame.math.Vector2(0, 0)
        self.floor_path = floor_path
        self.map_path = map_path
        self.chunks = {}

        self.assets = load_assets(self.floor_path)
        self.load_floor_map()

    def get_visible_chunks(self) -> list:
        center_x, center_y = width//2, height//2
        iso_center_pos = pygame.math.Vector2((center_x, center_y)) - self.camera_offset + pygame.math.Vector2(0, chunk_tile_size//8)
        iso_center_pos.x -= tile_size // 2
        iso_center_pos.y -= tile_size // 4
        chunk_x, chunk_y = iso_to_grid(iso_center_pos, grid_size=chunk_tile_size)
        return filter_visible_chunks(self.chunks, (chunk_x, chunk_y))

    def scroll(self, direction: pygame.math.Vector2, delta_time) -> None: # for scroll speed and camera offset
        scroll_speed = 2000
        self.camera_offset -= direction * scroll_speed * delta_time

    def clear_tile_flags(self) -> None: # clears flags. Some are 'mouse_over_chunk' and so on
        for chunk in self.chunks.values():
            chunk.flags.clear()
            for tile in chunk.tiles.values():
                tile.flags['mouse_over_tile'] = False

    def render(self, screen: pygame.surface.Surface, mouse_pos: pygame.math.Vector2, debug=False) -> None:
        visible_chunks = self.get_visible_chunks()
        chunk: Chunk

        chunk_data = []
        for chunk in visible_chunks:
            grid_pos = chunk.position
            iso_x, iso_y = chunk_to_iso(grid_pos)
            iso_x += self.camera_offset.x
            iso_y += self.camera_offset.y
            iso_x += width // 2
            iso_x -= chunk_width//2
            iso_y += height // 4
            chunk_surface = chunk.chunk_surface
            chunk_data.append((chunk_surface, (iso_x, iso_y)))
        screen.fblits(chunk_data)

    def update_chunk_surfaces(self) -> None:
        chunk: Chunk
        for chunk in self.chunks.values():
            chunk.update_chunk_surface(self.assets) # blits tiles to chunks

    def load_floor_map(self) -> None: # loads all csv data into a "Tile" object
        # all tile objects stored in thier respective chunks.
        with open(self.map_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for row_index, row in enumerate(reader):
                for col_index, tile_id_str in enumerate(row):
                    tile_id = int(tile_id_str)
                    if tile_id < 0:
                        continue
                    grid_pos = (col_index, row_index)
                    tile = Tile(tile_id, grid_pos)

                    chunk_x, chunk_y = grid_pos[0] // chunk_size, grid_pos[1] // chunk_size
                    chunk_pos = (chunk_x, chunk_y)
                    if chunk_pos not in self.chunks:
                        self.chunks[chunk_pos] = Chunk(chunk_pos)

                    self.chunks[chunk_pos].tiles[grid_pos] = tile
    
class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((width, height))
        self.running = True
        self.clock = pygame.time.Clock()
        self.delta_time = 0
        self.current_floor = None
        self.maps = ['LARGE.csv']
        
        self.key_time_accumulator = 0
        self.floor_index = 0
        self.debug = False

    def start_game(self): # loads the floors, and updates all chunks
        floor1 = Floor("Assets/Tiles/", "Floors/Floor1/LARGE.csv")
        self.current_floor = floor1
        self.update_chunk_surfaces()

    def render(self, mouse_pos, debug=False): # blits chunk surfaces to screen
        self.current_floor.render(self.screen, mouse_pos, debug=debug)

    def update_chunk_surfaces(self): # blits tiles to chunk surfaces
        self.current_floor.update_chunk_surfaces()

    def run(self):
        self.start_game()
        while self.running:
            self.delta_time = self.clock.tick(1000) / 1000
            mouse_pos = pygame.mouse.get_pos()

            keys = pygame.key.get_pressed()
            if keys:
                self.key_time_accumulator += self.delta_time
                if self.key_time_accumulator < 0.1:
                    continue
                direction = pygame.math.Vector2(0, 0)
                if keys[pygame.K_UP]:
                    direction += pygame.math.Vector2(0, -1)
                if keys[pygame.K_DOWN]:
                    direction += pygame.math.Vector2(0, 1)
                if keys[pygame.K_RIGHT]:
                    direction += pygame.math.Vector2(1, 0)
                if keys[pygame.K_LEFT]:
                    direction += pygame.math.Vector2(-1, 0)
                if keys[pygame.K_p]:
                    self.floor_index += 1
                    if self.floor_index > (len(self.maps)-1):
                        self.floor_index = 0
                    floor = Floor("Assets/Tiles/", f"Floors/Floor1/{self.maps[self.floor_index]}")
                    self.current_floor = floor
                    self.update_chunk_surfaces()
                if keys[pygame.K_o]:
                    self.floor_index -= 1
                    if self.floor_index < 0:
                        self.floor_index = len(self.maps)-1
                    floor = Floor("Assets/Tiles/", f"Floors/Floor1/{self.maps[self.floor_index]}")
                    self.current_floor = floor
                    self.update_chunk_surfaces()
                if keys[pygame.K_h]:
                    self.debug = not self.debug

                self.current_floor.scroll(direction, self.delta_time)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

            self.screen.fill((0, 0, 0))
            #self.current_floor.render_mouse_hover(mouse_pos)
            total_tiles = len(self.current_floor.chunks)*chunk_size*chunk_size
            self.render(mouse_pos, self.debug)
            pygame.display.update()
            pygame.display.set_caption(f"FPS: {int(self.clock.get_fps())} | Total Tiles: {total_tiles} ")

game = Game()
game.run()
pygame.quit()
