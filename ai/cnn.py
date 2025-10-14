import torch
import torch.nn as nn
import torch.nn.functional as F

class DigitCNN(nn.Module):
    def __init__(self):
        super(DigitCNN, self).__init__()
        # First "convolution layer": finds edges/lines in the image
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        # Second layer: finds more complex shapes
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        # Fully connected "dense" layers: combine features into decisions
        self.fc1 = nn.Linear(64*5*5, 128)  # adjust for 28x28 input size
        self.fc2 = nn.Linear(128, 10)      # outputs 10 classes: 0–9

    def forward(self, x):
        # How data flows through the network
        x = F.relu(self.conv1(x))               # apply first conv + ReLU activation
        x = F.max_pool2d(x, 2, 2)               # reduce size
        x = F.relu(self.conv2(x))               # second conv
        x = F.max_pool2d(x, 2, 2)               # reduce again
        x = torch.flatten(x, 1)                 # flatten into 1D
        x = F.relu(self.fc1(x))                 # dense layer
        x = self.fc2(x)                         # final predictions
        return x