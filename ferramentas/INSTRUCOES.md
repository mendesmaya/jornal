# Instruções da edição diária — O Dia em Perspetiva

Repositório: `mendesmaya/jornal` (branch `main`, GitHub Pages a partir da raiz).
Endereço de cada edição: `https://mendesmaya.github.io/jornal/AAAA-MM-DD/`.
Fuso horário de referência: Europe/Lisbon. A data da edição é a data de Lisboa no momento da execução.

## Horário
A tarefa agendada começa às 8h31 (Lisboa) para que a edição e o texto do LinkedIn estejam prontos por volta das 9h. A notificação final deve sair assim que a edição estiver publicada e as imagens confirmadas.

## Regra prévia
- Se `AAAA-MM-DD/index.html` já existir e o pedido for apenas publicá-lo, usar esse ficheiro. Não recriar nem reescrever; aplicar só as correções pedidas.
- Nunca apagar nem alterar pastas de edições anteriores (exceto correções pedidas pela dona do jornal).

## Conteúdo obrigatório (por edição)
18 notícias, por esta ordem de destaque na página:
- Cibersegurança: 3 · Inteligência Artificial: 3 · Tecnologia: 2 (bloco digital em destaque, no topo)
- Mundo: 4 · Portugal: 4
- Espaço: 2 (secção `espaco`, logo a seguir a Portugal e antes da Cultura; desde a edição de 2026-11-11): exploração espacial, missões, lançamentos, astronomia e ciência planetária, com as mesmas regras de verificação; incluir missões europeias/portuguesas quando houver.

Notícias positivas integram-se naturalmente nas secções, sem rótulo nem categoria própria.

## Formato desde a edição de 2026-11-12 (obrigatório; `construir.py` valida)
Modelo de referência: `ferramentas/conteudo/2026-11-12.json` (substitui as edições anteriores como modelo).
- **Manchete**: exatamente uma notícia com `"manchete": true` — a mais importante do dia, de qualquer secção. Aparece no topo, em destaque e com o texto completo; a secção dela mostra uma ligação para o topo. Continua a contar para as 18 e para a sua secção.
- **`em_2_minutos`**: 5 a 6 entradas `{"texto": "...", "noticia": N}` com o essencial do dia, uma frase cada (máx. ~35 palavras), por ordem de importância. `N` é a posição (1–18) da notícia no array `noticias`; para remeter para outra parte usar `"ancora": "cultura"` / `"agenda"` / `"jogos"` em vez de `noticia`. Só factos que já estão nas notícias da edição, com o mesmo cuidado com estados (declaração ≠ facto).
- **`acompanhar`** («O que acompanhar»): 3 a 4 entradas `{"quando": "Sexta, 13 nov.", "texto": "...", "noticia": N}` (ou `ancora`) sobre o que vem aí nos próximos dias: votações, lançamentos, cimeiras, greves, prazos, decisões esperadas. Só datas confirmadas nas fontes consultadas; usar «previsto», «não antes de», «se não houver adiamento» quando for o caso. `noticia`/`ancora` são opcionais.
- **Imagens**: só são mostradas na manchete, na primeira notícia de cada secção (abertura: Cibersegurança 1.ª, Mundo 1.ª, Portugal 1.ª, Espaço 1.ª — sem contar a manchete) e nos 4 artigos de cultura. Nas outras notícias o campo `imagem` é opcional e ignorado. Escolher para as aberturas imagens fortes; preferir fotografias a logótipos. Logótipos e esquemas em SVG aparecem inteiros; para forçar, usar `"ajuste": "conter"` (ou `"cobrir"`) na imagem.
- Na página, as notícias (exceto a manchete) e os artigos de cultura mostram o 1.º parágrafo e o resto em «Continuar a ler»: o 1.º parágrafo tem de funcionar sozinho (quem, o quê, quando, onde e o essencial).
- **`linkedin_abertura`**: uma frase de abertura forte para o LinkedIn (máx. ~30 palavras), sobre a manchete ou o facto mais marcante, informativa e sem «clickbait», com o mesmo rigor de estados. `construir.py` gera com ela `ferramentas/linkedin/AAAA-MM-DD.txt`: abertura, até 4 pontos do «Em 2 minutos» (sem repetir a manchete), o 1.º item do «O que acompanhar», ligação, assinatura de crédito à IA e hashtags. Não alterar a assinatura nem as hashtags. O campo opcional `linkedin_texto` substitui o texto automático por um texto escrito à mão (usado na publicação de lançamento de 2026-11-12); nas edições normais não o usar.
- Fontes e verificação aparecem recolhidas por baixo de cada notícia; o `estado` aparece por baixo do título, por isso deve ser curto (idealmente até ~20 palavras).

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
2. Pesquisar e escrever `ferramentas/conteudo/AAAA-MM-DD.json` (modelo: a edição de 2026-11-12; `numero` = número anterior + 1), incluindo manchete, `em_2_minutos` e `acompanhar`.
3. Gerar os jogos; `python3 ferramentas/construir.py AAAA-MM-DD` (valida contagens e atualiza `index.html` do arquivo).
4. Testar a página (sem erros de JavaScript, jogos funcionais, ligações de «Em 2 minutos» a apontar para as notícias certas, modo escuro legível).
5. Commit e push para `main`.
6. Esperar pela ação das imagens (~1–3 min), fazer `git pull` e confirmar em `AAAA-MM-DD/assets/creditos.json` que todas as imagens ficaram `ok`. Para cada `falhou`, escolher outra imagem do Commons, reconstruir e voltar a publicar.
7. Confirmar que `https://mendesmaya.github.io/jornal/AAAA-MM-DD/` responde.
8. **Texto do LinkedIn**: no fim, enviar à dona do jornal o conteúdo integral de `ferramentas/linkedin/AAAA-MM-DD.txt`, pronto a colar (não publicar no LinkedIn: ela revê e publica). Numa execução agendada, incluí-lo na notificação final (PushNotification, dentro de <routine_summary>: primeira frase com o endereço da edição, depois o texto do LinkedIn tal como está no ficheiro, depois o que não foi possível confirmar) e também na resposta final.
