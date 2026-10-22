// Build website/mkdocs.usecases.yml and serve it. Requires Playwright.
const {chromium}=require('playwright');const assert=require('node:assert/strict');
const base=process.env.REFUND_PREVIEW_URL||'http://localhost:8793/agentic-sidecar/usecases';
(async()=>{const browser=await chromium.launch();try{
 for(const width of [360,768,1440]){
  const page=await browser.newPage({viewport:{width,height:1000},reducedMotion:'reduce'});const errors=[],png=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('govern-langgraph-agent-workflows-flow.png'))png.push(r.url());});
  assert.equal((await page.goto(base+'/govern-langgraph-agent-workflows/')).status(),200);const app=page.locator('[data-langgraph-flow]');assert.equal(await app.count(),1);assert.equal(await app.locator('img').count(),0);
  assert.equal(await page.locator('#architecture').evaluate(n=>n.nextElementSibling.matches('[data-langgraph-flow]')),true);
  for(const amount of [850,120]){
   await app.locator('[data-lg-select]').selectOption(String(amount));const record=JSON.parse(await app.locator('[data-lg-record]').textContent());
   assert.equal(record.risk,'LOW');assert.equal(record.decision,amount===850?'BLOCK':'ALLOW');assert.equal(record.tool_executed,amount===120);assert.equal(record.final_message,amount===120?'Refund issued.':null);assert.equal(record.exception,amount===850?'SidecarBlockedError':null);
   assert.equal(await app.locator('[data-lg-calls]').innerText(),amount===850?'0':'1');assert.equal(await app.locator('[data-lg-funds]').innerText(),amount===850?'$0':'$120');assert.equal(await app.locator('[data-lg-node="3"].skipped').count(),amount===850?1:0);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.equal(await app.evaluate(el=>el.scrollWidth>el.clientWidth),false);
   const lengths=await app.locator('.lg-wire-track').evaluateAll(nodes=>nodes.map(n=>n.getTotalLength()));assert.ok(lengths.every(n=>Number.isFinite(n)&&n>0));
   const boxes=await app.locator('[data-lg-node]').evaluateAll(nodes=>nodes.map(n=>{const b=n.getBoundingClientRect();return{x:b.x,right:b.right,y:b.y,bottom:b.bottom,overflow:n.scrollWidth>n.clientWidth+2};}));assert.equal(boxes.some(b=>b.overflow),false);for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];assert.equal(a.x<b.right&&a.right>b.x&&a.y<b.bottom&&a.bottom>b.y,false);}
  }
  assert.deepEqual(png,[]);assert.deepEqual(errors,[]);await app.locator('[data-lg-select]').selectOption('850');
  if(process.env.REFUND_SCREENSHOT_DIR&&width===1440)await app.screenshot({path:process.env.REFUND_SCREENSHOT_DIR+'/langgraph-architecture.png'});
  console.log('PASS LangGraph Architecture: constraint block, LOW risk, allowed reply, preserved image unused and responsive layout at '+width+'px');await page.close();
 }
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});await page.clock.install({time:new Date('2026-10-21T12:00:00Z')});await page.clock.pauseAt(new Date('2026-10-21T12:00:01Z'));await page.goto(base+'/govern-langgraph-agent-workflows/');const app=page.locator('[data-langgraph-flow]');await app.scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('[data-langgraph-flow]').classList.contains('lg-playing'));
 for(const [amount,seq] of [[850,[0,1,2,4,5]],[120,[0,1,2,3,4,5]]]){
  assert.equal(await app.getAttribute('data-amount'),String(amount));
  for(const phase of seq){assert.equal(await app.getAttribute('data-phase'),String(phase));const record=JSON.parse(await app.locator('[data-lg-record]').textContent());assert.equal(record.tool_executed,amount===120&&phase>=3);if(record.tool_executed)assert.equal(record.decision,'ALLOW');if(phase>=4){assert.equal(record.risk,'LOW');assert.equal(record.graph_outcome,amount===850?'exception':'completed');}await page.clock.runFor(phase===5?2600:1000);}
 }
 await app.locator('[data-lg-play]').click();const phase=await app.getAttribute('data-phase');await page.clock.runFor(5000);assert.equal(await app.getAttribute('data-phase'),phase);
 await app.locator('[data-lg-replay]').click();await page.clock.runFor(1000);assert.equal(await app.getAttribute('data-phase'),'1');await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.querySelector('[data-langgraph-flow]').dataset.phase==='5');await page.clock.runFor(4000);assert.equal(await app.getAttribute('data-phase'),'5');await page.close();
 console.log('PASS timed tool-boundary gating, no blocked dispatch, successful return, pause/replay and reduced motion');
 const noJS=await browser.newPage({javaScriptEnabled:false});await noJS.goto(base+'/govern-langgraph-agent-workflows/');assert.equal(await noJS.locator('[data-langgraph-flow]').count(),1);assert.equal(await noJS.locator('[data-lg-select]').isVisible(),false);assert.match(await noJS.locator('[data-langgraph-flow]').innerText(),/SidecarBlockedError/);await noJS.close();console.log('PASS static no-JavaScript fallback');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
