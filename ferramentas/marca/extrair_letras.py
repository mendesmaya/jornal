"""Extrai os contornos das letras do título e do menu (TeX Gyre Pagella Bold, licença GUST — livre)
para letras_titulo.json, para que og.py não dependa de tipos de letra instalados.
Uso: python3 extrair_letras.py [caminho/para/texgyrepagella-bold.otf]"""
import json, sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ORIG = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-bold.otf"
CARS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        "ÁÀÂÃÄÇÉÈÊËÍÌÎÏÑÓÒÔÕÖÚÙÛÜáàâãäçéèêëíìîïñóòôõöúùûü"
        " .,;:!?'’«»\"-–—&/()·•+#@%")
f = TTFont(ORIG)
cmap, gs, hm = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
glifos = {}
for c in CARS:
    g = cmap.get(ord(c))
    if g is None:
        continue
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.0f}")
    gs[g].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))  # y para baixo (SVG)
    glifos[c] = {"d": pen.getCommands(), "w": hm[g][0]}
# kerning simples (pares de maiúsculas) a partir da tabela GPOS, se existir
kern = {}
try:
    from fontTools.otlLib.builder import buildPairPosClassesSubtable  # noqa: só para garantir a versão
    gpos = f["GPOS"].table
    rev = {v: k for k, v in cmap.items()}
    for li in gpos.LookupList.Lookup:
        if li.LookupType != 2:
            continue
        for st in li.SubTable:
            if st.Format == 1:
                for i, g1 in enumerate(st.Coverage.glyphs):
                    for pvr in st.PairSet[i].PairValueRecord:
                        v = getattr(pvr.Value1, "XAdvance", 0)
                        a, b = rev.get(g1), rev.get(pvr.SecondGlyph)
                        if v and a and b and chr(a) in glifos and chr(b) in glifos:
                            kern.setdefault(chr(a) + chr(b), v)
            elif st.Format == 2:
                c1, c2 = st.ClassDef1.classDefs, st.ClassDef2.classDefs
                cov = set(st.Coverage.glyphs)
                for a in CARS:
                    ga = cmap.get(ord(a))
                    if ga not in cov:
                        continue
                    for b in CARS:
                        gb = cmap.get(ord(b))
                        if gb is None:
                            continue
                        r = st.Class1Record[c1.get(ga, 0)].Class2Record[c2.get(gb, 0)]
                        v = getattr(r.Value1, "XAdvance", 0)
                        if v:
                            kern.setdefault(a + b, v)
except Exception as ex:
    print("sem kerning:", ex)
kern = {k: v for k, v in kern.items() if k.isupper() or k.replace(" ", "").isupper()}
out = {"fonte": "TeX Gyre Pagella Bold (GUST Font License)", "upm": f["head"].unitsPerEm,
       "altura_maiusculas": getattr(f["OS/2"], "sCapHeight", 692) or 692, "glifos": glifos, "kern": kern}
Path(__file__).with_name("letras_titulo.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print(len(glifos), "glifos,", len(kern), "pares de kerning")
