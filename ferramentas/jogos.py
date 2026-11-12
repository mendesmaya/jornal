#!/usr/bin/env python3
"""Gera os jogos diários (Sudoku e caça-palavras) e valida-os.

Uso: python3 ferramentas/jogos.py AAAA-MM-DD [PALAVRA1 … PALAVRA15]
Os jogos mudam com o dia da semana (ver JOGOS_DIA). As 15 palavras só são
usadas quando há caça-palavras (segunda-feira); nos outros dias são ignoradas.
Para testes: --jogos=sudoku,2048 antes da data força uma combinação.
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
    """Dificuldade média: 30–34 pistas, resolve-se só com «simples» e «ocultos»
    (sem pares nem interseções), mas não só com «simples»."""
    for _ in range(600):
        sol = full_grid(rng)
        puz = list(sol)
        alvo = rng.randint(30, 33)
        cells = list(range(81))
        rng.shuffle(cells)
        for c in cells:
            if sum(1 for v in puz if v) <= alvo:
                break
            keep = puz[c]
            puz[c] = 0
            if count_solutions(puz) != 1:
                puz[c] = keep
        clues = sum(1 for v in puz if v)
        if not 30 <= clues <= 34:
            continue
        so_simples, _ = logic_solve(puz, set())
        ok, used = logic_solve(puz, {"ocultos"})
        if so_simples or not ok:
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


# ------------------------------------------------------------- Rotação
# 0=segunda … 6=domingo (a partir de INICIO_ROTACAO; antes disso, sempre sudoku + caça-palavras)
INICIO_ROTACAO = "2026-11-12"
JOGOS_DIA = {
    0: ["sudoku", "caca"],
    1: ["diferencas", "2048"],
    2: ["sudoku", "nonograma"],
    3: ["minas", "cobra"],
    4: ["2048", "sudoku"],
    5: ["dino", "puzzle"],
    6: ["quiz"],
}


# ------------------------------------------------------------- Nonograma
def line_options(clue, n):
    """Todas as colocações possíveis de uma pista numa linha de n células."""
    if clue == [0] or not clue:
        return [tuple([0] * n)]
    res = []

    def rec(i, pos, acc):
        if i == len(clue):
            res.append(tuple(acc + [0] * (n - len(acc))))
            return
        rest = sum(clue[i + 1:]) + len(clue) - i - 1
        for start in range(pos, n - rest - clue[i] + 1):
            rec(i + 1, start + clue[i] + 1, acc + [0] * (start - len(acc)) + [1] * clue[i] + ([0] if i < len(clue) - 1 else []))

    rec(0, 0, [])
    return [r[:n] for r in res if len(r) >= n]


def clues_of(line):
    out, k = [], 0
    for v in line:
        if v:
            k += 1
        elif k:
            out.append(k)
            k = 0
    if k:
        out.append(k)
    return out or [0]


def nono_line_solve(rows, cols, n):
    """Resolve só por lógica de linhas. Devolve a grelha ou None se ficar ambíguo."""
    g = [[-1] * n for _ in range(n)]
    ropts = [line_options(c, n) for c in rows]
    copts = [line_options(c, n) for c in cols]
    changed = True
    while changed:
        changed = False
        for axis in (0, 1):
            opts = ropts if axis == 0 else copts
            for i in range(n):
                cur = [g[i][j] if axis == 0 else g[j][i] for j in range(n)]
                opts[i] = [o for o in opts[i] if all(c == -1 or c == o[j] for j, c in enumerate(cur))]
                if not opts[i]:
                    return None
                for j in range(n):
                    if cur[j] == -1:
                        vals = {o[j] for o in opts[i]}
                        if len(vals) == 1:
                            v = vals.pop()
                            if axis == 0:
                                g[i][j] = v
                            else:
                                g[j][i] = v
                            changed = True
    if any(-1 in r for r in g):
        return None
    return g


def make_nonogram(rng, seen, n=10):
    for _ in range(3000):
        g = [[1 if rng.random() < 0.52 else 0 for _ in range(n)] for _ in range(n)]
        for _ in range(1):  # suavizar para formar manchas em vez de ruído
            h = [[0] * n for _ in range(n)]
            for r in range(n):
                for c in range(n):
                    viz = [g[y][x] for y in range(r - 1, r + 2) for x in range(c - 1, c + 2) if 0 <= y < n and 0 <= x < n]
                    h[r][c] = 1 if sum(viz) * 2 > len(viz) else (g[r][c] if sum(viz) * 2 == len(viz) else 0)
            g = h
        dens = sum(map(sum, g)) / (n * n)
        if not 0.42 <= dens <= 0.65:
            continue
        rows = [clues_of(r) for r in g]
        cols = [clues_of([g[r][c] for r in range(n)]) for c in range(n)]
        if any(r == [0] for r in rows) or any(c == [0] for c in cols):
            continue
        # dificuldade: pelo menos 5 linhas/colunas com 3 ou mais blocos
        if sum(1 for x in rows + cols if len(x) >= 3) < 5:
            continue
        sol = nono_line_solve(rows, cols, n)
        if sol != g:
            continue
        flat = "".join(str(v) for r in g for v in r)
        key = hashlib.sha256(flat.encode()).hexdigest()
        if key in seen:
            continue
        return {"tamanho": n, "linhas": rows, "colunas": cols, "solucao": flat}, key
    raise SystemExit("Não foi possível gerar um nonograma com solução lógica única")


# ------------------------------------------------- Jogo das diferenças
CEUS = ["#bfe3f5", "#cfe8f7", "#f6d9b8", "#d9d2f0"]
CHAOS = ["#8cc084", "#9bc27a", "#c9b27c", "#7fb38a"]
CORES = ["#d1495b", "#edae49", "#00798c", "#30638e", "#6a4c93", "#f4845f", "#2a9d8f", "#e9c46a", "#264653", "#8d5a97", "#f28482", "#588157"]


def make_differences(rng, seen, W=480, H=320, ndif=7):
    for _ in range(400):
        el = []  # cada elemento: {"p": [primitivas], "bb": [x,y,w,h], "tipo": str, "mexe": [tipos de diferença]}

        def add(prims, bb, tipo, mexe):
            el.append({"p": prims, "bb": bb, "tipo": tipo, "mexe": mexe})

        chao_y = rng.randint(215, 240)
        add([{"t": "rect", "x": 0, "y": 0, "w": W, "h": chao_y, "f": rng.choice(CEUS)}], [0, 0, W, chao_y], "ceu", [])
        add([{"t": "rect", "x": 0, "y": chao_y, "w": W, "h": H - chao_y, "f": rng.choice(CHAOS)}], [0, chao_y, W, H - chao_y], "chao", [])
        sx, sy, sr = rng.randint(30, W - 30), rng.randint(28, 60), rng.randint(16, 24)
        add([{"t": "circ", "x": sx, "y": sy, "r": sr, "f": "#f9c74f"}], [sx - sr, sy - sr, 2 * sr, 2 * sr], "sol", ["falta", "cor", "tamanho"])
        for _ in range(rng.randint(2, 3)):
            cx, cy = rng.randint(40, W - 60), rng.randint(30, 95)
            prims = [{"t": "circ", "x": cx + dx, "y": cy + dy, "r": r, "f": "#ffffff"} for dx, dy, r in ((0, 0, 14), (16, -6, 17), (33, 0, 13))]
            add(prims, [cx - 14, cy - 23, 60, 37], "nuvem", ["falta", "mover", "tamanho"])
        # casas e árvores ao longo do chão, sem sobreposição
        x = rng.randint(8, 30)
        while x < W - 70:
            if rng.random() < 0.6:
                w, h = rng.randint(70, 95), rng.randint(55, 80)
                if x + w > W - 8:
                    break
                y = chao_y - h + 12
                corpo = rng.choice(CORES)
                add([{"t": "rect", "x": x, "y": y, "w": w, "h": h, "f": corpo}], [x, y, w, h], "casa", [])
                tel = rng.choice([c for c in CORES if c != corpo])
                add([{"t": "poly", "pts": [[x - 6, y], [x + w / 2, y - rng.randint(28, 40)], [x + w + 6, y]], "f": tel}], [x - 6, y - 40, w + 12, 40], "telhado", ["cor"])
                if rng.random() < 0.5:
                    cxm = x + w - 22
                    add([{"t": "rect", "x": cxm, "y": y - 30, "w": 10, "h": 22, "f": "#6d4c41"}], [cxm, y - 30, 10, 22], "chamine", ["falta"])
                pw, ph = 16, 26
                px = x + rng.randint(8, w - pw - 8)
                add([{"t": "rect", "x": px, "y": y + h - ph, "w": pw, "h": ph, "f": rng.choice(["#5d4037", "#3e2723", "#8d6e63"])}], [px, y + h - ph, pw, ph], "porta", ["cor", "falta"])
                for jx in (x + 8, x + w - 26):
                    if abs(jx - px) < 22:
                        continue
                    add([{"t": "rect", "x": jx, "y": y + 12, "w": 18, "h": 16, "f": "#fff8dc"}], [jx, y + 12, 18, 16], "janela", ["cor", "falta"])
                x += w + rng.randint(18, 40)
            else:
                tr = rng.randint(18, 26)
                tx = x + tr
                if tx + tr > W - 8:
                    break
                add([{"t": "rect", "x": tx - 4, "y": chao_y - 30, "w": 8, "h": 32, "f": "#795548"}], [tx - 4, chao_y - 30, 8, 32], "tronco", [])
                add([{"t": "circ", "x": tx, "y": chao_y - 30 - tr + 6, "r": tr, "f": rng.choice(["#2d6a4f", "#40916c", "#52b788", "#1b4332"])}],
                    [tx - tr, chao_y - 24 - 2 * tr, 2 * tr, 2 * tr], "copa", ["cor", "tamanho"])
                x += 2 * tr + rng.randint(14, 34)
        for _ in range(rng.randint(5, 8)):
            fx, fy = rng.randint(12, W - 12), rng.randint(chao_y + 22, H - 14)
            cor = rng.choice(CORES)
            add([{"t": "rect", "x": fx - 1, "y": fy, "w": 2, "h": 12, "f": "#2d6a4f"}, {"t": "circ", "x": fx, "y": fy, "r": 7, "f": cor},
                 {"t": "circ", "x": fx, "y": fy, "r": 3, "f": "#fff3b0"}], [fx - 7, fy - 7, 14, 19], "flor", ["cor", "falta"])
        # escolher diferenças bem separadas
        cand = [i for i, e in enumerate(el) if e["mexe"]]
        rng.shuffle(cand)
        escolhidas, alvos = [], []
        for i in cand:
            bx, by, bw, bh = el[i]["bb"]
            cx, cy, r = bx + bw / 2, by + bh / 2, max(18, max(bw, bh) / 2 + 6)
            if any((cx - ax) ** 2 + (cy - ay) ** 2 < (r + ar + 4) ** 2 for ax, ay, ar in alvos):
                continue
            tipos = el[i]["mexe"]
            escolhidas.append((i, rng.choice(tipos)))
            alvos.append((cx, cy, r))
            if len(escolhidas) == ndif:
                break
        if len(escolhidas) < ndif or len({el[i]["tipo"] for i, _ in escolhidas}) < 4:
            continue
        import copy
        b = copy.deepcopy(el)
        for i, tipo in escolhidas:
            e = b[i]
            if tipo == "falta":
                e["p"] = []
            elif tipo == "cor":
                for pr in e["p"]:
                    if pr["f"] not in ("#fff3b0", "#2d6a4f") or e["tipo"] != "flor":
                        pr["f"] = rng.choice([c for c in CORES + ["#ffffff", "#f9c74f"] if c != pr["f"]])
                        if e["tipo"] == "flor":
                            break
            elif tipo == "tamanho":
                bx, by, bw, bh = e["bb"]
                cx, cy, k = bx + bw / 2, by + bh / 2, rng.choice([0.6, 1.35])
                for pr in e["p"]:
                    if pr["t"] == "circ":
                        pr["x"], pr["y"], pr["r"] = cx + (pr["x"] - cx) * k, cy + (pr["y"] - cy) * k, pr["r"] * k
            elif tipo == "mover":
                d = rng.choice([-30, 30])
                for pr in e["p"]:
                    pr["x"] += d
        flat_a = [pr for e in el for pr in e["p"]]
        flat_b = [pr for e in b for pr in e["p"]]
        key = hashlib.sha256(json.dumps(flat_a, sort_keys=True).encode()).hexdigest()
        if key in seen:
            continue
        rnd = lambda prims: [{k: (round(v, 1) if isinstance(v, float) else ([[round(a, 1), round(c, 1)] for a, c in v] if k == "pts" else v)) for k, v in pr.items()} for pr in prims]
        return {"largura": W, "altura": H, "a": rnd(flat_a), "b": rnd(flat_b),
                "alvos": [[round(x, 1), round(y, 1), round(r, 1)] for x, y, r in alvos],
                "tipos": [el[i]["tipo"] + ":" + t for i, t in escolhidas]}, key
    raise SystemExit("Não foi possível gerar o jogo das diferenças")


def main():
    args = sys.argv[1:]
    forcar = None
    if args and args[0].startswith("--jogos="):
        forcar = args.pop(0).split("=", 1)[1].split(",")
    if not args:
        raise SystemExit(__doc__)
    date, words = args[0], args[1:]
    dia = __import__("datetime").date.fromisoformat(date)
    lista = forcar or (JOGOS_DIA[dia.weekday()] if date >= INICIO_ROTACAO else ["sudoku", "caca"])
    hist = json.loads(HIST.read_text()) if HIST.exists() else {}
    for k in ("sudoku", "caca", "nonograma", "diferencas"):
        hist.setdefault(k, {})
    rng = random.Random(f"jornal-{date}-{random.SystemRandom().random()}")
    seen = lambda k: {v for d, v in hist[k].items() if d != date}
    out, resumo = {"lista": lista}, []
    for jogo in lista:
        if jogo == "sudoku":
            puz, sol, clues, used, skey = make_sudoku(rng, seen("sudoku"))
            hist["sudoku"][date] = skey
            out["sudoku"] = {"puzzle": puz, "solucao": sol, "pistas": clues, "tecnicas": used}
            resumo.append(f"Sudoku: {clues} pistas, solução única, técnicas {used}")
        elif jogo == "caca":
            if len(words) != 15:
                raise SystemExit("O caça-palavras precisa de 15 palavras")
            caca, ckey = make_wordsearch(words, rng, seen("caca"))
            hist["caca"][date] = ckey
            out["caca"] = caca
            resumo.append("Caça-palavras 15x15 com 15 palavras validadas")
        elif jogo == "nonograma":
            nono, nkey = make_nonogram(rng, seen("nonograma"))
            hist["nonograma"][date] = nkey
            out["nonograma"] = nono
            resumo.append("Nonograma 10x10 com solução lógica única")
        elif jogo == "diferencas":
            dif, dkey = make_differences(rng, seen("diferencas"))
            hist["diferencas"][date] = dkey
            out["diferencas"] = dif
            resumo.append(f"Jogo das diferenças: {len(dif['alvos'])} diferenças ({', '.join(dif['tipos'])})")
        elif jogo in ("2048", "minas", "cobra", "dino"):
            out[jogo] = {"semente": rng.randrange(1, 2 ** 31)}
            if jogo == "minas":
                out[jogo].update({"linhas": 10, "colunas": 10, "minas": 15})
            resumo.append(f"{jogo}: semente do dia")
        elif jogo == "puzzle":
            n = 4
            while True:
                perm = list(range(n * n))
                rng.shuffle(perm)
                if all(perm[i] != i for i in range(n * n)):
                    break
            out["puzzle"] = {"n": n, "ordem": perm}
            resumo.append("Puzzle 4x4 com a imagem da manchete")
        elif jogo == "quiz":
            resumo.append("Quiz: perguntas vêm do conteúdo da edição (campo «quiz»)")
        else:
            raise SystemExit(f"Jogo desconhecido: {jogo}")
    (BASE / "jogos").mkdir(exist_ok=True)
    (BASE / "jogos" / f"{date}.json").write_text(json.dumps(out, ensure_ascii=False))
    HIST.write_text(json.dumps(hist, indent=1, sort_keys=True))
    print(f"{DIAS_PT[dia.weekday()]}: " + " · ".join(resumo))


DIAS_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

if __name__ == "__main__":
    main()
