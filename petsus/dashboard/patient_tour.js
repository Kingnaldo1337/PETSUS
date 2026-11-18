(() => {
  const config = __TOUR_CONFIG__;
  const key = 'dashjus.patientTour.v2.' + config.owner + '.' + config.role + '.' + config.page;
  const read = (storage, name) => { try { return storage.getItem(name); } catch (_) { return null; } };
  const write = (storage, name) => { try { storage.setItem(name, '1'); } catch (_) {} };
  const previous = window.__dashjusPatientTour;
  if (previous && previous.owner === config.owner && previous.role === config.role && previous.page === config.page && previous.restart === config.restart) return;
  if (previous) previous.close(false);
  const restartKey = key + '.restart.' + config.restart;
  const requested = config.restart && !read(sessionStorage,restartKey);
  if (!requested && (read(localStorage, key) || read(sessionStorage, key))) return;
  if (requested) write(sessionStorage,restartKey);
  const tours = {
  'Meus processos': [
    ['.st-key-patient_header', 'Seus processos', 'Esta aba reúne os processos vinculados à sua conta. Vamos conhecer as informações e os botões disponíveis.'],
    ['[class*="st-key-patient_record_"]', 'Resumo do processo', 'Cada cartão mostra o assunto, o número do processo e as informações de acompanhamento.'],
    ['[class*="st-key-patient_record_"] [data-testid="stButton"]', 'Acompanhe o processo', 'Use Acompanhar processo para abrir os detalhes e conferir o próximo passo.'],
    ['[class*="st-key-patient_record_"] [data-testid="stDownloadButton"]', 'Baixe o resumo', 'Este botão permite baixar o resumo de acompanhamento em PDF. Documentos oficiais devem ser obtidos com o tribunal ou seu representante.'],
    ['[class*="st-key-patient_record_"] iframe', 'Ouça o resumo', 'Use o botão de ouvir para escutar as informações de acompanhamento do processo.'],
    ['.st-key-support_chat_launcher', 'Precisa de orientação?', 'O assistente pode explicar como usar o portal. Não envie CPF, senhas ou dados de saúde.']
  ],
  'Ajuda e feedback': [
    ['.st-key-patient_header', 'Ajuda e contato', 'Aqui você encontra contatos, pode relatar problemas e consultar explicações sobre o portal.'],
    ['.st-key-patient_contacts', 'Encontre os contatos', 'Consulte os contatos disponíveis para procurar a equipe responsável pelo seu acompanhamento.'],
    ['[data-testid="stTabs"] [role="tablist"]', 'Escolha o tipo de ajuda', 'As abas reúnem os relatos e respostas, o significado das palavras, informações sobre os dados, a avaliação de uso e as principais dúvidas.'],
    ['[data-testid="stTabs"] [role="tabpanel"]:not([hidden])', 'Use a seção escolhida', 'Em Relatar e acompanhar, você pode registrar um problema e consultar a resposta da equipe. Selecione outra aba para acessar os demais conteúdos.'],
    ['.st-key-support_chat_launcher', 'Pergunte sobre o portal', 'Use Tirar dúvidas para receber orientação sobre o uso da plataforma. Evite informar dados pessoais.']
  ],
  'Meu acompanhamento': [
    ['.st-key-patient_header', 'Bem-vindo ao DASHJUS', 'Vamos conhecer o portal. Use Próximo para continuar ou Pular tutorial para sair.'],
    ['.st-key-patient_process', 'Escolha seu processo', 'Selecione o processo que deseja acompanhar. As informações abaixo correspondem ao processo escolhido.'],
    ['.patient-status-grid', 'Confira a situação', 'Aqui você vê a situação na Justiça e na saúde. Uma decisão favorável não significa que o atendimento já aconteceu.'],
    ['.patient-next-card', 'Veja o próximo passo', 'Este cartão mostra o que fazer agora, quem acompanha e o prazo informado.'],
    ['.st-key-nav_meus_processos', 'Meus processos', 'Neste menu você encontra seus processos e pode baixar ou ouvir o resumo de acompanhamento.'],
    ['.st-key-nav_ajuda_e_contato', 'Ajuda e contato', 'Encontre contatos, entenda os termos usados no portal e relate um problema.'],
    ['.st-key-support_chat_launcher', 'Tire suas dúvidas', 'Use este botão para perguntar como usar o portal. Evite enviar CPF, senhas e dados de saúde.']
  ]};
  const steps = config.steps || tours[config.page] || tours['Meu acompanhamento'];
  let index = 0, target, timer, closed = false;
  const focusBefore = document.activeElement;
  const root = document.createElement('div');
  root.id = 'dashjus-patient-tour';
  root.innerHTML = `<style>
    #dashjus-patient-tour{position:fixed;inset:0;z-index:2147483000;pointer-events:none;}
    #dashjus-patient-tour .tour-shade,#dashjus-patient-tour .tour-box{pointer-events:auto;}
    #dashjus-patient-tour .tour-shade{position:fixed;background:rgba(9,28,49,.57);backdrop-filter:blur(3px);z-index:100001;}
    #dashjus-patient-tour .tour-ring{position:fixed;pointer-events:none;border:3px solid #65e2e8;border-radius:12px;box-shadow:0 0 0 2px white;z-index:100002;}
    #dashjus-patient-tour .tour-box{position:fixed;box-sizing:border-box;width:min(360px,calc(100vw - 24px));max-height:calc(100dvh - 24px);overflow:auto;padding:20px;background:#fff;color:#122c50;border:1px solid #bddce5;border-radius:16px;box-shadow:0 14px 50px #001c4055;z-index:100003;font:16px/1.5 sans-serif;}
    #dashjus-patient-tour h2{font-size:20px;margin:6px 0 10px;color:#122c50;}
    #dashjus-patient-tour p{margin:0 0 16px;}
    #dashjus-patient-tour label{display:flex;gap:8px;align-items:center;font-size:14px;margin:12px 0;}
    #dashjus-patient-tour .tour-actions{display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end;}
    #dashjus-patient-tour button{padding:9px 12px;border-radius:8px;border:1px solid #b9ced8;background:white;color:#122c50;cursor:pointer;font:inherit;}
    #dashjus-patient-tour button.primary{background:#087f8c;color:white;border-color:#087f8c;}
    #dashjus-patient-tour button:focus-visible{outline:3px solid #d49100;outline-offset:2px;}
  </style><div class="tour-shade"></div><div class="tour-shade"></div><div class="tour-shade"></div><div class="tour-shade"></div><div class="tour-ring"></div>
  <section class="tour-box" role="dialog" aria-modal="true" aria-labelledby="tour-title" aria-describedby="tour-text" tabindex="-1">
    <small class="tour-count"></small><h2 id="tour-title"></h2><p id="tour-text"></p>
    <label><input type="checkbox"> Não mostrar novamente neste navegador</label>
    <div class="tour-actions"><button class="tour-skip">Pular tutorial</button><button class="tour-back">Voltar</button><button class="primary tour-next">Próximo</button></div>
  </section>`;
  document.body.appendChild(root);
  const box = root.querySelector('.tour-box'), shades = root.querySelectorAll('.tour-shade'), ring = root.querySelector('.tour-ring');
  // Keep clicks inside the tutorial until it is dismissed, including the highlighted area.
  function guard(event) {
    if (!box.contains(event.target)) { event.preventDefault(); event.stopPropagation(); }
  }
  document.addEventListener('click',guard,true);
  const place = (el, x, y, w, h) => Object.assign(el.style, {left:x+'px', top:y+'px', width:Math.max(0,w)+'px', height:Math.max(0,h)+'px'});
  function position() {
    if (!target || !target.isConnected) { close(true); return; }
    const r = target.getBoundingClientRect(), W = innerWidth, H = innerHeight;
    const x = Math.max(0,r.left-5), y = Math.max(0,r.top-5), right = Math.min(W,r.right+5), bottom = Math.min(H,r.bottom+5);
    place(shades[0],0,0,W,y); place(shades[1],0,bottom,W,H-bottom);
    place(shades[2],0,y,x,bottom-y); place(shades[3],right,y,W-right,bottom-y);
    place(ring,x,y,right-x,bottom-y);
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    const sidebarRect = sidebar && sidebar.getBoundingClientRect();
    const sidebarRight = sidebarRect && sidebarRect.width > 0 && sidebarRect.right > 0
      && getComputedStyle(sidebar).visibility !== 'hidden' ? Math.min(W,sidebarRect.right) : 0;
    // Prefer the main content area. On narrow screens keep a full-width bottom
    // panel above the sidebar instead of squeezing the explanation into a sliver.
    const minLeft = W-sidebarRight >= 300 ? sidebarRight+12 : 12;
    box.style.width = Math.min(360,Math.max(0,W-minLeft-12))+'px';
    const height = box.offsetHeight, width = box.offsetWidth;
    const maxLeft = W-width-12;
    let left = Math.max(minLeft,Math.min(maxLeft,x));
    const candidates = [
      {left,top:bottom+14},
      {left,top:y-height-14},
      {left:right+14,top:Math.max(12,Math.min(H-height-12,y))},
      {left:x-width-14,top:Math.max(12,Math.min(H-height-12,y))}
    ];
    const fit = candidates.find(p => p.left >= minLeft && p.left+width <= W-12
      && p.top >= 12 && p.top+height <= H-12);
    const chosen = fit || {left,top:H-height-12};
    box.style.left = Math.max(minLeft,Math.min(maxLeft,chosen.left))+'px';
    box.style.top = Math.max(12,chosen.top)+'px';
  }
  function show(direction = 1) {
    target = null;
    while (index >= 0 && index < steps.length) {
      const candidate = document.querySelector(steps[index][0]);
      if (candidate && candidate.getBoundingClientRect().width && candidate.getBoundingClientRect().height) { target = candidate; break; }
      index += direction;
    }
    if (!target) { close(true); return; }
    root.querySelector('.tour-count').textContent = `Passo ${index+1} de ${steps.length}`;
    root.querySelector('h2').textContent = steps[index][1]; root.querySelector('p').textContent = steps[index][2];
    root.querySelector('.tour-back').disabled = index === 0;
    root.querySelector('.tour-next').textContent = index === steps.length-1 ? 'Concluir' : 'Próximo';
    target.scrollIntoView({block:'center', behavior:'instant'});
    position(); box.focus({preventScroll:true});
  }
  function close(remember) {
    if (closed) return; closed = true; clearTimeout(timer);
    if (remember) {
      write(sessionStorage,key);
      if (root.querySelector('input').checked) write(localStorage,key);
    }
    window.removeEventListener('resize',position); document.removeEventListener('scroll',position,true); document.removeEventListener('keydown',keyboard,true); document.removeEventListener('click',guard,true);
    root.remove(); if (focusBefore && focusBefore.isConnected) focusBefore.focus({preventScroll:true});
  }
  function keyboard(event) {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close(true); }
    if (event.key === 'Tab') {
      const controls = [...box.querySelectorAll('input,button:not(:disabled)')];
      const first = controls[0], last = controls[controls.length-1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === box)) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && (document.activeElement === last || document.activeElement === box)) { event.preventDefault(); first.focus(); }
    }
  }
  root.querySelector('.tour-next').onclick = () => { index++; show(); };
  root.querySelector('.tour-back').onclick = () => { index--; show(-1); };
  root.querySelector('.tour-skip').onclick = () => close(true);
  window.addEventListener('resize',position); document.addEventListener('scroll',position,true); document.addEventListener('keydown',keyboard,true);
  window.__dashjusPatientTour = {owner:config.owner,role:config.role,page:config.page,restart:config.restart,close};
  timer = setTimeout(() => show(), 350);
})();
