/* Illustrates the documented RiskEvaluator rule. No SDK, tool or payment calls. */
(() => {
  const root = document.querySelector('[data-refund-flow]');
  if (!root) return;
  const media = matchMedia('(prefers-reduced-motion: reduce)');
  const stages = [...root.querySelectorAll('[data-refund-stage]')];
  const map = root.querySelector('.refund-map');
  const names = ['Agent call', 'Risk evaluation', 'Gate verdict', 'Tool boundary'];
  let phase = media.matches ? 3 : 0;
  let amount = 850;
  let playing = !media.matches;
  let visible = false;
  let timer;
  const set = (selector, text) => { root.querySelector(selector).textContent = text; };
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('aria-hidden', 'true');
  svg.classList.add('refund-wires');
  map.prepend(svg);
  const wires = stages.slice(1).map(() => {
    const group = document.createElementNS(svgNS, 'g');
    for (const cls of ['refund-wire-track', 'refund-wire-pulse']) {
      const path = document.createElementNS(svgNS, 'path');
      path.classList.add(cls); group.append(path);
    }
    svg.append(group); return group;
  });
  function drawWires() {
    const bounds = map.getBoundingClientRect();
    if (!bounds.width || !bounds.height) return;
    svg.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
    wires.forEach((group, i) => {
      const from = stages[i].getBoundingClientRect();
      const to = stages[i + 1].getBoundingClientRect();
      const down = to.top > from.top + 10;
      const x1 = (down ? from.left + from.width / 2 : from.right) - bounds.left;
      const y1 = (down ? from.bottom : from.top + from.height / 2) - bounds.top;
      const x2 = (down ? to.left + to.width / 2 : to.left) - bounds.left;
      const y2 = (down ? to.top : to.top + to.height / 2) - bounds.top;
      const d = down
        ? `M ${x1} ${y1} C ${x1} ${(y1+y2)/2}, ${x2} ${(y1+y2)/2}, ${x2} ${y2}`
        : `M ${x1} ${y1} C ${(x1+x2)/2} ${y1}, ${(x1+x2)/2} ${y2}, ${x2} ${y2}`;
      [...group.children].forEach(path => path.setAttribute('d', d));
      group.style.setProperty('--refund-wire-length', group.firstChild.getTotalLength());
    });
  }
  function render(manual = false) {
    const blocked = amount > 500;
    root.dataset.amount = String(amount);
    root.dataset.phase = String(phase);
    root.dataset.outcome = phase >= 2 ? (blocked ? 'blocked' : 'allowed') : 'pending';
    set('[data-refund-amount]', '$' + amount);
    set('[data-refund-comparison]', `$${amount} ${blocked ? '>' : '≤'} $500`);
    set('[data-refund-verdict]', phase >= 2 ? (blocked ? 'BLOCK' : 'ALLOW') : 'Pending verdict');
    set('[data-refund-reason]', phase >= 2 ? (blocked ? 'The request exceeds the configured limit.' : 'No HIGH-risk rule matches this request.') : 'The gate has not completed its check.');
    set('[data-refund-risk]', phase >= 2 ? (blocked ? 'Risk: HIGH' : 'Risk: LOW') : 'Awaiting evaluation');
    set('[data-refund-tool-title]', phase === 3 ? (blocked ? 'Execution halted' : 'Refund executed') : 'Tool call held');
    set('[data-refund-exception]', phase === 3 ? (blocked ? 'SidecarBlockedError' : 'refund_processed') : 'Not dispatched');
    set('[data-refund-tool-detail]', phase === 3 ? (blocked ? 'The inner refund function is never invoked.' : 'One authorized tool invocation is illustrated.') : 'No execution before the gate decision.');
    set('[data-refund-funds]', phase === 3 ? (blocked ? '$0 issued' : '$300 issued') : '$0 issued');
    const statuses = ['PROPOSAL CAPTURED', blocked ? 'HIGH RISK' : 'LOW RISK', blocked ? 'DISPATCH DENIED' : 'DISPATCH ALLOWED', blocked ? 'TOOL NOT CALLED' : 'SIMULATED EXECUTION'];
    stages.forEach((node, i) => {
      const completed = i < phase || (phase === 3 && i === 3);
      node.classList.toggle('active', i === phase);
      node.classList.toggle('complete', completed);
      const check = node.querySelector('.refund-check');
      check.textContent = completed ? '✓' : '·';
      check.setAttribute('aria-label', completed ? 'Complete' : i === phase ? 'Checking' : 'Pending');
      set(`[data-refund-stage-status="${i}"]`, completed ? statuses[i] : i === phase ? 'IN PROGRESS' : 'WAITING');
    });
    wires.forEach((group, i) => {
      group.setAttribute('class', phase === i + 1 ? 'pinging' : phase > i + 1 ? 'done' : 'pending');
    });
    const stories = [
      ['The agent proposes a refund.', `issue_refund("ORD-101", ${amount}) is intercepted before its inner function runs.`],
      ['Evaluate the amount, not the prompt.', `RiskEvaluator compares $${amount} against the $500 threshold using a deterministic rule.`],
      [blocked ? 'Policy says BLOCK.' : 'Policy says ALLOW.', blocked ? '$850 exceeds $500, so risk is HIGH and meets the configured blocking threshold.' : '$300 does not exceed $500. Risk defaults to LOW in this example and dispatch is allowed.'],
      [blocked ? 'Blocked before money can move.' : 'Within policy. Allowed to proceed.', blocked ? 'Govern mode raises SidecarBlockedError before issue_refund executes. No funds are issued.' : 'The governed tool returns refund_processed for $300. This animation illustrates the result without making a real payment.']
    ];
    root.querySelector('.refund-result').setAttribute('aria-live', manual ? 'polite' : 'off');
    set('[data-refund-phase]', `${String(phase + 1).padStart(2,'0')} / ${names[phase].toUpperCase()}`);
    set('[data-refund-result]', stories[phase][0]);
    set('[data-refund-detail]', stories[phase][1]);
    set('[data-refund-call-count]', phase === 3 && !blocked ? '1' : '0');
    set('[data-refund-result-funds]', phase === 3 && !blocked ? '$300' : '$0');
    set('[data-refund-playback]', `${playing ? 'Automatic playback' : media.matches ? 'Static overview · reduced motion' : 'Paused'} · $${amount} request`);
    set('[data-refund-play]', playing ? 'Ⅱ Pause animation' : '▶ Play animation');
    root.querySelector('[data-refund-play]').setAttribute('aria-pressed', String(playing));
    root.querySelector('.refund-progress>span').style.width = ((phase + 1) / 4 * 100) + '%';
    schedule();
  }
  function schedule() {
    clearTimeout(timer);
    const running = playing && visible && !document.hidden;
    root.classList.toggle('refund-playing', running);
    if (running) timer = setTimeout(() => {
      if (!visible || document.hidden) { schedule(); return; }
      if (phase === 3) { phase = 0; amount = amount === 850 ? 300 : 850; }
      else phase++;
      render();
    }, phase === 3 ? 2600 : 1000);
  }
  root.querySelectorAll('button').forEach(button => { button.hidden = false; });
  root.addEventListener('click', event => {
    const button = event.target.closest('button'); if (!button) return;
    if (button.hasAttribute('data-refund-play')) playing = !playing;
    else if (button.hasAttribute('data-refund-replay')) { amount = 850; phase = 0; playing = true; }
    else return;
    render(true);
  });
  new ResizeObserver(drawWires).observe(map);
  document.fonts.ready.then(drawWires);
  new IntersectionObserver(entries => { visible = entries[0].isIntersecting; schedule(); }, { threshold: 0.12 }).observe(root);
  document.addEventListener('visibilitychange', schedule);
  media.addEventListener('change', () => {
    if (media.matches) { playing = false; amount = 850; phase = 3; }
    render();
  });
  render(); drawWires();
})();
