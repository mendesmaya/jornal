#!/usr/bin/env python3
"""Constrói uma edição a partir de ferramentas/conteudo/AAAA-MM-DD.json
e ferramentas/jogos/AAAA-MM-DD.json, e atualiza o arquivo (index.html).

Uso: python3 ferramentas/construir.py AAAA-MM-DD
"""
import datetime as dt
import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
URL_SITE = "https://mendesmaya.github.io/jornal/"
NOME = "Jornal do Dia"
SUB = "Notícias verificadas, cultura, agenda do Porto e jogos"

SECCOES = {
    "ciberseguranca": ("Cibersegurança", 3),
    "ia": ("Inteligência Artificial", 3),
    "tecnologia": ("Tecnologia", 2),
    "mundo": ("Mundo", 4),
    "portugal": ("Portugal", 4),
}
RUBRICAS = {"cinema": "Cinema em análise", "artista": "Conhece o artista", "sabias": "Sabias que…?", "movimento": "Cultura em movimento"}
TIPOS_IMG = {"acontecimento": "Fotografia do acontecimento", "arquivo": "Imagem de arquivo", "ilustrativa": "Imagem ilustrativa", "oficial": "Imagem oficial / de imprensa", "obra": "Reprodução da obra", "cartaz": "Imagem promocional"}
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
CORES = {"mundo": "#5b6577", "portugal": "#1e4fa8", "ciberseguranca": "#0e7c6f", "ia": "#6a43c4", "tecnologia": "#b2560e", "cultura": "#a8325e"}

e = lambda s: html.escape(str(s or ""), quote=True)


def data_pt(iso, com_dia=True):
    d = dt.date.fromisoformat(iso)
    s = f"{d.day} de {MESES[d.month - 1]} de {d.year}"
    return f"{DIAS[d.weekday()]}, {s}" if com_dia else s


def data_curta(iso):
    if not iso:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", iso):
        d = dt.date.fromisoformat(iso)
        return f"{d.day} {MESES[d.month - 1][:3]}. {d.year}"
    return iso


def slug(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "img"


def reserva_svg(chave, rotulo, destino):
    cor = CORES.get(chave, "#1e4fa8")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500"><defs><pattern id="a" width="80" height="80" patternUnits="userSpaceOnUse"><rect width="80" height="80" fill="{cor}" opacity=".12"/><path d="M40 6 74 40 40 74 6 40Z" fill="none" stroke="{cor}" stroke-width="3" opacity=".55"/><circle cx="40" cy="40" r="9" fill="{cor}" opacity=".7"/><circle cx="0" cy="0" r="9" fill="{cor}" opacity=".35"/><circle cx="80" cy="0" r="9" fill="{cor}" opacity=".35"/><circle cx="0" cy="80" r="9" fill="{cor}" opacity=".35"/><circle cx="80" cy="80" r="9" fill="{cor}" opacity=".35"/></pattern></defs><rect width="800" height="500" fill="#f5f6f3"/><rect width="800" height="500" fill="url(#a)"/><rect x="0" y="390" width="800" height="110" fill="{cor}"/><text x="40" y="460" font-family="Segoe UI,Arial,sans-serif" font-size="44" font-weight="700" fill="#fff">{e(rotulo)}</text></svg>'''
    (destino / f"reserva-{chave}.svg").write_text(svg)
    return f"assets/reserva-{chave}.svg"


def url_remota(img):
    if img.get("commons"):
        nome = img["commons"].replace(" ", "_")
        return "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(nome) + "?width=1000"
    return img["url"]


def figura(img, chave, rotulo, manifest, assets, idx):
    if not img:
        raise SystemExit(f"Falta imagem em: {rotulo}")
    remota = url_remota(img)
    orig = img.get("commons") or urllib.parse.urlparse(img["url"]).path
    ext = Path(orig).suffix.lower() or ".jpg"
    if ext in (".svg", ".tif", ".tiff") and img.get("commons"):
        ext = ".png" if ext == ".svg" else ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"):
        ext = ".jpg"
    ficheiro = f"img/{idx:02d}-{slug(Path(orig).stem)}{ext}"
    manifest.append({"ficheiro": ficheiro, "url": remota})
    reserva = reserva_svg(chave, rotulo, assets)
    local = assets / ficheiro
    src = f"assets/{ficheiro}" if local.exists() else remota
    tipo = TIPOS_IMG.get(img.get("tipo", ""), img.get("tipo", ""))
    autor = img.get("autor", "")
    lic = img.get("licenca", "")
    origem = img.get("origem_url") or (f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(img['commons'].replace(' ', '_'))}" if img.get("commons") else "")
    cred = " · ".join(x for x in [f"Autoria: {e(autor)}" if autor else "", f"Licença: {e(lic)}" if lic else "", f'<a href="{e(origem)}" rel="noopener">origem</a>' if origem else ""] if x)
    leg = f"{e(img['legenda'])}. " if img.get("legenda") else ""
    return (f'<figure class="figura"><div class="moldura"><img src="{e(src)}" data-remota="{e(remota)}" data-reserva="{e(reserva)}" '
            f'alt="{e(img.get("alt", ""))}" loading="lazy" decoding="async" onerror="falhaImagem(this)">'
            f'<span class="tipo-img">{e(tipo)}</span></div><figcaption class="creditos">{leg}{cred}</figcaption></figure>')


def fontes_html(fontes):
    if not fontes:
        raise SystemExit("Item sem fontes")
    links = ", ".join(f'<a href="{e(f["url"])}" rel="noopener">{e(f["nome"])}</a>' for f in fontes)
    return f'<p class="fontes">Fontes: {links}</p>'


def verif_html(v):
    if not v:
        return ""
    n = v.get("independentes", 0)
    txt = "Confirmado por duas fontes independentes" if n >= 2 else "Fonte única"
    if v.get("nota"):
        txt += f": {v['nota']}" if n < 2 else f". {v['nota']}"
    return f'<span class="verif">{e(txt)}</span>'


def noticia(n, principal, manifest, assets, idx, rotulo, chave):
    paras = "".join(f"<p>{e(p)}</p>" for p in n["texto"])
    meta = f'<div class="meta"><span class="estado">{e(n["estado"])}</span><time datetime="{e(n.get("data", ""))}">{e(data_curta(n.get("data", "")))}</time></div>'
    fig = figura(n.get("imagem"), chave, rotulo, manifest, assets, idx)
    corpo = f'{meta}<h3>{e(n["titulo"])}</h3>{paras}{verif_html(n.get("verificacao"))}{fontes_html(n["fontes"])}'
    if principal:
        return f'<article class="noticia principal">{fig}<div>{corpo}</div></article>'
    return f'<article class="noticia">{fig}{corpo}</article>'


def construir(data):
    c = json.loads((BASE / "conteudo" / f"{data}.json").read_text())
    jogos = json.loads((BASE / "jogos" / f"{data}.json").read_text())
    pasta = RAIZ / data
    assets = pasta / "assets"
    (assets / "img").mkdir(parents=True, exist_ok=True)
    manifest = []
    idx = 1

    # validações de estrutura
    cont = {k: 0 for k in SECCOES}
    for n in c["noticias"]:
        cont[n["seccao"]] += 1
    for k, (nome, alvo) in SECCOES.items():
        if cont[k] != alvo:
            raise SystemExit(f"{nome}: {cont[k]} notícias (esperadas {alvo})")
    if sorted(a["rubrica"] for a in c["cultura"]) != sorted(RUBRICAS):
        raise SystemExit("A cultura precisa das quatro rubricas")
    if len(c["agenda"]) != 4:
        raise SystemExit("A agenda precisa de quatro dias")

    def bloco(chave):
        nonlocal idx
        nome, _ = SECCOES[chave]
        itens = [n for n in c["noticias"] if n["seccao"] == chave]
        partes = []
        for i, n in enumerate(itens):
            partes.append(noticia(n, i == 0, manifest, assets, idx, nome, chave))
            idx += 1
        return f'<section class="seccao s-{chave}" id="{chave}"><header><h2>{nome}</h2><span>{len(itens)} notícias</span></header><div class="lista-noticias">{"".join(partes)}</div></section>'

    digital = "".join(bloco(k) for k in ("ciberseguranca", "ia", "tecnologia"))
    resto = "".join(bloco(k) for k in ("mundo", "portugal"))

    arts = []
    for a in sorted(c["cultura"], key=lambda a: list(RUBRICAS).index(a["rubrica"])):
        ficha = ""
        if a.get("ficha"):
            ficha = '<dl class="ficha">' + "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in a["ficha"].items()) + "</dl>"
        paras = "".join(f"<p>{e(p)}</p>" for p in a["texto"])
        fig = figura(a.get("imagem"), "cultura", RUBRICAS[a["rubrica"]], manifest, assets, idx)
        idx += 1
        nota = f'<span class="verif">{e(a["nota"])}</span>' if a.get("nota") else ""
        arts.append(f'<article class="artigo">{fig}<div class="rubrica">{RUBRICAS[a["rubrica"]]}</div><h3>{e(a["titulo"])}</h3>{ficha}{paras}{nota}{fontes_html(a["fontes"])}</article>')
    cultura = f'<section class="seccao s-cultura" id="cultura"><header><h2>Cultura, cinema e arte</h2><span>4 artigos</span></header><div class="cultura-grelha">{"".join(arts)}</div></section>'

    tabs, paineis = [], []
    for i, d in enumerate(c["agenda"]):
        dd = dt.date.fromisoformat(d["dia"])
        rot = ("Hoje, " if i == 0 else "") + f"{DIAS[dd.weekday()].split('-')[0]} {dd.day}"
        tabs.append(f'<button type="button" role="tab" aria-selected="{"true" if i == 0 else "false"}" aria-controls="dia-{d["dia"]}">{e(rot.capitalize())}</button>')
        evs = []
        for ev in d["eventos"]:
            nota = f' <em>{e(ev["nota"])}</em>' if ev.get("nota") else ""
            evs.append(f'<div class="evento"><div class="hora">{e(ev["horario"])}<small>{e(ev.get("tipo", ""))}</small></div><div><h3>{e(ev["nome"])}</h3><p>{e(ev["descricao"])}</p>'
                       f'<div class="det">{e(ev["local"])} · {e(ev["preco"])} · <a href="{e(ev["url"])}" rel="noopener">{e(ev.get("ligacao", "Programação oficial"))}</a>{nota}</div></div></div>')
        paineis.append(f'<div class="dia-agenda" role="tabpanel" id="dia-{d["dia"]}"{"" if i == 0 else " hidden"}><h3 class="sr">{e(data_pt(d["dia"]))}</h3>{"".join(evs)}</div>')
    agenda = (f'<section class="seccao s-agenda" id="agenda"><header><h2>Agenda do Porto</h2><span>{e(data_curta(c["agenda"][0]["dia"]))} a {e(data_curta(c["agenda"][-1]["dia"]))}</span></header>'
              f'<div class="dias" role="tablist" aria-label="Dias da agenda">{"".join(tabs)}</div>{"".join(paineis)}'
              f'<p class="aviso">{e(c.get("agenda_aviso", "Horários, preços e lotação podem mudar. Confirma sempre na programação oficial antes de sair."))}</p></section>')

    teclado = "".join(f'<button type="button" data-v="{v}">{v}</button>' for v in range(1, 10)) + '<button type="button" data-v="0" aria-label="Apagar">⌫</button>'
    jogos_html = f'''<section class="seccao s-jogos" id="jogos"><header><h2>Jogos</h2><span>Desafios novos todos os dias</span></header><div class="jogos-grelha">
<div class="jogo"><h3>Sudoku</h3><p class="instr">Preenche a grelha para que cada linha, coluna e quadrado de 3×3 tenha os números de 1 a 9. Toca numa casa vazia e escolhe o número no teclado (ou usa o teclado do computador). Dificuldade: moderadamente difícil, com solução única.</p>
<div class="barra"><span class="crono parado" id="sudoku-crono" aria-live="off">00:00</span><button class="btn" type="button" id="sudoku-recomecar">Recomeçar</button><button class="btn" type="button" id="sudoku-solucao">Mostrar solução</button></div>
<p class="estado-jogo" id="sudoku-estado" aria-live="polite"></p><div class="sudoku" id="sudoku" role="grid" aria-label="Grelha de Sudoku"></div><div class="teclado" id="sudoku-teclado">{teclado}</div></div>
<div class="jogo"><h3>Caça-palavras</h3><p class="instr">Encontra as 15 palavras escondidas na horizontal, vertical ou diagonal, em qualquer sentido. Arrasta da primeira à última letra, ou toca na primeira e depois na última. Tema: {e(c.get("tema_palavras", "palavras desta edição"))}.</p>
<div class="barra"><span class="crono parado" id="caca-crono" aria-live="off">00:00</span><button class="btn" type="button" id="caca-recomecar">Recomeçar</button><button class="btn" type="button" id="caca-solucao">Mostrar solução</button></div>
<p class="estado-jogo" id="caca-estado" aria-live="polite"></p><div class="caca" id="caca" aria-label="Grelha do caça-palavras"></div><ul class="palavras" id="caca-palavras"></ul></div>
</div></section>'''

    css = (BASE / "estilo.css").read_text()
    js = (BASE / "jogos.js").read_text()
    falha = ("function falhaImagem(i){if(i.dataset.remota&&!i.dataset.tentou){i.dataset.tentou=1;i.src=i.dataset.remota;return}"
             "i.onerror=null;i.src=i.dataset.reserva;var f=i.closest('.figura'),t=f&&f.querySelector('.tipo-img');if(t)t.textContent='Ilustração (imagem original indisponível)'}")
    dia = dt.date.fromisoformat(data)
    destaque = c.get("resumo", "")
    pagina = f'''<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{NOME} · {e(data_pt(data, False))}</title><meta name="description" content="{e(destaque)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400&display=swap" rel="stylesheet">
<style>{css}.sr{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}</style><script>{falha}</script></head><body>
<header class="topo"><div class="azulejo"></div><div class="contentor"><div class="cabeca"><h1 class="marca"><a href="../">{NOME}</a><small>{SUB}</small></h1>
<div class="data-edicao"><div class="dia">{dia.day} {MESES[dia.month - 1][:3]}.</div><div class="resto">{e(DIAS[dia.weekday()].capitalize())}, {dia.year} · Edição n.º {e(c.get("numero", ""))}</div></div></div>
<nav class="indice-sec" aria-label="Secções"><a href="#ciberseguranca">Cibersegurança</a><a href="#ia">IA</a><a href="#tecnologia">Tecnologia</a><a href="#mundo">Mundo</a><a href="#portugal">Portugal</a><a href="#cultura">Cultura</a><a href="#agenda">Agenda do Porto</a><a href="#jogos">Jogos</a><a class="arquivo" href="../">Arquivo</a></nav></div></header>
<main><div class="digital"><div class="contentor"><div class="intro-digital"><h2 class="bloco">Cibersegurança, IA e tecnologia</h2><p>{e(destaque)}</p></div>{digital}</div></div>
<div class="contentor">{resto}{cultura}{agenda}{jogos_html}</div></main>
<footer class="rodape"><div class="contentor"><p>Cada notícia indica o estado da informação (facto confirmado, declaração, proposta, previsão ou anúncio), a data e as fontes consultadas. Procuramos confirmação em duas fontes independentes; quando só há uma, isso fica assinalado. Os textos são sínteses originais. As imagens têm autoria e licença identificadas; imagens de arquivo e ilustrativas estão marcadas como tal.</p>
<p>Edição publicada em <a href="{URL_SITE}{data}/">{URL_SITE}{data}/</a> · <a href="../">Ver todas as edições</a></p></div></footer>
<script type="application/json" id="dados-jogos">{json.dumps(jogos, ensure_ascii=False)}</script><script>{js}</script></body></html>'''
    (pasta / "index.html").write_text(pagina)
    (assets / "imagens.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    atualizar_arquivo(data, c)
    print(f"Edição {data}: {len(manifest)} imagens, {len(pagina)//1024} KB")


def atualizar_arquivo(data, c):
    arq_p = BASE / "arquivo.json"
    arq = json.loads(arq_p.read_text())
    arq = [x for x in arq if x["data"] != data]
    arq.append({"data": data, "numero": c.get("numero", ""), "resumo": c.get("resumo", ""), "formato": "16 notícias · 4 artigos culturais · Agenda do Porto · Sudoku e caça-palavras"})
    arq.sort(key=lambda x: x["data"], reverse=True)
    arq_p.write_text(json.dumps(arq, ensure_ascii=False, indent=1))
    css = (BASE / "estilo.css").read_text()
    itens = []
    for i, x in enumerate(arq):
        n = f" · n.º {e(x['numero'])}" if x.get("numero") else ""
        itens.append(f'<li class="{"novo" if i == 0 else ""}"><div class="d"><a href="./{x["data"]}/">{e(data_pt(x["data"], False))}</a><small>{e(DIAS[dt.date.fromisoformat(x["data"]).weekday()].capitalize())}{n}</small></div>'
                     f'<p>{e(x.get("resumo", ""))}{"<br>" if x.get("resumo") else ""}{e(x.get("formato", ""))}</p></li>')
    pagina = f'''<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{NOME} · Arquivo</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Source+Serif+4:opsz,wght@8..60,400..700&display=swap" rel="stylesheet">
<style>{css}</style></head><body><header class="topo"><div class="azulejo"></div><div class="contentor"><div class="cabeca"><h1 class="marca">{NOME}<small>{SUB}</small></h1>
<div class="data-edicao"><a class="btn" href="./{arq[0]["data"]}/">Abrir a edição mais recente</a></div></div></div></header>
<main class="contentor"><section class="seccao"><header><h2>Arquivo de edições</h2><span>{len(arq)} edições</span></header><ul class="arquivo-lista">{"".join(itens)}</ul></section></main>
<footer class="rodape"><div class="contentor"><p>Cada edição tem endereço permanente no formato {URL_SITE}AAAA-MM-DD/. As edições anteriores a 6 de novembro de 2026 mantêm o formato original.</p></div></footer></body></html>'''
    (RAIZ / "index.html").write_text(pagina)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    construir(sys.argv[1])
