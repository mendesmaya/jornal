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
AVISO_IA = ("Feito com inteligência artificial (Claude), a partir de regras editoriais definidas e supervisionadas pela autora. "
            "Pode conter erros: confirma sempre nas fontes indicadas em cada notícia.")
AVISO_IA_HTML = f'<p class="aviso-ia"><span aria-hidden="true">🤖</span> {AVISO_IA} <a href="../#correcoes">Correções</a></p>'
BOTAO_TEMA = '<button type="button" class="tema" id="tema" aria-pressed="false">Modo escuro</button>'

OG_IMG = URL_SITE + "og.png"


ICONES = (f'<link rel="icon" href="{URL_SITE}favicon.svg" type="image/svg+xml">'
          f'<link rel="icon" href="{URL_SITE}favicon-32.png" sizes="32x32" type="image/png">'
          f'<link rel="icon" href="{URL_SITE}favicon-16.png" sizes="16x16" type="image/png">'
          f'<link rel="apple-touch-icon" href="{URL_SITE}apple-touch-icon.png"><meta name="theme-color" content="#f1ebde">')


def og_html(titulo, descricao, url):
    """Etiquetas para a pré-visualização da ligação (LinkedIn, WhatsApp, etc.) e ícones do separador."""
    return (ICONES +f'<meta property="og:type" content="website"><meta property="og:site_name" content="{NOME}">'
            f'<meta property="og:title" content="{e(titulo)}"><meta property="og:description" content="{e(descricao)}">'
            f'<meta property="og:url" content="{e(url)}"><meta property="og:image" content="{OG_IMG}">'
            f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:image:alt" content="{NOME}: sol a nascer sobre o horizonte, desenhado à mão">'
            f'<meta property="og:locale" content="pt_PT"><meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:image" content="{OG_IMG}">')



def titulo_html(href):
    """Título desenhado à mão (ferramentas/marca/titulo.svg); recorre ao texto se o ficheiro faltar."""
    tp = BASE / "marca" / "titulo.svg"
    if not tp.exists():
        return f'<a href="{href}">{NOME}</a>'
    return f'<a href="{href}" class="titulo-desenhado">{tp.read_text().strip()}</a>'


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


def correcoes(ate=None, dias=None):
    """Lista de ferramentas/correcoes.json (mais recentes primeiro), opcionalmente só as dos `dias` anteriores a `ate`."""
    cp = BASE / "correcoes.json"
    lista = json.loads(cp.read_text()) if cp.exists() else []
    if ate:
        ini = (dt.date.fromisoformat(ate) - dt.timedelta(days=dias or 7)).isoformat()
        lista = [x for x in lista if ini <= x["data"] <= ate]
    return sorted(lista, key=lambda x: x["data"], reverse=True)


def item_correcao(x, prefixo="../"):
    ed = x.get("edicao", "")
    lig = f' <a href="{prefixo}{e(ed)}/{e(x.get("ancora", ""))}">Ver na edição de {e(data_pt(ed, False))}</a>' if ed else ""
    return f'<li><strong>{e(data_num(x["data"]))}</strong> · {e(x["texto"])}{lig}</li>'


def caixa_correcoes(data):
    lista = correcoes(data, 7)
    if not lista:
        return ""
    return (f'<section class="correcoes-box" aria-label="Correções"><h2>Correções e atualizações</h2>'
            f'<ul>{"".join(item_correcao(x) for x in lista)}</ul><p><a href="../#correcoes">Ver todas as correções</a></p></section>')


def noticia(n, num, etiqueta, fig, nid, classe="", visiveis=1):
    meta = (f'<p class="meta"><span class="estado">{e(n["estado"])}</span> · '
            f'<time datetime="{e(n.get("data", ""))}">{e(data_num(n.get("data", "")))}</time></p>')
    tag = f"{num:02d} / {e(etiqueta)}" if num else e(etiqueta)
    cab = f'<span class="tag">{tag}</span><h3>{e(n["titulo"])}</h3>{meta}'
    corpo = corpo_html(n["texto"], visiveis)
    pe = rodape(n["fontes"], n.get("verificacao"))
    if n.get("correcao"):
        pe = f'<p class="correcao"><strong>Correção:</strong> {e(n["correcao"])}</p>' + pe
    if fig and "manchete" in classe:
        return (f'<article class="card {classe}" id="{nid}">{cab}<div class="manchete-grelha"><div class="abertura-img">{fig}</div>'
                f'<div class="abertura-txt">{corpo}{pe}</div></div></article>')
    if fig and "abertura" in classe:
        return (f'<article class="card {classe}" id="{nid}"><div class="abertura-img">{fig}</div>'
                f'<div class="abertura-txt">{cab}{corpo}{pe}</div></article>')
    return f'<article class="card {classe}" id="{nid}">{cab}{fig}{corpo}{pe}</article>'


NOMES_JOGOS = {"sudoku": "Sudoku", "caca": "caça-palavras", "2048": "2048", "diferencas": "jogo das diferenças", "nonograma": "nonograma",
               "minas": "campo minado", "cobra": "jogo da cobra", "dino": "corrida do dinossauro", "puzzle": "puzzle", "quiz": "quiz da semana"}


def lista_jogos(jogos):
    return jogos.get("lista") or [k for k in ("sudoku", "caca") if k in jogos]


def descricao_jogos(jogos):
    nomes = [NOMES_JOGOS[k] for k in lista_jogos(jogos)]
    txt = " e ".join(nomes) if len(nomes) <= 2 else ", ".join(nomes[:-1]) + " e " + nomes[-1]
    return txt[:1].upper() + txt[1:]


def caixa(jid, titulo, instr, corpo, crono=True, solucao=True, extra=""):
    botoes = (f'<button class="pill" type="button" id="{jid}-recomecar">Recomeçar</button>'
              + (f'<button class="pill" type="button" id="{jid}-solucao">Mostrar solução</button>' if solucao else "") + extra)
    rel = f'<span>Tempo</span><output class="crono parado" id="{jid}-crono">00:00</output>' if crono else ""
    return (f'<div class="gamebox" id="jogo-{jid}"><h3>{titulo}</h3><p class="game-instructions">{instr}</p>'
            f'<div class="clock">{rel}{botoes}</div><p class="estado-jogo" id="{jid}-estado" aria-live="polite"></p>{corpo}</div>')


def setas(jid):
    return (f'<div class="setas" id="{jid}-setas" aria-label="Setas"><button type="button" data-d="cima" aria-label="Para cima">↑</button>'
            f'<button type="button" data-d="esq" aria-label="Para a esquerda">←</button><button type="button" data-d="baixo" aria-label="Para baixo">↓</button>'
            f'<button type="button" data-d="dir" aria-label="Para a direita">→</button></div>')


def placar(jid):
    return (f'<p class="placar">Pontos <output id="{jid}-pontos">0</output> · Melhor neste dispositivo <output id="{jid}-melhor">0</output></p>')


def html_jogos(jogos, c):
    tema = e(c.get("tema_palavras", "palavras desta edição"))
    teclado = "".join(f'<button type="button" data-v="{v}">{v}</button>' for v in range(1, 10)) + '<button type="button" data-v="0" aria-label="Apagar">⌫</button>'
    B = {
        "sudoku": caixa("sudoku", "Sudoku", "Preenche a grelha para que cada linha, coluna e quadrado de 3×3 tenha os números de 1 a 9. Toca numa casa vazia e escolhe o número. Liga o <strong>rascunho</strong> para anotar várias hipóteses pequenas numa casa antes de decidir (no computador: tecla N, ou Shift + número). Dificuldade: média, com solução única e sem precisar de tentativa-erro.",
                        '<div class="sudoku" id="sudoku" role="grid" aria-label="Grelha de Sudoku"></div>'
                        f'<div class="teclado" id="sudoku-teclado">{teclado}<button type="button" class="rascunho" id="sudoku-rascunho" aria-pressed="false">✏️ Rascunho: desligado</button></div>'),
        "caca": caixa("caca", "Caça-palavras", f"Encontra as 15 palavras escondidas na horizontal, vertical ou diagonal, em qualquer sentido. Arrasta da primeira à última letra, ou toca na primeira e depois na última. Tema: {tema}.",
                      '<div class="caca" id="caca" aria-label="Grelha do caça-palavras"></div><ul class="palavras" id="caca-palavras"></ul>'),
        "2048": caixa("g2048", "2048", "Desliza o dedo (ou usa as setas do teclado depois de tocares no tabuleiro) para mover todas as peças. Duas peças iguais que se tocam juntam-se numa só. Chega à peça 2048.",
                      placar("g2048") + '<div class="t2048" id="g2048" tabindex="0" aria-label="Tabuleiro do 2048"></div>' + setas("g2048"), crono=False, solucao=False),
        "diferencas": caixa("dif", "Jogo das diferenças", "As duas imagens têm 7 diferenças. Toca onde as vires, em qualquer uma das imagens.",
                            '<div class="dif"><figure id="dif-a"></figure><figure id="dif-b"></figure></div>'),
        "nonograma": caixa("nono", "Nonograma", "Os números dizem quantas casas seguidas estão pintadas em cada linha e coluna, por ordem, com pelo menos uma casa vazia entre blocos. Pinta as casas certas e descobre a figura. Solução única, só com lógica.",
                           '<div class="nono" id="nono" aria-label="Grelha do nonograma"></div>', extra='<button class="pill" type="button" id="nono-modo" aria-pressed="false">Modo: pintar ■</button>'),
        "minas": caixa("minas", "Campo minado", "Abre todas as casas sem minas. Cada número diz quantas minas há nas 8 casas à volta. Marca as minas com bandeira: toque longo, botão direito do rato ou o modo bandeira.",
                       '<p class="placar">Minas por marcar <output id="minas-restam">15</output></p><div class="minas" id="minas" aria-label="Campo minado"></div>',
                       solucao=False, extra='<button class="pill" type="button" id="minas-bandeira" aria-pressed="false">Modo: abrir</button>'),
        "cobra": caixa("cobra", "Jogo da cobra", "Guia a cobra até à comida. Cada ponto faz a cobra crescer e andar mais depressa. Não batas nas paredes nem na tua própria cauda.",
                       placar("cobra") + '<canvas class="cobra" id="cobra" tabindex="0" aria-label="Jogo da cobra"></canvas>' + setas("cobra"),
                       crono=False, solucao=False, extra='<button class="pill" type="button" id="cobra-jogar">Jogar</button>'),
        "dino": caixa("dino", "Corrida do dinossauro", "Inspirado no jogo de quando ficamos sem internet: o nosso dinossauro de pescoço comprido corre sozinho e tens de o fazer saltar por cima dos obstáculos. Cada vez mais depressa.",
                      placar("dino") + '<canvas class="dino" id="dino" tabindex="0" aria-label="Corrida do dinossauro"></canvas>',
                      crono=False, solucao=False, extra='<button class="pill" type="button" id="dino-saltar">Saltar</button>'),
        "puzzle": caixa("puzzle", "Puzzle", "A imagem da manchete foi cortada em 16 peças e baralhada. Toca em duas peças para as trocar até a imagem ficar completa. As peças no sítio certo ficam marcadas.",
                        '<div class="puzzle" id="puzzle" aria-label="Puzzle"></div><img class="puzzle-ref" id="puzzle-ref" alt="Imagem original do puzzle" hidden>',
                        extra='<button class="pill" type="button" id="puzzle-ver">Ver imagem</button>'),
        "quiz": caixa("quiz", "Quiz da semana", "Quanto te lembras das notícias desta semana? Escolhe uma resposta em cada pergunta; a explicação e a ligação para a notícia aparecem logo a seguir.",
                      '<div class="quiz" id="quiz"></div>', crono=False, solucao=False),
    }
    lista = lista_jogos(jogos)
    titulo = "Passatempo" if lista == ["quiz"] else "Jogos"
    return (f'<section class="newssection" id="jogos"><h2>{titulo}</h2><p class="edition-count">{e(descricao_jogos(jogos))} · desafios novos em cada edição</p>'
            f'<div class="games{" um" if len(lista) == 1 else ""}">{"".join(B[k] for k in lista)}</div></section>')


def html_agenda(c):
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
    return agenda


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

    if c.get("tipo") == "semanal":
        return construir_semanal(data, c, jogos, pasta, assets, manifest)

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

    agenda = html_agenda(c)
    jogos_html = html_jogos(jogos, c)

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
{og_html(f"{NOME} · {data_pt(data, False)}", destaque, f"{URL_SITE}{data}/")}
<style>{css}</style><script>{TEMA_JS}{falha}</script></head><body><main id="inicio">
<div class="top"><span>Edição n.º {e(c.get("numero", ""))} · {dia.day:02d} {MESES[dia.month - 1][:3]} {dia.year}</span><span class="top-dir"><span class="lema">Portugal · Leitura independente</span>{BOTAO_TEMA}</span></div>
<h1 class="masthead">{titulo_html("../")}</h1>
<p class="deck">{e(data_pt(data).capitalize())} · {total_noticias} notícias e 4 artigos culturais · Agenda Porto · {e(descricao_jogos(jogos))}</p>
<nav aria-label="Secções"><a href="../">Arquivo</a>{nav_resumo}<a href="#tecnologia"><span class="longo">Tecnologia, IA e Cibersegurança</span><span class="curto">Digital</span></a><a href="#mundo">Mundo</a><a href="#portugal">Portugal</a>{nav_espaco}<a href="#cultura">Cultura</a><a href="#agenda"><span class="longo">Agenda Porto</span><span class="curto">Agenda</span></a><a href="#jogos">Jogos</a></nav>
{resumo_linha}{briefing}{caixa_correcoes(data)}<span id="manchete"></span>{manchete_html}
{digital}{resto}{cultura}{agenda}{jogos_html}
<footer><p>Cada notícia indica o estado da informação (facto confirmado, declaração, proposta, previsão ou anúncio), a data e as fontes consultadas. Procuramos confirmação em duas fontes independentes; quando só há uma, isso fica assinalado. Os textos são sínteses originais. As imagens têm autoria e licença identificadas; imagens de arquivo e ilustrativas estão marcadas como tal.</p>
<p><strong>Sobre este jornal:</strong> {AVISO_IA} Projeto pessoal, sem publicidade e sem fins comerciais. Os erros detetados são corrigidos e registados na <a href="../#correcoes">lista de correções</a>.</p>
<p>Edição publicada em <a href="{URL_SITE}{data}/">{URL_SITE}{data}/</a> · <a href="../">Ver todas as edições</a></p></footer></main>
<a class="topo" href="#inicio" aria-label="Voltar ao topo">↑</a>
<script type="application/json" id="dados-jogos">{json.dumps(jogos, ensure_ascii=False)}</script><script>{js}</script><script>{UI_JS}</script></body></html>"""
    (pasta / "index.html").write_text(pagina)
    (assets / "imagens.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    atualizar_arquivo(data, c)
    if v2:
        li = texto_linkedin(data, c)
        print(f"Texto do LinkedIn: ferramentas/linkedin/{data}.txt ({len(li)} caracteres)")
    print(f"Edição {data}: {len(manifest)} imagens, {len(pagina)//1024} KB")


DIAS_CURTOS = ["seg.", "ter.", "qua.", "qui.", "sex.", "sáb.", "dom."]


def dia_curto(iso):
    d = dt.date.fromisoformat(iso)
    return f"{DIAS_CURTOS[d.weekday()]} {d.day} {MESES[d.month - 1][:3]}."


def temas_da_semana(inicio, fim):
    """Lê ferramentas/arquivo_temas.md e devolve as linhas (data, [cinema, artista, sabias, movimento]) entre as duas datas."""
    linhas = []
    tp = BASE / "arquivo_temas.md"
    if not tp.exists():
        return linhas
    for l in tp.read_text().splitlines():
        cel = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(cel) >= 5 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cel[0]) and inicio <= cel[0] <= fim:
            linhas.append((cel[0], cel[1:5]))
    return sorted(linhas)


def construir_semanal(data, c, jogos, pasta, assets, manifest):
    dia = dt.date.fromisoformat(data)
    # validações
    D = c.get("destaques", [])
    if not 8 <= len(D) <= 10:
        raise SystemExit(f"Edição semanal: são precisos 8 a 10 destaques (há {len(D)})")
    for k, d in enumerate(D[:3]):
        if not d.get("imagem"):
            raise SystemExit(f"Edição semanal: o destaque {k + 1} precisa de imagem")
    if not 5 <= len(c.get("em_2_minutos", [])) <= 6:
        raise SystemExit("Edição semanal: «em_2_minutos» precisa de 5 a 6 entradas")
    if not 4 <= len(c.get("semana_que_vem", [])) <= 6:
        raise SystemExit("Edição semanal: «semana_que_vem» precisa de 4 a 6 entradas")
    if not 6 <= len(c.get("quiz", [])) <= 10:
        raise SystemExit("Edição semanal: o quiz precisa de 6 a 10 perguntas")
    for q in c["quiz"]:
        if not 3 <= len(q["opcoes"]) <= 4 or not 0 <= q["certa"] < len(q["opcoes"]):
            raise SystemExit(f"Pergunta do quiz inválida: {q['pergunta']}")
    for it in c["em_2_minutos"]:
        if "destaque" in it and not 1 <= int(it["destaque"]) <= len(D):
            raise SystemExit(f"Referência a destaque inexistente: {it}")
    if len(c["agenda"]) != 4:
        raise SystemExit("A agenda precisa de quatro dias")
    inicio = (dia - dt.timedelta(days=6)).isoformat()
    ontem = (dia - dt.timedelta(days=1)).isoformat()
    idx = 1

    def ligacao_original(d):
        if not d.get("edicao"):
            return ""
        ancora = f"#n{int(d['noticia']):02d}" if d.get("noticia") and d["edicao"] >= INICIO_V2 else ""
        return f'<p class="original">Na edição de <a href="../{e(d["edicao"])}/{ancora}">{e(data_pt(d["edicao"]))}</a></p>'

    cartoes, palav = [], 0
    for k, d in enumerate(D, 1):
        palav += palavras(d["titulo"], *d["texto"], d.get("desenvolvimento", ""))
        nome = SECCOES.get(d.get("seccao", ""), (d.get("seccao", "").capitalize(),))[0]
        quando = dia_curto(d["data"]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.get("data", "")) else ""
        etiqueta = f"{k:02d} / {nome}" + (f" · {quando}" if quando else "")
        fig = ""
        if k <= 3:
            fig = figura(d["imagem"], d.get("seccao", "mundo") if d.get("seccao") in CORES else "mundo", nome, manifest, assets, idx)
            idx += 1
        classe = "manchete" if k == 1 else ("abertura" if k <= 3 else "simples")
        extra = ""
        if d.get("desenvolvimento"):
            extra = f'<p class="desenvolvimento"><strong>O que mudou desde então:</strong> {e(d["desenvolvimento"])}</p>'
        art = noticia(d, 0, etiqueta, fig, f"s{k:02d}", classe, visiveis=len(d["texto"]) if k == 1 else 1)
        art = art.replace('<details class="verificacao">', extra + ligacao_original(d) + '<details class="verificacao">', 1)
        if k == 1:
            art = art.replace('<span class="tag">', '<span class="tag">A notícia da semana · ', 1)
        cartoes.append(art)
    resto = cartoes[1:]
    if len(resto) > 2 and (len(resto) - 2) % 2 == 1:
        resto[-1] = resto[-1].replace('class="card simples"', 'class="card simples largo"', 1)
    semana = (f'<section class="manchete-sec" id="semana" aria-label="A notícia da semana">{cartoes[0]}</section>'
              f'<section class="newssection"><h2>As notícias da semana</h2><p class="edition-count">{len(D):02d} notícias · as mais importantes e as que mais deram que falar, de {e(dia_curto(inicio))} a {e(dia_curto(ontem))} · cerca de {minutos(palav)} min de leitura</p>'
              f'<div class="grid">{"".join(resto)}</div></section>')

    def item(it, com_quando=False):
        q = f'<strong class="quando">{e(it["quando"])}</strong> ' if com_quando and it.get("quando") else ""
        h = f"#s{int(it['destaque']):02d}" if it.get("destaque") else (f"#{it['ancora']}" if it.get("ancora") else "")
        ler = f' <a class="ir" href="{h}">Ler →</a>' if h else ""
        return f"<li>{q}<span>{e(it['texto'])}{ler}</span></li>"
    briefing = (f'<section class="briefing" id="resumo" aria-label="Resumo da semana">'
                f'<div class="b-col"><h2>A semana em 2 minutos</h2><ol>{"".join(item(i) for i in c["em_2_minutos"])}</ol></div>'
                f'<div class="b-col" id="semana-que-vem"><h2>A semana que vem</h2><ul>{"".join(item(i, True) for i in c["semana_que_vem"])}</ul></div></section>')

    # cultura da semana (a partir do arquivo de temas) e edições da semana (a partir do arquivo)
    temas = temas_da_semana(inicio, ontem)
    rot = ["Cinema", "Conhece o artista", "Sabias que…?", "Cultura em movimento"]
    colunas = []
    for j, r in enumerate(rot):
        itens = "".join(f'<li><a href="../{dd}/{"#c%02d" % (j + 1) if dd >= INICIO_V2 else "#cultura"}">{e(t[j])}</a> <small>{e(dia_curto(dd))}</small></li>' for dd, t in temas if t[j])
        colunas.append(f'<div><h3>{r}</h3><ul>{itens or "<li>Sem registos nesta semana.</li>"}</ul></div>')
    arq = json.loads((BASE / "arquivo.json").read_text())
    edicoes = [x for x in sorted(arq, key=lambda x: x["data"]) if inicio <= x["data"] <= ontem]
    lista_ed = "".join(f'<li><a href="../{x["data"]}/">{e(dia_curto(x["data"]))}</a> <span>{e(x.get("resumo", ""))}</span></li>' for x in edicoes)
    cultura = (f'<section class="newssection" id="cultura"><h2>Destaques culturais da semana</h2><p class="edition-count">o que passou pela Cultura de {e(dia_curto(inicio))} a {e(dia_curto(ontem))} · toca para ler</p>'
               f'<div class="cultura-semana">{"".join(colunas)}</div></section>'
               f'<section class="newssection" id="edicoes"><h2>As edições da semana</h2><p class="edition-count">{len(edicoes)} edições · cada uma com notícias, cultura, agenda e jogos</p><ul class="edicoes-semana">{lista_ed}</ul></section>')

    agenda = html_agenda(c)
    jogos = dict(jogos)
    jogos["quiz"] = [{"pergunta": q["pergunta"], "opcoes": q["opcoes"], "certa": q["certa"], "explicacao": q.get("explicacao", ""),
                      "ligacao": (f"#s{int(q['destaque']):02d}" if q.get("destaque") else
                                  (f"../{q['edicao']}/" + (f"#n{int(q['noticia']):02d}" if q.get("noticia") and q["edicao"] >= INICIO_V2 else "")) if q.get("edicao") else "")}
                     for q in c["quiz"]]
    jogos["lista"] = ["quiz"]
    jogos_html = html_jogos(jogos, c)

    css = (BASE / "estilo.css").read_text()
    js = (BASE / "jogos.js").read_text()
    falha = ("function falhaImagem(i){if(i.dataset.remota&&!i.dataset.tentou){i.dataset.tentou=1;i.src=i.dataset.remota;return}"
             "i.onerror=null;i.src=i.dataset.reserva;var f=i.closest('.figura'),t=f&&f.querySelector('.tipo-img');if(t)t.textContent='Ilustração (imagem original indisponível)'}")
    destaque = c.get("resumo", "")
    pagina = f"""<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{NOME} · A semana · {e(data_pt(data, False))}</title><meta name="description" content="{e(destaque)}">
{og_html(f"{NOME} · A semana em perspetiva · {data_pt(data, False)}", destaque, f"{URL_SITE}{data}/")}
<style>{css}</style><script>{TEMA_JS}{falha}</script></head><body class="semanal"><main id="inicio">
<div class="top"><span>Edição n.º {e(c.get("numero", ""))} · {dia.day:02d} {MESES[dia.month - 1][:3]} {dia.year} · Edição de domingo</span><span class="top-dir"><span class="lema">Portugal · Leitura independente</span>{BOTAO_TEMA}</span></div>
<h1 class="masthead">{titulo_html("../")}</h1>
<p class="kicker">A semana em perspetiva</p>
<p class="deck">{e(data_pt(data).capitalize())} · resumo de {e(dia_curto(inicio))} a {e(dia_curto(ontem))} · {len(D)} notícias da semana · Agenda Porto · Quiz</p>
<nav aria-label="Secções"><a href="../">Arquivo</a><a href="#resumo"><span class="longo">A semana em 2 minutos</span><span class="curto">Resumo</span></a><a href="#semana"><span class="longo">Notícias da semana</span><span class="curto">Notícias</span></a><a href="#semana-que-vem"><span class="longo">A semana que vem</span><span class="curto">Próxima semana</span></a><a href="#cultura">Cultura</a><a href="#edicoes">Edições</a><a href="#agenda"><span class="longo">Agenda Porto</span><span class="curto">Agenda</span></a><a href="#jogos">Quiz</a></nav>
{briefing}{caixa_correcoes(data)}{semana}{cultura}{agenda}{jogos_html}
<footer><p>Edição de domingo: seleção editorial das notícias mais importantes e com mais cobertura e seguimento ao longo da semana, atualizadas com o que mudou desde então. Não usamos dados de comentários nem de audiências. Cada notícia indica o estado da informação, a data e as fontes consultadas; procuramos confirmação em duas fontes independentes e assinalamos quando só há uma. Os textos são sínteses originais.</p>
<p><strong>Sobre este jornal:</strong> {AVISO_IA} Projeto pessoal, sem publicidade e sem fins comerciais. Os erros detetados são corrigidos e registados na <a href="../#correcoes">lista de correções</a>.</p>
<p>Edição publicada em <a href="{URL_SITE}{data}/">{URL_SITE}{data}/</a> · <a href="../">Ver todas as edições</a></p></footer></main>
<a class="topo" href="#inicio" aria-label="Voltar ao topo">↑</a>
<script type="application/json" id="dados-jogos">{json.dumps(jogos, ensure_ascii=False)}</script><script>{js}</script><script>{UI_JS}</script></body></html>"""
    (pasta / "index.html").write_text(pagina)
    (assets / "imagens.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    atualizar_arquivo(data, c)
    li = texto_linkedin(data, c)
    print(f"Texto do LinkedIn: ferramentas/linkedin/{data}.txt ({len(li)} caracteres)")
    print(f"Edição semanal {data}: {len(D)} destaques, {len(manifest)} imagens, {len(pagina)//1024} KB")


ASSINATURA_LI = ("🤖 «O Dia em Perspetiva» é um projeto pessoal, escrito com IA a partir de regras editoriais "
                 "definidas por mim. Fontes indicadas em cada notícia.")
HASHTAGS_LI = "#Notícias #Portugal #InteligênciaArtificial #Tecnologia #Leitura"


def texto_linkedin(data, c):
    """Texto pronto a colar no LinkedIn (sem markdown), gravado em ferramentas/linkedin/AAAA-MM-DD.txt."""
    d = dt.date.fromisoformat(data)
    if c.get("linkedin_texto"):  # texto especial escrito à mão (ex.: lançamento); substitui o automático
        txt = c["linkedin_texto"].strip()
        if len(txt) > 2900:
            raise SystemExit(f"Texto do LinkedIn demasiado longo ({len(txt)} caracteres; máximo 3000)")
        (BASE / "linkedin").mkdir(exist_ok=True)
        (BASE / "linkedin" / f"{data}.txt").write_text(txt + "\n")
        return txt
    if c.get("tipo") == "semanal":
        D = c["destaques"]
        linhas = [f"📰 A semana em perspetiva · {DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]}", "",
                  c.get("linkedin_abertura") or D[0]["titulo"], "", "As notícias da semana:"]
        linhas += [f"▪️ {x['titulo']}" for x in D[1:6]] + [""]
        if c.get("semana_que_vem"):
            a = c["semana_que_vem"][0]
            linhas += [f"📅 Na semana que vem ({a['quando']}): {a['texto']}", ""]
        linhas += ["Também nesta edição: destaques culturais da semana, agenda do Porto e um quiz sobre as notícias.", "",
                   f"👉 Edição completa: {URL_SITE}{data}/", "", ASSINATURA_LI, "", HASHTAGS_LI]
        txt = "\n".join(linhas)
        if len(txt) > 2900:
            raise SystemExit(f"Texto do LinkedIn demasiado longo ({len(txt)} caracteres; máximo 3000)")
        (BASE / "linkedin").mkdir(exist_ok=True)
        (BASE / "linkedin" / f"{data}.txt").write_text(txt + "\n")
        return txt
    man = next((i for i, n in enumerate(c["noticias"]) if n.get("manchete")), None)
    abertura = c.get("linkedin_abertura") or (c["noticias"][man]["titulo"] if man is not None else c.get("resumo", ""))
    pontos = [it["texto"] for it in c.get("em_2_minutos", []) if it.get("noticia") != (man + 1 if man is not None else None)][:4]
    linhas = [f"📰 O Dia em Perspetiva · {DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]}", "", abertura, ""]
    if pontos:
        linhas += ["Em 2 minutos:"] + [f"▪️ {t}" for t in pontos] + [""]
    if c.get("acompanhar"):
        a = c["acompanhar"][0]
        linhas += [f"📅 A acompanhar ({a['quando']}): {a['texto']}", ""]
    linhas += ["Também nesta edição: cultura, agenda do Porto, Sudoku e caça-palavras.", "",
               f"👉 Edição completa: {URL_SITE}{data}/", "", ASSINATURA_LI, "", HASHTAGS_LI]
    txt = "\n".join(linhas)
    if len(txt) > 2900:
        raise SystemExit(f"Texto do LinkedIn demasiado longo ({len(txt)} caracteres; máximo 3000)")
    pasta = BASE / "linkedin"
    pasta.mkdir(exist_ok=True)
    (pasta / f"{data}.txt").write_text(txt + "\n")
    return txt


def formato_arquivo(data, c):
    jp = BASE / "jogos" / f"{data}.json"
    jogos = descricao_jogos(json.loads(jp.read_text())) if jp.exists() else "Sudoku e caça-palavras"
    if c.get("tipo") == "semanal":
        return f"Resumo da semana · {len(c['destaques'])} notícias · destaques culturais · Agenda do Porto · {jogos}"
    return f"{len(c['noticias'])} notícias · 4 artigos culturais · Agenda do Porto · {jogos}"


def atualizar_arquivo(data, c):
    arq_p = BASE / "arquivo.json"
    arq = json.loads(arq_p.read_text())
    arq = [x for x in arq if x["data"] != data]
    arq.append({"data": data, "numero": c.get("numero", ""), "resumo": c.get("resumo", ""), "formato": formato_arquivo(data, c)})
    arq.sort(key=lambda x: x["data"], reverse=True)
    arq_p.write_text(json.dumps(arq, ensure_ascii=False, indent=1))
    css = (BASE / "estilo.css").read_text()
    corr = correcoes()
    lista_corr = (f'<ul class="lista-correcoes">{"".join(item_correcao(x, "./") for x in corr)}</ul>' if corr
                  else '<p class="game-note">Ainda não houve correções.</p>')
    itens = []
    for i, x in enumerate(arq):
        n = f" · n.º {e(x['numero'])}" if x.get("numero") else ""
        itens.append(f'<li class="{"novo" if i == 0 else ""}"><div class="d"><a href="./{x["data"]}/">{e(data_pt(x["data"], False))}</a><small>{e(DIAS[dt.date.fromisoformat(x["data"]).weekday()].capitalize())}{n}</small></div>'
                     f'<p>{e(x.get("resumo", ""))}{"<br>" if x.get("resumo") else ""}{e(x.get("formato", ""))}</p></li>')
    pagina = f"""<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{NOME} · Arquivo</title><meta name="description" content="Jornal diário feito com IA: notícias com fontes verificadas, cultura, agenda do Porto e jogos. Sem anúncios.">
{og_html(NOME, "Jornal diário feito com IA: notícias com fontes verificadas, cultura, agenda do Porto e jogos. Sem anúncios.", URL_SITE)}
<style>{css}</style><script>{TEMA_JS}</script></head><body><main><div class="top"><span>Arquivo · {len(arq)} edições</span><span class="top-dir"><span class="lema">Portugal · Leitura independente</span>{BOTAO_TEMA}</span></div>
<h1 class="masthead">{titulo_html("./")}</h1><p class="deck">Todas as edições, da mais recente para a mais antiga</p>
<nav aria-label="Atalhos"><a href="./{arq[0]["data"]}/">Edição mais recente</a><a href="#correcoes">Correções</a></nav>
<section class="newssection"><h2>Arquivo de edições</h2><p class="edition-count">{len(arq):02d} edições</p><ul class="arquivo-lista">{"".join(itens)}</ul></section>
<section class="newssection" id="correcoes"><h2>Correções e atualizações</h2><p class="edition-count">erros detetados depois da publicação, do mais recente para o mais antigo</p>{lista_corr}</section>
<footer><p><strong>Sobre este jornal:</strong> {AVISO_IA} Projeto pessoal, sem publicidade e sem fins comerciais.</p><p>Cada edição tem endereço permanente no formato {URL_SITE}AAAA-MM-DD/. As edições anteriores a 6 de novembro de 2026 mantêm o formato original.</p></footer></main></body></html>"""
    (RAIZ / "index.html").write_text(pagina)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    construir(sys.argv[1])
