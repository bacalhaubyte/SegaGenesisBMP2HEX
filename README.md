# Sega Genesis/Mega Drive BMP2HEX
This Python script converts bitmap images into Sega Genesis(Mega Drive)-compatible hex data for retro game development. It automatically processes images by reducing them to 16-color palettes, organizing graphics into 8x8 pixel tiles, and converting colors to the Genesis's 9-bit color format. The assembly formatted palette and tile data can be directly included in game projects.

Genesis Color Conversion:
* Converts RGB colors to Genesis 9-bit format (3 bits per color component)
* Creates a 16-color palette using median cut quantization

Tile-Based Processing:
* Converts images to 8x8 pixel tiles required by Genesis hardware
* Automatically pads image dimensions to multiples of 8

4-Bit Pixel Data:
* Each pixel uses 4 bits to reference palette colors (0-15)
* Two pixels are packed into each byte for efficient storage

Assembly Output:
* Formats output as Genesis assembly code with dc.w and dc.b directives
* Includes palette data and tile data
* Can be directly included in game source code
