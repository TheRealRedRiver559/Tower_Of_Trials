import os
import pygame
import csv

pygame.init()
tile_size = 32
width, height = 1000, 700
chunk_size = 12
chunk_tile_size = chunk_size * tile_size
tile_raise_amount = 40

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

def grid_to_iso_pos(grid_pos, size=tile_size):
    grid_x, grid_y = grid_pos
    iso_x = (grid_x - grid_y) * size // 2
    iso_y = (grid_x + grid_y) * size // 4

    iso_x -= tile_size//2
    iso_x += width // 2
    iso_y += height // 4
    return iso_x, iso_y

def iso_to_grid_pos(iso_pos, size=tile_size):
    iso_x, iso_y = iso_pos
    iso_x -= width // 2
    iso_x += tile_size//2
    iso_y -= height // 4

    grid_x = (2 * iso_y + iso_x) // size
    grid_y = (2 * iso_y - iso_x) // size

    return int(grid_x), int(grid_y)

def chunk_to_iso_pos(grid_pos):
    grid_x, grid_y = grid_pos
    iso_x = (grid_x - grid_y) * chunk_tile_size // 2
    iso_y = (grid_x + grid_y) * chunk_tile_size // 4
    iso_x += width // 2
    iso_y += height // 4
    return iso_x, iso_y

def iso_to_chunk_pos(iso_pos, size=chunk_tile_size):
    iso_x, iso_y = iso_pos
    iso_x -= width // 2
    iso_x += size//2
    iso_y -= height // 4

    grid_x = (2 * iso_y + iso_x) // size
    grid_y = (2 * iso_y - iso_x) // size

    return int(grid_x), int(grid_y)

def create_chunk_render_map(screen_chunk_x=4, screen_chunk_y=4):
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

class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_id, position, image) -> None:
        super().__init__()
        self.tile_id = tile_id
        self.position = pygame.math.Vector2(position)
        self.image = image
        self.rect = self.image.get_rect(topleft=grid_to_iso_pos(self.position))
        self.flags = {}

    def draw(self, screen: pygame.surface.Surface, camera_offset: pygame.math.Vector2) -> None:
        iso_pos = grid_to_iso_pos(self.position) + camera_offset
        if self.flags.get('mouse_over_tile'):
            iso_pos.y -= tile_raise_amount
        return (self.image, iso_pos)
        #screen.blit(self.image, iso_pos)


        if self.flags.get('mouse_over_tile'):
            iso_pos.y += tile_raise_amount
            p1 = (iso_pos.x, iso_pos.y) + pygame.math.Vector2(tile_size/2, tile_size/2)
            p2 = (iso_pos.x+tile_size/2, iso_pos.y+tile_size/4) + pygame.math.Vector2(tile_size/2, tile_size/2)
            p3 = (iso_pos.x, iso_pos.y+tile_size/2) + pygame.math.Vector2(tile_size/2, tile_size/2)
            p4 = (iso_pos.x-tile_size/2, iso_pos.y+tile_size/4) + pygame.math.Vector2(tile_size/2, tile_size/2)
            pygame.draw.polygon(screen, (255,255,0), [p1,p2,p3,p4], 1)

    def draw_tile_debug(self, screen, camera_offset):
        grid_x, grid_y = self.position
        p1 = grid_to_iso_pos((grid_x, grid_y)) + camera_offset + pygame.math.Vector2(tile_size/2, tile_size/2)
        p2 = grid_to_iso_pos((grid_x, grid_y+1)) + camera_offset + pygame.math.Vector2(tile_size/2, tile_size/2)
        p3 = grid_to_iso_pos((grid_x+1, grid_y+1)) + camera_offset + pygame.math.Vector2(tile_size/2, tile_size/2)
        p4 = grid_to_iso_pos((grid_x+1, grid_y)) + camera_offset + pygame.math.Vector2(tile_size/2, tile_size/2)
        pygame.draw.polygon(screen, (0,255,0), [p1,p2,p3,p4], 1)

class Chunk:
    def __init__(self, position) -> None:
        self.position = pygame.math.Vector2(position)
        self.tiles = {}
        self.flags = {}

    def draw_chunk(self, screen, camera_offset):
        tile: Tile
        tiles = []
        for tile in self.tiles.values():
            if self.flags.get('mouse_over_chunk'):
                tile.flags['mouse_over_tile'] = True
            tiles.append(tile.draw(screen, camera_offset))
        screen.fblits(tiles)

        if self.flags.get('mouse_over_chunk'):
            grid_x, grid_y = self.position
            p1 = chunk_to_iso_pos((grid_x, grid_y)) + camera_offset - pygame.math.Vector2(0, tile_raise_amount)
            p2 = chunk_to_iso_pos((grid_x, grid_y+1)) + camera_offset - pygame.math.Vector2(0, tile_raise_amount)
            p3 = chunk_to_iso_pos((grid_x+1, grid_y+1)) + camera_offset - pygame.math.Vector2(0, tile_raise_amount)
            p4 = chunk_to_iso_pos((grid_x+1, grid_y)) + camera_offset - pygame.math.Vector2(0, tile_raise_amount)
            pygame.draw.polygon(screen, (255,0,0), [p1,p2,p3,p4], 3)
    
    def draw_chunk_tile_debug(self, screen, camera_offset):
        tile: Tile
        for tile in self.tiles.values():
            tile.draw_tile_debug(screen, camera_offset)
    
    def draw_chunk_debug(self, screen, camera_offset):
        grid_x, grid_y = self.position
        p1 = chunk_to_iso_pos((grid_x, grid_y)) + camera_offset
        p2 = chunk_to_iso_pos((grid_x, grid_y+1)) + camera_offset
        p3 = chunk_to_iso_pos((grid_x+1, grid_y+1)) + camera_offset
        p4 = chunk_to_iso_pos((grid_x+1, grid_y)) + camera_offset
        pygame.draw.polygon(screen, (255,0,0), [p1,p2,p3,p4], 3)

class Floor:
    def __init__(self, floor_path, map_path) -> None:
        self.camera_offset = pygame.math.Vector2(0, 0)
        self.floor_path = floor_path
        self.map_path = map_path
        self.chunks = {}

        self.assets = load_assets(self.floor_path)
        self.load_floor_map()

    def get_visible_chunks(self):
        center_x, center_y = width//2, height//2
        iso_mouse_pos = pygame.math.Vector2((center_x, center_y)) - self.camera_offset + pygame.math.Vector2(0, chunk_tile_size//8)
        iso_mouse_pos.x -= tile_size // 2
        iso_mouse_pos.y -= tile_size // 4
        grid_mouse_pos = iso_to_grid_pos(iso_mouse_pos)

        chunk_x, chunk_y = grid_mouse_pos[0] // chunk_size, grid_mouse_pos[1] // chunk_size
        return filter_visible_chunks(self.chunks, (chunk_x, chunk_y))

    def get_mouse_tile(self, mouse_pos):
        iso_mouse_pos = pygame.math.Vector2(mouse_pos) - self.camera_offset
        iso_mouse_pos.x -= tile_size // 2
        iso_mouse_pos.y -= tile_size // 4
        grid_mouse_pos = iso_to_grid_pos(iso_mouse_pos)

        chunk_x, chunk_y = grid_mouse_pos[0] // chunk_size, grid_mouse_pos[1] // chunk_size
        chunk_pos = (chunk_x, chunk_y)

        chunk: Chunk = self.chunks.get(chunk_pos)
        if chunk and grid_mouse_pos in chunk.tiles:
            chunk.tiles[grid_mouse_pos].flags['mouse_over_tile'] = True

    def get_mouse_chunk(self, mouse_pos):
        iso_mouse_pos = pygame.math.Vector2(mouse_pos) - self.camera_offset + pygame.math.Vector2(0, chunk_tile_size//8)
        iso_mouse_pos.x -= tile_size // 2
        iso_mouse_pos.y -= tile_size // 4  + chunk_tile_size//8
        grid_mouse_pos = iso_to_grid_pos(iso_mouse_pos)

        chunk_x, chunk_y = grid_mouse_pos[0] // chunk_size, grid_mouse_pos[1] // chunk_size
        chunk_pos = (chunk_x, chunk_y)

        chunk: Chunk = self.chunks.get(chunk_pos)
        if chunk:
            chunk.flags['mouse_over_chunk'] = True
            return chunk


    def scroll(self, direction: pygame.math.Vector2, delta_time):
        scroll_speed = 600
        self.camera_offset -= direction * scroll_speed * delta_time

    def clear_tile_flags(self):
        for chunk in self.chunks.values():
            chunk.flags.clear()
            for tile in chunk.tiles.values():
                tile.flags['mouse_over_tile'] = False

    def render(self, screen: pygame.surface.Surface, mouse_pos, debug=False) -> None:
        #self.get_mouse_tile(mouse_pos)
        #self.get_mouse_chunk(mouse_pos)
        visible_chunks = self.get_visible_chunks()
        chunk: Chunk

        for chunk in visible_chunks:
            chunk.draw_chunk(screen, self.camera_offset)
        if debug:
            for chunk in visible_chunks:
                chunk.draw_chunk_debug(screen, self.camera_offset)
            for chunk in visible_chunks:
                chunk.draw_chunk_tile_debug(screen, self.camera_offset)
            self.clear_tile_flags()

    def load_floor_map(self) -> None:
        with open(self.map_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for row_index, row in enumerate(reader):
                for col_index, tile_id_str in enumerate(row):
                    tile_id = int(tile_id_str)
                    if tile_id < 0:
                        continue
                    grid_pos = (col_index, row_index)
                    tile_image = self.assets[tile_id]
                    tile = Tile(tile_id, grid_pos, tile_image)

                    chunk_x, chunk_y = grid_pos[0] // chunk_size, grid_pos[1] // chunk_size
                    chunk_pos = (chunk_x, chunk_y)
                    if chunk_pos not in self.chunks:
                        self.chunks[chunk_pos] = Chunk(chunk_pos)

                    self.chunks[chunk_pos].tiles[grid_pos] = tile

    def render_mouse_hover(self, mouse_pos):
        chunk: Chunk = self.get_mouse_chunk(mouse_pos)
        return chunk

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

    def start_game(self):
        floor1 = Floor("Assets/Tiles/", "Floors/Floor1/LARGE.csv")
        self.current_floor = floor1

    def render(self, mouse_pos):
        self.current_floor.render(self.screen, mouse_pos)

    def run(self):
        self.start_game()
        while self.running:
            self.delta_time = self.clock.tick(120) / 1000
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
                if keys[pygame.K_o]:
                    self.floor_index -= 1
                    if self.floor_index < 0:
                        self.floor_index = len(self.maps)-1
                    floor = Floor("Assets/Tiles/", f"Floors/Floor1/{self.maps[self.floor_index]}")
                    self.current_floor = floor

                self.current_floor.scroll(direction, self.delta_time)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

            self.screen.fill((0, 0, 0))
            #self.current_floor.render_mouse_hover(mouse_pos)
            total_tiles = len(self.current_floor.chunks)*chunk_size*chunk_size
            rendered_tiles = len(chunk_render_map)*chunk_size*chunk_size
            self.render(mouse_pos)
            pygame.display.update()
            pygame.display.set_caption(f"FPS: {int(self.clock.get_fps())} | Tiles being rendered: {rendered_tiles} | Total Tiles: {total_tiles} ")

game = Game()
game.run()
pygame.quit()
