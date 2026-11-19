#!/usr/bin/env python3
"""WaveSense A1 포스터 생성기.

실행: python3 poster/build_poster.py
결과: ../WaveSense_포스터_A1.html (594mm x 841mm), poster/assets/*.svg
모든 좌표 단위는 mm.
"""
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
# `python3 build_poster.py photo` → 실사 장면 버전 (별도 파일로 저장, 기존 벡터 버전은 건드리지 않음)
PHOTO = "photo" in sys.argv[1:]
OUT_HTML = ROOT.parent / ("WaveSense_포스터_A1_실사.html" if PHOTO else "WaveSense_포스터_A1.html")

# ── palette ────────────────────────────────────────────────────────────
NAVY = "#0d1637"
INK = "#101a3c"
INK2 = "#48536f"
MUTE = "#8088a0"
LINE = "#d8dbe4"
PAPER = "#ffffff" if PHOTO else "#f5f3ee"
ORANGE = "#14a58b" if PHOTO else "#ff5a1f"  # 감지 강조색 (실사 버전은 장면의 청록에 맞춤)
HOT_BG = "#d3f3ec" if PHOTO else "#ffd9c9"
BLUE = "#2f62ff"
FONT = "Pretendard, 'Apple SD Gothic Neo', sans-serif"

# ── axonometric projection (38° turn, 55° elevation) ──────────────────
TH = math.radians(38)
PHI = math.radians(55)
XX, XY = math.cos(TH), math.sin(TH) * math.sin(PHI)  # screen direction of world +x
YX, YY = -math.sin(TH), math.cos(TH) * math.sin(PHI)  # screen direction of world +y
C = math.cos(PHI)
S = 62.0  # mm per world unit (1 unit = 1.5 m)


def P(x, y, z=0.0):
    return ((x * XX + y * YX) * S, (x * XY + y * YY) * S - z * C * S)


def pts(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def poly(points, **attrs):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<polygon points="{pts(points)}" {a}/>'


def line(p, q, **attrs):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<line x1="{p[0]:.2f}" y1="{p[1]:.2f}" x2="{q[0]:.2f}" y2="{q[1]:.2f}" {a}/>'


def floor_ring(cx, cy, r, n=72):
    return [P(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def floor_text(x, y, text, size, fill, weight=800, opacity=1.0, anchor="middle"):
    px, py = P(x, y)
    return (
        f'<text transform="matrix({XX:.4f} {XY:.4f} {YX:.4f} {YY:.4f} {px:.2f} {py:.2f})" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" opacity="{opacity}" '
        f'text-anchor="{anchor}" dominant-baseline="central">{text}</text>'
    )


def person(cx, feet_y, h, fill, stroke="none", sw=0, dash=None, opacity=1.0):
    """정면 픽토그램. (cx, feet_y)가 발 위치, h가 키."""
    hr = 0.115 * h
    head_cy = feet_y - h + hr
    tw = 0.36 * h
    t_top = head_cy + hr + 0.035 * h
    t_bot = feet_y - 0.40 * h
    lw = 0.145 * h
    gap = 0.03 * h
    d = f' stroke-dasharray="{dash}"' if dash else ""
    st = f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}'
    return (
        f'<g opacity="{opacity}">'
        f'<rect x="{cx - gap - lw:.2f}" y="{t_bot - lw:.2f}" width="{lw:.2f}" height="{feet_y - t_bot + lw:.2f}" rx="{lw / 2:.2f}" {st}/>'
        f'<rect x="{cx + gap:.2f}" y="{t_bot - lw:.2f}" width="{lw:.2f}" height="{feet_y - t_bot + lw:.2f}" rx="{lw / 2:.2f}" {st}/>'
        f'<rect x="{cx - tw / 2:.2f}" y="{t_top:.2f}" width="{tw:.2f}" height="{t_bot - t_top:.2f}" rx="{tw * 0.36:.2f}" {st}/>'
        f'<circle cx="{cx:.2f}" cy="{head_cy:.2f}" r="{hr:.2f}" {st}/>'
        f"</g>"
    )


def board(x, y, label, fill=BLUE):
    bx, by = P(x, y, 0)
    tx, ty = P(x, y, 0.67)
    w, h = 13.5, 8.6
    return (
        f'<ellipse cx="{bx:.2f}" cy="{by:.2f}" rx="3.4" ry="1.7" fill="{NAVY}" opacity=".35"/>'
        f'<line x1="{bx:.2f}" y1="{by:.2f}" x2="{tx:.2f}" y2="{ty:.2f}" stroke="{NAVY}" stroke-width="1.3" stroke-linecap="round"/>'
        f'<rect x="{tx - w / 2:.2f}" y="{ty - h / 2:.2f}" width="{w}" height="{h}" rx="2" fill="{fill}" stroke="#fff" stroke-width=".7"/>'
        f'<text x="{tx:.2f}" y="{ty + 0.2:.2f}" font-size="5" font-weight="800" fill="#fff" text-anchor="middle" dominant-baseline="central" letter-spacing=".02em">{label}</text>'
    )


def hero_scene(kind, width_mm):
    """방 장면. kind='cctv' | 'wave'. 내부 좌표는 S=62 기준, width_mm으로 전체를 확대/축소."""
    cctv = kind == "cctv"
    WALL_H = 1.12
    PH = 1.05  # partition height
    PL = 1.75  # partition end
    T = 0.05  # partition thickness
    CAMY = 0.7
    px_, py_ = 1.46, 1.46  # person
    e = []

    # floor shadow of the obstacle as seen from the camera at (0, CAMY)
    r1y = CAMY + (1 - CAMY) * 2 / PL
    r2x = (2 - CAMY) / (PL - CAMY)
    shadow = [P(1, 1), P(PL, 1), P(2, r1y), P(2, 2), P(r2x, 2), P(1, PL)]
    floor = [P(0, 0), P(2, 0), P(2, 2), P(0, 2)]

    e.append(
        f'<defs><clipPath id="shadow-{kind}"><polygon points="{pts(shadow)}"/></clipPath>'
        f'<clipPath id="floor-{kind}"><polygon points="{pts(floor)}"/></clipPath></defs>'
    )

    # hard drop shadow + slab
    e.append(poly([P(-0.05, -0.05, -0.28), P(2.05, -0.05, -0.28), P(2.05, 2.05, -0.28), P(-0.05, 2.05, -0.28)], fill="#060b22"))
    t = 0.085
    e.append(poly([P(0, 2), P(2, 2), P(2, 2, -t), P(0, 2, -t)], fill="#6f7aa0" if cctv else "#7d88ab"))
    e.append(poly([P(2, 0), P(2, 2), P(2, 2, -t), P(2, 0, -t)], fill="#8a94b4" if cctv else "#99a3c2"))

    # back walls
    e.append(poly([P(0, 0), P(0, 2), P(0, 2, WALL_H), P(0, 0, WALL_H)], fill="#99a3be" if cctv else "#aeb8d2"))
    e.append(poly([P(0, 0), P(2, 0), P(2, 0, WALL_H), P(0, 0, WALL_H)], fill="#afb7cd" if cctv else "#c4cce2"))
    for a_, b_ in ((P(0, 2, WALL_H), P(0, 0, WALL_H)), (P(0, 0, WALL_H), P(2, 0, WALL_H))):
        e.append(line(a_, b_, stroke="#e3e8f5", stroke_width="1", stroke_linecap="round"))

    # floor
    e.append(poly(floor, fill="#f1f3f9" if cctv else "#e9edf7"))

    if cctv:
        e.append(poly(shadow, fill="#1c2654"))
        hatch = "".join(line(P(1 + 0.09 * i, 0.9), P(1 + 0.09 * i, 2.1), stroke="#3a4682", stroke_width=".6") for i in range(0, 13))
        e.append(f'<g clip-path="url(#shadow-{kind})">{hatch}</g>')
    else:
        rip = []
        for i, r in enumerate([0.42, 0.84, 1.26, 1.68, 2.1, 2.52]):
            seg = []
            for k in range(0, 91):
                ang = math.radians(k)
                x, y = r * math.cos(ang), r * math.sin(ang)
                if x <= 2.0 and y <= 2.0:
                    seg.append(P(x, y))
                else:
                    if len(seg) > 1:
                        rip.append((seg, i))
                    seg = []
            if len(seg) > 1:
                rip.append((seg, i))
        for seg, i in rip:
            e.append(
                f'<polyline points="{pts(seg)}" fill="none" stroke="{BLUE}" stroke-width="{1.5 - i * 0.12:.2f}" '
                f'stroke-linecap="round" opacity="{0.6 - i * 0.07:.2f}"/>'
            )
        zone4 = [P(1, 1), P(2, 1), P(2, 2), P(1, 2)]
        e.append(poly(zone4, fill="#ffd9c9"))
        e.append(poly(zone4, fill="none", stroke=ORANGE, stroke_width="1.3", stroke_linejoin="round"))

    for a_, b_ in ((P(1, 0), P(1, 2)), (P(0, 1), P(2, 1))):
        e.append(line(a_, b_, stroke="#9aa4c4", stroke_width=".6", stroke_dasharray="2.2 2.2"))

    num_fill = "#98a2c0"
    e.append(floor_text(0.66, 0.24, "1", 15, num_fill))
    e.append(floor_text(1.6, 0.36, "2", 15, num_fill))
    e.append(floor_text(0.36, 1.6, "3", 15, num_fill))
    e.append(floor_text(1.2, 1.82, "4", 15, "#7f8cc4" if cctv else ORANGE))

    # camera (left wall)
    cw = P(0, CAMY, 0.9)
    lens = (cw[0] + 13.2, cw[1] + 6.6)
    if cctv:
        beam = [lens, P(2, 0), P(2, r1y), P(PL, 1), P(1, 1), P(1, PL), P(r2x, 2), P(0, 2)]
        e.append(poly(beam, fill="#fff", opacity=".2"))
        for q in (P(2, r1y), P(r2x, 2)):
            e.append(line(lens, q, stroke="#fff", stroke_width=".7", stroke_dasharray="2 1.8"))
    e.append(
        f'<g opacity="{"1" if cctv else ".45"}"><line x1="{cw[0]:.2f}" y1="{cw[1]:.2f}" x2="{cw[0] + 4:.2f}" y2="{cw[1] + 1.5:.2f}" stroke="{NAVY}" stroke-width="1.6" stroke-linecap="round"/>'
        f'<g transform="translate({cw[0] + 3:.2f} {cw[1] + 1.2:.2f}) rotate(27)">'
        f'<rect x="0" y="-3.6" width="12.5" height="7.2" rx="2.2" fill="{NAVY}" stroke="#fff" stroke-width=".6"/>'
        f'<rect x="10.4" y="-2.6" width="3" height="5.2" rx="1" fill="#2a376e" stroke="#fff" stroke-width=".5"/>'
        f'<circle cx="3" cy="0" r="1" fill="{"#ff4d3d" if cctv else "#7f8bb5"}"/></g></g>'
    )

    tx_top = P(0, 0, 0.67)
    if not cctv:
        for q in (P(2, 0, 0.67), P(0, 2, 0.67), P(2, 2, 0.67)):
            e.append(line(tx_top, q, stroke=BLUE, stroke_width="1.1", stroke_dasharray="3 2"))
        e.append(board(0, 0, "TX", NAVY))
        e.append(board(2, 0, "RX"))
        e.append(board(0, 2, "RX"))

    # partition (L-shape around zone 4)
    e.append(poly([P(1, 1), P(1, PL), P(1, PL, PH), P(1, 1, PH)], fill="#414b78"))
    e.append(poly([P(1, 1), P(PL, 1), P(PL, 1, PH), P(1, 1, PH)], fill="#566190"))
    e.append(poly([P(PL, 1), P(PL, 1 - T), P(PL, 1 - T, PH), P(PL, 1, PH)], fill="#6b76a6"))
    e.append(poly([P(1, PL), P(1 - T, PL), P(1 - T, PL, PH), P(1, PL, PH)], fill="#333c66"))
    e.append(poly([P(1, 1, PH), P(PL, 1, PH), P(PL, 1 - T, PH), P(1 - T, 1 - T, PH), P(1 - T, PL, PH), P(1, PL, PH)], fill="#8a95c2"))
    ln = math.hypot(XX, XY)
    lx_, ly_ = P(1.38, 1, PH * 0.5)
    e.append(
        f'<text transform="matrix({XX / ln:.4f} {XY / ln:.4f} 0 1 {lx_:.2f} {ly_:.2f})" font-size="5.6" font-weight="700" fill="#fff" opacity=".8" '
        f'text-anchor="middle" dominant-baseline="central">장애물</text>'
    )

    feet = P(px_, py_)
    ph_mm = 1.1 * C * S
    hy = feet[1] - ph_mm * 0.42
    edge_x = P(2, 0)[0] + (hy - P(2, 0)[1]) / (P(2, 2)[1] - P(2, 0)[1]) * (P(2, 2)[0] - P(2, 0)[0])
    ex = edge_x + 8
    x0 = P(0, 2)[0] - 12
    if cctv:
        e.append(person(feet[0], feet[1], ph_mm, "#2a356a", stroke="#9aa6d2", sw=0.7, dash="2 1.6"))
        e.append(
            f'<text x="{cw[0] - 4:.1f}" y="{cw[1] - 9:.1f}" font-size="6" font-weight="800" fill="#fff" text-anchor="end" letter-spacing=".04em">CCTV</text>'
        )
        x1 = P(2, 0)[0] + 6
        y0 = -WALL_H * C * S - 8
    else:
        e.append(line(P(1.02, 1.02, 0.67), P(2, 2, 0.67), stroke=BLUE, stroke_width="1.1", stroke_dasharray="3 2"))
        for i, r in enumerate([0.2, 0.34, 0.48]):
            e.append(
                f'<g clip-path="url(#floor-{kind})"><polygon points="{pts(floor_ring(px_, py_, r))}" fill="none" stroke="{ORANGE}" '
                f'stroke-width="{1.3 - i * 0.25:.2f}" opacity="{1 - i * 0.28:.2f}"/></g>'
            )
        e.append(person(feet[0], feet[1], ph_mm, ORANGE, stroke="#fff", sw=0.8))
        e.append(board(2, 2, "RX"))
        # leader labels (all on the dark background)
        hx = feet[0] + 7.5
        e.append(f'<path d="M{hx:.1f} {hy:.1f} H{ex:.1f}" stroke="{ORANGE}" stroke-width=".7" fill="none"/>')
        e.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="1.1" fill="{ORANGE}"/>')
        e.append(f'<text x="{ex + 2.5:.1f}" y="{hy + 0.4:.1f}" font-size="8.4" font-weight="800" fill="{ORANGE}" dominant-baseline="central" letter-spacing="-.02em">사람 감지</text>')
        top = -WALL_H * C * S
        LAB, SUB, LEAD = "#fff", "#aab4d8", "#8f9bc8"

        def note(x, y, title, subs, anchor="start"):
            out = f'<text x="{x:.1f}" y="{y:.1f}" font-size="4.5" font-weight="800" fill="{LAB}" text-anchor="{anchor}" letter-spacing="-.02em">{title}</text>'
            for i, t_ in enumerate(subs):
                out += f'<text x="{x:.1f}" y="{y + 5.3 + i * 4.6:.1f}" font-size="3.5" font-weight="500" fill="{SUB}" text-anchor="{anchor}">{t_}</text>'
            return out

        e.append(f'<text x="{ex + 2.5:.1f}" y="{hy + 8.6:.1f}" font-size="3.5" font-weight="500" fill="{SUB}">구역 4 = 장애물로 가린</text>')
        e.append(f'<text x="{ex + 2.5:.1f}" y="{hy + 13.2:.1f}" font-size="3.5" font-weight="500" fill="{SUB}">웹캠 사각지대</text>')
        # TX
        e.append(f'<path d="M{tx_top[0]:.1f} {tx_top[1] - 4.6:.1f} V{top - 19:.1f}" stroke="{LEAD}" stroke-width=".45" fill="none"/>')
        e.append(note(tx_top[0] + 3.5, top - 15, "송신 보드 ESP32-C5 ×1", ["Wi-Fi 패킷을 계속 송신", "같은 패킷을 받아야 같은 기준으로 비교"]))
        # RX (right)
        rx_b = P(2, 0, 0.67)
        e.append(f'<path d="M{rx_b[0]:.1f} {rx_b[1] - 4.6:.1f} V-9.5" stroke="{LEAD}" stroke-width=".45" fill="none"/>')
        e.append(note(rx_b[0] + 3, -25, "수신 보드 ESP32-C5 ×3", ["방 모서리에서 CSI 측정", "경로 3개로 어느 쪽에 있는지 구분"], "end"))
        # height (near RX pole)
        nb = P(2, 2)
        e.append(note(nb[0] - 15, nb[1] + 7, "높이 약 1 m", ["신호를 가장 많이 바꾸는 몸통 높이"], "end"))
        # non-collinear placement (left RX)
        lb = P(0, 2)
        e.append(f'<path d="M{lb[0]:.1f} {lb[1] + 8:.1f} V{lb[1] + 39:.1f}" stroke="{LEAD}" stroke-width=".45" fill="none"/>')
        e.append(note(lb[0] - 9.5, lb[1] + 45, "일직선 회피", ["양 끝 위치 혼동 방지"]))
        # floor dimension
        d0, d1 = P(2.2, 0), P(2.2, 2)
        e.append(line(d0, d1, stroke=LEAD, stroke_width=".45"))
        for q in (0, 2):
            e.append(line(P(2.14, q), P(2.26, q), stroke=LEAD, stroke_width=".45"))
        tx_, ty_ = P(2.36, 1.3)
        e.append(
            f'<text transform="matrix({-YX:.4f} {-YY:.4f} {XX:.4f} {XY:.4f} {tx_:.2f} {ty_:.2f})" font-size="4.2" font-weight="600" '
            f'fill="#cbd3ee" text-anchor="middle" dominant-baseline="central">3 m × 3 m 이상</text>'
        )
        x1 = ex + 44
        y0 = top - 22

    y1 = P(2, 2)[1] + (14 if cctv else 20)
    w, h = x1 - x0, y1 - y0
    k = width_mm / w
    body = "\n".join(e)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
        f'width="{width_mm:.1f}mm" height="{h * k:.1f}mm" font-family="{FONT}">\n{body}\n</svg>'
    ), (width_mm, h * k)


# ── small diagrams ────────────────────────────────────────────────────
def wave_path(kind, x0, w, mid, amp, seed):
    rnd = random.Random(seed)
    n = 220
    out = []
    for i in range(n + 1):
        t = i / n
        if kind == "empty":
            y = 0.04 * math.sin(t * 40 + 1) + 0.03 * (rnd.random() - 0.5)
        elif kind == "still":
            y = 0.34 * math.sin(t * 5.4 + 0.6) + 0.16 * math.sin(t * 12.5 + 2) + 0.03 * (rnd.random() - 0.5)
        else:
            env = 0.5 + 0.5 * math.sin(t * 8.5 + 1.0) ** 2
            y = env * (0.7 * math.sin(t * 58) + 0.25 * math.sin(t * 91 + 1)) + 0.1 * (rnd.random() - 0.5)
        out.append((x0 + t * w, mid - y * amp))
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in out)


def wave_stack_svg():
    W, RH = 170, 36
    e = []
    rows = (("empty", "사람 없음", "거의 일정", INK), ("still", "사람 있음", "패턴이 달라짐", BLUE), ("move", "움직임", "크게 흔들림", ORANGE))
    for i, (k, t, d, col) in enumerate(rows):
        y = i * RH
        mid = y + RH / 2
        if i:
            e.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{LINE}" stroke-width=".4"/>')
        e.append(f'<text x="0" y="{mid - 3.4}" font-size="6.6" font-weight="800" fill="{INK}" dominant-baseline="central" letter-spacing="-.02em">{t}</text>')
        e.append(f'<text x="0" y="{mid + 4.6}" font-size="5.2" font-weight="500" fill="{INK2}" dominant-baseline="central">{d}</text>')
        e.append(f'<path d="{wave_path(k, 44, W - 44, mid, 13.5, 7)}" fill="none" stroke="{col}" stroke-width="1.15" stroke-linejoin="round" stroke-linecap="round"/>')
    return f'<svg viewBox="0 0 {W} {RH * 3}" width="100%" font-family="{FONT}" style="display:block">{"".join(e)}</svg>'


def wave_panel_svg(kind, color):
    W, H = 170, 46
    return (
        f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block">'
        f'<line x1="0" y1="{H / 2}" x2="{W}" y2="{H / 2}" stroke="{LINE}" stroke-width=".5" stroke-dasharray="2 2"/>'
        f'<path d="{wave_path(kind, 0, W, H / 2, 20, 7)}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


def plan_svg():
    x0, y0, s = 10, 10, 96  # room square
    cx, cy = x0 + s / 2, y0 + s / 2
    cam = (x0, y0 + s * 0.35)
    pl = 0.75
    ax, ay = cx + s / 2 * pl, cy + s / 2 * pl
    r1y = cam[1] + (cy - cam[1]) * (x0 + s - cam[0]) / (ax - cam[0])
    r2x = cam[0] + (cx - cam[0]) * (y0 + s - cam[1]) / (ay - cam[1])
    shadow = [(cx, cy), (ax, cy), (x0 + s, r1y), (x0 + s, y0 + s), (r2x, y0 + s), (cx, ay)]
    seen = [cam, (x0, y0), (x0 + s, y0), (x0 + s, r1y), (ax, cy), (cx, cy), (cx, ay), (r2x, y0 + s), (x0, y0 + s)]
    e = []
    e.append(f'<rect x="{x0}" y="{y0}" width="{s}" height="{s}" fill="#fff"/>')
    e.append(f'<polygon points="{pts(seen)}" fill="#e4eaff"/>')
    e.append(f'<polygon points="{pts(shadow)}" fill="#ffd9c9"/>')
    e.append(f'<line x1="{cx}" y1="{y0}" x2="{cx}" y2="{y0 + s}" stroke="#aab1c6" stroke-width=".5" stroke-dasharray="2 2"/>')
    e.append(f'<line x1="{x0}" y1="{cy}" x2="{x0 + s}" y2="{cy}" stroke="#aab1c6" stroke-width=".5" stroke-dasharray="2 2"/>')
    e.append(f'<rect x="{x0}" y="{y0}" width="{s}" height="{s}" fill="none" stroke="{INK}" stroke-width="1.1"/>')
    for q in ((x0 + s, y0), (x0, y0 + s), (x0 + s, y0 + s)):
        e.append(f'<line x1="{x0}" y1="{y0}" x2="{q[0]}" y2="{q[1]}" stroke="{BLUE}" stroke-width=".9" stroke-dasharray="2.6 2"/>')
    e.append(f'<path d="M{ax} {cy} H{cx} V{ay}" fill="none" stroke="{INK}" stroke-width="3"/>')
    for (nx, ny, t) in ((0.34, 0.16, "1"), (0.78, 0.26, "2"), (0.2, 0.8, "3")):
        e.append(f'<text x="{x0 + s * nx}" y="{y0 + s * ny}" font-size="9" font-weight="800" fill="{MUTE}" text-anchor="middle" dominant-baseline="central">{t}</text>')
    e.append(f'<text x="{cx + 8}" y="{cy + s * 0.3}" font-size="9" font-weight="800" fill="{ORANGE}" text-anchor="middle" dominant-baseline="central">4</text>')
    e.append(person(cx + s * 0.3, cy + s * 0.37, 20, ORANGE))
    e.append(f'<text x="{cx + s * 0.25 + 2}" y="{y0 + s - 4.5}" font-size="5.2" font-weight="800" fill="{ORANGE}" text-anchor="middle">사각지대</text>')
    e.append(f'<text x="{ax}" y="{cy - 4}" font-size="4.8" font-weight="700" fill="{INK}" text-anchor="end">장애물</text>')
    e.append(f'<rect x="{cam[0] - 3.2}" y="{cam[1] - 5}" width="6.4" height="10" rx="1.4" fill="{INK}"/>')
    e.append(f'<text x="{cam[0] + 6}" y="{cam[1] + 0.3}" font-size="4.8" font-weight="700" fill="{INK}" dominant-baseline="central">웹캠</text>')
    for (bx, by, t, col) in ((x0, y0, "TX", INK), (x0 + s, y0, "RX", BLUE), (x0, y0 + s, "RX", BLUE), (x0 + s, y0 + s, "RX", BLUE)):
        e.append(f'<rect x="{bx - 7}" y="{by - 5}" width="14" height="10" rx="2" fill="{col}" stroke="{PAPER}" stroke-width=".8"/>')
        e.append(f'<text x="{bx}" y="{by + 0.2}" font-size="5.4" font-weight="800" fill="#fff" text-anchor="middle" dominant-baseline="central">{t}</text>')
    dy = y0 + s + 11
    e.append(f'<path d="M{x0} {dy} H{x0 + s} M{x0} {dy - 2} v4 M{x0 + s} {dy - 2} v4" stroke="{MUTE}" stroke-width=".5" fill="none"/>')
    e.append(f'<rect x="{cx - 9}" y="{dy - 4}" width="18" height="8" fill="{PAPER}"/>')
    e.append(f'<text x="{cx}" y="{dy + 0.2}" font-size="5.4" font-weight="600" fill="{INK2}" text-anchor="middle" dominant-baseline="central">3 m</text>')
    dx = x0 + s + 11
    e.append(f'<path d="M{dx} {y0} V{y0 + s} M{dx - 2} {y0} h4 M{dx - 2} {y0 + s} h4" stroke="{MUTE}" stroke-width=".5" fill="none"/>')
    e.append(f'<rect x="{dx - 3}" y="{cy - 9}" width="6" height="18" fill="{PAPER}"/>')
    e.append(f'<text transform="translate({dx} {cy}) rotate(90)" font-size="5.4" font-weight="600" fill="{INK2}" text-anchor="middle" dominant-baseline="central">3 m</text>')
    return f'<svg viewBox="0 0 122 124" width="114mm" height="115.9mm" font-family="{FONT}" style="display:block;flex:none">{"".join(e)}</svg>'


def devices_svg():
    """보드 4대 → 노트북 → 대시보드."""
    W, H = 170, 46
    e = []
    for i, (t, col) in enumerate((("TX", INK), ("RX", BLUE), ("RX", BLUE), ("RX", BLUE))):
        bx, by = (i % 2) * 21, 2 + (i // 2) * 13.5
        e.append(f'<rect x="{bx}" y="{by}" width="19" height="11.5" rx="2" fill="{col}"/>')
        e.append(f'<text x="{bx + 9.5}" y="{by + 6}" font-size="5.2" font-weight="800" fill="#fff" text-anchor="middle" dominant-baseline="central">{t}</text>')
    e.append(f'<text x="0" y="38" font-size="5.6" font-weight="700" fill="{INK}" dominant-baseline="central">ESP32-C5 보드 4대</text>')
    # arrow 1
    e.append(f'<path d="M46 15 H68 M64.5 11.5 L68 15 L64.5 18.5" fill="none" stroke="{INK}" stroke-width=".9" stroke-linecap="round" stroke-linejoin="round"/>')
    e.append(f'<text x="56.5" y="9.5" font-size="4.4" font-weight="600" fill="{INK2}" text-anchor="middle">USB 시리얼</text>')
    # laptop
    lx = 74
    e.append(f'<rect x="{lx}" y="1.5" width="32" height="21" rx="2" fill="#fff" stroke="{INK}" stroke-width="1.1"/>')
    e.append(f'<path d="M{lx - 4} 26.2 H{lx + 36}" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>')
    e.append(f'<path d="M{lx + 4} 15 l5 -5 l4 3 l5 -6 l4 4 l5 -2" fill="none" stroke="{BLUE}" stroke-width="1" stroke-linejoin="round" stroke-linecap="round"/>')
    e.append(f'<text x="{lx + 16}" y="38" font-size="5.6" font-weight="700" fill="{INK}" text-anchor="middle" dominant-baseline="central">노트북 · AI 판정</text>')
    # arrow 2
    e.append(f'<path d="M116 15 H134 M130.5 11.5 L134 15 L130.5 18.5" fill="none" stroke="{INK}" stroke-width=".9" stroke-linecap="round" stroke-linejoin="round"/>')
    # dashboard
    dx = 140
    e.append(f'<rect x="{dx}" y="1.5" width="28" height="25" rx="2" fill="#fff" stroke="{INK}" stroke-width="1.1"/>')
    e.append(f'<rect x="{dx + 14}" y="14" width="13.4" height="11.9" fill="{ORANGE}"/>')
    e.append(f'<path d="M{dx + 14} 2 V26 M{dx + .6} 14 H{dx + 27.4}" stroke="{INK}" stroke-width=".6"/>')
    e.append(f'<text x="{dx + 14}" y="38" font-size="5.6" font-weight="700" fill="{INK}" text-anchor="middle" dominant-baseline="central">평면도 화면</text>')
    return f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="{FONT}" style="display:block">{"".join(e)}</svg>'


def dashboard_svg():
    e = []
    W, H = 166, 68
    e.append(f'<rect x=".6" y=".6" width="{W - 1.2}" height="{H - 1.2}" rx="2.5" fill="#fff" stroke="{INK}" stroke-width="1.1"/>')
    e.append(f'<path d="M.6 9.5 V3.1 a2.5 2.5 0 0 1 2.5 -2.5 H{W - 3.1} a2.5 2.5 0 0 1 2.5 2.5 V9.5 Z" fill="{INK}"/>')
    e.append(f'<text x="5.5" y="5.3" font-size="4.2" font-weight="700" fill="#fff" dominant-baseline="central">WaveSense · 실시간 감지</text>')
    px, py, ps = (6, 15, 40) if PHOTO else (6, 15, 47)  # 실사 버전은 웹캠 사진 자리를 넓힌다
    e.append(f'<rect x="{px}" y="{py}" width="{ps}" height="{ps}" fill="#e9edf7"/>')
    e.append(f'<rect x="{px + ps / 2}" y="{py + ps / 2}" width="{ps / 2}" height="{ps / 2}" fill="{ORANGE}"/>')
    e.append(f'<path d="M{px + ps / 2} {py} V{py + ps} M{px} {py + ps / 2} H{px + ps}" stroke="#fff" stroke-width="1"/>')
    for (nx, ny, t) in ((0.25, 0.25, "1"), (0.75, 0.25, "2"), (0.25, 0.75, "3")):
        e.append(f'<text x="{px + ps * nx}" y="{py + ps * ny}" font-size="5.6" font-weight="700" fill="#9aa3bd" text-anchor="middle" dominant-baseline="central">{t}</text>')
    e.append(person(px + ps * 0.75, py + ps * 0.93, 16, "#fff"))
    lx, lw = (51, 44) if PHOTO else (59, 50)
    rows = (("구역 1", "없음", False), ("구역 2", "없음", False), ("구역 3", "없음", False), ("구역 4", "사람 감지", True))
    for i, (z, st, hot) in enumerate(rows):
        y = 15 + i * 9.4
        if hot:
            e.append(f'<rect x="{lx}" y="{y}" width="{lw}" height="8" fill="{HOT_BG}"/>')
        e.append(f'<line x1="{lx}" y1="{y + 8.7}" x2="{lx + lw}" y2="{y + 8.7}" stroke="{LINE}" stroke-width=".3"/>')
        e.append(f'<text x="{lx + 2.5}" y="{y + 4.2}" font-size="4.3" font-weight="700" fill="{INK}" dominant-baseline="central">{z}</text>')
        e.append(
            f'<text x="{lx + lw - 2.5}" y="{y + 4.2}" font-size="4.3" font-weight="{800 if hot else 500}" fill="{ORANGE if hot else MUTE}" text-anchor="end" dominant-baseline="central">{st}</text>'
        )
    e.append(f'<text x="{lx}" y="58.6" font-size="3.8" font-weight="600" fill="{INK2}" dominant-baseline="central">판정 신뢰도</text>')
    e.append(f'<rect x="{lx + 20}" y="57.3" width="{lw - 20}" height="2.6" fill="{LINE}"/><rect x="{lx + 20}" y="57.3" width="{(lw - 20) * 0.8}" height="2.6" fill="{INK}"/>')
    if PHOTO:
        tx, ty, tw, th = 100, 25, 60, 27.26  # 웹캠 사진 비율 1860:845
        hy = ty - 4.6
        e.append(f'<text x="{tx}" y="{hy}" font-size="4.1" font-weight="800" fill="{INK}" dominant-baseline="central">웹캠 화면</text>')
        e.append(f'<circle cx="{tx + tw - 28.6}" cy="{hy - 0.1}" r="1.35" fill="#e5382b"/>')
        e.append(
            f'<text x="{tx + tw}" y="{hy}" font-size="3.7" text-anchor="end" dominant-baseline="central">'
            f'<tspan font-weight="800" fill="#e5382b">LIVE</tspan><tspan font-weight="500" fill="{INK2}"> 14:03:22</tspan></text>'
        )
        e.append(f'<image href="poster/assets/webcam.jpg" x="{tx}" y="{ty}" width="{tw}" height="{th}" preserveAspectRatio="xMidYMid slice"/>')
        e.append(f'<text x="{tx + 2.4}" y="{ty + 4.6}" font-size="3.4" font-weight="700" fill="#fff" dominant-baseline="central" style="paint-order:stroke" stroke="#0b1220" stroke-width=".7" stroke-opacity=".55">CAM01</text>')
        e.append(f'<circle cx="{tx + tw - 3.4}" cy="{ty + 4.4}" r="1.25" fill="#ff4d3d"/>')
        e.append(f'<text x="{tx}" y="{ty + th + 4.4}" font-size="3.7" font-weight="600" fill="{INK2}" dominant-baseline="central">웹캠 · 구역 4 안 보임</text>')
    else:
        tx, ty, tw, th = 115, 15, 45, 37.6
        e.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" fill="#c3c9d8"/>')
        e.append(f'<rect x="{tx}" y="{ty + 25}" width="{tw}" height="{th - 25}" fill="#aab2c6"/>')
        e.append(f'<rect x="{tx + 19}" y="{ty + 8}" width="21" height="27" fill="#69738f"/>')
        e.append(f'<circle cx="{tx + 4.2}" cy="{ty + 4.4}" r="1.3" fill="#ff4d3d"/>')
        e.append(f'<text x="{tx + 7}" y="{ty + 4.5}" font-size="3.4" font-weight="700" fill="{INK}" dominant-baseline="central">웹캠</text>')
        e.append(f'<text x="{tx + tw / 2}" y="58.6" font-size="3.9" font-weight="700" fill="{INK2}" text-anchor="middle" dominant-baseline="central">웹캠: 구역 4 미감지</text>')
    return f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="{FONT}" style="display:block">{"".join(e)}</svg>'


CHAIN_ICON = {
    "tx": f'<rect x="1" y="3" width="24" height="14" rx="2.4" fill="{INK}"/><text x="13" y="10.3" font-size="6.2" font-weight="800" fill="#fff" text-anchor="middle" dominant-baseline="central">TX</text>',
    "rx": "".join(f'<rect x="{1 + i * 2.6}" y="{7.4 - i * 3.2}" width="21" height="12" rx="2.2" fill="{BLUE}" stroke="{PAPER}" stroke-width=".8"/>' for i in (2, 1, 0))
    + '<text x="11.5" y="13.7" font-size="5.6" font-weight="800" fill="#fff" text-anchor="middle" dominant-baseline="central">RX</text>',
    "laptop": f'<rect x="4" y="1.5" width="19" height="13" rx="1.6" fill="#fff" stroke="{INK}" stroke-width="1.1"/><path d="M1 18 H26" stroke="{INK}" stroke-width="1.8" stroke-linecap="round"/>'
    f'<path d="M7 10.5 l3 -3 l2.6 2 l3 -4 l2.6 2.6 l2 -1" fill="none" stroke="{BLUE}" stroke-width="1" stroke-linejoin="round" stroke-linecap="round"/>',
    "dash": f'<rect x="3" y="1" width="21" height="18" rx="1.6" fill="#fff" stroke="{INK}" stroke-width="1.1"/><rect x="13.5" y="10" width="10" height="8.5" fill="{ORANGE}"/>'
    f'<path d="M13.5 1.5 V18.5 M3.5 10 H23.5" stroke="{INK}" stroke-width=".6"/>',
}


def chain_node(icon, name, sub):
    return f'<div class="node"><svg viewBox="0 0 27 20" width="21.6mm" height="16mm">{CHAIN_ICON[icon]}</svg><p><b>{name}</b><span>{sub}</span></p></div>'


def chain_link(label):
    return (
        f'<div class="link"><span>{label}</span><svg viewBox="0 0 24 8" width="19mm" height="6.3mm">'
        f'<path d="M1 4 H22 M18.5 1 L22 4 L18.5 7" fill="none" stroke="{INK}" stroke-width=".9" stroke-linecap="round" stroke-linejoin="round"/></svg></div>'
    )


def track(name, nodes):
    cells = "".join(f'<li class="{"end" if i == len(nodes) - 1 else ""}"><b>{t}</b><span>{d}</span></li>' for i, (t, d) in enumerate(nodes))
    return f'<div class="track"><h4>{name}</h4><ol>{cells}</ol></div>'


def build():
    ASSETS.mkdir(exist_ok=True)
    small, _ = hero_scene("cctv", 172)
    big, (bw, bh) = hero_scene("wave", 352)
    parts = {
        "dashboard": dashboard_svg(),
        "wave_empty": wave_panel_svg("empty", INK),
        "wave_still": wave_panel_svg("still", BLUE),
        "wave_move": wave_panel_svg("move", ORANGE),
    }
    if not PHOTO:  # 실사 버전은 기존 SVG 에셋을 덮어쓰지 않는다
        (ASSETS / "hero_cctv.svg").write_text(small, encoding="utf-8")
        (ASSETS / "hero_wavesense.svg").write_text(big, encoding="utf-8")
        for name, svg in parts.items():
            (ASSETS / f"{name}.svg").write_text(svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1), encoding="utf-8")

    html = (ROOT / ("template_photo.html" if PHOTO else "template.html")).read_text(encoding="utf-8")
    rep = {
        "{{HERO_SMALL}}": small,
        "{{HERO_BIG}}": big,
        "{{W_EMPTY}}": parts["wave_empty"],
        "{{W_STILL}}": parts["wave_still"],
        "{{W_MOVE}}": parts["wave_move"],
        "{{DASH}}": parts["dashboard"],
        "{{CHAIN}}": chain_node("tx", "송신 보드 ESP32-C5 ×1", "Wi-Fi 패킷을 계속 송신")
        + chain_link("Wi-Fi 신호<br>(사람이 있으면 변형)")
        + chain_node("rx", "수신 보드 ESP32-C5 ×3", "방 모서리에서 CSI 측정")
        + chain_link("USB 시리얼")
        + chain_node("laptop", "노트북 (Python) + 웹캠", "수집 → 전처리 → AI 판정")
        + chain_link("감지 결과 전송")
        + chain_node("dash", "웹/앱 대시보드", "구역별 감지 · 웹캠과 비교 표시"),
        "{{TRAIN}}": track("학습 단계", [("구역별 수집", "구역 번호(0~4) 붙여 저장"), ("전처리", "진폭 계산 · 4초 단위 분할"), ("모델 학습", "존재 · 구역 판정 모델"), ("평가", "다른 날 수집한 데이터로 검증")]),
        "{{INFER}}": track("판정 단계", [("실시간 수집", "수신 보드 3대 CSI 동시 수집"), ("분석", "같은 방식으로 전처리"), ("판정", "존재 여부 + 구역 판정"), ("표시", "웹캠이 놓친 구역 강조")]),
    }
    for k, v in rep.items():
        html = html.replace(k, v)
    for k, v in (("NAVY", NAVY), ("INK2", INK2), ("INK", INK), ("MUTE", MUTE), ("LINE", LINE), ("PAPER", PAPER), ("ORANGE", ORANGE), ("BLUE", BLUE)):
        html = html.replace("$" + k, v)
    OUT_HTML.write_text(html, encoding="utf-8")
    print("wrote", OUT_HTML, f"big scene {bw:.0f}x{bh:.0f}mm")


if __name__ == "__main__":
    build()
