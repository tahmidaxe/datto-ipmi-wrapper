import sys
from PIL import Image

if len(sys.argv) < 3:
    print("Usage: python convert_icon.py <input.png> <output.ico>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    img = Image.open(input_file)
    # Resize to have multiple sizes in the ICO for better scaling
    icon_sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
    img.save(output_file, format='ICO', sizes=icon_sizes)
    print(f"Successfully converted {input_file} to {output_file}")
except Exception as e:
    print(f"Error converting image: {e}")
