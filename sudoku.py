import math
from itertools import combinations
import pyautogui

def refactorBoard(board):
    size = int(math.sqrt(len(board)))
    if size * size != len(board):
        return []
    return [board[i*size:(i+1)*size] for i in range(size)]

def getcandidates(board):
        size = len(board)
        boxsize = int(size ** 0.5)
        numbers = set(range(1, size+1))
        cands = [[set(numbers) for _ in range(size)] for _ in range(size)]

        for r in range(size):
            for c in range(size):
                if board[r][c] != 0:
                    cands[r][c] = set()
                else:
                    rowVals = set(board[r])
                    colVals = {board[x][c] for x in range(size)}
                    br, bc = (r // boxsize) * boxsize, (c // boxsize) * boxsize
                    boxVals = {board[rr][cc] for rr in range(br, br + boxsize) for cc in range(bc, bc + boxsize)}
                    cands[r][c] -= (rowVals | colVals | boxVals)
        return cands

def solveBoard(board):
    size = len(board)
    boxsize = int(size ** 0.5)

    solvedBoard = [row[:] for row in board]
    solvedEmpties = [[0 for _ in row] for row in board]

    candidates = getcandidates(board)

    # Remove candidate from row, col, and box
    def removecandidates(r, c, val, candidates):
        for cc in range(size):
            if val in candidates[r][cc]:
                candidates[r][cc].discard(val)
        for rr in range(size):
            if val in candidates[rr][c]:
                candidates[rr][c].discard(val)
        br, bc = (r // 3) * 3, (c // 3) * 3
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if val in candidates[i][j]:
                    candidates[i][j].discard(val)

    progress = True
    while progress:
        progress = False

        # --- Naked Singles ---
        for r in range(size):
            for c in range(size):
                if solvedBoard[r][c] == 0 and len(candidates[r][c]) == 1:
                    val = next(iter(candidates[r][c]))

                    solvedBoard[r][c] = val
                    solvedEmpties[r][c] = val
                    candidates[r][c].clear()

                    removecandidates(r, c, val, candidates)

                    progress = True
        
        # --- Hidden Singles ---
        def HiddenSingles(cell_coords):
            nonlocal progress, solvedBoard

            # map: digit -> list of cells where it's a candidate
            digit_map = {d: [] for d in range(1, size+1)}

            for (r, c) in cell_coords:
                for d in candidates[r][c]:
                    digit_map[d].append((r, c))

            # if a digit appears only once, it must go there
            for d, locs in digit_map.items():
                if len(locs) == 1:
                    r, c = locs[0]
                    candidates[r][c] = {d}
                    progress = True

        # --- Naked Pairs ---
        def NakedPairs(cell_coords):
            nonlocal progress

            # finds cells with exactly 2 candidates
            digit_map = {}
            for (r, c) in cell_coords:
                if len(candidates[r][c]) == 2:
                    key = tuple(sorted(candidates[r][c]))
                    digit_map.setdefault(key, []).append((r, c))

            # any key with exactly two locations is a naked pair
            for key, locs in digit_map.items():
                if len(locs) == 2:
                    pair_vals = set(key)
                    for (r, c) in cell_coords:
                        if (r, c) not in locs and (candidates[r][c] & pair_vals):
                            before = set(candidates[r][c])
                            candidates[r][c] -= pair_vals
                            if candidates[r][c] != before:
                                progress = True
        
        # --- Naked Triples ---
        def NakedTriples(cell_coords):
            nonlocal progress

            # consider cells with 2–3 candidates
            cells = [(r, c) for (r, c) in cell_coords if 2 <= len(candidates[r][c]) <= 3]

            for combo in combinations(cells, 3):
                sets = [candidates[r][c] for (r, c) in combo]
                union = set().union(*sets)

                if len(union) == 3:
                    # found a naked triple
                    for (r, c) in cell_coords:
                        if (r, c) not in combo and (candidates[r][c] & union):
                            before = set(candidates[r][c])
                            candidates[r][c] -= union
                            if candidates[r][c] != before:
                                progress = True

        # --- Hidden Pairs ---
        def HiddenPairs(cell_coords):
            nonlocal progress

            # map each digit to its candidate cells in this unit
            digit_map = {d: [] for d in range(1, size+1)}
            for (r, c) in cell_coords:
                for d in candidates[r][c]:
                    digit_map[d].append((r, c))

            # check all pairs of digits
            for d1, d2 in combinations(range(1, size+1), 2):
                locs1, locs2 = digit_map[d1], digit_map[d2]
                if len(locs1) == 2 and locs1 == locs2:
                    # hidden pair found in these two cells
                    pair_vals = {d1, d2}
                    for (r, c) in locs1:
                        before = set(candidates[r][c])
                        candidates[r][c] &= pair_vals  # strip all others
                        if candidates[r][c] != before:
                            progress = True

        # --- Hidden Triples ---
        def HiddenTriples(cell_coords):
            nonlocal progress
            
            # Digits 1..9 (generalize to size if needed)
            for digits in combinations(range(1, size+1), 3):
                # Collect where these digits appear
                digit_map = set()
                for d in digits:
                    for (r, c) in cell_coords:
                        if d in candidates[r][c]:
                            digit_map.add((r, c))

                # Condition: exactly 3 cells for these 3 digits
                if len(digit_map) == 3:
                    # Now check if all 3 digits actually appear across these cells
                    appearing_digits = set()
                    for (r, c) in digit_map:
                        appearing_digits |= candidates[r][c]
                    appearing_digits &= set(digits)  # restrict to the triple

                    if len(appearing_digits) == 3:
                        # Hidden Triple found: prune other digits
                        for (r, c) in digit_map:
                            before = set(candidates[r][c])
                            candidates[r][c] &= set(digits)
                            if candidates[r][c] != before:
                                progress = True
        
        # --- Naked Quads ---
        def NakedQuads(cell_coords):
            nonlocal progress

            # Gather unsolvedBoard cells with <= 4 candidates (otherwise can’t be in a quad)
            quad_candidates = [(r, c) for (r, c) in cell_coords if 2 <= len(candidates[r][c]) <= 4]

            for combo in combinations(quad_candidates, 4):
                union = set()
                for (r, c) in combo:
                    union |= candidates[r][c]

                # Condition for Naked Quad: union has exactly 4 digits
                if len(union) == 4:
                    # Check if all 4 chosen cells are subsets of this union
                    if all(candidates[r][c].issubset(union) for (r, c) in combo):
                        # Then eliminate these 4 digits from all *other* cells in this unit
                        for (r, c) in cell_coords:
                            if (r, c) not in combo:
                                before = set(candidates[r][c])
                                candidates[r][c] -= union
                                if candidates[r][c] != before:
                                    progress = True

        # --- Hidden Quads ---
        def HiddenQuads(cell_coords):
            nonlocal progress
            
            # Digits 1..9 (generalize to size if needed)
            for digits in combinations(range(1, size+1), 4):
                # Collect where these digits appear
                digit_map = set()
                for d in digits:
                    for (r, c) in cell_coords:
                        if d in candidates[r][c]:
                            digit_map.add((r, c))

                # Condition: exactly 4 cells for these 4 digits
                if len(digit_map) == 4:
                    # Now check if all 4 digits actually appear across these cells
                    appearing_digits = set()
                    for (r, c) in digit_map:
                        appearing_digits |= candidates[r][c]
                    appearing_digits &= set(digits)  # restrict to the triple

                    if len(appearing_digits) == 4:
                        # Hidden Quad found: prune other digits
                        for (r, c) in digit_map:
                            before = set(candidates[r][c])
                            candidates[r][c] &= set(digits)
                            if candidates[r][c] != before:
                                progress = True

        # --- Pointing Pairs ---
        def PointingPairs(cell_coords):
            nonlocal progress
            digits = range(1, size+1)

            for d in digits:
                # collect all cells in this unit containing d
                d_cells = [(r, c) for (r, c) in cell_coords if d in candidates[r][c]]
                if len(d_cells) < 2:
                    continue

                # if all candidates for d in this box are in the same row
                rows = {r for (r, c) in d_cells}
                if len(rows) == 1:
                    row = rows.pop()
                    for c in range(size):
                        if (row, c) not in d_cells and (row, c) not in cell_coords:
                            if d in candidates[row][c]:
                                candidates[row][c].discard(d)
                                progress = True

                # if all candidates for d in this box are in the same column
                cols = {c for (r, c) in d_cells}
                if len(cols) == 1:
                    col = cols.pop()
                    for r in range(size):
                        if (r, col) not in d_cells and (r, col) not in cell_coords:
                            if d in candidates[r][col]:
                                candidates[r][col].discard(d)
                                progress = True

        # --- Box/Line Reduction ---
        def BoxLineReduction(cell_coords):
            nonlocal progress
            digits = range(1, size+1)

            for d in digits:
                # find all cells in this unit containing d
                d_cells = [(r, c) for (r, c) in cell_coords if d in candidates[r][c]]
                if len(d_cells) < 2:
                    continue

                # check if all these cells are inside the same box
                box_rows = {r // boxsize for (r, c) in d_cells}
                box_cols = {c // boxsize for (r, c) in d_cells}
                if len(box_rows) == 1 and len(box_cols) == 1:
                    # single box
                    box_r = box_rows.pop() * boxsize
                    box_c = box_cols.pop() * boxsize

                    # eliminate d from the rest of this box
                    for r in range(box_r, box_r + boxsize):
                        for c in range(box_c, box_c + boxsize):
                            if (r, c) not in d_cells and (r, c) not in cell_coords:
                                if d in candidates[r][c]:
                                    candidates[r][c].discard(d)
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
        for r in range(size):
            cells = [(r, c) for c in range(size) if solvedBoard[r][c] == 0]
            ApplyRules(cells)

            if not progress:
                BoxLineReduction(cells)

        # Columns
        for c in range(size):
            cells = [(r, c) for r in range(size) if solvedBoard[r][c] == 0]
            ApplyRules(cells)

            if not progress:
                BoxLineReduction(cells)

        # Boxes
        for br in range(0, size, 3):
            for bc in range(0, size, 3):
                cells = [(r, c)
                         for r in range(br, br + 3)
                         for c in range(bc, bc + 3)
                         if solvedBoard[r][c] == 0]
                ApplyRules(cells)

                if not progress:
                    PointingPairs(cells)
    
    def isValidGrid(Grid):
        for i in range(size):
            row_vals = [x for x in Grid[i] if x != 0]
            if len(row_vals) != len(set(row_vals)):
                return False
            col_vals = [Grid[r][i] for r in range(size) if Grid[r][i] != 0]
            if len(col_vals) != len(set(col_vals)):
                return False
        for br in range(0, size, boxsize):
            for bc in range(0, size, boxsize):
                vals = []
                for r in range(br, br+boxsize):
                    for c in range(bc, bc+boxsize):
                        if Grid[r][c] != 0:
                            vals.append(Grid[r][c])
                if len(vals) != len(set(vals)):
                    return False
        return True
    
    # --- 🔥 Bowman’s Bingo ---
    isSolved = all(all(cell != 0 for cell in row) for row in solvedBoard)
    if not isSolved:

        min_cands = size + 1
        target = None
        for r in range(size):
            for c in range(size):
                if solvedBoard[r][c] == 0 and 1 < len(candidates[r][c]) < min_cands:
                    min_cands = len(candidates[r][c])
                    target = (r, c)


        if target:
            r, c = target
            for guess in list(candidates[r][c]):
                print("Guessing at ", target, "= ", guess)

                new_matrix = [row[:] for row in solvedBoard]
                new_matrix[r][c] = guess

                if not isValidGrid(new_matrix):
                    print("Not valid")
                    continue  # prune early
                
                print("Retrying with new matrix: ", new_matrix)

                resultBoard, resultEmpties = solveBoard(new_matrix)

                print("Result: ", resultBoard)

                if all(all(cell != 0 for cell in row) for row in resultBoard):
                    resultBoard[r][c] = guess

                    return resultBoard, resultEmpties
        
        # if all guesses fail → dead end
        print("Dead end 😒")
        return solvedBoard, solvedEmpties

    return solvedBoard, solvedEmpties


def FillBoard(solvedEmpties, boardCorner, cellSize):
    size = len(solvedEmpties)

    for r in range(size):
        for c in range(size):
            val = solvedEmpties[r][c]

            if val != 0:
                retry = True
                tries = 0

                pixelX = boardCorner[0] + (cellSize / 2) + (cellSize * c)
                pixelY = boardCorner[1] + (cellSize / 2) + (cellSize * r)

                while retry and tries < 4:
                    retry = False
                    tries += 1

                    pyautogui.click(pixelX, pixelY)
                    pyautogui.press(str(val))