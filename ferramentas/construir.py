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
    "espaco": ("Espaço", 2),
}
INICIO_ESPACO = "2026-11-11"  # edições anteriores não têm a secção Espaço
INICIO_V2 = "2026-11-12"  # «Em 2 minutos», «O que acompanhar», manchete e imagens só nas aberturas
PALAVRAS_MIN = 200  # ritmo de leitura para o tempo estimado
RUBRICAS = {"cinema": "Cinema em análise", "artista": "Conhece o artista", "sabias": "Sabias que…?", "movimento": "Cultura em movimento"}
TIPOS_IMG = {"acontecimento": "Fotografia do acontecimento", "arquivo": "Imagem de arquivo", "ilustrativa": "Imagem ilustrativa", "oficial": "Imagem oficial / de imprensa", "obra": "Reprodução da obra", "cartaz": "Imagem promocional"}
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
CORES = {"mundo": "#5b6577", "portugal": "#1e4fa8", "ciberseguranca": "#0e7c6f", "ia": "#6a43c4", "tecnologia": "#b2560e", "espaco": "#243b6b", "cultura": "#a8325e"}

TEMA_JS = ("(function(){try{var t=localStorage.getItem('tema');if(t)document.documentElement.dataset.tema=t}catch(e){}})();")
UI_JS = """(function(){
var r=document.documentElement,b=document.getElementById('tema');
function escuro(){return r.dataset.tema?r.dataset.tema==='escuro':matchMedia('(prefers-color-scheme: dark)').matches}
function rot(){if(b){b.textContent=escuro()?'Modo claro':'Modo escuro';b.setAttribute('aria-pressed',escuro())}}
if(b){b.addEventListener('click',function(){var n=escuro()?'claro':'escuro';r.dataset.tema=n;try{localStorage.setItem('tema',n)}catch(e){}rot()});rot()}
var t=document.querySelector('.topo');
if(t){var f=function(){t.classList.toggle('visivel',scrollY>900)};addEventListener('scroll',f,{passive:true});f()}
function abrir(){if(!location.hash)return;var a=document.getElementById(location.hash.slice(1));if(!a)return;a.querySelectorAll('details.mais').forEach(function(d){d.open=true})}
addEventListener('hashchange',abrir);abrir();
addEventListener('beforeprint',function(){document.querySelectorAll('details').forEach(function(d){d.dataset.f=d.open?'':'1';d.open=true})});
addEventListener('afterprint',function(){document.querySelectorAll('details[data-f]').forEach(function(d){if(d.dataset.f)d.open=false;delete d.dataset.f})});
})();"""
BOTAO_TEMA = '<button type="button" class="tema" id="tema" aria-pressed="false">Modo escuro</button>'

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
    conter = img.get("ajuste") == "conter" or (img.get("ajuste") != "cobrir" and orig.lower().endswith(".svg"))
    return (f'<figure class="figura"><div class="moldura{" conter" if conter else ""}"><img id="img-{idx:02d}" src="{e(src)}" data-remota="{e(remota)}" data-reserva="{e(reserva)}" '
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


def rodape(fontes, verif=None, nota=""):
    """Fontes e verificação recolhidas num bloco que se abre ao clicar."""
    resumo = "Fontes e verificação"
    if verif:
        resumo += " · " + ("2 fontes independentes" if verif.get("independentes", 0) >= 2 else "fonte única")
    else:
        resumo = "Fontes"
    corpo = fontes_html(fontes) + verif_html(verif) + (f'<span class="verif">{e(nota)}</span>' if nota else "")
    return f'<details class="verificacao"><summary>{e(resumo)}</summary>{corpo}</details>'


def data_num(iso):
    try:
        d = dt.date.fromisoformat(iso)
        return f"{d.day:02d}/{d.month:02d}/{d.year}"
    except Exception:
        return iso or ""


def palavras(*textos):
    return sum(len(str(t).split()) for t in textos)


def minutos(n):
    return max(1, round(n / PALAVRAS_MIN))


def corpo_html(paras, visiveis=1, ficha=""):
    """Mostra os primeiros parágrafos; o resto fica em «Continuar a ler»."""
    vis = "".join(f"<p>{e(p)}</p>" for p in paras[:visiveis])
    resto = paras[visiveis:]
    mais = ""
    if resto:
        mais = ('<details class="mais"><summary><span class="abrir">Continuar a ler</span><span class="fechar">Mostrar menos</span></summary>'
                + "".join(f"<p>{e(p)}</p>" for p in resto) + "</details>")
    return f'<div class="corpo">{ficha}{vis}{mais}</div>'


def noticia(n, num, etiqueta, fig, nid, classe="", visiveis=1):
    meta = (f'<p class="meta"><span class="estado">{e(n["estado"])}</span> · '
            f'<time datetime="{e(n.get("data", ""))}">{e(data_num(n.get("data", "")))}</time></p>')
    tag = f"{num:02d} / {e(etiqueta)}" if num else e(etiqueta)
    cab = f'<span class="tag">{tag}</span><h3>{e(n["titulo"])}</h3>{meta}'
    corpo = corpo_html(n["texto"], visiveis)
    pe = rodape(n["fontes"], n.get("verificacao"))
    if fig and "manchete" in classe:
        return (f'<article class="card {classe}" id="{nid}">{cab}<div class="manchete-grelha"><div class="abertura-img">{fig}</div>'
                f'<div class="abertura-txt">{corpo}{pe}</div></div></article>')
    if fig and "abertura" in classe:
        return (f'<article class="card {classe}" id="{nid}"><div class="abertura-img">{fig}</div>'
                f'<div class="abertura-txt">{cab}{corpo}{pe}</div></article>')
    return f'<article class="card {classe}" id="{nid}">{cab}{fig}{corpo}{pe}</article>'


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
    com_espaco = data >= INICIO_ESPACO
    v2 = data >= INICIO_V2
    cont = {k: 0 for k in SECCOES}
    for n in c["noticias"]:
        cont[n["seccao"]] += 1
    for k, (nome, alvo) in SECCOES.items():
        if k == "espaco" and not com_espaco and cont[k] == 0:
            continue
        if cont[k] != alvo:
            raise SystemExit(f"{nome}: {cont[k]} notícias (esperadas {alvo})")
    if sorted(a["rubrica"] for a in c["cultura"]) != sorted(RUBRICAS):
        raise SystemExit("A cultura precisa das quatro rubricas")
    if len(c["agenda"]) != 4:
        raise SystemExit("A agenda precisa de quatro dias")
    total = len(c["noticias"])
    manchetes = [i for i, n in enumerate(c["noticias"]) if n.get("manchete")]
    if v2:
        if len(manchetes) != 1:
            raise SystemExit(f"É precisa exatamente uma notícia com \"manchete\": true (há {len(manchetes)})")
        if not 5 <= len(c.get("em_2_minutos", [])) <= 6:
            raise SystemExit("«em_2_minutos» precisa de 5 a 6 entradas")
        if not 3 <= len(c.get("acompanhar", [])) <= 4:
            raise SystemExit("«acompanhar» precisa de 3 a 4 entradas")
        for it in c["em_2_minutos"] + c["acompanhar"]:
            if "noticia" in it and not 1 <= int(it["noticia"]) <= total:
                raise SystemExit(f"Referência a notícia inexistente: {it}")
    i_manchete = manchetes[0] if (v2 and manchetes) else None
    nid = lambda i: f"n{i + 1:02d}"

    def fig_de(n, chave, rotulo):
        nonlocal idx
        f = figura(n.get("imagem"), chave, rotulo, manifest, assets, idx)
        idx += 1
        return f

    # manchete (fora da sua secção, no topo)
    manchete_html = ""
    if i_manchete is not None:
        n = c["noticias"][i_manchete]
        nome = SECCOES[n["seccao"]][0]
        fig = fig_de(n, n["seccao"], nome)
        manchete_html = ('<section class="manchete-sec" aria-label="Manchete">'
                         + noticia(n, 0, f"Manchete · {nome}", fig, nid(i_manchete), "manchete", visiveis=len(n["texto"]))
                         + "</section>")

    def seccao(sid, titulo, chaves, contagem):
        cartoes, num, palav, primeiro = [], 1, 0, True
        tem_manchete = False
        for chave in chaves:
            nome, tot = SECCOES[chave]
            pos = 0
            for i, n in enumerate(c["noticias"]):
                if n["seccao"] != chave:
                    continue
                pos += 1
                palav += palavras(n["titulo"], *n["texto"])
                if i == i_manchete:
                    tem_manchete = True
                    continue
                etiqueta = f"{nome} {pos}/{tot}" if len(chaves) > 1 else nome
                if v2 and primeiro:
                    cartoes.append(noticia(n, num, etiqueta, fig_de(n, chave, nome), nid(i), "abertura"))
                elif v2:
                    cartoes.append(noticia(n, num, etiqueta, "", nid(i), "simples"))
                else:
                    cartoes.append(noticia(n, num, etiqueta, fig_de(n, chave, nome), nid(i)))
                primeiro = False
                num += 1
        # num par de notícias sem imagem, a última ocupa a largura toda
        if v2 and len(cartoes) > 1 and (len(cartoes) - 1) % 2 == 1:
            cartoes[-1] = cartoes[-1].replace('class="card simples"', 'class="card simples largo"', 1)
        if tem_manchete:
            contagem += ' · <a href="#manchete">a manchete desta secção está no topo</a>'
        ancoras = "".join(f'<span id="{k}"></span>' for k in chaves if k != sid)
        return (f'<section class="newssection" id="{sid}">{ancoras}<h2>{titulo}</h2><p class="edition-count">{contagem} · cerca de {minutos(palav)} min de leitura</p>'
                f'<div class="grid">{"".join(cartoes)}</div></section>')

    digital = seccao("tecnologia", "Tecnologia, IA e Cibersegurança", ["ciberseguranca", "ia", "tecnologia"],
                     "08 notícias · 3 cibersegurança · 3 IA · 2 tecnologia")
    resto = seccao("mundo", "Mundo", ["mundo"], "04 notícias") + seccao("portugal", "Portugal", ["portugal"], "04 notícias")
    if com_espaco:
        resto += seccao("espaco", "Espaço", ["espaco"], "02 notícias")

    arts, palav_cult = [], 0
    for num, a in enumerate(sorted(c["cultura"], key=lambda a: list(RUBRICAS).index(a["rubrica"])), 1):
        ficha = ""
        if a.get("ficha"):
            ficha = '<dl class="ficha">' + "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in a["ficha"].items()) + "</dl>"
        palav_cult += palavras(a["titulo"], *a["texto"])
        fig = figura(a.get("imagem"), "cultura", RUBRICAS[a["rubrica"]], manifest, assets, idx)
        idx += 1
        arts.append(f'<article class="card cultura" id="c{num:02d}"><span class="tag">{num:02d} / {RUBRICAS[a["rubrica"]]}</span><h3>{e(a["titulo"])}</h3>{fig}'
                    f'{corpo_html(a["texto"], 1, ficha)}{rodape(a["fontes"], None, a.get("nota", ""))}</article>')
    cultura = (f'<section class="newssection" id="cultura"><h2>Cultura, Cinema e Arte</h2><p class="edition-count">04 artigos · cinema · artista · curiosidade · cultura em movimento · cerca de {minutos(palav_cult)} min de leitura</p>'
               f'<div class="grid">{"".join(arts)}</div></section>')

    # «Em 2 minutos» e «O que acompanhar»
    briefing = ""
    if v2:
        def alvo(it):
            if "noticia" in it:
                return f"#{nid(int(it['noticia']) - 1)}"
            return f"#{it['ancora']}" if it.get("ancora") else ""
        def item(it, com_quando=False):
            q = f'<strong class="quando">{e(it["quando"])}</strong> ' if com_quando and it.get("quando") else ""
            h = alvo(it)
            ler = f' <a class="ir" href="{h}" aria-label="Ler a notícia">Ler →</a>' if h else ""
            return f"<li>{q}<span>{e(it['texto'])}{ler}</span></li>"
        briefing = (f'<section class="briefing" id="resumo" aria-label="Resumo do dia">'
                    f'<div class="b-col"><h2>Em 2 minutos</h2><ol>{"".join(item(i) for i in c["em_2_minutos"])}</ol></div>'
                    f'<div class="b-col"><h2>O que acompanhar</h2><ul>{"".join(item(i, True) for i in c["acompanhar"])}</ul></div></section>')

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
    total_noticias = len(c["noticias"])
    nav_espaco = '<a href="#espaco">Espaço</a>' if com_espaco else ""
    nav_resumo = '<a href="#resumo"><span class="longo">Em 2 minutos</span><span class="curto">Resumo</span></a>' if v2 else ""
    resumo_linha = "" if v2 else f'<p class="game-note">{e(destaque)}</p>'
    pagina = f"""<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{NOME} · {e(data_pt(data, False))}</title><meta name="description" content="{e(destaque)}">
<style>{css}</style><script>{TEMA_JS}{falha}</script></head><body><main id="inicio">
<div class="top"><span>Edição n.º {e(c.get("numero", ""))} · {dia.day:02d} {MESES[dia.month - 1][:3]} {dia.year}</span><span class="top-dir"><span class="lema">Portugal · Leitura independente</span>{BOTAO_TEMA}</span></div>
<h1 class="masthead"><a href="../">{NOME}</a></h1>
<p class="deck">{e(data_pt(data).capitalize())} · {total_noticias} notícias e 4 artigos culturais · Agenda Porto · Sudoku e caça-palavras</p>
<nav aria-label="Secções"><a href="../">Arquivo</a>{nav_resumo}<a href="#tecnologia"><span class="longo">Tecnologia, IA e Cibersegurança</span><span class="curto">Digital</span></a><a href="#mundo">Mundo</a><a href="#portugal">Portugal</a>{nav_espaco}<a href="#cultura">Cultura</a><a href="#agenda"><span class="longo">Agenda Porto</span><span class="curto">Agenda</span></a><a href="#jogos">Jogos</a></nav>
{resumo_linha}{briefing}<span id="manchete"></span>{manchete_html}
{digital}{resto}{cultura}{agenda}{jogos_html}
<footer><p>Cada notícia indica o estado da informação (facto confirmado, declaração, proposta, previsão ou anúncio), a data e as fontes consultadas. Procuramos confirmação em duas fontes independentes; quando só há uma, isso fica assinalado. Os textos são sínteses originais. As imagens têm autoria e licença identificadas; imagens de arquivo e ilustrativas estão marcadas como tal.</p>
<p>Edição publicada em <a href="{URL_SITE}{data}/">{URL_SITE}{data}/</a> · <a href="../">Ver todas as edições</a></p></footer></main>
<a class="topo" href="#inicio" aria-label="Voltar ao topo">↑</a>
<script type="application/json" id="dados-jogos">{json.dumps(jogos, ensure_ascii=False)}</script><script>{js}</script><script>{UI_JS}</script></body></html>"""
    (pasta / "index.html").write_text(pagina)
    (assets / "imagens.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    atualizar_arquivo(data, c)
    print(f"Edição {data}: {len(manifest)} imagens, {len(pagina)//1024} KB")


def atualizar_arquivo(data, c):
    arq_p = BASE / "arquivo.json"
    arq = json.loads(arq_p.read_text())
    arq = [x for x in arq if x["data"] != data]
    arq.append({"data": data, "numero": c.get("numero", ""), "resumo": c.get("resumo", ""), "formato": f"{len(c['noticias'])} notícias · 4 artigos culturais · Agenda do Porto · Sudoku e caça-palavras"})
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
<style>{css}</style><script>{TEMA_JS}</script></head><body><main><div class="top"><span>Arquivo · {len(arq)} edições</span><span class="top-dir"><span class="lema">Portugal · Leitura independente</span>{BOTAO_TEMA}</span></div>
<h1 class="masthead">{NOME}</h1><p class="deck">Todas as edições, da mais recente para a mais antiga</p>
<nav aria-label="Atalhos"><a href="./{arq[0]["data"]}/">Edição mais recente</a></nav>
<section class="newssection"><h2>Arquivo de edições</h2><p class="edition-count">{len(arq):02d} edições</p><ul class="arquivo-lista">{"".join(itens)}</ul></section>
<footer><p>Cada edição tem endereço permanente no formato {URL_SITE}AAAA-MM-DD/. As edições anteriores a 6 de novembro de 2026 mantêm o formato original.</p></footer></main></body></html>"""
    (RAIZ / "index.html").write_text(pagina)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    construir(sys.argv[1])
