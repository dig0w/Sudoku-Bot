import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms


# ---- DataSet ----
from torch.utils.data import Dataset
import os
from PIL import Image

class DigitDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.images = []
        
        for label in range(10):
            folder = os.path.join(root_dir, str(label))
            for filename in os.listdir(folder):
                if filename.endswith(".png") or filename.endswith(".jpg"):
                    self.images.append((os.path.join(folder, filename), label))
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        path, label = self.images[idx]
        img = Image.open(path).convert("L")
        if self.transform:
            img = self.transform(img)
        return img, label


# ---- CNN ----
from digitsCNN import DigitsCNN


# ---- Train Model ----
# Transforms
transform = transforms.Compose([
    transforms.Resize((28,28)),
    transforms.RandomRotation(5),
    transforms.RandomAffine(0, translate=(0.05, 0.05)),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

# Dataset & Dataloader
dataset = DigitDataset("dataset", transform=transform)
loader = DataLoader(dataset, batch_size=16, shuffle=True)

# Model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DigitsCNN().to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training Loop
epochs = 5
print(f"🚀 Training on {device} for {epochs} epochs...\n")

for epoch in range(epochs):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

    print(f"Epoch {epoch+1}/{epochs}: Loss: {total_loss/len(loader):.4f} | Acc: {100*correct/total:.2f}%")

# Save
saveName = "digitsCNN.pt"
torch.save(model.state_dict(), f"../{saveName}")
print(f"\n💾 Model saved as {saveName}")