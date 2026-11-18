(() => {
  const config = __TOUR_CONFIG__;
  const key = 'dashjus.patientTour.v1.' + config.owner;
  const read = (storage, name) => { try { return storage.getItem(name); } catch (_) { return null; } };
  const write = (storage, name) => { try { storage.setItem(name, '1'); } catch (_) {} };
  const previous = window.__dashjusPatientTour;
  if (previous && previous.owner === config.owner && previous.restart === config.restart) return;
  if (previous) previous.close(false);
  const restartKey = key + '.restart.' + config.restart;
  const requested = config.restart && !read(sessionStorage,restartKey);
  if (!requested && (read(localStorage, key) || read(sessionStorage, key))) return;
  if (requested) write(sessionStorage,restartKey);
  const steps = [
    ['.st-key-patient_header', 'Bem-vindo ao DASHJUS', 'Vamos conhecer o portal. Use Próximo para continuar ou Pular tutorial para sair.'],
    ['.st-key-patient_process', 'Escolha seu processo', 'Selecione o processo que deseja acompanhar. As informações abaixo correspondem ao processo escolhido.'],
    ['.patient-status-grid', 'Confira a situação', 'Aqui você vê a situação na Justiça e na saúde. Uma decisão favorável não significa que o atendimento já aconteceu.'],
    ['.patient-next-card', 'Veja o próximo passo', 'Este cartão mostra o que fazer agora, quem acompanha e o prazo informado.'],
    ['.st-key-nav_meus_processos', 'Meus processos', 'Neste menu você encontra seus processos e pode baixar ou ouvir o resumo de acompanhamento.'],
    ['.st-key-nav_ajuda_e_contato', 'Ajuda e contato', 'Encontre contatos, entenda os termos usados no portal e relate um problema.'],
    ['.st-key-support_chat_launcher', 'Tire suas dúvidas', 'Use este botão para perguntar como usar o portal. Evite enviar CPF, senhas e dados de saúde.']
  ];
  let index = 0, target, timer, closed = false;
  const focusBefore = document.activeElement;
  const root = document.createElement('div');
  root.id = 'dashjus-patient-tour';
  root.innerHTML = `<style>
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
    const height = box.offsetHeight, width = box.offsetWidth;
    let top = bottom+14, left = Math.min(W-width-12,Math.max(12,x));
    if (top+height > H-12) top = y-height-14;
    if (top < 12) {
      top = Math.max(12,Math.min(H-height-12,y));
      if (right+width+20 < W) left = right+14;
      else if (x-width-14 > 12) left = x-width-14;
    }
    box.style.left = Math.max(12,left)+'px'; box.style.top = Math.max(12,top)+'px';
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
  window.__dashjusPatientTour = {owner:config.owner,restart:config.restart,close};
  timer = setTimeout(() => show(), 350);
})();
