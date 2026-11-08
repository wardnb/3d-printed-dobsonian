// Close-up shots of the viewer with labels/beam off, camera set directly (exposes window.__cam by patching the page).
const { chromium } = require('/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad/npm/node_modules/playwright');
const path = require('path'), fs = require('fs');
const NM = '/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad/npm/node_modules/three';
const DIST = '/home/claude/3d-printed-dobsonian/goto-rebuild/dist';
const OUT = '/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad';
const SHOTS = JSON.parse(process.argv[2] || '[]');   // [{tag, alt, pos:[x,y,z], tgt:[x,y,z]}]
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport:{width:1400,height:900}, colorScheme: 'light' });
  const errs=[]; p.on('pageerror', e=>errs.push(e.message));
  await p.route('**/*', r => {
    const u = r.request().url();
    if (u.startsWith('https://cdn.jsdelivr.net/npm/three@0.160.0/')) {
      const f = path.join(NM, u.replace('https://cdn.jsdelivr.net/npm/three@0.160.0/',''));
      return r.fulfill({ status:200, contentType:'application/javascript', body: fs.readFileSync(f) });
    }
    if (u.startsWith('http://local/')) {
      const f = path.join(DIST, u.replace('http://local/','') || 'index.html');
      let body = fs.readFileSync(f, 'utf8');
      const ct = f.endsWith('.html') ? 'text/html' : 'text/plain';
      if (f.endsWith('.html')) {
        body = body.replace('setView("three", true);', 'setView("three", true); window.__cam = { camera, controls, scene, pivot, THREE };');
        body = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + body + '</body></html>';
      }
      return r.fulfill({ status:200, contentType: ct, body });
    }
    return r.abort();
  });
  await p.goto('http://local/index.html');
  await p.waitForTimeout(5000);
  await p.evaluate(() => { for (const id of ['beam','tags']) { const c=document.getElementById(id); c.checked=false; c.dispatchEvent(new Event('change')); } });
  for (const s of SHOTS) {
    await p.evaluate((s) => { const i=document.getElementById('alt'); i.value=s.alt; i.dispatchEvent(new Event('input'));
      const {camera, controls, scene} = window.__cam; const THREE = window.__cam.THREE; if (s.hideTube) window.__cam.pivot.visible=false; if (s.view) { document.querySelector(`button.v[data-view="${s.view}"]`).click(); return; }
      if (s.zoom) { const d = camera.position.clone().sub(controls.target).multiplyScalar(s.zoom); if (s.shift) controls.target.add(new THREE.Vector3(...s.shift)); camera.position.copy(controls.target).add(d); controls.update(); return; } if (s.double) scene.traverse(o=>{ if(o.isMesh){ o.material.side = 2; }}); camera.position.set(...s.pos); controls.target.set(...s.tgt); controls.update(); }, s);
    await p.waitForTimeout(s.view ? 3000 : 1200);
    await p.screenshot({ path: `${OUT}/shot_${s.tag}.png`, clip: {x:40, y:155, width:965, height:665} });
  }
  console.log('errors:', errs.slice(0,5));
  await b.close();
})();
