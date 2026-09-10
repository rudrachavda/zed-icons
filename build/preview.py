"""Render the README showcase images.

Writes two self-contained SVGs to docs/:
  tree.svg   a mock project tree, icons resolved through the theme's own
             association table so it matches exactly what Zed renders
  grid.svg   a sample of the pack

Both are composited from the shipped icons, so they can never drift from the
theme. Re-run after changing icons or associations.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ICONS = os.path.join(ROOT, 'icons')
DOCS = os.path.join(ROOT, 'docs')
THEME = json.load(open(os.path.join(
    ROOT, 'icon_themes', 'catppuccin-noctis-icons-theme.json')))['themes'][0]

BG, TEXT, DIM = '#1E1E2E', '#CDD6F4', '#7F849C'
MONO = ('ui-monospace,SFMono-Regular,Menlo,Consolas,'
        '&quot;Liberation Mono&quot;,monospace')

_SVG_OPEN = re.compile(r'<svg[^>]*>', re.S)
_VIEWBOX = re.compile(r'viewBox="([^"]+)"')


def load(rel):
    """Return (viewBox, inner markup) with ids namespaced to avoid collisions.

    44 icons carry gradient ids like `paint0_linear_1_2`; compositing them into
    one document would make those ids ambiguous, so each is prefixed.
    """
    raw = open(os.path.join(ICONS, rel)).read()
    vb = _VIEWBOX.search(raw)
    vb = vb.group(1) if vb else '0 0 24 24'
    inner = _SVG_OPEN.sub('', raw, count=1).replace('</svg>', '').strip()
    tag = re.sub(r'[^a-zA-Z0-9]', '', rel)
    for ident in set(re.findall(r'id="([^"]+)"', inner)):
        safe = f'{tag}_{ident}'
        inner = inner.replace(f'id="{ident}"', f'id="{safe}"')
        inner = inner.replace(f'url(#{ident})', f'url(#{safe})')
        inner = inner.replace(f'href="#{ident}"', f'href="#{safe}"')
    return vb, inner


def place(rel, x, y, size):
    vb, inner = load(rel)
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="{vb}" overflow="visible">{inner}</svg>')


def resolve(name, folder=False):
    """Mirror Zed's lookup: exact stem first, then longest matching suffix."""
    if folder:
        e = THEME['named_directory_icons'].get(name)
        p = e['collapsed'] if e else THEME['directory_icons']['collapsed']
        return p.replace('./icons/', '')
    icon = THEME['file_stems'].get(name)
    if not icon:
        for i, c in enumerate(name):
            if c == '.' and name[i + 1:] in THEME['file_suffixes']:
                icon = THEME['file_suffixes'][name[i + 1:]]
                break
    # Upstream Symbols ships 21 associations pointing at icons it never
    # defines (.gitignore -> "git" among them); those fall through to Zed's
    # built-in glyph, so treat them as unresolved here too.
    if not icon or icon not in THEME['file_icons']:
        return None
    return THEME['file_icons'][icon]['path'].replace('./icons/', '')


# ---------------------------------------------------------------- tree.svg
# (indent, name, is_folder) -- a realistic project, not a curated best-case.
TREE = [
    (0, 'src', True), (1, 'components', True), (2, 'Button.tsx', False),
    (2, 'Header.astro', False), (1, 'hooks', True), (2, 'useAuth.ts', False),
    (1, 'styles', True), (2, 'globals.css', False), (1, 'main.rs', False),
    (1, 'server.go', False), (1, 'schema.prisma', False),
    (0, 'tests', True), (1, 'app.test.ts', False), (1, 'conftest.py', False),
    (0, 'public', True), (1, 'logo.svg', False), (1, 'favicon.ico', False),
    (0, '.github', True), (1, 'workflows', True), (2, 'ci.yml', False),
    (0, 'Dockerfile', False), (0, 'docker-compose.yml', False),
    (0, 'package.json', False), (0, 'tsconfig.json', False),
    (0, 'components.json', False), (0, 'postcss.config.mjs', False),
    (0, 'Cargo.toml', False), (0, 'pyproject.toml', False),
    (0, '.env', False), (0, '.gitignore', False), (0, 'README.md', False),
    (0, 'LICENSE', False), (0, 'notes.txt', False), (0, 'CNAME', False),
]

ROW, PAD, ICON, INDENT = 26, 22, 17, 18
COLS = 2
per = -(-len(TREE) // COLS)
COLW = 290
W = PAD * 2 + COLW * COLS
H = PAD * 2 + ROW * per

parts = [f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>']
for i, (depth, name, is_dir) in enumerate(TREE):
    col, row = divmod(i, per)
    x = PAD + col * COLW + depth * INDENT
    y = PAD + row * ROW
    rel = resolve(name, is_dir)
    if rel:
        parts.append(place(rel, x, y + (ROW - ICON) // 2 - 1, ICON))
    parts.append(
        f'<text x="{x + ICON + 9}" y="{y + ROW // 2 + 4}" fill="'
        f'{TEXT if not is_dir else TEXT}" font-family="{MONO}" '
        f'font-size="12.5"{" font-weight=\"500\"" if is_dir else ""}>'
        f'{name}</text>')

os.makedirs(DOCS, exist_ok=True)
open(os.path.join(DOCS, 'tree.svg'), 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}" fill="none">{"".join(parts)}</svg>')

# ---------------------------------------------------------------- grid.svg
SAMPLE = """react-ts react vue svelte angular astro nuxt next solid qwik
python rust go java kotlin swift ruby php c cplus csharp haskell elixir
lua zig ocaml scala clojure erlang dart perl r julia nim crystal
ts js html css sass tailwind graphql prisma docker kubernetes terraform
git github gitlab npm yarn pnpm bun deno vite webpack rollup esbuild
eslint prettier biome jest vitest cypress playwright storybook figma
markdown json yaml toml xml database redis postgres mongo supabase firebase
aws azure vercel netlify cloudflare nginx claude cursor""".split()

avail = [n for n in SAMPLE if os.path.exists(os.path.join(ICONS, 'files', n + '.svg'))]
GC, GS, GP = 16, 30, 16
gw = GP * 2 + GC * GS
gh = GP * 2 + -(-len(avail) // GC) * GS
g = [f'<rect width="{gw}" height="{gh}" rx="10" fill="{BG}"/>']
for i, n in enumerate(avail):
    r, c = divmod(i, GC)
    g.append(place(f'files/{n}.svg', GP + c * GS + 4, GP + r * GS + 4, 22))
open(os.path.join(DOCS, 'grid.svg'), 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{gw}" height="{gh}" '
    f'viewBox="0 0 {gw} {gh}" fill="none">{"".join(g)}</svg>')

missing = [n for (d, n, f) in TREE if not resolve(n, f)]
print(f'docs/tree.svg  {W}x{H}  {len(TREE)} entries'
      f'{"  UNRESOLVED: " + str(missing) if missing else ""}')
print(f'docs/grid.svg  {gw}x{gh}  {len(avail)}/{len(SAMPLE)} sample icons present')
print('skipped (not in pack):', [n for n in SAMPLE if n not in avail])
