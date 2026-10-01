#!/usr/bin/env python3
"""Generate rollout scenario math, markdown, and a shareable HTML report."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)

# --- prices ---
E_PUB, I_PUB = 39, 99
E_FND, I_FND = 29, 79
E_OLD, I_OLD = 39, 119
I_OLD_FND = 89
E_SEM, I_SEM = 149, 299
E_SEM_FND, I_SEM_FND = 109, 249
CAMP_EARLY, CAMP_REG = 149, 199
CAMP_EXPLORER = 79
STRIPE_PCT, STRIPE_FLAT = 0.029, 0.30

LEAN = 40  # domain, Zoom, parts, misc. Moodle/n8n/Pages already running.
HONEST = 120  # lean + Canva + liability share + VPS share
PLAN = 600  # Kajabi + $300 ads + tools from the original plan
GOAL_NET = 5000

RAMP = [
    ("Month 1 · founding", 15, 5, True),
    ("Month 3", 30, 10, False),
    ("Month 6", 60, 20, False),
    ("Month 9 · goal", 75, 25, False),
    ("Month 12", 90, 30, False),
]


def money(n: float) -> str:
    sign = "-" if n < 0 else ""
    return f"{sign}${abs(n):,.0f}"


def money2(n: float) -> str:
    sign = "-" if n < 0 else ""
    return f"{sign}${abs(n):,.2f}"


def fees(rev: float, invoices: int) -> float:
    if invoices <= 0 or rev <= 0:
        return 0.0
    return round(STRIPE_PCT * rev + STRIPE_FLAT * invoices, 2)


def pnl(explorers: int, inventors: int, e_price: float, i_price: float, overhead: float):
    rev = explorers * e_price + inventors * i_price
    n = explorers + inventors
    f = fees(rev, n)
    net = rev - f - overhead
    return {"e": explorers, "i": inventors, "n": n, "rev": rev, "fees": f, "oh": overhead, "net": net}


def pnl_mix(explorers: int, inventors: int, founding: bool, overhead: float, new_prices: bool = True):
    if founding:
        e_p, i_p = (E_FND, I_FND) if new_prices else (E_FND, I_OLD_FND)
    else:
        e_p, i_p = (E_PUB, I_PUB) if new_prices else (E_OLD, I_OLD)
    return pnl(explorers, inventors, e_p, i_p, overhead)


def locked_ramp(e_total: int, i_total: int, e_found: int = 15, i_found: int = 5, new_prices: bool = True):
    """Founders stay at founding rates; extras pay public."""
    e_f = min(e_found, e_total)
    i_f = min(i_found, i_total)
    e_p = e_total - e_f
    i_p = i_total - i_f
    if new_prices:
        rev = e_f * E_FND + e_p * E_PUB + i_f * I_FND + i_p * I_PUB
    else:
        rev = e_f * E_FND + e_p * E_OLD + i_f * I_OLD_FND + i_p * I_OLD
    n = e_total + i_total
    f = fees(rev, n)
    return rev, f, n


def members_for_net(target_net: float, overhead: float, e_price: float, i_price: float, inventor_share: float) -> float:
    """Approximate members needed. Fees ~3% + 0.30/member; solve iteratively."""
    blend = (1 - inventor_share) * e_price + inventor_share * i_price
    if blend <= 0:
        return float("inf")
    n = 1.0
    for _ in range(20):
        rev = n * blend
        f = STRIPE_PCT * rev + STRIPE_FLAT * n
        # net = rev - f - overhead = target
        # n*blend*(1-pct) - 0.30 n - overhead = target
        n = (target_net + overhead) / (blend * (1 - STRIPE_PCT) - STRIPE_FLAT)
        if n <= 0:
            return float("inf")
    return n


def break_even_explorers(overhead: float, price: float) -> float:
    # net = n*p - (0.029 n p + 0.30 n) - oh = 0
    return overhead / (price * (1 - STRIPE_PCT) - STRIPE_FLAT)


# ---------- SVG helpers ----------
NAVY, PANEL, INK, INK2, LINE = "#0F1626", "#16203A", "#E6EBF4", "#A3AEC4", "#2A3656"
ACCENT, GREEN, BLUE, RED = "#FF8A4C", "#4CC9A4", "#7FA6E8", "#E85D5D"


def svg_wrap(inner: str, w: int, h: int, title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">
  <rect width="{w}" height="{h}" fill="{PANEL}" rx="12"/>
  <text x="20" y="28" fill="{INK}" font-family="IBM Plex Sans, system-ui, sans-serif" font-size="14" font-weight="600">{title}</text>
  {inner}
</svg>'''


def grouped_bars(title: str, labels: list[str], series: list[tuple[str, list[float], str]], ylabel: str = "USD") -> str:
    w, h = 760, 320
    pad_l, pad_r, pad_t, pad_b = 64, 20, 48, 56
    plot_w, plot_h = w - pad_l - pad_r, h - pad_t - pad_b
    groups = len(labels)
    nser = len(series)
    all_vals = [v for _, vals, _ in series for v in vals]
    vmax = max(all_vals) * 1.12 if all_vals else 1
    vmin = min(0, min(all_vals))
    span = vmax - vmin if vmax != vmin else 1
    gap = plot_w / groups
    bar_w = gap * 0.32
    inner = [f'<text x="18" y="48" fill="{INK2}" font-size="11" font-family="IBM Plex Sans, system-ui, sans-serif" transform="rotate(-90 18 160)">{ylabel}</text>']
    # y ticks
    for t in range(5):
        yv = vmin + span * t / 4
        y = pad_t + plot_h - (yv - vmin) / span * plot_h
        inner.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="{LINE}" stroke-width="1"/>')
        inner.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" fill="{INK2}" font-size="11" text-anchor="end" font-family="IBM Plex Sans, system-ui, sans-serif">{money(yv)}</text>')
    for gi, lab in enumerate(labels):
        gx = pad_l + gi * gap + gap * 0.18
        for si, (_, vals, color) in enumerate(series):
            v = vals[gi]
            bh = (v - vmin) / span * plot_h
            x = gx + si * (bar_w + 4)
            y = pad_t + plot_h - bh
            if v < 0:
                y0 = pad_t + plot_h - (0 - vmin) / span * plot_h
                inner.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bar_w:.1f}" height="{abs(bh):.1f}" fill="{color}" rx="3"/>')
            else:
                inner.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{max(bh,0):.1f}" fill="{color}" rx="3"/>')
        inner.append(f'<text x="{pad_l + gi * gap + gap/2:.1f}" y="{h-18}" fill="{INK2}" font-size="11" text-anchor="middle" font-family="IBM Plex Sans, system-ui, sans-serif">{lab}</text>')
    lx = pad_l
    for name, _, color in series:
        inner.append(f'<rect x="{lx}" y="{h-42}" width="10" height="10" fill="{color}" rx="2"/>')
        inner.append(f'<text x="{lx+14}" y="{h-33}" fill="{INK2}" font-size="11" font-family="IBM Plex Sans, system-ui, sans-serif">{name}</text>')
        lx += 140
    return svg_wrap("\n".join(inner), w, h, title)


def hbars(title: str, rows: list[tuple[str, float, str]], w: int = 760, h: int | None = None) -> str:
    h = h or (56 + 36 * len(rows))
    pad_l, pad_r, pad_t, pad_b = 210, 70, 48, 20
    plot_w = w - pad_l - pad_r
    vals = [v for _, v, _ in rows]
    vmax = max(max(vals), 1) * 1.08
    inner = []
    for i, (lab, v, color) in enumerate(rows):
        y = pad_t + i * 36
        bw = max(0, v / vmax * plot_w)
        inner.append(f'<text x="{pad_l-10}" y="{y+16}" fill="{INK2}" font-size="12" text-anchor="end" font-family="IBM Plex Sans, system-ui, sans-serif">{lab}</text>')
        inner.append(f'<rect x="{pad_l}" y="{y+2}" width="{plot_w}" height="22" fill="{NAVY}" rx="4"/>')
        inner.append(f'<rect x="{pad_l}" y="{y+2}" width="{bw:.1f}" height="22" fill="{color}" rx="4"/>')
        inner.append(f'<text x="{pad_l+bw+8:.1f}" y="{y+18}" fill="{INK}" font-size="12" font-family="IBM Plex Mono, ui-monospace, monospace">{money(v)}</text>')
    return svg_wrap("\n".join(inner), w, h, title)


def line_chart(title: str, xs: list[float], series: list[tuple[str, list[float], str]], xlabel: str, ylabel: str) -> str:
    w, h = 760, 320
    pad_l, pad_r, pad_t, pad_b = 64, 20, 48, 56
    plot_w, plot_h = w - pad_l - pad_r, h - pad_t - pad_b
    ymin, ymax = 0, max(max(s[1]) for s in series) * 1.12
    xmin, xmax = min(xs), max(xs)
    def xpix(x):
        return pad_l + (x - xmin) / (xmax - xmin) * plot_w
    def ypix(y):
        return pad_t + plot_h - (y - ymin) / (ymax - ymin) * plot_h
    inner = []
    for t in range(5):
        yv = ymin + (ymax - ymin) * t / 4
        y = ypix(yv)
        inner.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="{LINE}" stroke-width="1"/>')
        inner.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" fill="{INK2}" font-size="11" text-anchor="end" font-family="IBM Plex Sans, system-ui, sans-serif">{money(yv) if ylabel=="USD" else f"{yv:.0f}"}</text>')
    for name, ys, color in series:
        pts = " ".join(f"{xpix(x):.1f},{ypix(y):.1f}" for x, y in zip(xs, ys))
        inner.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{pts}"/>')
        inner.append(f'<circle cx="{xpix(xs[-1]):.1f}" cy="{ypix(ys[-1]):.1f}" r="3.5" fill="{color}"/>')
    for i, x in enumerate(xs):
        if i % max(1, len(xs)//6) == 0 or i == len(xs) - 1:
            inner.append(f'<text x="{xpix(x):.1f}" y="{h-18}" fill="{INK2}" font-size="11" text-anchor="middle" font-family="IBM Plex Sans, system-ui, sans-serif">{x:g}</text>')
    inner.append(f'<text x="{w/2}" y="{h-4}" fill="{INK2}" font-size="11" text-anchor="middle" font-family="IBM Plex Sans, system-ui, sans-serif">{xlabel}</text>')
    lx = pad_l
    for name, _, color in series:
        inner.append(f'<rect x="{lx}" y="36" width="10" height="10" fill="{color}" rx="2"/>')
        inner.append(f'<text x="{lx+14}" y="45" fill="{INK2}" font-size="11" font-family="IBM Plex Sans, system-ui, sans-serif">{name}</text>')
        lx += 170
    return svg_wrap("\n".join(inner), w, h, title)


# ---------- compute ----------
old_rev, new_rev, old_net_plan, new_net_lean, new_net_honest, new_net_plan = [], [], [], [], [], []
labels = []
ramp_rows = []
for name, e, i, founding in RAMP:
    labels.append(name.split("·")[0].strip())
    o = pnl_mix(e, i, founding, PLAN, new_prices=False)
    n = pnl_mix(e, i, founding, LEAN, new_prices=True)
    nh = pnl_mix(e, i, founding, HONEST, new_prices=True)
    np_ = pnl_mix(e, i, founding, PLAN, new_prices=True)
    old_rev.append(o["rev"])
    new_rev.append(n["rev"])
    old_net_plan.append(o["net"])
    new_net_lean.append(n["net"])
    new_net_honest.append(nh["net"])
    new_net_plan.append(np_["net"])
    rev_l, f_l, _ = locked_ramp(e, i, new_prices=True)
    ramp_rows.append((name, e, i, founding, o, n, nh, np_, rev_l, f_l))

scenarios = [
    ("10 Explorer founding, 0 Inventor", 10, 0, True),
    ("10 Explorer founding + 1 Inventor founding", 10, 1, True),
    ("15 Sentinel, all Explorer founding", 15, 0, True),
    ("12 Explorer + 3 Inventor founding", 12, 3, True),
    ("15 Explorer + 5 Inventor founding (plan M1 headcount)", 15, 5, True),
    ("20 founders: 15 Explorer + 5 Inventor, new rates", 15, 5, True),
    ("20 founders: 10 Explorer + 10 Inventor", 10, 10, True),
    ("Stuck 6 months: 10 Explorer public, 0 Inventor", 10, 0, False),
]

scenario_calcs = []
for name, e, i, founding in scenarios:
    scenario_calcs.append({
        "name": name,
        "lean": pnl_mix(e, i, founding, LEAN, True),
        "honest": pnl_mix(e, i, founding, HONEST, True),
        "plan": pnl_mix(e, i, founding, PLAN, True),
        "founding": founding,
        "e": e,
        "i": i,
    })

# 12-month stuck at 10 founding explorers
stuck = []
cash = 0.0
for m in range(1, 13):
    p = pnl(10, 0, E_FND, I_FND, LEAN)
    # month 1 extra: 10 patches ~$6 each
    extra = 60 if m == 1 else 0
    net = p["net"] - extra
    cash += net
    stuck.append((m, p["rev"], net, cash))

be_lean = break_even_explorers(LEAN, E_FND)
be_honest = break_even_explorers(HONEST, E_FND)
be_plan = break_even_explorers(PLAN, E_FND)
be_lean_pub = break_even_explorers(LEAN, E_PUB)

shares = [i / 20 for i in range(0, 21)]
need_lean = [members_for_net(GOAL_NET, LEAN, E_PUB, I_PUB, s) for s in shares]
need_honest = [members_for_net(GOAL_NET, HONEST, E_PUB, I_PUB, s) for s in shares]
need_plan = [members_for_net(GOAL_NET, PLAN, E_PUB, I_PUB, s) for s in shares]
need_old = [members_for_net(GOAL_NET, PLAN, E_OLD, I_OLD, s) for s in shares]

m9_new_lean = pnl_mix(75, 25, False, LEAN, True)
m9_new_honest = pnl_mix(75, 25, False, HONEST, True)
m9_new_plan = pnl_mix(75, 25, False, PLAN, True)
m9_old_plan = pnl_mix(75, 25, False, PLAN, False)
m9_locked_rev, m9_locked_fees, m9_n = locked_ramp(75, 25, True)
m9_locked_lean = m9_locked_rev - m9_locked_fees - LEAN
m9_locked_honest = m9_locked_rev - m9_locked_fees - HONEST

# Inventor session fill
inventor_fill = []
for k in range(0, 13):
    inventor_fill.append(pnl(0, k, E_FND, I_FND, 0))  # contribution before overhead

# hours
H_NO_OH = 5.5 * 4.33  # ~24 h/mo without office hour
H_OH = 7.5 * 4.33  # ~32.5 h/mo with office hour
H_OH_SHORT = (5.5 + 0.5) * 4.33  # 30-min office hour ~26 h/mo

# charts
chart_ramp = grouped_bars(
    "Monthly revenue on the original headcount ramp",
    labels,
    [
        ("Old prices $39 / $119", old_rev, BLUE),
        ("Live prices $39 / $99", new_rev, ACCENT),
    ],
)
chart_net = grouped_bars(
    "Month-9 net vs $5,000 goal (75 Explorer / 25 Inventor)",
    ["Old + $600", "New + $600", "New + honest $120", "New + lean $40", "New + locked founders, lean"],
    [("Net", [m9_old_plan["net"], m9_new_plan["net"], m9_new_honest["net"], m9_new_lean["net"], m9_locked_lean], GREEN)],
)
# fix chart_net - grouped_bars expects series of lists matching labels. That works with 5 labels and 1 series of 5.

chart_scen = hbars(
    "Net this month, 10 cheap seats (lean $40 overhead)",
    [
        ("10 Explorer founding", scenario_calcs[0]["lean"]["net"], ACCENT),
        ("10 Explorer + 1 Inventor", scenario_calcs[1]["lean"]["net"], GREEN),
        ("15 Explorer founding", scenario_calcs[2]["lean"]["net"], BLUE),
        ("12 E + 3 I founding", scenario_calcs[3]["lean"]["net"], GREEN),
        ("Plan M1 headcount 15+5", scenario_calcs[4]["lean"]["net"], GREEN),
        ("10 E public, no founders", scenario_calcs[7]["lean"]["net"], BLUE),
    ],
)
chart_cost = hbars(
    "What 10 founding Explorers net under each cost stack",
    [
        ("Lean $40 (your stack)", scenario_calcs[0]["lean"]["net"], GREEN),
        ("Honest $120", scenario_calcs[0]["honest"]["net"], BLUE),
        ("Plan $600 (Kajabi + ads)", scenario_calcs[0]["plan"]["net"], RED),
    ],
)
chart_need = line_chart(
    "Members needed to clear $5,000 net / month",
    [s * 100 for s in shares],
    [
        ("New prices, lean $40", need_lean, GREEN),
        ("New prices, honest $120", need_honest, ACCENT),
        ("New prices, plan $600", need_plan, RED),
        ("Old $119 Inventor, plan $600", need_old, BLUE),
    ],
    "Inventor share of members (%)",
    "members",
)
# line chart ylabel members - money() is wrong. I passed ylabel that's not USD... my line_chart uses money if ylabel==USD else .0f. Good.

chart_stuck = line_chart(
    "Cash if you stay at 10 founding Explorers all year (lean costs)",
    [m for m, _, _, _ in stuck],
    [
        ("Monthly net", [n for _, _, n, _ in stuck], ACCENT),
        ("Cumulative cash", [c for _, _, _, c in stuck], GREEN),
    ],
    "Month",
    "USD",
)
chart_fill = line_chart(
    "Inventor office-hour contribution (founding $79, before overhead)",
    list(range(0, 13)),
    [("Monthly Inventor revenue − Stripe", [x["net"] for x in inventor_fill], ACCENT)],
    "Inventors in the one Thursday session",
    "USD",
)

charts = {
    "ramp": chart_ramp,
    "net": grouped_bars(
        "Month-9 net at 75 / 25 (public rates unless noted)",
        ["Old+$600", "New+$600", "New+$120", "New+$40", "Locked+$40"],
        [("Net $", [m9_old_plan["net"], m9_new_plan["net"], m9_new_honest["net"], m9_new_lean["net"], m9_locked_lean], GREEN)],
    ),
    "scen": chart_scen,
    "cost": chart_cost,
    "need": chart_need,
    "stuck": chart_stuck,
    "fill": chart_fill,
}
for k, svg in charts.items():
    (CHARTS / f"{k}.svg").write_text(svg, encoding="utf-8")


def tbl(headers, rows) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(r) + " |" for r in rows)
    return f"{head}\n{sep}\n{body}"


# ---------- markdown ----------
md = f"""# Robot Logic Lab — go-live math

**Date:** 1 October 2026. **Prices on the site now:** Explorer $39 / $29 founding, Inventor $99 / $79 founding, Inventor semester $299 / $249 founding. Kit $40–80, bought by the family.

This is a pre-launch review of the Fall 2026 rollout plan against those prices, with costs cut to what you actually run (GitHub Pages, Moodle at learn.mgit.io, n8n, Cloudflare). It plays the 10-Explorer and 1-Inventor cases before you charge anyone.

**Open the shareable version:** [rollout.html](rollout.html)

## Verdict

The $5,000/month net goal still works **if overhead stays lean**. It fails if you turn on the plan’s $600 stack (Kajabi + $300 ads) at 10 students.

Inventor tuition dropped $20/month versus the original plan ($119 → $99). On the plan’s month-9 headcount (75 Explorer / 25 Inventor) that is **$500 less revenue**. Lean costs ($40) more than replace Kajabi + ads ($425 of the $600). Net at month 9 on lean public rates: **{money(m9_new_lean['net'])}**, which clears $5,000. The same headcount on the old $600 stack: **{money(m9_new_plan['net'])}**, which misses.

**10 founding Explorers and zero Inventors is a viable studio, not a salary.** On lean costs it nets about **{money(scenario_calcs[0]['lean']['net'])}/month**. Two founding Explorers cover lean costs. Five cover the honest $120 stack (insurance + a VPS share). The original $600 stack needs **22** founding Explorers before it breaks even — that is why ads and Kajabi wait.

**One Inventor is worth running, as a short session.** The Thursday office hour is a fixed cost. One founding Inventor adds **{money(scenario_calcs[1]['lean']['rev'] - scenario_calcs[0]['lean']['rev'])}** revenue. Keep that session to **25–30 minutes** until four Inventors are in the room. Do not add Zoom, Kajabi, or ads for one person.

Go live on the waitlist and the Sentinel reconstruction now. Charge founding families when DNS works and five Explorers (or three Inventors) are ready to pay. Hold ads at $0.

## What changed versus the written plan

{tbl(
    ["Item", "Original plan", "Live offer / stack"],
    [
        ["Explorer", "$39 · founding $29", "Same"],
        ["Inventor", "$119 · founding $89", "$99 · founding $79"],
        ["Semester", "Not in the plan table", "Explorer $149 / Inventor $299"],
        ["Goal", "$5,000 net ≈ $5,800 gross ≈ 100 members", "Same goal; ~101 members at 25% Inventor on lean costs"],
        ["Overhead", "$600 + 3% fees (Kajabi $125, ads $300, tools $175)", "Lean $40 or honest $120. Pages, Moodle, n8n, Cloudflare already exist"],
        ["Mix", "3 of 4 Explorer", "Same assumption unless Sentinel families pick Inventor"],
        ["Time", "5–8 hours/week, office hour 90 min", "Skip office hour at 0 Inventors; 30 min until 4 Inventors"],
    ],
)}

Industry study check: Inventor semester **$299 for 12 live sessions** sits in the Create & Learn / Coding with Kids band ($284–$420 for twelve). Monthly Inventor $99 is $299 / 3 months. Explorer is the self-paced club and was never that 12-session live product.

## Cost stack — keep it boring

{tbl(
    ["Line", "Plan $600", "Lean $40 (use this at launch)", "Honest $120 (once kids are paying)"],
    [
        ["Course platform", "$100–150 Kajabi / Teachable", "$0 Moodle you already run", "$25 VPS share"],
        ["Live video", "$15 Zoom", "$15 Zoom, or $0 Meet", "$16"],
        ["Design", "$30", "$0 Canva free", "$15 Canva Pro"],
        ["Ads", "$300 from month 3 in the plan", "$0 until the starter challenge converts", "$0 until month 6"],
        ["Insurance, domain, parts", "$100", "$25 domain + demo parts", "$40 liability + $25 parts"],
        ["n8n / Cloudflare / Pages", "not in the plan", "$0 already on", "$0"],
        ["Stripe", "3% of revenue", "2.9% + $0.30 per invoice", "same"],
        ["GN2R patch mail", "not costed", "$6 × paid founders, once", "same"],
    ],
)}

Lean $40 is domain + Zoom + a parts jar. Honest $120 adds insurance and a fair Moodle share. Do not buy a second course platform.

**Break-even Explorers (founding $29):** lean **{be_lean:.1f}** → 2 families. Honest **{be_honest:.1f}** → 5 families. Plan $600 **{be_plan:.1f}** → 22 families.

## Original ramp, rerun at live prices

Plan note: month 1 used founding rates; later rows used full public rates and ignored the founder lock. The last column shows the lock (15 Explorer + 5 Inventor stay at founding rates).

{tbl(
    ["Milestone", "E", "I", "Old revenue", "New revenue", "New net lean $40", "New net honest $120", "New net plan $600", "Locked founders revenue"],
    [
        [
            name, str(e), str(i),
            money(o["rev"]), money(n["rev"]),
            money(n["net"]), money(nh["net"]), money(np_["net"]),
            money(rev_l),
        ]
        for (name, e, i, founding, o, n, nh, np_, rev_l, f_l) in ramp_rows
    ],
)}

![Revenue ramp old vs new prices](charts/ramp.svg)

Month 9 at public rates, 75 / 25:

- Old prices + $600 overhead: net **{money(m9_old_plan['net'])}** (the plan’s “goal line”)
- New prices + $600: net **{money(m9_new_plan['net'])}** — **misses** $5,000 by about {money(GOAL_NET - m9_new_plan['net'])}
- New prices + honest $120: net **{money(m9_new_honest['net'])}** — **clears**
- New prices + lean $40: net **{money(m9_new_lean['net'])}** — **clears**
- Founders still locked, lean: revenue {money(m9_locked_rev)}, net **{money(m9_locked_lean)}** — about the goal

![Month 9 net under each stack](charts/net.svg)

To hit $5,000 net at a 25% Inventor mix and public rates you need about **{need_lean[5]:.0f} members** on lean costs, **{need_honest[5]:.0f}** on honest, **{need_plan[5]:.0f}** on the $600 stack. The old $119 Inventor price needed about **{need_old[5]:.0f}** on $600. The price cut costs you ~9 members of mix, or about $500/month at month 9. Lean ops give that back.

![Members to $5k vs Inventor share](charts/need.svg)

Year-1 plan “≈ $53k revenue, ≈ $44k you keep” assumed the old blend and $600 overhead. At the new blend (~$54/member vs $59) and lean costs, 60 average members is about $39k revenue and ~$33k net — short of that year-1 story unless you grow faster than 60 average or sell camp. Camp at 40 early-bird non-members is another **{money(40 * CAMP_EARLY)}** in June/July.

## Play-through: 10 cheap seats, and one Inventor

![Net on the cheap-seat scenarios](charts/scen.svg)

![10 Explorers under each cost stack](charts/cost.svg)

{tbl(
    ["Scenario", "People", "Revenue", "Stripe", "Net lean $40", "Net honest $120", "Net plan $600"],
    [
        [
            s["name"],
            f'{s["e"]} E + {s["i"]} I',
            money(s["lean"]["rev"]),
            money2(s["lean"]["fees"]),
            money(s["lean"]["net"]),
            money(s["honest"]["net"]),
            money(s["plan"]["net"]),
        ]
        for s in scenario_calcs
    ],
)}

### 10 Explorers, 0 Inventors

Revenue **{money(scenario_calcs[0]['lean']['rev'])}** at founding $29. Stripe about {money2(scenario_calcs[0]['lean']['fees'])}.

- Lean: **{money(scenario_calcs[0]['lean']['net'])}** in the black. This is coffee-and-parts money, and it pays for the recordings you already wanted to make.
- Honest (insurance on): **{money(scenario_calcs[0]['honest']['net'])}**.
- Plan $600: **{money(scenario_calcs[0]['plan']['net'])}**. That is a loss. Do not run ads or Kajabi here.

Time: skip Thursday office hour. About 5.5 hours/week of recording, community, and marketing ≈ **{H_NO_OH:.0f} hours/month**. Effective **{scenario_calcs[0]['lean']['net'] / H_NO_OH:.0f}/hour** on lean net. That is below a roboticist wage. Treat months 1–3 as **building the library**, not drawing pay. The unit that scales is recorded missions, not live seats.

If this is the whole year:

![Cash if you never grow past 10 founding Explorers](charts/stuck.svg)

Twelve months at 10 founding Explorers, lean costs, $60 of patches in month 1: about **{money(stuck[-1][3])}** cash. Fine as a studio. Not the $44k year-1 keep figure.

### 10 Explorers + 1 Inventor

Revenue **{money(scenario_calcs[1]['lean']['rev'])}**. The extra Inventor is **$79** (founding). Lean net **{money(scenario_calcs[1]['lean']['net'])}**.

The trap: a 90-minute office hour for one kid is **~8–9 hours/month** of live time for $76 after Stripe, about **$9/hour** on the live slice. The Explorer recordings still happen either way.

**Fix:** 25–30 minute Thursday for 1–3 Inventors. Same promise (live roboticist, live feedback), smaller room. At **4 founding Inventors** the one session brings **{money(4 * I_FND)}** before fees, still one slot on the calendar.

![Fill the one Inventor session](charts/fill.svg)

Do not open a second office hour until **40 Inventors** (the plan’s own guardrail). One Inventor is not a reason to buy Zoom Rooms, a community moderator, or ads.

### 15 Sentinel families (the email list)

If all 15 take founding Explorer: lean net **{money(scenario_calcs[2]['lean']['net'])}**.  
If 12 Explorer + 3 Inventor: **{money(scenario_calcs[3]['lean']['net'])}**.  
If they match plan month-1 headcount (15 + 5, which is 20 people): **{money(scenario_calcs[4]['lean']['net'])}**.

Hold the 15 at the front of the 20 founding spots. Even a full-Explorer take from that list covers honest costs with room.

## Semester and camp cash (lumpier)

Monthly is smoother. Semester is better cash in September and January.

{tbl(
    ["If these 10 cheap seats pay once", "Cash now", "Then"],
    [
        ["10 Explorer founding monthly", money(10 * E_FND), "Repeats every month until they churn"],
        ["10 Explorer founding semester ($109)", money(10 * E_SEM_FND), "Silent until the next semester unless they convert to monthly"],
        ["10 Explorer public semester ($149)", money(10 * E_SEM), "Same shape, public rate"],
        ["1 Inventor founding semester ($249)", money(I_SEM_FND), "12 live sessions already paid"],
        ["1 Inventor public semester ($299)", money(I_SEM), "Matches the industry study"],
        ["10 camp early-bird, not members", money(10 * CAMP_EARLY), "Four weeks, then a $1 first-month fall offer"],
    ],
)}

A semester Inventor at $299 is the study course. Do not discount it on the public page; founding $249 is the only cut, and it closes at 20 families.

Inventors already paying monthly get camp free. At 1 Inventor that gift costs you $149 of list price you were unlikely to collect twice anyway. Leave the perk — it is a reason to pick Inventor.

## Time, wage, and what “realistic” means

{tbl(
    ["Mode", "Hours/month", "Example net (lean)", "Implied $/hour"],
    [
        ["10 Explorer, no office hour", f"{H_NO_OH:.0f}", money(scenario_calcs[0]["lean"]["net"]), f"${scenario_calcs[0]['lean']['net'] / H_NO_OH:.0f}"],
        ["10 E + 1 I, 90-min office hour", f"{H_OH:.0f}", money(scenario_calcs[1]["lean"]["net"]), f"${scenario_calcs[1]['lean']['net'] / H_OH:.0f}"],
        ["10 E + 1 I, 30-min office hour", f"{H_OH_SHORT:.0f}", money(scenario_calcs[1]["lean"]["net"]), f"${scenario_calcs[1]['lean']['net'] / H_OH_SHORT:.0f}"],
        ["Plan month 9, 75/25, lean", f"{H_OH:.0f}", money(m9_new_lean["net"]), f"${m9_new_lean['net'] / H_OH:.0f}"],
    ],
)}

The plan’s “5–8 hours/week” only becomes a real wage after tens of members, because most of that week is content and marketing with near-zero marginal cost. **Do not hire an editor, buy a filming kit, or run $300 ads** until net is past $2,000/month (the plan’s own unlock table).

## Does it meet the rollout plan?

{tbl(
    ["Plan checkpoint", "Met?"],
    [
        [f"$5,000 net at ~100 members", f"Yes on lean/honest costs ({money(m9_new_lean['net'])} / {money(m9_new_honest['net'])} at 100 people, 25% Inventor). No if you spend $600/month from day one."],
        ["Month 1 founding 15 E + 5 I = $880", f"New founding mix is {money(pnl_mix(15,5,True,0,True)['rev'])} revenue ({money(pnl_mix(15,5,True,0,True)['rev'] - 880)} vs plan). Still a fine founding month on lean costs."],
        ["3 of 4 Explorer", "Still the right mix. Explorer is the scalable product. Inventor is the live room you fill."],
        ["Industry $299 / 12 live", "Yes. That is Inventor semester. Monthly $99 is the same course on a club bill."],
        ["5–8 hours/week", "Yes if office hour shrinks at n=1 and content is batched. No if you 1:1 every Explorer."],
        ["Year 1 keep ≈ $44k", "Optimistic. Needs the ramp, not 10 stuck Explorers. Camp plus a 100-member second half can still land near it."],
        ["Churn under 8%", "Unchanged and still the number that matters after month 3."],
        ["Utah ESA fit", "$299 is 7.5% of a $4,000 Utah Fits All award. Keep kit as a separate $40–80 materials line."],
    ],
)}

## Go-live gates

1. Finish Cloudflare: `@` and `www` CNAME to `wegunterjr.github.io`, DNS only (grey cloud). Do not send the family email until `https://gunterbots.com` loads.
2. Charge **after** five Explorers or three Inventors say yes. The waitlist can collect before that.
3. Overhead cap at launch: **$40**. No Kajabi, no ads, no second Zoom account.
4. Office hour: **off** at 0 Inventors, **30 minutes** at 1–3, **60–90 minutes** at 4+.
5. Mail patches only after a paid founding seat, not with the free Sentinel login.
6. Buy liability insurance when the 6th paying kid joins (honest stack), not before.
7. Ads $0 until the 5-day starter challenge converts waitlist → paid at 5%+. Then $50 tests, not $300.
8. Sibling +$10 and “10 months pay for 12” are still good levers from the plan. They are not on the page yet; add them after the first 20.

## Risks if you ignore the cheap-seat case

- Spending the plan’s $600 on 10 Explorers lights about **{money(-scenario_calcs[0]['plan']['net'])}/month**.
- A 90-minute office hour for one Inventor trains you to hate the live product. Shorten it.
- Founding rates locked for life: 20 founders at 15/5 drag month-9 revenue from {money(m9_new_lean['rev'])} to {money(m9_locked_rev)}. That is acceptable. Do not extend founding past 20.
- Semester-only Explorers disappear in January. Keep a $1 first-month bridge into year-round, same as the camp→fall offer in the plan.

## Method

Revenue = Explorer count × Explorer price + Inventor count × Inventor price. Stripe = 2.9% + $0.30 per subscription invoice. Net = revenue − Stripe − overhead. Lean overhead $40, honest $120, plan $600. Mix 75/25 matches the written plan. Kit is not tuition. Moodle, n8n, GitHub Pages, and Cloudflare are treated as already paid. Figures are planning math, not a forecast of demand.
"""

(ROOT / "rollout.md").write_text(md, encoding="utf-8")

# ---------- HTML ----------
def html_table(headers, rows) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for r in rows:
        tds = "".join(f"<td>{c}</td>" for c in r)
        body.append(f"<tr>{tds}</tr>")
    return f"<div class='tbl'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"


def kpi(k, v, sub=""):
    return f'<div class="kpi"><div class="k">{k}</div><div class="v">{v}</div><div class="s">{sub}</div></div>'


scen_rows = [
    [
        s["name"],
        f'{s["e"]} E + {s["i"]} I',
        money(s["lean"]["rev"]),
        money2(s["lean"]["fees"]),
        money(s["lean"]["net"]),
        money(s["honest"]["net"]),
        money(s["plan"]["net"]),
    ]
    for s in scenario_calcs
]
ramp_html_rows = [
    [
        name, str(e), str(i),
        money(o["rev"]), money(n["rev"]),
        money(n["net"]), money(nh["net"]), money(np_["net"]),
        money(rev_l),
    ]
    for (name, e, i, founding, o, n, nh, np_, rev_l, f_l) in ramp_rows
]

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Robot Logic Lab — go-live math</title>
  <meta name="robots" content="noindex" />
  <meta name="description" content="Pre-launch scenarios for Robot Logic Lab: 10 Explorers, one Inventor, and whether $5,000 net still holds at the new prices." />
  <link rel="icon" type="image/svg+xml" href="../favicon.svg" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --paper:#0F1626; --panel:#16203A; --ink:#E6EBF4; --ink-2:#A3AEC4; --line:#2A3656;
      --accent:#FF8A4C; --accent-deep:#E8590C; --green:#4CC9A4; --blue:#7FA6E8; --red:#E85D5D;
      --display:"Chakra Petch",sans-serif; --body:"IBM Plex Sans",system-ui,sans-serif; --mono:"IBM Plex Mono",monospace;
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{
      margin:0; background:var(--paper); color:var(--ink); font-family:var(--body); line-height:1.55;
      background-image:linear-gradient(rgba(230,235,244,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(230,235,244,.045) 1px,transparent 1px);
      background-size:24px 24px;
    }}
    .wrap {{ max-width:920px; margin:0 auto; padding:0 1.25rem; }}
    header.hero {{ padding:2.5rem 0 1.5rem; }}
    .label {{ font-family:var(--mono); font-size:.75rem; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); }}
    h1 {{ font-family:var(--display); font-size:clamp(2rem,5vw,3.1rem); line-height:1.1; margin:.4rem 0; }}
    h2 {{ font-family:var(--display); font-size:1.7rem; margin:2.4rem 0 .6rem; }}
    h3 {{ font-family:var(--display); font-size:1.15rem; margin:1.2rem 0 .4rem; }}
    p {{ color:var(--ink-2); }}
    a {{ color:var(--accent); }}
    .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:.75rem; margin:1.2rem 0 1.6rem; }}
    .kpi {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:.9rem 1rem; }}
    .kpi .k {{ font-family:var(--mono); font-size:.7rem; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-2); }}
    .kpi .v {{ font-family:var(--display); font-size:1.45rem; color:var(--ink); margin:.2rem 0; }}
    .kpi .s {{ font-size:.8rem; color:var(--ink-2); }}
    .callout {{ background:#15342C; border:1px solid #2a5a4c; border-radius:10px; padding:1rem 1.1rem; color:var(--ink); margin:1rem 0; }}
    .warn {{ background:#3A2419; border:1px solid #6a3b1e; }}
    .chart {{ margin:1rem 0 1.4rem; overflow:auto; background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:.4rem; }}
    .chart svg {{ display:block; width:100%; height:auto; }}
    .tbl {{ overflow:auto; margin:1rem 0 1.4rem; border:1px solid var(--line); border-radius:10px; }}
    table {{ border-collapse:collapse; width:100%; font-size:.92rem; }}
    th, td {{ padding:.55rem .7rem; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }}
    th {{ font-family:var(--mono); font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-2); background:#121a30; }}
    td:nth-child(n+2) {{ font-variant-numeric:tabular-nums; }}
    tr:last-child td {{ border-bottom:0; }}
    ul {{ color:var(--ink-2); }}
    footer {{ padding:2rem 0 3rem; color:var(--ink-2); font-size:.9rem; }}
    nav.toc {{ display:flex; flex-wrap:wrap; gap:.5rem .9rem; margin:1rem 0 0; font-size:.9rem; }}
    @media print {{
      body {{ background:#fff; color:#111; background-image:none; }}
      p, ul, td {{ color:#222; }}
      .kpi, .chart, .tbl, .callout {{ break-inside:avoid; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <div class="wrap">
      <div class="label">Gunterbots school · 1 Oct 2026 · pre-launch</div>
      <h1>Go-live math for Robot Logic Lab</h1>
      <p>Does the $5,000/month rollout still hold at Inventor $99 / $299 a semester? What if you only get 10 Explorers, or one Inventor? This is the review before you charge anyone.</p>
      <nav class="toc">
        <a href="#verdict">Verdict</a>
        <a href="#costs">Costs</a>
        <a href="#ramp">Ramp</a>
        <a href="#ten">10 Explorers</a>
        <a href="#one">One Inventor</a>
        <a href="#gates">Go-live gates</a>
      </nav>
      <div class="kpis">
        {kpi("10 Explorers, lean net", money(scenario_calcs[0]['lean']['net']), "founding $29, 0 Inventors")}
        {kpi("Those 10 + 1 Inventor", money(scenario_calcs[1]['lean']['net']), "still skip $600 ads")}
        {kpi("Month 9 net, lean", money(m9_new_lean['net']), "75 Explorer / 25 Inventor")}
        {kpi("Break-even Explorers", f"{be_lean:.0f} lean / {be_honest:.0f} honest", "founding $29")}
      </div>
    </div>
  </header>
  <main class="wrap">
    <section id="verdict">
      <h2>Verdict</h2>
      <div class="callout">The $5,000 net goal still works if overhead stays lean. It fails if you turn on the plan’s $600 stack (Kajabi + $300 ads) while you only have 10 cheap seats.</div>
      <p>Inventor dropped $20/month versus the written plan ($119 → $99). On month-9 headcount that is $500 less revenue. You already run Moodle, n8n, GitHub Pages, and Cloudflare, so you do not need Kajabi. Lean costs ($40) replace that $500 and then some. Month 9 net on lean public rates: <b style="color:var(--ink)">{money(m9_new_lean['net'])}</b>. Same headcount on the $600 stack: <b style="color:var(--ink)">{money(m9_new_plan['net'])}</b>, which misses the goal.</p>
      <p><b style="color:var(--ink)">10 founding Explorers and zero Inventors is a viable studio, not a salary.</b> Lean net about {money(scenario_calcs[0]['lean']['net'])}/month. Two founding Explorers cover lean costs. Five cover the honest $120 stack. The $600 stack needs 22 founding Explorers before it breaks even.</p>
      <p><b style="color:var(--ink)">One Inventor is worth a short Thursday, not a 90-minute show.</b> The office hour is a fixed cost. Keep it to 25–30 minutes until four Inventors are in the room. Do not buy tools for one person.</p>
    </section>

    <section id="costs">
      <h2>Cost stack — keep it boring</h2>
      <p>The original plan assumed a paid course platform and $300 ads. Your real stack is already paid for. Use lean $40 at launch. Move to honest $120 when the sixth paying kid joins (insurance).</p>
      {html_table(
        ["Line", "Plan $600", "Lean $40 at launch", "Honest $120 later"],
        [
          ["Course platform", "$100–150 Kajabi / Teachable", "$0 Moodle you already run", "$25 VPS share"],
          ["Live video", "$15 Zoom", "$15 Zoom or $0 Meet", "$16"],
          ["Design", "$30", "$0 Canva free", "$15 Canva Pro"],
          ["Ads", "$300", "$0 until the starter converts", "$0 until month 6"],
          ["Insurance, domain, parts", "$100", "$25 domain + parts", "$40 liability + parts"],
          ["n8n / Cloudflare / Pages", "not in the plan", "$0 already on", "$0"],
          ["Stripe", "~3% of revenue", "2.9% + $0.30 / invoice", "same"],
          ["GN2R patch", "not costed", "$6 × paid founders, once", "same"],
        ],
      )}
      <p>Break-even founding Explorers at $29: <b style="color:var(--ink)">2 on lean, 5 on honest, 22 on the $600 plan stack.</b></p>
    </section>

    <section id="ramp">
      <h2>Original ramp, rerun at live prices</h2>
      <p>Explorer is still $39. Inventor is $99 public / $79 founding (was $119 / $89). Month 1 uses founding rates. Later rows use public rates, same as the written plan. The last column keeps 15 Explorer + 5 Inventor locked at founding rates.</p>
      <div class="chart">{charts['ramp']}</div>
      {html_table(
        ["Milestone", "E", "I", "Old rev", "New rev", "Net lean", "Net honest", "Net $600", "Locked rev"],
        ramp_html_rows,
      )}
      <div class="chart">{charts['net']}</div>
      <p>Members needed to clear $5,000 net at public rates, by Inventor mix:</p>
      <div class="chart">{charts['need']}</div>
      <p>At the plan’s 25% Inventor mix you need about <b style="color:var(--ink)">{need_lean[5]:.0f} members on lean costs</b>, {need_honest[5]:.0f} on honest, {need_plan[5]:.0f} on $600. The old $119 price needed about {need_old[5]:.0f} on $600. Lean ops buy back the $20 Inventor cut.</p>
    </section>

    <section id="ten">
      <h2>Play-through: 10 cheap seats</h2>
      <div class="chart">{charts['scen']}</div>
      <div class="chart">{charts['cost']}</div>
      {html_table(
        ["Scenario", "People", "Revenue", "Stripe", "Net lean $40", "Net honest $120", "Net plan $600"],
        scen_rows,
      )}
      <h3>10 Explorers, 0 Inventors</h3>
      <p>Revenue {money(scenario_calcs[0]['lean']['rev'])} at founding $29. Lean net <b style="color:var(--ink)">{money(scenario_calcs[0]['lean']['net'])}</b>. Honest {money(scenario_calcs[0]['honest']['net'])}. Plan $600: <b style="color:var(--ink)">{money(scenario_calcs[0]['plan']['net'])}</b> — a loss. Skip Thursday office hour. About {H_NO_OH:.0f} hours/month of recording and community, ~${scenario_calcs[0]['lean']['net'] / H_NO_OH:.0f}/hour. Treat months 1–3 as building the library.</p>
      <div class="chart">{charts['stuck']}</div>
      <p>If you never grow past those 10 founding Explorers, twelve months of lean costs (plus $60 of patches in month 1) leaves about <b style="color:var(--ink)">{money(stuck[-1][3])}</b> cash. A studio. Not the plan’s $44k year-1 keep figure.</p>
    </section>

    <section id="one">
      <h2>What if you only get one Inventor?</h2>
      <p>10 founding Explorers + 1 founding Inventor: revenue {money(scenario_calcs[1]['lean']['rev'])}, lean net <b style="color:var(--ink)">{money(scenario_calcs[1]['lean']['net'])}</b>. The extra $79 does not change overhead. A 90-minute office hour for one kid is ~8–9 live hours/month for $76 after Stripe, about $9/hour on the live slice.</p>
      <div class="warn callout">Keep Thursday to 25–30 minutes until four Inventors are in the room. One session, one calendar slot. The plan already says a second office hour starts at 40 Inventors.</div>
      <div class="chart">{charts['fill']}</div>
      <p>Four founding Inventors in that one session: {money(4 * I_FND)} before fees, still one Thursday. That is the live product. Explorer remains the scalable one.</p>
      <h3>15 Sentinel families</h3>
      <p>All Explorer founding: lean net {money(scenario_calcs[2]['lean']['net'])}. Twelve Explorer + three Inventor: {money(scenario_calcs[3]['lean']['net'])}. Plan month-1 headcount (15+5): {money(scenario_calcs[4]['lean']['net'])}. Hold those 15 at the front of the 20 founding spots.</p>
      <h3>Semester cash</h3>
      <p>10 Explorer founding semesters = {money(10 * E_SEM_FND)} now, then quiet until spring. 1 Inventor public semester = {money(I_SEM)}, the industry-study course. Inventors get summer camp free; at n=1 that perk is cheap. Leave it.</p>
    </section>

    <section id="gates">
      <h2>Does it meet the rollout plan?</h2>
      {html_table(
        ["Checkpoint", "Met?"],
        [
          ["$5,000 net at ~100 members", f"Yes on lean/honest ({money(m9_new_lean['net'])} / {money(m9_new_honest['net'])} at 75/25). No on $600/month from day one."],
          ["Month 1 founding 15+5 = $880", f"New founding mix {money(pnl_mix(15,5,True,0,True)['rev'])} revenue. Fine on lean costs."],
          ["3 of 4 Explorer", "Still right. Explorer scales. Inventor is a room you fill."],
          ["Industry $299 / 12 live", "Yes — Inventor semester. Monthly $99 is that course on a club bill."],
          ["5–8 hours/week", "Yes if office hour shrinks at n=1 and content is batched."],
          ["Year 1 keep ≈ $44k", "Needs the ramp, not 10 stuck Explorers. Camp can still help."],
          ["Utah ESA", "$299 is 7.5% of a $4,000 Utah Fits All award. Kit stays a separate $40–80 line."],
        ],
      )}
      <h2>Go-live gates</h2>
      <ol>
        <li>Finish Cloudflare: <code>@</code> and <code>www</code> CNAME to <code>wegunterjr.github.io</code>, DNS only. Do not send the family email until https://gunterbots.com loads.</li>
        <li>Charge after five Explorers or three Inventors say yes. The waitlist can collect before that.</li>
        <li>Overhead cap at launch: $40. No Kajabi, no ads, no second Zoom account.</li>
        <li>Office hour: off at 0 Inventors, 30 minutes at 1–3, 60–90 minutes at 4+.</li>
        <li>Mail patches only after a paid founding seat, not with the free Sentinel login.</li>
        <li>Buy liability insurance at the 6th paying kid, not before.</li>
        <li>Ads $0 until the 5-day starter converts waitlist → paid at 5%+. Then $50 tests, not $300.</li>
        <li>Sibling +$10 and “pay 10 months, get 12” are still good levers from the plan. Add them after the first 20.</li>
      </ol>
      <div class="callout">Go live on the waitlist and the Sentinel reconstruction now. Charge founding families when the domain works and five cheap seats (or three Inventors) are ready to pay.</div>
    </section>
  </main>
  <footer>
    <div class="wrap">
      Robot Logic Lab · a Gunterbots school · planning math, not a demand forecast · <a href="rollout.md">Markdown</a> · <a href="../index.html">Back to the club</a>
    </div>
  </footer>
</body>
</html>
"""

(ROOT / "rollout.html").write_text(html, encoding="utf-8")
print("Wrote", ROOT / "rollout.md")
print("Wrote", ROOT / "rollout.html")
print("Charts", list(CHARTS.glob("*.svg")))
print("M9 lean", round(m9_new_lean["net"]))
print("10E lean", round(scenario_calcs[0]["lean"]["net"]))
print("10E+1I lean", round(scenario_calcs[1]["lean"]["net"]))
print("10E plan", round(scenario_calcs[0]["plan"]["net"]))
print("BE", round(be_lean, 2), round(be_honest, 2), round(be_plan, 2))
