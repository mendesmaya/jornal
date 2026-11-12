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

## Pessoas, suspeitas e correções
- **Presunção de inocência**: suspeitos, detidos e arguidos são sempre referidos como tal («suspeito de», «indiciado por»), nunca como culpados. **Não nomear pessoas que não sejam figuras públicas** quando são suspeitas, arguidas, vítimas ou doentes; usar a função ou descrição («seis funcionários de uma empresa de assistência em escala»). Figuras públicas podem ser nomeadas quando o caso diz respeito às suas funções.
- **Aviso de IA**: o rodapé de todas as páginas mostra automaticamente o aviso de que o jornal é feito com IA (AI Act, art. 50.º). Não o remover (por decisão da dona do jornal, fica só no rodapé).
- **Correções** (só quando a dona do jornal as pedir, ou quando a rotina detetar um erro claro numa edição anterior ao pesquisar): corrigir o texto da notícia no JSON dessa edição, acrescentar-lhe `"correcao": "O que estava errado e o que foi corrigido (data)."`, reconstruir essa edição e registar a correção em `ferramentas/correcoes.json` com `{"data": "AAAA-MM-DD (dia da correção)", "edicao": "AAAA-MM-DD", "ancora": "#nNN", "texto": "..."}`. As correções dos últimos 7 dias aparecem numa caixa no topo das edições seguintes; todas ficam na página do arquivo. Nunca apagar uma correção.

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

## Jogos (mudam com o dia da semana, desde 2026-11-12)
| Dia | Jogos |
|---|---|
| Segunda | Sudoku e caça-palavras |
| Terça | Jogo das diferenças e 2048 |
| Quarta | Sudoku e nonograma |
| Quinta | Campo minado e jogo da cobra |
| Sexta | 2048 e Sudoku |
| Sábado | Corrida do dinossauro e puzzle (com a imagem da manchete) |
| Domingo | Quiz da semana (edição de domingo) |

`python3 ferramentas/jogos.py AAAA-MM-DD [P1 … P15]` escolhe sozinho os jogos do dia (tabela `JOGOS_DIA`). As 15 palavras (ligadas à edição, máx. 15 letras, sem repetições) só são obrigatórias à **segunda-feira** (caça-palavras); nos outros dias podem ser passadas e são ignoradas. O script garante Sudoku de dificuldade média (30–34 pistas, resolúvel só com casas únicas e números escondidos, sem pares nem tentativa-erro) com solução única (com modo rascunho na página), nonograma 10×10 com solução lógica única, jogo das diferenças com 7 diferenças bem separadas, e grelhas diferentes das anteriores (`historico_jogos.json`). 2048, campo minado, cobra e dinossauro usam uma semente do dia (o mesmo desafio para todos os leitores). Ao sábado, a manchete deve ter uma imagem nítida e não um logótipo, porque é a imagem do puzzle.

## Edição de domingo: «A semana em perspetiva» (desde 2026-11-15)
Ao domingo **não** há edição normal: em vez das 18 notícias e dos 4 artigos culturais, faz-se o resumo da semana. Esta secção prevalece sobre qualquer outra instrução (incluindo a da tarefa agendada) quando o dia é domingo.
- JSON com `"tipo": "semanal"` (ver `construir.py`, função `construir_semanal`, e o exemplo abaixo).
- **Pesquisa**: ler os JSON de segunda a sábado em `ferramentas/conteudo/`, escolher as 8–10 notícias **mais importantes e com mais cobertura e seguimento** (as que voltaram em várias edições ou dominaram a imprensa). Não temos números de comentários nem de audiências: não afirmar que foram «as mais comentadas» como facto medido. Para cada uma, pesquisar o que mudou desde a publicação (desenvolvimento novo, desmentido, decisão) e confirmar com fontes atuais.
- `destaques` (8–10, por ordem de importância; o 1.º é «A notícia da semana»): `titulo`, `seccao` (chaves das secções), `data`, `estado`, `texto` (2–3 parágrafos; o 1.º funciona sozinho), `desenvolvimento` (opcional: o que mudou desde então, com data), `verificacao`, `fontes`, `edicao` e `noticia` (edição e posição da notícia original, para a ligação «Na edição de…»). `imagem` obrigatória nos 3 primeiros (Commons, mesmas regras).
- `em_2_minutos` (5–6, com `"destaque": N`, posição 1–10 no array `destaques`) → «A semana em 2 minutos».
- `semana_que_vem` (4–6, `{"quando", "texto"}`): o que acompanhar na semana seguinte, só com datas confirmadas.
- `quiz` (6–10 perguntas): `{"pergunta", "opcoes": [3–4], "certa": índice a partir de 0, "explicacao", "destaque": N}` (ou `"edicao"` + `"noticia"`). Perguntas factuais, sem ratoeiras, sobre notícias da semana; uma única resposta certa, confirmada no texto da notícia.
- `agenda_aviso` e `agenda` (domingo e os três dias seguintes), como nas outras edições.
- `linkedin_abertura`: frase de abertura do texto do LinkedIn da semana.
- «Destaques culturais da semana» e «As edições da semana» são gerados automaticamente a partir de `ferramentas/arquivo_temas.md` e `ferramentas/arquivo.json` (não escrever nada).
- `jogos.py` gera só a lista do quiz; não acrescentar linha a `arquivo_temas.md` ao domingo.
- Exemplo mínimo de chaves: `{"data", "numero", "tipo": "semanal", "resumo", "em_2_minutos", "destaques", "semana_que_vem", "quiz", "agenda_aviso", "agenda", "linkedin_abertura"}`.

## Passo a passo
1. `git clone` / `git pull` do repositório; verificar se a edição do dia já existe.
2. Pesquisar e escrever `ferramentas/conteudo/AAAA-MM-DD.json` (modelo: a edição de 2026-11-12; `numero` = número anterior + 1), incluindo manchete, `em_2_minutos` e `acompanhar`.
3. Gerar os jogos; `python3 ferramentas/construir.py AAAA-MM-DD` (valida contagens e atualiza `index.html` do arquivo).
4. Testar a página (sem erros de JavaScript, os dois jogos do dia funcionais, ligações de «Em 2 minutos» a apontar para as notícias certas, modo escuro legível).
5. Commit e push para `main`.
6. Esperar pela ação das imagens (~1–3 min), fazer `git pull` e confirmar em `AAAA-MM-DD/assets/creditos.json` que todas as imagens ficaram `ok`. Para cada `falhou`, escolher outra imagem do Commons, reconstruir e voltar a publicar.
7. Confirmar que `https://mendesmaya.github.io/jornal/AAAA-MM-DD/` responde.
8. **Texto do LinkedIn**: no fim, enviar à dona do jornal o conteúdo integral de `ferramentas/linkedin/AAAA-MM-DD.txt`, pronto a colar (não publicar no LinkedIn: ela revê e publica). Numa execução agendada, incluí-lo na notificação final (PushNotification, dentro de <routine_summary>: primeira frase com o endereço da edição, depois o texto do LinkedIn tal como está no ficheiro, depois o que não foi possível confirmar) e também na resposta final.
