(function(){
"use strict";
const J = JSON.parse(document.getElementById('dados-jogos').textContent);
const $ = id => document.getElementById(id);
const ler = k => { try { return localStorage.getItem(k) } catch (e) { return null } };
const guardar = (k, v) => { try { localStorage.setItem(k, v) } catch (e) {} };
const cor = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || '#111';
function aleatorio(seed){ let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296 } }
function msg(el, txt, cls){ if (!el) return; el.textContent = txt; el.className = 'estado-jogo' + (cls ? ' ' + cls : '') }

function Cronometro(el){
  let inicio=0, acumulado=0, id=null;
  const fmt=ms=>{const s=Math.floor(ms/1000);return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')};
  const desenhar=()=>{if(el)el.textContent=fmt(acumulado+(inicio?Date.now()-inicio:0))};
  return {
    get ativo(){return !!inicio},
    get usado(){return !!inicio||acumulado>0},
    iniciar(){if(inicio)return;inicio=Date.now();if(el)el.classList.remove('parado','concluido');id=setInterval(desenhar,250);desenhar()},
    parar(classe){if(inicio){acumulado+=Date.now()-inicio;inicio=0}clearInterval(id);id=null;desenhar();if(el)el.classList.add(classe||'parado')},
    reiniciar(){inicio=0;acumulado=0;clearInterval(id);id=null;if(el)el.className='crono parado';desenhar()},
    texto(){return el?el.textContent:''}
  };
}
// gestos de deslizar (2048 e cobra)
function deslizar(el, cb){
  let x0=null,y0=null;
  el.addEventListener('pointerdown',e=>{x0=e.clientX;y0=e.clientY});
  el.addEventListener('pointerup',e=>{if(x0===null)return;const dx=e.clientX-x0,dy=e.clientY-y0;x0=null;
    if(Math.max(Math.abs(dx),Math.abs(dy))<24)return;
    cb(Math.abs(dx)>Math.abs(dy)?(dx>0?'dir':'esq'):(dy>0?'baixo':'cima'))});
  el.addEventListener('pointercancel',()=>{x0=null});
}
const SETAS={ArrowLeft:'esq',ArrowRight:'dir',ArrowUp:'cima',ArrowDown:'baixo',a:'esq',d:'dir',w:'cima',s:'baixo'};

/* ---------------- Sudoku (com rascunho) ---------------- */
if(J.sudoku&&$('sudoku'))(function(){
  const S=J.sudoku, grelha=$('sudoku'), estado=$('sudoku-estado'), bR=$('sudoku-rascunho');
  const cr=Cronometro($('sudoku-crono'));
  const PEERS=[];for(let i=0;i<81;i++){const r=Math.floor(i/9),c=i%9,p=[];for(let k=0;k<81;k++){if(k===i)continue;const r2=Math.floor(k/9),c2=k%9;
    if(r2===r||c2===c||(Math.floor(r2/3)===Math.floor(r/3)&&Math.floor(c2/3)===Math.floor(c/3)))p.push(k)}PEERS.push(p)}
  let tab, notas, sel=-1, revelado=false, terminado=false, rasc=false;
  const celulas=[];
  for(let i=0;i<81;i++){
    const b=document.createElement('button');b.type='button';
    const r=Math.floor(i/9),c=i%9;
    if(c%3===2&&c<8)b.classList.add('c3'); if(r%3===2&&r<8)b.classList.add('l3');
    b.addEventListener('click',()=>{sel=i;desenhar()});
    grelha.appendChild(b);celulas.push(b);
  }
  const conflito=i=>{const v=tab[i];return !!v&&PEERS[i].some(k=>tab[k]===v)};
  function desenhar(){
    const vs=sel>=0?tab[sel]:0;
    celulas.forEach((b,i)=>{
      const v=tab[i];
      if(v)b.textContent=v;
      else if(notas[i].size){b.innerHTML='<span class="notas">'+[1,2,3,4,5,6,7,8,9].map(n=>'<i>'+(notas[i].has(n)?n:'')+'</i>').join('')+'</span>'}
      else b.textContent='';
      b.classList.toggle('fixo',S.puzzle[i]!==0);
      b.classList.toggle('sel',i===sel);
      b.classList.toggle('mesma',!!vs&&v===vs&&i!==sel);
      b.classList.toggle('erro',S.puzzle[i]===0&&conflito(i));
      b.classList.toggle('revel',revelado&&S.puzzle[i]===0);
      b.setAttribute('aria-label','Linha '+(Math.floor(i/9)+1)+', coluna '+(i%9+1)+(v?', '+v:(notas[i].size?', rascunho '+[...notas[i]].sort().join(' '):', vazia')));
    });
  }
  function modo(v){rasc=v;bR.setAttribute('aria-pressed',rasc);bR.classList.toggle('ativo',rasc);
    bR.textContent='✏️ Rascunho: '+(rasc?'ligado':'desligado');grelha.classList.toggle('modo-rascunho',rasc)}
  function jogar(v,nota){
    if(sel<0||terminado||S.puzzle[sel]!==0)return;
    if((rasc||nota)&&v){if(tab[sel])return;if(!cr.usado)cr.iniciar();
      notas[sel].has(v)?notas[sel].delete(v):notas[sel].add(v);desenhar();return}
    if(!v){if(tab[sel])tab[sel]=0;else notas[sel].clear();desenhar();return}
    if(tab[sel]===v)return;
    if(!cr.usado)cr.iniciar();
    tab[sel]=v;notas[sel].clear();PEERS[sel].forEach(k=>notas[k].delete(v));desenhar();
    if(tab.every((x,i)=>x===S.solucao[i])){terminado=true;cr.parar('concluido');msg(estado,'Concluído em '+cr.texto()+'. Parabéns!','ganho')}
  }
  function reiniciar(){tab=S.puzzle.slice();notas=Array.from({length:81},()=>new Set());sel=-1;revelado=false;terminado=false;cr.reiniciar();
    msg(estado,'O tempo começa no primeiro número que colocares. Usa o rascunho para anotar hipóteses.');desenhar()}
  document.querySelectorAll('#sudoku-teclado button[data-v]').forEach(b=>b.addEventListener('click',()=>jogar(+b.dataset.v)));
  bR.addEventListener('click',()=>modo(!rasc));
  $('sudoku-recomecar').addEventListener('click',reiniciar);
  $('sudoku-solucao').addEventListener('click',()=>{
    if(terminado&&!revelado)return;tab=S.solucao.slice();revelado=true;terminado=true;cr.parar('parado');
    msg(estado,'Solução revelada'+(cr.usado?' aos '+cr.texto():'')+'. Recomeça para tentar de novo.','revelado');desenhar()});
  grelha.addEventListener('keydown',e=>{
    const d=e.code&&e.code.startsWith('Digit')?+e.code.slice(5):(e.key>='1'&&e.key<='9'?+e.key:NaN);
    if(d>=1&&d<=9){jogar(d,e.shiftKey);e.preventDefault()}
    else if(e.key==='Backspace'||e.key==='Delete'||e.key==='0'){jogar(0);e.preventDefault()}
    else if(e.key==='n'||e.key==='r'){modo(!rasc);e.preventDefault()}
    else{const m={ArrowUp:-9,ArrowDown:9,ArrowLeft:-1,ArrowRight:1}[e.key];if(m!==undefined&&sel>=0){const n=sel+m;if(n>=0&&n<81){sel=n;desenhar();celulas[n].focus()}e.preventDefault()}}
  });
  modo(false);reiniciar();
})();

/* ---------------- 2048 ---------------- */
if(J['2048']&&$('g2048'))(function(){
  const el=$('g2048'), estado=$('g2048-estado'), pts=$('g2048-pontos'), mel=$('g2048-melhor');
  const cel=[];for(let i=0;i<16;i++){const d=document.createElement('div');el.appendChild(d);cel.push(d)}
  let R,b,score,acabou,ganhou,continuar;
  const melhor=()=>+(ler('jornal-2048-melhor')||0);
  function novo(){const v=[];b.forEach((x,i)=>{if(!x)v.push(i)});if(!v.length)return;b[v[Math.floor(R()*v.length)]]=R()<0.9?2:4}
  function desenhar(){
    cel.forEach((d,i)=>{const v=b[i];d.textContent=v||'';d.dataset.v=v||'';
      if(v){const k=Math.log2(v),l=Math.max(30,90-k*5.5);d.style.background='hsl('+(40-k*3)+' '+(35+k*4)+'% '+l+'%)';d.style.color=l<62?'#fff':'#222';d.style.fontSize=v>=1024?'1.15rem':v>=128?'1.4rem':''}
      else{d.style.background='';d.style.color='';d.style.fontSize=''}});
    pts.textContent=score;mel.textContent=Math.max(melhor(),score);
  }
  function linhas(dir){const L=[];for(let k=0;k<4;k++){const l=[];for(let j=0;j<4;j++){
    l.push(dir==='esq'?k*4+j:dir==='dir'?k*4+3-j:dir==='cima'?j*4+k:(3-j)*4+k)}L.push(l)}return L}
  function podeMover(){if(b.includes(0))return true;for(let i=0;i<16;i++){if(i%4<3&&b[i]===b[i+1])return true;if(i<12&&b[i]===b[i+4])return true}return false}
  function mover(dir){
    if(acabou||(ganhou&&!continuar))return;
    let mexeu=false;
    linhas(dir).forEach(l=>{const vals=l.map(i=>b[i]).filter(x=>x),out=[];
      for(let k=0;k<vals.length;k++){if(vals[k]===vals[k+1]){out.push(vals[k]*2);score+=vals[k]*2;k++}else out.push(vals[k])}
      while(out.length<4)out.push(0);
      l.forEach((i,k)=>{if(b[i]!==out[k])mexeu=true;b[i]=out[k]})});
    if(!mexeu)return;
    novo();if(score>melhor())guardar('jornal-2048-melhor',score);desenhar();
    if(!ganhou&&b.includes(2048)){ganhou=true;msg(estado,'Chegaste a 2048 com '+score+' pontos! Podes continuar a jogar.','ganho');continuar=true}
    else if(!podeMover()){acabou=true;msg(estado,'Sem jogadas possíveis. Fizeste '+score+' pontos.','revelado')}
  }
  function reiniciar(){R=aleatorio(J['2048'].semente);b=Array(16).fill(0);score=0;acabou=false;ganhou=false;continuar=false;novo();novo();desenhar();
    msg(estado,'Junta peças iguais para chegar a 2048. O tabuleiro de partida é o mesmo para todos os leitores hoje.')}
  el.addEventListener('keydown',e=>{const d=SETAS[e.key];if(d){mover(d);e.preventDefault()}});
  deslizar(el,mover);
  document.querySelectorAll('#g2048-setas button').forEach(x=>x.addEventListener('click',()=>mover(x.dataset.d)));
  $('g2048-recomecar').addEventListener('click',reiniciar);
  reiniciar();
})();

/* ---------------- Jogo das diferenças ---------------- */
if(J.diferencas&&$('dif-a'))(function(){
  const D=J.diferencas, A=$('dif-a'), B=$('dif-b'), estado=$('dif-estado'), cr=Cronometro($('dif-crono'));
  const NS='http://www.w3.org/2000/svg';
  function desenhar(alvo,prims){
    const s=document.createElementNS(NS,'svg');s.setAttribute('viewBox','0 0 '+D.largura+' '+D.altura);s.setAttribute('role','img');
    prims.forEach(p=>{let e;
      if(p.t==='rect'){e=document.createElementNS(NS,'rect');e.setAttribute('x',p.x);e.setAttribute('y',p.y);e.setAttribute('width',p.w);e.setAttribute('height',p.h)}
      else if(p.t==='circ'){e=document.createElementNS(NS,'circle');e.setAttribute('cx',p.x);e.setAttribute('cy',p.y);e.setAttribute('r',p.r)}
      else{e=document.createElementNS(NS,'polygon');e.setAttribute('points',p.pts.map(q=>q.join(',')).join(' '))}
      e.setAttribute('fill',p.f);s.appendChild(e)});
    const g=document.createElementNS(NS,'g');g.setAttribute('class','marcas');s.appendChild(g);
    alvo.innerHTML='';alvo.appendChild(s);return g;
  }
  const gA=desenhar(A,D.a), gB=desenhar(B,D.b);
  A.querySelector('svg').setAttribute('aria-label','Imagem original');B.querySelector('svg').setAttribute('aria-label','Imagem com diferenças');
  let achadas,erros,fim;
  function marca(g,x,y,r,cls){const c=document.createElementNS(NS,'circle');c.setAttribute('cx',x);c.setAttribute('cy',y);c.setAttribute('r',r);c.setAttribute('class',cls);g.appendChild(c)}
  function falha(g,x,y){const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y+7);t.setAttribute('class','falha');t.setAttribute('text-anchor','middle');t.textContent='✕';g.appendChild(t);setTimeout(()=>t.remove(),700)}
  function atualizar(){msg(estado,achadas.size+' de '+D.alvos.length+' diferenças'+(erros?' · '+erros+(erros===1?' toque errado':' toques errados'):'')+'.')}
  function clique(e){
    if(fim)return;const s=e.currentTarget.querySelector('svg'),r=s.getBoundingClientRect();
    const x=(e.clientX-r.left)*D.largura/r.width,y=(e.clientY-r.top)*D.altura/r.height;
    if(!cr.usado)cr.iniciar();
    const k=D.alvos.findIndex(([ax,ay,ar],i)=>!achadas.has(i)&&(x-ax)**2+(y-ay)**2<=ar*ar);
    if(k<0){erros++;falha(gA,x,y);falha(gB,x,y);atualizar();return}
    achadas.add(k);const [ax,ay,ar]=D.alvos[k];marca(gA,ax,ay,ar,'achada');marca(gB,ax,ay,ar,'achada');atualizar();
    if(achadas.size===D.alvos.length){fim=true;cr.parar('concluido');msg(estado,'Encontraste as '+D.alvos.length+' diferenças em '+cr.texto()+(erros?' com '+erros+(erros===1?' toque errado':' toques errados'):' sem erros')+'. Parabéns!','ganho')}
  }
  A.addEventListener('click',clique);B.addEventListener('click',clique);
  function reiniciar(){achadas=new Set();erros=0;fim=false;gA.innerHTML='';gB.innerHTML='';cr.reiniciar();msg(estado,'Toca nas diferenças em qualquer uma das imagens. O tempo começa no primeiro toque.')}
  $('dif-recomecar').addEventListener('click',reiniciar);
  $('dif-solucao').addEventListener('click',()=>{if(fim&&achadas.size===D.alvos.length)return;fim=true;cr.parar('parado');
    D.alvos.forEach(([ax,ay,ar],i)=>{if(!achadas.has(i)){marca(gA,ax,ay,ar,'revel');marca(gB,ax,ay,ar,'revel')}});
    msg(estado,'Solução revelada: '+achadas.size+' de '+D.alvos.length+' encontradas. Recomeça para tentar de novo.','revelado')});
  reiniciar();
})();

/* ---------------- Nonograma ---------------- */
if(J.nonograma&&$('nono'))(function(){
  const N=J.nonograma,n=N.tamanho,el=$('nono'),estado=$('nono-estado'),bM=$('nono-modo'),cr=Cronometro($('nono-crono'));
  el.style.gridTemplateColumns='auto repeat('+n+',1fr)';
  const canto=document.createElement('div');canto.className='canto';el.appendChild(canto);
  const pc=N.colunas.map(c=>{const d=document.createElement('div');d.className='pista col';d.innerHTML=c.map(x=>'<span>'+x+'</span>').join('');el.appendChild(d);return d});
  const pl=[],cel=[];
  for(let r=0;r<n;r++){const d=document.createElement('div');d.className='pista lin';d.innerHTML=N.linhas[r].map(x=>'<span>'+x+'</span>').join('');el.appendChild(d);pl.push(d);
    for(let c=0;c<n;c++){const q=document.createElement('div');q.className='q';q.dataset.i=r*n+c;
      if(c%5===4&&c<n-1)q.classList.add('c5');if(r%5===4&&r<n-1)q.classList.add('l5');el.appendChild(q);cel.push(q)}}
  let st,fim,marcar=false,arrasto=null;
  const pistas=l=>{const o=[];let k=0;l.forEach(v=>{if(v===1)k++;else if(k){o.push(k);k=0}});if(k)o.push(k);return o.length?o:[0]};
  function desenhar(){
    cel.forEach((q,i)=>{q.classList.toggle('cheia',st[i]===1);q.classList.toggle('x',st[i]===2)});
    for(let r=0;r<n;r++)pl[r].classList.toggle('feita',pistas(st.slice(r*n,r*n+n)).join()===N.linhas[r].join());
    for(let c=0;c<n;c++){const col=[];for(let r=0;r<n;r++)col.push(st[r*n+c]);pc[c].classList.toggle('feita',pistas(col).join()===N.colunas[c].join())}
  }
  function verificar(){if(st.every((v,i)=>(v===1)===(N.solucao[i]==='1'))){fim=true;cr.parar('concluido');
    cel.forEach((q,i)=>{if(st[i]===2){st[i]=0}});desenhar();msg(estado,'Imagem revelada em '+cr.texto()+'. Parabéns!','ganho')}}
  function aplicar(i){if(st[i]===arrasto)return;st[i]=arrasto;desenhar()}
  el.addEventListener('pointerdown',e=>{if(fim)return;const q=e.target.closest('.q');if(!q)return;e.preventDefault();
    if(!cr.usado)cr.iniciar();const i=+q.dataset.i,alvo=marcar?2:1;arrasto=st[i]===alvo?0:alvo;aplicar(i)});
  el.addEventListener('pointermove',e=>{if(arrasto===null)return;const t=document.elementFromPoint(e.clientX,e.clientY);if(t&&t.classList.contains('q')&&el.contains(t))aplicar(+t.dataset.i)});
  const soltar=()=>{if(arrasto!==null){arrasto=null;verificar()}};
  el.addEventListener('pointerup',soltar);el.addEventListener('pointercancel',soltar);el.addEventListener('pointerleave',soltar);
  bM.addEventListener('click',()=>{marcar=!marcar;bM.setAttribute('aria-pressed',marcar);bM.classList.toggle('ativo',marcar);bM.textContent=marcar?'Modo: marcar ✕':'Modo: pintar ■'});
  function reiniciar(){st=Array(n*n).fill(0);fim=false;cr.reiniciar();desenhar();msg(estado,'Pinta as casas seguindo os números. Usa ✕ para marcar casas vazias. Podes arrastar.')}
  $('nono-recomecar').addEventListener('click',reiniciar);
  $('nono-solucao').addEventListener('click',()=>{fim=true;cr.parar('parado');st=N.solucao.split('').map(x=>x==='1'?1:0);desenhar();
    msg(estado,'Solução revelada. Recomeça para tentar de novo.','revelado')});
  reiniciar();
})();

/* ---------------- Campo minado ---------------- */
if(J.minas&&$('minas'))(function(){
  const M=J.minas,L=M.linhas,C=M.colunas,T=L*C,el=$('minas'),estado=$('minas-estado'),bB=$('minas-bandeira'),resta=$('minas-restam'),cr=Cronometro($('minas-crono'));
  el.style.gridTemplateColumns='repeat('+C+',1fr)';
  const cel=[];for(let i=0;i<T;i++){const b=document.createElement('button');b.type='button';b.dataset.i=i;el.appendChild(b);cel.push(b)}
  const viz=i=>{const r=Math.floor(i/C),c=i%C,o=[];for(let dr=-1;dr<=1;dr++)for(let dc=-1;dc<=1;dc++){if(!dr&&!dc)continue;const y=r+dr,x=c+dc;if(y>=0&&y<L&&x>=0&&x<C)o.push(y*C+x)}return o};
  let mina,aberta,band,num,gerado,fim,modoB=false,abertas;
  function gerar(p){const R=aleatorio(M.semente+p),proib=new Set([p,...viz(p)]),livres=[];for(let i=0;i<T;i++)if(!proib.has(i))livres.push(i);
    for(let i=livres.length-1;i>0;i--){const j=Math.floor(R()*(i+1));[livres[i],livres[j]]=[livres[j],livres[i]]}
    livres.slice(0,M.minas).forEach(i=>mina[i]=true);for(let i=0;i<T;i++)num[i]=viz(i).filter(k=>mina[k]).length;gerado=true}
  function desenhar(){cel.forEach((b,i)=>{b.className='';b.textContent='';
    if(aberta[i]){b.classList.add('aberta');if(mina[i]){b.textContent='✸';b.classList.add('mina')}else if(num[i]){b.textContent=num[i];b.classList.add('n'+num[i])}}
    else if(band[i]){b.textContent='⚑';b.classList.add('band')}
    b.setAttribute('aria-label','Linha '+(Math.floor(i/C)+1)+', coluna '+(i%C+1)+(aberta[i]?(mina[i]?', mina':', '+num[i]+' minas à volta'):band[i]?', bandeira':', fechada'))});
    resta.textContent=M.minas-band.filter(Boolean).length}
  function abrir(i){
    if(fim||aberta[i]||band[i])return;
    if(!gerado){gerar(i);cr.iniciar()}
    if(mina[i]){fim=true;cr.parar('parado');for(let k=0;k<T;k++)if(mina[k])aberta[k]=true;desenhar();cel[i].classList.add('explodiu');
      msg(estado,'Boom! Pisaste uma mina aos '+cr.texto()+'. Recomeça para tentar de novo.','revelado');return}
    const fila=[i];while(fila.length){const k=fila.pop();if(aberta[k]||band[k])continue;aberta[k]=true;abertas++;if(num[k]===0)viz(k).forEach(v=>{if(!aberta[v]&&!mina[v])fila.push(v)})}
    if(abertas===T-M.minas){fim=true;cr.parar('concluido');for(let k=0;k<T;k++)if(mina[k])band[k]=true;desenhar();msg(estado,'Campo limpo em '+cr.texto()+'. Parabéns!','ganho');return}
    desenhar()}
  function bandeira(i){if(fim||aberta[i])return;band[i]=!band[i];desenhar()}
  let toque=null,longo=false;
  el.addEventListener('pointerdown',e=>{const b=e.target.closest('button');if(!b)return;longo=false;clearTimeout(toque);toque=setTimeout(()=>{longo=true;bandeira(+b.dataset.i);if(navigator.vibrate)navigator.vibrate(20)},450)});
  ['pointerup','pointerleave','pointercancel'].forEach(t=>el.addEventListener(t,()=>clearTimeout(toque)));
  el.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(longo){longo=false;return}const i=+b.dataset.i;modoB?bandeira(i):abrir(i)});
  el.addEventListener('contextmenu',e=>{const b=e.target.closest('button');if(!b)return;e.preventDefault();if(!longo)bandeira(+b.dataset.i);longo=false});
  bB.addEventListener('click',()=>{modoB=!modoB;bB.setAttribute('aria-pressed',modoB);bB.classList.toggle('ativo',modoB);bB.textContent=modoB?'Modo: bandeira ⚑':'Modo: abrir'});
  function reiniciar(){mina=Array(T).fill(false);aberta=Array(T).fill(false);band=Array(T).fill(false);num=Array(T).fill(0);gerado=false;fim=false;abertas=0;cr.reiniciar();desenhar();
    msg(estado,'O primeiro toque nunca é mina. Bandeira: toque longo, botão direito ou o modo bandeira.')}
  $('minas-recomecar').addEventListener('click',reiniciar);
  reiniciar();
})();

/* ---------------- Cobra ---------------- */
if(J.cobra&&$('cobra'))(function(){
  const cv=$('cobra'),ctx=cv.getContext('2d'),N=17,estado=$('cobra-estado'),pts=$('cobra-pontos'),mel=$('cobra-melhor'),bJ=$('cobra-jogar');
  let R,cobra,dir,fila,comida,score,vel,acc,ult,ativo,fim,raf;
  const melhor=()=>+(ler('jornal-cobra-melhor')||0);
  function tamanho(){const w=cv.clientWidth||300,d=window.devicePixelRatio||1;cv.width=w*d;cv.height=w*d;ctx.setTransform(d,0,0,d,0,0)}
  function novaComida(){const livres=[];for(let i=0;i<N*N;i++){if(!cobra.some(p=>p.x+p.y*N===i))livres.push(i)}const k=livres[Math.floor(R()*livres.length)];comida={x:k%N,y:Math.floor(k/N)}}
  function desenhar(){const w=cv.clientWidth||300,c=w/N;ctx.fillStyle=cor('--cinza');ctx.fillRect(0,0,w,w);
    ctx.fillStyle=cor('--acento');ctx.beginPath();ctx.arc((comida.x+.5)*c,(comida.y+.5)*c,c*.38,0,7);ctx.fill();
    cobra.forEach((p,i)=>{ctx.fillStyle=i?cor('--ink'):cor('--agenda');ctx.fillRect(p.x*c+1,p.y*c+1,c-2,c-2)});
    if(!ativo){ctx.fillStyle=cor('--paper');ctx.globalAlpha=.85;ctx.fillRect(0,w/2-26,w,52);ctx.globalAlpha=1;ctx.fillStyle=cor('--ink');ctx.font='700 15px Arial';ctx.textAlign='center';
      ctx.fillText(fim?'Fim de jogo · '+score+' pontos':(score?'Pausa':'Toca em «Jogar» ou numa seta'),w/2,w/2+5)}
    pts.textContent=score;mel.textContent=Math.max(melhor(),score)}
  function passo(){if(fila.length){const d=fila.shift();if(d.x!==-dir.x||d.y!==-dir.y)dir=d}
    const h={x:cobra[0].x+dir.x,y:cobra[0].y+dir.y};
    if(h.x<0||h.y<0||h.x>=N||h.y>=N||cobra.some(p=>p.x===h.x&&p.y===h.y)){fim=true;ativo=false;bJ.textContent='Jogar de novo';
      if(score>melhor())guardar('jornal-cobra-melhor',score);msg(estado,'Bateste '+(h.x<0||h.y<0||h.x>=N||h.y>=N?'na parede':'na própria cauda')+'. Fizeste '+score+' pontos.','revelado');return}
    cobra.unshift(h);if(h.x===comida.x&&h.y===comida.y){score++;vel=Math.max(120,vel-3);novaComida()}else cobra.pop()}
  function ciclo(t){if(!ativo){desenhar();return}acc+=t-ult;ult=t;while(acc>=vel&&ativo){acc-=vel;passo()}desenhar();raf=requestAnimationFrame(ciclo)}
  function iniciar(){if(fim||!cobra)reiniciar(true);ativo=true;bJ.textContent='Pausa';ult=performance.now();acc=0;msg(estado,'Setas, teclas WASD, deslizar no ecrã ou os botões.');cancelAnimationFrame(raf);raf=requestAnimationFrame(ciclo)}
  function pausa(){ativo=false;bJ.textContent='Continuar';desenhar()}
  function virar(d){const m={esq:{x:-1,y:0},dir:{x:1,y:0},cima:{x:0,y:-1},baixo:{x:0,y:1}}[d];if(!m)return;if(!ativo)iniciar();fila.push(m);if(fila.length>3)fila.shift()}
  function reiniciar(semDesenho){R=aleatorio(J.cobra.semente);cobra=[{x:5,y:8},{x:4,y:8},{x:3,y:8}];dir={x:1,y:0};fila=[];score=0;vel=230;fim=false;ativo=false;novaComida();bJ.textContent='Jogar';
    if(!semDesenho){desenhar();msg(estado,'Come os pontos sem bater nas paredes nem na cauda. A comida aparece nos mesmos sítios para todos hoje.')}}
  bJ.addEventListener('click',()=>ativo?pausa():iniciar());
  $('cobra-recomecar').addEventListener('click',()=>{cancelAnimationFrame(raf);reiniciar()});
  document.querySelectorAll('#cobra-setas button').forEach(x=>x.addEventListener('click',()=>virar(x.dataset.d)));
  deslizar(cv,virar);
  addEventListener('keydown',e=>{if(!ativo&&document.activeElement!==cv)return;const d=SETAS[e.key];if(d){virar(d);e.preventDefault()}else if(e.key===' '&&ativo){pausa();e.preventDefault()}});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&ativo)pausa()});
  addEventListener('resize',()=>{tamanho();desenhar()});
  tamanho();reiniciar();
})();

/* ---------------- Dinossauro (corrida) ---------------- */
if(J.dino&&$('dino'))(function(){
  const cv=$('dino'),ctx=cv.getContext('2d'),W=600,H=170,CHAO=146,estado=$('dino-estado'),pts=$('dino-pontos'),mel=$('dino-melhor');
  let R,y,vy,obs,vel,dist,prox,ativo,fim,ult,raf,passoAnim;
  const melhor=()=>+(ler('jornal-dino-melhor')||0);
  function tamanho(){const w=cv.clientWidth||W,d=window.devicePixelRatio||1;cv.width=w*d;cv.height=w*H/W*d;ctx.setTransform(w/W*d,0,0,w/W*d,0,0)}
  // dinossauro de pescoço comprido (desenho próprio do jornal)
  function dino(x,yb,t){ctx.fillStyle=cor('--ink');
    ctx.beginPath();ctx.ellipse(x+20,yb-20,20,12,0,0,7);ctx.fill();               // corpo
    ctx.beginPath();ctx.moveTo(x+2,yb-24);ctx.quadraticCurveTo(x-14,yb-22,x-20,yb-12);ctx.lineTo(x-16,yb-11);ctx.quadraticCurveTo(x-6,yb-17,x+4,yb-14);ctx.fill(); // cauda
    ctx.beginPath();ctx.moveTo(x+32,yb-28);ctx.quadraticCurveTo(x+38,yb-44,x+40,yb-52);ctx.lineTo(x+47,yb-50);ctx.quadraticCurveTo(x+44,yb-38,x+38,yb-22);ctx.fill(); // pescoço
    ctx.beginPath();ctx.ellipse(x+46,yb-54,8,5,-.2,0,7);ctx.fill();                // cabeça
    ctx.fillStyle=cor('--paper');ctx.beginPath();ctx.arc(x+48,yb-56,1.6,0,7);ctx.fill();ctx.fillStyle=cor('--ink');
    const a=y<CHAO?0:Math.sin(t)*4;[[x+8,a],[x+14,-a],[x+28,-a],[x+34,a]].forEach(([lx,o])=>ctx.fillRect(lx,yb-12,5,12+(y<CHAO?-2:0)-Math.abs(o)/2))}
  function cato(o){ctx.fillStyle=cor('--agenda');
    if(o.tipo==='pedra'){ctx.beginPath();ctx.ellipse(o.x+o.w/2,CHAO-o.h/2,o.w/2,o.h/2,0,0,7);ctx.fill();return}
    ctx.fillRect(o.x+o.w/2-4,CHAO-o.h,8,o.h);ctx.fillRect(o.x,CHAO-o.h*.6,4,o.h*.35);ctx.fillRect(o.x,CHAO-o.h*.3,o.w/2,4);ctx.fillRect(o.x+o.w-4,CHAO-o.h*.75,4,o.h*.35);ctx.fillRect(o.x+o.w/2,CHAO-o.h*.45,o.w/2,4)}
  function desenhar(t){ctx.fillStyle=cor('--paper');ctx.fillRect(0,0,W,H);ctx.fillStyle=cor('--line');ctx.fillRect(0,CHAO,W,1.5);
    for(let k=0;k<12;k++){const gx=((k*61-dist*1.0)%W+W)%W;ctx.fillRect(gx,CHAO+7+(k%3)*4,8,1.2)}
    obs.forEach(cato);dino(46,y,t||0);
    ctx.fillStyle=cor('--muted');ctx.font='700 13px Arial';ctx.textAlign='right';ctx.fillText(String(Math.floor(dist/10)).padStart(5,'0'),W-10,20);
    if(!ativo){ctx.fillStyle=cor('--ink');ctx.textAlign='center';ctx.font='700 15px Arial';ctx.fillText(fim?'Fim · '+Math.floor(dist/10)+' pontos · toca para recomeçar':'Toca no ecrã ou carrega em espaço para começar',W/2,72)}
    pts.textContent=Math.floor(dist/10);mel.textContent=Math.max(melhor(),Math.floor(dist/10))}
  function novoObs(){const r=R();obs.push(r<.25?{tipo:'pedra',x:W+10,w:30,h:16}:{tipo:'cato',x:W+10,w:16+Math.floor(R()*12),h:28+Math.floor(R()*20)});
    if(R()<.18&&vel>.42)obs.push({tipo:'cato',x:W+34,w:16,h:30});prox=dist+vel*(650+R()*800)}
  function ciclo(t){if(!ativo)return;const dt=Math.min(40,t-ult);ult=t;
    vel=Math.min(.8,vel+dt*0.000006);dist+=vel*dt;
    vy+=0.0022*dt;y=Math.min(CHAO,y+vy*dt);if(y===CHAO)vy=0;
    obs.forEach(o=>o.x-=vel*dt);obs=obs.filter(o=>o.x+o.w>-10);if(dist>=prox)novoObs();
    passoAnim+=dt*0.02;
    const bx=46+6,bw=40,by=y-30;
    if(obs.some(o=>o.x+3<bx+bw&&o.x+o.w-3>bx&&CHAO-o.h+3<y&&by<CHAO)){ativo=false;fim=true;const s=Math.floor(dist/10);if(s>melhor())guardar('jornal-dino-melhor',s);
      msg(estado,'Tropeçaste! Fizeste '+s+' pontos. Toca ou carrega em espaço para tentar de novo.','revelado');desenhar(passoAnim);return}
    desenhar(passoAnim);raf=requestAnimationFrame(ciclo)}
  function reiniciar(){R=aleatorio(J.dino.semente);y=CHAO;vy=0;obs=[];vel=.32;dist=0;prox=500;ativo=false;fim=false;passoAnim=0;desenhar(0)}
  function saltar(){if(!ativo){if(fim)reiniciar();ativo=true;ult=performance.now();msg(estado,'Salta os catos e as pedras. Os obstáculos aparecem pela mesma ordem para todos hoje.');cancelAnimationFrame(raf);raf=requestAnimationFrame(ciclo)}
    if(y>=CHAO){vy=-0.62}}
  cv.addEventListener('pointerdown',e=>{e.preventDefault();cv.focus();saltar()});
  addEventListener('keydown',e=>{if(!ativo&&document.activeElement!==cv)return;if(e.key===' '||e.key==='ArrowUp'||e.key==='w'){saltar();e.preventDefault()}});
  $('dino-saltar').addEventListener('click',saltar);
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&ativo){ativo=false;msg(estado,'Em pausa. Toca para continuar.');desenhar(passoAnim)}});
  addEventListener('resize',()=>{tamanho();desenhar(passoAnim)});
  tamanho();reiniciar();msg(estado,'Toca no ecrã, no botão «Saltar» ou carrega em espaço.');
})();

/* ---------------- Puzzle ---------------- */
if(J.puzzle&&$('puzzle'))(function(){
  const P=J.puzzle,n=P.n,el=$('puzzle'),estado=$('puzzle-estado'),ref=$('puzzle-ref'),cr=Cronometro($('puzzle-crono'));
  const fonte=document.querySelector('.manchete .figura img')||document.querySelector('.figura img');
  el.style.gridTemplateColumns='repeat('+n+',1fr)';
  const pecas=[];for(let i=0;i<n*n;i++){const b=document.createElement('button');b.type='button';b.dataset.p=i;el.appendChild(b);pecas.push(b)}
  let ordem,sel,jog,fim;
  function imagem(){const src=fonte?fonte.src:'';pecas.forEach(b=>b.style.backgroundImage=src?'url("'+src+'")':'');if(ref&&src)ref.src=src;
    if(fonte&&fonte.naturalWidth){const r=fonte.naturalWidth/fonte.naturalHeight;el.style.aspectRatio=Math.min(1.6,Math.max(.75,r))}}
  function desenhar(){pecas.forEach((b,p)=>{const k=ordem[p];b.style.backgroundSize=(n*100)+'% '+(n*100)+'%';
    b.style.backgroundPosition=(k%n)*100/(n-1)+'% '+Math.floor(k/n)*100/(n-1)+'%';b.classList.toggle('sel',p===sel);b.classList.toggle('certa',k===p&&!fim);
    b.setAttribute('aria-label','Peça '+(p+1)+(k===p?', no sítio certo':''))})}
  el.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||fim)return;const p=+b.dataset.p;if(!cr.usado)cr.iniciar();
    if(sel<0){sel=p}else if(sel===p){sel=-1}else{[ordem[sel],ordem[p]]=[ordem[p],ordem[sel]];sel=-1;jog++;
      if(ordem.every((k,i)=>k===i)){fim=true;cr.parar('concluido');el.classList.add('completo');msg(estado,'Imagem completa em '+jog+' trocas e '+cr.texto()+'. Parabéns!','ganho')}
      else msg(estado,jog+(jog===1?' troca':' trocas')+' · '+ordem.filter((k,i)=>k===i).length+' de '+n*n+' peças no sítio.')}
    desenhar()});
  function reiniciar(){ordem=P.ordem.slice();sel=-1;jog=0;fim=false;el.classList.remove('completo');cr.reiniciar();desenhar();
    msg(estado,'Toca em duas peças para as trocar. A imagem é a da manchete de hoje.')}
  $('puzzle-recomecar').addEventListener('click',reiniciar);
  $('puzzle-solucao').addEventListener('click',()=>{ordem=ordem.map((_,i)=>i);fim=true;sel=-1;cr.parar('parado');el.classList.add('completo');desenhar();msg(estado,'Solução revelada. Recomeça para tentar de novo.','revelado')});
  $('puzzle-ver').addEventListener('click',e=>{const v=ref.hidden;ref.hidden=!v;e.currentTarget.textContent=v?'Esconder imagem':'Ver imagem'});
  if(fonte){fonte.loading='eager';fonte.addEventListener('load',()=>{imagem();desenhar()})}
  imagem();reiniciar();
})();

/* ---------------- Quiz da semana ---------------- */
if(J.quiz&&$('quiz'))(function(){
  const Q=J.quiz,el=$('quiz'),estado=$('quiz-estado');
  let certas,resp;
  function render(){el.innerHTML='';certas=0;resp=0;
    Q.forEach((q,k)=>{const f=document.createElement('fieldset');f.className='pergunta';
      f.innerHTML='<legend><span class="qn">'+(k+1)+'.</span> '+q.pergunta.replace(/</g,'&lt;')+'</legend>';
      const ops=document.createElement('div');ops.className='opcoes';
      q.opcoes.forEach((o,j)=>{const b=document.createElement('button');b.type='button';b.className='pill';b.textContent=o;
        b.addEventListener('click',()=>{if(f.dataset.feito)return;f.dataset.feito=1;resp++;
          const ok=j===q.certa;if(ok)certas++;b.classList.add(ok?'certa':'errada');ops.children[q.certa].classList.add('certa');
          const ex=document.createElement('p');ex.className='explicacao';ex.textContent=(ok?'Certo! ':'Não. ')+(q.explicacao||'');
          if(q.ligacao){const a=document.createElement('a');a.href=q.ligacao;a.textContent=' Ler a notícia →';ex.appendChild(a)}
          f.appendChild(ex);atualizar()});ops.appendChild(b)});
      f.appendChild(ops);el.appendChild(f)});atualizar()}
  function atualizar(){if(resp===Q.length)msg(estado,'Acertaste '+certas+' de '+Q.length+'. '+(certas===Q.length?'Leitura em dia!':certas>=Q.length/2?'Boa semana de leitura!':'Há edições da semana à tua espera no arquivo.'),'ganho');
    else msg(estado,resp?certas+(certas===1?' certa':' certas')+' em '+resp+(resp===1?' resposta.':' respostas.'):Q.length+' perguntas sobre as notícias da semana.')}
  $('quiz-recomecar').addEventListener('click',render);
  render();
})();

/* ---------------- Caça-palavras ---------------- */
if(J.caca&&document.getElementById('caca'))(function(){
  const C=J.caca,N=C.tamanho,el=document.getElementById('caca'),lista=document.getElementById('caca-palavras'),estado=document.getElementById('caca-estado');
  const cr=Cronometro(document.getElementById('caca-crono'));
  el.style.gridTemplateColumns='repeat('+N+',1fr)';
  const cel=[];C.grelha.join('').split('').forEach((l,i)=>{const d=document.createElement('div');d.textContent=l;d.dataset.i=i;el.appendChild(d);cel.push(d)});
  const itens=C.palavras.map(p=>{const li=document.createElement('li');li.textContent=p.mostrar;lista.appendChild(li);return li});
  let achadas,revelado,terminado,inicio=-1,arrasto=false,ultimo=-1;
  function linha(a,b){const r1=Math.floor(a/N),c1=a%N,r2=Math.floor(b/N),c2=b%N,dr=Math.sign(r2-r1),dc=Math.sign(c2-c1);
    const len=Math.max(Math.abs(r2-r1),Math.abs(c2-c1));
    if(len===0)return[a];if(!(r1===r2||c1===c2||Math.abs(r2-r1)===Math.abs(c2-c1)))return null;
    const out=[];for(let k=0;k<=len;k++)out.push((r1+dr*k)*N+c1+dc*k);return out}
  function limparSel(){cel.forEach(d=>d.classList.remove('marca-sel','inicio'))}
  function mostrarSel(a,b){limparSel();const l=linha(a,b);if(l)l.forEach(i=>cel[i].classList.add('marca-sel'));else cel[a].classList.add('inicio')}
  function avaliar(a,b){
    const l=linha(a,b);limparSel();if(!l||l.length<2||terminado)return;
    if(!cr.usado)cr.iniciar();
    const s=l.join(','),r=l.slice().reverse().join(',');
    C.palavras.forEach((p,k)=>{if(achadas.has(k))return;const x=p.celulas.join(',');
      if(x===s||x===r){achadas.add(k);itens[k].classList.add('ok');p.celulas.forEach(i=>cel[i].classList.add('encontrada'))}});
    estado.textContent=achadas.size+' de '+C.palavras.length+' palavras encontradas.';
    if(achadas.size===C.palavras.length){terminado=true;cr.parar('concluido');estado.textContent='Todas encontradas em '+cr.texto()+'. Parabéns!';estado.className='estado-jogo ganho'}
  }
  const celDe=e=>{const t=document.elementFromPoint(e.clientX,e.clientY);return t&&t.parentNode===el?+t.dataset.i:-1};
  el.addEventListener('pointerdown',e=>{if(terminado)return;const i=celDe(e);if(i<0)return;e.preventDefault();
    if(inicio>=0&&!arrasto&&i!==inicio){const a=inicio;inicio=-1;avaliar(a,i);return}
    inicio=i;ultimo=i;arrasto=true;mostrarSel(i,i);cel[i].classList.add('inicio')});
  el.addEventListener('pointermove',e=>{if(!arrasto||inicio<0)return;const i=celDe(e);if(i>=0&&i!==ultimo){ultimo=i;mostrarSel(inicio,i)}});
  const soltar=e=>{if(!arrasto)return;arrasto=false;const i=celDe(e);
    if(i>=0&&i!==inicio){const a=inicio;inicio=-1;avaliar(a,i)}
    else{limparSel();if(inicio>=0)cel[inicio].classList.add('inicio')}};
  el.addEventListener('pointerup',soltar);el.addEventListener('pointercancel',()=>{arrasto=false;inicio=-1;limparSel()});
  function reiniciar(){achadas=new Set();revelado=false;terminado=false;inicio=-1;cr.reiniciar();
    cel.forEach(d=>d.className='');itens.forEach(li=>li.className='');
    estado.textContent='O tempo começa na primeira seleção.';estado.className='estado-jogo'}
  document.getElementById('caca-recomecar').addEventListener('click',reiniciar);
  document.getElementById('caca-solucao').addEventListener('click',()=>{if(terminado&&!revelado)return;revelado=true;terminado=true;cr.parar('parado');
    C.palavras.forEach((p,k)=>{if(!achadas.has(k))p.celulas.forEach(i=>cel[i].classList.add('revel'));itens[k].classList.add('ok')});
    estado.textContent='Solução revelada'+(cr.usado?' aos '+cr.texto():'')+'. Recomeça para tentar de novo.';estado.className='estado-jogo revelado'});
  reiniciar();
})();

/* ---------------- Agenda: marcar o dia escolhido no menu ---------------- */
(function(){
  const links=[...document.querySelectorAll('.menu-dias a')];
  const marcar=()=>{const h=location.hash||'';const alvo=links.find(a=>a.getAttribute('href')===h)||links[0];links.forEach(a=>a.setAttribute('aria-current',a===alvo?'true':'false'))};
  window.addEventListener('hashchange',marcar);marcar();
})();
/* ---------------- Agenda: separadores (edições antigas) ---------------- */
document.querySelectorAll('.dias button').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.dias button').forEach(x=>x.setAttribute('aria-selected',x===b));
  document.querySelectorAll('.dia-agenda').forEach(p=>p.hidden=p.id!==b.getAttribute('aria-controls'));
}));

})();
