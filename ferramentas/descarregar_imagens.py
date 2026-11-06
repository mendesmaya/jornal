#!/usr/bin/env python3
"""Corre no GitHub Actions. Para cada edição com assets/imagens.json:
- consulta a API do Wikimedia Commons (autoria, licença, URL da miniatura);
- descarrega a imagem para assets/img/;
- escreve assets/creditos.json e atualiza no HTML o src local e os créditos.
Se a imagem não existir, troca-a pela ilustração de reserva e assinala-o."""
import html, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

UA = "JornalDoDia/1.0 (https://github.com/mendesmaya/jornal; jornal diario estatico)"
API = "https://commons.wikimedia.org/w/api.php"
raiz = Path(__file__).resolve().parent.parent


def pedir(url, binario=False):
    for t in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                dados = r.read()
                return dados if binario else json.loads(dados), r.headers.get("Content-Type", "")
        except Exception as ex:
            print("tentativa falhou", url, ex, file=sys.stderr)
            time.sleep(4 * (t + 1))
    return None, ""


def limpar(txt):
    txt = re.sub(r"<[^>]+>", "", txt or "")
    txt = html.unescape(re.sub(r"\s+", " ", txt)).strip()
    txt = txt.replace("No machine-readable author provided.", "").replace("assumed (based on copyright claims).", "")
    return re.sub(r"\bUser:", "", txt).strip(" .") 


def info_commons(nome):
    q = {"action": "query", "format": "json", "prop": "imageinfo", "titles": "File:" + nome,
         "iiprop": "url|extmetadata", "iiurlwidth": "1000"}
    dados, _ = pedir(API + "?" + urllib.parse.urlencode(q))
    if not dados:
        return None
    for pag in dados.get("query", {}).get("pages", {}).values():
        if "imageinfo" not in pag:
            return None
        ii = pag["imageinfo"][0]
        md = ii.get("extmetadata", {})
        autor = limpar(md.get("Artist", {}).get("value", "")) or "Autor não indicado no Commons"
        lic = limpar(md.get("LicenseShortName", {}).get("value", "")) or "Licença não indicada"
        return {"thumb": ii.get("thumburl") or ii.get("url"), "autor": autor[:160], "licenca": lic,
                "origem": ii.get("descriptionurl", "")}
    return None


for man in sorted(raiz.glob("20??-??-??/assets/imagens.json")):
    assets = man.parent
    pagina = assets.parent / "index.html"
    cp = assets / "creditos.json"
    creditos = json.loads(cp.read_text()) if cp.exists() else {}
    doc = pagina.read_text()
    alterou = False
    for item in json.loads(man.read_text()):
        f = item["ficheiro"]
        if f in creditos:
            continue
        destino = assets / f
        destino.parent.mkdir(parents=True, exist_ok=True)
        if item.get("commons"):
            info = info_commons(item["commons"])
            if not info:
                creditos[f] = {"estado": "falhou", "motivo": "ficheiro não encontrado no Commons"}
            else:
                dados, tipo = pedir(info["thumb"], binario=True)
                if dados and tipo.startswith("image/") and len(dados) > 500:
                    destino.write_bytes(dados)
                    creditos[f] = {"estado": "ok", **{k: info[k] for k in ("autor", "licenca", "origem")}}
                else:
                    creditos[f] = {"estado": "falhou", "motivo": "download falhou"}
        else:
            dados, tipo = pedir(item["url"], binario=True)
            if dados and tipo.startswith("image/"):
                destino.write_bytes(dados)
                creditos[f] = {"estado": "ok-externo"}
            else:
                creditos[f] = {"estado": "falhou", "motivo": "download falhou"}
        n = f'{item["id"]:02d}'
        c = creditos[f]
        if c["estado"] in ("ok", "ok-externo"):
            doc = re.sub(rf'(<img id="img-{n}" src=")[^"]*(")', rf'\g<1>assets/{f}\g<2>', doc)
        if c["estado"] == "ok":
            novo = (f'Autoria: {html.escape(c["autor"])} · Licença: {html.escape(c["licenca"])} · '
                    f'<a href="{html.escape(c["origem"])}" rel="noopener">origem</a>')
            doc = re.sub(rf'(<span class="cred" id="cred-{n}">).*?(</span></figcaption>)', lambda m: m.group(1) + novo + m.group(2), doc, flags=re.S)
        elif c["estado"] == "falhou":
            doc = re.sub(rf'(<img id="img-{n}" src=")[^"]*(")', rf'\g<1>{item["reserva"]}\g<2>', doc)
            doc = re.sub(rf'(<span class="tipo-img" id="tipo-{n}">).*?(</span>)', r'\g<1>Ilustração do jornal (imagem original indisponível)\g<2>', doc)
            doc = re.sub(rf'(<span class="cred" id="cred-{n}">).*?(</span></figcaption>)', r'\g<1>Ilustração gráfica de O Dia em Perspetiva, de uso livre.\g<2>', doc, flags=re.S)
        alterou = True
        print(f, c["estado"])
    if alterou:
        pagina.write_text(doc)
        cp.write_text(json.dumps(creditos, ensure_ascii=False, indent=1))
