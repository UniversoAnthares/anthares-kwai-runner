(function(){
'use strict';
const root=document.getElementById('anthares-estudio-root');
if(!root||!window.AntharesEstudio)return;
const cfg=window.AntharesEstudio;
// Keep the writer's visual preference in this browser. New installations open in dark mode.
const themeStorageKey='anthares_studio_theme_v1';
let themeMode='dark';
try{const saved=window.localStorage.getItem(themeStorageKey);const initial=saved===null?window.localStorage.getItem('anthares_estudio_theme_v1'):saved;themeMode=initial==='light'?'light':'dark';}catch(_){}
function applyTheme(mode){
 themeMode=mode==='light'?'light':'dark';
 document.body.classList.toggle('aest-dark-mode',themeMode==='dark');
 root.dataset.theme=themeMode;
}
applyTheme(themeMode);
window.addEventListener('storage',ev=>{
 if(ev.key===themeStorageKey){
  applyTheme(ev.newValue==='light'?'light':'dark');
  const control=root.querySelector('[data-action="theme-toggle"]');
  if(control){control.innerHTML='<span aria-hidden="true">'+(themeMode==='dark'?'☼':'☾')+'</span>'+(themeMode==='dark'?'Modo claro':'Modo escuro');
   control.setAttribute('aria-pressed',String(themeMode==='dark'));}
 }
});
const endpoint=new URL(cfg.rest,location.href);
const base=endpoint.pathname.replace(/\/?$/,'/');
let db={projects:[],notes:[],chapters:[],cards:[]};let fullDataLoaded=false;let loadedScope='slim';let trashItems=[];
let view='inicio',projectId=0,tab='visao',chapterId=0,editor=null,lastRange=null,saveTimer=null,saveBusy=false,savePending=false,dirty=false,flash='';
const $=s=>root.querySelector(s);
const esc=s=>String(s===undefined||s===null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const words=d=>{if(!d||!Array.isArray(d.ops))return 0;return (d.ops.map(o=>typeof o.insert==='string'?o.insert:' ').join(' ').trim().match(/\S+/g)||[]).length};
const findProject=()=>db.projects.find(p=>p.id===projectId);
const findChapter=()=>db.chapters.find(c=>c.id===chapterId);
const projectChapters=()=>db.chapters.filter(c=>c.project===projectId).sort((a,b)=>a.order-b.order||a.id-b.id);
const projectNotes=(kind)=>db.notes.filter(n=>n.project===projectId&&(!kind||n.kind===kind));
const hotmart=esc(cfg.hotmart);
async function api(method,path,payload){
 const url=base+path+(method==='GET'?(path.includes('?')?'&':'?')+'fresh='+Date.now():'');
 const res=await fetch(url,{method,headers:{'X-WP-Nonce':cfg.nonce,'Content-Type':'application/json'},credentials:'same-origin',body:payload?JSON.stringify(payload):undefined,cache:'no-store'});
 let data;try{data=await res.json()}catch(e){throw Error('Não foi possível interpretar a resposta do site.');}
 if(!res.ok)throw Error(data.message||'A operação falhou. Tente novamente.');
 return data;
}
async function reload(scope=0){
 const wanted=Number(scope)||0;
 const fresh=await api('GET','bootstrap'+(wanted?'?project='+wanted:''));
 if(!fresh||!Array.isArray(fresh.projects)||!Array.isArray(fresh.notes)||!Array.isArray(fresh.chapters))
   throw Error('O servidor não devolveu o conteúdo solicitado. Os dados permanecem salvos.');
 if(!Array.isArray(fresh.cards))fresh.cards=[];
 db=fresh;fullDataLoaded=true;loadedScope=wanted||'all';
}
async function ensureFullData(scope=0){
 const wanted=Number(scope)||0;
 if(!fullDataLoaded||(wanted&&loadedScope!=='all'&&loadedScope!==wanted)||(!wanted&&loadedScope!=='all'))
   await reload(wanted);
}
async function fetchTrash(){const out=await api('GET','trash');trashItems=out.items||[];}

// Deep-link routing: every navigable screen has a stable URL.
// WordPress owns /studio/; only the fragment identifies the cloned UI state.
let routeReady=false,routeRestoring=false,routeSerial=0,routeEventScheduled=false,routeScrollTimer=null;
const routeViews=['inicio','novo','projetos','ideias','lixeira','ajuda'];
const routeTabs=['visao','planejamento','pesquisa','elementos','estrutura','manuscrito','analises','revisao','publicacao'];
const routeSections=['mural','assunto','premissa','logline','storyline','tema','outline'];
let structureSection='atos',editingElementFolder='';
function routeFromLocation(){
 const raw=(location.hash||'').replace(/^#\/?/,'');
 const parts=raw.split('/').filter(Boolean);
 if(parts[0]!=='studio'||!parts[1])return{view:'inicio'};
 if(routeViews.includes(parts[1]))return{view:parts[1]};
 if(parts[1]==='projeto'){
   const id=Number(parts[2]);
   if(!Number.isSafeInteger(id)||id<1)return{view:'projetos',invalid:true};
   const nextTab=routeTabs.includes(parts[3])?parts[3]:'planejamento';
   const section=nextTab==='planejamento'&&routeSections.includes(parts[4])?parts[4]:null;
   const nextChapter=nextTab==='manuscrito'&&parts[4]==='capitulo'?Number(parts[5]):0;
   const structure=nextTab==='estrutura'&&['cronologia','jornada'].includes(parts[4])?parts[4]:'atos';
   return{view:'projeto',id,tab:nextTab,section,structure,
     chapter:Number.isSafeInteger(nextChapter)&&nextChapter>0?nextChapter:0};
 }
 return{view:'inicio',invalid:true};
}
function currentRouteHash(){
 if(view!=='projeto')return '#studio/'+(routeViews.includes(view)?view:'inicio');
 const p=findProject();
 if(!p||!projectId)return'#studio/projetos';
 const nextTab=routeTabs.includes(tab)?tab:'visao';
 let suffix='';
 if(nextTab==='estrutura'&&structureSection!=='atos')suffix='/'+structureSection;
 if(nextTab==='planejamento'&&p.start!=='manuscrito'&&!unlockShowPlanning){
   const ix=conceptOrder.indexOf(unlockState(p).step);
   suffix='/'+routeSections[ix>=0?ix:0];
 }else if(nextTab==='manuscrito'&&chapterId>0){
   suffix='/capitulo/'+chapterId;
 }
 return '#studio/projeto/'+projectId+'/'+nextTab+suffix;
}
function writeCurrentScroll(){
 if(!routeReady||routeRestoring||!window.history?.replaceState)return;
 const current=window.history.state&&typeof window.history.state==='object'?window.history.state:{};
 window.history.replaceState({...current,anstScrollY:Math.max(0,window.scrollY||0)},'',location.href);
}
function syncRouteOnRender(){
 if(!routeReady||routeRestoring)return;
 const wanted=currentRouteHash();
 if(location.hash===wanted)return;
 if(window.history?.pushState){
   writeCurrentScroll();
   window.history.pushState({anstScrollY:0},'',wanted);
 }else location.hash=wanted;
}
function restoreScroll(y,serial){
 const restore=()=>{
   if(serial!==routeSerial)return;
   window.scrollTo({top:Math.max(0,Math.floor(Number(y)||0)),behavior:'instant'});
 };
 if(typeof window.requestAnimationFrame==='function')
   window.requestAnimationFrame(()=>window.requestAnimationFrame(restore));
 else setTimeout(restore,0);
}
async function openRouteFromLocation({initial=false}={}){
 const serial=++routeSerial,route=routeFromLocation();
 try{
   if(!initial){
     if(dirty&&chapterId)await saveChapter();
     if(unlockDirty&&view==='projeto')await saveUnlock();
     if(unlockBusy)await unlockBusy;
   }
   if(route.view==='ideias')await ensureFullData();
   if(route.view==='projeto')await ensureFullData(route.id);
   if(route.view==='lixeira')await fetchTrash();
   if(serial!==routeSerial)return;
   routeRestoring=true;
   unlockEditing=false;unlockShowPlanning=false;
   chapterId=0;tab='visao';projectId=0;structureSection='atos';
   if(route.view==='projeto'){
     const p=db.projects.find(x=>x.id===route.id);
     if(!p){view='projetos';flash='Projeto indisponível ou excluído.';}
     else{
       view='projeto';projectId=p.id;tab=route.tab;structureSection=route.structure||'atos';
       if(route.section&&p.start!=='manuscrito'&&tab==='planejamento'){
         const ix=routeSections.indexOf(route.section);
         unlockState(p).step=conceptOrder[ix];
       }
       if(route.chapter&&tab==='manuscrito'){
         const chapter=db.chapters.find(c=>c.id===route.chapter&&c.project===p.id);
         chapterId=chapter?chapter.id:0;
       }
     }
   }else view=route.view;
   render();
   const canonical=currentRouteHash();
   if(location.hash!==canonical&&window.history?.replaceState){
     window.history.replaceState({anstScrollY:0},'',canonical);
   }
   routeReady=true;routeRestoring=false;
   const savedY=window.history?.state?.anstScrollY||0;
   restoreScroll(savedY,serial);
 }catch(error){
   if(serial!==routeSerial)return;
   routeRestoring=false;routeReady=true;
   view='inicio';projectId=0;chapterId=0;tab='visao';
   flash='Não foi possível abrir a seção solicitada: '+error.message;
   render();
 }
}
function scheduleRouteRestore(){
 if(!routeReady||routeEventScheduled)return;
 routeEventScheduled=true;
 Promise.resolve().then(()=>{
   routeEventScheduled=false;
   openRouteFromLocation().catch(e=>{flash=e.message;render()});
 });
}
window.addEventListener('popstate',scheduleRouteRestore);
window.addEventListener('hashchange',scheduleRouteRestore);
window.addEventListener('pagehide',writeCurrentScroll);
window.addEventListener('scroll',()=>{
 if(!routeReady||routeRestoring)return;
 clearTimeout(routeScrollTimer);
 routeScrollTimer=setTimeout(writeCurrentScroll,220);
},{passive:true});
if(window.history&&'scrollRestoration'in window.history)window.history.scrollRestoration='manual';

function notice(){const msg=flash;flash='';return msg?'<div role="status" class="aest-alert">'+esc(msg)+'</div>':'';}
function btn(label,act,attrs='',primary=false){return '<button type="button" class="aest-btn'+(primary?' aest-primary':'')+'" data-action="'+act+'" '+attrs+'>'+label+'</button>'}
function noteForm(kind,prId,placeholder){
 return '<form class="aest-form" data-form="note" data-kind="'+kind+'" data-project="'+(prId||0)+'"><label for="aest-note-text">'+(kind==='research'?'Nova anotação de pesquisa':kind==='review'?'Nova observação de revisão':'Registre sua ideia')+'</label><textarea id="aest-note-text" name="text" required maxlength="20000" placeholder="'+esc(placeholder)+'"></textarea><div class="aest-form-footer"><button type="submit" class="aest-btn aest-primary">Salvar anotação</button><span class="aest-hint">A anotação ficará guardada na sua conta.</span></div></form>';
}
function noteList(arr){return arr.length?'<div class="aest-list">'+arr.map(n=>
 '<div class="aest-list-row aest-note-list-row"><div class="aest-note" tabindex="0" aria-label="Texto da anotação">'+esc(n.text)+'</div>'+
 btn('Excluir','trash-item','data-id="'+n.id+'"')+'</div>').join('')+'</div>':
 '<div class="aest-empty">Ainda não há anotações nesta seção.</div>'}
// G6: exatamente cinco destinos globais, idênticos em qualquer contexto de projeto.
function sidebar(){
 const nav=[['inicio','⌂','Início'],['projetos','▤','Meus projetos'],['ideias','✧','Banco de ideias']];
 const projectArea=view==='projetos'||view==='projeto'||view==='lixeira'||view==='novo';
 return '<aside class="aest-nav" aria-label="Menu do Estúdio"><div class="aest-nav-title">Estúdio de Escrita</div>'+
 nav.map(x=>'<button type="button" data-action="nav" data-view="'+x[0]+'" class="'+((view===x[0]||(projectArea&&x[0]==='projetos'))?'is-current':'')+'"><span aria-hidden="true">'+x[1]+'</span>'+x[2]+'</button>').join('')+
 '<a href="'+hotmart+'" target="_blank" rel="noopener noreferrer"><span aria-hidden="true">▣</span>Curso de Escrita ↗</a>'+
 '<button type="button" data-action="nav" data-view="ajuda" class="'+(view==='ajuda'?'is-current':'')+'"><span aria-hidden="true">?</span>Ajuda</button>'+
 '<button type="button" class="aest-theme-toggle" data-action="theme-toggle" aria-pressed="'+(themeMode==='dark')+'" title="Alternar aparência do Estúdio"><span aria-hidden="true">'+(themeMode==='dark'?'☼':'☾')+'</span>'+(themeMode==='dark'?'Modo claro':'Modo escuro')+'</button></aside>';
}
function startCards(){const data=[
 ['sem-ideia','✧','Não sei o que escrever','Etapa 1: mural de ideias'],
 ['assunto','⌕','Quero partir de um assunto','Etapa 2: assunto e pesquisa inicial'],
 ['ideia','♧','Já tenho uma ideia de história','Etapa 3: premissa · logline · storyline · outline'],
 ['manuscrito','▤','Já tenho um manuscrito','Etapa 4: capítulos · organização · revisão']
 ];return '<div class="aest-cards">'+data.map(x=>'<button type="button" class="aest-path" data-action="start" data-mode="'+x[0]+'"><span class="aest-icon" aria-hidden="true">'+x[1]+'</span><strong>'+x[2]+' →</strong><small>'+x[3]+'</small></button>').join('')+'</div>'}
function renderStart(){
 return '<h1>Bem-vindo(a) ao Estúdio de Escrita.</h1><p class="aest-lead">Escolha como você quer começar. Seu projeto será criado e a ferramenta adequada será aberta.</p>'+
 '<h2>Como você quer começar?</h2>'+startCards()+
 '<div class="aest-sub-actions">'+btn('✎ Registrar uma ideia rápida','nav','data-view="ideias"')+
 '<a class="aest-btn" href="'+hotmart+'" target="_blank" rel="noopener noreferrer">↗ Abrir curso na Hotmart</a>'+
 btn('ⓘ Ver como funciona','nav','data-view="ajuda"')+'</div>';
}
function renderProjects(){
 const category={
  'sem-ideia':'Come\u00e7ando uma hist\u00f3ria',
  'assunto':'Partindo de um assunto',
  'ideia':'Ideia de hist\u00f3ria',
  'manuscrito':'Manuscrito'
 };
 const tones=[['none','Padr\u00e3o'],['sea','Verde-\u00e1gua'],['blue','Azul'],['violet','Lil\u00e1s'],['rose','Rosa'],['amber','Dourado'],['forest','Verde'],['slate','Cinza']];
 const cards=db.projects.map(p=>{
  const id=Number(p.id);
  const title=esc(p.title||'Projeto sem t\u00edtulo');
  const raw=String(p.created||'').slice(0,10);
  const match=raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const when=match?match[3]+'/'+match[2]+'/'+match[1]:'data indispon\u00edvel';
  const kind=category[p.start]||'Projeto de escrita';
  const tone=tones.some(x=>x[0]===p.color)?p.color:'none';
  const choices=tones.map(([value,label])=>
   '<button type="button" class="aest-project-color-swatch" data-action="project-color" data-id="'+id+
    '" data-tone="'+value+'" title="'+label+'" aria-label="Cor '+label+'" aria-pressed="'+(tone===value)+'">'+
    '<span class="aest-project-swatch-fill aest-tone-'+value+'" aria-hidden="true"></span>'+
    '<span class="aest-project-swatch-label">'+label+'</span>'+
   '</button>').join('');
  return '<article class="aest-project-tile" data-tone="'+tone+'">'+
   '<button type="button" class="aest-project-tile-open" data-action="open-project" data-id="'+id+'" aria-label="Abrir '+title+'">'+
    '<span class="aest-project-tile-top">'+
     '<span class="aest-project-tile-icon" aria-hidden="true">&#9636;</span>'+
     '<span class="aest-project-tile-status">Privado</span>'+
    '</span>'+
    '<span class="aest-project-tile-title">'+title+'</span>'+
    '<span class="aest-project-tile-kind">'+esc(kind)+'</span>'+
    '<span class="aest-project-tile-bottom">'+
     '<span class="aest-project-tile-details">Criado em '+when+' <span aria-hidden="true">&#183;</span> N\u00ba '+id+'</span>'+
     '<span class="aest-project-tile-open-label">Abrir projeto <span aria-hidden="true">&#8594;</span></span>'+
    '</span>'+
   '</button>'+
   '<div class="aest-project-color-controls">'+
    '<button type="button" class="aest-project-color-trigger" data-action="project-color-menu" data-id="'+id+
    '" aria-expanded="false" aria-label="Escolher cor de '+title+'" title="Escolher cor do projeto">'+
    '<span aria-hidden="true">\uD83C\uDFA8</span></button>'+
    '<div class="aest-project-color-palette" role="group" aria-label="Cores do projeto" hidden>'+
     '<strong>Cor do projeto</strong><div class="aest-project-color-options">'+choices+'</div>'+
    '</div>'+
   '</div>'+
   '<button type="button" class="aest-project-tile-delete" data-action="delete-project" data-id="'+id+'" aria-label="Mover '+title+' para a lixeira" title="Mover para a lixeira">'+
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2m3 0-1 14H6L5 6m5 4v6m4-6v6"/></svg>'+
   '</button>'+
  '</article>';
 }).join('');
 return '<div class="aest-row aest-projects-heading"><div><h1>Meus projetos</h1><p class="aest-muted">Seus livros e hist\u00f3rias em desenvolvimento.</p></div>'+
  btn('+ Novo projeto','nav','data-view="novo"',true)+btn('Lixeira','nav','data-view="lixeira" aria-label="Abrir lixeira dos projetos"')+'</div>'+
  (db.projects.length?'<section class="aest-project-grid" aria-label="Projetos salvos">'+cards+'</section>':
   '<div class="aest-empty">Voc\u00ea ainda n\u00e3o criou projetos. Escolha um ponto de partida para come\u00e7ar.</div>');
}
function renderIdeas(){
 const all=db.notes.filter(n=>n.kind==='idea'&&!n.project).sort((a,b)=>b.id-a.id);
 return '<h1>Banco de ideias</h1><p class="aest-lead">Guarde pensamentos e possibilidades de histórias antes de decidir em qual livro utilizá-los.</p>'+
 '<section class="aest-ideas-entry">'+noteForm('idea',0,'Uma situação, um personagem, uma pergunta ou algo que você gostaria de escrever…')+'</section>'+
 '<section class="aest-ideas-saved" aria-live="polite"><h2 class="aest-section-heading">Ideias guardadas ('+all.length+')</h2>'+noteList(all)+'</section>';
}

function renderTrash(){
 const rows=[...trashItems].sort((a,b)=>(b.trashedAt||0)-(a.trashedAt||0));
 const labelDate=sec=>sec?new Date(Number(sec)*1000).toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric'}):'Data desconhecida';
 return '<div class="aest-row"><div><h1>Lixeira</h1>'+
   '<p class="aest-muted">Itens excluídos permanecem por 7 dias. Depois disso, são apagados automaticamente e não podem ser recuperados.</p>'+
   '</div>'+btn('Atualizar','trash-refresh')+'</div>'+
  (rows.length?'<div class="aest-list aest-trash-list">'+rows.map(x=>{
   const parent=rows.find(p=>p.id===x.project&&p.type==='anst_projeto');
   const info=x.cascade&&parent?' · excluído junto com "'+esc(parent.title)+'"':'';
   return '<div class="aest-list-row aest-trash-row">'+
     '<div class="aest-trash-description"><strong>'+esc(x.title)+'</strong>'+
     '<div class="aest-hint">'+esc(x.typeLabel)+info+
     ' · excluído em '+labelDate(x.trashedAt)+
     ' · exclusão definitiva: '+labelDate(x.expiresAt)+'</div></div>'+
     '<div class="aest-trash-actions">'+
       btn('Restaurar','trash-restore','data-id="'+x.id+'"')+
       btn('Excluir definitivamente','trash-permanent','data-id="'+x.id+'"')+
     '</div></div>';
  }).join('')+'</div>':'<div class="aest-empty">A lixeira está vazia.</div>');
}

function renderHelp(){
 return '<h1>Como funciona o Estúdio</h1><p class="aest-lead">Cada projeto guarda seus materiais. Você pode escrever, pesquisar e planejar na ordem que preferir.</p>'+
 '<div class="aest-list"><div class="aest-list-row"><div><strong>1. Comece como preferir</strong><p class="aest-muted">Você pode começar sem ideia, com um assunto, uma história ou um texto pronto.</p></div>'+btn('Começar →','nav','data-view="novo"')+'</div>'+
 '<div class="aest-list-row"><div><strong>2. Escreva e organize</strong><p class="aest-muted">Use Planejamento para a premissa e Manuscrito para os capítulos.</p></div>'+btn('Ver meus projetos →','nav','data-view="projetos"')+'</div>'+
 '<div class="aest-list-row"><div><strong>3. Consulte as aulas</strong><p class="aest-muted">O curso está hospedado na Hotmart. As atividades práticas ficam aqui.</p></div><a class="aest-btn" href="'+hotmart+'" target="_blank" rel="noopener noreferrer">Abrir Hotmart ↗</a></div></div>';
}
const projectGroups=[['visao','Vis\u00e3o geral'],['pesquisa','Pesquisa'],['planejamento','Planejamento'],['manuscrito','Manuscrito'],['analises','An\u00e1lises'],['revisao','Revis\u00e3o'],['publicacao','Publica\u00e7\u00e3o']];
const planningTools=[['planejamento','Conceito'],['elementos','Personagens e universo'],['estrutura','Estrutura']];
function activeProjectGroup(){return tab==='elementos'||tab==='estrutura'?'planejamento':tab;}
function projectTabs(){const active=activeProjectGroup();
 return '<div class="aest-tabs aest-group-tabs" role="tablist" aria-label="Grupos do projeto">'+
 projectGroups.map(t=>'<button role="tab" type="button" data-action="tab" data-tab="'+t[0]+'" aria-selected="'+(active===t[0])+'">'+t[1]+'</button>').join('')+'</div>';}
function planningSubnav(){if(activeProjectGroup()!=='planejamento')return'';
 return '<nav class="aest-planning-subnav" aria-label="Ferramentas de planejamento">'+
 planningTools.map(t=>'<button type="button" data-action="tab" data-tab="'+t[0]+'" aria-current="'+(tab===t[0]?'page':'false')+'">'+t[1]+'</button>').join('')+'</nav>';
}

// Percurso pedagógico M1/A2, M2/A8 e M2/A9, organizado em uma tarefa por tela.
let unlockDirty=false,unlockBusy=null,unlockTimer=null,unlockEditing=false,unlockShowPlanning=false;
const unlockSteps=[
 ['Brainstorm','Anote tudo o que vier à cabeça','Reserve alguns minutos para escrever palavras, lembranças, situações, personagens ou perguntas. Registre cada ideia em uma linha. Você escolherá o assunto depois.'],
 ['Assunto e primeira frase','Encontre um assunto e escreva uma frase','Consulte os cartões do mural e escolha um assunto que desperte seu interesse. Em seguida, registre uma frase de partida.'],
 ['Desenvolvimento inicial','Amplie sua frase em um parágrafo','Acrescente detalhes à frase: quem poderia participar da história, o que poderia acontecer e onde a situação se passa.'],
 ['Premissa','Formule a premissa da sua história','Transforme o assunto em uma pergunta narrativa. A aula sugere começar por “E se...?” ou “Como seria se...?”.'],
 ['Possibilidades narrativas','Pense no que pode acontecer','A partir da premissa, faça outro brainstorm: possíveis personagens, consequências, acontecimentos, locais ou revelações.'],
 ['Conflito principal','Defina quem age, o que deseja e o que impede','O protagonista precisa de um objetivo e encontrará dificuldades. Identifique esses três elementos antes da logline.'],
 ['Logline','Escreva a logline','Resuma o protagonista, seu objetivo e o obstáculo em uma frase. Use os elementos que você acabou de definir.'],
 ['Storyline','Escreva a storyline','Acrescente o acontecimento que coloca a história em movimento e explique como ele leva ao conflito.'],
 ['Tema, tese e tom','Defina o tema e a tese','Registre o assunto central, a ideia que deseja desenvolver por meio da história e a tonalidade que pretende utilizar.'],
 ['Resumo e eventos','Resuma a história e anote os acontecimentos','Descreva a trajetória geral em um parágrafo. Em seguida, liste os acontecimentos importantes, um por linha.'],
 ['Outline','Organize os eventos da sua história','Coloque os acontecimentos em uma ordem de leitura. Cada linha representa um evento. Você poderá ajustar a sequência depois.']
];
function unlockState(p){
 if(!p.unlock)p.unlock={version:2,revision:0,step:0,completed:false};
 const u=p.unlock;
 const olderLogline=!Object.prototype.hasOwnProperty.call(u,'logline_mode')&&Boolean(u.logline);
 const olderStoryline=!Object.prototype.hasOwnProperty.call(u,'storyline_mode')&&Boolean(u.storyline);
 for(const f of ['brainstorm','pattern','sentence','paragraph','premise','developments','protagonist',
  'objective','obstacle','logline','turning','storyline','theme','thesis','tone','summary','events','outline','expanded_topics','questions_outline',
  'logline_custom','logline_actor','logline_action','logline_goal','logline_want','logline_block',
  'storyline_custom','storyline_incident','storyline_actor','storyline_goal','storyline_challenge','storyline_stakes']){
   if(typeof u[f]!=='string')u[f]='';
 }
 if(!['free','template'].includes(u.logline_mode)){
   u.logline_mode=olderLogline?'free':'template';
   if(olderLogline&&!u.logline_custom)u.logline_custom=u.logline;
 }
 if(!['free','template'].includes(u.storyline_mode)){
   u.storyline_mode=olderStoryline?'free':'template';
   if(olderStoryline&&!u.storyline_custom)u.storyline_custom=u.storyline;
 }
 if(!['need','want'].includes(u.logline_template))u.logline_template='need';
 u.step=Math.max(0,Math.min(10,Number(u.step)||0));
 return u;
}
function templateText(u,kind,withPlaceholders=false){
 const item=(key,placeholder)=>String(u[key]||'').trim()||(withPlaceholders?'['+placeholder+']':'');
 if(kind==='logline'){
  if(u.logline_template==='want'){
   const a=item('logline_actor','alguém'),b=item('logline_want','alguma coisa'),c=item('logline_block','algo');
   return (a&&b&&c)?a+' quer '+b+' mas '+c+' o impede.':'';
  }
  const a=item('logline_actor','alguém'),b=item('logline_action','fazer algo'),c=item('logline_goal','completar um objetivo');
  return (a&&b&&c)?a+' precisa '+b+' para '+c+'.':'';
 }
 const a=item('storyline_incident','um acontecimento importante'),b=item('storyline_actor','personagem'),
   c=item('storyline_goal','um objetivo'),d=item('storyline_challenge','superar desafios'),
   e=item('storyline_stakes','há coisas em jogo');
 return a&&b&&c&&d&&e?'Após '+a+', um '+b+' decide '+c+', porém ele precisará '+d+' porque '+e+'.':'';
}
function syncNarrativeText(u,kind){
 if(kind==='logline')u.logline=u.logline_mode==='free'?u.logline_custom:templateText(u,'logline');
 if(kind==='storyline')u.storyline=u.storyline_mode==='free'?u.storyline_custom:templateText(u,'storyline');
}
function inlineSlot(name,label,value,placeholder){
 return '<input type="text" class="aest-sentence-slot" data-unlock-field="'+name+
  '" aria-label="'+esc(label)+'" title="'+esc(label)+'" placeholder="'+esc(placeholder)+
  '" maxlength="2500" value="'+esc(value)+'">';
}
function sentenceEditor(u,kind){
 const isLogline=kind==='logline',mode=isLogline?u.logline_mode:u.storyline_mode;
 const modelToggle='<div class="aest-mode-controls" role="group" aria-label="Modo de escrita">'+
   btn('Preencher a frase da aula','sentence-mode','data-kind="'+kind+'" data-mode="template" aria-pressed="'+(mode==='template')+'"')+
   btn('Escrever livremente','sentence-mode','data-kind="'+kind+'" data-mode="free" aria-pressed="'+(mode==='free')+'"')+
   '</div>';
 if(mode==='free'){
   return modelToggle+uField(kind+'_custom',isLogline?'Sua logline':'Sua storyline',
       u[kind+'_custom'],'Escreva sua própria frase.',5);
 }
 let sentence='';
 if(isLogline){
   sentence='<div class="aest-template-choice" role="group" aria-label="Escolha o modelo">'+
     btn('Modelo 1','sentence-template','data-template="need" aria-pressed="'+(u.logline_template==='need')+'"')+
     btn('Modelo 2','sentence-template','data-template="want" aria-pressed="'+(u.logline_template==='want')+'"')+
     '</div>';
   const a=inlineSlot('logline_actor','Quem é o protagonista?',u.logline_actor,'alguém');
   if(u.logline_template==='want'){
     sentence+='<div class="aest-sentence-form">'+a+' <span>quer</span> '+
       inlineSlot('logline_want','O que deseja?',u.logline_want,'alguma coisa')+
       ' <span>mas</span> '+inlineSlot('logline_block','O que o impede?',u.logline_block,'algo')+
       ' <span>o impede.</span></div>';
   }else{
     sentence+='<div class="aest-sentence-form">'+a+' <span>precisa</span> '+
       inlineSlot('logline_action','O que precisa fazer?',u.logline_action,'fazer algo')+
       ' <span>para</span> '+inlineSlot('logline_goal','Qual é o objetivo?',u.logline_goal,'completar um objetivo')+
       '<span>.</span></div>';
   }
 }else{
   sentence='<div class="aest-sentence-form"><span>Após</span> '+
     inlineSlot('storyline_incident','Acontecimento importante',u.storyline_incident,'um acontecimento importante')+
     '<span>, um</span> '+inlineSlot('storyline_actor','Personagem',u.storyline_actor,'personagem')+
     ' <span>decide</span> '+inlineSlot('storyline_goal','Objetivo',u.storyline_goal,'um objetivo')+
     '<span>, porém ele precisará</span> '+
     inlineSlot('storyline_challenge','Desafios',u.storyline_challenge,'superar desafios')+
     ' <span>porque</span> '+inlineSlot('storyline_stakes','O que está em jogo?',u.storyline_stakes,'há coisas em jogo')+
     '<span>.</span></div>';
 }
 return modelToggle+'<div class="aest-sentence-container"><p>Preencha os campos inseridos na frase:</p>'+
  sentence+'<div class="aest-sentence-result"><strong>Frase resultante</strong>'+
  '<p id="aest-'+kind+'-preview">'+esc(u[kind]||'Preencha todas as lacunas para formar a frase.')+
  '</p></div></div>';
}
function lessonControls(section){
 const lessons=cfg.lessonVideos||{},link=String(lessons[section]||'');
 let result='<div class="aest-lesson-actions">';
 if(cfg.canManageLessons)result+=btn('▶ Vídeo da aula','lesson-edit','data-section="'+section+'"');
 if(link)result+='<a class="aest-btn aest-lesson-watch" target="_blank" rel="noopener noreferrer" href="'+esc(link)+'">▶ Assista à aula</a>';
 result+='</div>';
 if(cfg.canManageLessons&&lessonEditing===section){
  result+='<form class="aest-lesson-form" data-form="lesson-video" data-section="'+section+'">'+
     '<label>Endereço da aula (YouTube ou Hotmart)</label>'+
     '<input name="url" type="url" maxlength="2048" placeholder="https://..." value="'+esc(link)+'">'+
     '<div class="aest-u-actions"><button type="submit" class="aest-btn aest-primary">Salvar vídeo</button>'+
     btn('Cancelar','lesson-cancel')+
     (link?btn('Remover link','lesson-remove','data-section="'+section+'"'):'')+'</div></form>';
 }
 return result;
}
function unlockStatus(msg,isError=false){
 const el=$('#aest-unlock-status');
 if(el){el.textContent=msg;el.classList.toggle('is-error',isError)}
}
function uField(name,label,value,placeholder,lines=3,help=''){
 return '<label class="aest-u-label" for="aest-u-'+name+'">'+label+'</label>'+
   (help?'<p class="aest-u-hint">'+help+'</p>':'')+
   '<textarea id="aest-u-'+name+'" class="aest-u-field" data-unlock-field="'+name+
   '" rows="'+lines+'" placeholder="'+esc(placeholder)+'">'+esc(value)+'</textarea>';
}

const conceptOrder=[0,1,3,6,7,8,10];
const conceptLabels=['Mural de ideias','Assunto','Premissa','Logline','Storyline','Tema e tese','Outline'];
let cardDragId=0,columnDragId='',columnOriginalOrder=[],columnEdgeScrolledAt=0,lessonEditing='',cardNotesOpenId=0;
let structureDragId=0,structureDragModel='',structureDragBusy=false;
function boardCols(p){return Array.isArray(p.boardColumns)&&p.boardColumns.length?p.boardColumns:[
 {id:'soltas',name:'Título'},{id:'desenvolvimento',name:'Título'},{id:'trama',name:'Título'}]}
function cardsByColumn(col){
 return (db.cards||[]).filter(c=>c.project===projectId&&c.column===col).sort((a,b)=>a.rank-b.rank||a.id-b.id);
}
function boardCard(c){
 const hasNotes=Boolean(String(c.notes||'').trim());
 return '<article class="aest-mural-card aest-mural-color-'+esc(c.color||'none')+
   '" draggable="true" data-card-id="'+c.id+'">'+
   '<div class="aest-card-firstline">'+
   '<button type="button" class="aest-card-content" data-action="card-notes-open" data-id="'+c.id+'" title="Abrir bloco de notas do cartão" aria-label="Abrir anotações do cartão: '+esc(c.text.slice(0,85))+'">'+
   '<span class="aest-card-summary">'+esc(c.text)+'</span></button>'+
   (hasNotes?'<span class="aest-card-hasnotes" title="Este cartão possui anotações" aria-label="Contém anotações">▤</span>':'')+
   btn('Editar','card-edit','data-id="'+c.id+'"')+'</div></article>';
}
function openCardNotes(id){
 const card=(db.cards||[]).find(c=>c.id===id&&c.project===projectId);
 if(!card)return;
 root.querySelector('.aest-card-notes-overlay')?.remove();
 cardNotesOpenId=id;
 const notes=String(card.notes||'');
 root.insertAdjacentHTML('beforeend',
  '<div class="aest-card-notes-overlay" data-card-notes-backdrop="1">'+
   '<section class="aest-card-notes-dialog" role="dialog" aria-modal="true" aria-labelledby="aest-notes-title">'+
    '<div class="aest-card-notes-header"><h2 id="aest-notes-title">Anotações do cartão</h2>'+
     btn('Fechar ×','card-notes-close','aria-label="Fechar bloco de notas"')+'</div>'+
    '<p class="aest-card-notes-summary">'+esc(card.text)+'</p>'+
    '<form data-form="card-notes" data-id="'+card.id+'">'+
     '<label for="aest-card-notes-text">Suas anotações</label>'+
     '<textarea id="aest-card-notes-text" name="notes" maxlength="30000" placeholder="Escreva aqui informações, referências ou observações relacionadas a este cartão.">'+esc(notes)+'</textarea>'+
     '<div class="aest-card-notes-actions"><span id="aest-card-notes-status" role="status"></span>'+
      '<button type="submit" class="aest-btn aest-primary">Salvar anotações</button></div>'+
    '</form></section></div>');
 const input=root.querySelector('#aest-card-notes-text');
 if(input){input.focus();input.setSelectionRange(input.value.length,input.value.length);}
}
function closeCardNotes(force=false){
 const overlay=root.querySelector('.aest-card-notes-overlay');if(!overlay)return;
 const notes=overlay.querySelector('#aest-card-notes-text')?.value||'';
 const card=(db.cards||[]).find(c=>c.id===cardNotesOpenId);
 if(!force&&card&&notes!==String(card.notes||'')&&!window.confirm('Descartar as alterações não salvas neste bloco de notas?'))return;
 overlay.remove();
 cardNotesOpenId=0;
 const focus=root.querySelector('[data-action="card-notes-open"][data-id="'+(card?.id||'')+'"]');
 focus?.focus();
}

function muralMarkup(p){
 const cols=boardCols(p),u=unlockState(p);
 const old=u.brainstorm.split(/\r?\n/).map(t=>t.trim()).filter(Boolean);
 const zoom=Math.max(50,Math.min(150,Number(p.boardZoom)||100));
 const scale=zoom/100,width=Math.round(380*scale);
 return '<div class="aest-board-tools" aria-label="Ferramentas do mural">'+
  '<div class="aest-board-zoom" aria-label="Tamanho dos cartões">'+
  btn('−','board-zoom','data-change="-10" aria-label="Diminuir cartões e colunas"')+
  '<span class="aest-zoom-value">'+zoom+'%</span>'+
  btn('+','board-zoom','data-change="10" aria-label="Aumentar cartões e colunas"')+
  btn('100%','board-zoom-reset','aria-label="Restaurar tamanho padrão"')+'</div>'+
  btn('+ Nova coluna','column-add','',true)+'</div>'+
 '<div class="aest-mural-help">Cada ideia é um cartão independente. Arraste os cartões para organizá-los e arraste as colunas por qualquer área livre do cabeçalho. A posição muda na tela antes de salvar. A coluna original de trama continua disponível para alimentar a outline.</div>'+
 (old.length&&!p.legacyImported?
   '<div class="aest-mural-import"><span>Você tem '+old.length+' anotações anteriores.</span>'+
   btn('Transformar em cartões','card-import')+'</div>':'')+
 '<div class="aest-mural" style="--aest-column-width:'+width+'px;--aest-mural-scale:'+scale+'">'+cols.map(col=>{
  const cards=cardsByColumn(col.id);
  return '<section class="aest-mural-column" data-column="'+esc(col.id)+'">'+
   '<h3 class="aest-column-header" draggable="true" data-column-drag="'+esc(col.id)+'" tabindex="0" aria-label="Reorganizar coluna '+esc(col.name)+'; arraste ou use Alt e setas" title="Arraste pelo cabeçalho para reorganizar"><span class="aest-column-grip" aria-hidden="true">⠿</span><span class="aest-mural-title">'+esc(col.name)+'</span>'+
   btn('✎','column-edit','data-column="'+esc(col.id)+'" aria-label="Editar título da coluna" title="Renomear coluna"')+
   ' <small>'+cards.length+'</small></h3>'+
   '<div class="aest-mural-drop" data-column="'+esc(col.id)+'">'+cards.map(boardCard).join('')+
   (cards.length?'':'<p class="aest-mural-empty">Solte um cartão aqui.</p>')+'</div>'+
   '<form data-form="card-add" data-column="'+esc(col.id)+'">'+
   '<label class="aest-u-label">Novo cartão</label><textarea name="text" required maxlength="4000" rows="2" placeholder="Ideia, cena, acontecimento, pergunta..."></textarea>'+
   '<button type="submit" class="aest-btn aest-primary">+ Adicionar cartão</button></form></section>'
 }).join('')+'</div>';
}

function columnDomOrder(mural){
 return mural?Array.from(mural.children).filter(el=>el.classList.contains('aest-mural-column')).map(el=>el.dataset.column):[];
}
function clearColumnDragState(restore=false){
 const mural=root.querySelector('.aest-mural');
 if(restore&&mural&&columnOriginalOrder.length){
  for(const id of columnOriginalOrder){
   const el=Array.from(mural.children).find(e=>e.dataset.column===id);
   if(el)mural.appendChild(el);
  }
 }
 columnDragId='';columnOriginalOrder=[];columnEdgeScrolledAt=0;
 root.querySelectorAll('.is-column-dragging,.is-column-target,.is-column-preview').forEach(el=>{
  el.classList.remove('is-column-dragging','is-column-target','is-column-preview');
 });
}
function previewColumnPosition(ev,mural){
 if(!columnDragId||!mural)return;
 const moving=Array.from(mural.children).find(el=>el.dataset.column===columnDragId);
 const target=ev.target.closest('.aest-mural-column');
 if(!moving||!target||target===moving)return;
 const rect=target.getBoundingClientRect();
 const after=ev.clientX>rect.left+rect.width/2;
 const children=Array.from(mural.children);
 const old=children.indexOf(moving),found=children.indexOf(target);
 let index=found+(after?1:0);
 if(old<index)index--;
 if(old===index)return;
 const before=new Map(children.map(el=>[el,el.getBoundingClientRect().left]));
 if(after)mural.insertBefore(moving,target.nextSibling);
 else mural.insertBefore(moving,target);
 moving.classList.add('is-column-preview');
 if(!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)){
  for(const el of Array.from(mural.children)){
   if(el===moving||typeof el.animate!=='function')continue;
   const dx=(before.get(el)??el.getBoundingClientRect().left)-el.getBoundingClientRect().left;
   if(Math.abs(dx)>1)el.animate([{transform:'translateX('+dx+'px)'},{transform:'translateX(0)'}],
     {duration:150,easing:'ease-out'});
  }
 }
}
function scrollMuralDuringColumnDrag(ev,mural){
 if(!mural||typeof ev.clientX!=='number')return;
 const rect=mural.getBoundingClientRect(),now=Date.now();
 if(now-columnEdgeScrolledAt<35||ev.clientX<rect.left||ev.clientX>rect.right)return;
 const step=ev.clientX>rect.right-66?25:ev.clientX<rect.left+66?-25:0;
 if(step){mural.scrollLeft+=step;columnEdgeScrolledAt=now;}
}

async function moveColumn(id,target,after=false){
 const p=findProject();
 if(!p)return;
 const current=boardCols(p).slice();
 if(!current.some(x=>x.id===id)||!current.some(x=>x.id===target)||id===target)return;
 const moving=current.find(x=>x.id===id);
 const sorted=current.filter(x=>x.id!==id);
 const position=sorted.findIndex(x=>x.id===target)+(after?1:0);
 sorted.splice(position,0,moving);
 if(current.every((col,i)=>col.id===sorted[i].id))return;
 p.boardColumns=sorted;
 render();
 try{
   const result=await api('POST','projects/'+p.id+'/columns/reorder',{order:sorted.map(x=>x.id)});
   p.boardColumns=result.columns;
 }catch(e){
   p.boardColumns=current;
   flash='Não foi possível alterar a ordem das colunas: '+e.message;
   render();
 }
}

// Repaint only card lists, keeping forms, zoom, horizontal scroll and other tabs intact.
function refreshMuralCards(){
 const mural=root.querySelector('.aest-mural');
 if(!mural)return false;
 for(const column of mural.querySelectorAll('.aest-mural-column[data-column]')){
  const items=cardsByColumn(column.dataset.column);
  const drop=column.querySelector('.aest-mural-drop');
  const counter=column.querySelector('.aest-column-header small');
  if(drop)drop.innerHTML=items.length?items.map(boardCard).join(''):'<p class="aest-mural-empty">Solte um cartão aqui.</p>';
  if(counter)counter.textContent=String(items.length);
 }
 return true;
}
function cardOrderSnapshot(){
 const p=findProject();return boardCols(p).flatMap(col=>cardsByColumn(col.id).map((c,i)=>({id:c.id,column:col.id,rank:i})));
}
async function cardMove(id,how,destination=null,place=999999){
 const cards=(db.cards||[]).filter(c=>c.project===projectId);
 const c=cards.find(x=>x.id===id);if(!c)return;
 const prev=cards.map(x=>({id:x.id,column:x.column,rank:x.rank}));
 const cols=boardCols(findProject()),src=cardsByColumn(c.column),oldIndex=src.findIndex(x=>x.id===id);
 let newCol=c.column,position=oldIndex;
 if(how==='up')position=Math.max(0,oldIndex-1);
 if(how==='down')position=Math.min(src.length-1,oldIndex+1);
 if(how==='left'||how==='right'){
  const pos=cols.findIndex(x=>x.id===c.column),newIndex=pos+(how==='left'?-1:1);
  if(newIndex<0||newIndex>=cols.length)return;
  newCol=cols[newIndex].id;position=cardsByColumn(newCol).length;
 }
 if(how==='drop'){newCol=destination;position=place;}
 if(!cols.some(x=>x.id===newCol))return;
 const groups={};for(const col of cols)groups[col.id]=cardsByColumn(col.id).filter(x=>x.id!==id);
 groups[newCol].splice(Math.max(0,Math.min(position,groups[newCol].length)),0,c);
 for(const col of cols)groups[col.id].forEach((item,i)=>{item.column=col.id;item.rank=i});
 if(!refreshMuralCards())render();
 try{await api('POST','cards/reorder',{project:projectId,items:cardOrderSnapshot()});}
 catch(e){for(const row of prev){const found=cards.find(x=>x.id===row.id);if(found)Object.assign(found,row)}
  flash='Não foi possível mover o cartão: '+e.message;render();}
}

function renderUnlock(p){
 const u=unlockState(p);
 if(!conceptOrder.includes(u.step))u.step=u.step<=2?1:u.step<=5?3:10;
 const ix=u.step,step=unlockSteps[ix];
 let form='';
 if(ix===0)form=muralMarkup(p);
 if(ix===1)form=uField('pattern','Qual assunto você encontrou?',u.pattern,
     'Ex.: saudade; uma amizade interrompida; uma investigação...',2)+
     uField('sentence','Escreva uma frase sobre esse assunto',u.sentence,
     'Ex.: Um homem encontra uma carta que ficou escondida durante vinte anos.',3)+
     uField('paragraph','Desenvolvimento inicial (opcional)',u.paragraph,
     'Amplie a frase em um parágrafo, descrevendo personagens, acontecimentos e cenário.',6);
 if(ix===2)form=uField('paragraph','Amplie a frase anterior',u.paragraph,
     'Quem poderia estar envolvido? O que aconteceu antes? Que problema pode surgir?',7,
     'Comece pela frase que escreveu e acrescente detalhes. Este parágrafo é um rascunho.');
 if(ix===3)form=uField('premise','Qual é a sua premissa?',u.premise,
     'E se um homem recebesse uma carta escrita por seu pai, falecido há vinte anos?',5,
     'Exemplo da aula: “E se um detetive usasse viagem no tempo para resolver crimes?”')+
     uField('developments','Possibilidades narrativas (opcional)',u.developments,
     'Personagens, acontecimentos e consequências possíveis, uma ideia por linha.',6);
 if(ix===4)form=uField('developments','O que poderia acontecer a partir dessa premissa?',u.developments,
     'Uma consequência ou possibilidade por linha: personagens, obstáculos, lugares, descobertas...',8,
     'Ainda é um brainstorm. Guarde as possibilidades mesmo que sejam provisórias.');
 if(ix===5)form=uField('protagonist','Quem é o protagonista?',u.protagonist,'Ex.: um detetive que investiga um desaparecimento',2)+
     uField('objective','O que ele quer ou precisa conseguir?',u.objective,'Ex.: encontrar a pessoa desaparecida',2)+
     uField('obstacle','O que o impede?',u.obstacle,'Ex.: a única testemunha mente para protegê-la',2);
 if(ix===6)form=(u.premise?'<div class="aest-u-context"><strong>Premissa registrada</strong><p>'+esc(u.premise)+'</p></div>':'')+
   uField('protagonist','Protagonista',u.protagonist,'Quem conduz a história?',2)+
   uField('objective','Objetivo',u.objective,'O que o protagonista quer alcançar?',2)+
   uField('obstacle','Impedimento / conflito principal',u.obstacle,'O que impede o protagonista?',2)+
   sentenceEditor(u,'logline');
 if(ix===7)form=uField('turning','Primeiro acontecimento decisivo / ponto de virada',u.turning,
    'Que acontecimento altera a situação inicial?',3)+sentenceEditor(u,'storyline');
 if(ix===8)form=uField('theme','Tema central',u.theme,'Ex.: confiança; culpa; memória...',2)+
     uField('thesis','Tese ou ideia que deseja desenvolver',u.thesis,'Ex.: a verdade sobre o passado altera as relações do presente.',3)+
     uField('tone','Tom da narrativa (opcional)',u.tone,'Ex.: melancólico, tenso, irônico...',2);
 if(ix===9)form=uField('summary','Resumo da história',u.summary,
     'Conte em um parágrafo o que acontece do início ao desfecho.',6)+
     uField('events','Acontecimentos importantes (um por linha)',u.events,
     '1. O protagonista recebe uma carta\n2. Ele procura uma testemunha\n3. Descobre uma mentira\n4. Enfrenta as consequências...',8);
 if(ix===10)form=(cardsByColumn('trama').length?
     '<div class="aest-mural-import"><span>Há '+cardsByColumn('trama').length+' cartões na coluna “Na trama”.</span>'+
     btn('Inserir cartões na outline','outline-from-cards')+'</div>':'')+
     uField('summary','1. Resumo geral da história (opcional)',u.summary,
     'Registre o rumo da história.',4)+
     uField('events','2. Tópicos: uma frase por acontecimento',u.events,
     'Anote os momentos importantes.',5)+
     uField('expanded_topics','3. Um parágrafo para cada tópico',u.expanded_topics,
     'Descreva brevemente o que acontece em cada ponto. Utilize as perguntas sobre protagonistas, causas e consequências.',7)+
     uField('outline','Outline: ordem de leitura da história',u.outline||u.events,
     'Organize os tópicos na sequência escolhida.',8)+
     uField('questions_outline','4. Perguntas-guia dos capítulos (Módulo 2, aula 9)',u.questions_outline,
     'Ex.: O que leva o protagonista a procurar a testemunha? Uma pergunta por capítulo.',6);
 const stage=ix===0?1:ix===1?2:3;
 const stageLabel=ix===0?'Mural de ideias':ix===1?'Assunto e pesquisa':'Desenvolvimento da ideia de história';
 return '<section class="aest-u-flow '+(ix===0?'aest-mural-screen':'')+'" aria-label="Ferramentas do projeto">'+
 '<p class="aest-stage-caption">ETAPA '+stage+' DE 4 · '+stageLabel+'</p>'+
   '<nav class="aest-concept-nav" aria-label="Ferramentas de concepção">'+
   conceptOrder.map((stepIndex,i)=>'<button type="button" data-action="concept-jump" data-step="'+stepIndex+
     '" class="'+(ix===stepIndex?'selected':'')+'" aria-current="'+(ix===stepIndex?'page':'false')+'">'+conceptLabels[i]+'</button>').join('')+
   '</nav>'+
   '<div class="aest-section-heading"><h1>'+esc(ix===0?'Mural de ideias':ix===1?'Escolha um assunto':ix===3?'Premissa':
      ix===6?'Logline':ix===7?'Storyline':ix===8?'Tema e tese':'Outline')+'</h1>'+
   lessonControls(['mural','assunto','premissa','logline','storyline','tema','outline'][conceptOrder.indexOf(ix)])+'</div>'+
   (ix===0?'':'<p class="aest-u-intro">'+esc(step[2])+'</p>')+
   '<div class="aest-u-paper">'+form+
   '<div class="aest-u-actions">'+btn('Salvar alterações','concept-save','',ix!==10)+
    (ix!==10?btn(ix===0?'Continuar: escolher um assunto →':ix===1?'Continuar: desenvolver uma ideia de história →':'Próxima seção →','unlock-next'):
      btn('Continuar: trabalhar no manuscrito →','tab','data-tab="manuscrito"',true))+
   '</div><p class="aest-u-status" id="aest-unlock-status" role="status">Salvamento automático ativado.</p></div>'+
   (ix===10?'<section class="aest-next-stage"><strong>Use o planejamento durante a escrita</strong>'+
    '<p>Fichas, modelos narrativos e capítulos compartilham o mesmo projeto. Voc? pode revis?-los em qualquer ordem.</p>'+
    '<div class="aest-u-actions">'+btn('Cadastrar elementos','tab','data-tab="elementos"')+
    btn('Organizar estrutura','tab','data-tab="estrutura"')+btn('Escrever capítulos','tab','data-tab="manuscrito"',true)+'</div></section>':'')+
   '<div class="aest-u-course">Mural de fichas: Módulo 2, aula 4. Conceito narrativo: Módulo 2, aula 8.</div></section>';
}
function unlockCheck(u) {
 const req=[
  ['brainstorm','Registre ideias no mural de cartões.'],
  ['pattern','Escreva o assunto que você encontrou.'],
  ['paragraph','Amplie sua frase em um parágrafo.'],
  ['premise','Escreva a premissa da história.'],
  ['developments','Anote pelo menos uma possibilidade narrativa.'],
  ['protagonist','Identifique o protagonista.'],
  ['logline','Escreva a logline.'],
  ['turning','Registre o acontecimento decisivo.'],
  ['theme','Registre o tema central.'],
  ['summary','Escreva um resumo da história.'],
  ['outline','Organize os acontecimentos na outline.']
 ];
 const ix=u.step;
 if(!String(u[req[ix][0]]||'').trim())return req[ix][1];
 if(ix===1&&!u.sentence.trim())return 'Escreva uma frase sobre o assunto.';
 if(ix===5&&(!u.objective.trim()||!u.obstacle.trim()))return 'Registre o objetivo e o obstáculo do protagonista.';
 if(ix===7&&!u.storyline.trim())return 'Escreva a storyline.';
 if(ix===8&&!u.thesis.trim())return 'Registre sua tese.';
 if(ix===9&&!u.events.trim())return 'Anote os acontecimentos da história.';
 return '';
}
function unlockFlagChanged(){
 unlockDirty=true;
 unlockStatus('Salvando…');
 clearTimeout(unlockTimer);
 unlockTimer=setTimeout(()=>saveUnlock().catch(e=>unlockStatus(e.message,true)),800);
}
async function saveUnlock(complete=false){
 clearTimeout(unlockTimer);
 if(unlockBusy){
  try{await unlockBusy}catch(e){if(complete)throw e}
 }
 if(!unlockDirty&&!complete)return true;
 const p=findProject();
 if(!p||p.start==='manuscrito')return false;
 const data=JSON.parse(JSON.stringify(unlockState(p)));
 unlockDirty=false;
 unlockBusy=api('POST','projects/'+p.id+'/unlock',{state:data,complete});
 try{
  const result=await unlockBusy;
  p.unlock.revision=result.state.revision;
  p.unlock.completed=result.state.completed;
  if(result.concept)Object.assign(p,result.concept);
  unlockStatus('Salvo automaticamente');
  return true;
 }catch(e){
  unlockDirty=true;unlockStatus('Erro ao salvar: '+e.message,true);throw e;
 }finally{
  unlockBusy=null;
  if(unlockDirty&&!complete){
   clearTimeout(unlockTimer);
   unlockTimer=setTimeout(()=>saveUnlock().catch(e=>unlockStatus(e.message,true)),1800);
  }
 }
}


const elementCategories=['Personagens','Lugares','Cidades','Povos','Famílias','Organizações','Criaturas','Objetos','Eventos','Religiões','Idiomas','Tecnologias','Regras do mundo'];
// Cada ficha tem campos pertinentes ? sua categoria e relações por IDs imutáveis.
const elementDetails={
 personagens:[['funcao','Função narrativa'],['objetivo','Objetivo'],['motivacao','Motivação'],['conflito','Conflito'],['arco','Arco do personagem'],['aparencia','Aparência e marcas'],['voz','Voz e linguagem'],['primeira_aparicao','Primeira aparição']],
 lugares:[['tipo','Tipo de lugar'],['descricao','Ambiente e características'],['funcao','Função na trama'],['regras','Regras ou restrições']],
 cidades:[['regiao','Região'],['organizacao','Organização'],['historia','História'],['lugares','Locais importantes']],
 povos:[['origem','Origem'],['costumes','Costumes'],['valores','Valores'],['conflitos','Conflitos e relações']],
 familias:[['origem','Origem'],['membros','Membros'],['relacoes','Relações'],['conflitos','Conflitos']],
 organizacoes:[['objetivo','Objetivo'],['integrantes','Integrantes'],['hierarquia','Hierarquia'],['conflitos','Conflitos']],
 criaturas:[['origem','Origem'],['caracteristicas','Características'],['comportamento','Comportamento'],['regras','Regras']],
 objetos:[['origem','Origem'],['propriedades','Propriedades'],['posse','Posse'],['funcao','Função na trama']],
 eventos:[['causa','Causa'],['consequencia','Consequências'],['envolvidos','Envolvidos'],['local','Local']],
 religioes:[['crencas','Crenças'],['praticas','Práticas'],['organizacao','Organização'],['influencia','Influência na história']],
 idiomas:[['origem','Origem'],['falantes','Falantes'],['caracteristicas','Características']],
 tecnologias:[['uso','Uso'],['limites','Limitações'],['impactos','Consequências']],
 regras_do_mundo:[['regra','Regra'],['condicoes','Condições'],['excecoes','Exceções'],['consequencias','Consequências']]
};
function elementCategoryKey(folderName){
 return String(folderName||'').toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
}
function elementSchema(folder){
 return elementDetails[elementCategoryKey(folder.name)]||[['funcao','Função na história'],['origem','Origem'],['caracteristicas','Características']];
}
function elementAttrFields(folder,item={}){
 const attrs=item.attrs||{};
 return '<details class="aest-element-details" '+(Object.values(attrs).some(v=>String(v).trim())?'open':'')+'><summary>Ficha detalhada</summary>'+
  '<div class="aest-element-fields">'+elementSchema(folder).map(([key,label])=>
   '<label>'+esc(label)+'<textarea name="attr_'+key+'" rows="2" maxlength="5000" placeholder="'+esc(label)+'">'+esc(attrs[key]||'')+'</textarea></label>').join('')+'</div></details>';
}
function elementLinkFields(folders,selected=[],selfId=''){
 const list=folders.flatMap(folder=>(folder.items||[]).filter(item=>item.id!==selfId).map(item=>({item,folder})));
 return '<details class="aest-element-details" '+(selected.length?'open':'')+'><summary>Relações com outros elementos'+(selected.length?' ('+selected.length+')':'')+'</summary>'+
  (list.length?'<div class="aest-element-relations">'+list.map(({item,folder})=>
   '<label><input type="checkbox" name="links" value="'+esc(item.id)+'" '+(selected.includes(item.id)?'checked':'')+'>'+
   '<span>'+esc(item.title)+' <small>'+esc(folder.name)+'</small></span></label>').join('')+'</div>':
   '<p class="aest-muted">Cadastre outro elemento para estabelecer relações.</p>')+'</details>';
}
function renderElements(){
 const p=findProject(),folders=Array.isArray(p?.elements?.folders)?p.elements.folders:[];
 const options=elementCategories.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('');
 const folderCreator='<details class="aest-el-new-folder"><summary>+ Nova pasta</summary>'+
 '<form data-form="element-folder-add" class="aest-element-create">'+
 '<label for="aest-element-category">Categoria</label><select name="category" id="aest-element-category" required>'+
 '<option value="" selected disabled>Selecione a categoria</option>'+options+
 '<option value="_custom" style="background-color:#d9eee9;color:#065e56;font-weight:700">+ Categoria personalizada</option></select>'+
 '<input type="text" name="custom" class="aest-element-custom" maxlength="65" placeholder="Nome da categoria" aria-label="Nome personalizado" hidden disabled>'+
 '<button class="aest-btn aest-primary" type="submit">Criar pasta</button></form></details>';
 const sections=folders.map(folder=>{
  const items=Array.isArray(folder.items)?folder.items:[];
  const heading='<header class="aest-element-heading"><div><h3>'+esc(folder.name)+'</h3><small>'+items.length+' elemento'+(items.length===1?'':'s')+'</small></div>'+
   btn('?','element-folder-rename','data-folder="'+esc(folder.id)+'" title="Renomear pasta" aria-label="Renomear pasta"')+'</header>';
  const rename=editingElementFolder===folder.id?'<form data-form="element-folder-rename" data-folder="'+esc(folder.id)+'" class="aest-element-rename">'+
   '<input name="name" type="text" maxlength="65" required value="'+esc(folder.name)+'" aria-label="Nome da pasta">'+
   '<button class="aest-btn aest-primary" type="submit">Salvar</button></form>':'';
  const rows=items.length?'<div class="aest-element-list">'+items.map(item=>{
   const outward=(item.links||[]).map(id=>folders.flatMap(f=>(f.items||[]).map(i=>({i,f}))).find(x=>x.i.id===id)).filter(Boolean);
   const inward=folders.flatMap(f=>(f.items||[]).filter(i=>(i.links||[]).includes(item.id)).map(i=>({i,f})));
   return '<details class="aest-element-item"><summary><span>'+esc(item.title)+'</span><span aria-hidden="true">?</span></summary>'+
    '<form data-form="element-item-update" data-folder="'+esc(folder.id)+'" data-item="'+esc(item.id)+'">'+
    '<label>Nome<input name="title" type="text" maxlength="140" value="'+esc(item.title)+'" required></label>'+
    '<label>Descrição e anotações<textarea name="notes" rows="4" maxlength="20000">'+esc(item.notes||'')+'</textarea></label>'+
    elementAttrFields(folder,item)+elementLinkFields(folders,item.links||[],item.id)+
    (outward.length?'<p class="aest-element-related">Relacionados: '+outward.map(x=>esc(x.i.title)).join(', ')+'</p>':'')+
    (inward.length?'<p class="aest-element-related">Citado em: '+inward.map(x=>esc(x.i.title)).join(', ')+'</p>':'')+
    '<button class="aest-btn aest-primary" type="submit">Salvar ficha</button></form></details>';
  }).join('')+'</div>':'<p class="aest-elements-empty">Esta pasta ainda est? vazia.</p>';
  const add='<details class="aest-el-new-item"><summary>+ Novo elemento</summary>'+
   '<form class="aest-element-add" data-form="element-item-add" data-folder="'+esc(folder.id)+'">'+
   '<label>Nome<input name="title" type="text" maxlength="140" required placeholder="Nome do elemento"></label>'+
   '<label>Descrição e anotações<textarea name="notes" rows="3" maxlength="20000" placeholder="Características, função narrativa e observações..."></textarea></label>'+
   elementAttrFields(folder)+elementLinkFields(folders)+
   '<button class="aest-btn aest-primary" type="submit">Salvar elemento</button></form></details>';
  return '<section class="aest-element-folder">'+heading+rename+rows+add+'</section>';
 }).join('');
 return '<div class="aest-elements"><header class="aest-section-bar"><div><h2>Elementos da história</h2>'+
  '<p class="aest-muted">Cadastre personagens, lugares, cidades, povos, regras e outros elementos. Abra uma ficha para registrar detalhes e estabelecer relações.</p></div>'+btn('Hist?rico das fichas','element-history-open')+folderCreator+'</header>'+
  (folders.length?'<div class="aest-element-grid">'+sections+'</div>':'<div class="aest-empty">Crie uma pasta para começar a cadastrar os elementos da história.</div>')+'</div>';
}

function elementHistoryDialog(rows){
 root.querySelector('.aest-review-overlay')?.remove();
 const overlay=document.createElement('div');overlay.className='aest-review-overlay';
 overlay.innerHTML='<div class="aest-review-modal" role="dialog" aria-modal="true" aria-label="Hist?rico de fichas">'+
 '<header><h3>Hist?rico de fichas</h3>'+btn('Fechar','element-history-close')+'</header>'+
 '<p class="aest-muted">Guarde uma vers?o de suas pastas e fichas. Restaurar recupera os campos e relacionamentos e preserva o estado anterior.</p>'+
 btn('Guardar vers?o atual','element-history-save')+
 '<div class="aest-element-history-list">'+(rows.length?rows.map(row=>
  '<div class="aest-review-version-row"><span>'+esc(row.created)+' ? '+row.folders+' pasta(s), '+row.elements+' ficha(s) ('+esc(row.source)+')</span>'+
  btn('Restaurar','element-history-restore','data-version="'+esc(row.id)+'"')+'</div>').join(''):
  '<p class="aest-muted">Nenhuma vers?o guardada.</p>')+'</div></div>';
 root.appendChild(overlay);
}
const structureModels={
 three_acts:{title:'Três atos',stages:[
 ['ato1','Ato I','Apresentação, situação inicial e primeira virada.'],
 ['ato2','Ato II','Desenvolvimento, obstáculos e mudança da situação.'],
 ['ato3','Ato III','Clímax, consequências e resolução.']]},
 hero_journey:{title:'Jornada do herói',stages:[
 ['mundo_comum','Mundo comum','Situação inicial.'],
 ['chamado','Chamado à aventura','Acontecimento que convoca a personagem.'],
 ['recusa','Recusa do chamado','Resistência ao novo percurso.'],
 ['mentor','Encontro com o mentor','Informações, recursos ou orientação.'],
 ['limiar','Travessia do limiar','Entrada na nova situação.'],
 ['provas','Provas, aliados e inimigos','Conflitos e relações.'],
 ['aproximacao','Aproximação','Preparação para o confronto.'],
 ['provacao','Provação suprema','Confronto principal.'],
 ['recompensa','Recompensa','Resultado da provação.'],
 ['retorno','Caminho de volta','Desdobramentos e nova pressão.'],
 ['ressurreicao','Ressurreição','Teste final.'],
 ['elixir','Retorno com o elixir','Encerramento e resultado.']]}
};
const chapterStage=(c,model)=>c?.structure?.positions?.[model]||'';
const stageTitle=(model,stage)=>structureModels[model]?.stages.find(x=>x[0]===stage)?.[1]||'Sem posição';
function renderStructure(){
 const chrono=structureSection==='cronologia',journey=structureSection==='jornada';
 const model=journey?'hero_journey':'three_acts',schema=structureModels[model],cs=projectChapters();
 const nav='<nav class="aest-structure-nav" aria-label="Modelo estrutural">'+
 [['atos','Três atos'],['jornada','Jornada do herói'],['cronologia','Cronologia']].map(x=>
 '<button type="button" data-action="structure-section" data-section="'+x[0]+'" aria-pressed="'+(structureSection===x[0])+'">'+x[1]+'</button>').join('')+'</nav>';
 const header='<header class="aest-section-head"><h2>Estrutura da história</h2>'+
 '<p class="aest-muted">Distribua os capítulos pelos pontos estruturais. O mesmo capítulo permanece em Manuscrito, com seu texto e título originais.</p></header>';
 if(chrono)return '<div class="aest-structure">'+header+nav+
 '<div class="aest-empty"><h3>Cronologia</h3><p>Esta área reunirá as datas e a duração dos acontecimentos. Consulte a ordem dos cap\u00edtulos em Manuscrito e os v\u00ednculos estruturais em Tr\u00eas atos e Jornada do her\u00f3i.</p></div></div>';
 const stages=schema.stages.map(([id,title,desc],i)=>{
   const attached=cs.filter(c=>chapterStage(c,model)===id);
   const available=cs.filter(c=>chapterStage(c,model)!==id);
   const list=attached.length?'<ul class="aest-stage-chapters">'+attached.map(c=>
    '<li class="aest-stage-draggable" draggable="true" data-structure-chapter="'+c.id+'" data-model="'+model+'" title="Arraste para outra etapa"><span class="aest-stage-grip" aria-hidden="true">&#8942;&#8942;</span><span class="aest-stage-number">'+(cs.indexOf(c)+1)+'</span><span class="aest-stage-chapter-name">'+esc(c.title)+'</span>'+
    btn('Abrir','open-chapter','data-id="'+c.id+'"')+btn('Desvincular','structure-unlink','data-id="'+c.id+'" data-model="'+model+'"')+'</li>').join('')+'</ul>':
    '<div class="aest-stage-empty">Nenhum capítulo associado.</div>';
   const link=available.length?'<form class="aest-stage-attach" data-form="structure-chapter-link" data-model="'+model+'" data-stage="'+id+'">'+
    '<label>Vincular capítulo existente</label><div><select name="chapter" required aria-label="Escolher capítulo">'+
    '<option value="" disabled selected>Selecione o capítulo</option>'+
    available.map(c=>'<option value="'+c.id+'">'+esc(c.title)+'</option>').join('')+'</select>'+
    '<button type="submit" class="aest-btn">Vincular</button></div></form>':'';
   const create='<form class="aest-stage-create" data-form="structure-chapter-create" data-model="'+model+'" data-stage="'+id+'">'+
    '<label>Ou criar um capítulo neste ponto</label><div><input name="title" type="text" maxlength="140" required placeholder="Título do capítulo">'+
    '<button type="submit" class="aest-btn aest-primary">+ Criar</button></div></form>';
   return '<section class="aest-stage-card aest-structure-dropzone" data-drop-model="'+model+'" data-drop-stage="'+id+'"><header class="aest-stage-head"><span class="aest-stage-index">'+String(i+1).padStart(2,'0')+'</span>'+
    '<div><h3>'+esc(title)+'</h3><p>'+esc(desc)+'</p></div><small>'+attached.length+'</small></header>'+
    list+'<div class="aest-stage-drop-hint" aria-hidden="true">Solte o cap\u00edtulo nesta etapa</div><details class="aest-stage-tools"><summary>+ Adicionar capítulo</summary>'+link+create+'</details></section>';
 }).join('');
 const unassigned=cs.filter(c=>!chapterStage(c,model));
 const note='<aside class="aest-stage-unassigned aest-structure-dropzone" data-drop-model="'+model+'" data-drop-stage="">'+
 '<strong>Cap\u00edtulos dispon\u00edveis ('+unassigned.length+')</strong>'+
 '<p>Arraste um cap\u00edtulo para a etapa desejada. Arraste-o de volta para c\u00e1 para retirar a associa\u00e7\u00e3o.</p>'+
 '<div class="aest-stage-pool" role="list">'+(unassigned.length?unassigned.map(c=>
 '<div role="listitem" draggable="true" class="aest-stage-pool-chip" data-structure-chapter="'+c.id+'" data-model="'+model+'" title="Arraste para uma etapa"><span aria-hidden="true">&#8942;&#8942;</span> '+esc(c.title)+'</div>').join(''):'<small>Todos os cap\u00edtulos j\u00e1 est\u00e3o associados a uma etapa deste modelo.</small>')+'</div>'+
 '<div class="aest-stage-drop-hint" aria-hidden="true">Solte aqui para desvincular</div>'+
 '<small>Voc\u00ea tamb\u00e9m pode usar "+ Adicionar cap\u00edtulo" em cada etapa.</small></aside>';
 return '<div class="aest-structure">'+header+nav+note+'<div class="aest-structure-acts">'+stages+'</div></div>';
}
function renderAnalyses(){
 return '<section class="aest-analyses">'+
  '<h2>An\u00e1lises</h2>'+
  '<p class="aest-muted">Esta aba receber\u00e1 os gr\u00e1ficos de tens\u00e3o, ritmo e distribui\u00e7\u00e3o das marca\u00e7\u00f5es narrativas. As informa\u00e7\u00f5es do manuscrito e da estrutura permanecem preservadas.</p>'+
  '</section>';
}

const reviewTypes=[['trama','Trama'],['personagem','Personagem'],['narrador','Narrador'],['descricao','Descrição'],['dialogo','Diálogo'],['tensao','Tensão'],['concisa','Concisão'],['causalidade','Causalidade'],['conhecimento','Conhecimento'],['continuidade','Continuidade'],['elementos','Elementos recorrentes'],['outro','Outro']];
let reviewVersionChapter=0,reviewVersionCache=[];
function reviewState(p){if(!p.review)p.review={revision:0,tasks:[],checklist:{}};return p.review}
function reviewOptions(){return reviewTypes.map(([key,label])=>'<option value="'+key+'">'+esc(label)+'</option>').join('')}
function renderReview(){
 const p=findProject(),rev=reviewState(p),cs=projectChapters(),open=rev.tasks.filter(t=>t.status!=='resolvida').length;
 const checklist=reviewTypes.filter(x=>x[0]!=='outro').map(([key,label])=>
  '<label><input type="checkbox" data-review-check="'+key+'" '+(rev.checklist[key]?'checked':'')+'>'+esc(label)+'</label>').join('');
 const tasks=rev.tasks.map(t=>{
  const chapter=cs.find(c=>c.id===t.chapter),done=t.status==='resolvida';
  return '<article class="aest-review-task '+(done?'is-reviewed':'')+'"><div class="aest-review-task-top"><strong>'+esc(reviewTypes.find(x=>x[0]===t.type)?.[1]||'Revisão')+'</strong><small>'+esc(t.priority)+' ? '+esc(chapter?.title||'Projeto inteiro')+'</small></div>'+
   (t.quote?'<blockquote>'+esc(t.quote)+'</blockquote>':'')+'<p>'+esc(t.note)+'</p>'+
   btn(done?'Reabrir':'Marcar resolvida','review-status','data-id="'+esc(t.id)+'" data-status="'+(done?'aberta':'resolvida')+'"')+
   (chapter?btn('Abrir capítulo','open-chapter','data-id="'+chapter.id+'"'):'')+'</article>';
 }).join('');
 return '<div class="aest-review"><h2>Revisão</h2><p class="aest-muted">Confira as técnicas, registre pendências e comentários ligados a trechos e recupere versões anteriores dos capítulos.</p>'+
 '<p class="aest-review-count"><strong>'+open+'</strong> pendências abertas</p>'+
 '<section class="aest-review-box"><h3>Conferência por técnica</h3><div class="aest-review-checklist">'+checklist+'</div></section>'+
 '<section class="aest-review-box"><h3>Nova pendência</h3><form data-form="review-task-add" class="aest-review-form">'+
 '<label>Capítulo<select name="chapter"><option value="0">Projeto inteiro</option>'+cs.map(c=>'<option value="'+c.id+'">'+esc(c.title)+'</option>').join('')+'</select></label>'+
 '<label>Técnica<select name="type">'+reviewOptions()+'</select></label>'+
 '<label>Prioridade<select name="priority"><option value="normal">Normal</option><option value="alta">Alta</option><option value="baixa">Baixa</option></select></label>'+
 '<label class="aest-review-full">Observação<textarea name="note" maxlength="5000" rows="3" required></textarea></label>'+
 '<button type="submit" class="aest-btn aest-primary">Salvar pendência</button></form></section>'+
 '<section class="aest-review-box"><h3>Pendências ('+rev.tasks.length+')</h3>'+(tasks||'<p class="aest-muted">Nenhuma pendência registrada.</p>')+'</section>'+
 '<section class="aest-review-box"><h3>Histórico de versões</h3><p class="aest-muted">Guarde versões e compare o texto atual com estados anteriores. Antes de restaurar, o estado atual ser? preservado.</p>'+
 (cs.length?'<div class="aest-review-version-controls"><select id="aest-review-chapter">'+cs.map(c=>'<option value="'+c.id+'" '+((reviewVersionChapter||cs[0].id)===c.id?'selected':'')+'>'+esc(c.title)+'</option>').join('')+'</select>'+
 btn('Consultar versões','review-version-list')+btn('Guardar versão atual','review-version-save')+'</div><div id="aest-review-version-list" aria-live="polite">Selecione o capítulo.</div>':
 '<p>Crie primeiro um capítulo.</p>')+'</section></div>';
}
function reviewQuoteDialog(quote,offset){
 root.querySelector('.aest-review-overlay')?.remove();
 const overlay=document.createElement('div');overlay.className='aest-review-overlay';
 overlay.innerHTML='<div class="aest-review-modal" role="dialog" aria-modal="true" aria-label="Comentar trecho"><header><h3>Comentar trecho</h3>'+btn('Fechar','review-close')+'</header><blockquote>'+esc(quote)+'</blockquote>'+
 '<form data-form="review-quote-add" data-offset="'+offset+'"><input type="hidden" name="quote" value="'+esc(quote)+'">'+
 '<label>Técnica<select name="type">'+reviewOptions()+'</select></label>'+
 '<label>Prioridade<select name="priority"><option value="normal">Normal</option><option value="alta">Alta</option><option value="baixa">Baixa</option></select></label>'+
 '<label>Comentário<textarea name="note" rows="3" maxlength="5000" required></textarea></label>'+
 '<button class="aest-btn aest-primary" type="submit">Salvar comentário</button></form></div>';
 root.appendChild(overlay);overlay.querySelector('textarea')?.focus();
}
async function reviewVersionList(id){
 const result=await api('GET','chapters/'+id+'/versions');reviewVersionChapter=id;reviewVersionCache=result.versions||[];
 const target=$('#aest-review-version-list');if(!target)return;
 target.innerHTML=reviewVersionCache.length?reviewVersionCache.map(v=>
 '<div class="aest-review-version-row"><span>'+esc(v.created)+' ? '+esc(v.title)+' ('+esc(v.source)+')</span>'+btn('Comparar','review-version-compare','data-version="'+esc(v.id)+'"')+'</div>').join(''):
 '<p class="aest-muted">Nenhuma versão disponível. Use Guardar versão atual.</p>';
}
function reviewCompareDialog(version,chapter){
 const text=d=>(d?.ops||[]).map(op=>typeof op.insert==='string'?op.insert:' ').join('');
 root.querySelector('.aest-review-overlay')?.remove();
 const overlay=document.createElement('div');overlay.className='aest-review-overlay';
 overlay.innerHTML='<div class="aest-review-modal aest-review-compare" role="dialog" aria-modal="true" aria-label="Comparar versões"><header><h3>Comparar ? '+esc(chapter.title)+'</h3>'+btn('Fechar','review-close')+'</header>'+
 '<div class="aest-review-diff"><section><h4>Versão de '+esc(version.created)+'</h4><pre>'+esc(text(version.delta))+'</pre></section><section><h4>Atual</h4><pre>'+esc(text(chapter.delta))+'</pre></section></div>'+
 btn('Restaurar esta versão','review-version-restore','data-version="'+esc(version.id)+'"')+'</div>';
 root.appendChild(overlay);
}

function renderProject(){
 const p=findProject();if(!p){view='projetos';return renderProjects()}
 const crumb='<nav class="aest-project-breadcrumb" aria-label="Localização no projeto">'+
 '<button type="button" data-action="nav" data-view="projetos">Meus projetos</button>'+
 '<span aria-hidden="true">›</span><strong>'+esc(p.title)+'</strong>'+
 '<button type="button" class="aest-switch-project" data-action="nav" data-view="projetos">Trocar projeto</button></nav>';
 const top='<div class="aest-project-top"><div class="aest-project-identity"><h1 id="aest-project-title">'+esc(p.title)+'</h1><span class="aest-pill">Privado</span></div>'+btn('Editar nome','rename-project')+(tab==='planejamento'&&p.start!=='manuscrito'?'':btn('Excluir projeto','delete-project','data-id="'+p.id+'"'))+'</div>';
 let body='';
 if(tab==='visao'){
  const cs=projectChapters(),wc=cs.reduce((sum,c)=>sum+words(c.delta),0);
  body=(p.start!=='manuscrito'&&!p.unlock.completed?'<div class="aest-unlock-resume"><strong>Sua história ainda está nas primeiras ideias.</strong>'+btn('Continuar desbloqueio criativo →','unlock-resume')+'</div>':'')+'<h2>Seu projeto</h2><div class="aest-stats"><div class="aest-stat"><strong>'+cs.length+'</strong><span>Capítulos</span></div><div class="aest-stat"><strong>'+wc.toLocaleString('pt-BR')+'</strong><span>Palavras</span></div><div class="aest-stat"><strong>'+projectNotes().length+'</strong><span>Anotações</span></div></div><div class="aest-sub-actions">'+btn('Planejar a história','tab','data-tab="planejamento"',true)+btn('Abrir manuscrito','tab','data-tab="manuscrito"')+btn('Registrar pesquisa','tab','data-tab="pesquisa"')+'</div>';
 }else if(tab==='elementos'){body=renderElements();}
 else if(tab==='estrutura'){body=renderStructure();}
 else if(tab==='pesquisa'){
  body='<h2>Pesquisa</h2><p class="aest-muted">Anote informações, perguntas e referências que podem ajudar a construir sua história.</p>'+noteForm('research',p.id,'O que você precisa investigar? Registre fontes e observações aqui.')+'<h3 class="aest-section-heading">Anotações de pesquisa</h3>'+noteList(projectNotes('research'));
 }else if(tab==='planejamento'){
  if(p.start!=='manuscrito'&&!unlockShowPlanning){body=renderUnlock(p);}
  else {
  const exploration=p.start!=='manuscrito'&&!(p.unlock&&p.unlock.completed)?'<h2>Encontre sua primeira ideia</h2><p class="aest-muted">Comece registrando uma observação, uma pergunta ou uma situação que desperte sua curiosidade. Você pode desenvolver a premissa depois.</p>'+noteForm('idea',p.id,'O que você observou ou gostaria de explorar em uma história?')+'<h3 class="aest-section-heading">Ideias registradas</h3>'+noteList(projectNotes('idea'))+'<hr style="margin:30px 0;border:0;border-top:1px solid #dce5e7">':'';
  const conceptOverview=p.start!=='manuscrito'&&p.unlock&&p.unlock.completed?
    '<div class="aest-u-summary"><div><strong>Premissa</strong><p>'+esc(p.premise||p.unlock.premise)+'</p></div>'+
    '<div><strong>Logline</strong><p>'+esc(p.logline||p.unlock.logline)+'</p></div>'+
    '<div><strong>Storyline</strong><p>'+esc(p.storyline||p.unlock.storyline)+'</p></div>'+
    '<div><strong>Tema</strong><p>'+esc(p.theme||p.unlock.theme)+'</p></div>'+
    '<div><strong>Tese</strong><p>'+esc(p.thesis||p.unlock.thesis)+'</p></div>'+
    '<div><strong>Outline</strong><p>'+esc(p.outline||p.unlock.outline)+'</p></div></div>':'';
  const conceptFields=[
   ['topic','Assunto','Qual assunto ser? explorado?'],
   ['premise','Premissa','E se...? Qual ? a hipótese narrativa?'],
   ['logline','Logline','Quem age, qual ? o objetivo e qual ? o obst?culo?'],
   ['storyline','Storyline','Que acontecimento decisivo modifica a situação e que consequências surgem?'],
   ['theme','Tema','Assunto central da história.'],
   ['thesis','Tese','Ideia desenvolvida pelos acontecimentos.'],
   ['tone','Tom','Ex.: tenso, melancólico, cômico...'],
   ['summary','Resumo','Amplie a storyline em um parágrafo.'],
   ['outline','Outline','Organize os acontecimentos na ordem da leitura.']
  ];
  body=conceptOverview+exploration+'<h2>Concepção da história</h2><p class="aest-muted">Módulo 2, aulas 4, 8 e 9. Registre suas decisões e consulte Elementos e Estrutura durante a redação. Os campos permanecem editáveis.</p>'+
   '<form class="aest-form aest-concept-direct" data-form="project">'+conceptFields.map(([key,label,hint])=>
    '<label for="aest-concept-'+key+'">'+esc(label)+'</label><textarea id="aest-concept-'+key+'" name="'+key+'" placeholder="'+esc(hint)+'">'+esc(p[key]||'')+'</textarea>').join('')+
   '<div class="aest-form-footer"><button class="aest-btn aest-primary" type="submit">Salvar planejamento</button></div></form>'+
   '<div class="aest-sub-actions">'+btn('Guardar uma ideia','nav','data-view="ideias"')+
   btn('Elementos','tab','data-tab="elementos"')+btn('Estrutura','tab','data-tab="estrutura"')+
   btn('Manuscrito','tab','data-tab="manuscrito"')+'</div>';
  }
 }else if(tab==='manuscrito'){body=renderManuscript();}
 else if(tab==='analises'){body=renderAnalyses();
 }else if(tab==='revisao'){body=renderReview();
 }else if(tab==='publicacao'){
  body='<h2>Publicação</h2><div class="aest-empty"><strong>Este projeto é privado.</strong><p>Seus capítulos e notas estão acessíveis somente à sua conta. A integração com os projetos públicos das homes do Anthares será disponibilizada após os testes de permissões.</p></div>';
 }
 return crumb+top+projectTabs()+planningSubnav()+body;
}
function renderManuscript(){
 const cs=projectChapters();
 if(chapterId && cs.some(c=>c.id===chapterId))return editorMarkup(cs.find(c=>c.id===chapterId));
 chapterId=0;
 return '<div class="aest-row"><div><h2>Capítulos</h2><p class="aest-muted">Arraste os capítulos pelo cabeçalho para alterar a ordem de leitura. A mesma ordem ? utilizada nos modelos da aba Estrutura.</p></div>'+
 btn('+ Novo capítulo','new-chapter','',true)+'<label class="aest-btn" style="cursor:pointer">Importar TXT<input id="aest-import" type="file" accept=".txt,.md,text/plain" hidden></label></div>'+
 (cs.length?'<div class="aest-list aest-chapter-sort-list" aria-label="Capítulos na ordem de leitura">'+cs.map((c,i)=>
 '<div class="aest-list-row aest-chapter-sort" draggable="true" data-chapter-sort="'+c.id+'" title="Arraste para reorganizar"><div><strong><span class="aest-chapter-grip" aria-hidden="true">?</span> '+(i+1)+'. '+esc(c.title)+'</strong><div class="aest-hint">'+words(c.delta)+' palavras ? '+esc(stageTitle('three_acts',chapterStage(c,'three_acts')))+' ? '+esc(stageTitle('hero_journey',chapterStage(c,'hero_journey')))+'</div></div>'+
 btn('Estrutura','chapter-structure')+btn('Escrever ?','open-chapter','data-id="'+c.id+'"')+btn('Excluir','trash-item','data-id="'+c.id+'"')+'</div>').join('')+'</div>':
 '<div class="aest-empty">Seu manuscrito ainda não tem capítulos. Crie o primeiro para começar a escrever.</div>');
}
function editorMarkup(c){
 const damaged=(c.delta?.ops||[]).some(op=>typeof op.insert==='string'&&op.insert.includes('\uFFFD'));
 const repairAction=damaged?'<label class="aest-btn aest-reimport-action" title="Corrigir acentos usando o arquivo TXT original">Corrigir acentos · Reimportar TXT<input id="aest-reimport" type="file" accept=".txt,.md,text/plain" hidden></label>':'';
 const repairNotice=damaged?
  '<aside class="aest-repair-notice" role="status"><span><strong>Este capítulo contém caracteres ilegíveis.</strong> Para recuperar os acentos, selecione o TXT original. A versão atual ficará preservada.</span><label for="aest-reimport" class="aest-repair-trigger">Selecionar TXT original</label></aside>':'';
 return '<div class="aest-crumb"><button data-action="back-chapters">‹ Todos os capítulos</button></div>'+
 '<div class="aest-editor-head"><input id="aest-chapter-title" class="aest-input" value="'+esc(c.title)+'" aria-label="Título do capítulo" maxlength="140">'+btn('Salvar','save-chapter','',true)+repairAction+'</div>'+
 repairNotice+
 '<div id="aest-toolbar" aria-label="Ferramentas de formatação"><button class="ql-bold" title="Negrito" aria-label="Negrito"></button><button class="ql-italic" title="Itálico" aria-label="Itálico"></button><button class="ql-underline" title="Sublinhado" aria-label="Sublinhado"></button><button class="ql-list" value="ordered" aria-label="Lista numerada"></button><button class="ql-list" value="bullet" aria-label="Lista com marcadores"></button><button type="button" data-action="mark-pista" class="aest-mark" title="Selecione um trecho do manuscrito e clique para destacar ou retirar uma pista narrativa" aria-label="Destacar ou retirar marca\u00e7\u00e3o de pista no trecho selecionado">Marcar pista</button><button type="button" class="aest-mark" data-action="review-quote" title="Selecione um trecho para comentar">Comentar trecho</button></div>'+
 '<div id="aest-quill" aria-label="Texto do capítulo"></div><div class="aest-editor-meta"><span id="aest-wordcount">'+words(c.delta)+' palavras</span><span id="aest-save-status" role="status">Salvo</span></div>';
}
function render(){
 cardNotesOpenId=0;
 root.innerHTML='<div class="aest-layout">'+sidebar()+'<main class="aest-main" id="aest-content">'+notice()+
 (view==='inicio'?(db.projects.length?renderHome():renderStart()):view==='novo'?('<h1>Começar um projeto</h1><p class="aest-lead">Escolha de onde quer partir.</p>'+startCards()):view==='projetos'?renderProjects():view==='ideias'?renderIdeas():view==='lixeira'?renderTrash():view==='ajuda'?renderHelp():view==='projeto'?renderProject():renderStart())+
 '</main></div>';
 if(view==='projeto'&&tab==='manuscrito'&&chapterId)setupEditor();
 syncRouteOnRender();
}
function renderHome(){
 // O menu Início preserva a mesma orientação para escritores novos e experientes.
 // Projetos existentes acrescentam só um acesso de retomada, sem substituir os quatro cartões.
 const p=db.projects[0];
 if(!p)return renderStart();
 const u=p.unlock||{},cs=db.chapters.filter(c=>c.project===p.id).sort((a,b)=>b.id-a.id);
 let status='Projeto privado';
 if(p.start!=='manuscrito'&&!u.completed){
   const s=Number(u.step)||0;
   status='Etapa '+(s===0?1:s===1?2:3)+' de 4 · '+(s===0?'Mural de ideias':s===1?'Assunto':'Desenvolvimento da história');
 }else if(cs.length){
   status='Último capítulo: '+cs[0].title;
 }else if(p.premise){
   status='Premissa registrada';
 }else if(p.start!=='manuscrito'&&u.completed){
   status='Desbloqueio criativo concluído';
 }else{
   status='Em planejamento';
 }
 return renderStart()+
  '<section class="aest-home-resume" aria-label="Projeto em andamento">'+
   '<div class="aest-home-resume-copy"><span>CONTINUAR DE ONDE PAROU</span>'+
   '<strong>'+esc(p.title)+'</strong><small>'+esc(status)+'</small></div>'+
   btn('Continuar projeto →','open-project','data-id="'+p.id+'"',true)+
  '</section>'+
  (db.projects.length>1?
    '<div class="aest-home-extra">'+btn('Ver todos os projetos ('+db.projects.length+')','nav','data-view="projetos"')+'</div>':'');
}
let quillLoading = null;
function loadQuill(){
 if(window.Quill)return Promise.resolve();
 if(quillLoading)return quillLoading;
 quillLoading=new Promise((resolve,reject)=>{
  if(!document.querySelector('[data-aest-quill-css]')){
   const link=document.createElement('link');
   link.rel='stylesheet';link.href=cfg.quillCss;link.dataset.aestQuillCss='1';
   document.head.appendChild(link);
  }
  const script=document.createElement('script');
  script.src=cfg.quillJs;script.async=true;
  const timer=setTimeout(()=>reject(new Error('O editor demorou para carregar.')),12000);
  script.onload=()=>{clearTimeout(timer);window.Quill?resolve():reject(new Error('Editor indisponível.'))};
  script.onerror=()=>{clearTimeout(timer);reject(new Error('Falha ao carregar o editor.'))};
  document.head.appendChild(script);
 });
 return quillLoading;
}
async function setupEditor(){
 const c=findChapter(),id=chapterId;
 if(!c || !$('#aest-quill'))return;
 editor=null;dirty=false;lastRange=null;
 if(!window.Quill){
  const status=$('#aest-save-status');
  if(status)status.textContent='Preparando editor…';
  try{await loadQuill()}catch(e){quillLoading=null}
 }
 if(view!=='projeto'||tab!=='manuscrito'||chapterId!==id||!$('#aest-quill'))return;
 if(window.Quill){
  if(!window.aestPistaRegistered){
   const Inline=Quill.import('blots/inline');
   class Pista extends Inline{}
   Pista.blotName='aestPista';Pista.tagName='MARK';Pista.className='aest-pista';
   Quill.register(Pista,true);window.aestPistaRegistered=true;
  }
  editor=new Quill('#aest-quill',{theme:'snow',modules:{toolbar:'#aest-toolbar'},placeholder:'Comece a escrever seu capítulo…'});
  try{editor.setContents(c.delta,'silent')}catch(e){editor.setText('','silent')}
  editor.on('selection-change',range=>{if(range)lastRange=range});
  editor.on('text-change',()=>{dirty=true;updateWordCount();queueSave()});
  const status=$('#aest-save-status');if(status)status.textContent='Salvo';
 }else{
  $('#aest-quill').innerHTML='<textarea id="aest-fallback" aria-label="Texto do capítulo" placeholder="Escreva o capítulo…">'+esc((c.delta.ops||[]).map(o=>typeof o.insert==='string'?o.insert:'').join(''))+'</textarea>';
  $('#aest-fallback').addEventListener('input',()=>{dirty=true;updateWordCount();queueSave()});
  const mark=$('[data-action="mark-pista"]');if(mark)mark.hidden=true;
  $('#aest-save-status').textContent='Editor básico disponível';
 }
 $('#aest-chapter-title').addEventListener('input',()=>{dirty=true;queueSave()});
 updateWordCount();
}
function editorDelta(){if(editor)return editor.getContents();const t=$('#aest-fallback');return{ops:[{insert:(t?t.value:'').replace(/\n?$/,'\n')}]} }
function updateWordCount(){const el=$('#aest-wordcount');if(el)el.textContent=words(editorDelta())+' palavras';}
function queueSave(){clearTimeout(saveTimer);const el=$('#aest-save-status');if(el)el.textContent='Alterações pendentes…';saveTimer=setTimeout(()=>saveChapter(),1200)}
async function saveChapter(){
 if(!chapterId||view!=='projeto'||tab!=='manuscrito')return;
 if(saveBusy){savePending=true;return true}
 if(!dirty)return;
 clearTimeout(saveTimer);saveBusy=true;savePending=false;
 const id=chapterId,delta=editorDelta(),title=$('#aest-chapter-title')?$('#aest-chapter-title').value:'';
 dirty=false;const status=$('#aest-save-status');if(status)status.textContent='Salvando…';
 let savedOk=false;
 try{
  const chapter=db.chapters.find(c=>c.id===id);
   if(!chapter||!/^[a-f0-9]{64}$/.test(chapter.contentHash||''))throw Error('Reabra o capítulo para confirmar a versão antes de salvar.');
   const confirmed=await api('POST','chapters/'+id,{delta,title,expected_hash:chapter.contentHash});
  if(!confirmed||confirmed.ok!==true||!/^[a-f0-9]{64}$/.test(confirmed.contentHash||''))throw Error('O servidor não confirmou o salvamento.');
  const c=db.chapters.find(x=>x.id===id);if(c){c.delta=delta;c.title=title||c.title;c.contentHash=confirmed.contentHash;c.modified=confirmed.modified||c.modified;}
  if(status&&chapterId===id)status.textContent='Salvo automaticamente';
  savedOk=true;
 }catch(e){
  dirty=true;
  if(status)status.textContent='Falha ao salvar: '+e.message+' Corrija ou clique Salvar para tentar novamente.';
 }
 saveBusy=false;
 if(savedOk&&savePending){savePending=false;queueSave();}
 else savePending=false;
 return savedOk;
}
async function navigate(newView,newTab,newId){
 if(dirty&&chapterId){
   const ok=await saveChapter();
   if(ok===false)return;
 }
 if(unlockDirty && view==='projeto')await saveUnlock();
 if(unlockBusy)await unlockBusy;
 if(newView==='ideias')await ensureFullData();
 if(newView==='projeto')await ensureFullData(newId||projectId);
 view=newView;chapterId=0;unlockEditing=false;unlockShowPlanning=false;
 if(newTab){if(newTab==='estrutura'&&tab!=='estrutura')structureSection='atos';tab=newTab;}if(newId)projectId=newId;
 flash='';render();window.scrollTo({top:0,behavior:'instant'});
}
async function createProject(mode){
 const created=await api('POST','projects',{mode});
 db.projects.unshift({id:created.id,title:'Projeto sem título',created:new Date().toISOString().slice(0,10),
   start:mode,topic:'',premise:'',visibility:'private',unlock:{revision:0,step:mode==='assunto'?1:mode==='ideia'?3:0,version:2,completed:false},
   boardColumns:[{id:'soltas',name:'Título'},{id:'desenvolvimento',name:'Título'},{id:'trama',name:'Título'}]});
 projectId=created.id;chapterId=0;
 await reload(created.id);
 tab=(mode==='manuscrito'?'manuscrito':'planejamento');
 view='projeto';unlockEditing=false;unlockShowPlanning=false;flash='Seu projeto privado foi criado e salvo.';render();
}
root.addEventListener('mousedown',ev=>{
 if(editor&&ev.target.closest('[data-action="mark-pista"],[data-action="review-quote"]'))ev.preventDefault();
});
root.addEventListener('click',async ev=>{
 const b=ev.target.closest('[data-action]');if(!b)return;
 const action=b.dataset.action;
 if(action==='theme-toggle'){
  const next=themeMode==='dark'?'light':'dark';
  applyTheme(next);
  try{window.localStorage.setItem(themeStorageKey,next);}catch(_){}
  b.innerHTML='<span aria-hidden="true">'+(next==='dark'?'☼':'☾')+'</span>'+(next==='dark'?'Modo claro':'Modo escuro');
  b.setAttribute('aria-pressed',String(next==='dark'));
  return;
 }
 try{
  b.disabled=true;
  if(action==='card-notes-open'){
    openCardNotes(Number(b.dataset.id));return;
  }
  if(action==='card-notes-close'){
    closeCardNotes();return;
  }
  if(action==='project-color-menu'){
    const tile=b.closest('.aest-project-tile');
    if(!tile)return;
    const panel=tile.querySelector('.aest-project-color-palette');
    const wasClosed=panel?.hidden;
    root.querySelectorAll('.aest-project-tile.is-color-open').forEach(other=>{
     other.classList.remove('is-color-open');
     const previous=other.querySelector('.aest-project-color-palette');
     if(previous)previous.hidden=true;
     other.querySelector('.aest-project-color-trigger')?.setAttribute('aria-expanded','false');
    });
    if(panel){
     panel.hidden=!wasClosed;
     tile.classList.toggle('is-color-open',wasClosed);
     b.setAttribute('aria-expanded',String(wasClosed));
     if(wasClosed)panel.querySelector('button')?.focus();
    }
    return;
  }
  if(action==='project-color'){
    const p=db.projects.find(x=>x.id===Number(b.dataset.id));
    const tile=b.closest('.aest-project-tile');
    if(!p||!tile)return;
    const valid=['none','sea','blue','violet','rose','amber','forest','slate'];
    const tone=b.dataset.tone;
    if(!valid.includes(tone))return;
    const previous=p.color||'none';
    p.color=tone;
    tile.dataset.tone=tone;
    const palette=tile.querySelector('.aest-project-color-palette');
    tile.querySelectorAll('.aest-project-color-swatch').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.tone===tone)));
    if(palette)palette.hidden=true;
    tile.classList.remove('is-color-open');
    tile.querySelector('.aest-project-color-trigger')?.setAttribute('aria-expanded','false');
    try{
     const result=await api('POST','projects/'+p.id,{color:tone});
     if(!result?.ok||result.color!==tone)throw Error('A cor escolhida n\u00e3o foi confirmada.');
    }catch(error){
     p.color=previous;tile.dataset.tone=previous;
     tile.querySelectorAll('.aest-project-color-swatch').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.tone===previous)));
     throw error;
    }
    return;
  }

  if(action==='element-history-close'){root.querySelector('.aest-review-overlay')?.remove();return;}
  if(action==='element-history-open'){
   const p=findProject();if(!p)return;
   const result=await api('GET','projects/'+p.id+'/elements/versions');
   elementHistoryDialog(result.versions||[]);return;
  }
  if(action==='element-history-save'){
   const p=findProject();if(!p)return;
   const result=await api('POST','projects/'+p.id+'/elements/versions',{action:'snapshot'});
   if(!result?.ok)throw Error('A vers?o das fichas n?o foi confirmada.');
   elementHistoryDialog(result.versions||[]);return;
  }
  if(action==='element-history-restore'){
   const p=findProject();if(!p)return;
   if(!window.confirm('Restaurar esta vers?o das fichas? O estado atual ser? guardado antes da recupera??o.'))return;
   const result=await api('POST','projects/'+p.id+'/elements/versions',{
    action:'restore',version:b.dataset.version,revision:Number(p.elements?.revision||0)});
   if(!result?.ok||!result.elements)throw Error('A restaura??o das fichas n?o foi confirmada.');
   p.elements=result.elements;root.querySelector('.aest-review-overlay')?.remove();
   flash='Fichas restauradas. Uma c?pia do estado anterior foi guardada.';render();return;
  }
  if(action==='review-close'){root.querySelector('.aest-review-overlay')?.remove();return;}
  if(action==='review-quote'){
   const status=$('#aest-save-status'),range=editor?.getSelection()||lastRange;
   if(!editor||!range?.length){
    if(status)status.textContent='Selecione uma passagem do texto antes de comentar.';
    return;
   }
   const quote=editor.getText(range.index,Math.min(range.length,600)).trim();
   if(!quote){if(status)status.textContent='Selecione um trecho com palavras.';return;}
   reviewQuoteDialog(quote,range.index);
   return;
  }
  if(action==='review-status'){
   const p=findProject();if(!p)return;
   const review=reviewState(p);
   const result=await api('POST','projects/'+p.id+'/review',{revision:review.revision,
    action:'status',item:b.dataset.id,status:b.dataset.status});
   if(!result.ok)throw Error('Atualização não confirmada.');
   p.review=result.review;render();return;
  }
  if(action==='review-version-list'||action==='review-version-save'){
   const id=Number($('#aest-review-chapter')?.value);
   if(!db.chapters.some(c=>c.project===projectId&&c.id===id))throw Error('Escolha um capítulo deste projeto.');
   if(action==='review-version-save'){
    const result=await api('POST','chapters/'+id+'/versions',{action:'snapshot'});
    if(!result.ok)throw Error('O servidor não confirmou a versão.');
   }
   await reviewVersionList(id);return;
  }
  if(action==='review-version-compare'){
   const id=reviewVersionChapter,chapter=db.chapters.find(c=>c.id===id&&c.project===projectId);
   if(!chapter)throw Error('Selecione um capítulo.');
   const result=await api('GET','chapters/'+id+'/versions?version='+encodeURIComponent(b.dataset.version));
   if(!result?.version)throw Error('Versão não encontrada.');
   reviewCompareDialog(result.version,chapter);return;
  }
  if(action==='review-version-restore'){
   const id=reviewVersionChapter;
   if(!window.confirm('Restaurar esta versão do capítulo? O estado atual ser? guardado antes da restauração.'))return;
   const c=db.chapters.find(x=>x.id===id&&x.project===projectId);
    if(!c||!/^[a-f0-9]{64}$/.test(c.contentHash||''))throw Error('Reabra o capítulo antes de restaurar a versão.');
    const result=await api('POST','chapters/'+id+'/versions',{action:'restore',version:b.dataset.version,expected_hash:c.contentHash});
   if(!result?.ok||!result.chapter)throw Error('Restauração não confirmada.');
   const ix=db.chapters.findIndex(c=>c.id===id);
   if(ix>=0)db.chapters[ix]=result.chapter;
   root.querySelector('.aest-review-overlay')?.remove();
   flash='Versão restaurada. O estado anterior foi guardado no histórico.';
   render();await reviewVersionList(id);return;
  }
  if(action==='nav'){
    if(b.dataset.view==='ideias')await ensureFullData();
    if(b.dataset.view==='lixeira')await fetchTrash();
    await navigate(b.dataset.view);
  }
  else if(action==='trash-refresh'){await fetchTrash();render();}
  else if(action==='trash-restore'){
    const t=trashItems.find(x=>x.id===Number(b.dataset.id));if(!t)return;
    if(t.cascade&&trashItems.some(x=>x.id===t.project&&x.type==='anst_projeto'))
      throw Error('Restaure primeiro o projeto que contém este material.');
    await api('POST','trash/'+t.id+'/restore',{});
    await fetchTrash();await reload();
    flash='Item restaurado com sucesso.';render();
  }else if(action==='trash-permanent'){
    const t=trashItems.find(x=>x.id===Number(b.dataset.id));if(!t)return;
    if(!window.confirm('Excluir DEFINITIVAMENTE "'+t.title+'"? Esta operação é irreversível.'))return;
    await api('DELETE','trash/'+t.id,{confirm_title:t.title});
    await fetchTrash();await reload();
    flash='Item excluído definitivamente.';render();
  }else if(action==='trash-item'){
    const id=Number(b.dataset.id);
    if(!window.confirm('Enviar este item para a Lixeira por até 7 dias?'))return;
    await api('DELETE','items/'+id,{});
    db.notes=db.notes.filter(x=>x.id!==id);
    db.chapters=db.chapters.filter(x=>x.id!==id);
    db.cards=db.cards.filter(x=>x.id!==id);
    if(chapterId===id)chapterId=0;
    flash='Item enviado à Lixeira.';render();
  }
  else if(action==='structure-section'){structureSection=['atos','jornada','cronologia'].includes(b.dataset.section)?b.dataset.section:'atos';render();}
  else if(action==='element-folder-rename'){editingElementFolder=b.dataset.folder||'';render();}
  else if(action==='start')await createProject(b.dataset.mode);
  else if(action==='open-project'){
    const wanted=Number(b.dataset.id);await ensureFullData(wanted);
    const p=db.projects.find(x=>x.id===wanted);
    if(!p)throw Error('Projeto indisponível.');
    await navigate('projeto',p.start==='manuscrito'?'manuscrito':'planejamento',wanted);
  }
  else if(action==='unlock-resume'){
    const p=findProject();if(!p)return;
    await ensureFullData(p.id);
    unlockEditing=false;unlockShowPlanning=false;
    await navigate('projeto','planejamento');
  }
  else if(action==='tab')await navigate('projeto',b.dataset.tab);
  else if(action==='unlock-edit'){unlockEditing=true;unlockShowPlanning=false;render()}
  else if(action==='unlock-to-plan'){unlockShowPlanning=true;unlockEditing=false;render()}
  else if(action==='concept-jump'||action==='unlock-next'){
    const u=unlockState(findProject());
    const old=conceptOrder.indexOf(u.step),next=action==='concept-jump'?Number(b.dataset.step):
      conceptOrder[Math.min(conceptOrder.length-1,old+1)];
    if(!conceptOrder.includes(next))return;
    u.step=next;unlockDirty=true;
    render();
    saveUnlock().catch(e=>unlockStatus('Falha ao salvar: '+e.message,true));
  }else if(action==='concept-save'){
    unlockDirty=true;await saveUnlock();unlockStatus('Alterações salvas.');
  }else if(action==='board-zoom'||action==='board-zoom-reset'){
    const p=findProject();if(!p)return;
    const old=Number(p.boardZoom)||100;
    const val=action==='board-zoom-reset'?100:Math.max(50,Math.min(150,old+Number(b.dataset.change||0)));
    if(val===old)return;
    p.boardZoom=val;render();
    try{await api('POST','projects/'+p.id+'/zoom',{zoom:val});}
    catch(e){p.boardZoom=old;flash='Falha ao salvar tamanho: '+e.message;render();}
  }else if(action==='column-add'){
    const out=await api('POST','projects/'+projectId+'/columns',{name:'Título'});
    const p=findProject();if(p)p.boardColumns=out.columns;
    render();const mural=$('.aest-mural');if(mural)mural.scrollLeft=mural.scrollWidth;
  }else if(action==='column-edit'){
    const p=findProject(),col=boardCols(p).find(x=>x.id===b.dataset.column);
    if(!col)return;
    const el=Array.from(root.querySelectorAll('.aest-mural-column')).find(x=>x.dataset.column===col.id);
    const h=el?.querySelector('h3');if(!h)return;
    h.innerHTML='<form data-form="column-rename" data-column="'+esc(col.id)+'" class="aest-rename-column">'+
      '<input name="name" type="text" maxlength="40" required aria-label="Título da coluna" value="'+esc(col.name)+'">'+
      '<button type="submit" class="aest-btn aest-primary" aria-label="Salvar título">✓</button>'+
      btn('✕','column-cancel','aria-label="Cancelar alteração"')+'</form>';
    h.querySelector('input')?.focus();
  }else if(action==='column-cancel'){render()}
  else if(action==='lesson-edit'){
    if(!cfg.canManageLessons)return;
    lessonEditing=lessonEditing===b.dataset.section?'':b.dataset.section;render();
  }else if(action==='lesson-cancel'){lessonEditing='';render()}
  else if(action==='lesson-remove'){
    if(!cfg.canManageLessons)return;
    if(!window.confirm('Remover o vídeo desta seção para todos os alunos?'))return;
    const out=await api('POST','lesson/'+b.dataset.section,{url:''});
    cfg.lessonVideos=out.videos;lessonEditing='';render();
  }else if(action==='sentence-mode'){
    const u=unlockState(findProject()),kind=b.dataset.kind,mode=b.dataset.mode;
    if(!['logline','storyline'].includes(kind)||!['template','free'].includes(mode))return;
    if(mode==='free'&&!u[kind+'_custom'])u[kind+'_custom']=u[kind]||'';
    u[kind+'_mode']=mode;syncNarrativeText(u,kind);
    unlockFlagChanged();render();
  }else if(action==='sentence-template'){
    const u=unlockState(findProject()),which=b.dataset.template;
    if(!['need','want'].includes(which))return;
    u.logline_template=which;syncNarrativeText(u,'logline');
    unlockFlagChanged();render();
  }else if(action==='card-import'){
    const result=await api('POST','projects/'+projectId+'/import-ideas',{});
    await reload();
    flash=result.imported?'Anotações transformadas em '+result.imported+' cartões.':'Importação já realizada.';
    render();
  }else if(action==='card-edit'){
    const c=(db.cards||[]).find(x=>x.id===Number(b.dataset.id)&&x.project===projectId);
    if(!c)return;
    const el=root.querySelector('[data-card-id="'+c.id+'"]');
    if(!el)return;
    el.innerHTML='<form class="aest-mural-edit" data-form="card-edit" data-id="'+c.id+'">'+
      '<label>Texto do cartão</label><textarea name="text" required maxlength="4000">'+esc(c.text)+'</textarea>'+
      '<label>Cor</label><select name="color">'+
      [['none','Sem cor'],['yellow','Amarelo'],['blue','Azul'],['green','Verde'],['pink','Rosa']].map(x=>
        '<option value="'+x[0]+'" '+((c.color||'none')===x[0]?'selected':'')+'>'+x[1]+'</option>').join('')+
      '</select><button class="aest-btn aest-primary" type="submit">Salvar</button>'+
      btn('Cancelar','card-cancel')+btn('Excluir cartão','card-delete','data-id="'+c.id+'"')+'</form>';
  }else if(action==='card-cancel'){render()}
  else if(action==='card-delete'){
    const id=Number(b.dataset.id);
    if(!window.confirm('Excluir este cartão?'))return;
    await api('DELETE','cards/'+id);
    db.cards=db.cards.filter(x=>x.id!==id);render();
  }else if(action==='card-move'){
    await cardMove(Number(b.dataset.id),b.dataset.dir);
  }
  else if(action==='delete-project'){
    const id=Number(b.dataset.id),p=db.projects.find(x=>x.id===id);
    if(!p)return;
    if(!window.confirm('Excluir o projeto "'+p.title+'" com seus capítulos, cartões e anotações? Os dados serão movidos para a lixeira.'))return;
    const result=await api('DELETE','projects/'+id,{title:p.title});
    if(!result.ok)throw Error('Exclusão não confirmada.');
    db.projects=db.projects.filter(x=>x.id!==id);
    db.cards=(db.cards||[]).filter(x=>x.project!==id);
    db.chapters=db.chapters.filter(x=>x.project!==id);
    db.notes=db.notes.filter(x=>x.project!==id);
    projectId=0;view='projetos';tab='visao';flash='Projeto movido para a lixeira.';render();
  }
  else if(action==='outline-from-cards'){
    const u=unlockState(findProject()),items=cardsByColumn('trama');
    if(!items.length)throw Error('Coloque alguns cartões na coluna Na trama.');
    const next=items.map(c=>c.text).join('\n');
    if(u.outline&&u.outline.trim()!==next&&!window.confirm('Substituir a outline atual pelo conteúdo dos cartões da coluna Na trama?'))return;
    u.outline=next;unlockDirty=true;render();
    saveUnlock().catch(e=>unlockStatus('Falha ao salvar: '+e.message,true));
  }
  else if(action==='structure-unlink'){
    const id=Number(b.dataset.id),model=b.dataset.model;
    const chapter=db.chapters.find(c=>c.id===id&&c.project===projectId);
    if(!chapter||!['three_acts','hero_journey'].includes(model))throw Error('Cap\u00edtulo ou modelo indisponível.');
    const result=await api('POST','chapters/'+id+'/structure',{model,stage:'',revision:Number(chapter.structure?.revision||0)});
    if(!result?.ok||!result.structure||result.structure.positions?.[model]!=='')
      throw Error('A retirada da associa\u00e7\u00e3o não foi confirmada.');
    chapter.structure=result.structure;
    flash='Cap\u00edtulo desvinculado desta etapa. O manuscrito foi preservado.';
    render();
  }
  else if(action==='chapter-structure'){tab='estrutura';structureSection='atos';chapterId=0;render();window.scrollTo({top:0,behavior:'instant'});}
  else if(action==='new-chapter'){
   const c=await api('POST','chapters',{project:projectId});
   if(c?.chapter&&c.chapter.id===Number(c.id))db.chapters.push(c.chapter);
   else await reload();
   chapterId=Number(c.id);render();
   window.scrollTo({top:0,behavior:'instant'});
  }else if(action==='open-chapter'){
   tab='manuscrito';chapterId=Number(b.dataset.id);render();window.scrollTo({top:0,behavior:'instant'});
  }
  else if(action==='back-chapters'){
   await saveChapter();chapterId=0;render();window.scrollTo({top:0,behavior:'instant'});
  }
  else if(action==='save-chapter'){dirty=true;await saveChapter()}
  else if(action==='mark-pista'){
   const status=$('#aest-save-status');
   if(!editor){
    if(status)status.textContent='Editor de marca\u00e7\u00f5es indispon\u00edvel neste modo.';
   }else{
    const range=editor.getSelection()||lastRange;
    if(!range||!range.length){
     if(status)status.textContent='Selecione primeiro uma palavra ou trecho do manuscrito. Depois clique em Marcar pista.';
    }else{
     const isMarked=!!editor.getFormat(range.index,range.length).aestPista;
     editor.formatText(range.index,range.length,'aestPista',!isMarked,'user');
     editor.setSelection(range.index,range.length,'silent');
     lastRange=range;
     dirty=true;
     queueSave();
     if(status)status.textContent=isMarked?'Marca\u00e7\u00e3o retirada. Salvamento autom\u00e1tico ativado.':'Pista destacada. Salvamento autom\u00e1tico ativado.';
    }
   }
  }else if(action==='rename-project'){
   const p=findProject();if(!p)return;
   const existing=$('#aest-rename-inline');
   if(existing){existing.focus();existing.select();return;}
   const title=$('#aest-project-title');if(!title)return;
   title.outerHTML='<form data-form="rename" class="aest-inline-rename" aria-label="Editar nome do projeto">'+
    '<input id="aest-rename-inline" name="title" class="aest-inline-rename-input" aria-label="Nome do projeto" required maxlength="140" value="'+esc(p.title)+'">'+
    '<button type="submit" class="aest-btn aest-primary">Salvar</button>'+btn('Cancelar','cancel-rename')+'</form>';
   const input=$('#aest-rename-inline');if(input){input.focus();input.select();}
  }else if(action==='cancel-rename'){render()}

 }catch(e){flash='Erro: '+e.message;render()}finally{if(b.isConnected)b.disabled=false}
});
root.addEventListener('click',ev=>{
 if(!ev.target.closest('.aest-project-color-controls')){
  root.querySelectorAll('.aest-project-tile.is-color-open').forEach(tile=>{
   tile.classList.remove('is-color-open');
   const picker=tile.querySelector('.aest-project-color-palette');if(picker)picker.hidden=true;
   tile.querySelector('.aest-project-color-trigger')?.setAttribute('aria-expanded','false');
  });
 }
 if(ev.target.matches('[data-card-notes-backdrop]'))closeCardNotes();
 const openFolder=root.querySelector('.aest-el-new-folder[open]');
 if(openFolder&&!openFolder.contains(ev.target))openFolder.open=false;
});
let manuscriptDragId=0;
function resetStructureDrag(){
 structureDragId=0;structureDragModel='';
 root.querySelectorAll('.is-structure-dragging,.is-structure-over,.is-structure-saving').forEach(el=>
  el.classList.remove('is-structure-dragging','is-structure-over','is-structure-saving'));
 root.querySelector('.aest-structure')?.classList.remove('is-structure-active');
}
root.addEventListener('pointerdown',ev=>{
 const h=ev.target.closest('.aest-column-header');
 if(h&&ev.target.closest('button,a,input,textarea,select,form'))h.draggable=false;
});
root.addEventListener('pointerup',()=>{
 root.querySelectorAll('.aest-column-header').forEach(h=>{h.draggable=true;});
});
root.addEventListener('pointercancel',()=>{
 root.querySelectorAll('.aest-column-header').forEach(h=>{h.draggable=true;});
});
root.addEventListener('dragstart',ev=>{
 const sort=ev.target.closest('[data-chapter-sort]');
 if(sort&&tab==='manuscrito'&&!chapterId){
  if(ev.target.closest('button,a,input,textarea,select,form')){ev.preventDefault();return;}
  manuscriptDragId=Number(sort.dataset.chapterSort);
  sort.classList.add('is-dragging');
  if(ev.dataTransfer){ev.dataTransfer.effectAllowed='move';ev.dataTransfer.setData('text/plain','anthares-sort:'+manuscriptDragId);}
  return;
 }
 const chapterEl=ev.target.closest('[data-structure-chapter]');
 if(chapterEl){
  if(ev.target.closest('button,a,input,textarea,select,form')||structureDragBusy){ev.preventDefault();return;}
  const id=Number(chapterEl.dataset.structureChapter),model=chapterEl.dataset.model;
  if(tab!=='estrutura'||!['three_acts','hero_journey'].includes(model)||!db.chapters.some(c=>c.project===projectId&&c.id===id)){ev.preventDefault();return;}
  structureDragId=id;structureDragModel=model;cardDragId=0;columnDragId='';
  chapterEl.classList.add('is-structure-dragging');
  root.querySelector('.aest-structure')?.classList.add('is-structure-active');
  if(ev.dataTransfer){ev.dataTransfer.effectAllowed='move';ev.dataTransfer.setData('text/plain','anthares-chapter:'+id);}
  return;
 }
 if(ev.target.closest('.aest-card-content')||ev.target.closest('.aest-card-notes-overlay')){
  ev.preventDefault();return;
 }
 const grip=ev.target.closest('[data-column-drag]');
 if(grip){
   if(ev.target.closest('button,input,textarea,form,select,a')||grip.draggable===false){
     ev.preventDefault();return;
   }
   columnDragId=grip.dataset.columnDrag;
   const mural=grip.closest('.aest-mural');
   columnOriginalOrder=columnDomOrder(mural);
   cardDragId=0;
   const column=grip.closest('.aest-mural-column');
   if(column)column.classList.add('is-column-dragging','is-column-preview');
   if(ev.dataTransfer){ev.dataTransfer.effectAllowed='move';ev.dataTransfer.setData('text/plain','column:'+columnDragId);}
   return;
 }
 const el=ev.target.closest('[data-card-id]');if(!el)return;
 cardDragId=Number(el.dataset.cardId);
 if(ev.dataTransfer){ev.dataTransfer.effectAllowed='move';ev.dataTransfer.setData('text/plain',String(cardDragId))}
 el.classList.add('is-dragging');
});
root.addEventListener('dragend',ev=>{
 manuscriptDragId=0;
 root.querySelectorAll('.aest-chapter-sort.is-sort-target').forEach(el=>el.classList.remove('is-sort-target'));
 resetStructureDrag();
 cardDragId=0;clearColumnDragState(true);
 root.querySelectorAll('.is-dragging').forEach(el=>el.classList.remove('is-dragging'));
});
root.addEventListener('dragover',ev=>{
 if(manuscriptDragId){
  const target=ev.target.closest('[data-chapter-sort]');
  root.querySelectorAll('.aest-chapter-sort.is-sort-target').forEach(el=>el.classList.remove('is-sort-target'));
  if(target){ev.preventDefault();target.classList.add('is-sort-target');if(ev.dataTransfer)ev.dataTransfer.dropEffect='move';}
  return;
 }
 if(structureDragId){
  const target=ev.target.closest('.aest-structure-dropzone');
  root.querySelectorAll('.aest-structure-dropzone.is-structure-over').forEach(el=>{if(el!==target)el.classList.remove('is-structure-over');});
  if(target&&target.dataset.dropModel===structureDragModel){
   ev.preventDefault();if(ev.dataTransfer)ev.dataTransfer.dropEffect='move';
   target.classList.add('is-structure-over');
  }
  return;
 }
 if(columnDragId){
  const mural=ev.target.closest('.aest-mural');
  if(mural){
   ev.preventDefault();
   if(ev.dataTransfer)ev.dataTransfer.dropEffect='move';
   previewColumnPosition(ev,mural);
   scrollMuralDuringColumnDrag(ev,mural);
  }
  return;
 }
 if(cardDragId&&ev.target.closest('[data-column]')){ev.preventDefault();if(ev.dataTransfer)ev.dataTransfer.dropEffect='move'}
});
root.addEventListener('drop',async ev=>{
 if(manuscriptDragId){
  ev.preventDefault();
  const target=ev.target.closest('[data-chapter-sort]');
  const id=manuscriptDragId;manuscriptDragId=0;
  root.querySelectorAll('.aest-chapter-sort.is-sort-target').forEach(el=>el.classList.remove('is-sort-target'));
  const ordered=projectChapters(),from=ordered.findIndex(c=>c.id===id);
  const to=ordered.findIndex(c=>c.id===Number(target?.dataset.chapterSort));
  if(from<0||to<0||from===to)return;
  const before=ordered.map(c=>[c.id,c.order]);
  const [moved]=ordered.splice(from,1);ordered.splice(to,0,moved);
  ordered.forEach((c,i)=>{c.order=i;});
  render();
  try{
   const result=await api('POST','chapters/reorder',{project:projectId,ids:ordered.map(c=>c.id)});
   if(!result?.ok||JSON.stringify(result.ids)!==JSON.stringify(ordered.map(c=>c.id)))
    throw Error('Ordem não confirmada pelo servidor.');
  }catch(e){
   before.forEach(([cid,n])=>{const c=db.chapters.find(x=>x.id===cid);if(c)c.order=n;});
   flash='Erro ao reordenar capítulos: '+e.message;render();
  }
  return;
 }
 if(structureDragId){
  const target=ev.target.closest('.aest-structure-dropzone'),id=structureDragId,model=structureDragModel;
  if(!target||target.dataset.dropModel!==model){resetStructureDrag();return;}
  ev.preventDefault();
  const stage=target.dataset.dropStage||'',project=projectId;
  const chapter=db.chapters.find(c=>c.project===project&&c.id===id);
  if(!chapter){resetStructureDrag();return;}
  if(chapterStage(chapter,model)===stage){resetStructureDrag();return;}
  resetStructureDrag();structureDragBusy=true;
  target.classList.add('is-structure-saving');
  const before=chapter.structure;
  chapter.structure={revision:Number(before?.revision||0),positions:{...(before?.positions||{}),[model]:stage}};
  render(); // display target immediately, before the server responds
  try{
   const saved=await api('POST','chapters/'+id+'/structure',{model,stage,revision:Number(before?.revision||0)});
   if(!saved?.ok||Number(saved.id)!==id||saved.structure?.positions?.[model]!==stage)
    throw Error('A posi\u00e7\u00e3o nova n\u00e3o foi confirmada pelo servidor.');
   chapter.structure=saved.structure;
  }catch(error){
   chapter.structure=before;
   flash='Falha ao mover cap\u00edtulo: '+error.message;
   render();
  }
  finally{structureDragBusy=false;target.classList.remove('is-structure-saving');}
  return;
 }
 if(columnDragId){
   const mural=ev.target.closest('.aest-mural');
   if(!mural)return;
   ev.preventDefault();
   previewColumnPosition(ev,mural);
   const order=columnDomOrder(mural);
   const original=columnOriginalOrder.slice();
   clearColumnDragState();
   const p=findProject();
   if(!p||!original.length||order.length!==original.length||order.every((id,i)=>id===original[i]))return;
   const prev=boardCols(p).slice();
   const ordered=order.map(id=>prev.find(x=>x.id===id));
   if(ordered.some(x=>!x))return;
   p.boardColumns=ordered;
   try{
     const result=await api('POST','projects/'+p.id+'/columns/reorder',{order});
     if(!result||!Array.isArray(result.columns)||result.columns.length!==order.length||
       result.columns.some((x,i)=>x.id!==order[i]))
       throw Error('O servidor não confirmou a nova posição.');
     p.boardColumns=result.columns;
   }catch(e){
     p.boardColumns=prev;
     flash='Não foi possível salvar a ordem das colunas: '+e.message;
     const scroll=mural.scrollLeft;
     render();
     const newer=root.querySelector('.aest-mural');if(newer)newer.scrollLeft=scroll;
   }
   return;
 }
 if(!cardDragId)return;
 const col=ev.target.closest('[data-column]');if(!col)return;
 ev.preventDefault();
 const target=ev.target.closest('[data-card-id]');
 const after=target?(db.cards||[]).find(x=>x.id===Number(target.dataset.cardId))?.rank:999999;
 const id=cardDragId;cardDragId=0;
 await cardMove(id,'drop',col.dataset.column,after);
});
root.addEventListener('keydown',async ev=>{
 if(ev.key==='Escape'){
  const tile=root.querySelector('.aest-project-tile.is-color-open');
  if(tile){
   ev.preventDefault();tile.classList.remove('is-color-open');
   const picker=tile.querySelector('.aest-project-color-palette');if(picker)picker.hidden=true;
   const trigger=tile.querySelector('.aest-project-color-trigger');
   if(trigger){trigger.setAttribute('aria-expanded','false');trigger.focus();}
   return;
  }
 }
 if(ev.key==='Escape'){
  const openFolder=root.querySelector('.aest-el-new-folder[open]');
  if(openFolder){ev.preventDefault();openFolder.open=false;return;}
 }
 if(ev.key==='Escape'&&root.querySelector('.aest-review-overlay')){
  ev.preventDefault();root.querySelector('.aest-review-overlay')?.remove();return;
 }
 if(ev.key==='Escape'&&root.querySelector('.aest-card-notes-overlay')){
  ev.preventDefault();closeCardNotes();return;
 }
 if(ev.key==='Escape'&&ev.target.closest('.aest-inline-rename')){
   ev.preventDefault();render();return;
 }

 const grip=ev.target.closest('[data-column-drag]');
 if(ev.target.closest('button,input,textarea,select')||!grip||!ev.altKey||!['ArrowLeft','ArrowRight'].includes(ev.key))return;
 ev.preventDefault();
 const cols=boardCols(findProject()),ix=cols.findIndex(x=>x.id===grip.dataset.columnDrag);
 const step=ev.key==='ArrowLeft'?-1:1,other=cols[ix+step];
 if(!other)return;
 const id=grip.dataset.columnDrag;
 await moveColumn(id,other.id,step===1);
 root.querySelector('[data-column-drag="'+id+'"]')?.focus();
});
root.addEventListener('change',ev=>{
 const target=ev.target;
 if(target?.matches('[data-review-check]')){
  const p=findProject();if(!p)return;
  const review=reviewState(p),checked=target.checked;
  target.disabled=true;
  api('POST','projects/'+p.id+'/review',{revision:review.revision,action:'checklist',
   type:target.dataset.reviewCheck,checked}).then(result=>{
    if(!result?.ok)throw Error('Checklist não confirmado.');
    p.review=result.review;
  }).catch(error=>{
    target.checked=!checked;
    flash='Falha ao atualizar checklist: '+error.message;
    render();
  }).finally(()=>{if(target.isConnected)target.disabled=false;});
  return;
 }
 if(target&&target.id==='aest-element-category'){
  const custom=root.querySelector('.aest-element-custom');
  if(custom){const active=target.value==='_custom';custom.hidden=!active;custom.disabled=!active;custom.required=active;if(active)custom.focus();}
 }
});
root.addEventListener('input',ev=>{
 const el=ev.target;if(!el||!el.dataset||!el.dataset.unlockField)return;
 const p=findProject();if(!p)return;const u=unlockState(p),f=el.dataset.unlockField;
 if(f.startsWith('question-')){
   const ix=Number(f.slice('question-'.length));
   if(ix>=0&&ix<3)u.questions[ix]=el.value;
 }else if(['observation','brainstorm','pattern','sentence','paragraph','premise','developments','protagonist','objective','obstacle','logline','turning','storyline','theme','thesis','tone','summary','events','outline',
  'logline_custom','logline_actor','logline_action','logline_goal','logline_want','logline_block',
  'storyline_custom','storyline_incident','storyline_actor','storyline_goal','storyline_challenge','storyline_stakes','questions_outline'].includes(f)){
  u[f]=el.value;
  if(f.startsWith('logline_'))syncNarrativeText(u,'logline');
  else if(f.startsWith('storyline_'))syncNarrativeText(u,'storyline');
  const kind=f.startsWith('logline_')?'logline':f.startsWith('storyline_')?'storyline':'';
  if(kind){const preview=$('#aest-'+kind+'-preview');if(preview)preview.textContent=u[kind]||'Preencha todas as lacunas para formar a frase.';}
 }
 unlockFlagChanged();
 const banner=$('.aest-alert');if(banner)banner.remove();
});
root.addEventListener('submit',async ev=>{
 const f=ev.target.closest('form[data-form]');if(!f)return;ev.preventDefault();
 const submit=f.querySelector('[type="submit"]');if(submit)submit.disabled=true;
 const values=new FormData(f);
 try{
  if(f.dataset.form==='card-notes'){
    const id=Number(f.dataset.id),notes=String(values.get('notes')||'');
    const status=f.querySelector('#aest-card-notes-status');
    try{
      if(status)status.textContent='Salvando…';
      const card=await api('POST','cards/'+id,{notes});
      if(!card||card.id!==id)throw Error('O servidor não confirmou o cartão.');
      if(String(card.notes||'')!==String(notes))
        throw Error('As notas não foram confirmadas na resposta do servidor.');
      const index=db.cards.findIndex(x=>x.id===id);
      if(index>=0)db.cards[index]=card;
      cardNotesOpenId=0;
      render();
    }catch(error){
      if(status)status.textContent='Erro ao salvar: '+error.message;
      if(submit)submit.disabled=false;
    }
    return;
  }
  if(['review-task-add','review-quote-add'].includes(f.dataset.form)){
   const p=findProject();if(!p)throw Error('Projeto indisponível.');
   if(f.dataset.form==='review-quote-add'&&dirty){const ok=await saveChapter();if(ok===false)throw Error('Salve o texto antes do comentário.');}
   const review=reviewState(p),quote=f.dataset.form==='review-quote-add'?String(values.get('quote')||''):'';
   const chapter=f.dataset.form==='review-quote-add'?chapterId:Number(values.get('chapter')||0);
   const result=await api('POST','projects/'+p.id+'/review',{
    revision:review.revision,action:'create',chapter,
    quote,offset:f.dataset.form==='review-quote-add'?Number(f.dataset.offset||-1):-1,
    type:String(values.get('type')||'trama'),priority:String(values.get('priority')||'normal'),
    note:String(values.get('note')||'').trim()
   });
   if(!result?.ok||!result.review)throw Error('O comentário não foi confirmado.');
   p.review=result.review;
   if(f.dataset.form==='review-quote-add'){
    root.querySelector('.aest-review-overlay')?.remove();
    const status=$('#aest-save-status');if(status)status.textContent='Comentário guardado em Revisão.';
   }else {flash='Pendência registrada.';render();}
   return;
  }
  if(['structure-chapter-create','structure-chapter-link'].includes(f.dataset.form)){
    const model=f.dataset.model,stage=f.dataset.stage;
    if(f.dataset.form==='structure-chapter-create'){
      const title=String(values.get('title')||'').trim();
      if(!title)throw Error('Informe o título do capítulo.');
      const created=await api('POST','chapters',{project:projectId,title,structureModel:model,structureStage:stage});
      if(!Number.isInteger(Number(created.id)))throw Error('A criação do capítulo não foi confirmada.');
      if(created.chapter&&created.chapter.id===Number(created.id))db.chapters.push(created.chapter);
      else await reload();
      flash='Cap\u00edtulo criado e associado ao modelo. Clique em Abrir para escrever.';render();return;
    }
    const id=Number(values.get('chapter'));
    const chapter=db.chapters.find(x=>x.project===projectId&&x.id===id);
    if(!chapter)throw Error('Escolha um capítulo deste projeto.');
    const state=chapter.structure||{revision:0,positions:{}};
    const saved=await api('POST','chapters/'+id+'/structure',{model,stage,revision:Number(state.revision||0)});
    if(!saved?.ok||!saved.structure)throw Error('A posição não foi confirmada.');
    chapter.structure=saved.structure;flash=stage?'Capítulo associado à estrutura.':'Vínculo estrutural retirado.';render();return;
  }
  if(['element-folder-add','element-folder-rename','element-item-add','element-item-update'].includes(f.dataset.form)){
    const p=findProject();if(!p)throw Error('Projeto indisponível.');
    let action='',payload={revision:Number(p.elements?.revision||0)};
    if(f.dataset.form==='element-folder-add'){
      const category=String(values.get('category')||'');
      payload.name=category==='_custom'?String(values.get('custom')||'').trim():category;
      if(!payload.name)throw Error('Informe o nome da pasta.');
      action='folder_add';
    }else if(f.dataset.form==='element-folder-rename'){
      action='folder_rename';payload.folder=f.dataset.folder;payload.name=String(values.get('name')||'').trim();
    }else{
      action=f.dataset.form==='element-item-add'?'item_add':'item_update';
      payload.folder=f.dataset.folder;payload.title=String(values.get('title')||'').trim();payload.notes=String(values.get('notes')||'');
      payload.attrs={};
      for(const [k,v] of values.entries())if(k.startsWith('attr_'))payload.attrs[k.slice(5)]=String(v||'');
      payload.links=values.getAll('links').map(String);
      if(action==='item_update')payload.item=f.dataset.item;
    }
    const saved=await api('POST','projects/'+p.id+'/elements',{action,...payload});
    if(!saved?.ok||!saved.elements)throw Error('O salvamento não foi confirmado.');
    p.elements=saved.elements;editingElementFolder='';flash='Registro salvo e confirmado.';render();return;
  }
  if(f.dataset.form==='column-rename'){
    const out=await api('POST','projects/'+projectId+'/columns/rename',{
      column:f.dataset.column,name:String(values.get('name')||'')});
    const p=findProject();if(p)p.boardColumns=out.columns;
    render();return;
  }else if(f.dataset.form==='lesson-video'){
    if(!cfg.canManageLessons)throw Error('Somente o papel Anthares cadastra vídeos.');
    const out=await api('POST','lesson/'+f.dataset.section,{url:String(values.get('url')||'')});
    cfg.lessonVideos=out.videos;lessonEditing='';render();return;
  }else if(f.dataset.form==='card-add'){
    const card=await api('POST','cards',{project:projectId,column:f.dataset.column,text:String(values.get('text')||'')});
    db.cards=db.cards||[];db.cards.push(card);if(!refreshMuralCards())render();else f.reset();return;
  }else if(f.dataset.form==='card-edit'){
    const card=await api('POST','cards/'+Number(f.dataset.id),{
      text:String(values.get('text')||''),color:String(values.get('color')||'none')});
    const ix=db.cards.findIndex(x=>x.id===card.id);if(ix>=0)db.cards[ix]=card;
    render();return;
  }else if(f.dataset.form==='column-add'){
    const out=await api('POST','projects/'+projectId+'/columns',{name:String(values.get('name')||'')});
    const p=findProject();if(p)p.boardColumns=out.columns;
    render();return;
  }else if(f.dataset.form==='note'){
   const text=String(values.get('text')||'').trim(),kind=f.dataset.kind,project=Number(f.dataset.project)||0;
   const saved=await api('POST','notes',{text,kind,project});
   if(!saved?.note||Number(saved.id)!==Number(saved.note.id)||saved.note.text!==text)
     throw Error('A gravação da anotação não foi confirmada.');
   db.notes.push(saved.note);
   flash=kind==='idea'?'Ideia gravada e confirmada.':'Anotação gravada e confirmada.';
   render();
   if(view==='ideias')root.querySelector('#aest-note-text')?.focus();
   return;
  }else if(f.dataset.form==='project'){
   const payload={};
   for(const key of ['topic','premise','logline','storyline','theme','thesis','tone','summary','outline'])
    if(values.has(key))payload[key]=String(values.get(key)||'');
   const result=await api('POST','projects/'+projectId,payload);
   if(!result?.ok)throw Error('Planejamento não confirmado.');
   const project=findProject();if(project)Object.assign(project,payload);
   flash='Planejamento salvo.';render();return;
  }else if(f.dataset.form==='rename'){
   const title=String(values.get('title')||'').trim();
   if(!title)throw Error('Informe um nome para o projeto.');
   const result=await api('POST','projects/'+projectId,{title});
   const p=findProject();
   if(p)p.title=typeof result.title==='string'&&result.title.trim()?result.title:title;
   flash='Nome do projeto atualizado.';render();return;
  }
  await reload();render();
 }catch(e){
   if(f.dataset.form==='note'){
     let error=f.querySelector('.aest-note-save-error');
     if(!error){
       error=document.createElement('p');error.className='aest-note-save-error';
       error.setAttribute('role','alert');f.appendChild(error);
     }
     error.textContent='Gravação ainda não confirmada: '+e.message+' Seu texto permanece neste campo.';
   }else{flash='Erro: '+e.message;render();}
 }finally{if(submit&&submit.isConnected)submit.disabled=false}
});
async function decodeTextImport(file){
 if(!file||!file.size)throw Error('Selecione um arquivo TXT com conteúdo.');
 if(file.size>1500000)throw Error('O arquivo TXT deve ter até 1,5 MB.');
 const bytes=new Uint8Array(await file.arrayBuffer());
 let encoding='';
 if(bytes.length>=2&&bytes[0]===0xff&&bytes[1]===0xfe)encoding='utf-16le';
 else if(bytes.length>=2&&bytes[0]===0xfe&&bytes[1]===0xff)encoding='utf-16be';
 else if(bytes.length>=3&&bytes[0]===0xef&&bytes[1]===0xbb&&bytes[2]===0xbf)encoding='utf-8';
 else{
  const pairs=Math.min(4096,Math.floor(bytes.length/2));
  let evenNul=0,oddNul=0;
  for(let i=0;i<pairs;i++){
   if(bytes[i*2]===0)evenNul++;
   if(bytes[i*2+1]===0)oddNul++;
  }
  if(pairs>=8&&oddNul/pairs>.4&&evenNul/pairs<.03)encoding='utf-16le';
  else if(pairs>=8&&evenNul/pairs>.4&&oddNul/pairs<.03)encoding='utf-16be';
  else{
   try{new TextDecoder('utf-8',{fatal:true}).decode(bytes);encoding='utf-8';}
   catch{encoding='windows-1252';}
  }
 }
 let text;
 try{text=new TextDecoder(encoding,{fatal:true}).decode(bytes).replace(/^\uFEFF/,'');}
 catch{throw Error('O TXT não pôde ser interpretado com segurança ('+encoding+').');}
 if(!text.trim()||text.includes('\0'))throw Error('O arquivo está vazio ou não contém texto legível.');
 if(text.includes('\uFFFD'))throw Error('A leitura encontrou símbolos ilegíveis (�). Corrija a codificação do TXT original antes de importar.');
 return {text,encoding};
}
root.addEventListener('change',async ev=>{
 const input=ev.target;if(!['aest-import','aest-reimport'].includes(input.id)||!input.files||!input.files[0])return;
 try{
  const file=input.files[0],replacingChapter=input.id==='aest-reimport'?chapterId:0;
  const decoded=await decodeTextImport(file),text=decoded.text;
  const title=file.name.replace(/\.(txt|md)$/i,'').slice(0,140)||'Manuscrito importado';
  const targetProject=projectId;
  if(replacingChapter){
    const summary=text.trim().slice(0,180).replace(/\s+/g,' ');
    if(!window.confirm('Reimportar o TXT e substituir o texto deste capítulo? Uma cópia da versão atual será preservada.\n\nCodificação: '+decoded.encoding+'\nPrévia: '+summary))return;
    if(dirty){
      const saved=await saveChapter();
      if(saved===false)throw Error('Salve o conteúdo atual do capítulo antes de substituí-lo.');
    }
  }
  const endpoint=replacingChapter?'chapters/'+replacingChapter+'/reimport':'chapters/import';
  const result=await api('POST',endpoint,{project:targetProject,title,text});
  if(!result||result.ok!==true||!Number.isSafeInteger(Number(result.id)))
    throw Error('O servidor não confirmou a importação.');
  if(result.chapter&&result.chapter.id===Number(result.id)&&result.chapter.project===targetProject){
    const existingIndex=db.chapters.findIndex(c=>c.id===Number(result.id));
    if(existingIndex>=0)db.chapters[existingIndex]=result.chapter;
    else db.chapters.push(result.chapter);
  }else await reload();
  const imported=db.chapters.find(c=>c.id===Number(result.id)&&c.project===targetProject);
  if(!imported||!Array.isArray(imported.delta?.ops)||
     !imported.delta.ops.some(op=>typeof op.insert==='string'&&op.insert.trim().length))
    throw Error('A importação foi recebida, porém o capítulo ainda não apareceu na leitura. Confira a lista antes de reenviar.');
  projectId=targetProject;view='projeto';tab='manuscrito';chapterId=Number(result.id);
  flash=replacingChapter?'TXT reimportado com os acentos corrigidos. A versão anterior foi preservada.':
    result.existing?'Texto recuperado de importação anterior.':
    'Capítulo importado e conferido ('+decoded.encoding+').';
  render();
  window.scrollTo({top:0,behavior:'instant'});
 }catch(e){flash='Erro ao importar: '+e.message;render();}
});
function initialOpenError(error){
 root.innerHTML='<div class="aest-access"><h2>Erro ao abrir o Estúdio</h2><p>'+
 esc(error.message)+'</p><button class="aest-btn" type="button" onclick="location.reload()">Tentar novamente</button></div>';
}
if(cfg.initial && Array.isArray(cfg.initial.projects) && Array.isArray(cfg.initial.notes) && Array.isArray(cfg.initial.chapters)){
 db=cfg.initial;if(!Array.isArray(db.cards))db.cards=[];
 fullDataLoaded=!cfg.initial.slim;loadedScope=fullDataLoaded?'all':'slim';
 openRouteFromLocation({initial:true}).catch(initialOpenError);
}else{
 reload().then(()=>openRouteFromLocation({initial:true})).catch(initialOpenError);
}
})();