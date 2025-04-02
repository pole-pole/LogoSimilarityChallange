import hashlib
import os
import csv
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

# Configuration variables
LOGO_FOLDER = "logos"  # Replace with your target directory
NUM_THREADS = 100  # Adjust based on your CPU cores

database_file = 'database.csv'
database = pd.read_csv(database_file)

#convert column types
database = database.astype('object')

def compute_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_file(file_path):
    try:
        relative_path = os.path.relpath(file_path, LOGO_FOLDER)
        return (relative_path, compute_checksum(file_path))
    except Exception as e:
        return None

# Collect all file paths first
file_paths = []
for root, _, files in os.walk(LOGO_FOLDER):
    for filename in files:
        file_path = os.path.join(root, filename)
        file_paths.append(file_path)

# Process files in parallel
checksum_groups = {}
with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    results = executor.map(process_file, file_paths)

    # Process results as they complete
    for result in results:
        if result:
            rel_path, checksum = result
            checksum_groups.setdefault(checksum, []).append(rel_path)

# Create sorted group assignments
sorted_checksums = sorted(checksum_groups.keys())
group_assignment = {
    checksum: f"group_{i + 1}"
    for i, checksum in enumerate(sorted_checksums)
}

#we delete any existing groupings
database['image_group'] = ''

for checksum, image_list in checksum_groups.items():
    for item in image_list:
        row_id = item.split('.')[0]
        database.loc[database['id'] == row_id, 'image_group'] = group_assignment[checksum]
        print(f"{row_id} is in {group_assignment[checksum]}")

for item in file_paths:
    row_id = item.split('.')[0].replace("logos\\", "")
    database.loc[database['id'] == row_id, 'logo_file_name'] = item

database.to_csv(database_file, index=False)

print(f"Created {database['image_group'].nunique()} groups")
