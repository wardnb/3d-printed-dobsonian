const { chromium } = require('/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad/npm/node_modules/playwright');
const path = require('path'), fs = require('fs');
const NM = '/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad/npm/node_modules/three';
const DIST = '/home/claude/dob16/dist';
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'] });
  for (const [w,h,scheme,tag,alt,view] of [[1400,900,'light','side',45,'side'],[1400,900,'light','three',20,'three']]) {
    const p = await b.newPage({ viewport:{width:w,height:h}, colorScheme: scheme });
    const errs=[]; p.on('console', m=>{ if(m.type()==='error') errs.push(m.text())}); p.on('pageerror', e=>errs.push(e.message));
    await p.route('**/*', r => {
      const u = r.request().url();
      if (u.startsWith('https://cdn.jsdelivr.net/npm/three@0.160.0/')) {
        const f = path.join(NM, u.replace('https://cdn.jsdelivr.net/npm/three@0.160.0/',''));
        return r.fulfill({ status:200, contentType:'application/javascript', body: fs.readFileSync(f) });
      }
      if (u.startsWith('http://local/')) {
        const f = path.join(DIST, u.replace('http://local/','') || 'index.html');
        const body = fs.readFileSync(f);
        const ct = f.endsWith('.html') ? 'text/html' : 'text/plain';
        const html = f.endsWith('.html') ? '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>'+body+'</body></html>' : body;
        return r.fulfill({ status:200, contentType: ct, body: html });
      }
      return r.abort();
    });
    await p.goto('http://local/index.html');
    await p.waitForTimeout(4000);
    await p.evaluate(([a,v,t]) => { const i=document.getElementById('alt'); i.value=a; i.dispatchEvent(new Event('input')); document.querySelector(`button.v[data-view="${v}"]`).click(); if(t){const r=document.querySelector('input[name="spider"][value="wire"]'); r.checked=true; r.dispatchEvent(new Event('change'));} }, [alt, view, false]);
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad/shot_${tag}.png`, fullPage: tag==='phone' });
    console.log(tag, 'errors:', errs.slice(0,5));
    await p.close();
  }
  await b.close();
})();
