(function(){
"use strict";
const J = JSON.parse(document.getElementById('dados-jogos').textContent);

function Cronometro(el){
  let inicio=0, acumulado=0, id=null;
  const fmt=ms=>{const s=Math.floor(ms/1000);return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')};
  const desenhar=()=>{el.textContent=fmt(acumulado+(inicio?Date.now()-inicio:0))};
  return {
    get ativo(){return !!inicio},
    get usado(){return !!inicio||acumulado>0},
    iniciar(){if(inicio)return;inicio=Date.now();el.classList.remove('parado','concluido');id=setInterval(desenhar,250);desenhar()},
    parar(classe){if(inicio){acumulado+=Date.now()-inicio;inicio=0}clearInterval(id);id=null;desenhar();el.classList.add(classe||'parado')},
    reiniciar(){inicio=0;acumulado=0;clearInterval(id);id=null;el.className='crono parado';desenhar()},
    texto(){return el.textContent}
  };
}

/* ---------------- Sudoku ---------------- */
(function(){
  const S=J.sudoku, grelha=document.getElementById('sudoku'), estado=document.getElementById('sudoku-estado');
  const cr=Cronometro(document.getElementById('sudoku-crono'));
  let tab, sel=-1, revelado=false, terminado=false;
  const celulas=[];
  for(let i=0;i<81;i++){
    const b=document.createElement('button');b.type='button';
    const r=Math.floor(i/9),c=i%9;
    if(c%3===2&&c<8)b.classList.add('c3'); if(r%3===2&&r<8)b.classList.add('l3');
    b.setAttribute('aria-label','Linha '+(r+1)+', coluna '+(c+1));
    b.addEventListener('click',()=>{sel=i;desenhar()});
    grelha.appendChild(b);celulas.push(b);
  }
  function conflito(i){const v=tab[i];if(!v)return false;const r=Math.floor(i/9),c=i%9;
    for(let k=0;k<81;k++){if(k===i||tab[k]!==v)continue;const r2=Math.floor(k/9),c2=k%9;
      if(r2===r||c2===c||(Math.floor(r2/3)===Math.floor(r/3)&&Math.floor(c2/3)===Math.floor(c/3)))return true}return false}
  function desenhar(){
    const vs=sel>=0?tab[sel]:0;
    celulas.forEach((b,i)=>{
      const v=tab[i];b.textContent=v||'';
      b.classList.toggle('fixo',S.puzzle[i]!==0);
      b.classList.toggle('sel',i===sel);
      b.classList.toggle('mesma',vs&&v===vs&&i!==sel);
      b.classList.toggle('erro',S.puzzle[i]===0&&conflito(i));
      b.classList.toggle('revel',revelado&&S.puzzle[i]===0);
      b.setAttribute('aria-label','Linha '+(Math.floor(i/9)+1)+', coluna '+(i%9+1)+(v?', '+v:', vazia'));
    });
  }
  function jogar(v){
    if(sel<0||terminado||S.puzzle[sel]!==0)return;
    if(tab[sel]===v)return;
    if(v && !cr.usado) cr.iniciar();
    tab[sel]=v;desenhar();
    if(tab.every((x,i)=>x===S.solucao[i])){terminado=true;cr.parar('concluido');estado.textContent='Concluído em '+cr.texto()+'. Parabéns!';estado.className='estado-jogo ganho'}
  }
  function reiniciar(){tab=S.puzzle.slice();sel=-1;revelado=false;terminado=false;cr.reiniciar();estado.textContent='O tempo começa no primeiro número que colocares.';estado.className='estado-jogo';desenhar()}
  document.querySelectorAll('#sudoku-teclado button').forEach(b=>b.addEventListener('click',()=>jogar(+b.dataset.v)));
  document.getElementById('sudoku-recomecar').addEventListener('click',reiniciar);
  document.getElementById('sudoku-solucao').addEventListener('click',()=>{
    if(terminado&&!revelado)return;tab=S.solucao.slice();revelado=true;terminado=true;cr.parar('parado');
    estado.textContent='Solução revelada'+(cr.usado?' aos '+cr.texto():'')+'. Recomeça para tentar de novo.';estado.className='estado-jogo revelado';desenhar()});
  grelha.addEventListener('keydown',e=>{
    if(e.key>='1'&&e.key<='9'){jogar(+e.key);e.preventDefault()}
    else if(e.key==='Backspace'||e.key==='Delete'||e.key==='0'){jogar(0);e.preventDefault()}
    else{const m={ArrowUp:-9,ArrowDown:9,ArrowLeft:-1,ArrowRight:1}[e.key];if(m!==undefined&&sel>=0){const n=sel+m;if(n>=0&&n<81){sel=n;desenhar();celulas[n].focus()}e.preventDefault()}}
  });
  reiniciar();
})();

/* ---------------- Caça-palavras ---------------- */
(function(){
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

/* ---------------- Agenda: separadores ---------------- */
document.querySelectorAll('.dias button').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.dias button').forEach(x=>x.setAttribute('aria-selected',x===b));
  document.querySelectorAll('.dia-agenda').forEach(p=>p.hidden=p.id!==b.getAttribute('aria-controls'));
}));

})();
