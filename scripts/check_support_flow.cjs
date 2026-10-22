// Build and serve website/mkdocs.usecases.yml. Requires Playwright.
const {chromium}=require('playwright');const assert=require('node:assert/strict');
const base=process.env.REFUND_PREVIEW_URL||'http://localhost:8793/agentic-sidecar/usecases';
(async()=>{const browser=await chromium.launch();try{
 for(const width of [360,768,1440]){
  const page=await browser.newPage({viewport:{width,height:1000},reducedMotion:'reduce'});const errors=[],png=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('governed-customer-support-agent-flow.png'))png.push(r.url());});
  assert.equal((await page.goto(base+'/governed-customer-support-agent/')).status(),200);
  const app=page.locator('[data-support-flow]');assert.equal(await app.count(),1);assert.equal(await app.locator('img').count(),0);
  assert.equal(await page.locator('#architecture').evaluate(n=>n.nextElementSibling.matches('[data-support-flow]')),true);
  for(const [id,decision,executed,refund,skips] of [['refund-block','BLOCK',false,0,2],['delete','BLOCK',false,0,3],['observe-refund','BLOCK',true,850,2],['budget','PAUSE',false,0,0],['read','ALLOW',true,0,0],['refund-allow','ALLOW',true,300,0]]){
   await app.locator('[data-support-select]').selectOption(id);
   assert.equal(await app.getAttribute('data-decision'),decision);assert.equal(await app.getAttribute('data-executed'),String(executed));
   assert.equal(await app.locator('.support-gate.skipped').count(),skips);
   const record=JSON.parse(await app.locator('[data-support-record]').textContent());assert.equal(record.refund_issued,refund);assert.equal(record.tool_executed,executed);assert.equal(record.evaluators.filter(e=>e.status==='not_evaluated').length,skips);
   assert.equal(await app.locator('[data-support-calls]').innerText(),executed?'1':'0');
   if(id==='delete'){assert.equal(record.risk,null);assert.match(await app.locator('[data-support-verdict-detail]').innerText(),/DENY produces decision BLOCK/);}
   if(id==='observe-refund')assert.match(await app.locator('[data-support-dispatch]').innerText(),/Observe: tool still runs/);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   assert.equal(await app.evaluate(n=>n.scrollWidth>n.clientWidth),false);
   const lengths=await app.locator('.support-wire-track').evaluateAll(nodes=>nodes.map(n=>n.getTotalLength()));assert.ok(lengths.every(n=>Number.isFinite(n)&&n>0));
  }
  assert.deepEqual(png,[]);assert.deepEqual(errors,[]);
  await app.locator('[data-support-select]').selectOption('refund-block');
  if(process.env.REFUND_SCREENSHOT_DIR&&width===1440)await app.screenshot({path:process.env.REFUND_SCREENSHOT_DIR+'/support-architecture.png'});
  console.log('PASS support Architecture: six outcomes, early returns, observe dispatch, audit and layout at '+width+'px');await page.close();
 }
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
 await page.clock.install({time:new Date('2026-10-21T12:00:00Z')});await page.clock.pauseAt(new Date('2026-10-21T12:00:01Z'));
 await page.goto(base+'/governed-customer-support-agent/');const app=page.locator('[data-support-flow]');await app.scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('[data-support-flow]').classList.contains('support-playing'));
 for(const [id,seq,executed] of [['refund-block',[0,1,2,5,6,7],false],['delete',[0,1,5,6,7],false],['observe-refund',[0,1,2,5,6,7],true],['budget',[0,1,2,3,4,5,6,7],false],['read',[0,1,2,3,4,5,6,7],true],['refund-allow',[0,1,2,3,4,5,6,7],true]]){
  assert.equal(await app.getAttribute('data-scenario'),id);
  for(const phase of seq){assert.equal(await app.getAttribute('data-phase'),String(phase));assert.equal(await app.getAttribute('data-executed'),String(phase>=6&&executed));await page.clock.runFor(phase===7?2600:1000);}
 }
 await app.locator('[data-support-play]').click();const phase=await app.getAttribute('data-phase');await page.clock.runFor(5000);assert.equal(await app.getAttribute('data-phase'),phase);
 await app.locator('[data-support-replay]').click();await page.clock.runFor(1000);assert.equal(await app.getAttribute('data-phase'),'1');
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.querySelector('[data-support-flow]').dataset.phase==='7');await page.clock.runFor(4000);assert.equal(await app.getAttribute('data-phase'),'7');
 console.log('PASS timed sequences skip unevaluated gates, Observe executes BLOCK, Govern prevents it, pause/replay and reduced motion work');await page.close();
 const staticPage=await browser.newPage({javaScriptEnabled:false});await staticPage.goto(base+'/governed-customer-support-agent/');assert.equal(await staticPage.locator('[data-support-flow]').count(),1);assert.equal(await staticPage.locator('[data-support-select]').isVisible(),false);assert.match(await staticPage.locator('[data-support-flow]').innerText(),/Execution prevented/);await staticPage.close();
 console.log('PASS no-JavaScript static fallback');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
