"""Gera a imagem de partilha (Open Graph) de «O Dia em Perspetiva» em estilo desenhado à mão.
Letras desenhadas como traços (sem tipo de letra), com tremor de mão e bordas de tinta."""
import math, random, sys
from pathlib import Path

INK = "#161514"
PAPEL = "#f1ebde"


def catmull(pts, n=10):
    """Curva suave que passa pelos pontos."""
    if len(pts) < 3:
        return pts
    out = []
    p = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


def arco(cx, cy, rx, ry, a0, a1, n=28):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


# glifos: lista de traços; coordenadas com y para cima, altura-x = 1; largura devolvida
def glifo(c):
    o = lambda cx=0.45, rx=0.43: arco(cx, 0.5, rx, 0.5, 95, 455)
    if c == "o":
        return [o()], 0.95
    if c == "a":
        return [arco(0.42, 0.5, 0.4, 0.5, 80, 440), [(0.86, 1.02), (0.86, 0.0)]], 1.0
    if c == "d":
        return [arco(0.42, 0.5, 0.4, 0.5, 80, 440), [(0.86, 1.75), (0.86, 0.0)]], 1.0
    if c == "p":
        return [arco(0.5, 0.5, 0.4, 0.5, -100, 260), [(0.06, 1.02), (0.06, -0.72)]], 1.0
    if c == "e":
        return [[(0.06, 0.52), (0.86, 0.52)] + arco(0.45, 0.5, 0.42, 0.5, 2, 320)[1:]], 0.95
    if c == "i":
        return [[(0.12, 1.0), (0.12, 0.0)], [(0.12, 1.42), (0.13, 1.40)]], 0.3
    if c == "m":
        return [[(0.06, 1.0), (0.06, 0.0)], catmull([(0.06, 0.7), (0.25, 0.98), (0.45, 0.85), (0.5, 0.0)]),
                catmull([(0.5, 0.7), (0.7, 0.98), (0.9, 0.85), (0.95, 0.0)])], 1.08
    if c == "r":
        return [[(0.06, 1.0), (0.06, 0.0)], catmull([(0.06, 0.68), (0.25, 0.95), (0.52, 0.98)])], 0.62
    if c == "s":
        return [catmull([(0.74, 0.86), (0.45, 1.0), (0.12, 0.85), (0.2, 0.6), (0.6, 0.45), (0.76, 0.2), (0.45, 0.0), (0.06, 0.12)])], 0.85
    if c == "t":
        return [catmull([(0.3, 1.55), (0.3, 0.6), (0.33, 0.12), (0.62, 0.02)]), [(0.02, 1.0), (0.66, 1.02)]], 0.72
    if c == "v":
        return [[(0.02, 1.0), (0.42, 0.0), (0.84, 1.02)]], 0.9
    if c == " ":
        return [], 0.55
    raise ValueError(c)


def amostrar(pts, passo=0.04):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        n = max(1, int(d / passo))
        for k in range(1, n + 1):
            out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return out


def tremer(pts, rng, amp):
    """Tremor de mão: ruído suave (baixa frequência) ao longo do traço."""
    fase = [rng.uniform(0, 6.28) for _ in range(4)]
    out = []
    for k, (x, y) in enumerate(pts):
        t = k / max(1, len(pts) - 1)
        dx = amp * (math.sin(t * 5 + fase[0]) + 0.5 * math.sin(t * 13 + fase[1]))
        dy = amp * (math.sin(t * 6 + fase[2]) + 0.5 * math.sin(t * 11 + fase[3]))
        out.append((x + dx, y + dy))
    return out


def palavra_svg(texto, x0, base, esc, rng, largura_traco, espaco=0.12):
    """Devolve (paths, largura total em px)."""
    paths, x = [], x0
    for ch in texto:
        tracos, w = glifo(ch)
        rot = rng.uniform(-4, 4)
        dy = rng.uniform(-0.05, 0.05)
        cx = x + w * esc / 2
        for tr in tracos:
            pts = tremer(amostrar(tr), rng, 0.018)
            pp = []
            for (gx, gy) in pts:
                px, py = x + gx * esc, base - (gy + dy) * esc
                # rodar a letra à volta do centro
                a = math.radians(rot)
                rx, ry = px - cx, py - (base - 0.5 * esc)
                pp.append((cx + rx * math.cos(a) - ry * math.sin(a), base - 0.5 * esc + rx * math.sin(a) + ry * math.cos(a)))
            if len(pp) == 2 and math.dist(*pp) < 4:  # ponto do i
                (px, py) = pp[0]
                paths.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{largura_traco * 0.62:.1f}" fill="{INK}"/>')
                continue
            d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pp)
            paths.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{largura_traco * rng.uniform(0.92, 1.08):.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
        x += (w + espaco) * esc
    return paths, x - x0 - espaco * esc


def mancha(cx, cy, r, rng, n=60, irreg=0.06):
    pts = []
    f = [rng.uniform(0, 6.28) for _ in range(3)]
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (1 + irreg * (math.sin(3 * a + f[0]) + 0.6 * math.sin(5 * a + f[1]) + 0.4 * math.sin(9 * a + f[2])) / 2)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def traco(pts, rng, w, amp=1.2):
    pp = tremer(amostrar(pts, 3), rng, amp)
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pp)
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'


def marca(cx, horizonte, r, rng):
    """Sol a nascer sobre o horizonte, com linhas de fuga (perspetiva)."""
    el = []
    # sol: meia mancha cheia acima do horizonte
    pts = [p for p in mancha(cx, horizonte, r, rng, 90, 0.05) if p[1] <= horizonte + 1]
    pts.sort(key=lambda p: math.atan2(p[1] - horizonte, p[0] - cx))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
    el.append(f'<path d="{d}" fill="{INK}"/>')
    # raios: traços curtos e irregulares
    for k in range(9):
        a = math.radians(180 + 12 + k * (156 / 8) + rng.uniform(-3, 3))
        r1, r2 = r * rng.uniform(1.28, 1.36), r * rng.uniform(1.62, 1.78)
        el.append(traco([(cx + r1 * math.cos(a), horizonte + r1 * math.sin(a)), (cx + r2 * math.cos(a), horizonte + r2 * math.sin(a))], rng, r * 0.11, 0.6))
    # horizonte
    L = r * 3.1
    el.append(traco([(cx - L, horizonte + rng.uniform(-2, 2)), (cx, horizonte), (cx + L, horizonte + rng.uniform(-2, 2))], rng, r * 0.085, 1.5))
    # linhas de fuga: caminho a convergir para o ponto de fuga (base do sol)
    for (bx, k) in ((-1.15, 1), (1.15, 1), (-0.45, 0.7), (0.45, 0.7)):
        el.append(traco([(cx + bx * L * 0.62, horizonte + r * 1.15 * k), (cx + bx * 0.04 * L, horizonte + 4)], rng, r * (0.075 if k == 1 else 0.055), 1.0))
    return el


def svg_variante(var, seed=7):
    rng = random.Random(seed)
    W, H = 1200, 630
    el = []
    filtro = ('<filter id="tinta" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/>'
              '<feDisplacementMap in="SourceGraphic" scale="3.2"/></filter>'
              '<filter id="grao"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" seed="9"/><feColorMatrix values="0 0 0 0 0.35 0 0 0 0 0.3 0 0 0 0 0.22 0 0 0 0.08 0"/></filter>')
    def largura(txt, esc):
        return palavra_svg(txt, 0, 0, esc, random.Random(0), 1)[1]
    if var == "A":
        el += marca(600, 205, 66, rng)
        esc = min(70, 1000 / (largura("o dia em perspetiva", 1)))
        w = largura("o dia em perspetiva", esc)
        p, _ = palavra_svg("o dia em perspetiva", (W - w) / 2, 440, esc, random.Random(seed + 1), esc * 0.14)
        el += p
        sub = '<text x="600" y="530" text-anchor="middle" font-family="Inter" font-weight="700" font-size="21" letter-spacing="6" fill="#161514">JORNAL DIÁRIO · PORTUGAL · FEITO COM IA</text>'
    else:
        el += marca(250, 330, 74, rng)
        x0 = 505
        esc = min(92, (1130 - x0) / largura("perspetiva", 1))
        p1, _ = palavra_svg("o dia em", x0, 300, esc, random.Random(seed + 2), esc * 0.14)
        p2, _ = palavra_svg("perspetiva", x0, 300 + esc * 1.75, esc, random.Random(seed + 3), esc * 0.14)
        el += p1 + p2
        sub = f'<text x="{x0 + 4}" y="{300 + esc * 1.75 + esc * 1.25:.0f}" font-family="Inter" font-weight="700" font-size="20" letter-spacing="5" fill="#161514">JORNAL DIÁRIO · PORTUGAL</text>'
    corpo = "".join(el)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{filtro}</defs>'
            f'<rect width="{W}" height="{H}" fill="{PAPEL}"/><g filter="url(#tinta)">{corpo}{sub}</g>'
            f'<rect width="{W}" height="{H}" filter="url(#grao)"/></svg>')


if __name__ == "__main__":
    out = Path(sys.argv[1])
    for v in ("A", "B"):
        (out / f"og-{v}.svg").write_text(svg_variante(v))
