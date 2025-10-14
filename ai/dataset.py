import os
from PIL import Image
from torch.utils.data import Dataset

class SudokuDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        """
        root_dir: path to dataset folder
        transform: torchvision transforms to apply (augmentation + normalization)
        """
        self.root_dir = root_dir
        self.transform = transform
        self.images = []  # list of (image_path, label)
        
        for label in range(10):
            folder = os.path.join(root_dir, str(label))
            for filename in os.listdir(folder):
                if filename.endswith(".png") or filename.endswith(".jpg"):
                    self.images.append((os.path.join(folder, filename), label))
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        path, label = self.images[idx]
        img = Image.open(path).convert("L")  # grayscale
        if self.transform:
            img = self.transform(img)
        return img, label