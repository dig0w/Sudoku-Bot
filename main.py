# Install Requirements
# pip install -r requirements.txt

import numpy as np
from PIL import Image
import pyautogui
import keyboard
import time
import readBoard
import sudoku

if __name__ == "__main__":
    print("Press 's' to start")

    # Wait for start
    keyboard.wait("s")
    # Or
    # time.sleep(2)

    # Start timer
    startTime = time.time()
    readBoardTime = startTime
    solvedBoardTime = startTime

    # img = Image.open("data/test_screenshot_30.png")
    img = pyautogui.screenshot()
    
    # LINUX USERS
    def screenshot(path="screenshot.png"):
        import os
        # Replace command with the respective one
        os.system(f"spectacle -n -f -b -o {path}")
        return Image.open(path)
    # img = screenshot()

    # Loads an image
    imgNA, thresh = readBoard.loadImage(img)

    # Finds the board
    boardContour = readBoard.findBoard(thresh)

    if boardContour is not None:
        # top-left, top-right, bottom-right, bottom-left
        pts = boardContour.reshape(4, 2)
        boardCorner = (int(pts[0,0]), int(pts[0,1]))

        width  = np.linalg.norm(pts[3,0] - pts[0,0])
        height = np.linalg.norm(pts[2,1] - pts[0,1])

        cellSize = int(((width / 9) + (height / 9)) / 2)

        # Cuts the board
        boardImg = readBoard.warpBoard(imgNA, boardContour)

        # Cuts all cells
        cells = readBoard.splitCells(boardImg)

        # Processes Cells
        processedCells = readBoard.preprocessCells(cells)

        # Loads CNN Model
        model = readBoard.loadModel()

        # Reads the board
        board = readBoard.readBoard(model, processedCells)

        readBoardTime = time.time()

        # Makes it a matrix
        board = sudoku.refactorBoard(board)

        print(f"\nBoard: {board}")

        # Solves the sudoku
        solvedBoard, solvedEmpties = sudoku.solveBoard(board)

        print(f"\nSolved Board: {solvedBoard}")

        solvedBoardTime = time.time()

        # Fills the board
        print(f"\nboardCorner: {boardCorner}")
        print(f"\ncellSize: {cellSize}")

        isSolved = all(all(cell != 0 for cell in row) for row in solvedBoard)
        if isSolved:
            sudoku.FillBoard(solvedEmpties, boardCorner, cellSize)

    # End timer
    endTime = time.time()

    print(f"\nTotal Time: {endTime - startTime:.6f} seconds")
    print(f"\nRead Board Time: {readBoardTime - startTime:.6f} seconds")
    print(f"\nSolve Time: {solvedBoardTime - startTime:.6f} seconds")