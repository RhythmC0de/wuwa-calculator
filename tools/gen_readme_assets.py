"""Gera os SVGs do README do Tethys System (tema escuro e claro)."""
import math
import pathlib
import sys

OUT = pathlib.Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

THEMES = {
    "dark": dict(bg1="#0A0C11", bg2="#121722", panel="#10141C", line="#2B3242",
                 text="#ECE7DA", muted="#8B92A3", gold="#DDB86B", gold2="#8F7842",
                 cyan="#63D3D9", glow="0.55"),
    "light": dict(bg1="#F7F4EC", bg2="#ECE7DA", panel="#FFFFFF", line="#CBC3B0",
                  text="#1B1D23", muted="#666B77", gold="#A67C1F", gold2="#C9AE6E",
                  cyan="#1B8A92", glow="0.35"),
}
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Consolas,'Liberation Mono',monospace"
SANS = "'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"


def write(name, svg):
    (OUT / name).write_text(svg, encoding="utf-8")


def wave(width, y, amp, cycles, phase=0.0, steps=240):
    pts = []
    for i in range(steps + 1):
        x = width * i / steps
        env = math.sin(math.pi * i / steps) ** 1.5
        yy = y + amp * env * math.sin(2 * math.pi * cycles * i / steps + phase)
        pts.append(f"{x:.1f},{yy:.1f}")
    return "M" + " L".join(pts)


def bracket(x, y, sx, sy, c, n=26):
    return (f'<path d="M{x},{y + sy * n} L{x},{y} L{x + sx * n},{y}" fill="none" '
            f'stroke="{c}" stroke-width="2"/>')


def banner(t, p):
    W, H = 1280, 360
    rings = "".join(
        f'<circle cx="1015" cy="180" r="{r}" fill="none" stroke="{p["line"]}" '
        f'stroke-width="1" opacity="{0.9 - i * 0.12:.2f}"/>'
        for i, r in enumerate((70, 115, 165, 220, 285)))
    ticks = "".join(
        f'<line x1="1015" y1="{180 - 232}" x2="1015" y2="{180 - 244}" stroke="{p["gold2"]}" '
        f'stroke-width="2" transform="rotate({a} 1015 180)"/>' for a in range(0, 360, 15))
    diamond = (f'<path d="M1015,118 L1077,180 L1015,242 L953,180 Z" fill="none" '
               f'stroke="{p["gold"]}" stroke-width="2"/>'
               f'<path d="M1015,142 L1053,180 L1015,218 L977,180 Z" fill="{p["gold"]}" opacity="0.14"/>'
               f'<circle cx="1015" cy="180" r="5" fill="{p["gold"]}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Tethys Archive</title><desc id="d">Arquivo de Ressonadores das Black Shores</desc>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p['bg1']}"/><stop offset="1" stop-color="{p['bg2']}"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p['gold']}" stop-opacity="0"/><stop offset=".5" stop-color="{p['gold']}"/><stop offset="1" stop-color="{p['gold']}" stop-opacity="0"/></linearGradient>
<radialGradient id="halo" cx="1015" cy="180" r="300" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{p['gold']}" stop-opacity="{p['glow']}"/><stop offset="1" stop-color="{p['gold']}" stop-opacity="0"/></radialGradient>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{p['line']}" stroke-width=".6" opacity=".55"/></pattern>
<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<style>
.spin{{transform-origin:1015px 180px;animation:spin 90s linear infinite}}
.spin2{{transform-origin:1015px 180px;animation:spin 140s linear infinite reverse}}
.wv{{stroke-dasharray:6 10;animation:dash 14s linear infinite}}
.wv2{{stroke-dasharray:2 14;animation:dash 22s linear infinite reverse}}
.cur{{animation:blink 1.1s steps(2) infinite}}
.in1{{animation:rise .9s .1s both}}.in2{{animation:rise .9s .3s both}}.in3{{animation:rise .9s .5s both}}.in4{{animation:rise .9s .7s both}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes dash{{to{{stroke-dashoffset:-320}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style></defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#grid)"/>
<rect width="{W}" height="{H}" fill="url(#halo)"/>
{rings}
<g class="spin" opacity=".8">{ticks}</g>
<g class="spin2"><circle cx="1015" cy="180" r="190" fill="none" stroke="{p['gold']}" stroke-width="1.2" stroke-dasharray="3 22" opacity=".7"/></g>
{diamond}
<path class="wv" d="{wave(W, 322, 14, 5)}" fill="none" stroke="{p['cyan']}" stroke-width="1.6" opacity=".75"/>
<path class="wv2" d="{wave(W, 322, 8, 9, 1.3)}" fill="none" stroke="{p['gold']}" stroke-width="1.2" opacity=".6"/>
<g font-family="{MONO}" font-size="13" letter-spacing="2.4">
<text class="in1" x="64" y="82" fill="{p['gold']}">[ TETHYS ARCHIVE / ARQUIVO DE RESSONADORES ]</text>
</g>
<text class="in2" x="62" y="164" font-family="{SANS}" font-size="68" font-weight="300" letter-spacing="14" fill="{p['text']}">TETHYS</text>
<text class="in2" x="64" y="214" font-family="{SANS}" font-size="30" font-weight="600" letter-spacing="15" fill="{p['gold']}">ARCHIVE</text>
<rect class="in3" x="64" y="234" width="260" height="2" fill="url(#fade)"/>
<g class="in3" font-family="{MONO}" font-size="13" letter-spacing="1.6" fill="{p['muted']}">
<text x="64" y="262">UNIDADE    <tspan fill="{p['text']}">JARDINEIROS · BLACK SHORES</tspan></text>
<text x="64" y="284">SESSÃO     <tspan fill="{p['text']}">AGUARDANDO ID DO RESSONADOR</tspan><tspan class="cur" fill="{p['gold']}"> ▌</tspan></text>
</g>
<text class="in4" x="1216" y="82" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{p['gold2']}">v1.4</text>
{bracket(18, 18, 1, 1, p['gold'])}{bracket(W - 18, 18, -1, 1, p['gold'])}
{bracket(18, H - 18, 1, -1, p['gold'])}{bracket(W - 18, H - 18, -1, -1, p['gold'])}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{p['line']}"/>
</svg>'''


def pipeline(t, p):
    W, H = 1200, 330
    nodes = [("01", "VÍDEO", "gravação local"),
             ("02", "MÁSCARA", "cor dos números"),
             ("03", "LEITURA", "OCR dos dígitos"),
             ("04", "RASTREIO", "agrupa no tempo"),
             ("05", "REVISÃO", "só o duvidoso"),
             ("06", "TOTAL", "dano e DPS")]
    bw, gap, x0, y0, bh = 148, 40, 56, 70, 96
    parts = []
    for i, (n, title, sub) in enumerate(nodes):
        x = x0 + i * (bw + gap)
        hi = i == 4
        stroke = p["gold"] if hi else p["line"]
        parts.append(f'''<g>
<path d="M{x + 12},{y0} H{x + bw} V{y0 + bh - 12} L{x + bw - 12},{y0 + bh} H{x} V{y0 + 12} Z" fill="{p['panel']}" stroke="{stroke}" stroke-width="{1.8 if hi else 1.2}"/>
<text x="{x + 16}" y="{y0 + 26}" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{p['gold']}">{n}</text>
<text x="{x + 16}" y="{y0 + 56}" font-family="{SANS}" font-size="17" font-weight="600" letter-spacing="3" fill="{p['text']}">{title}</text>
<text x="{x + 16}" y="{y0 + 78}" font-family="{MONO}" font-size="11.5" fill="{p['muted']}">{sub}</text></g>''')
        if i < len(nodes) - 1:
            ax = x + bw + 8
            parts.append(f'<path d="M{ax},{y0 + bh / 2} H{ax + gap - 18}" stroke="{p["gold2"]}" stroke-width="1.6" stroke-dasharray="4 5" class="fl"/>'
                         f'<path d="M{ax + gap - 24},{y0 + bh / 2 - 5} L{ax + gap - 14},{y0 + bh / 2} L{ax + gap - 24},{y0 + bh / 2 + 5}" fill="none" stroke="{p["gold"]}" stroke-width="1.6"/>')
    rx = x0 + 4 * (bw + gap)
    mid = rx + bw / 2
    modes = f'''
<path d="M{mid},{y0 + bh} V{y0 + bh + 26} H{mid - 151} V{y0 + bh + 40}" fill="none" stroke="{p['gold2']}" stroke-width="1.2"/>
<path d="M{mid},{y0 + bh + 26} H{mid + 151} V{y0 + bh + 40}" fill="none" stroke="{p['gold2']}" stroke-width="1.2"/>
<g font-family="{MONO}" font-size="12.5" letter-spacing=".6">
<rect x="{mid - 296}" y="{y0 + bh + 40}" width="290" height="62" rx="4" fill="{p['panel']}" stroke="{p['line']}"/>
<text x="{mid - 282}" y="{y0 + bh + 62}" fill="{p['gold']}" letter-spacing="2">MODO 1 · SOMENTE A ENGINE</text>
<text x="{mid - 282}" y="{y0 + bh + 83}" fill="{p['muted']}">soma os hits confirmados; o resto vai</text>
<text x="{mid - 282}" y="{y0 + bh + 98}" fill="{p['muted']}" opacity="0">.</text>
<rect x="{mid + 6}" y="{y0 + bh + 40}" width="290" height="62" rx="4" fill="{p['panel']}" stroke="{p['gold']}"/>
<text x="{mid + 20}" y="{y0 + bh + 62}" fill="{p['gold']}" letter-spacing="2">MODO 2 · COM REVISÃO MINHA</text>
<text x="{mid + 20}" y="{y0 + bh + 83}" fill="{p['muted']}">você aceita, corrige ou descarta</text>
</g>'''
    modes = modes.replace('soma os hits confirmados; o resto vai', 'soma o confirmado, avisa o resto')
    head = (f'<text x="56" y="40" font-family="{MONO}" font-size="12.5" letter-spacing="3" fill="{p["muted"]}">'
            f'PIPELINE DE ANÁLISE · MULTIMÍDIA</text>'
            f'<rect x="56" y="50" width="120" height="2" fill="{p["gold"]}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Pipeline: vídeo, máscara, leitura, rastreio, revisão e total">
<style>.fl{{animation:d 6s linear infinite}}@keyframes d{{to{{stroke-dashoffset:-90}}}}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<rect width="{W}" height="{H}" rx="12" fill="{p['bg1']}"/><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{p['line']}"/>
{head}{''.join(parts)}{modes}</svg>'''


ICONS = {
    "dossie": '<rect x="10" y="8" width="44" height="48" rx="3"/><path d="M32 18 L40 26 L32 34 L24 26 Z"/><path d="M18 44H46M18 50H38"/><path d="M10 14H4M10 22H4" opacity=".6"/>',
    "simulador": '<path d="M46 20A18 18 0 1 0 50 36"/><path d="M40 12 L48 20 L38 24"/><path d="M26 40V30M32 40V24M38 40V33" stroke-width="3"/>',
    "teams": '<path d="M32 10 L40 18 L32 26 L24 18 Z"/><path d="M16 36 L23 43 L16 50 L9 43 Z"/><path d="M48 36 L55 43 L48 50 L41 43 Z"/><path d="M29 26 L19 37M35 26 L45 37M23 43H41" opacity=".7"/>',
    "historico": '<circle cx="32" cy="32" r="21"/><path d="M32 20V32L40 38"/><path d="M8 20L11 32L21 27" opacity=".8"/>',
    "multimidia": '<rect x="6" y="12" width="52" height="34" rx="3"/><path d="M27 21 L40 29 L27 37 Z"/><path d="M6 54C14 48 18 58 26 52S38 50 44 54 52 56 58 52" opacity=".8"/>',
}


def icon(name, body):
    g = "#C9A55D"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="{name}">'
            f'<g fill="none" stroke="{g}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


def divider():
    g = "#B89350"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 28" width="1200" height="28" role="presentation">'
            f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{g}" stop-opacity="0"/><stop offset=".5" stop-color="{g}"/><stop offset="1" stop-color="{g}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="0" y="13" width="1200" height="1.4" fill="url(#g)"/>'
            f'<path d="M600 4 L610 14 L600 24 L590 14 Z" fill="none" stroke="{g}" stroke-width="1.6"/>'
            f'<path d="M600 9 L605 14 L600 19 L595 14 Z" fill="{g}"/>'
            f'<path d="M572 14H580M620 14H628" stroke="{g}" stroke-width="1.6"/></svg>')


for t, p in THEMES.items():
    write(f"banner-{t}.svg", banner(t, p))
    write(f"pipeline-{t}.svg", pipeline(t, p))
for n, b in ICONS.items():
    write(f"icon-{n}.svg", icon(n, b))
write("divider.svg", divider())
