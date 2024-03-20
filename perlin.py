from noise import pnoise2
import numpy as np

def save_map(map_data: np.ndarray, np_file: str) -> None:
    np.save(np_file, map_data)

def generate_perlin_noise_map(shape, scale, octaves, persistence, lacunarity, num_tiles):
    height, width = shape
    map_data = np.zeros(shape, dtype=int)

    for y in range(height):
        for x in range(width):
            noise_value = pnoise2(x / scale, 
                                  y / scale, 
                                  octaves=octaves, 
                                  persistence=persistence, 
                                  lacunarity=lacunarity)
            tile_id = int((noise_value + 1) / 2 * num_tiles)
            map_data[y, x] = tile_id+99

    return map_data

map_shape = (10000, 10000) # may take a few minutes to generate (decease size if needed)
scale = 60
octaves = 7
persistence = 0.5 
lacunarity = 3.0
num_tiles = 5 
perlin_map = generate_perlin_noise_map(map_shape, scale, octaves, persistence, lacunarity, num_tiles)
save_map(perlin_map, 'perlin.npy')
