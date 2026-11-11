# Instruções da edição diária — O Dia em Perspetiva

Repositório: `mendesmaya/jornal` (branch `main`, GitHub Pages a partir da raiz).
Endereço de cada edição: `https://mendesmaya.github.io/jornal/AAAA-MM-DD/`.
Fuso horário de referência: Europe/Lisbon. A data da edição é a data de Lisboa no momento da execução.

## Regra prévia
- Se `AAAA-MM-DD/index.html` já existir e o pedido for apenas publicá-lo, usar esse ficheiro. Não recriar nem reescrever; aplicar só as correções pedidas.
- Nunca apagar nem alterar pastas de edições anteriores (exceto correções pedidas pela dona do jornal).

## Conteúdo obrigatório (por edição)
18 notícias, por esta ordem de destaque na página:
- Cibersegurança: 3 · Inteligência Artificial: 3 · Tecnologia: 2 (bloco digital em destaque, no topo)
- Mundo: 4 · Portugal: 4
- Espaço: 2 (secção `espaco`, logo a seguir a Portugal e antes da Cultura; desde a edição de 2026-11-11): exploração espacial, missões, lançamentos, astronomia e ciência planetária, com as mesmas regras de verificação; incluir missões europeias/portuguesas quando houver.

Notícias positivas integram-se naturalmente nas secções, sem rótulo nem categoria própria.

Cada notícia (campo no JSON):
- `titulo` informativo; `texto` com 2–4 parágrafos de contexto; `data` (AAAA-MM-DD) do acontecimento ou da informação.
- `estado`: distinguir factos confirmados, declarações, propostas, previsões e anúncios. Nunca apresentar uma intenção como medida aplicada.
- `verificacao`: `independentes` = 2 quando há duas fontes independentes; = 1 com `nota` que atribui claramente a informação à fonte disponível.
- `fontes`: só ligações efetivamente consultadas (ou citadas por uma fonte consultada, marcadas “(citado)”).
- `imagem`: ver secção Imagens.

Privilegiar fontes primárias, organismos oficiais e meios credíveis (Lusa, RTP, Público, Observador, Expresso, Renascença, AP, Reuters, AFP, BBC, Euronews, organismos oficiais; em ciber/IA/tec: avisos oficiais, SecurityWeek, The Hacker News, BleepingComputer, The Record, Ars Technica, The Verge). Não inventar notícias, citações, fontes, imagens, datas ou ligações. Assinalar o que não foi possível confirmar. Sínteses originais: não copiar frases das fontes.

## Cultura (4 artigos, `rubrica`)
1. `cinema` — filme recente **em exibição em Portugal** (confirmar em filmSPOT/cinecartaz/exibidores). Sem spoilers; sinopse breve, pontos fortes, pontos fracos, avaliação equilibrada. Dizer que a apreciação resulta das críticas consultadas.
2. `artista` — artista famoso: história, estilo, obras principais, curiosidades.
3. `sabias` — curiosidade educativa sobre arte, cinema, fotografia, música, etc.
4. `movimento` — movimento, coletivo ou iniciativa cultural ativa em Portugal (origem, participantes, proposta, relevância), com atenção a projetos independentes, arte urbana, música, cinema, comunidades artísticas.
Variar temas: consultar `ferramentas/arquivo_temas.md` e acrescentar lá os temas usados.

## Agenda do Porto
4 dias: o dia da edição e os três seguintes, 3–5 eventos por dia. Para cada evento: nome, descrição breve, horário, local, preço (ou entrada gratuita) e ligação oficial/bilheteira. Fontes preferidas: Casa da Música (casadamusica.com/agenda), Agenda Porto da Câmara (agenda-porto.pt), Teatro Municipal do Porto, TNSJ, Serralves, Coliseu, sites dos organizadores. Dados em falta ficam “Por confirmar” com `nota`; nunca inventar horários, preços ou disponibilidade.

## Imagens
- Usar ficheiros do **Wikimedia Commons** (campo `commons` com o nome exato do ficheiro, encontrado numa pesquisa com `allowed_domains: ["commons.wikimedia.org"]`).
- `tipo`: `acontecimento` (foto do próprio acontecimento), `arquivo`, `ilustrativa`, `oficial`, `obra`, `cartaz`. A `legenda` deve deixar claro se a imagem não mostra o acontecimento.
- Não usar cartazes de filmes, personagens protegidas, obras protegidas nem fotografias de agências sem licença; nesses casos usar imagem ilustrativa e dizê-lo.
- Autoria e licença são lidas automaticamente da API do Commons pela ação `Guardar imagens das edições`, que também descarrega a imagem para `AAAA-MM-DD/assets/img/`. Se o ficheiro não existir, a ação troca-o por uma ilustração de reserva marcada como tal.

## Jogos
`python3 ferramentas/jogos.py AAAA-MM-DD P1 … P15` com 15 palavras ligadas à edição (máx. 15 letras, sem repetições). O script garante Sudoku moderadamente difícil com solução única, caça-palavras com as 15 palavras validadas e grelhas diferentes das anteriores (`historico_jogos.json`).

## Passo a passo
1. `git clone` / `git pull` do repositório; verificar se a edição do dia já existe.
2. Pesquisar e escrever `ferramentas/conteudo/AAAA-MM-DD.json` (ver a edição de 2026-11-06 como modelo; `numero` = número anterior + 1).
3. Gerar os jogos; `python3 ferramentas/construir.py AAAA-MM-DD` (valida contagens e atualiza `index.html` do arquivo).
4. Testar a página (sem erros de JavaScript, jogos funcionais).
5. Commit e push para `main`.
6. Esperar pela ação das imagens (~1–3 min), fazer `git pull` e confirmar em `AAAA-MM-DD/assets/creditos.json` que todas as imagens ficaram `ok`. Para cada `falhou`, escolher outra imagem do Commons, reconstruir e voltar a publicar.
7. Confirmar que `https://mendesmaya.github.io/jornal/AAAA-MM-DD/` responde.
