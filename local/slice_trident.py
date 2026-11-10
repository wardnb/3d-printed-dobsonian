#!/usr/bin/env python3
"""Headless OrcaSlicer for the Voron Trident (trident1) from this machine. Local-session tool; the cloud session
never needs it.

    local/slice_trident.py [--filament pla|asa] [--set key=value ...] [--upload FOLDER] [--out DIR] file.stl ...

Flattens the user presets (machine "Voron Trident 300 - trident1", process "0.20mm Standard @Voron - trident1",
filament "Generic PLA - trident1" / "Generic ASA - trident1") by resolving their `inherits` chains, because the
OrcaSlicer CLI cannot resolve inherits itself. Gotchas learned 2026-11-04: every JSON needs "from": "User" and
"version"; the machine and process must KEEP their `inherits` names (the CLI's compatibility check compares the
process's `compatible_printers` with the machine's inherited system name, not its own name); run under xvfb-run.
--tool N adds TOOL=N to the PRINT_START line (AFC lane; check `AFC_stepper laneN` material first).
--pa X adds PA=X to the PRINT_START line. PRINT_START only sets pressure advance when it is given PA=; without it
Klipper runs printer.cfg's global (0.037, stale, tuned for the old 0.6 nozzle: found 2026-11-10 after four fixture
prints). The value is per spool (Spoolman filament `extra.pa`; `python3 ~/trident/forge/forge.py spool`):
iSANMATE ASA gloss 0.066, Zyltech ASA matte 0.054, an unmeasured ASA 0.055 until calibrated.
Prints time + filament per part; --upload sends the G-code to Moonraker (upload only, never starts a print).
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.expanduser('~/.config/OrcaSlicer')
ORCA = os.path.expanduser('~/Applications/OrcaSlicer_Linux_AppImage_Ubuntu2404_V2.4.2.AppImage')
HOST = 'http://192.168.100.11'
MACHINE, PROCESS = 'Voron Trident 300 - trident1', '0.20mm Standard @Voron - trident1'
FILAMENTS = {'pla': 'Generic PLA - trident1', 'asa': 'Generic ASA - trident1'}
DROP = ('is_custom_defined', 'setting_id', 'filament_id', 'instantiation')


def index():
    idx = {}
    for f in glob.glob(f'{ROOT}/system/**/*.json', recursive=True) + glob.glob(f'{ROOT}/user/default/*/*.json'):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if isinstance(d, dict) and 'name' in d:
            idx.setdefault(d['name'], f)
    return idx


def flat(idx, name):
    d = json.load(open(idx[name]))
    parent = d.pop('inherits', None)
    base = flat(idx, parent) if parent else {}
    base.update(d)
    base['_parent'] = parent or base.get('_parent')
    return base


def write(idx, name, out, extra=None):
    d = flat(idx, name)
    parent = d.pop('_parent', None)
    for k in DROP:
        d.pop(k, None)
    if extra:
        d.update(extra)
    d['from'], d['version'] = 'User', '2.4.2.0'
    if parent:
        d['inherits'] = parent
    json.dump(d, open(out, 'w'), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stl', nargs='+')
    ap.add_argument('--filament', default='asa', choices=FILAMENTS)  # ASA default: PLA creeps under clamp loads
    ap.add_argument('--set', action='append', default=[], help='process override key=value (repeatable)')
    ap.add_argument('--fset', action='append', default=[], help='filament override key=value, e.g. filament_shrink=99.5%% (repeatable)')
    ap.add_argument('--out', default='.')
    ap.add_argument('--upload', help='Moonraker folder under gcodes/ to upload into')
    ap.add_argument('--tag', default='', help='suffix for the G-code name')
    ap.add_argument('--tool', type=int, help='AFC lane as Tn for PRINT_START (lane3/ASA = 2). Without it PRINT_START_STAGE2 runs T0 = lane1 PLA')
    ap.add_argument('--pa', type=float, help="pressure advance for PRINT_START (per spool; without it Klipper's stale global 0.037 runs)")
    a = ap.parse_args()
    extra = dict(kv.split('=', 1) for kv in a.set)
    fextra = {k: [v] for k, v in (kv.split('=', 1) for kv in a.fset)}  # filament values are one-element lists
    idx = index()
    tmp = tempfile.mkdtemp(prefix='slice_')
    write(idx, MACHINE, f'{tmp}/machine.json')
    write(idx, PROCESS, f'{tmp}/process.json', extra)
    write(idx, FILAMENTS[a.filament], f'{tmp}/filament.json', fextra)
    os.makedirs(a.out, exist_ok=True)
    for stl in a.stl:
        n = os.path.splitext(os.path.basename(stl))[0]
        od = f'{tmp}/{n}'
        os.makedirs(od)
        subprocess.run(['xvfb-run', '-a', ORCA, '--load-settings', f'{tmp}/machine.json;{tmp}/process.json',
                        '--load-filaments', f'{tmp}/filament.json', '--slice', '0', '--outputdir', od, stl],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
        res = json.load(open(f'{od}/result.json'))
        if res.get('return_code'):
            print(f'{n}: FAILED {res.get("error_string")}', file=sys.stderr)
            continue
        dst = os.path.join(a.out, f'{n}{a.tag}.gcode')
        shutil.move(f'{od}/plate_1.gcode', dst)
        if a.tool is not None or a.pa is not None:  # PRINT_START params Orca never emits: T{tool} and PA
            txt = open(dst).read()
            if a.tool is not None:  # the Trident's PRINT_START ends with T{tool}; Orca's single-filament slice never sets it
                txt = re.sub(r'^(PRINT_START[^\n]*?)(?: TOOL=\d+)?$', rf'\1 TOOL={a.tool}', txt, count=1, flags=re.M)
            if a.pa is not None:
                txt = re.sub(r'^(PRINT_START[^\n]*?)(?: PA=[\d.]+)?$', rf'\1 PA={a.pa:g}', txt, count=1, flags=re.M)
            open(dst, 'w').write(txt)
        info = {}
        for line in open(dst):
            if line.startswith('; estimated printing time (normal mode)'):
                info['time'] = line.split('=')[1].strip()
            elif line.startswith('; total filament used [g]'):
                info['g'] = line.split('=')[1].strip()
            if len(info) == 2:
                break
        print(f'{n:28s} {info.get("time", "?"):>12s}  {info.get("g", "?")} g')
        if a.upload:
            subprocess.run(['curl', '-s', '-m', '120', '-F', f'file=@{dst}', '-F', f'path={a.upload}',
                            f'{HOST}/server/files/upload'], stdout=subprocess.DEVNULL, check=True)
            print(f'  uploaded to gcodes/{a.upload}/')
    shutil.rmtree(tmp)


if __name__ == '__main__':
    main()
