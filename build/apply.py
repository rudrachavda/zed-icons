"""Retint the Symbols icon pack to Catppuccin Mocha.

Default target is the installed Zed extension (option A, a live preview).
Pass --out DIR to write the retinted icons somewhere else instead, which is how
the standalone extension in option B is built.

Restore the installed pack with: python3 apply.py --restore
"""
import os, re, shutil, sys, collections
import palette as P

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.expanduser(
    '~/Library/Application Support/Zed/extensions/installed/symbols/icons')
BACKUP = os.path.join(HERE, 'upstream', 'symbols')


THEME_JSON = os.path.join(os.path.dirname(ICONS), 'icon_themes',
                          'symbols-icon-theme.json')
THEME_BACKUP = os.path.join(HERE, 'upstream', 'symbols', 'icon-theme.json')


def patch_live_theme():
    """Apply the association overrides to the installed Symbols theme JSON."""
    import json
    import palette as P
    if not os.path.exists(THEME_BACKUP):
        shutil.copy(THEME_JSON, THEME_BACKUP)
    # Always patch from the pristine copy so reruns stay idempotent.
    data = json.load(open(THEME_BACKUP))
    changed = {}
    for t in data['themes']:
        changed = P.apply_assoc(t)
    json.dump(data, open(THEME_JSON, 'w'), indent=2)
    return changed


def restore():
    for sub in ('files', 'folders'):
        dst = os.path.join(ICONS, sub)
        shutil.rmtree(dst)
        shutil.copytree(os.path.join(BACKUP, sub), dst)
    if os.path.exists(THEME_BACKUP):
        shutil.copy(THEME_BACKUP, THEME_JSON)
    print('restored pristine Symbols icons and theme json')


def retint(out_dir, quiet=False):
    """Retint from the pristine backup into out_dir. Idempotent."""
    full, ex, inferred = P.build()
    stats = collections.Counter()
    per_icon = {}

    for sub in ('files', 'folders'):
        src_dir = os.path.join(BACKUP, sub)
        if not os.path.isdir(src_dir):
            continue
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)
        for fn in sorted(os.listdir(src_dir)):
            if not fn.endswith('.svg'):
                continue
            name = fn[:-4]
            noctis = os.path.join(P.CN, fn)
            if name in P.ADOPT_NOCTIS and os.path.exists(noctis):
                open(os.path.join(out_dir, sub, fn), 'w').write(open(noctis).read())
                stats['adopted'] += 1
                continue
            text = open(os.path.join(src_dir, fn)).read()
            new, swaps = P.remap(text, full, name=name, guessed=inferred)
            new = P.post_process(new, name)
            open(os.path.join(out_dir, sub, fn), 'w').write(new)
            if swaps:
                stats['files'] += 1
                stats['swaps'] += len(swaps)
                for s, _ in swaps:
                    stats['inferred' if s in inferred else 'extracted'] += 1
                per_icon[f'{sub}/{fn[:-4]}'] = swaps

    if not quiet:
        print(f'adopted {stats["adopted"]} icons verbatim from Noctis')
        print(f'retinted {stats["files"]} svg files, {stats["swaps"]} swaps')
        print(f'  extracted from Noctis: {stats["extracted"]}')
        print(f'  rule-derived:          {stats["inferred"]}')
    return per_icon, full, ex, inferred


if __name__ == '__main__':
    if '--restore' in sys.argv:
        restore()
        raise SystemExit

    if not os.path.exists(BACKUP):
        shutil.copytree(ICONS, BACKUP)
        print(f'backed up originals -> {BACKUP}')

    out = ICONS
    if '--out' in sys.argv:
        out = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
        os.makedirs(out, exist_ok=True)
    print(f'target: {out}')
    retint(out)
    if out == ICONS:
        print('theme json assoc:', patch_live_theme())

    # Nothing dark should survive on a #1E1E2E tree.
    dark = []
    for sub in ('files', 'folders'):
        d = os.path.join(out, sub)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.svg'):
                continue
            t = open(os.path.join(d, fn)).read()
            for c in set(P._HEX6.findall(t)):
                if P.lch(c)[0] < 0.45:
                    dark.append(f'{fn[:-4]}:{c}')
            if re.search(r'(fill|stroke)="(black)"', t):
                dark.append(f'{fn[:-4]}:black')
    print(f'\nremaining dark colors: {len(dark)}')
    for d in dark:
        print(f'  {d}')
