// Product-style render of the viewer model: PBR materials by part name, image-based lighting, soft shadows.
// usage: node tools/render_pbr.js '[{"tag":"hero","alt":45,"pos":[2300,1650,2500],"tgt":[0,700,-150],"w":1600,"h":1000}]'
const { chromium } = require('/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad/npm/node_modules/playwright');
const path = require('path'), fs = require('fs');
const NM = '/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad/npm/node_modules/three';
const DIST = '/home/claude/3d-printed-dobsonian/goto-rebuild/dist';
const OUT = process.env.OUT || '/tmp/claude-0/-home-claude/1cb5d628-4a67-5c85-b2f5-b06b9468717d/scratchpad';
const SHOTS = JSON.parse(process.argv[2] || '[]');
const W = (SHOTS[0] && SHOTS[0].w) || 1600, H = (SHOTS[0] && SHOTS[0].h) || 1000;
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2, colorScheme: 'light' });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.route('**/*', r => {
    const u = r.request().url();
    if (u.startsWith('https://cdn.jsdelivr.net/npm/three@0.160.0/')) {
      const f = path.join(NM, u.replace('https://cdn.jsdelivr.net/npm/three@0.160.0/', ''));
      return r.fulfill({ status: 200, contentType: 'application/javascript', body: fs.readFileSync(f) });
    }
    if (u.startsWith('http://local/')) {
      const f = path.join(DIST, u.replace('http://local/', '') || 'index.html');
      let body = fs.readFileSync(f, 'utf8');
      const ct = f.endsWith('.html') ? 'text/html' : 'text/plain';
      if (f.endsWith('.html')) {
        body = body.replace('setView("three", true);', 'setView("three", true); window.__cam = { camera, controls, scene, pivot, THREE, renderer, base, tube, floor, beam, key, fillLight };');
        body = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + body + '</body></html>';
      }
      return r.fulfill({ status: 200, contentType: ct, body });
    }
    return r.abort();
  });
  await p.goto('http://local/index.html');
  await p.waitForTimeout(6000);
  // beautify
  const berr = await p.evaluate(async () => { try {
    const { scene, THREE, renderer, floor, beam, key, fillLight, camera } = window.__cam;
    const { RoomEnvironment } = await import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/environments/RoomEnvironment.js');
    const cv = renderer.domElement; const hostEl = cv.parentElement;
    let top = hostEl; while (top.parentElement !== document.body) top = top.parentElement;
    Array.from(document.body.children).forEach(el => { if (el !== top) el.style.display = 'none'; });
    for (let el = hostEl; el; el = el.parentElement === document.body ? null : el.parentElement) {
      Object.assign(el.style, { position: 'fixed', left: '0', top: '0', width: '100vw', height: '100vh', margin: '0', padding: '0', maxWidth: 'none', display: 'block', border: '0', borderRadius: '0' });
      Array.from(el.children).forEach(ch => { if (ch !== cv && !ch.contains(cv)) ch.style.display = 'none'; });
    }
    document.body.style.margin = '0';
    await new Promise(r => setTimeout(r, 300));
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight, false);
    camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix();
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    // backdrop: soft studio gradient
    const c = document.createElement('canvas'); c.width = 16; c.height = 512; const g = c.getContext('2d');
    const gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, '#2a2f3a'); gr.addColorStop(0.55, '#4a5160'); gr.addColorStop(1, '#8b8f98');
    g.fillStyle = gr; g.fillRect(0, 0, 16, 512);
    const bg = new THREE.CanvasTexture(c); bg.colorSpace = THREE.SRGBColorSpace; scene.background = bg;
    floor.visible = false; beam.visible = false;
    const lab = document.getElementById('labels'); if (lab) lab.hidden = true;
    scene.traverse(o => { if (o.isSprite || (o.isCSS2DObject)) o.visible = false; });
    // ground: wide matte disc receiving shadows
    const gnd = new THREE.Mesh(new THREE.CircleGeometry(9000, 96), new THREE.MeshStandardMaterial({ color: 0x484c54, roughness: 0.95, metalness: 0 }));
    gnd.rotation.x = -Math.PI / 2; gnd.position.y = -1; gnd.receiveShadow = true; scene.add(gnd);
    // lights
    scene.children.filter(o => o.isHemisphereLight).forEach(o => o.intensity = 0.35);
    key.intensity = 2.6; key.color.set(0xfff1e0); key.position.set(2600, 3200, 1800); key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0005; key.shadow.normalBias = 2;
    const sc = key.shadow.camera; sc.left = -2200; sc.right = 2200; sc.top = 2600; sc.bottom = -600; sc.near = 500; sc.far = 9000; sc.updateProjectionMatrix();
    fillLight.intensity = 0.6; fillLight.color.set(0xcfd8ff);
    const rim = new THREE.DirectionalLight(0xffffff, 1.2); rim.position.set(-1800, 1500, -2600); scene.add(rim);
    // procedural birch texture
    const wc = document.createElement('canvas'); wc.width = 1024; wc.height = 1024; const w = wc.getContext('2d');
    w.fillStyle = '#e4d2ad'; w.fillRect(0, 0, 1024, 1024);
    for (let i = 0; i < 1400; i++) { w.strokeStyle = `rgba(${170 + Math.random() * 50 | 0},${135 + Math.random() * 40 | 0},${85 + Math.random() * 30 | 0},${0.06 + Math.random() * 0.10})`; w.lineWidth = 1 + Math.random() * 3; w.beginPath(); const y = Math.random() * 1024; w.moveTo(0, y); w.bezierCurveTo(300, y + (Math.random() - 0.5) * 40, 700, y + (Math.random() - 0.5) * 40, 1024, y + (Math.random() - 0.5) * 20); w.stroke(); }
    const wood = new THREE.CanvasTexture(wc); wood.colorSpace = THREE.SRGBColorSpace; wood.wrapS = wood.wrapT = THREE.RepeatWrapping; wood.repeat.set(0.002, 0.002);
    const M = {
      birch: () => new THREE.MeshStandardMaterial({ map: wood, color: 0xf3ead8, roughness: 0.5, metalness: 0 }),
      anod: () => new THREE.MeshStandardMaterial({ color: 0x15161a, roughness: 0.42, metalness: 0.75 }),     // bead-blast black Type II
      alu: () => new THREE.MeshStandardMaterial({ color: 0xc9ccd1, roughness: 0.35, metalness: 0.9 }),      // as-milled / clear
      steel: () => new THREE.MeshStandardMaterial({ color: 0xb8bcc2, roughness: 0.25, metalness: 1.0 }),
      carbon: () => new THREE.MeshPhysicalMaterial({ color: 0x0b0b0d, roughness: 0.22, metalness: 0.1, clearcoat: 0.9, clearcoatRoughness: 0.12 }),
      rubber: () => new THREE.MeshStandardMaterial({ color: 0x141414, roughness: 0.85, metalness: 0 }),
      mirror: () => new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.02, metalness: 1.0, envMapIntensity: 1.6 }),
      glassy: () => new THREE.MeshPhysicalMaterial({ color: 0xdde6f0, roughness: 0.05, metalness: 0.0, transmission: 0.0, clearcoat: 1 }),
      plastic: () => new THREE.MeshStandardMaterial({ color: 0x1c1d21, roughness: 0.5, metalness: 0.05 }),
      ptfe: () => new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: 0.6, metalness: 0 }),
      electronics: () => new THREE.MeshStandardMaterial({ color: 0x25272c, roughness: 0.55, metalness: 0.2 }),
    };
    const birchNames = /bearing|mirror_cage$|rocker|ground|feet|wall|floor|ends/;
    const anodNames = /block|arm_plate|base_plate|bracket|cage_struts|diagonal_nodes|finder_cradle|finder_adjuster|focuser_board|board_rails|cell_frame|cell_triangles|cell_edge|cell_guard|socket_blocks|pair_blocks|plugs|collars|gib|flange_plates|lateral_tabs|spring_block|tail_block|pivot_housing|secondary_body|secondary_carrier|quad_hub|track$|az_track|enc_plate/;
    const aluNames = /cage_ring|mirror_cage_tubes|diagonal_tubes|cell_pivots|az_enc_disc|pulley|pinion_hub|jackshaft|standoff|spacer/;
    const steelNames = /screw|bolt|nut|axle|dowel|rod|stud|head_screws|vanes|rollers|bearing_A|bearing_B|collimation|spring$|pins/;
    const carbonNames = /truss_poles/;
    const rubberNames = /belt|cam_lever|knobs|track_drive|track_plain|cell_pads/;
    const mirrorNames = /primary_mirror|secondary_mirror/;
    const elecNames = /motor|electronics|enc_reader|fan|waypoint|feather_touch|eyepiece|baffle|enc_ring|enc_boss/;
    scene.traverse(m => {
      if (!m.isMesh || m === gnd) return;
      const n = m.name || (m.parent && m.parent.name) || '';
      let mat;
      if (mirrorNames.test(n)) mat = M.mirror();
      else if (carbonNames.test(n)) mat = M.carbon();
      else if (rubberNames.test(n)) mat = M.rubber();
      else if (elecNames.test(n)) mat = M.electronics();
      else if (steelNames.test(n)) mat = M.steel();
      else if (birchNames.test(n)) mat = M.birch();
      else if (aluNames.test(n)) mat = M.alu();
      else if (anodNames.test(n)) mat = M.anod();
      else {
        const c = m.material.color; const isAlu = Math.abs(c.r - c.b) < 0.08 && c.r > 0.45 && c.r < 0.8;
        mat = c.r > 0.6 && c.g > 0.4 && c.b < 0.35 ? M.birch() : isAlu ? M.anod() : c.r < 0.1 ? M.plastic() : M.alu();
      }
      mat.side = THREE.DoubleSide; m.material = mat; m.castShadow = true; m.receiveShadow = true;
    });
    window.__ready = true; return null; } catch (e) { return String(e && e.stack || e); } });
  console.log('beautify:', berr);
  await p.waitForTimeout(1500);
  for (const s of SHOTS) {
    await p.evaluate((s) => {
      const { camera, controls, pivot, THREE } = window.__cam;
      pivot.rotation.x = THREE.MathUtils.degToRad(s.alt == null ? 45 : s.alt);
      if (s.fov) { camera.fov = s.fov; camera.updateProjectionMatrix(); }
      camera.position.set(...s.pos); controls.target.set(...s.tgt); controls.update();
    }, s);
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `${OUT}/render_${s.tag}.png`, timeout: 400000 });
    console.log('wrote', `${OUT}/render_${s.tag}.png`);
  }
  console.log('errors:', errs.slice(0, 8));
  await b.close();
})();
