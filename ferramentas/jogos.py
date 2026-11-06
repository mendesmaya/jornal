#!/usr/bin/env python3
"""Gera os jogos diários (Sudoku e caça-palavras) e valida-os.

Uso: python3 ferramentas/jogos.py AAAA-MM-DD PALAVRA1 PALAVRA2 ... (15 palavras)
Escreve ferramentas/jogos/AAAA-MM-DD.json e regista as grelhas em
ferramentas/historico_jogos.json para evitar repetições.
"""
import hashlib
import json
import random
import sys
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
HIST = BASE / "historico_jogos.json"

# ---------------------------------------------------------------- Sudoku
UNITS = []
for i in range(9):
    UNITS.append([i * 9 + j for j in range(9)])
    UNITS.append([j * 9 + i for j in range(9)])
for br in range(3):
    for bc in range(3):
        UNITS.append([(br * 3 + r) * 9 + bc * 3 + c for r in range(3) for c in range(3)])
PEERS = [set() for _ in range(81)]
CELL_UNITS = [[] for _ in range(81)]
for u in UNITS:
    for c in u:
        CELL_UNITS[c].append(u)
        PEERS[c].update(x for x in u if x != c)


def count_solutions(grid, limit=2):
    g = list(grid)
    count = 0

    def solve():
        nonlocal count
        best, cands = -1, None
        for i in range(81):
            if g[i] == 0:
                c = {1, 2, 3, 4, 5, 6, 7, 8, 9} - {g[p] for p in PEERS[i]}
                if not c:
                    return
                if cands is None or len(c) < len(cands):
                    best, cands = i, c
                    if len(c) == 1:
                        break
        if best == -1:
            count += 1
            return
        for v in cands:
            g[best] = v
            solve()
            if count >= limit:
                break
        g[best] = 0

    solve()
    return count


def full_grid(rng):
    g = [0] * 81

    def fill(i=0):
        if i == 81:
            return True
        if g[i]:
            return fill(i + 1)
        vals = list(range(1, 10))
        rng.shuffle(vals)
        for v in vals:
            if all(g[p] != v for p in PEERS[i]):
                g[i] = v
                if fill(i + 1):
                    return True
        g[i] = 0
        return False

    fill()
    return g


def logic_solve(grid, techniques):
    """Resolve só com lógica. Devolve (resolvido, técnicas usadas)."""
    cand = [set() if v else {1, 2, 3, 4, 5, 6, 7, 8, 9} - {grid[p] for p in PEERS[i]} for i, v in enumerate(grid)]
    g = list(grid)
    used = set()

    def place(i, v):
        g[i] = v
        cand[i] = set()
        for p in PEERS[i]:
            cand[p].discard(v)

    progress = True
    while progress:
        progress = False
        for i in range(81):
            if not g[i] and len(cand[i]) == 1:
                place(i, next(iter(cand[i])))
                used.add("simples")
                progress = True
        if progress:
            continue
        if "ocultos" in techniques:
            for u in UNITS:
                for v in range(1, 10):
                    spots = [c for c in u if v in cand[c]]
                    if len(spots) == 1:
                        place(spots[0], v)
                        used.add("ocultos")
                        progress = True
            if progress:
                continue
        if "pares" in techniques:
            for u in UNITS:
                pairs = [c for c in u if len(cand[c]) == 2]
                for a in range(len(pairs)):
                    for b in range(a + 1, len(pairs)):
                        if cand[pairs[a]] == cand[pairs[b]]:
                            pv = cand[pairs[a]]
                            for c in u:
                                if c not in (pairs[a], pairs[b]) and cand[c] & pv:
                                    cand[c] -= pv
                                    used.add("pares")
                                    progress = True
            # interseções (pointing / claiming)
            for bu in UNITS[18:]:
                for v in range(1, 10):
                    spots = [c for c in bu if v in cand[c]]
                    if len(spots) < 2:
                        continue
                    for line in UNITS[:18]:
                        if all(s in line for s in spots):
                            for c in line:
                                if c not in bu and v in cand[c]:
                                    cand[c].discard(v)
                                    used.add("intersecoes")
                                    progress = True
    return all(g), used


def make_sudoku(rng, seen):
    for _ in range(400):
        sol = full_grid(rng)
        puz = list(sol)
        cells = list(range(81))
        rng.shuffle(cells)
        for c in cells:
            if sum(1 for v in puz if v) <= 24:
                break
            keep = puz[c]
            puz[c] = 0
            if count_solutions(puz) != 1:
                puz[c] = keep
        clues = sum(1 for v in puz if v)
        if not 24 <= clues <= 29:
            continue
        easy, _ = logic_solve(puz, {"ocultos"})
        ok, used = logic_solve(puz, {"ocultos", "pares"})
        # moderadamente difícil: exige técnicas além de simples/ocultos,
        # mas resolve-se sem tentativa-erro
        if easy or not ok:
            continue
        key = hashlib.sha256("".join(map(str, puz)).encode()).hexdigest()
        if key in seen:
            continue
        assert count_solutions(puz) == 1
        return puz, sol, clues, sorted(used), key
    raise SystemExit("Não foi possível gerar um Sudoku com a dificuldade pretendida")


# ---------------------------------------------------------- Caça-palavras
DIRS = [(0, 1), (1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)]
LETTERS = "AAAAABCCDEEEEFGHIIIIJLMMNNOOOOOPQRRRSSSSTTTUUUVXZ"


def norm(word):
    w = unicodedata.normalize("NFD", word.upper())
    w = "".join(ch for ch in w if unicodedata.category(ch) != "Mn")
    return "".join(ch for ch in w if ch.isalpha())


def make_wordsearch(words, rng, seen, size=15):
    clean = [norm(w) for w in words]
    if len(clean) != 15 or len(set(clean)) != 15:
        raise SystemExit("São precisas 15 palavras diferentes")
    if max(map(len, clean)) > size:
        raise SystemExit("Palavra demasiado longa para a grelha")
    order = sorted(range(15), key=lambda i: -len(clean[i]))
    for _ in range(500):
        grid = [[""] * size for _ in range(size)]
        placements = {}
        ok = True
        for i in order:
            w = clean[i]
            opts = []
            for dr, dc in DIRS:
                for r in range(size):
                    for c in range(size):
                        er, ec = r + dr * (len(w) - 1), c + dc * (len(w) - 1)
                        if not (0 <= er < size and 0 <= ec < size):
                            continue
                        cells = [(r + dr * k, c + dc * k) for k in range(len(w))]
                        if all(grid[y][x] in ("", w[k]) for k, (y, x) in enumerate(cells)):
                            overlap = sum(1 for k, (y, x) in enumerate(cells) if grid[y][x] == w[k])
                            opts.append((overlap, rng.random(), cells))
            if not opts:
                ok = False
                break
            opts.sort(key=lambda o: (-o[0] if rng.random() < 0.3 else 0, o[1]))
            cells = opts[0][2]
            for k, (y, x) in enumerate(cells):
                grid[y][x] = w[k]
            placements[i] = cells
        if not ok:
            continue
        dirs_used = {(placements[i][1][0] - placements[i][0][0], placements[i][1][1] - placements[i][0][1]) for i in placements}
        if len(dirs_used) < 5:
            continue
        for y in range(size):
            for x in range(size):
                if not grid[y][x]:
                    grid[y][x] = rng.choice(LETTERS)
        # validação: cada palavra aparece exatamente onde foi colocada (e só uma vez)
        flat = ["".join(row) for row in grid]
        valid = True
        for i, w in enumerate(clean):
            if "".join(grid[y][x] for y, x in placements[i]) != w:
                valid = False
            hits = 0
            for dr, dc in DIRS:
                for r in range(size):
                    for c in range(size):
                        er, ec = r + dr * (len(w) - 1), c + dc * (len(w) - 1)
                        if 0 <= er < size and 0 <= ec < size and all(flat[r + dr * k][c + dc * k] == w[k] for k in range(len(w))):
                            hits += 1
            if hits != 1:
                valid = False
        if not valid:
            continue
        key = hashlib.sha256("".join(flat).encode()).hexdigest()
        if key in seen:
            continue
        return {
            "tamanho": size,
            "grelha": flat,
            "palavras": [{"mostrar": words[i].upper(), "procurar": clean[i], "celulas": [y * size + x for y, x in placements[i]]} for i in range(15)],
        }, key
    raise SystemExit("Não foi possível colocar as palavras")


def main():
    if len(sys.argv) != 17:
        raise SystemExit(__doc__)
    date, words = sys.argv[1], sys.argv[2:]
    hist = json.loads(HIST.read_text()) if HIST.exists() else {"sudoku": {}, "caca": {}}
    rng = random.Random(f"jornal-{date}-{random.SystemRandom().random()}")
    seen_s = {v for k, v in hist["sudoku"].items() if k != date}
    seen_c = {v for k, v in hist["caca"].items() if k != date}
    puz, sol, clues, used, skey = make_sudoku(rng, seen_s)
    caca, ckey = make_wordsearch(words, rng, seen_c)
    hist["sudoku"][date] = skey
    hist["caca"][date] = ckey
    out = {"sudoku": {"puzzle": puz, "solucao": sol, "pistas": clues, "tecnicas": used}, "caca": caca}
    (BASE / "jogos").mkdir(exist_ok=True)
    (BASE / "jogos" / f"{date}.json").write_text(json.dumps(out, ensure_ascii=False))
    HIST.write_text(json.dumps(hist, indent=1, sort_keys=True))
    print(f"Sudoku: {clues} pistas, solução única, técnicas {used}. Caça-palavras 15x15 com 15 palavras validadas.")


if __name__ == "__main__":
    main()
