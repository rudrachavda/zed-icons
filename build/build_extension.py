"""Option B: build a standalone Zed icon-theme extension.

Forks the Symbols pack into its own extension with a new id, retinted to
Catppuccin Mocha. Keeps Symbols' full association table (424 suffixes, 1562
stems, 601 named folders) rather than the thinner one in the VS Code theme.
"""
import json, os, shutil
import apply as A
import palette as P

DEST = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_EXT = os.path.expanduser(
    '~/Library/Application Support/Zed/extensions/installed/symbols')
THEME_NAME = 'Catppuccin Noctis Icons'
EXT_ID = 'catppuccin-noctis-icons'

os.makedirs(DEST, exist_ok=True)

# 1. icons, retinted from the pristine backup
per_icon, full, ex, inferred = A.retint(os.path.join(DEST, 'icons'))

# 2. icon theme json, carried over wholesale with only the identity renamed
src = json.load(open(os.path.join(P.SY, 'icon-theme.json')))
src['name'] = THEME_NAME
src['author'] = 'Symbols by Joan Garcia; Mocha retint'
for t in src['themes']:
    t['name'] = THEME_NAME
    print('  assoc:', P.apply_assoc(t))
os.makedirs(os.path.join(DEST, 'icon_themes'), exist_ok=True)
theme_path = os.path.join(DEST, 'icon_themes', f'{EXT_ID}-theme.json')
json.dump(src, open(theme_path, 'w'), indent=2)

# 3. manifest
open(os.path.join(DEST, 'extension.toml'), 'w').write(f'''id = "{EXT_ID}"
name = "{THEME_NAME}"
version = "0.1.0"
schema_version = 1
description = "Symbols file icons in the Catppuccin Mocha palette"
authors = ["Rudra Chavda"]
repository = "https://github.com/rudrachavda/zed-icons"
icon_themes = ["icon_themes/{EXT_ID}-theme.json"]
''')

t = src['themes'][0]
n_inf = len({k for k, sw in per_icon.items()
             if any(s in inferred for s, _ in sw)})


print(f'\nbuilt {DEST}')
for root, _, files in os.walk(DEST):
    if '.git' in root:
        continue
    rel = os.path.relpath(root, DEST)
    print(f'  {rel}/ -> {len(files)} files' if rel != '.' else
          f'  {", ".join(sorted(files))}')
print(f'\nassociations carried over: '
      f'{len(t["file_suffixes"])} suffixes, {len(t["file_stems"])} stems, '
      f'{len(t["named_directory_icons"])} folders')
