from pyautogui import *
import pyautogui
import pyscreeze
import time
import keyboard
import random
import win32api, win32con
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
import cv2
import numpy as np
from itertools import combinations

CenterCoord = (495, 377) # Center pixel of the board
DistanceToBig = 161 # Distance from center of big square to another
CellSize = 52 # Size of each cell

# 9x9 Matrix with the center pixel of each cell
def getCellsPixels():
    Squares = [[None for _ in range(9)] for _ in range(9)]

    for row in range(9):
        for col in range(9):
            # local offsets relative to the center of the grid
            dx = (col - 4) * CellSize + ((col // 3) - 1) * (DistanceToBig - 3 * CellSize)
            dy = (row - 4) * CellSize + ((row // 3) - 1) * (DistanceToBig - 3 * CellSize)

            # calculate the actual square center
            squareCenter = (CenterCoord[0] + dx, CenterCoord[1] + dy)

            Squares[row][col] = squareCenter

    return Squares

# Makes image 1 or 0
def Binarize(pil_img):
    arr = np.array(pil_img)   # PIL → numpy
    # Otsu threshold automatically finds a cutoff between background & digit
    _, threshed = cv2.threshold(arr, 100, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(threshed)

def readCell(x, y, img):
    if not img:
        img = pyautogui.screenshot()

    half = int(CellSize // 2)

    # Crop a region (x, y, width, height)
    cell_img = img.crop((x - half, y - half, x + half, y + half))

    gray = cell_img.convert("L")
    bw = Binarize(gray)
    bw_big = bw.resize((bw.width * 2, bw.height * 2), Image.LANCZOS)

    text = pytesseract.image_to_string(bw_big, config="--psm 10 -c tessedit_char_whitelist=123456789").strip()
    if not text.isdigit():
        text = pytesseract.image_to_string(bw_big, config="--psm 13 -c tessedit_char_whitelist=123456789").strip()
        if not text.isdigit():
            text = pytesseract.image_to_string(bw_big, config="--psm 6 -c tessedit_char_whitelist=123456789").strip()
            if not text.isdigit():
                bw_big.save(f"debug_x{x}_y{y}.png")

    if not text.isdigit():
        val = 0
    else:
        val = int(text)

    # Sanity check: if val is 7 but pixel intensity is mostly white, ignore
    if val == 7 and np.mean(np.array(bw)) > 245:
        val = 0
        bw_big.save(f"debug_x{x}_y{y}_San7.png")

    # Sanity check: if val is 0 but pixel intensity is mostly black, make it 9
    if val == 0 and np.mean(np.array(bw)) < 226:
        val = 9
        bw_big.save(f"debug_x{x}_y{y}_San9.png")

    return val

# Using a screenshot, crops the cell, and reads the number
def readBoard(Squares):
    img = pyautogui.screenshot()
    # img = Image.open("Board1.png")
    board = [[0 for _ in range(9)] for _ in range(9)]
    
    for r in range(9):
        for c in range(9):
            x, y = Squares[r][c]

            board[r][c] = readCell(x, y, img)

    return board

def getCandidates(Grid):
        Size = len(Grid)
        BoxSize = int(Size ** 0.5)
        Numbers = set(range(1, Size+1))
        Cands = [[set(Numbers) for _ in range(Size)] for _ in range(Size)]

        for r in range(Size):
            for c in range(Size):
                if Grid[r][c] != 0:
                    Cands[r][c] = set()
                else:
                    row_vals = set(Grid[r])
                    col_vals = {Grid[x][c] for x in range(Size)}
                    br, bc = (r//BoxSize)*BoxSize, (c//BoxSize)*BoxSize
                    box_vals = {Grid[rr][cc] for rr in range(br, br+BoxSize) 
                                            for cc in range(bc, bc+BoxSize)}
                    Cands[r][c] -= (row_vals | col_vals | box_vals)
        return Cands

# 
def Solve(Matrix):
    Size = len(Matrix)
    BoxSize = int(Size ** 0.5)
    Numbers = set(range(1, Size+1))
    Solved = [row[:] for row in Matrix]
    SolvedEmpties = [[0 for _ in row] for row in Matrix]
    
    # remove val from row, col, and box candidate sets
    def removeFromPeers(r, c, val, Candidates):
        for cc in range(Size):
            if val in Candidates[r][cc]:
                Candidates[r][cc].discard(val)
        for rr in range(Size):
            if val in Candidates[rr][c]:
                Candidates[rr][c].discard(val)
        br, bc = (r // 3) * 3, (c // 3) * 3
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if val in Candidates[i][j]:
                    Candidates[i][j].discard(val)

    Candidates = getCandidates(Matrix)

    progress = True
    while progress:
        progress = False

        # --- Naked Singles ---
        for r in range(Size):
            for c in range(Size):
                if Solved[r][c] == 0 and len(Candidates[r][c]) == 1:
                    val = next(iter(Candidates[r][c]))
                    Solved[r][c] = val
                    SolvedEmpties[r][c] = val
                    Candidates[r][c].clear()
                    removeFromPeers(r, c, val, Candidates)
                    progress = True
        
        # --- Hidden Singles ---
        def HiddenSingles(cell_coords):
            nonlocal progress, Solved

            # map: digit -> list of cells where it's a candidate
            digit_map = {d: [] for d in range(1, Size+1)}

            for (r, c) in cell_coords:
                for d in Candidates[r][c]:
                    digit_map[d].append((r, c))

            # if a digit appears only once, it must go there
            for d, locs in digit_map.items():
                if len(locs) == 1:
                    r, c = locs[0]
                    Candidates[r][c] = {d}
                    progress = True

        # --- Naked Pairs ---
        def NakedPairs(cell_coords):
            nonlocal progress

            # finds cells with exactly 2 candidates
            digit_map = {}
            for (r, c) in cell_coords:
                if len(Candidates[r][c]) == 2:
                    key = tuple(sorted(Candidates[r][c]))
                    digit_map.setdefault(key, []).append((r, c))

            # any key with exactly two locations is a naked pair
            for key, locs in digit_map.items():
                if len(locs) == 2:
                    pair_vals = set(key)
                    for (r, c) in cell_coords:
                        if (r, c) not in locs and (Candidates[r][c] & pair_vals):
                            before = set(Candidates[r][c])
                            Candidates[r][c] -= pair_vals
                            if Candidates[r][c] != before:
                                progress = True
        
        # --- Naked Triples ---
        def NakedTriples(cell_coords):
            nonlocal progress

            # consider cells with 2–3 candidates
            cells = [(r, c) for (r, c) in cell_coords if 2 <= len(Candidates[r][c]) <= 3]

            for combo in combinations(cells, 3):
                sets = [Candidates[r][c] for (r, c) in combo]
                union = set().union(*sets)

                if len(union) == 3:
                    # found a naked triple
                    for (r, c) in cell_coords:
                        if (r, c) not in combo and (Candidates[r][c] & union):
                            before = set(Candidates[r][c])
                            Candidates[r][c] -= union
                            if Candidates[r][c] != before:
                                progress = True

        # --- Hidden Pairs ---
        def HiddenPairs(cell_coords):
            nonlocal progress

            # map each digit to its candidate cells in this unit
            digit_map = {d: [] for d in range(1, Size+1)}
            for (r, c) in cell_coords:
                for d in Candidates[r][c]:
                    digit_map[d].append((r, c))

            # check all pairs of digits
            for d1, d2 in combinations(range(1, Size+1), 2):
                locs1, locs2 = digit_map[d1], digit_map[d2]
                if len(locs1) == 2 and locs1 == locs2:
                    # hidden pair found in these two cells
                    pair_vals = {d1, d2}
                    for (r, c) in locs1:
                        before = set(Candidates[r][c])
                        Candidates[r][c] &= pair_vals  # strip all others
                        if Candidates[r][c] != before:
                            progress = True

        # --- Hidden Triples ---
        def HiddenTriples(cell_coords):
            nonlocal progress
            
            # Digits 1..9 (generalize to Size if needed)
            for digits in combinations(range(1, Size+1), 3):
                # Collect where these digits appear
                digit_map = set()
                for d in digits:
                    for (r, c) in cell_coords:
                        if d in Candidates[r][c]:
                            digit_map.add((r, c))

                # Condition: exactly 3 cells for these 3 digits
                if len(digit_map) == 3:
                    # Now check if all 3 digits actually appear across these cells
                    appearing_digits = set()
                    for (r, c) in digit_map:
                        appearing_digits |= Candidates[r][c]
                    appearing_digits &= set(digits)  # restrict to the triple

                    if len(appearing_digits) == 3:
                        # Hidden Triple found: prune other digits
                        for (r, c) in digit_map:
                            before = set(Candidates[r][c])
                            Candidates[r][c] &= set(digits)
                            if Candidates[r][c] != before:
                                progress = True
        
        # --- Naked Quads ---
        def NakedQuads(cell_coords):
            nonlocal progress

            # Gather unsolved cells with <= 4 candidates (otherwise can’t be in a quad)
            quad_candidates = [(r, c) for (r, c) in cell_coords if 2 <= len(Candidates[r][c]) <= 4]

            for combo in combinations(quad_candidates, 4):
                union = set()
                for (r, c) in combo:
                    union |= Candidates[r][c]

                # Condition for Naked Quad: union has exactly 4 digits
                if len(union) == 4:
                    # Check if all 4 chosen cells are subsets of this union
                    if all(Candidates[r][c].issubset(union) for (r, c) in combo):
                        # Then eliminate these 4 digits from all *other* cells in this unit
                        for (r, c) in cell_coords:
                            if (r, c) not in combo:
                                before = set(Candidates[r][c])
                                Candidates[r][c] -= union
                                if Candidates[r][c] != before:
                                    progress = True

        # --- Hidden Quads ---
        def HiddenQuads(cell_coords):
            nonlocal progress
            
            # Digits 1..9 (generalize to Size if needed)
            for digits in combinations(range(1, Size+1), 4):
                # Collect where these digits appear
                digit_map = set()
                for d in digits:
                    for (r, c) in cell_coords:
                        if d in Candidates[r][c]:
                            digit_map.add((r, c))

                # Condition: exactly 4 cells for these 4 digits
                if len(digit_map) == 4:
                    # Now check if all 4 digits actually appear across these cells
                    appearing_digits = set()
                    for (r, c) in digit_map:
                        appearing_digits |= Candidates[r][c]
                    appearing_digits &= set(digits)  # restrict to the triple

                    if len(appearing_digits) == 4:
                        # Hidden Quad found: prune other digits
                        for (r, c) in digit_map:
                            before = set(Candidates[r][c])
                            Candidates[r][c] &= set(digits)
                            if Candidates[r][c] != before:
                                progress = True

        # --- Pointing Pairs ---
        def PointingPairs(cell_coords):
            nonlocal progress
            digits = range(1, Size+1)

            for d in digits:
                # collect all cells in this unit containing d
                d_cells = [(r, c) for (r, c) in cell_coords if d in Candidates[r][c]]
                if len(d_cells) < 2:
                    continue

                # if all candidates for d in this box are in the same row
                rows = {r for (r, c) in d_cells}
                if len(rows) == 1:
                    row = rows.pop()
                    for c in range(Size):
                        if (row, c) not in d_cells and (row, c) not in cell_coords:
                            if d in Candidates[row][c]:
                                Candidates[row][c].discard(d)
                                progress = True

                # if all candidates for d in this box are in the same column
                cols = {c for (r, c) in d_cells}
                if len(cols) == 1:
                    col = cols.pop()
                    for r in range(Size):
                        if (r, col) not in d_cells and (r, col) not in cell_coords:
                            if d in Candidates[r][col]:
                                Candidates[r][col].discard(d)
                                progress = True

        # --- Box/Line Reduction ---
        def BoxLineReduction(cell_coords):
            nonlocal progress
            digits = range(1, Size+1)

            for d in digits:
                # find all cells in this unit containing d
                d_cells = [(r, c) for (r, c) in cell_coords if d in Candidates[r][c]]
                if len(d_cells) < 2:
                    continue

                # check if all these cells are inside the same box
                box_rows = {r // BoxSize for (r, c) in d_cells}
                box_cols = {c // BoxSize for (r, c) in d_cells}
                if len(box_rows) == 1 and len(box_cols) == 1:
                    # single box
                    box_r = box_rows.pop() * BoxSize
                    box_c = box_cols.pop() * BoxSize

                    # eliminate d from the rest of this box
                    for r in range(box_r, box_r + BoxSize):
                        for c in range(box_c, box_c + BoxSize):
                            if (r, c) not in d_cells and (r, c) not in cell_coords:
                                if d in Candidates[r][c]:
                                    Candidates[r][c].discard(d)
                                    progress = True

        def ApplyRules(cell_coords):
            nonlocal progress

            # Hidden Singles
            HiddenSingles(cell_coords)
            if progress:
                return

            # Naked Pairs
            NakedPairs(cell_coords)
            if progress:
                return

            # Naked Triples
            NakedTriples(cell_coords)
            if progress:
                return

            # Hidden Pairs
            HiddenPairs(cell_coords)
            if progress:
                return

            # Hidden Triples
            HiddenTriples(cell_coords)
            if progress:
                return

            # Naked Quads
            NakedQuads(cell_coords)
            if progress:
                return
            
            # Hidden Quads
            HiddenQuads(cell_coords)
            if progress:
                return
        
        # Rows
        for r in range(Size):
            cells = [(r, c) for c in range(Size) if Solved[r][c] == 0]
            ApplyRules(cells)

            if not progress:
                BoxLineReduction(cells)

        # Columns
        for c in range(Size):
            cells = [(r, c) for r in range(Size) if Solved[r][c] == 0]
            ApplyRules(cells)

            if not progress:
                BoxLineReduction(cells)

        # Boxes
        for br in range(0, Size, 3):
            for bc in range(0, Size, 3):
                cells = [(r, c)
                         for r in range(br, br + 3)
                         for c in range(bc, bc + 3)
                         if Solved[r][c] == 0]
                ApplyRules(cells)

                if not progress:
                    PointingPairs(cells)
    
    def isValidGrid(Grid):
        for i in range(Size):
            row_vals = [x for x in Grid[i] if x != 0]
            if len(row_vals) != len(set(row_vals)):
                return False
            col_vals = [Grid[r][i] for r in range(Size) if Grid[r][i] != 0]
            if len(col_vals) != len(set(col_vals)):
                return False
        for br in range(0, Size, BoxSize):
            for bc in range(0, Size, BoxSize):
                vals = []
                for r in range(br, br+BoxSize):
                    for c in range(bc, bc+BoxSize):
                        if Grid[r][c] != 0:
                            vals.append(Grid[r][c])
                if len(vals) != len(set(vals)):
                    return False
        return True
    
    # --- 🔥 Bowman’s Bingo ---
    solved = all(all(cell != 0 for cell in row) for row in Solved)
    if not solved:

        min_cands = Size + 1
        target = None
        for r in range(Size):
            for c in range(Size):
                if Solved[r][c] == 0 and 1 < len(Candidates[r][c]) < min_cands:
                    min_cands = len(Candidates[r][c])
                    target = (r, c)


        if target:
            r, c = target
            for guess in list(Candidates[r][c]):
                print("Guessing at ", target, "= ", guess)

                new_matrix = [row[:] for row in Solved]
                new_matrix[r][c] = guess

                if not isValidGrid(new_matrix):
                    print("Not valid")
                    continue  # prune early
                
                print("Retrying with new matrix: ", new_matrix)

                result = Solve(new_matrix)
                fullBoard_result = MergeBoards(new_matrix, result)

                print("Result: ", result)

                if all(all(cell != 0 for cell in row) for row in fullBoard_result):
                    print("Solved")
                    result[r][c] = guess
                    final_result = MergeBoards(SolvedEmpties, result)

                    return final_result
        # if all guesses fail → dead end
        print("Dead end 😒")
        return SolvedEmpties

    return SolvedEmpties

# Fills the gaps (0) of Matrix1, by the numbers in Matrix2
def MergeBoards(Matrix1, Matrix2):
    Merged = []
    
    for row_m1, row_m2 in zip(Matrix1, Matrix2):
        MergedRow = []

        for c1, c2 in zip(row_m1, row_m2):
            if c1 != 0:
                MergedRow.append(c1)
            else:
                MergedRow.append(c2)
        Merged.append(MergedRow)

    return Merged

# 
def FillBoard(Pixels, Matrix, Squares):
    Size = len(Matrix)
    for r in range(Size):
        for c in range(Size):
            val = Matrix[r][c]
            if val != 0:
                retry = True
                tries = 0

                while retry and tries < 4:
                    retry = False
                    tries += 1

                    pyautogui.click(Pixels[r][c][0], Pixels[r][c][1])
                    time.sleep(0.3)
                    keyboard.press_and_release(str(val))
                    time.sleep(0.1)

                    x, y = Squares[r][c]
                    if val != readCell(x, y, None):
                        retry = True

                    time.sleep(0.4)

# --- MAIN ---
CellsPixels = getCellsPixels()

print("Press 's' to start")

# Wait for start
keyboard.wait("s")

pyautogui.click(1, 1)

print("Reading board...")
Board = readBoard(CellsPixels)
Size = len(Board)

print('Board: ', Board, '\n')

print("Solving...")
SolvedEmpties = Solve(Board)

print('Solved Cells: ', SolvedEmpties, '\n')

print('Final Board: ', MergeBoards(Board, SolvedEmpties), '\n')

print("Filling board...")
FillBoard(CellsPixels, SolvedEmpties, CellsPixels)