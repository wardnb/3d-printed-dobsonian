import json, shutil, pathlib
root = pathlib.Path(__file__).parent
src = (root / "site" / "index.html").read_text()
params = (root / "out" / "params.json").read_text()
dist = root / "dist"; dist.mkdir(exist_ok=True)
(dist / "index.html").write_text(src.replace("__PARAMS__", json.dumps(json.loads(params))))
import base64
for f in ("base.glb", "tube.glb", "truss_pairs.glb", "truss_zigzag.glb", "spider_curved.glb", "spider_wire.glb", "spider_quad.glb"):
    (dist / (f + ".txt")).write_text(base64.b64encode((root / "out" / f).read_bytes()).decode())
print("built", list(p.name for p in dist.iterdir()))
