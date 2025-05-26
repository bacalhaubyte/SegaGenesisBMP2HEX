import re
import struct

def parse_genesis_assembly(asm_path):
    """
    Extract palette and tile data from Genesis assembly file
    """
    with open(asm_path, 'r') as f:
        content = f.read()

    # Extract palette data (dc.w entries)
    palette = []
    palette_matches = re.findall(r'palette_data:\s*(.*?)(?=\n\S|\Z)', content, re.DOTALL)
    if palette_matches:
        for match in re.findall(r'\$([0-9A-Fa-f]{3,4})', palette_matches[0]):
            palette.append(int(match, 16))

    # Extract tile data (dc.b entries)
    tile_data = []
    tile_matches = re.findall(r'tile_data:\s*(.*?)(?=\n\S|\Z)', content, re.DOTALL)
    if tile_matches:
        for match in re.findall(r'\$([0-9A-Fa-f]{2})', tile_matches[0]):
            tile_data.append(int(match, 16))

    return palette, tile_data

def genesis_to_rgb(color):
    """
    Convert Genesis 9-bit color to 24-bit RGB
    """
    r = (color & 0x007) << 5  # 3 bits red
    g = (color & 0x038) << 2  # 3 bits green
    b = (color & 0x1C0) >> 1  # 3 bits blue
    return (r, g, b)

def create_bmp(palette, tiles, width_tiles, height_tiles, output_path):
    """
    Create indexed BMP from Genesis tile data
    """
    # BMP dimensions
    tile_size = 8
    width_px = width_tiles * tile_size
    height_px = height_tiles * tile_size

    # Create BMP headers
    headers = struct.pack('<HLHHL',
        0x4D42,                 # BM signature
        54 + 64 + (width_px * height_px // 2), # File size
        0, 0,                   # Reserved
        54 + 64)                # Pixel data offset

    # BITMAPINFOHEADER
    headers += struct.pack('<LLLHHLLLLLL',
        40,                     # Header size
        width_px,
        height_px,
        1,                      # Planes
        4,                      # Bits per pixel (4-bit indexed)
        0,                      # Compression (none)
        0,                      # Image size (0 for uncompressed)
        2835, 2835,             # Pixels/meter (72 DPI)
        16,                     # Colors used
        16)                     # Important colors

    # Create color table (16 entries)
    color_table = bytearray()
    for color in palette:
        rgb = genesis_to_rgb(color)
        color_table += struct.pack('<BBBx',
            min(rgb[2], 255),   # Blue
            min(rgb[1], 255),   # Green
            min(rgb[0], 255))   # Red

    # Pad color table to 64 bytes
    color_table += b'\x00' * (64 - len(color_table))

    # Reconstruct pixel data
    pixel_data = bytearray()
    for ty in range(height_tiles-1, -1, -1):
        for y in range(7, -1, -1):
            row = bytearray()
            for tx in range(width_tiles):
                tile_index = ty * width_tiles + tx
                tile_start = tile_index * 32
                tile_row = tile_data[tile_start + y*4 : tile_start + y*4 + 4]
                
                # Unpack 4-bit pixels
                for byte in tile_row:
                    row.append((byte >> 4) & 0x0F)
                    row.append(byte & 0x0F)
            
            # Pack 4-bit pixels into bytes
            packed_row = bytearray()
            for i in range(0, len(row), 2):
                packed_row.append((row[i] << 4) | row[i+1])
            
            # Add row padding to multiple of 4 bytes
            packed_row += b'\x00' * (-len(packed_row) % 4)
            pixel_data.extend(packed_row)

    # Write BMP file
    with open(output_path, 'wb') as f:
        f.write(headers)
        f.write(color_table)
        f.write(pixel_data)

if __name__ == "__main__":
    print("Genesis Assembly to BMP Converter")
    print("=" * 35)
    
    # Get user input
    input_file = input("Enter path to Genesis assembly file: ").strip()
    output_file = input("Enter output BMP filename: ").strip()
    width_tiles = int(input("Enter width in tiles (e.g., 6): ").strip())
    height_tiles = int(input("Enter height in tiles (e.g., 6): ").strip())

    try:
        # Process assembly file
        palette, tile_data = parse_genesis_assembly(input_file)
        
        # Create BMP
        create_bmp(palette, tile_data, width_tiles, height_tiles, output_file)
        print(f"\nSuccessfully converted {input_file} to {output_file}")
        print(f"Image dimensions: {width_tiles*8}x{height_tiles*8} pixels")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please verify:")
        print("- Input file is valid Genesis assembly from the converter script")
        print("- Tile dimensions match the original image")
        print("- You have read/write permissions for the files")
