/* Scripted visualization of the documented supervision paths; no runtime calls. */
(() => {
 const root=document.querySelector('[data-support-flow]');if(!root)return;
 const cases=[
  {id:'refund-block',mode:'govern',tool:'issue_refund',args:{order_id:'ORD-999',amount:850},decision:'BLOCK',risk:'HIGH',stops:'risk',reason:'Refund exceeds threshold ($500)'},
  {id:'delete',mode:'govern',tool:'delete_customer_record',args:{customer_id:'cust_1001'},decision:'BLOCK',risk:null,stops:'policy',reason:'Account deletion requires explicit admin authorization'},
  {id:'observe-refund',mode:'observe',tool:'issue_refund',args:{order_id:'ORD-999',amount:850},decision:'BLOCK',risk:'HIGH',stops:'risk',reason:'Refund exceeds threshold ($500)'},
  {id:'budget',mode:'govern',tool:'read_order',args:{order_id:'ORD-999'},decision:'PAUSE',risk:'LOW',stops:'budget',reason:'Budget Guardian: cost $5.0000 >= $5.0000'},
  {id:'read',mode:'govern',tool:'read_order',args:{order_id:'ORD-999'},decision:'ALLOW',risk:'LOW',stops:null,reason:'All configured checks passed'},
  {id:'refund-allow',mode:'govern',tool:'issue_refund',args:{order_id:'ORD-999',amount:300},decision:'ALLOW',risk:'LOW',stops:null,reason:'All configured checks passed'}
 ];
 const keys=['request','policy','risk','intent','budget','verdict','dispatch','audit'];
 const labels=['Agent request','Policy Advisor','Risk Evaluator','Intent Guardian','Budget Guardian','Decision gate','Tool boundary','Audit'];
 const media=matchMedia('(prefers-reduced-motion: reduce)');
 let caseIndex=0,phase=media.matches?7:0,playing=!media.matches,visible=false,timer;
 const current=()=>cases[caseIndex];
 const sequence=()=>{const stop=current().stops;return keys.map((_,i)=>i).filter(i=>!stop||i<=keys.indexOf(stop)||i>=5);};
 const set=(sel,text)=>{root.querySelector(sel).textContent=text;};
 const map=root.querySelector('.support-map');
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.classList.add('support-wires');svg.setAttribute('aria-hidden','true');map.prepend(svg);
 let wires=[];
 function rebuildWires(){
  svg.replaceChildren();wires=[];
  const seq=sequence();
  for(let i=1;i<seq.length;i++){
   const from=seq[i-1],to=seq[i],group=document.createElementNS(ns,'g');
   for(const cls of ['support-wire-track','support-wire-pulse']){const path=document.createElementNS(ns,'path');path.classList.add(cls);group.append(path);}
   svg.append(group);wires.push({from,to,group});
  }
  drawWires();
 }
 function drawWires(){
  const bounds=map.getBoundingClientRect();if(!bounds.width||!bounds.height)return;
  svg.setAttribute('viewBox',`0 0 ${bounds.width} ${bounds.height}`);
  wires.forEach(({from,to,group})=>{
   const a=root.querySelector(`[data-support-node="${keys[from]}"]`).getBoundingClientRect(),b=root.querySelector(`[data-support-node="${keys[to]}"]`).getBoundingClientRect();
   const down=b.top>a.top+15;
   const x1=(down?a.left+a.width/2:a.right)-bounds.left,y1=(down?a.bottom:a.top+a.height/2)-bounds.top;
   const x2=(down?b.left+b.width/2:b.left)-bounds.left,y2=(down?b.top:b.top+b.height/2)-bounds.top;
   const d=down?`M ${x1} ${y1} C ${x1} ${(y1+y2)/2}, ${x2} ${(y1+y2)/2}, ${x2} ${y2}`:`M ${x1} ${y1} C ${(x1+x2)/2} ${y1}, ${(x1+x2)/2} ${y2}, ${x2} ${y2}`;
   [...group.children].forEach(path=>path.setAttribute('d',d));group.style.setProperty('--support-wire-length',group.firstChild.getTotalLength());
  });
 }
 function render(manual=false){
  const c=current(),seq=sequence(),shortCircuited=Boolean(c.stops)&&phase>keys.indexOf(c.stops),executed=phase>=6&&(c.mode==='observe'||c.decision==='ALLOW'),refund=executed&&c.tool==='issue_refund'?c.args.amount:0;
  root.dataset.scenario=c.id;root.dataset.phase=String(phase);root.dataset.mode=c.mode;root.dataset.decision=phase>=5?c.decision:'PENDING';root.dataset.executed=String(executed);
  set('[data-support-call]',`${c.tool}(${Object.values(c.args).map(v=>typeof v==='string'?JSON.stringify(v):v).join(', ')})`);
  set('[data-support-mode]',c.mode.toUpperCase());set('[data-support-mode-detail]',c.mode==='observe'?'Log only · not enforced':'Active enforcement');
  const descriptions={
   policy:c.stops==='policy'?'delete_* matches: policy effect is deny.':'No deny rule matches this proposed tool.',
   risk:c.risk==='HIGH'?'$850 exceeds $500: HIGH risk reaches the BLOCK threshold.':'No HIGH-risk refund rule matches; risk defaults to LOW.',
   intent:c.tool==='issue_refund'?`Compare $${c.args.amount} to the user-authorized maximum refund of $500.`:'The refund amount binding does not apply to this order-read tool.',
   budget:c.id==='budget'?'Recorded task spend is $5.00, at the $5.00 ceiling.':'Recorded task spend is $0.00 of the $5.00 ceiling in this example.'
  };
  for(let i=0;i<keys.length;i++){
   const node=root.querySelector(`[data-support-node="${keys[i]}"]`),skipped=!seq.includes(i)&&shortCircuited,done=seq.includes(i)&&(i<phase||phase===7),failed=c.stops===keys[i]&&i<phase;
   node.classList.toggle('active',i===phase);node.classList.toggle('complete',done);node.classList.toggle('skipped',skipped);node.classList.toggle('failed',failed);
   const check=node.querySelector('.support-tick');check.textContent=skipped?'–':done?(failed?'×':'✓'):'·';check.setAttribute('aria-label',skipped?'Not evaluated':done?(failed?'Check returned an intervention':'Complete'):i===phase?'Checking':'Pending');
   if(i>=1&&i<=4){const key=keys[i];const pendingDetail={policy:'Configured rule: deny tools matching delete_*.',risk:'Configured rule: refunds above $500 are HIGH risk.',intent:'Bind refund amount to the user-authorized maximum of $500.',budget:'Compare recorded spend against the $5.00 task budget.'};set(`[data-support-${key}-detail]`,skipped?`Earlier ${c.stops} evaluation returned ${c.decision}; this gate is not evaluated.`:done||i===phase?descriptions[key]:pendingDetail[key]);set(`[data-support-${key}]`,skipped?'NOT EVALUATED':done?(key===c.stops?(key==='policy'?'DENY → BLOCK':key==='risk'?'HIGH → BLOCK':'CEILING REACHED → PAUSE'):'PASS'):i===phase?'EVALUATING':'WAITING');}
  }
  set('[data-support-verdict]',phase>=5?c.decision:'Awaiting decision');
  set('[data-support-verdict-detail]',phase>=5?(c.stops==='policy'?'Policy effect DENY produces decision BLOCK.':c.reason):'Decision follows the configured evaluator order.');
  set('[data-support-dispatch]',phase<6?'Tool call held':executed?(c.mode==='observe'&&c.decision!=='ALLOW'?'Observe: tool still runs':'Authorized tool executes'):'Execution prevented');
  set('[data-support-dispatch-code]',phase<6?'Not dispatched':executed?(c.tool==='issue_refund'?'refund_processed':c.tool==='read_order'?'order retrieved':'tool executed'):c.decision==='PAUSE'?'Held for escalation':'SidecarBlockedError');
  set('[data-support-dispatch-detail]',phase<6?'No execution outcome yet.':executed?(c.mode==='observe'?'Observe records the verdict without blocking the illustrated tool call.':'The illustration dispatches one allowed tool call.'):'The governed action is held before its inner tool runs.');
  set('[data-support-calls]',executed?'1':'0');set('[data-support-funds]','$'+refund);
  set('[data-support-audit-title]',phase===7?'The decision and outcome are recorded.':'Awaiting decision provenance.');
  set('[data-support-audit]',phase===7?`Mode ${c.mode} · decision ${c.decision} · ${executed?'illustrated tool executed':'tool not executed'} · ${c.reason}.`:'The illustrative record will retain tool, arguments, mode, verdict, reason and tool outcome.');
  const stories=[['Capture the proposed action.','The support agent proposes a tool call. Its arguments enter the pre-action boundary.'],['Apply the policy rules.','Policy Advisor checks delete_* first. A deny returns BLOCK immediately.'],['Evaluate financial risk.','Refunds above $500 produce HIGH risk, reaching the configured blocking threshold.'],['Check intent alignment.','Intent Guardian evaluates applicable bindings against the user’s $500 authorization.'],['Check recorded task spend.','Budget Guardian checks accounted cost. Reaching the $5 ceiling produces PAUSE, not an ALLOW.'],['Return the decision.',c.mode==='observe'?`${c.decision} is recorded in Observe mode. This is not an enforced stop.`:`${c.decision} determines whether the governed tool can dispatch.`],['Apply the mode at the tool boundary.',c.mode==='observe'?'Observe mode permits the illustrated call even when the recorded decision is BLOCK. Govern mode would stop it.':c.decision==='ALLOW'?'The allowed tool call is illustrated. No real service is contacted.':'The tool does not execute. An earlier decision prevents the governed call.'],['Keep an attributable record.',`The sample record distinguishes ${c.decision} from ${executed?'execution':'non-execution'}, and shows which gates actually evaluated.`]];
  set('[data-support-phase]',`${String(phase+1).padStart(2,'0')} / ${labels[phase].toUpperCase()}`);set('[data-support-heading]',stories[phase][0]);set('[data-support-story]',stories[phase][1]);
  root.querySelector('.support-story').setAttribute('aria-live',manual?'polite':'off');
  const record={simulation:true,scenario:c.id,mode:c.mode,tool:c.tool,arguments:c.args,decision:phase>=5?c.decision:'PENDING',risk:phase>=5?c.risk:null,reason:phase>=5?c.reason:null,evaluators:keys.slice(1,5).map((key,i)=>({name:key,status:!seq.includes(i+1)&&shortCircuited?'not_evaluated':phase>i+1?'evaluated':phase===i+1?'evaluating':'pending'})),tool_executed:executed,refund_issued:refund,audit_recorded:phase===7};
  set('[data-support-record]',JSON.stringify(record,null,2));
  set('[data-support-play]',playing?'Ⅱ Pause animation':'▶ Play animation');root.querySelector('[data-support-play]').setAttribute('aria-pressed',String(playing));root.querySelector('[data-support-select]').value=c.id;
  set('[data-support-playback]',`${playing?'Automatic playback':media.matches?'Static overview · reduced motion':'Paused'} · ${c.mode} mode`);
  root.querySelector('.refund-progress>span').style.width=((seq.indexOf(phase)+1)/seq.length*100)+'%';
  wires.forEach(({to,group})=>group.setAttribute('class',to===phase?'pinging':to<phase?'done':'pending'));
  schedule();
 }
 function schedule(){clearTimeout(timer);const running=playing&&visible&&!document.hidden;root.classList.toggle('support-playing',running);if(running)timer=setTimeout(()=>{if(!visible||document.hidden){schedule();return;}const seq=sequence(),i=seq.indexOf(phase);if(i===seq.length-1){caseIndex=(caseIndex+1)%cases.length;phase=0;rebuildWires();}else phase=seq[i+1];render();},phase===7?2600:1000);}
 root.querySelectorAll('button,[data-support-picker]').forEach(node=>node.hidden=false);
 root.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.hasAttribute('data-support-play'))playing=!playing;else if(b.hasAttribute('data-support-replay')){phase=0;playing=true;}else return;render(true);});
 root.querySelector('[data-support-select]').addEventListener('change',e=>{caseIndex=cases.findIndex(c=>c.id===e.target.value);phase=media.matches?7:0;playing=!media.matches;rebuildWires();render(true);});
 new ResizeObserver(drawWires).observe(map);document.fonts.ready.then(drawWires);
 new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;schedule();},{threshold:.1}).observe(root);
 document.addEventListener('visibilitychange',schedule);
 media.addEventListener('change',()=>{if(media.matches){playing=false;phase=7;}render();});
 rebuildWires();render();
})();
