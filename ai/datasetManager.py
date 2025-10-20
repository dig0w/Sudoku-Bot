import os
import re

from PIL import Image

def getNextNumber(path, reg):
    os.makedirs(path, exist_ok=True)

    files = os.listdir(path)

    pattern = re.compile(fr'{reg}_(?:[^_]*_)*?(\d+)\.png$')

    # Extract the numbers from the existing files
    numbers = [int(pattern.match(f).group(1)) for f in files if pattern.match(f)]

    # Find the last number (0 if no files exist)
    last_number = max(numbers) if numbers else 0

    return last_number + 1

def saveImage(img, val):
    path = f"./dataset/{val}";

    next_number = getNextNumber(path, val)

    img_resized = img.resize((28, 28), Image.LANCZOS)

    img_resized.save(f"{path}/{val}_{next_number:03d}.png")



def dataset_stats(dataset_path, classes=range(10)):
    """
    Returns the dataset size and count per class.

    Args:
        dataset_path (str): Path to the dataset folder.
        classes (iterable): Iterable of class names/subfolders, e.g., 0-9

    Returns:
        total_files (int): Total number of files.
        class_counts (dict): Mapping from class -> count
    """
    total_files = 0
    class_counts = {}

    # Make sure dataset folder exists
    os.makedirs(dataset_path, exist_ok=True)

    for c in classes:
        class_folder = os.path.join(dataset_path, str(c))
        os.makedirs(class_folder, exist_ok=True)  # create class folder if missing
        num_files = len([f for f in os.listdir(class_folder) if os.path.isfile(os.path.join(class_folder, f))])
        class_counts[c] = num_files
        total_files += num_files

    print("Total files:", total_files)
    print("Files per class:", class_counts)


dataset_stats("./ai/dataset")