import cv2
import numpy as np
import ai.datasetManager as dsM

# Returns the default image and a binary tresholded version
def loadImage(img):
    imgNA = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(imgNA, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    return imgNA, thresh

# Finds the biggest square
def findBoard(thresh):
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Sort by area (biggest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:  # Found a quadrilateral
            return approx
    
    return None

def orderPoints(pts):
    pts = pts.reshape((4,2))
    rect = np.zeros((4,2), dtype="float32")
    
    s = pts.sum(axis=1)

    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)

    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

# Warps the detected quadrilateral into a clean 450×450 square
def warpBoard(img, boardContour):
    rect = orderPoints(boardContour)
    dst = np.array([[0,0],[450,0],[450,450],[0,450]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    
    warp = cv2.warpPerspective(img, M, (450,450))

    # Image.fromarray(warp).save(f"./debug/board/board_{dsM.getNextNumber('./debug/board', 'board'):03d}.png")
    
    return warp

# Splits board into cells
def splitCells(warp):
    cells = []
    step = warp.shape[0] // 9

    for y in range(9):
        for x in range(9):
            x1, y1 = x*step, y*step
            x2, y2 = (x+1)*step, (y+1)*step
            cell = warp[y1:y2, x1:x2]
            cells.append(cell)
    
    return cells

# Procecess a cell
def preprocessCell(cell):
    arr = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

    # Otsu thresholding
    _, threshed = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    threshed = cv2.resize(threshed, (28,28), interpolation=cv2.INTER_AREA)

    return threshed

# Procecess all cells
def preprocessCells(cells):
    processed = []

    for cell in cells:
        processedCell = preprocessCell(cell)

        if processedCell is None:
            blank = (np.zeros((28, 28), dtype=np.uint8))
            processed.append(blank)
        else:
            processed.append(processedCell)

    return processed


import torch
from ai.cnn import DigitCNN
from PIL import Image
import torchvision.transforms as transforms

def loadModel(path="ai/digit_cnn_sudoku.pt"):
    model = DigitCNN()

    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()

    return model.to("cpu")

def readDigit(model, cellImg):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    img = Image.fromarray(cellImg)
    tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)
        pred = output.argmax(dim=1).item()

    return pred

def readBoard(model, cellImgs):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    tensors = [transform(Image.fromarray(img)) for img in cellImgs]
    batch = torch.stack(tensors).to("cpu")

    with torch.no_grad():
        outputs = model(batch)
        preds = outputs.argmax(dim=1).cpu().numpy()

    # for img, val in zip(cellImgs, preds):
    #     Image.fromarray(img).save(f"./debug/{val}/{val}_{dsM.getNextNumber(f'./debug/{val}', val):03d}.png")

    return preds.tolist()