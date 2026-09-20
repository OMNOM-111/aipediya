import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const pw = require(process.env.AIPEDIA_PLAYWRIGHT_PACKAGE || 'playwright');
const base = process.env.AIPEDIA_PUBLIC_URL || 'http://127.0.0.1:18816';
const out = path.resolve('artifacts/chronology-20260920', process.env.AIPEDIA_QA_PHASE || 'local-ui');
fs.mkdirSync(out, {recursive:true});
const result = {base, started:new Date().toISOString(), physicalDevices:'Not tested; mobile viewport emulation', checks:[], screenshots:[]};
const save=()=>fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2));
const assert=(v,m)=>{if(!v) throw Error(m);};
const rows=page=>page.locator('#model-rows > tr[data-number]').evaluateAll(rs=>rs.map(r=>({
  number:r.querySelector('.number-col').innerText.trim()==='—'?null:Number(r.querySelector('.number-col').innerText.trim().replace('#','')),
  date:r.querySelector('time')?.getAttribute('datetime')||null,
  shown:r.querySelector('.release-date')?.innerText,
  name:r.querySelector('.model-name').innerText,
  slug:new URL(r.querySelector('.model-name').href).pathname,
})));
async function run(engine){
  const browser=await pw[engine].launch({headless:true});
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage();
  const check=async(name,fn)=>{
    try {result.checks.push({engine,name,status:'PASS',data:await fn()});}
    catch(e){result.checks.push({engine,name,status:'FAIL',error:e.message});}
    save();
  };
  try{
    await check('default-oldest-first-and-two-header-clicks',async()=>{
      await page.goto(base+'/?lang=ru',{waitUntil:'networkidle'});
      assert(await page.locator('select[name=sort]').inputValue()==='number_asc','default is not chronology');
      const first=await rows(page);
      assert(first[0].number===1,'First catalogue number is not1');
      assert(first[0].date,'First row has no date');
      const before=first[0].slug;
      await Promise.all([page.waitForURL(/sort=number_desc/),page.locator('a[data-sort=number]').click()]);
      const reverse=await rows(page);
      assert(reverse[0].number>first[0].number,'First header click did not reverse');
      await Promise.all([page.waitForURL(/sort=number_asc/),page.locator('a[data-sort=number]').click()]);
      assert((await rows(page))[0].slug===before,'Second click did not restore');
      return {first:first[0],newest:reverse[0]};
    });
    for(const dir of ['asc','desc']) await check('full-catalogue-'+dir,async()=>{
      let all=[], index=1;
      while(true){
        await page.goto(`${base}/?lang=en&status=all&sort=number_${dir}&page=${index}`,{waitUntil:'networkidle'});
        all.push(...await rows(page));
        const next=await page.locator('#infinite-scroll').getAttribute('data-next-url');
        if(!next)break;
        assert(index++<30,'pagination loop');
      }
      assert(all.length===255,'Unexpected full count '+all.length);
      assert(new Set(all.map(r=>r.slug)).size===all.length,'Duplicate rows');
      const dated=all.filter(r=>r.date), unknown=all.filter(r=>!r.date);
      assert(unknown.every(r=>r.number===null),'Undated row has chronological number');
      assert(all.slice(dated.length).every(r=>!r.date),'Unknown not last');
      assert(dated.every((r,i)=>r.number===(dir==='asc'?i+1:dated.length-i)),'Non-contiguous chronological numbers');
      assert(dated.every((r,i)=>!i || (dir==='asc'?dated[i-1].date<=r.date:dated[i-1].date>=r.date)),'Dates not chronological');
      return {rows:all.length,dated:dated.length,unknown:unknown.length,first:dated[0],last:dated.at(-1)};
    });
    for(const lang of ['ru','en']) for(const theme of ['light','dark']) for(const width of [390,1440]){
      await check(`visual-${width}-${lang}-${theme}`,async()=>{
        await page.setViewportSize({width,height:width===390?844:1000});
        await page.goto(base+'/?lang='+lang,{waitUntil:'networkidle'});
        if (await page.locator('html').getAttribute('data-theme') !== theme) {
          await page.locator('#theme').click();
        }
        assert(await page.locator('html').getAttribute('data-theme') === theme, 'Theme did not change');
        const measure=await page.evaluate(()=>({width:innerWidth,page:document.documentElement.scrollWidth}));
        assert(measure.page<=measure.width+1,'External horizontal overflow');
        const file=`${engine}-${width}-${lang}-${theme}.png`;
        await page.screenshot({path:path.join(out,file)});result.screenshots.push(file);
        const selected=(await rows(page))[0];
        await page.locator('.model-name').first().click();
        await page.waitForLoadState('networkidle');
        assert((await page.locator('h1').innerText()).includes('#'+selected.number),'Detail number mismatch');
        assert(await page.locator('.release-date time').getAttribute('datetime')===selected.date,'Detail date mismatch');
        const card=`${engine}-card-${width}-${lang}-${theme}.png`;
        await page.screenshot({path:path.join(out,card)});result.screenshots.push(card);
        await page.locator('a.back').click();await page.waitForLoadState('networkidle');
        assert((await rows(page))[0].slug===selected.slug,'Return order changed');
      });
    }
    if(base.startsWith('https://')) await check('public-release-and-original-archive',async()=>{
      const health=await page.evaluate(async()=>({status:(await fetch('/healthz')).status,body:await(await fetch('/healthz')).json()}));
      assert(health.status===200,'Health failed');
      if(process.env.AIPEDIA_EXPECT_COMMIT) assert(health.body.release===process.env.AIPEDIA_EXPECT_COMMIT,'Wrong release');
      return health;
    });
  } finally{await context.close();await browser.close();}
}
await Promise.all(['chromium','firefox','webkit'].map(run));
result.completed=new Date().toISOString();
result.summary=result.checks.reduce((a,c)=>(a[c.status]=(a[c.status]||0)+1,a),{});save();
console.log(JSON.stringify(result.summary));
if(result.checks.some(c=>c.status!=='PASS'))process.exitCode=1;
