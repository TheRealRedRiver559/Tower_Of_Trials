# testing
import numpy as np
import pygame
import os
import math

screen_width = 800
screen_height = 800

tile_size = 32
chunk_size = 12
chunk_tile_size = tile_size*chunk_size
chunk_height = chunk_tile_size//2 - tile_size//2
position = tuple[int, int]

def convert_csv_numpy(csv_file: str, delimiter=',', dtype=int) -> np.ndarray:
    return np.genfromtxt(csv_file, delimiter=delimiter, dtype=dtype)

def save_map(map_data: np.ndarray, np_file: str) -> None:
    np.save(np_file, map_data)

def load_map(np_map_path: str) -> np.ndarray:
    return np.load(np_map_path) 

def get_circle_mask(map_data: np.ndarray, center_x: int, center_y: int, radius: int, thickness: int = 1) -> np.ndarray:
    Y, X = np.ogrid[:map_data.shape[0], :map_data.shape[1]]
    dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    mask = np.logical_and(dist_from_center >= radius - thickness, dist_from_center <= radius + thickness)
    return mask


def convert_csv_numpy(csv_file: str, delimiter=',', dtype=int) -> np.ndarray:
    return np.genfromtxt(csv_file, delimiter=delimiter, dtype=dtype)
def save_map(map_data: np.ndarray, np_file: str) -> None:
    np.save(np_file, map_data)
def load_map(np_map_path: str) -> np.ndarray:
    return np.load(np_map_path)  
def create_chunk_render_map(screen_chunk_x=5, screen_chunk_y=5) -> list:
    chunk_grid_offsets = []
    for row in range(-screen_chunk_y, screen_chunk_y+1):
        for col in range(-screen_chunk_x, screen_chunk_x+1):
            chunk_grid_offsets.append((col, row))
    
    return chunk_grid_offsets

def chunk_to_iso(chunk_pos: position) -> position:
    grid_x, grid_y = chunk_pos
    iso_x = (grid_x - grid_y) * chunk_tile_size // 2 
    iso_y = (grid_x + grid_y) * chunk_tile_size // 4
    iso_x += screen_width // 2
    iso_x -= chunk_tile_size // 2
    iso_y += screen_height // 4

    iso_x -= tile_size
    iso_y -= tile_size
    return iso_x, iso_y
    
def iso_to_grid(iso_pos, grid_size=tile_size) -> tuple: # outdated (needs updated)
    iso_x, iso_y = iso_pos
    iso_x -= screen_width // 2
    iso_x += tile_size//2
    iso_y -= screen_height // 4

    grid_x = (2 * iso_y + iso_x) // grid_size
    grid_y = (2 * iso_y - iso_x) // grid_size

    return int(grid_x), int(grid_y)
def load_assets(asset_path: str) -> dict[int, pygame.Surface]:
    assets = {}
    file_names = os.listdir(asset_path)

    for file_name in file_names:
        asset_info = file_name.split("_")[1]  # Ex: "asset_000.png"
        period_index = asset_info.index(".")
        asset_number = int(asset_info[:period_index])
        asset_image = pygame.image.load(asset_path + file_name).convert_alpha()
        assets[asset_number] = asset_image
    return assets

class Chunk:
    def __init__(self, chunk_pos: position, tiles=None) -> None:
        self.position = chunk_pos
        self.tiles = tiles or {}
        self.flags = {}
        self.iso_pos = chunk_to_iso(self.position)
        self.chunk_surface = pygame.Surface((chunk_tile_size+tile_size*2, chunk_height+tile_size+tile_size*2), flags=pygame.SRCALPHA)
        self.chunk_surface.fill((0,0,0,0))

    def update_chunk_surface(self, assets: list[pygame.Surface]) -> None:
        self.chunk_surface.fill((0,0,0,0))
        tile: Tile
        tiles = []
        for tile in self.tiles.values():
            tiles.append(tile.draw(assets))
        self.chunk_surface.fblits(tiles)

    def draw_chunk(self, camera_offset: pygame.Vector2, screen: pygame.Surface, debug=False) -> tuple[pygame.Surface, position]:
        iso_x, iso_y = self.iso_pos
        iso_pos = (iso_x+camera_offset.x, iso_y+camera_offset.y)
        return (self.chunk_surface, iso_pos)
    
class Tile:
    def __init__(self, tile_position: position, tile_id: int) -> None:
        self.tile_position = tile_position
        self.tile_id = tile_id
        self.iso_pos = None
        self.flags = {}

    def draw(self, assets: dict[int, pygame.Surface]) -> tuple[pygame.Surface, position]:
        if self.iso_pos is None:
            grid_x, grid_y = self.tile_position
            iso_x = (grid_x - grid_y) * tile_size // 2 - tile_size//2 + chunk_tile_size // 2
            iso_y = (grid_x + grid_y) * tile_size // 4
            iso_x += tile_size
            iso_y += tile_size
            self.iso_pos = (iso_x, iso_y)

        iso_x, iso_y = self.iso_pos
        if self.flags.get('mouse_over') or self.flags.get('raised'):
            iso_y -= 20
        image = assets[self.tile_id]
        return (image, (iso_x, iso_y))

class Floor:
    def __init__(self, npy_map_path: str, asset_path: str) -> None:
        self.camera_offset = pygame.Vector2(0,0)
        self.npy_map_path = npy_map_path
        self.asset_path = asset_path
        self.assets = load_assets(asset_path)
        self.chunk_render_map = create_chunk_render_map()
        self.chunks = {}
        self.pooled_chunks = [Chunk((0,0)) for _ in range(len(self.chunk_render_map))]
        self.map_data = load_map(npy_map_path)
        self.map_dimensions = self.map_data.shape
        self.prev_camera_chunk = self.get_center_screen_chunk()
        self.current_camera_chunk = self.prev_camera_chunk

        self.delta_time = 0
        
        self.wave_radius_animation = 1
        self.current_time = 1  # 0 - 24 hours
        self.time_alpha = 0
        self.time_scale = 1000 # 60
        self.time_map = {
            0: 230,
            6: 180,
            12: 0,
            14: 0,
            18: 50,
            20: 100,
            24: 240
        }

        self.flagged_chunks = set()
        self.flagged_tiles = set()

    def update_time(self) -> None:
        self.current_time += (self.delta_time / 60) * self.time_scale 
        self.current_time %= 10

        keys = sorted(self.time_map.keys())
        for i in range(len(keys)):
            if self.current_time < keys[i]:
                break# TODO remove later
                start_time, start_alpha = keys[i - 1], self.time_map[keys[i - 1]]
                end_time, end_alpha = keys[i], self.time_map[keys[i]]
                self.time_alpha = start_alpha + (end_alpha - start_alpha) * ((self.current_time - start_time) / (end_time - start_time))
                break
        else:
            self.time_alpha = self.time_map[keys[-1]]
        self.time_alpha = 0

    def clear_flags(self, chunks=True, tiles=True):
        if chunks:
            for chunk in self.flagged_chunks:
                chunk.flags.clear()
                chunk.update_chunk_surface(self.assets)
            self.flagged_chunks.clear()
        if tiles:
            for tile in self.flagged_tiles:
                tile.flags.clear()
            self.flagged_tiles.clear()
        
    def update(self, delta_time: float):
        self.delta_time = delta_time
        self.update_time()
        #self.wave_animation(int(self.current_time))

    def load_chunk(self, chunk_pos: tuple[int, int]) -> Chunk:
        x, y = chunk_pos[0] * chunk_size, chunk_pos[1] * chunk_size
        end_y = min(y + chunk_size, self.map_data.shape[0])
        end_x = min(x + chunk_size, self.map_data.shape[1])
        chunk_tile_slice = self.map_data[y:end_y, x:end_x]
        if chunk_tile_slice.size == 0:
            return False
        chunk: Chunk = self.pooled_chunks.pop()
        chunk.position = chunk_pos
        chunk.iso_pos = chunk_to_iso(chunk_pos)
        for index, tile_id in np.ndenumerate(chunk_tile_slice):
            if tile_id >= 0:
                tile_pos = (index[1], index[0])
                chunk.tiles[tile_pos] = Tile(tile_pos, tile_id)
        return chunk

    def pool_chunk(self, chunk_pos: tuple[int, int]) -> None:
        chunk: Chunk = self.chunks.pop(chunk_pos)
        chunk.tiles.clear()
        chunk.flags.clear()
        self.pooled_chunks.append(chunk)

    def get_center_screen_chunk(self) -> position:
        center_x, center_y = screen_width // 2, screen_height // 2
        iso_center_pos = pygame.math.Vector2((center_x, center_y)) - self.camera_offset
        iso_center_pos.x -= chunk_tile_size // 8
        iso_center_pos.y -= chunk_height // 2
        chunk_x, chunk_y = iso_to_grid(iso_center_pos, grid_size=chunk_tile_size)
        return (chunk_x, chunk_y)
    
    def get_mouse_pos_chunk(self, mouse_pos: tuple[position]) -> position:
        center_x, center_y = mouse_pos[0], mouse_pos[1]
        iso_center_pos = pygame.math.Vector2((center_x, center_y)) - self.camera_offset
        chunk_x, chunk_y = iso_to_grid(iso_center_pos, grid_size=chunk_tile_size)
        return (chunk_x, chunk_y)

    def scroll(self, direction: position, delta_time: float) -> None: # for scroll speed and camera offset
        scroll_speed = 8000
        self.camera_offset.x -= direction[0] * scroll_speed * delta_time
        self.camera_offset.y -= direction[1] * scroll_speed * delta_time

    def get_visible_chunk_positions(self, center_chunk_pos: tuple[int, int]) -> set[Chunk]:
        visible_chunks = set()
        for chunk_x, chunk_y in self.chunk_render_map:
            visible_chunks.add((chunk_x + center_chunk_pos[0], chunk_y + center_chunk_pos[1]))
        return visible_chunks

    def update_chunks(self) -> None:
        self.current_camera_chunk = self.get_center_screen_chunk()
        self.prev_camera_chunk = self.current_camera_chunk

        visible_chunks = self.get_visible_chunk_positions(self.current_camera_chunk)
        chunks_to_load = visible_chunks - set(self.chunks.keys())
        chunks_to_unload = set(self.chunks.keys()) - visible_chunks

        for chunk_pos in chunks_to_unload:
            self.pool_chunk(chunk_pos)

        for chunk_pos in chunks_to_load:
            if 0 <= chunk_pos[0] <= self.map_dimensions[0] and 0 <= chunk_pos[1] <= self.map_dimensions[1]:
                chunk = self.load_chunk(chunk_pos)
                if chunk:
                    self.chunks[chunk_pos] = chunk
                    chunk.update_chunk_surface(self.assets)
            
    def render(self, screen: pygame.Surface, light_screen: pygame.Surface , mouse_pos: position, debug=False) -> None:
        chunk_data = []
        chunk: Chunk
        for chunk in self.chunks.values():
            iso_x, iso_y = chunk.iso_pos
            iso_x += self.camera_offset.x
            iso_y += self.camera_offset.y
            if chunk.flags.get('mouse_over'):
                iso_y -= 200
            chunk_surface = chunk.chunk_surface
            chunk_data.append((chunk_surface, (iso_x, iso_y)))
        chunk_data.sort(key=lambda x: (x[1][1], x[1][0]))
        screen.fblits(chunk_data)
        if debug:
            for chunk in self.chunks.values():
                rect = chunk.chunk_surface.get_rect()
                iso_x, iso_y = chunk.iso_pos
                iso_x += self.camera_offset.x
                iso_y += self.camera_offset.y
                rect.topleft = (iso_x, iso_y)
                pygame.draw.rect(screen, (255, 0, 0), rect, 1)

    def wave_animation(self, time):
        center_x, center_y = 15, 15
        ripple_count = 10
        ripple_spacing = 10
        ripple_speed = 1 
        ripple_thickness = 1 

        affected_chunks = set()

        for i in range(ripple_count):
            ripple_radius = i * ripple_spacing + ripple_speed * time
            mask = get_circle_mask(self.map_data, center_x=center_x, center_y=center_y, radius=int(ripple_radius), thickness=ripple_thickness)
            positions = np.where(mask)
            positions = list(zip(positions[1], positions[0]))

            for tile_x, tile_y in positions:
                chunk_x, chunk_y = tile_x // chunk_size, tile_y // chunk_size
                chunk: Chunk = self.chunks.get((chunk_x, chunk_y))
                if chunk:
                    affected_chunks.add(chunk)
                    self.flagged_chunks.add(chunk)
                    tile: Tile = chunk.tiles.get((tile_x % chunk_size, tile_y % chunk_size))
                    if tile:
                        tile.flags['raised'] = True
                        self.flagged_tiles.add(tile)

        for chunk in affected_chunks:
            chunk.update_chunk_surface(self.assets)

    def update_chunk_surfaces(self, target_chunks=None) -> None:
        chunk: Chunk
        if target_chunks:
            for chunk_pos in target_chunks:
                chunk = self.chunks[chunk_pos]
                chunk.update_chunk_surface(self.assets)
            return
        for chunk in self.chunks.values():
            chunk.update_chunk_surface(self.assets)

class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((screen_width, screen_width))
        self.running = True
        self.clock = pygame.time.Clock()
        self.delta_time = 0
        self.current_floor = None
        self.key_time_accumulator = 0
        self.debug = False
        self.mouse_light_source = pygame.image.load(r"Assets/light.png").convert_alpha()
        self.light_mask = pygame.mask.from_surface(self.mouse_light_source)

        # Night / Day light Sources
        self.light_time_surface = pygame.Surface((screen_width, screen_width), pygame.SRCALPHA)

    def start_game(self) -> None: # loads the floors, and updates all chunks
        floor = Floor("perlin.npy", "Assets/Tiles/")
        self.current_floor = floor
        self.current_floor.update_chunks()
    def render(self, mouse_pos: position, debug=False) -> None: # blits chunk surfaces to screen
        self.current_floor.update_chunks()
        self.current_floor.render(self.screen, self.light_time_surface, mouse_pos, debug=debug)
        self.light_time_surface.blit(self.mouse_light_source, (self.mouse_light_source.get_rect(center=mouse_pos)), special_flags=pygame.BLEND_RGBA_SUB)
        self.screen.blit(self.light_time_surface, (0,0))

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
                direction_x, direction_y = 0, 0
                if keys[pygame.K_UP]:
                    direction_y += -1
                if keys[pygame.K_DOWN]:
                    direction_y += 1
                if keys[pygame.K_RIGHT]:
                    direction_x += 1
                if keys[pygame.K_LEFT]:
                    direction_x += -1
                
                if abs(direction_y) == abs(direction_x):
                    direction_x *= 1/1.414
                    direction_y *= 1/1.414

                direction = (direction_x, direction_y)
                self.current_floor.scroll(direction, self.delta_time)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
            self.screen.fill((0, 0, 0, 255))
            self.light_time_surface.fill((0,0,0, self.current_floor.time_alpha))
            self.current_floor.update(self.delta_time)
            self.render(mouse_pos, self.debug)
            self.current_floor.clear_flags()
            pygame.display.update()
            pygame.display.set_caption(f'FPS: {str(round(self.clock.get_fps(), 1))} | Time: {int(self.current_floor.current_time)}')
game = Game()
game.run()
pygame.quit()


