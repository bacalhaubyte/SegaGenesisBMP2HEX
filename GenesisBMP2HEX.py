from PIL import Image
import os
import numpy as np

def rgb_to_genesis_color(r, g, b):
    """
    Convert RGB values to Genesis 9-bit color format.
    Genesis uses 3 bits per color component (0-7 range).
    """
    # Convert 8-bit RGB (0-255) to 3-bit Genesis format (0-7)
    genesis_r = round(r / 255 * 7)
    genesis_g = round(g / 255 * 7)
    genesis_b = round(b / 255 * 7)
    
    # Combine into 9-bit value: BBB GGG RRR
    return (genesis_b << 6) | (genesis_g << 3) | genesis_r

def create_genesis_palette(image):
    """
    Create a 16-color palette from the image, converted to Genesis format.
    """
    # Convert image to use only 16 colors
    quantized = image.quantize(colors=16, method=Image.MEDIANCUT)
    palette_colors = quantized.getpalette()[:48]  # 16 colors × 3 components
    
    # Convert palette to Genesis format
    genesis_palette = []
    for i in range(0, 48, 3):
        r, g, b = palette_colors[i], palette_colors[i+1], palette_colors[i+2]
        genesis_color = rgb_to_genesis_color(r, g, b)
        genesis_palette.append(genesis_color)
    
    # Pad palette to 16 colors if needed
    while len(genesis_palette) < 16:
        genesis_palette.append(0)
    
    return genesis_palette, quantized

def image_to_tiles(image):
    """
    Convert image to 8x8 tiles and return tile data.
    """
    width, height = image.size
    
    # Ensure image dimensions are multiples of 8
    new_width = ((width + 7) // 8) * 8
    new_height = ((height + 7) // 8) * 8
    
    # Resize image if needed
    if new_width != width or new_height != height:
        new_image = Image.new('P', (new_width, new_height), 0)
        new_image.paste(image, (0, 0))
        image = new_image
    
    # Convert to array for easier manipulation
    img_array = np.array(image)
    
    tiles = []
    tiles_x = new_width // 8
    tiles_y = new_height // 8
    
    for tile_y in range(tiles_y):
        for tile_x in range(tiles_x):
            # Extract 8x8 tile
            tile_data = []
            for y in range(8):
                for x in range(8):
                    pixel_x = tile_x * 8 + x
                    pixel_y = tile_y * 8 + y
                    pixel_value = img_array[pixel_y, pixel_x]
                    tile_data.append(pixel_value & 0xF)  # Ensure 4-bit value
            
            tiles.append(tile_data)
    
    return tiles, tiles_x, tiles_y

def tiles_to_genesis_hex(tiles):
    """
    Convert tile data to Genesis hex format.
    Each tile is 32 bytes (8x8 pixels, 4 bits per pixel).
    """
    hex_data = []
    
    for tile in tiles:
        tile_bytes = []
        # Pack two 4-bit pixels into each byte
        for i in range(0, 64, 2):
            byte_value = (tile[i] << 4) | tile[i + 1]
            tile_bytes.append(f"{byte_value:02X}")
        
        hex_data.extend(tile_bytes)
    
    return hex_data

def bitmap_to_genesis_hex(image_path):
    """
    Convert a bitmap image to Sega Genesis compatible hex format.
    """
    # Open and convert image to RGB
    img = Image.open(image_path)
    img = img.convert('RGB')
    
    print(f"Original image size: {img.size}")
    
    # Create Genesis-compatible palette
    genesis_palette, quantized_img = create_genesis_palette(img)
    
    # Convert to tiles
    tiles, tiles_x, tiles_y = image_to_tiles(quantized_img)
    
    print(f"Image converted to {tiles_x}x{tiles_y} tiles ({len(tiles)} total tiles)")
    
    # Convert tiles to hex
    tile_hex_data = tiles_to_genesis_hex(tiles)
    
    return {
        'palette': genesis_palette,
        'tile_data': tile_hex_data,
        'tiles_x': tiles_x,
        'tiles_y': tiles_y,
        'total_tiles': len(tiles)
    }

def format_output(data):
    """
    Format the output for Genesis development.
    """
    output = []
    
    # Palette data
    output.append("; Genesis Palette Data (16 colors)")
    output.append("palette_data:")
    palette_hex = [f"${color:04X}" for color in data['palette']]
    for i in range(0, 16, 8):
        line = "    dc.w " + ", ".join(palette_hex[i:i+8])
        output.append(line)
    
    output.append("")
    
    # Tile data
    output.append("; Genesis Tile Data")
    output.append(f"; {data['total_tiles']} tiles ({data['tiles_x']}x{data['tiles_y']})")
    output.append("tile_data:")
    
    tile_data = data['tile_data']
    for i in range(0, len(tile_data), 16):
        line_data = tile_data[i:i+16]
        line = "    dc.b $" + ", $".join(line_data)
        output.append(line)
    
    return "\n".join(output)

def get_image_path():
    """
    Prompt user for image file path with validation.
    """
    while True:
        image_path = input("Enter path to image file: ").strip()
        
        # Remove quotes if user wrapped path in quotes
        if image_path.startswith('"') and image_path.endswith('"'):
            image_path = image_path[1:-1]
        elif image_path.startswith("'") and image_path.endswith("'"):
            image_path = image_path[1:-1]
        
        if os.path.exists(image_path):
            return image_path
        else:
            print(f"Error: File '{image_path}' not found. Try again.")

def main():
    print("Bitmap to Sega Genesis Hex Converter")
    print("=" * 40)
    print("This script converts images to Genesis-compatible tile data.")
    print("- Images are converted to 16-color palettes")
    print("- Graphics are organized as 8x8 pixel tiles")
    print("- Output is formatted for Genesis assembly code")
    print()
    
    # Get image path from user
    image_path = get_image_path()
    
    try:
        print(f"\nProcessing image: {image_path}")
        result = bitmap_to_genesis_hex(image_path)
        
        # Format output
        formatted_output = format_output(result)
        
        print("\nGenesis-compatible hex data generated!")
        print(f"Palette: {len(result['palette'])} colors")
        print(f"Tiles: {result['total_tiles']} tiles ({result['tiles_x']}x{result['tiles_y']})")
        
        # Ask user if they want to save to file
        save_choice = input("\nSave the output to an assembly file? (y/n): ").lower().strip()
        
        if save_choice in ['y', 'yes']:
            output_filename = input("Enter output filename (or press Enter for 'genesis_data.asm'): ").strip()
            if not output_filename:
                output_filename = 'genesis_data.asm'
            
            with open(output_filename, 'w') as f:
                f.write(formatted_output)
            print(f"Genesis data saved to '{output_filename}'")
        else:
            print("\nGenerated assembly code:")
            print("-" * 40)
            print(formatted_output)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        print("Make sure the file is a valid image format.")

if __name__ == "__main__":
    main()
