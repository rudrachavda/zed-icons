"""Derive a Tailwind->Catppuccin Mocha map for the Symbols icon pack.

Two sources:
  1. EXTRACTED - diffed from the user's installed Catppuccin Noctis VS Code
     extension, for icons whose geometry is identical to Symbols'. Ground truth.
  2. INFERRED  - a hue-matching rule for colors Noctis never touched.

The inference rule maps to Catppuccin *accents* by hue while ignoring source
lightness, because that is demonstrably what Noctis itself does: it lifts dark
Tailwind colors (#7F1D1D, #075985, #334155) up to mid pastels rather than
matching them to Catppuccin's dark surface ramp. Nearest-neighbour in Lab space
would instead preserve darkness, reintroducing the exact problem we are fixing.
"""
import json, math, os, re, collections

_HERE = os.path.dirname(os.path.abspath(__file__))
# Upstream sources are vendored under build/upstream/ so the build never
# depends on Zed's managed copy or on a VS Code extension being installed.
SY = os.path.join(_HERE, 'upstream', 'symbols')
CN = os.path.join(_HERE, 'upstream', 'noctis', 'files')
# Pristine copy of the Symbols pack, made by apply.py before it retints.
# Every read of the "original" palette must go through here once it exists.
_BACKUP = SY   # the vendored copy is the pristine source
_orig = lambda sub: os.path.join(
    _BACKUP if os.path.isdir(_BACKUP) else SY, sub)

MOCHA_ACCENTS = {
    'rosewater': '#F5E0DC', 'flamingo': '#F2CDCD', 'pink': '#F5C2E7',
    'mauve': '#CBA6F7', 'red': '#F38BA8', 'maroon': '#EBA0AC',
    'peach': '#FAB387', 'yellow': '#F9E2AF', 'green': '#A6E3A1',
    'teal': '#94E2D5', 'sky': '#89DCEB', 'sapphire': '#74C7EC',
    'blue': '#89B4FA', 'lavender': '#B4BEFE',
}
# Greys, light -> dark. Achromatic sources map here by lightness.
MOCHA_GREYS = [
    ('text', '#CDD6F4'), ('subtext1', '#BAC2DE'), ('subtext0', '#A6ADC8'),
    ('overlay2', '#9399B2'), ('overlay1', '#7F849C'), ('overlay0', '#6C7086'),
    ('surface2', '#585B70'),
]


def srgb_to_oklab(hex_):
    h = hex_.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def lch(hex_):
    L, a, b = srgb_to_oklab(hex_)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


# Accents Noctis actually targets. rosewater/flamingo/pink/maroon never appear
# as destinations in the extracted map - sources at those hues (e.g. #F472B6,
# H=350) resolve to red instead, so including them would over-desaturate.
TARGET_ACCENTS = ['red', 'peach', 'yellow', 'green', 'teal',
                  'sky', 'sapphire', 'blue', 'mauve', 'lavender']

DARK_L = 0.52      # below this, Noctis discards hue and goes grey
FLAT_C = 0.05      # below this, treat as achromatic

_ACC_LCH = {n: lch(MOCHA_ACCENTS[n]) for n in TARGET_ACCENTS}
_GREY_L = [(n, v, lch(v)[0]) for n, v in MOCHA_GREYS]


def infer(hex_):
    """Map an arbitrary source color onto the Mocha palette.

    Derived by fitting the 21 high-confidence extracted mappings. Noctis
    normalises to a mid-lightness pastel: dark colors collapse to overlay1
    regardless of hue (#7E22CE, a saturated purple at L=0.50, becomes grey),
    near-neutrals ride the grey ramp, and everything else keeps its hue.
    """
    L, C, H = lch(hex_)
    if L < DARK_L:
        return '#7F849C'                             # overlay1
    if C < FLAT_C:
        return min(_GREY_L, key=lambda g: abs(g[2] - L))[1]
    best = min(_ACC_LCH.items(),
               key=lambda kv: min(abs(kv[1][2] - H), 360 - abs(kv[1][2] - H)))
    return MOCHA_ACCENTS[best[0]]


# Colors that never appear as hex and so were missed by a hex-only pass.
# `black` is the worst offender: on Zed's #1E1E2E tree it is near-invisible.
NAMED_COLORS = {'black': '#7F849C', 'white': '#CDD6F4'}

# Noctis treats #475569 per-icon (kept in editorconfig, lifted to #7F849C in
# keystatic). A global map can't express that, so we take the lifted value --
# the whole point of this retint is fewer dark icons.
OVERRIDES = {'#475569': '#7F849C'}

_ACC_NAME = {v: k for k, v in MOCHA_ACCENTS.items()}
_GREY_NAME = {v: n for n, v in MOCHA_GREYS}


def explain(hex_):
    """Return (destination, human reason) for a rule-derived color."""
    L, C, H = lch(hex_)
    if L < DARK_L:
        return '#7F849C', f'lightness {L:.2f} is below {DARK_L} — too dark to ' \
                          f'stay, so hue is dropped for overlay1 grey'
    if C < FLAT_C:
        dst = min(_GREY_L, key=lambda g: abs(g[2] - L))[1]
        return dst, f'near-neutral (chroma {C:.03f}) — matched to ' \
                    f'{_GREY_NAME[dst]} on the grey ramp by lightness'
    best = min(_ACC_LCH.items(),
               key=lambda kv: min(abs(kv[1][2] - H), 360 - abs(kv[1][2] - H)))
    dst = MOCHA_ACCENTS[best[0]]
    return dst, f'hue {H:.0f}° is closest to {best[0]}'


COLOR_ATTR = re.compile(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,8})"')
_HEX6 = re.compile(r'#[0-9a-fA-F]{6}\b')
_NAMED = re.compile(r'\b(fill|stroke)="(black|white)"')
_RGB_PCT = re.compile(r'\b(fill|stroke):rgb\(([\d.]+)%,\s*([\d.]+)%,\s*([\d.]+)%\)')


# Complex multi-color logos that Noctis leaves alone: it preserves every brand
# hex and converts only the white/black keywords. Verified by diffing these
# against pristine Symbols -- the only additions on the Noctis side were
# #CDD6F4 (from white) and #11111B (from black).
BRAND_KEEP = {'expressive-code', 'jenkins', 'earthfile', 'lunaria', 'pug'}

# Icons where Noctis's own version is preferred outright -- its artwork and its
# colors, copied verbatim rather than retinted. Chosen by eye from the
# side-by-side comparison. Five of these use #11111B, which is fractionally
# darker than the file tree; that is Noctis's deliberate two-tone look, with a
# light #CDD6F4 shape carrying the icon, and it was picked knowing that.
ADOPT_NOCTIS = {'python', 'visual-studio', 'crystal', 'svelte', 'svelte-ts',
                'gleam', 'bun', 'vite'}

# Filename/extension routing changed to match Noctis. Every target already
# exists in the Symbols pack, so nothing new has to be imported.
SUFFIX_OVERRIDES = {
    'css': 'brackets-sky',
    'txt': 'document',
    # All three are unmapped in both packs and fall through to Zed's default.
    # Their contents are JSON, so they take the JSON icon.
    'tsbuildinfo': 'brackets-yellow',
    'jsonc': 'brackets-yellow',
    'json5': 'brackets-yellow',
}
STEM_OVERRIDES = {
    'CNAME': 'document',
    # The shadcn logo is a dull #6C7086 grey and reads worse than plain JSON
    # braces. Tool configs with real logos (tsconfig, vite, eslint, ...) keep
    # theirs -- this is the only *.json stem that isn't one of those.
    'components.json': 'brackets-yellow',
    'COMPONENTS.JSON': 'brackets-yellow',
    # Noctis has no postcss.config.mjs rule, so it falls back to the yellow js
    # lettermark. Matching that here. The other 11 .mjs configs Symbols knows
    # and Noctis doesn't (tailwind, rspack, oxlint, ...) keep their tool logos.
    'postcss.config.mjs': 'js',
    'POSTCSS.CONFIG.MJS': 'js',
}

# Post-retint tweaks, applied by name after the color pass so they don't depend
# on what the color map happened to do.
ICON_RECOLOR = {
    # .d.ts / .d.cts / .d.mts read as TypeScript, so match the blue ts icon
    # rather than sitting alone in green.
    'ts-types': {'#A6E3A1': '#89B4FA'},
}

# Geometry is left exactly as upstream draws it, so every glyph matches
# Catppuccin Noctis. The document icon briefly carried a 2-unit corner radius
# here; that was reverted for consistency. The mechanism stays because it is
# load-bearing for post_process and errors loudly if a target path ever moves.
SHAPE_TWEAKS = {}


def post_process(text, name):
    """Apply shape and color tweaks that are keyed to a specific icon."""
    for src, dst in ICON_RECOLOR.get(name, {}).items():
        text = text.replace(src, dst).replace(src.lower(), dst)
    for old, new in SHAPE_TWEAKS.get(name, []):
        if old not in text:
            raise ValueError(f'{name}: shape tweak target not found - '
                             f'upstream artwork changed, tweak needs revisiting')
        text = text.replace(old, new)
    return text
# Applied to every stem currently pointing at docker-pink (the 34
# docker-compose.* variants) rather than listing them out.
STEM_RETARGET = {'docker-pink': 'docker'}


# Zed's icon-theme format has NO way to override the fallback icon: every
# published schema (v0.1.0 through v0.3.0, the newest) defines the same 8
# properties and none is a default, and setting file_icons.file / .default was
# tested and ignored. Unmapped files always get Zed's bundled file.svg.
#
# So the only lever is mapping extensions explicitly. These fill gaps found by
# scanning real projects -- they are applied ONLY where no rule already exists,
# so upstream Symbols mappings are never clobbered.
SUFFIX_FALLBACKS = {
    # C/C++ headers and templates
    **{e: 'cplus' for e in ('hpp', 'hxx', 'h++', 'ipp', 'inl', 'ixx', 'tpp',
                            'cppm', 'pch', 'hh', 'modulemap')},
    'm': 'c',                      # Objective-C
    **{e: 'python' for e in ('pyc', 'pyo', 'pyd')},
    **{e: 'perl' for e in ('pl', 'pm')},
    **{e: 'java' for e in ('class', 'jar')},
    **{e: 'compressed' for e in ('zst', 'xz', 'lz4', 'br', 'tgz')},
    # build and project config
    **{e: 'gear' for e in ('xcconfig', 'xcscheme', 'pbxproj', 'xcprivacy',
                           'xcworkspacedata', 'entitlements', 'am', 'ac',
                           'm4', 'meson', 'build', 'in', 'rc')},
    **{e: 'code-gray' for e in ('s', 'asm')},
}
# Genuinely generic - the document glyph, same as .txt uses.
_GENERIC = ('properties', 'map', 'table', 'log', 'old', 'natvis', 'bin', 'dat',
            'out', 'o', 'a', 'so', 'dylib', 'lib', 'obj', 'd', 'def', 'sym',
            'manifest', 'spec', 'list', 'cfg', 'conf', 'nfo', 'todo', 'rst',
            'inc', 'jam', 'probe', 're', 'patch', 'orig', 'bak', 'tmp')
SUFFIX_FALLBACKS.update({e: 'document' for e in _GENERIC})

# Zed matches suffixes case-sensitively -- upstream Symbols carries .GITIGNORE
# alongside .gitignore for exactly this reason. `.S` (assembly) is the common
# real-world case, but cover the whole set rather than special-casing it.
SUFFIX_FALLBACKS.update({e.upper(): i for e, i in list(SUFFIX_FALLBACKS.items())
                         if e.upper() != e})


def apply_assoc(theme):
    """Rewrite icon associations in-place. Returns a summary of what changed."""
    changed = {}
    # Which key Zed reads for the fallback is not documented: the published
    # v0.3.0 schema lists no default at all, yet material-icon-theme and
    # monospace-icon-theme both set `file`. Setting both candidates -- extra
    # file_icons keys are inert (the theme already carries 21 unreferenced
    # ones), so the only cost is two spare entries.
    # Drop the file/default keys - tested against Zed 1.16.2 and ignored.
    for dead in ('file', 'default'):
        theme['file_icons'].pop(dead, None)
    added = 0
    for suf, icon in SUFFIX_FALLBACKS.items():
        if suf not in theme['file_suffixes'] and icon in theme['file_icons']:
            theme['file_suffixes'][suf] = icon
            added += 1
    if added:
        changed[f'{added} gap suffixes'] = ('(unmapped)', 'filled')
    # A missing entry means "add it", not "skip it" -- .tsbuildinfo is unmapped
    # upstream and still needs setting.
    for suf, icon in SUFFIX_OVERRIDES.items():
        if theme['file_suffixes'].get(suf) != icon:
            changed[f'.{suf}'] = (theme['file_suffixes'].get(suf), icon)
            theme['file_suffixes'][suf] = icon
    for stem, icon in STEM_OVERRIDES.items():
        if theme['file_stems'].get(stem) != icon:
            changed[stem] = (theme['file_stems'].get(stem), icon)
            theme['file_stems'][stem] = icon
    n = 0
    for stem, icon in list(theme['file_stems'].items()):
        if icon in STEM_RETARGET:
            theme['file_stems'][stem] = STEM_RETARGET[icon]
            n += 1
    if n:
        changed[f'{n} stems'] = tuple(next(iter(STEM_RETARGET.items())))
    return changed

# hugo looks like a brand logo but Noctis does recolor it, so it is not in
# BRAND_KEEP. #DB2777 can't go in OVERRIDES because vanilla-extract keeps it.
PER_ICON = {'hugo': {'#DB2777': '#EBA0AC'}}


def remap(text, cmap, name=None, guessed=None):
    """Rewrite every color form Symbols uses. Returns (new_text, swaps).

    Covers hex, the named `black`/`white` keywords, and the percentage rgb()
    inside style attributes that the rsbuild/rslib/rspack icons use.

    `name` (the icon's basename) selects the brand-logo exceptions above.
    Named colors are converted even for BRAND_KEEP icons, since `black` is
    invisible on the file tree and carries no brand meaning.
    """
    swaps = []
    cmap = {**cmap, **PER_ICON.get(name, {})}

    # An icon is left at its original hex if ANY of its colors would have to be
    # guessed. These are overwhelmingly brand logos, and a rule-derived recolor
    # destroys the brand scheme for no fidelity gain -- there is no Noctis
    # version to match. Partial retinting would be worse still: a half-swapped
    # logo reads as a mistake. All-or-nothing per icon.
    keep_hex = name in BRAND_KEEP or (
        guessed is not None
        and any(c.upper() in guessed for c in _HEX6.findall(text)))

    def note(src, dst):
        if dst and dst.upper() != src.upper():
            swaps.append((src.upper(), dst.upper()))
            return dst
        return None

    def do_hex(m):
        return note(m.group(0), cmap.get(m.group(0).upper())) or m.group(0)

    def do_named(m):
        dst = note(m.group(2), NAMED_COLORS[m.group(2)])
        return f'{m.group(1)}="{dst}"' if dst else m.group(0)

    def do_rgb(m):
        hx = '#%02X%02X%02X' % tuple(
            round(float(m.group(i)) * 255 / 100) for i in (2, 3, 4))
        dst = note(hx, cmap.get(hx.upper()) or infer(hx))
        return f'{m.group(1)}:{dst}' if dst else m.group(0)

    if not keep_hex:
        text = _HEX6.sub(do_hex, text)
    text = _NAMED.sub(do_named, text)
    text = _RGB_PCT.sub(do_rgb, text)
    return text, swaps
strip = lambda s: re.sub(r'\s+', '', re.sub(
    r'(fill|stroke)="#[0-9a-fA-F]{3,8}"', '', s))


def extracted_map():
    """Ground-truth map from geometry-identical Symbols/Noctis icon pairs."""
    votes = collections.defaultdict(collections.Counter)
    for f in sorted(os.listdir(CN)):
        if not f.endswith('.svg'):
            continue
        p = os.path.join(_orig('files'), f)
        if not os.path.exists(p):
            continue
        a, b = open(os.path.join(CN, f)).read(), open(p).read()
        if strip(a) != strip(b):
            continue
        ca, cb = COLOR_ATTR.findall(a), COLOR_ATTR.findall(b)
        if len(ca) != len(cb):
            continue
        for src, dst in zip(cb, ca):
            votes[src.upper()][dst.upper()] += 1
    return {s: c.most_common(1)[0][0] for s, c in votes.items()}, votes


def all_symbols_colors():
    # Read from the pristine backup once it exists, so rebuilding the map after
    # a retint still sees the original Tailwind palette rather than the Mocha
    # one we just wrote. Without this the map silently becomes identity.
    root = _BACKUP if os.path.isdir(_BACKUP) else SY
    seen = collections.Counter()
    for sub in ('files', 'folders'):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith('.svg'):
                for c in re.findall(r'#[0-9a-fA-F]{3,8}',
                                    open(os.path.join(d, f)).read()):
                    seen[c.upper()] += 1
    return seen


def build():
    ex, _ = extracted_map()
    full, inferred = dict(ex), {}
    for c in all_symbols_colors():
        if c not in full:
            full[c] = inferred[c] = infer(c)
    full.update(OVERRIDES)
    return full, ex, inferred


if __name__ == '__main__':
    full, ex, inferred = build()
    _, votes = extracted_map()
    # Validate only against mappings Noctis clearly made on purpose: seen 3+
    # times, and an actual recolor rather than a left-untouched brand color.
    hi = {c: d for c, d in ex.items()
          if sum(votes[c].values()) >= 3 and c != d}
    agree = [c for c in hi if infer(c) == hi[c]]
    print(f'extracted (ground truth): {len(ex)}   of which high-confidence: {len(hi)}')
    print(f'inferred (hue rule):      {len(inferred)}')
    print(f'\nrule validation - reproduces {len(agree)}/{len(hi)} '
          f'high-confidence mappings ({100*len(agree)//len(hi)}%)')
    miss = sorted(set(hi) - set(agree))
    print('\nremaining disagreements (extracted always wins in the final map):'
          if miss else '\nno disagreements.')
    for c in miss:
        print(f'  {c} -> noctis {hi[c]}   rule said {infer(c)}')
    json.dump(full, open(os.path.join(os.path.dirname(__file__), 'map.json'), 'w'),
              indent=1, sort_keys=True)
    print(f'\nwrote map.json  ({len(full)} colors)')
