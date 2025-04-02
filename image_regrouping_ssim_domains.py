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

groups_at_start = database['image_group'].nunique()

#identify domain groups with images from multiple image groups
multi_group_domains = database.groupby('domain_group')['image_group'] \
    .nunique() \
    .loc[lambda x: x > 1] \
    .index.tolist()

print(f"We have {len(multi_group_domains)} domain groups with images from different image groups")

for domain_group in multi_group_domains:

    # image groups in the domain group
    image_groups = database.loc[(database['domain_group'] == domain_group) & (database['image_group'].notna()), 'image_group'].unique().tolist()

    #print(f"Image groups for domain group {domain_group}: {image_groups}")

    benchmark = database.loc[database['image_group'] == image_groups[0], 'id'].iloc[0]
    try:
        img1 = cv2.imread(f"{LOGO_FOLDER}/{benchmark}.png")
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print(f"Error for benchmark {benchmark}: {e}")
        continue
    #print(f"Benchmark is: {benchmark}")

    for i in range(1, len(image_groups)):
        representative = database.loc[database['image_group'] == image_groups[i], 'id'].iloc[0]

        try:
            img2 = cv2.imread(f"{LOGO_FOLDER}/{representative}.png")
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            print(f"Error for representative {representative}: {e}")
            continue

        similarity, _ = ssim(gray1, gray2, full=True)

        if similarity > SSIM_THRESHOLD:
            # the image groups could be merged
            database.loc[database['image_group'] == image_groups[i], 'image_group'] = image_groups[0]
            #print(f"{representative} | Groups merged {image_groups[0]} and {image_groups[i]} because their similarity score was {similarity}")

        print(f"Comparing {benchmark} with {representative} --> similarity: {similarity}")

print(f"Image groups at start | end: {groups_at_start} | {database['image_group'].nunique()}")

database.to_csv(database_file, index=False)
