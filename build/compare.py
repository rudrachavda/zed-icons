"""Compare the built extension against the VS Code Catppuccin Noctis pack.

Buckets every icon as: only in Noctis, only in ours, redrawn (same name,
different geometry), recolored differently, or an exact match.
"""
import os, re, collections
import palette as P

_HERE = os.path.dirname(os.path.abspath(__file__))
OURS = os.path.join(os.path.dirname(_HERE), 'icons')
CN_ROOT = os.path.join(_HERE, 'upstream', 'noctis')

strip = lambda s: re.sub(r'\s+', '', re.sub(
    r'(fill|stroke)="[^"]*"', '', re.sub(r'#[0-9a-fA-F]{6}', '', s)))
colors = lambda s: collections.Counter(c.upper() for c in re.findall(
    r'#[0-9a-fA-F]{6}', s))

svgs = lambda d: {f[:-4] for f in os.listdir(d)
                  if f.endswith('.svg')} if os.path.isdir(d) else set()

report = {}
for sub in ('files', 'folders'):
    ours_d, cn_d = os.path.join(OURS, sub), os.path.join(CN_ROOT, sub)
    ours, cn = svgs(ours_d), svgs(cn_d)
    b = {'only_noctis': sorted(cn - ours), 'only_ours': sorted(ours - cn),
         'redrawn': [], 'recolored': [], 'exact': []}
    for n in sorted(ours & cn):
        a = open(os.path.join(ours_d, n + '.svg')).read()
        c = open(os.path.join(cn_d, n + '.svg')).read()
        if strip(a) != strip(c):
            b['redrawn'].append(n)
        elif colors(a) != colors(c):
            diff = sorted(set(colors(a)) ^ set(colors(c)))
            b['recolored'].append((n, diff))
        else:
            b['exact'].append(n)
    report[sub] = b

for sub, b in report.items():
    tot = sum(len(v) for v in b.values())
    print(f'\n{"="*66}\n{sub.upper()}  ({tot} distinct icon names across both packs)\n{"="*66}')
    print(f'  exact match          {len(b["exact"]):4}')
    print(f'  recolored            {len(b["recolored"]):4}')
    print(f'  redrawn (diff art)   {len(b["redrawn"]):4}')
    print(f'  only in ours         {len(b["only_ours"]):4}')
    print(f'  only in Noctis       {len(b["only_noctis"]):4}  <- genuinely missing')
    if b['only_noctis']:
        print(f'\n  MISSING: {", ".join(b["only_noctis"])}')
    if b['redrawn']:
        print(f'\n  REDRAWN ({len(b["redrawn"])}): {", ".join(b["redrawn"])}')
    if b['recolored']:
        print(f'\n  RECOLORED ({len(b["recolored"])}):')
        for n, d in b['recolored']:
            print(f'    {n:24} {" ".join(d)}')

print(f'\n{"="*66}')
allo = sum(len(b['only_ours']) for b in report.values())
allm = sum(len(b['only_noctis']) for b in report.values())
print(f'net: we ship {allo} icons Noctis lacks, and lack {allm} it has')
