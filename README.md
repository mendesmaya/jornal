# Jornal do Dia

Jornal diário estático publicado no GitHub Pages: https://mendesmaya.github.io/jornal/

## Estrutura

- `index.html` — arquivo de edições (a mais recente primeiro).
- `AAAA-MM-DD/index.html` — edição do dia, com estilos e jogos incluídos (funciona sem serviços externos).
- `AAAA-MM-DD/assets/` — imagens (`img/`), ilustrações de reserva, `imagens.json` e `creditos.json`.
- `ferramentas/` — gerador das edições:
  - `INSTRUCOES.md` — regras editoriais e passo a passo de cada edição.
  - `conteudo/AAAA-MM-DD.json` — conteúdo de cada edição.
  - `jogos.py` — gera e valida o Sudoku (solução única) e o caça-palavras (15 palavras).
  - `construir.py` — monta a edição e atualiza o arquivo.
  - `descarregar_imagens.py` + `.github/workflows/imagens.yml` — descarregam as imagens para `assets/` e preenchem autoria e licença a partir da API do Wikimedia Commons.

As edições anteriores a 6 de novembro de 2026 mantêm o formato original e não são alteradas.
