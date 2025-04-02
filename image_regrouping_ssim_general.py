import pandas as pd
from skimage.metrics import structural_similarity as ssim
from skimage.io import imread
from skimage.transform import resize
from svgpathtools import svg2paths
from io import BytesIO
from itertools import combinations
from PIL import Image, ImageDraw
#from wand.image import Image, ImageDraw
import numpy as np
import cv2

database_file = 'database.csv'

database = pd.read_csv(database_file)
#convert column types
database = database.astype('object')

LOGO_FOLDER = 'logos_ssim'
SSIM_THRESHOLD = 0.95


image_groups = database['image_group'].dropna().unique().tolist()
groups_at_start = len(image_groups)

merged_groups = []
remaining_groups = image_groups.copy()

for image_group in image_groups:

    print(f"Comparing group {image_group}")

    if image_group in merged_groups:
        #we skip this group because we already merged it
        continue

    if image_group in remaining_groups:
        remaining_groups.remove(image_group)

    query = database.loc[database['image_group'] == image_group, 'id']
    if query.empty:
        continue
    else:
        benchmark = str(query.iloc[0])

    try:
        img1 = cv2.imread(f"{LOGO_FOLDER}/{benchmark}.png")
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print(f"Error for benchmark {benchmark}: {e}")
        continue
    #print(f"Benchmark is: {benchmark}")

    for group in remaining_groups:

        query = database.loc[database['image_group'] == group, 'id']
        if query.empty:
            continue
        else:
            representative = str(query.iloc[0])

        try:
            img2 = cv2.imread(f"{LOGO_FOLDER}/{representative}.png")
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            print(f"Error for representative {representative}: {e}")
            continue

        similarity, _ = ssim(gray1, gray2, full=True)

        if similarity > SSIM_THRESHOLD:
            # the image groups could be merged
            database.loc[database['image_group'] == group, 'image_group'] = image_group
            remaining_groups.remove(group)
            print(f"Removed group {group}, {len(remaining_groups)} remaining")
            # print(f"{representative} | Groups merged {image_groups[0]} and {image_groups[i]} because their similarity score was {similarity}")

        #print(f"Comparing {benchmark} with {representative} --> similarity: {similarity}")

print(f"Image groups at start | end: {groups_at_start} | {database['image_group'].nunique()}")
print(f"Merged groups: {merged_groups}")

database.to_csv(database_file, index=False)
