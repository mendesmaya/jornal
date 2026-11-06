#!/usr/bin/env python3
"""Corre no GitHub Actions: descarrega para AAAA-MM-DD/assets/ as imagens listadas
em assets/imagens.json que ainda não existem e troca as ligações remotas pelas locais."""
import json, re, sys, time, urllib.request
from pathlib import Path
UA = "JornalDoDia/1.0 (+https://github.com/mendesmaya/jornal)"
raiz = Path(__file__).resolve().parent.parent
mudou = False
for man in sorted(raiz.glob("20??-??-??/assets/imagens.json")):
    assets = man.parent
    pagina = assets.parent / "index.html"
    html = pagina.read_text()
    for item in json.loads(man.read_text()):
        destino = assets / item["ficheiro"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not destino.exists():
            for tentativa in range(3):
                try:
                    req = urllib.request.Request(item["url"], headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        dados = r.read()
                        tipo = r.headers.get("Content-Type", "")
                    if not tipo.startswith("image/") or len(dados) < 500:
                        raise ValueError(f"resposta não é imagem: {tipo}")
                    destino.write_bytes(dados)
                    print("ok", destino)
                    break
                except Exception as ex:
                    print("falhou", item["url"], ex, file=sys.stderr)
                    time.sleep(3)
        if destino.exists():
            local = f'src="assets/{item["ficheiro"]}"'
            remoto = 'src="' + item["url"].replace("&", "&amp;") + '"'
            if remoto in html:
                html = html.replace(remoto, local)
                mudou = True
    pagina.write_text(html)
print("alterações" if mudou else "sem alterações")
