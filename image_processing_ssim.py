import os
from PIL import Image, ImageOps, ImageDraw
import io
import cairosvg

INPUT_FOLDER = 'logos'
OUTPUT_FOLDER = 'logos_ssim'
SVG_FOLDER = 'logos_svg_temp'

def process_image(image_path, output_folder, target_size=(256, 256)):
    try:
        # Open image and convert to RGBA to handle transparency
        with Image.open(image_path).convert("RGBA") as img:
            # Create white background for alpha composite
            background = Image.new("RGBA", img.size, (255, 255, 255))
            img = Image.alpha_composite(background, img).convert("RGB")

            # Trim white/transparent borders
            trimmed = ImageOps.crop(img, border=0)
            bbox = trimmed.convert("RGB").getbbox()
            if bbox:
                trimmed = trimmed.crop(bbox)

            #trimmed.thumbnail((target_size[0] * 2, target_size[1] * 2), Image.Resampling.LANCZOS)
            resized = ImageOps.pad(trimmed, target_size, color="white")

            output_path = os.path.join(output_folder, os.path.splitext(os.path.basename(image_path))[0] + ".png")
            resized.save(output_path, "PNG", optimize=True)

    except Exception as e:
        print(f"Error processing {image_path}: {e}")


def svg_to_raster(svg_path, size):

    with open(svg_path, 'r', encoding='utf-8') as svg_file:
        svg_content = svg_file.read()

    png_bytes = cairosvg.svg2png(bytestring=svg_content)

    img = Image.open(io.BytesIO(png_bytes))

    return img.resize(size)

def batch_process_images(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        print(f"Processing {filename}")
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')):
            process_image(os.path.join(input_folder, filename), output_folder)
        elif filename.lower().endswith(('.svg')):
            #we have a svg
            svg_image = svg_to_raster(f"{INPUT_FOLDER}/{filename}", size=(256, 256))
            svg_image.save(f"{SVG_FOLDER}/{filename.replace('svg','png')}", "PNG", optimize=True)
            process_image(os.path.join(SVG_FOLDER, filename.replace('svg','png')), output_folder)

        else:
            #we have something else...
            print("What is this???")

def process_one_image(input_folder, output_folder, imgfile):
    print(f"Processing {imgfile}")
    if imgfile.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')):
        process_image(os.path.join(input_folder, imgfile), output_folder)
    elif imgfile.lower().endswith(('.svg')):
        #we have a svg
        svg_image = svg_to_raster(f"{INPUT_FOLDER}/{imgfile}", size=(256, 256))
        svg_image.save(f"{SVG_FOLDER}/{imgfile.replace('svg','png')}", "PNG", optimize=True)
        process_image(os.path.join(SVG_FOLDER, imgfile.replace('svg','png')), output_folder)

    else:
        #we have something else...
        print("What is this???")

batch_process_images(INPUT_FOLDER, OUTPUT_FOLDER)

#process_one_image(INPUT_FOLDER, OUTPUT_FOLDER, 'mercyships_be.png')
