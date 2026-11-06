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
NOME = "O Dia em Perspetiva"
SUB = "Notícias verificadas · Cultura · Agenda do Porto · Passatempos"
FONTES = ("https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&family=Playfair+Display:ital,wght@0,600..900;1,600..700"
          "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400&display=swap")

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

CREDITOS = {}
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
    reserva = reserva_svg(chave, rotulo, assets)
    manifest.append({"id": idx, "ficheiro": ficheiro, "url": remota, "commons": img.get("commons", ""), "reserva": reserva})
    local = assets / ficheiro
    src = f"assets/{ficheiro}" if local.exists() else remota
    tipo = TIPOS_IMG.get(img.get("tipo", ""), img.get("tipo", ""))
    autor = img.get("autor", "")
    lic = img.get("licenca", "")
    origem = img.get("origem_url") or (f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(img['commons'].replace(' ', '_'))}" if img.get("commons") else "")
    cr = CREDITOS.get(ficheiro)
    if cr and cr.get("estado") == "ok":
        autor, lic, origem = cr["autor"], cr["licenca"], cr["origem"]
    if cr and cr.get("estado") == "falhou":
        src, tipo, autor, lic, origem = reserva, "Ilustração do jornal (imagem original indisponível)", "O Dia em Perspetiva", "uso livre", ""
    if img.get("commons") and not autor:
        # autoria e licença são preenchidas pela ação do GitHub a partir da API do Commons
        cred = f'Imagem: Wikimedia Commons · <a href="{e(origem)}" rel="noopener">ver autoria e licença</a>'
    else:
        cred = " · ".join(x for x in [f"Autoria: {e(autor)}" if autor else "", f"Licença: {e(lic)}" if lic else "", f'<a href="{e(origem)}" rel="noopener">origem</a>' if origem else ""] if x)
    leg = f"{e(img['legenda'])}. " if img.get("legenda") else ""
    return (f'<figure class="figura"><div class="moldura"><img id="img-{idx:02d}" src="{e(src)}" data-remota="{e(remota)}" data-reserva="{e(reserva)}" '
            f'alt="{e(img.get("alt", ""))}" loading="lazy" decoding="async" onerror="falhaImagem(this)">'
            f'<span class="tipo-img" id="tipo-{idx:02d}">{e(tipo)}</span></div><figcaption class="creditos">{leg}<span class="cred" id="cred-{idx:02d}">{cred}</span></figcaption></figure>')


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


def data_num(iso):
    try:
        d = dt.date.fromisoformat(iso)
        return f"{d.day:02d}/{d.month:02d}/{d.year}"
    except Exception:
        return iso or ""


def noticia(n, num, etiqueta, manifest, assets, idx, rotulo, chave):
    paras = "".join(f"<p>{e(p)}</p>" for p in n["texto"])
    fig = figura(n.get("imagem"), chave, rotulo, manifest, assets, idx)
    meta = (f'<p class="meta"><span class="estado">{e(n["estado"])}</span> · Data: '
            f'<time datetime="{e(n.get("data", ""))}">{e(data_num(n.get("data", "")))}</time></p>')
    return (f'<article class="card"><span class="tag">{num:02d} / {e(etiqueta)}</span><h3>{e(n["titulo"])}</h3>{fig}'
            f'<div class="corpo">{paras}</div><div class="rodape-noticia">{fontes_html(n["fontes"])}{verif_html(n.get("verificacao"))}{meta}</div></article>')


def construir(data):
    c = json.loads((BASE / "conteudo" / f"{data}.json").read_text())
    jogos = json.loads((BASE / "jogos" / f"{data}.json").read_text())
    pasta = RAIZ / data
    assets = pasta / "assets"
    (assets / "img").mkdir(parents=True, exist_ok=True)
    manifest = []
    idx = 1
    cp = assets / "creditos.json"
    if cp.exists():
        CREDITOS.update(json.loads(cp.read_text()))

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

    def seccao(sid, titulo, chaves, contagem):
        nonlocal idx
        cartoes, num = [], 1
        for chave in chaves:
            nome, total = SECCOES[chave]
            itens = [n for n in c["noticias"] if n["seccao"] == chave]
            for i, n in enumerate(itens, 1):
                etiqueta = f"{nome} {i}/{total}" if len(chaves) > 1 else nome
                cartoes.append(noticia(n, num, etiqueta, manifest, assets, idx, nome, chave))
                idx += 1
                num += 1
        ancoras = "".join(f'<span id="{k}"></span>' for k in chaves if k != sid)
        return (f'<section class="newssection" id="{sid}">{ancoras}<h2>{titulo}</h2><p class="edition-count">{contagem}</p>'
                f'<div class="grid">{"".join(cartoes)}</div></section>')

    digital = seccao("tecnologia", "Tecnologia, IA e Cibersegurança", ["ciberseguranca", "ia", "tecnologia"],
                     "08 notícias · 3 cibersegurança · 3 IA · 2 tecnologia")
    resto = seccao("mundo", "Mundo", ["mundo"], "04 notícias") + seccao("portugal", "Portugal", ["portugal"], "04 notícias")

    arts = []
    for num, a in enumerate(sorted(c["cultura"], key=lambda a: list(RUBRICAS).index(a["rubrica"])), 1):
        ficha = ""
        if a.get("ficha"):
            ficha = '<dl class="ficha">' + "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in a["ficha"].items()) + "</dl>"
        paras = "".join(f"<p>{e(p)}</p>" for p in a["texto"])
        fig = figura(a.get("imagem"), "cultura", RUBRICAS[a["rubrica"]], manifest, assets, idx)
        idx += 1
        nota = f'<span class="verif">{e(a["nota"])}</span>' if a.get("nota") else ""
        arts.append(f'<article class="card"><span class="tag">{num:02d} / {RUBRICAS[a["rubrica"]]}</span><h3>{e(a["titulo"])}</h3>{fig}'
                    f'<div class="corpo">{ficha}{paras}</div><div class="rodape-noticia">{fontes_html(a["fontes"])}{nota}</div></article>')
    cultura = (f'<section class="newssection" id="cultura"><h2>Cultura, Cinema e Arte</h2><p class="edition-count">04 artigos · cinema · artista · curiosidade · cultura em movimento</p>'
               f'<div class="grid">{"".join(arts)}</div></section>')

    dias_html, menu_dias = [], []
    for i, d in enumerate(c["agenda"]):
        dd = dt.date.fromisoformat(d["dia"])
        evs = []
        for ev in d["eventos"]:
            nota = f'<small class="nota-ev">{e(ev["nota"])}</small>' if ev.get("nota") else ""
            evs.append(f'<div class="event"><small class="ev-hora">{e(ev["horario"])} · {e(ev.get("tipo", ""))}</small><strong>{e(ev["nome"])}</strong>'
                       f'<p class="ev-desc">{e(ev["descricao"])}</p><p class="eventplace">{e(ev["local"])}</p><p class="eventprice">{e(ev["preco"])}</p>'
                       f'<a href="{e(ev["url"])}" rel="noopener">{e(ev.get("ligacao", "Programação oficial"))}</a>{nota}</div>')
        titulo_dia = ("Hoje · " if i == 0 else "") + f"{DIAS[dd.weekday()].capitalize()}, {dd.day} {MESES[dd.month - 1][:3]}."
        did = f"dia-{d['dia']}"
        rot_menu = ("Hoje · " if i == 0 else "") + f"{DIAS[dd.weekday()].split('-')[0].capitalize()} {dd.day}"
        menu_dias.append(f'<a href="#{did}"{" aria-current=\"true\"" if i == 0 else ""}>{e(rot_menu)}</a>')
        # só o dia de hoje aparece; os outros dias abrem a partir do menu da agenda
        dias_html.append(f'<div class="dia-agenda{" hoje" if i == 0 else ""}" id="{did}"><h3>{e(titulo_dia)}</h3>{"".join(evs)}</div>')
    agenda = (f'<section class="newssection" id="agenda"><h2>Agenda do Porto</h2><p class="edition-count">{e(data_num(c["agenda"][0]["dia"]))} a {e(data_num(c["agenda"][-1]["dia"]))} · hoje e os próximos 3 dias no menu</p>'
              f'<div class="menu-dias" role="navigation" aria-label="Dias da agenda">{"".join(menu_dias)}</div>'
              f'<div class="agenda">{"".join(dias_html)}</div>'
              f'<p class="game-note">{e(c.get("agenda_aviso", "Horários, preços e lotação podem mudar. Confirma sempre na programação oficial antes de sair."))}</p></section>')

    teclado = "".join(f'<button type="button" data-v="{v}">{v}</button>' for v in range(1, 10)) + '<button type="button" data-v="0" aria-label="Apagar">⌫</button>'
    jogos_html = f"""<section class="newssection" id="jogos"><h2>Jogos</h2><p class="edition-count">Sudoku · caça-palavras · desafios novos em cada edição</p><div class="games">
<div class="gamebox"><h3>Sudoku</h3><p class="game-instructions">Preenche a grelha para que cada linha, coluna e quadrado de 3×3 tenha os números de 1 a 9. Toca numa casa vazia e escolhe o número no teclado (ou usa o teclado do computador). Dificuldade: moderadamente difícil, com solução única.</p>
<div class="clock"><span>Tempo</span><output class="crono parado" id="sudoku-crono">00:00</output><button class="pill" type="button" id="sudoku-recomecar">Recomeçar</button><button class="pill" type="button" id="sudoku-solucao">Mostrar solução</button></div>
<p class="estado-jogo" id="sudoku-estado" aria-live="polite"></p><div class="sudoku" id="sudoku" role="grid" aria-label="Grelha de Sudoku"></div><div class="teclado" id="sudoku-teclado">{teclado}</div></div>
<div class="gamebox"><h3>Caça-palavras</h3><p class="game-instructions">Encontra as 15 palavras escondidas na horizontal, vertical ou diagonal, em qualquer sentido. Arrasta da primeira à última letra, ou toca na primeira e depois na última. Tema: {e(c.get("tema_palavras", "palavras desta edição"))}.</p>
<div class="clock"><span>Tempo</span><output class="crono parado" id="caca-crono">00:00</output><button class="pill" type="button" id="caca-recomecar">Recomeçar</button><button class="pill" type="button" id="caca-solucao">Mostrar solução</button></div>
<p class="estado-jogo" id="caca-estado" aria-live="polite"></p><div class="caca" id="caca" aria-label="Grelha do caça-palavras"></div><ul class="palavras" id="caca-palavras"></ul></div>
</div></section>"""

    css = (BASE / "estilo.css").read_text()
    js = (BASE / "jogos.js").read_text()
    falha = ("function falhaImagem(i){if(i.dataset.remota&&!i.dataset.tentou){i.dataset.tentou=1;i.src=i.dataset.remota;return}"
             "i.onerror=null;i.src=i.dataset.reserva;var f=i.closest('.figura'),t=f&&f.querySelector('.tipo-img');if(t)t.textContent='Ilustração (imagem original indisponível)'}")
    dia = dt.date.fromisoformat(data)
    destaque = c.get("resumo", "")
    pagina = f"""<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{NOME} · {e(data_pt(data, False))}</title><meta name="description" content="{e(destaque)}">
<style>{css}</style><script>{falha}</script></head><body><main>
<div class="top"><span>Edição n.º {e(c.get("numero", ""))} · {dia.day:02d} {MESES[dia.month - 1][:3]} {dia.year}</span><span>Portugal · Leitura independente</span></div>
<h1 class="masthead"><a href="../">{NOME}</a></h1>
<p class="deck">{e(data_pt(data).capitalize())} · 16 notícias e 4 artigos culturais · Agenda Porto · Sudoku e caça-palavras</p>
<nav aria-label="Secções"><a href="../">Arquivo</a><a href="#tecnologia">Tecnologia, IA e Cibersegurança</a><a href="#mundo">Mundo</a><a href="#portugal">Portugal</a><a href="#cultura">Cultura, Cinema e Arte</a><a href="#agenda">Agenda Porto</a><a href="#jogos">Jogos</a></nav>
<p class="game-note">{e(destaque)}</p>
{digital}{resto}{cultura}{agenda}{jogos_html}
<footer><p>Cada notícia indica o estado da informação (facto confirmado, declaração, proposta, previsão ou anúncio), a data e as fontes consultadas. Procuramos confirmação em duas fontes independentes; quando só há uma, isso fica assinalado. Os textos são sínteses originais. As imagens têm autoria e licença identificadas; imagens de arquivo e ilustrativas estão marcadas como tal.</p>
<p>Edição publicada em <a href="{URL_SITE}{data}/">{URL_SITE}{data}/</a> · <a href="../">Ver todas as edições</a></p></footer></main>
<script type="application/json" id="dados-jogos">{json.dumps(jogos, ensure_ascii=False)}</script><script>{js}</script></body></html>"""
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
    pagina = f"""<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{NOME} · Arquivo</title>
<style>{css}</style></head><body><main><div class="top"><span>Arquivo · {len(arq)} edições</span><span>Portugal · Leitura independente</span></div>
<h1 class="masthead">{NOME}</h1><p class="deck">Todas as edições, da mais recente para a mais antiga</p>
<nav aria-label="Atalhos"><a href="./{arq[0]["data"]}/">Edição mais recente</a></nav>
<section class="newssection"><h2>Arquivo de edições</h2><p class="edition-count">{len(arq):02d} edições</p><ul class="arquivo-lista">{"".join(itens)}</ul></section>
<footer><p>Cada edição tem endereço permanente no formato {URL_SITE}AAAA-MM-DD/. As edições anteriores a 6 de novembro de 2026 mantêm o formato original.</p></footer></main></body></html>"""
    (RAIZ / "index.html").write_text(pagina)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    construir(sys.argv[1])
