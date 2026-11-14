"""Edição em inglês: traduz os textos fixos da página (interface, rodapé, jogos).

O conteúdo (notícias, cultura, agenda) vem já traduzido de ferramentas/conteudo/AAAA-MM-DD.en.json,
escrito pela rotina diária. Este módulo só troca os textos fixos gerados por construir.py e jogos.js.
A página em inglês fica em AAAA-MM-DD/en/index.html e usa as imagens de AAAA-MM-DD/assets/.
"""
import re

# Menu (letras desenhadas à mão: og.py não tem F, H, K, W nem Y — escolher palavras sem essas letras)
NAV = [
    ('<a href="../">Arquivo</a>', '<a href="../">Past issues</a>'),
    ('<span class="longo">Em 2 minutos</span><span class="curto">Resumo</span>', '<span class="longo">In 2 minutes</span><span class="curto">Digest</span>'),
    ('<span class="longo">Tecnologia, IA e Cibersegurança</span><span class="curto">Digital</span>', '<span class="longo">Digital and AI</span><span class="curto">Digital</span>'),
    ('<a href="#mundo">Mundo</a>', '<a href="#mundo">Global</a>'),
    ('<a href="#espaco">Espaço</a>', '<a href="#espaco">Space</a>'),
    ('<a href="#cultura">Cultura</a>', '<a href="#cultura">Culture</a>'),
    ('<span class="longo">Agenda Porto</span><span class="curto">Agenda</span>', '<span class="longo">Porto events</span><span class="curto">Events</span>'),
    ('<a href="#jogos">Jogos</a>', '<a href="#jogos">Games</a>'),
    # domingo
    ('<span class="longo">A semana em 2 minutos</span><span class="curto">Resumo</span>', '<span class="longo">The week in 2 minutes</span><span class="curto">Digest</span>'),
    ('<span class="longo">Notícias da semana</span><span class="curto">Notícias</span>', '<span class="longo">Stories</span><span class="curto">Stories</span>'),
    ('<span class="longo">A semana que vem</span><span class="curto">Próxima semana</span>', '<span class="longo">Next week</span><span class="curto">Next week</span>'),
    ('<a href="#edicoes">Edições</a>', '<a href="#edicoes">Issues</a>'),
    ('<a href="#jogos">Quiz</a>', '<a href="#jogos">Quiz</a>'),
]

SECCOES_EN = {"Cibersegurança": "Cybersecurity", "Inteligência Artificial": "Artificial Intelligence", "Tecnologia": "Technology",
              "Mundo": "World", "Portugal": "Portugal", "Espaço": "Space", "Manchete": "Lead story",
              "A notícia da semana": "Story of the week",
              "Cinema em análise": "Film review", "Conhece o artista": "Meet the artist", "Sabias que…?": "Did you know…?",
              "Cultura em movimento": "Culture on the move"}

# Textos da página (ordem: os mais longos primeiro, para não partir frases)
HTML = [
    # rodapé
    ("Cada notícia indica o estado da informação (facto confirmado, declaração, proposta, previsão ou anúncio), a data e as fontes consultadas. Procuramos confirmação em duas fontes independentes; quando só há uma, isso fica assinalado. Os textos são sínteses originais. As imagens têm autoria e licença identificadas; imagens de arquivo e ilustrativas estão marcadas como tal.",
     "Each story shows the status of the information (confirmed fact, statement, proposal, forecast or announcement), the date and the sources consulted. We look for confirmation from two independent sources; when there is only one, this is flagged. All texts are original summaries. Images carry their author and licence; archive and illustrative images are labelled as such. This English edition is an AI translation of the Portuguese original, checked against it; most sources are in Portuguese or English."),
    ("Edição de domingo: seleção editorial das notícias mais importantes e com mais cobertura e seguimento ao longo da semana, atualizadas com o que mudou desde então. Não usamos dados de comentários nem de audiências. Cada notícia indica o estado da informação, a data e as fontes consultadas; procuramos confirmação em duas fontes independentes e assinalamos quando só há uma. Os textos são sínteses originais.",
     "Sunday edition: an editorial selection of the week's most important stories with the most coverage and follow-up, updated with what has changed since. We do not use comment or audience data. Each story shows the status of the information, the date and the sources consulted; we look for confirmation from two independent sources and flag when there is only one. All texts are original summaries. This English edition is an AI translation of the Portuguese original."),
    ("Feito com inteligência artificial (Claude), a partir de regras editoriais definidas e supervisionadas pela autora. Pode conter erros: confirma sempre nas fontes indicadas em cada notícia.",
     "Made with artificial intelligence (Claude), following editorial rules set and supervised by the author. It may contain errors: always check the sources listed under each story."),
    ("Projeto pessoal, sem publicidade e sem fins comerciais. Os erros detetados são corrigidos e registados na ", "A personal project, with no advertising and no commercial purpose. Errors are corrected and logged in the "),
    (">lista de correções<", ">list of corrections<"),
    ("<strong>Sobre este jornal:</strong>", "<strong>About this newspaper:</strong>"),
    ("Edição publicada em ", "Issue published at "),
    ("Ver todas as edições", "See all issues (in Portuguese)"),
    (">Correções</a>", ">Corrections</a>"),
    # topo
    ("Portugal · Leitura independente", "Portugal · Independent reading"),
    ("Edição de domingo", "Sunday edition"),
    ("Edição n.º ", "Issue no. "),
    ("A semana em perspetiva", "The week in perspective"),
    (" notícias e 4 artigos culturais · Agenda Porto · ", " stories and 4 culture pieces · Porto events · "),
    # resumo
    ("<h2>A semana em 2 minutos</h2>", "<h2>The week in 2 minutes</h2>"),
    ("<h2>A semana que vem</h2>", "<h2>The week ahead</h2>"),
    ("<h2>Em 2 minutos</h2>", "<h2>In 2 minutes</h2>"),
    ("<h2>O que acompanhar</h2>", "<h2>What to watch</h2>"),
    ('aria-label="Resumo do dia"', 'aria-label="Today in brief"'),
    ('aria-label="Resumo da semana"', 'aria-label="The week in brief"'),
    ('aria-label="Ler a notícia">Ler →', 'aria-label="Read the story">Read →'),
    ('">Ler →</a>', '">Read →</a>'),
    # secções
    ("<h2>Tecnologia, IA e Cibersegurança</h2>", "<h2>Technology, AI and Cybersecurity</h2>"),
    ("<h2>Mundo</h2>", "<h2>World</h2>"),
    ("<h2>Espaço</h2>", "<h2>Space</h2>"),
    ("<h2>Cultura, Cinema e Arte</h2>", "<h2>Culture, Film and Art</h2>"),
    ("<h2>Agenda do Porto</h2>", "<h2>What's on in Porto</h2>"),
    ("<h2>Jogos</h2>", "<h2>Games</h2>"),
    ("<h2>Passatempo</h2>", "<h2>Quiz</h2>"),
    ("<h2>As notícias da semana</h2>", "<h2>The stories of the week</h2>"),
    ("<h2>Destaques culturais da semana</h2>", "<h2>This week in Culture</h2>"),
    ("<h2>As edições da semana</h2>", "<h2>This week's issues</h2>"),
    ("<h2>Correções e atualizações</h2>", "<h2>Corrections and updates</h2>"),
    ("Ver todas as correções", "See all corrections"),
    ("Ver na edição de ", "See the issue of "),
    ("08 notícias · 3 cibersegurança · 3 IA · 2 tecnologia", "08 stories · 3 cybersecurity · 3 AI · 2 technology"),
    ("04 artigos · cinema · artista · curiosidade · cultura em movimento", "04 articles · film · artist · did you know · culture on the move"),
    ("a manchete desta secção está no topo", "this section's lead story is at the top"),
    ('aria-label="Manchete"', 'aria-label="Lead story"'),
    ('aria-label="A notícia da semana"', 'aria-label="Story of the week"'),
    ('aria-label="Secções"', 'aria-label="Sections"'),
    ("O que mudou desde então:", "What has changed since:"),
    ('<p class="original">Na edição de ', '<p class="original">In the issue of '),
    ("Sem registos nesta semana.", "Nothing this week."),
    ("<h3>Conhece o artista</h3>", "<h3>Meet the artist</h3>"),
    ("<h3>Sabias que…?</h3>", "<h3>Did you know…?</h3>"),
    ("<h3>Cultura em movimento</h3>", "<h3>Culture on the move</h3>"),
    ("<h3>Cinema</h3>", "<h3>Film</h3>"),
    # notícias
    ('<span class="abrir">Continuar a ler</span><span class="fechar">Mostrar menos</span>', '<span class="abrir">Continue reading</span><span class="fechar">Show less</span>'),
    ("<summary>Fontes e verificação · 2 fontes independentes</summary>", "<summary>Sources and verification · 2 independent sources</summary>"),
    ("<summary>Fontes e verificação · fonte única</summary>", "<summary>Sources and verification · single source</summary>"),
    ("<summary>Fontes</summary>", "<summary>Sources</summary>"),
    ('<p class="fontes">Fontes: ', '<p class="fontes">Sources: '),
    ('<span class="verif">Confirmado por duas fontes independentes', '<span class="verif">Confirmed by two independent sources'),
    ('<span class="verif">Fonte única', '<span class="verif">Single source'),
    ("<strong>Correção:</strong>", "<strong>Correction:</strong>"),
    # imagens
    ("Fotografia do acontecimento", "Photo of the event"), ("Imagem de arquivo", "Archive image"), ("Imagem ilustrativa", "Illustrative image"),
    ("Imagem oficial / de imprensa", "Official / press image"), ("Reprodução da obra", "Reproduction of the work"), ("Imagem promocional", "Promotional image"),
    ("Ilustração do jornal (imagem original indisponível)", "Newspaper illustration (original image unavailable)"),
    ("Ilustração gráfica de O Dia em Perspetiva, de uso livre.", "Graphic illustration by O Dia em Perspetiva, free to use."),
    ("Imagem: Wikimedia Commons · ", "Image: Wikimedia Commons · "), (">ver autoria e licença</a>", ">see author and licence</a>"),
    ("Autoria: ", "Author: "), (" · Licença: ", " · Licence: "), ("Licença: ", "Licence: "), ('rel="noopener">origem</a>', 'rel="noopener">source</a>'),
    # agenda
    ("hoje e os próximos 3 dias no menu", "today and the next 3 days in the menu"),
    ('aria-label="Dias da agenda"', 'aria-label="Event days"'),
    (">Programação oficial<", ">Official programme<"),
    ("Hoje · ", "Today · "),
    ("Horários, preços e lotação podem mudar. Confirma sempre na programação oficial antes de sair.", "Times, prices and availability may change. Always check the official listing before you go."),
    # jogos
    ("desafios novos em cada edição", "new challenges in every issue"),
    (">Recomeçar<", ">Restart<"), (">Mostrar solução<", ">Show solution<"), ("<span>Tempo</span>", "<span>Time</span>"),
    ("Melhor neste dispositivo", "Best on this device"), ('<p class="placar">Pontos ', '<p class="placar">Points '),
    ("Minas por marcar ", "Mines left "),
    ('aria-label="Setas"', 'aria-label="Arrows"'), ('aria-label="Para cima"', 'aria-label="Up"'), ('aria-label="Para a esquerda"', 'aria-label="Left"'),
    ('aria-label="Para baixo"', 'aria-label="Down"'), ('aria-label="Para a direita"', 'aria-label="Right"'), ('aria-label="Apagar"', 'aria-label="Delete"'),
    ("✏️ Rascunho: desligado", "✏️ Notes: off"), (">Modo: pintar ■<", ">Mode: fill ■<"), (">Modo: abrir<", ">Mode: open<"),
    (">Jogar<", ">Play<"), (">Saltar<", ">Jump<"), (">Ver imagem<", ">See image<"),
    ('aria-label="Grelha de Sudoku"', 'aria-label="Sudoku grid"'), ('aria-label="Grelha do caça-palavras"', 'aria-label="Word search grid"'),
    ('aria-label="Tabuleiro do 2048"', 'aria-label="2048 board"'), ('aria-label="Grelha do nonograma"', 'aria-label="Nonogram grid"'),
    ('aria-label="Campo minado"', 'aria-label="Minesweeper"'), ('aria-label="Jogo da cobra"', 'aria-label="Snake"'),
    ('aria-label="Corrida do dinossauro"', 'aria-label="Dinosaur run"'), ('alt="Imagem original do puzzle"', 'alt="Original puzzle image"'),
    ("<h3>Sudoku</h3>", "<h3>Sudoku</h3>"), ("<h3>Caça-palavras</h3>", "<h3>Word search</h3>"), ("<h3>Jogo das diferenças</h3>", "<h3>Spot the difference</h3>"),
    ("<h3>Nonograma</h3>", "<h3>Nonogram</h3>"), ("<h3>Campo minado</h3>", "<h3>Minesweeper</h3>"), ("<h3>Jogo da cobra</h3>", "<h3>Snake</h3>"),
    ("<h3>Corrida do dinossauro</h3>", "<h3>Dinosaur run</h3>"), ("<h3>Puzzle</h3>", "<h3>Jigsaw puzzle</h3>"), ("<h3>Quiz da semana</h3>", "<h3>Quiz of the week</h3>"),
    ("Preenche a grelha para que cada linha, coluna e quadrado de 3×3 tenha os números de 1 a 9. Toca numa casa vazia e escolhe o número. Liga o <strong>rascunho</strong> para anotar várias hipóteses pequenas numa casa antes de decidir (no computador: tecla N, ou Shift + número). Dificuldade: média, com solução única e sem precisar de tentativa-erro.",
     "Fill the grid so that every row, column and 3×3 box contains the numbers 1 to 9. Tap an empty cell and choose a number. Turn on <strong>notes</strong> to pencil in several candidates before deciding (on a computer: N key, or Shift + number). Difficulty: medium, with a unique solution and no trial and error needed."),
    ("Encontra as 15 palavras escondidas na horizontal, vertical ou diagonal, em qualquer sentido. Arrasta da primeira à última letra, ou toca na primeira e depois na última. Tema: ",
     "Find the 15 hidden words (in Portuguese, from today's Portuguese issue) horizontally, vertically or diagonally, in any direction. Drag from the first to the last letter, or tap the first and then the last. Theme: "),
    ("Desliza o dedo (ou usa as setas do teclado depois de tocares no tabuleiro) para mover todas as peças. Duas peças iguais que se tocam juntam-se numa só. Chega à peça 2048.",
     "Swipe (or use the arrow keys after tapping the board) to move all the tiles. Two equal tiles that touch merge into one. Reach the 2048 tile."),
    ("As duas imagens têm 7 diferenças. Toca onde as vires, em qualquer uma das imagens.", "The two images have 7 differences. Tap them in either image."),
    ("Os números dizem quantas casas seguidas estão pintadas em cada linha e coluna, por ordem, com pelo menos uma casa vazia entre blocos. Pinta as casas certas e descobre a figura. Solução única, só com lógica.",
     "The numbers tell you how many consecutive cells are filled in each row and column, in order, with at least one empty cell between blocks. Fill the right cells and reveal the picture. Unique solution, logic only."),
    ("Abre todas as casas sem minas. Cada número diz quantas minas há nas 8 casas à volta. Marca as minas com bandeira: toque longo, botão direito do rato ou o modo bandeira.",
     "Open every cell without a mine. Each number tells you how many mines are in the 8 surrounding cells. Flag mines with a long press, right-click or flag mode."),
    ("Guia a cobra até à comida. Cada ponto faz a cobra crescer e andar mais depressa. Não batas nas paredes nem na tua própria cauda.",
     "Steer the snake to the food. Each point makes it longer and faster. Don't hit the walls or your own tail."),
    ("Inspirado no jogo de quando ficamos sem internet: o nosso dinossauro de pescoço comprido corre sozinho e tens de o fazer saltar por cima dos obstáculos. Cada vez mais depressa.",
     "Inspired by the game you get when the internet goes down: our long-necked dinosaur runs on its own and you make it jump over the obstacles. Faster and faster."),
    ("A imagem da manchete foi cortada em 16 peças e baralhada. Toca em duas peças para as trocar até a imagem ficar completa. As peças no sítio certo ficam marcadas.",
     "The lead story's image has been cut into 16 pieces and shuffled. Tap two pieces to swap them until the picture is complete. Pieces in the right place are marked."),
    ("Quanto te lembras das notícias desta semana? Escolhe uma resposta em cada pergunta; a explicação e a ligação para a notícia aparecem logo a seguir.",
     "How much do you remember of this week's news? Pick an answer for each question; the explanation and a link to the story appear straight after."),
    ("Ilustração (imagem original indisponível)", "Illustration (original image unavailable)"),
    ('aria-label="Voltar ao topo"', 'aria-label="Back to top"'),
]

# Textos de jogos.js e do JavaScript da página (trocados com as aspas, para não tocar no código)
JS = [
    ("Modo claro", "Light mode"), ("Modo escuro", "Dark mode"),
    ("Ilustração (imagem original indisponível)", "Illustration (original image unavailable)"),
    (" Ler a notícia →", " Read the story →"), (" diferenças em ", " differences in "), (" diferenças", " differences"),
    (" encontradas. Recomeça para tentar de novo.", " found. Restart to try again."), (" minas à volta", " mines around"),
    (" palavras encontradas.", " words found."), (" perguntas sobre as notícias da semana.", " questions about this week's news."),
    (" peças no sítio.", " pieces in place."), (" pontos · toca para recomeçar", " points · tap to restart"),
    (" pontos! Podes continuar a jogar.", " points! You can keep playing."),
    (" pontos. Toca ou carrega em espaço para tentar de novo.", " points. Tap or press space to try again."),
    (" sem erros", " with no mistakes"), (" toque errado", " wrong tap"), (" toques errados", " wrong taps"), (" trocas e ", " swaps and "),
    (", no sítio certo", ", in the right place"), (". Parabéns!", ". Well done!"), (". Recomeça para tentar de novo.", ". Restart to try again."),
    (" resposta.", " answer."), (" respostas.", " answers."), (" certa", " correct"), (" certas", " correct"), (" em ", " out of "),
    (" de ", " of "), (" troca", " swap"), (" trocas", " swaps"), (" aos ", " at "), (". Fizeste ", ". You scored "),
    ("Acertaste ", "You got "), ("Bateste ", "You hit "), ("Boa semana de leitura!", "Have a good week of reading!"),
    ("Boom! Pisaste uma mina aos ", "Boom! You stepped on a mine at "), ("Campo limpo em ", "Field cleared in "), ("Certo! ", "Correct! "),
    ("Chegaste a 2048 com ", "You reached 2048 with "),
    ("Come os pontos sem bater nas paredes nem na cauda. A comida aparece nos mesmos sítios para todos hoje.", "Eat the dots without hitting the walls or your tail. The food appears in the same places for everyone today."),
    ("Concluído em ", "Completed in "), ("Continuar", "Continue"), ("Em pausa. Toca para continuar.", "Paused. Tap to continue."),
    ("Encontraste as ", "You found all "), ("Esconder imagem", "Hide image"), ("Fim de jogo · ", "Game over · "), ("Fim · ", "Game over · "),
    ("Há edições da semana à tua espera no arquivo.", "This week's issues are waiting for you in the archive."),
    ("Imagem com diferenças", "Image with differences"), ("Imagem completa em ", "Picture completed in "), ("Imagem original", "Original image"),
    ("Imagem revelada em ", "Picture revealed in "), ("Jogar de novo", "Play again"), ("Jogar", "Play"), ("Pausa", "Pause"),
    ("Junta peças iguais para chegar a 2048. O tabuleiro de partida é o mesmo para todos os leitores hoje.", "Merge equal tiles to reach 2048. The starting board is the same for every reader today."),
    ("Leitura em dia!", "All caught up!"), ("Linha ", "Row "), (", coluna ", ", column "), (", rascunho ", ", notes "), (", vazia", ", empty"),
    (", mina", ", mine"), (", bandeira", ", flag"), (", fechada", ", closed"),
    ("Modo: abrir", "Mode: open"), ("Modo: bandeira ⚑", "Mode: flag ⚑"), ("Modo: marcar ✕", "Mode: mark ✕"), ("Modo: pintar ■", "Mode: fill ■"),
    ("Não. ", "No. "), ("O primeiro toque nunca é mina. Bandeira: toque longo, botão direito ou o modo bandeira.", "The first tap is never a mine. Flag: long press, right-click or flag mode."),
    ("O tempo começa na primeira seleção.", "The clock starts at your first selection."),
    ("O tempo começa no primeiro número que colocares. Usa o rascunho para anotar hipóteses.", "The clock starts with the first number you place. Use notes to pencil in candidates."),
    ("Peça ", "Piece "), ("Pinta as casas seguindo os números. Usa ✕ para marcar casas vazias. Podes arrastar.", "Fill cells following the numbers. Use ✕ to mark empty cells. You can drag."),
    ("Salta os catos e as pedras. Os obstáculos aparecem pela mesma ordem para todos hoje.", "Jump over the cacti and rocks. Obstacles come in the same order for everyone today."),
    ("Sem jogadas possíveis. Fizeste ", "No moves left. You scored "), ("Setas, teclas WASD, deslizar no ecrã ou os botões.", "Arrows, WASD keys, swipe or the buttons."),
    ("Solução revelada", "Solution revealed"), ("Solução revelada. Recomeça para tentar de novo.", "Solution revealed. Restart to try again."),
    ("Solução revelada: ", "Solution revealed: "), ("Toca em duas peças para as trocar. A imagem é a da manchete de hoje.", "Tap two pieces to swap them. The picture is from today's lead story."),
    ("Toca em «Jogar» ou numa seta", "Tap «Play» or an arrow"),
    ("Toca nas diferenças em qualquer uma das imagens. O tempo começa no primeiro toque.", "Tap the differences in either image. The clock starts with your first tap."),
    ("Toca no ecrã ou carrega em espaço para começar", "Tap the screen or press space to start"),
    ("Toca no ecrã, no botão «Saltar» ou carrega em espaço.", "Tap the screen, the «Jump» button or press space."),
    ("Todas encontradas em ", "All found in "), ("Tropeçaste! Fizeste ", "You tripped! You scored "), ("Ver imagem", "See image"),
    ("na parede", "the wall"), ("na própria cauda", "your own tail"), ("✏️ Rascunho: ", "✏️ Notes: "), ("ligado", "on"), ("desligado", "off"),
]


def _js(txt):
    for pt, en in sorted(JS, key=lambda x: -len(x[0])):
        for q in ("'", '"'):
            txt = txt.replace(q + pt + q, q + en.replace(q, "\\" + q) + q)
    return txt


def _html(txt):
    for pt, en in NAV + sorted(HTML, key=lambda x: -len(x[0])):
        txt = txt.replace(pt, en)
    # etiquetas das notícias e da cultura: «01 / Cibersegurança 1/3», «Manchete · Mundo»
    def tag(m):
        t = m.group(2)
        for pt, en in sorted(SECCOES_EN.items(), key=lambda x: -len(x[0])):
            t = t.replace(pt, en)
        return m.group(1) + t + m.group(3)
    txt = re.sub(r'(<span class="tag">)(.*?)(</span>)', tag, txt)
    txt = re.sub(r"(\d\d) notícias</p>|(\d\d) notícias ·", lambda m: (m.group(1) or m.group(2)) + (" stories</p>" if m.group(1) else " stories ·"), txt)
    txt = re.sub(r"cerca de (\d+) min de leitura", r"about \1 min read", txt)
    txt = re.sub(r"(\d\d/\d\d/\d{4}) a (\d\d/\d\d/\d{4})", r"\1 to \2", txt)
    # edição de domingo
    txt = re.sub(r" · resumo de (.+?) a (.+?) · (\d+) notícias da semana · Agenda Porto · Quiz",
                 r" · a look back from \1 to \2 · \3 stories of the week · Porto events · Quiz", txt)
    txt = re.sub(r"notícias · as mais importantes e as que mais deram que falar, de (.+?) a (.+?) · ",
                 r"stories · the most important and most followed, from \1 to \2 · ", txt)
    txt = re.sub(r"o que passou pela Cultura de (.+?) a (.+?) · toca para ler",
                 r"what appeared in Culture from \1 to \2 (in Portuguese) · tap to read", txt)
    txt = re.sub(r"(\d+) edições · cada uma com notícias, cultura, agenda e jogos",
                 r"\1 issues (in Portuguese) · each with news, culture, events and games", txt)
    txt = txt.replace(" · A semana · ", " · The week · ")
    return txt


def traduzir(pagina, data, url_site):
    """Traduz os textos fixos e acerta os caminhos para a subpasta en/."""
    partes = re.split(r"(<style>.*?</style>|<script[^>]*>.*?</script>)", pagina, flags=re.S)
    out = []
    for p in partes:
        if p.startswith("<style>") or p.startswith('<script type="application/json"'):
            out.append(p)
        elif p.startswith("<script"):
            out.append(_js(p))
        else:
            out.append(_html(p))
    pagina = "".join(out)
    pagina = pagina.replace('<html lang="pt-PT">', '<html lang="en-GB">').replace('content="pt_PT"', 'content="en_GB"')
    pagina = pagina.replace('href="../', 'href="../../').replace('src="assets/', 'src="../assets/').replace('data-reserva="assets/', 'data-reserva="../assets/')
    pagina = pagina.replace(f'content="{url_site}{data}/"', f'content="{url_site}{data}/en/"')
    pagina = pagina.replace(f'<a href="{url_site}{data}/">{url_site}{data}/</a>', f'<a href="{url_site}{data}/en/">{url_site}{data}/en/</a>')
    return pagina
