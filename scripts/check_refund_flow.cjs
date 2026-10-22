// Build website/mkdocs.usecases.yml and serve the output before running. Requires Playwright.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const base=process.env.REFUND_PREVIEW_URL||'http://localhost:8793/agentic-sidecar/usecases';
(async()=>{
 const browser=await chromium.launch();
 try {
  for(const width of [360,768,1440]){
   const page=await browser.newPage({viewport:{width,height:1000},reducedMotion:'reduce'});
   const errors=[],images=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('prevent-unauthorized-refunds-flow.png'))images.push(r.url());});
   assert.equal((await page.goto(base+'/prevent-unauthorized-refunds/')).status(),200);
   const app=page.locator('[data-refund-flow]');assert.equal(await app.count(),1);
   assert.equal(await app.locator('img').count(),0);assert.deepEqual(images,[]);
   assert.equal(await app.getAttribute('data-outcome'),'blocked');
   assert.equal(await app.locator('[data-refund-call-count]').innerText(),'0');
   assert.equal(await app.locator('[data-refund-result-funds]').innerText(),'$0');
   assert.equal(await app.locator('.refund-stages>li').count(),4);
   assert.equal(await page.locator('#architecture').count(),1);
   assert.equal(await page.locator('#architecture').evaluate(el=>el.nextElementSibling.matches('[data-refund-flow]')),true);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   assert.equal(await app.evaluate(el=>el.scrollWidth>el.clientWidth),false);
   const lengths=await app.locator('.refund-wire-track').evaluateAll(nodes=>nodes.map(n=>n.getTotalLength()));assert.equal(lengths.length,3);assert.ok(lengths.every(n=>n>0&&Number.isFinite(n)));
   const rects=await app.locator('[data-refund-stage]').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return{x:r.x,y:r.y,right:r.right,bottom:r.bottom,overflow:n.scrollWidth>n.clientWidth+2};}));
   assert.equal(rects.some(r=>r.overflow),false);
   for(let i=0;i<4;i++)for(let j=i+1;j<4;j++){const a=rects[i],b=rects[j];assert.equal(a.x<b.right&&a.right>b.x&&a.y<b.bottom&&a.bottom>b.y,false);}
   assert.deepEqual(errors,[]);
   if(process.env.REFUND_SCREENSHOT_DIR&&width===1440)await app.screenshot({path:process.env.REFUND_SCREENSHOT_DIR+'/refund-architecture.png'});
   console.log('PASS native refund architecture: static blocked outcome, no PNG request, wiring and layout at '+width+'px');await page.close();
  }
  const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
  await page.clock.install({time:new Date('2026-10-21T12:00:00Z')});await page.clock.pauseAt(new Date('2026-10-21T12:00:01Z'));
  await page.goto(base+'/prevent-unauthorized-refunds/');
  const app=page.locator('[data-refund-flow]');await app.scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('[data-refund-flow]').classList.contains('refund-playing'));
  for(const amount of [850,300]){
   assert.equal(await app.getAttribute('data-amount'),String(amount));
   for(let phase=0;phase<4;phase++){
    assert.equal(await app.getAttribute('data-phase'),String(phase));
    assert.equal(await app.locator('[data-refund-call-count]').innerText(),phase===3&&amount===300?'1':'0');
    if(phase>=2)assert.equal(await app.getAttribute('data-outcome'),amount===850?'blocked':'allowed');
    if(phase===3){assert.equal(await app.locator('[data-refund-result-funds]').innerText(),amount===850?'$0':'$300');assert.match(await app.locator('[data-refund-exception]').innerText(),amount===850?/SidecarBlockedError/:/refund_processed/);}
    await page.clock.runFor(phase===3?2600:1000);
   }
  }
  await app.locator('[data-refund-play]').click();const paused=await app.getAttribute('data-phase');await page.clock.runFor(5000);assert.equal(await app.getAttribute('data-phase'),paused);
  await app.locator('[data-refund-replay]').click();assert.equal(await app.getAttribute('data-amount'),'850');assert.equal(await app.getAttribute('data-phase'),'0');
  await page.clock.runFor(1000);assert.equal(await app.getAttribute('data-phase'),'1');
  await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.querySelector('[data-refund-flow]').dataset.phase==='3');
  await page.clock.runFor(5000);assert.equal(await app.getAttribute('data-outcome'),'blocked');assert.equal(await app.getAttribute('data-phase'),'3');
  console.log('PASS $850 blocked and $300 allowed cycles; dispatch counts, funds, pause/replay and reduced-motion transition');await page.close();
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
