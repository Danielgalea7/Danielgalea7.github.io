#!/usr/bin/env python3
"""Builds the static portfolio (ES + EN) from real query results.

Data: ../data/*.json (results the owner ran in the BigQuery sandbox on 2026-10-12).
Output: ../site/
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
DATA = os.path.join(HERE, "..", "data")
SITE_URL = os.environ.get("SITE_URL", "https://danielgalea7.github.io").rstrip("/")

EMAIL = "darnite26@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/daniel-galea-romero-060941371/"
GITHUB = "https://github.com/Danielgalea7"
CREDLY = "https://www.credly.com/badges/53fe75b2-e19a-4265-aa9f-7e4d497fc33a/public_url"
CAPSTONE_REPO = "https://github.com/Danielgalea7/thelook-fintech-capstone"
CV = {"es": "/cv/daniel-galea-romero-cv-es.pdf", "en": "/cv/daniel-galea-romero-cv-en.pdf"}
HOME = {"es": "/", "en": "/en/"}
CASE = {"es": "/caso/thelook-fintech/", "en": "/en/case-study/thelook-fintech/"}

TL = json.load(open(os.path.join(DATA, "thelook-snapshot-2026-10-12.json")))
FT = json.load(open(os.path.join(DATA, "fintech-capstone.json")))

esc = html.escape


# ---------------------------------------------------------------- formatting
def num(x, lang, dec=0):
    s = f"{x:,.{dec}f}"
    if lang == "es":
        s = s.replace(",", " ").replace(".", ",").replace(" ", ".")
    return s


def pct(x, lang, dec=1):
    v = num(x, lang, dec)
    return f"{v} %" if lang == "es" else f"{v}%"


def musd(x, lang, dec=1):
    """Millions of dollars."""
    v = num(x / 1e6, lang, dec)
    return f"{v} M$" if lang == "es" else f"${v}M"


def kusd(x, lang, dec=1):
    v = num(x / 1e3, lang, dec)
    return f"{v} K$" if lang == "es" else f"${v}K"


# ---------------------------------------------------------------- code highlight
SQL_KW = r"""SELECT|FROM|WHERE|GROUP|BY|ORDER|AS|INNER|JOIN|ON|CREATE|OR|REPLACE|TABLE|LOAD|DATA|OVERWRITE|FILES|DISTINCT|WITH|CASE|WHEN|THEN|ELSE|END|AND|NOT|IN|IS|NULL|LIMIT|DESC|ASC|OVER|PROCEDURE|BEGIN|CALL|INSERT|INTO|CROSS|STRUCT|string|format|uris"""
SQL_FN = r"""COUNT|SUM|MIN|MAX|AVG|ROUND|DATE_DIFF|DATE_TRUNC|CURRENT_TIMESTAMP|CURRENT_DATE|NTILE|ST_GEOGPOINT|ST_DISTANCE|COALESCE|NULLIF|CONCAT|ARRAY_AGG|DATE_SUB|LEAST|SAFE_DIVIDE"""
LKML_KW = r"""measure|dimension|dimension_group|explore|join|type|sql|sql_on|relationship|timeframes|drill_fields|description|constant|value|export|connection"""


def highlight(code, lang="sql"):
    out = []
    pattern = re.compile(
        r"(--[^\n]*|#[^\n]*)"            # comments
        r"|('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")"  # strings
        r"|(`[^`]*`)"                     # identifiers in backticks
        r"|\b(\d+(?:\.\d+)?)\b"           # numbers
        r"|\b([A-Za-z_][A-Za-z_0-9]*)\b"  # words
        r"|(\s+|.)", re.S)
    kw = re.compile(rf"^(?:{SQL_KW})$", re.I) if lang == "sql" else re.compile(rf"^(?:{LKML_KW})$")
    fn = re.compile(rf"^(?:{SQL_FN})$", re.I)
    for m in pattern.finditer(code):
        com, st, bt, nu, wd, other = m.groups()
        if com is not None and (lang == "sql" and com.startswith("--") or lang == "lookml" and com.startswith("#")):
            out.append(f'<span class="c">{esc(com)}</span>')
        elif com is not None:
            out.append(esc(com))
        elif st is not None:
            out.append(f'<span class="s">{esc(st)}</span>')
        elif bt is not None:
            out.append(f'<span class="s">{esc(bt)}</span>')
        elif nu is not None:
            out.append(f'<span class="n">{nu}</span>')
        elif wd is not None:
            if fn.match(wd) and lang == "sql":
                out.append(f'<span class="f">{wd}</span>')
            elif kw.match(wd):
                out.append(f'<span class="k">{wd}</span>')
            else:
                out.append(esc(wd))
        else:
            out.append(esc(other))
    return "".join(out)


def code_block(code, lang="sql", copy=True):
    attr = ' data-copy' if copy else ''
    return (f'<div class="codewrap"><pre{attr} tabindex="0"><code class="language-{lang}">'
            f'{highlight(code.strip(), lang)}</code></pre></div>')


def sql_details(summary, code, lang="sql", open_=False):
    o = " open" if open_ else ""
    return f'<details class="sql"{o}><summary>{esc(summary)}</summary>{code_block(code, lang)}</details>'


# ---------------------------------------------------------------- icons
def icon(name):
    p = {
        "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
        "moon": '<path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/>',
        "down": '<path d="M12 4v12M6 11l6 6 6-6M5 20h14"/>',
        "arrow": '<path d="M7 17 17 7M9 7h8v8"/>',
        "back": '<path d="M15 6l-6 6 6 6"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
        "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
        "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
        "cloud": '<path d="M7 18a5 5 0 1 1 1.6-9.7A6 6 0 0 1 20 10a4 4 0 0 1-1 8z"/>',
        "people": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6.5 6.5 0 0 1 4 6"/>',
    }[name]
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{p}</svg>')


STAGE_ICONS = {
    # collect: inbox tray receiving
    "collect": '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 5v16M13 14l7 7 7-7"/><path d="M6 24h8l2 4h8l2-4h8v8a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3z"/></svg>',
    # process: funnel with gear dots
    "process": '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8h28l-11 13v10l-6 3V21z"/><circle cx="12" cy="4" r="1.2" fill="currentColor"/><circle cx="20" cy="4" r="1.2" fill="currentColor"/><circle cx="28" cy="4" r="1.2" fill="currentColor"/></svg>',
    # store: stacked cylinders
    "store": '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="20" cy="9" rx="12" ry="4"/><path d="M8 9v8c0 2.2 5.4 4 12 4s12-1.8 12-4V9M8 17v8c0 2.2 5.4 4 12 4s12-1.8 12-4v-8M8 25v6c0 2.2 5.4 4 12 4s12-1.8 12-4v-6"/></svg>',
    # analyze: magnifier over bars
    "analyze": '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 33V22M13 33V15M19 33v-8"/><circle cx="26" cy="15" r="7"/><path d="m31 20 5 5"/><path d="M4 33h22"/></svg>',
    # activate: lightning in a dashboard
    "activate": '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="7" width="30" height="22" rx="3"/><path d="M14 35h12M20 29v6"/><path d="m21 11-5 8h6l-3 7"/></svg>',
}
LINK_ARROW = '<svg class="link" viewBox="0 0 18 16" aria-hidden="true"><path d="M1 8h14M10 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

BRAND = ('<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="currentColor"/>'
         '<rect x="8" y="17" width="3.5" height="7" rx="1" fill="var(--bg)"/><rect x="14.25" y="12" width="3.5" height="12" rx="1" fill="var(--bg)"/>'
         '<rect x="20.5" y="8" width="3.5" height="16" rx="1" fill="var(--accent)"/></svg>')


# ---------------------------------------------------------------- charts
def bars(items, lang, label_w=120, crit=None, hl=None, muted=None, unit_fmt=None, title=None, sub=None, note=None, table_head=None):
    """items: list of (label, value, display, tip). Width relative to max."""
    mx = max(v for _, v, _, _ in items) or 1
    lis = []
    for i, (lab, v, disp, tipt) in enumerate(items):
        cls = []
        if crit and i in crit: cls.append("crit")
        if hl and i in hl: cls.append("hl")
        if muted and i in muted: cls.append("muted-row")
        c = f' class="{" ".join(cls)}"' if cls else ""
        w = max(0.6, v / mx * 100)
        lis.append(f'<li{c}><span class="bl">{esc(lab)}</span><span class="bt" data-tip="{esc(tipt)}"><span class="bb" style="--v:{w:.2f}%"></span></span><span class="bv">{disp}</span></li>')
    head = ""
    if title: head += f'<p class="ctitle">{title}</p>'
    if sub: head += f'<p class="csub">{sub}</p>'
    foot = f'<p class="cnote">{note}</p>' if note else ""
    tbl = ""
    if table_head:
        rows = "".join(f"<tr><td>{esc(l)}</td><td class=\"r\">{d}</td></tr>" for l, _, d, _ in items)
        tbl = (f'<details class="table"><summary>{table_head[0]}</summary><table><thead><tr><th>{table_head[1]}</th>'
               f'<th class="r">{table_head[2]}</th></tr></thead><tbody>{rows}</tbody></table></details>')
    return f'<div class="chart reveal">{head}<ol class="bars" style="--lw:{label_w}px">{"".join(lis)}</ol>{foot}{tbl}</div>'


def cols(items, label_idx=None, muted_idx=None, title=None, sub=None, note=None, height=180, table_head=None):
    """items: list of (xlabel, value, display, tip)."""
    mx = max(v for _, v, _, _ in items) or 1
    label_idx = set(label_idx or [])
    muted_idx = set(muted_idx or [])
    cs, xs = [], []
    for i, (x, v, disp, tipt) in enumerate(items):
        h = max(1.5, v / mx * 100)
        cl = " muted-col" if i in muted_idx else ""
        lab = f'<span class="cv">{disp}</span>' if i in label_idx else ""
        cs.append(f'<div class="col{cl}" style="--h:{h:.2f}%" data-tip="{esc(tipt)}">{lab}<span class="cb"></span></div>')
        xs.append(f"<span>{esc(str(x))}</span>")
    head = ""
    if title: head += f'<p class="ctitle">{title}</p>'
    if sub: head += f'<p class="csub">{sub}</p>'
    foot = f'<p class="cnote">{note}</p>' if note else ""
    tbl = ""
    if table_head:
        rows = "".join(f"<tr><td>{esc(str(x))}</td><td class=\"r\">{d}</td></tr>" for x, _, d, _ in items)
        tbl = (f'<details class="table"><summary>{table_head[0]}</summary><table><thead><tr><th>{table_head[1]}</th>'
               f'<th class="r">{table_head[2]}</th></tr></thead><tbody>{rows}</tbody></table></details>')
    return (f'<div class="chart reveal">{head}<div class="cols" style="height:{height}px" aria-hidden="true">{"".join(cs)}</div>'
            f'<div class="cols-x" aria-hidden="true">{"".join(xs)}</div>{foot}{tbl}</div>')


def line_chart(points, lang, title_id, title, desc, end_label, y_fmt, x_labels):
    """points: list of (xlabel, value, tiphtml). Single series, 2px line + 10% wash."""
    W, H = 420, 210
    L, R, T, B = 40, 52, 14, 26
    vals = [v for _, v, _ in points]
    vmax = max(vals)
    step = 100000 if vmax > 250000 else 50000
    top = (int(vmax / step) + 1) * step
    n = len(points)
    def X(i): return L + i * (W - L - R) / (n - 1)
    def Y(v): return T + (1 - v / top) * (H - T - B)
    pts = [(round(X(i), 2), round(Y(v), 2), tip) for i, (_, v, tip) in enumerate(points)]
    d = "M" + " L".join(f"{x},{y}" for x, y, _ in pts)
    area = d + f" L{pts[-1][0]},{H - B} L{pts[0][0]},{H - B} Z"
    grid = []
    for g in range(0, top + 1, step):
        y = round(Y(g), 2)
        grid.append(f'<line x1="{L}" x2="{W - R}" y1="{y}" y2="{y}"/>')
        grid.append(f'<text x="{L - 6}" y="{y + 3.5}" text-anchor="end">{y_fmt(g)}</text>')
    xl = []
    for i, lab in x_labels:
        xl.append(f'<text x="{round(X(i), 2)}" y="{H - 8}" text-anchor="middle">{esc(lab)}</text>')
    ex, ey, _ = pts[-1]
    data_points = esc(json.dumps([[x, y, t] for x, y, t in pts]))
    return (f'<svg class="linechart" viewBox="0 0 {W} {H}" role="img" aria-labelledby="{title_id}-t {title_id}-d" data-points="{data_points}">'
            f'<title id="{title_id}-t">{esc(title)}</title><desc id="{title_id}-d">{esc(desc)}</desc>'
            f'<g class="grid">{"".join(g for g in grid if g.startswith("<line"))}</g>'
            f'<g class="axis">{"".join(g for g in grid if g.startswith("<text"))}{"".join(xl)}</g>'
            f'<path class="area" d="{area}"/><path class="ln" d="{d}"/>'
            f'<line class="xh" x1="0" x2="0" y1="{T}" y2="{H - B}"/>'
            f'<circle class="end" cx="{ex}" cy="{ey}" r="4.5"/>'
            f'<text class="endlabel" x="{ex + 8}" y="{ey + 4}">{esc(end_label)}</text>'
            f'<circle class="hov" cx="{ex}" cy="{ey}" r="5"/></svg>')


def stacked(rows, segs, legend_items):
    """rows: list of (label, [values...]) values in %, segs: list of (cls, name)."""
    out = []
    for lab, vals in rows:
        spans = []
        for (cls, name), v in zip(segs, vals):
            spans.append(f'<span class="{cls}" style="flex:{v:.2f}" data-tip="{esc(name)}: {esc(str(v))}"></span>')
        out.append(f'<div class="stack-row"><span>{esc(lab)}</span><div class="stack">{"".join(spans)}</div></div>')
    leg = "".join(f'<li><i class="{c}"></i>{t}</li>' for c, t in legend_items)
    return f'<div class="chart">{"".join(out)}<ul class="legend">{leg}</ul></div>'


# ---------------------------------------------------------------- data shortcuts
BY = FT["by_year"]
TOTAL_LOANS = sum(r["loans"] for r in BY)
TOTAL_AMT = sum(r["total_amount"] for r in BY)
OUT = FT["outstanding_by_status"]
OUT_TOTAL = sum(r["amount"] for r in OUT)
NOT_CURRENT = sum(r["amount"] for r in OUT if r["loan_status"] != "Current")
K = TL["kpis"]
MONTHLY = TL["monthly"]
RFM = {r["segment"]: r for r in TL["rfm"]}
RFM_CUST = sum(r["customers"] for r in TL["rfm"])
RFM_REV = sum(r["revenue"] for r in TL["rfm"])
FREQ1 = TL["rfm_check"]["one_order_customers"]
MISCL = TL["rfm_check"]["one_order_in_top_freq_quartiles"]
STATUS_TOTAL = sum(r["orders"] for r in TL["order_status"])
CANC_RET = sum(r["orders"] for r in TL["order_status"] if r["status"] in ("Cancelled", "Returned"))
PREV12 = sum(r["revenue"] for r in MONTHLY[:12])
LAST12 = sum(r["revenue"] for r in MONTHLY[12:])
assert LAST12 == K["revenue_12m"], "monthly and kpi revenue disagree"
assert OUT_TOTAL == 3080553000, OUT_TOTAL

# ---------------------------------------------------------------- SQL snippets (verbatim from the labs)
SQL_HERO = """SELECT issue_year,
       COUNT(loan_id) AS loans
FROM fintech.loan
GROUP BY issue_year
ORDER BY issue_year;"""

SQL_LOAD = """LOAD DATA OVERWRITE fintech.state_region
(
  state string,
  subregion string,
  region string
)
FROM FILES (
  format = 'CSV',
  uris = ['gs://sureskills-lab-dev/future-workforce/da-capstone/temp_35_us/state_region_mapping/state_region_*.csv']);"""

SQL_JOIN = """-- Query B: join on the key both tables share
CREATE OR REPLACE TABLE fintech.loan_with_region AS
SELECT
  lo.loan_id,
  lo.loan_amount,
  sr.region
FROM fintech.loan lo
INNER JOIN fintech.state_region sr
  ON lo.state = sr.state;"""

SQL_DEDUP = """-- purpose lives inside the nested RECORD `application`
CREATE OR REPLACE TABLE fintech.loan_purposes AS
SELECT DISTINCT application.purpose AS purpose
FROM fintech.loan;"""

SQL_YEAR = """CREATE OR REPLACE TABLE fintech.loan_count_by_year AS
SELECT issue_year, COUNT(loan_id) AS loan_count
FROM fintech.loan
GROUP BY issue_year;

-- Cash out per year (Treasury's cash-flow question)
SELECT issue_year, SUM(loan_amount) AS total_amount
FROM fintech.loan
GROUP BY issue_year
ORDER BY issue_year;"""

SQL_LOOKER = """-- SQL that Looker generates for the LookML measure
-- "Outstanding Loans Amount" (single value tile)
SELECT COALESCE(SUM(CASE WHEN (loan.loan_status <> 'Fully Paid'
                               OR loan.loan_status IS NULL)
                         THEN loan.loan_amount ELSE NULL END), 0)
       AS loan_outstanding_loans_amount
FROM `cloud-training-demos.fintech.loan` AS loan
LIMIT 500;"""

SQL_RFM = """WITH rfm_calc AS (
  SELECT
    o.user_id AS customer_id,
    DATE_DIFF(CURRENT_TIMESTAMP(), MAX(o.created_at), DAY) AS recency,
    COUNT(DISTINCT o.order_id) AS frequency,   -- fix 1: orders, not items
    ROUND(SUM(oi.sale_price)) AS monetary
  FROM `thelook_ecommerce.orders` o
  INNER JOIN `thelook_ecommerce.order_items` oi
    ON o.order_id = oi.order_id
  GROUP BY customer_id
),
rfm_quant AS (
  SELECT
    customer_id,
    NTILE(4) OVER (ORDER BY recency DESC) AS recency_quantile,  -- fix 2: 4 = most recent
    NTILE(4) OVER (ORDER BY frequency) AS frequency_quantile,
    NTILE(4) OVER (ORDER BY monetary) AS monetary_quantile
  FROM rfm_calc
)
SELECT
  customer_id,
  CASE
    WHEN monetary_quantile >= 3 AND frequency_quantile >= 3 THEN "High Value Customer"
    WHEN frequency_quantile >= 3 THEN "Loyal Customer"
    WHEN recency_quantile <= 1 THEN "At Risk Customer"
    WHEN recency_quantile >= 3 THEN "Persuadable Customer"
    ELSE "Other"                                                -- fix 3: no NULL segment
  END AS customer_segment
FROM rfm_quant;"""

LKML_DASH = """# order_items.view
measure: total_revenue {
  type: sum
  sql: ${sale_price} ;;
}

# fixed: reference fields with ${} and avoid dividing by zero
measure: revenue_per_user {
  type: number
  sql: ${total_revenue} / NULLIF(${users.total_users}, 0) ;;
}

# model file
explore: order_items {
  join: users {
    relationship: many_to_one
    sql_on: ${users.id} = ${order_items.user_id} ;;
  }
}"""

SQL_PIPE = """CREATE OR REPLACE PROCEDURE `thelook_ecommerce.sp_create_load_tables`()
BEGIN
  -- centers: public table + geography transformation
  CREATE OR REPLACE TABLE `thelook_ecommerce.centers` AS
  SELECT id, name, latitude, longitude,
         ST_GEOGPOINT(dcenters.longitude, dcenters.latitude) AS point_location
  FROM `bigquery-public-data.thelook_ecommerce.distribution_centers` AS dcenters;

  -- customers, product_orders_fulfillment: same pattern ...
END;

CALL `thelook_ecommerce.sp_create_load_tables`();

-- distance (km) from each customer to the closest distribution center
SELECT
  customers.id AS customer_id,
  (SELECT MIN(ST_DISTANCE(centers.point_location, customers.point_location)) / 1000
   FROM `thelook_ecommerce.centers` AS centers) AS distance_to_closest_center
FROM `thelook_ecommerce.customers` AS customers;"""

SQL_PART = """-- No partition filter: scans the whole table (~489 MB)
SELECT * FROM `thelook_gcda.taxi_trips`
ORDER BY pickup_datetime DESC
LIMIT 100;

-- Filter on the partitioning column: only Nov-Dec 2022 partitions (~10 MB)
SELECT * FROM `thelook_gcda.taxi_trips`
WHERE pickup_datetime > '2022-11-01'
ORDER BY pickup_datetime ASC;"""


# ---------------------------------------------------------------- copy (ES / EN)
def C(lang):
    es = lang == "es"
    L = lambda a, b: a if es else b  # noqa: E731
    return {
        "lang": lang,
        "other": "en" if es else "es",
        "site_name": "Daniel Galea Romero",
        "title_home": L("Daniel Galea Romero · Data Analyst junior (Google Cloud)", "Daniel Galea Romero · Junior Data Analyst (Google Cloud)"),
        "desc_home": L("Portfolio de Daniel Galea Romero: estudiante de Ingeniería Informática y Matemáticas (UGR) con el Google Cloud Data Analytics Certificate. SQL, BigQuery, Looker y LookML con datos reales.",
                       "Portfolio of Daniel Galea Romero: Computer Engineering & Mathematics student (University of Granada) with the Google Cloud Data Analytics Certificate. SQL, BigQuery, Looker and LookML on real data."),
        "skip": L("Saltar al contenido", "Skip to content"),
        "nav": [("#sobre-mi", L("Sobre mí", "About")), ("#proyectos", L("Proyectos", "Projects")), ("#stack", "Stack"), ("#certificado", L("Certificado", "Certificate")), ("#contacto", L("Contacto", "Contact"))],
        "theme": L("Cambiar entre tema claro y oscuro", "Switch between light and dark theme"),
        "lang_label": L("Read in English", "Leer en español"),
        "lang_short": "EN" if es else "ES",
        "eyebrow": L("Data Analyst junior · Granada", "Junior Data Analyst · Granada, Spain"),
        "h1": 'Daniel Galea <em>Romero</em>',
        "lead": L(
            "Estudio el <strong>Doble Grado en Ingeniería Informática y Matemáticas</strong> en la Universidad de Granada "
            "(<strong>9,1 de media, 7 matrículas de honor</strong>) y acabo de completar el <strong>Google Cloud Data Analytics Certificate</strong>. "
            "Convierto preguntas de negocio en SQL, modelos y dashboards que alguien pueda usar el lunes por la mañana.",
            "I study a <strong>double degree in Computer Engineering and Mathematics</strong> at the University of Granada "
            "(<strong>9.1/10 GPA, 7 distinctions</strong>) and just completed the <strong>Google Cloud Data Analytics Certificate</strong>. "
            "I turn business questions into SQL, models and dashboards that someone can actually use on Monday morning."),
        "avail": L("Disponible para media jornada · remoto o híbrido desde Granada", "Available part-time · remote or hybrid from Granada, Spain"),
        "cta_cv": L("Descargar CV", "Download CV"),
        "cta_mail": L("Escríbeme", "Email me"),
        "qcard_file": "fintech.loan",
        "qcard_run": L("Ejecutada", "Ran"),
        "qcard_cap": L(f"Consulta real del proyecto final: {num(TOTAL_LOANS, 'es')} préstamos de TheLook Fintech, de 2012 a 2019.",
                       f"Real query from my capstone: {num(TOTAL_LOANS, 'en')} TheLook Fintech loans, 2012–2019."),
        # about
        "about_k": L("<b>01</b> · Sobre mí", "<b>01</b> · About"),
        "about_h": L("Matemáticas, código y <em>datos de negocio</em>", "Maths, code and <em>business data</em>"),
        "about_p": [
            L("En la carrera aprendo a demostrar las cosas y a escribir código que funcione. Con el certificado de Google Cloud he aprendido a aplicarlo a datos de negocio: de la ingesta en BigQuery al dashboard en Looker, pasando por la limpieza, el modelado y el resumen para quien decide.",
              "My degree teaches me to prove things and to write code that works. The Google Cloud certificate taught me to apply that to business data: from ingestion in BigQuery to a Looker dashboard, through cleaning, modelling and a summary for whoever has to decide."),
            L("Busco mi primera experiencia como analista de datos <strong>a media jornada, compatible con el grado</strong>: un equipo en el que aprender de analistas senior, aportar SQL limpio y explicar los números con claridad.",
              "I'm looking for my first data analyst role, <strong>part-time and compatible with my degree</strong>: a team where I can learn from senior analysts, contribute clean SQL and explain the numbers clearly."),
            L("Fuera de la pantalla he sido socorrista jefe dos veranos en el Ayuntamiento de Fuentes de León, ayudo con las matemáticas a amigos que lo necesitan y organizo actividades con AJM La Sotarraña, una asociación cultural de mi pueblo, donde suelo acabar montando los formularios y las hojas de inscripción.",
              "Away from the screen I've been head lifeguard for two summers at Fuentes de León Town Council, I help friends with maths and I organise events with AJM La Sotarraña, a cultural association in my home town, where I usually end up building the sign-up forms and spreadsheets."),
        ],
        "facts": [
            (L("Formación", "Education"), L("Doble Grado en Ing. Informática y Matemáticas · UGR · 2025–2030", "BSc Computer Engineering & Mathematics (double degree) · University of Granada · 2025–2030")),
            (L("Expediente", "Grades"), L("9,1 de media · 7 matrículas de honor", "9.1/10 GPA · 7 distinctions (Matrícula de Honor)")),
            (L("Certificado", "Certificate"), L("Google Cloud Data Analytics · oct. 2026", "Google Cloud Data Analytics · Oct 2026")),
            (L("Idiomas", "Languages"), L("Español nativo · inglés B2 (Trinity ISE II)", "Spanish (native) · English B2 (Trinity ISE II)")),
            (L("Jornada", "Availability"), L("Media jornada, tardes y fines de semana · incorporación inmediata", "Part-time, afternoons and weekends · available now")),
            (L("Ubicación", "Location"), L("Granada · remoto o híbrido", "Granada, Spain · remote or hybrid")),
        ],
        # journey
        "journey_k": L("<b>02</b> · Cómo trabajo", "<b>02</b> · How I work"),
        "journey_h": L("El <em>data journey</em>, de punta a punta", "The <em>data journey</em>, end to end"),
        "journey_intro": L("Los cinco pasos que sigue el certificado y las herramientas con las que los he practicado. Pulsa una etapa para ver qué proyectos la tocan.",
                           "The five steps the certificate follows and the tools I practised them with. Click a stage to see which projects touch it."),
        "stages": [
            ("collect", L("Recoger", "Collect"), L("Localizar y traer los datos: ficheros en Cloud Storage, datasets públicos, formularios.", "Find and bring in the data: files in Cloud Storage, public datasets, forms."), "Cloud Storage · LOAD DATA · public datasets"),
            ("process", L("Procesar", "Process"), L("Limpiar, deduplicar, unir y derivar columnas con SQL.", "Clean, deduplicate, join and derive columns with SQL."), "JOIN · DISTINCT · CTE · NTILE · ST_DISTANCE"),
            ("store", L("Almacenar", "Store"), L("Guardar tablas reutilizables y baratas de consultar.", "Save reusable tables that are cheap to query."), "CTAS · partitions · procedures · lakehouse"),
            ("analyze", L("Analizar", "Analyze"), L("Modelar métricas una vez y explorarlas sin reescribir SQL.", "Model metrics once and explore them without rewriting SQL."), "LookML · Explores · Data Studio"),
            ("activate", L("Activar", "Activate"), L("Que alguien decida con ello: dashboards, hojas conectadas, resúmenes.", "Help someone decide: dashboards, connected sheets, summaries."), "Dashboards · Connected Sheets · exec summary"),
        ],
        "journey_reset": L("Ver todos los proyectos", "Show all projects"),
        # featured
        "proj_k": L("<b>03</b> · Proyectos", "<b>03</b> · Projects"),
        "proj_h": L("Proyecto estrella y <em>prácticas</em> del certificado", "Flagship project and certificate <em>labs</em>"),
        "proj_intro": L("El capstone es el proyecto final, que mezclaba pasos guiados con retos sin instrucciones paso a paso. Los demás son proyectos prácticos guiados del certificado; donde he podido, los he vuelto a ejecutar con los datos públicos actuales.",
                        "The capstone is the final project, mixing guided steps with challenges that had no step-by-step instructions. The rest are guided hands-on labs from the certificate; where possible I re-ran them on today's public data."),
        "feat_tag": L("Proyecto estrella · capstone", "Flagship · capstone"),
        "feat_h": L("TheLook Fintech: la salud de la cartera de préstamos, para Tesorería", "TheLook Fintech: loan-portfolio health for the Treasury team"),
        "feat_p": L(f"De {num(TOTAL_LOANS, 'es')} préstamos en BigQuery a un dashboard de autoservicio en Looker que avisa cuando el saldo pendiente supera el límite de riesgo, y un resumen ejecutivo para dirección.",
                    f"From {num(TOTAL_LOANS, 'en')} loans in BigQuery to a self-service Looker dashboard that flags when the outstanding balance breaks the risk limit, plus an executive summary for leadership."),
        "feat_kpis": [
            (num(TOTAL_LOANS, lang), L("préstamos analizados (2012–2019)", "loans analysed (2012–2019)"), ""),
            (L("3.080,6 M$", "$3.08B"), L("pendientes: +2,7 % sobre el límite de 3.000 M$", "outstanding: 2.7% over the $3B limit"), "alert"),
            (pct(NOT_CURRENT / OUT_TOTAL * 100, lang), L("del saldo pendiente no está al corriente", "of the outstanding balance is not current"), ""),
        ],
        "feat_cta": L("Leer el caso completo", "Read the case study"),
        "feat_chart_t": L("Importe prestado por año", "Amount lent per year"),
        "feat_chart_s": L("Millones de dólares · ×24 entre 2012 y 2019", "Millions of dollars · 24× between 2012 and 2019"),
        "tools_feat": ["BigQuery", "SQL", "Cloud Storage", "Connected Sheets", "Looker Enterprise", "LookML"],
        # project labels
        "lbl_goal": L("Objetivo", "Goal"),
        "lbl_did": L("Qué hice", "What I did"),
        "lbl_result": L("Resultado", "Result"),
        "lbl_learn": L("Lo que me llevo", "Takeaway"),
        "lbl_sql": L("Ver el SQL clave", "Show the key SQL"),
        "lbl_lkml": L("Ver el LookML clave", "Show the key LookML"),
        "lbl_stages": L("Etapas", "Stages"),
        # stack
        "stack_k": L("<b>04</b> · Stack", "<b>04</b> · Stack"),
        "stack_h": L("Herramientas que <em>he usado</em>", "Tools I <em>have used</em>"),
        "stack_groups": [
            ("db", L("Consultas y almacén", "Query & warehouse"), [("SQL (GoogleSQL)", ""), ("BigQuery", ""), (L("CTE y funciones de ventana", "CTEs & window functions"), ""), ("CTAS · LOAD DATA", ""), ("Stored procedures", ""), (L("Funciones geográficas", "Geography functions"), ""), (L("Particionado y clustering", "Partitioning & clustering"), ""), ("STRUCT / ARRAY", "")]),
            ("chart", L("BI y visualización", "BI & visualisation"), [("Looker Enterprise", ""), ("LookML", ""), ("Data Studio", L("antes Looker Studio", "formerly Looker Studio")), ("Connected Sheets", ""), (L("Dashboards de autoservicio", "Self-service dashboards"), ""), ("Wireframes", ""), ("Data storytelling", "")]),
            ("cloud", L("Plataforma de datos", "Data platform"), [("Cloud Storage", ""), ("Data lakehouse", ""), ("Knowledge Catalog", L("antes Dataplex", "formerly Dataplex")), ("BigQuery sharing", L("antes Analytics Hub", "formerly Analytics Hub")), ("Managed Service for Apache Spark", L("antes Dataproc", "formerly Dataproc")), ("Agent Platform · BigQuery ML", L("antes Vertex AI", "formerly Vertex AI"))]),
            ("people", L("Método y código", "Method & code"), [("ETL / ELT", ""), (L("Calidad de datos", "Data quality"), ""), (L("Gobierno del dato y PII", "Data governance & PII"), ""), (L("Resumen ejecutivo", "Executive summaries"), ""), ("Google Sheets · Forms", ""), ("Git · GitHub", ""), ("C++", ""), ("Python · pandas · NumPy", L("nivel básico", "basic level"))]),
        ],
        "stack_old_group": 2,
        "stack_note": L("En gris, lo que conozco a nivel de fundamentos: lo he estudiado y practicado en labs, pero aún no en un proyecto propio.",
                        "Greyed out: things I know at a fundamentals level — studied and tried in labs, not yet used in a project of my own."),
        # cert
        "cert_k": L("<b>05</b> · Certificado", "<b>05</b> · Certificate"),
        "cert_h": L("Google Cloud <em>Data Analytics</em> Certificate", "Google Cloud <em>Data Analytics</em> Certificate"),
        "cert_p": L("Emitido por Google Cloud en Google Skills y verificable en Credly. Cinco cursos con labs en BigQuery, Looker y Google Cloud, y un proyecto final de todo el ciclo de vida del dato.",
                    "Issued by Google Cloud on Google Skills and verifiable on Credly. Five courses with hands-on labs in BigQuery, Looker and Google Cloud, plus a capstone covering the full data lifecycle."),
        "courses": ["Introduction to Data Analytics in Google Cloud", "Data Management and Storage in the Cloud", "Data Transformation in the Cloud",
                    "The Power of Storytelling: How to Visualize Data in the Cloud", "Put It All Together: Prepare for a Cloud Data Analyst Job"],
        "cert_btn": L("Ver la credencial en Credly", "View the credential on Credly"),
        "seal_mid": L("cursos completados", "courses completed"),
        "seal_date": L("OCT · 2026", "OCT · 2026"),
        # contact
        "contact_k": L("<b>06</b> · Contacto", "<b>06</b> · Contact"),
        "contact_h": L("¿<em>Hablamos</em>?", "Let's <em>talk</em>"),
        "contact_p": L("Busco un puesto de analista de datos junior a media jornada, en remoto o híbrido desde Granada, con incorporación inmediata.",
                       "I'm looking for a part-time junior data analyst role, remote or hybrid from Granada, and I can start right away."),
        "links": [
            ("Email", EMAIL, f"mailto:{EMAIL}"),
            ("LinkedIn", "linkedin.com/in/daniel-galea-romero", LINKEDIN),
            ("GitHub", "github.com/Danielgalea7", GITHUB),
            ("Credly", L("Insignia del certificado", "Certificate badge"), CREDLY),
            (L("CV (PDF)", "Résumé (PDF)"), L("Español · English", "English · Español"), CV[lang]),
        ],
        "footer": L(
            "Datos: <code>bigquery-public-data.thelook_ecommerce</code> (sintético, foto del 12/10/2026) y <code>cloud-training-demos.fintech</code> (capstone). Consultas ejecutadas en el BigQuery sandbox. Sitio estático en HTML, CSS y JavaScript, sin frameworks ni cookies.",
            "Data: <code>bigquery-public-data.thelook_ecommerce</code> (synthetic, snapshot of 12 Oct 2026) and <code>cloud-training-demos.fintech</code> (capstone). Queries run in the BigQuery sandbox. Static site in HTML, CSS and JavaScript — no frameworks, no cookies."),
    }


# ---------------------------------------------------------------- projects (cards)
def projects(lang):
    es = lang == "es"
    L = lambda a, b: a if es else b  # noqa: E731
    c = C(lang)
    out = []

    # RFM
    seg_order = [("High Value", "s1"), ("Loyal", "s2"), ("Persuadable", "s3"), ("At Risk", "s4"), ("Other", "sm")]
    rows = [(L("Clientes", "Customers"), [RFM[s]["customers"] / RFM_CUST * 100 for s, _ in seg_order]),
            (L("Ingresos", "Revenue"), [RFM[s]["revenue"] / RFM_REV * 100 for s, _ in seg_order])]
    legend = [(cls, f'{esc(s)} <span class="num">{pct(RFM[s]["customers"] / RFM_CUST * 100, lang, 0)} · {pct(RFM[s]["revenue"] / RFM_REV * 100, lang, 0)}</span>') for s, cls in seg_order]
    # nicer tooltips with rounded numbers
    rows_fmt = []
    for lab, vals in rows:
        rows_fmt.append((lab, [round(v, 1) for v in vals]))
    rfm_chart = stacked(rows_fmt, [(cls, s) for s, cls in seg_order], legend)
    rfm = {
        "id": "rfm", "stages": "process store", "src": L("Curso 3 · lab", "Course 3 · lab"),
        "title": L("Segmentación RFM de clientes", "RFM customer segmentation"),
        "desc": L("Marketing de TheLook eCommerce quería campañas por tipo de cliente porque la retención había caído.",
                  "TheLook eCommerce's marketing lead wanted campaigns per customer type because retention had dropped."),
        "did": L("Calculé recencia, frecuencia y valor monetario con CTEs, los repartí en cuartiles con <code>NTILE</code> y asigné segmentos con <code>CASE</code>. Corregí tres fallos del enunciado: la frecuencia contaba artículos y no pedidos, la recencia estaba invertida y faltaba un <code>ELSE</code>.",
                 "I computed recency, frequency and monetary value with CTEs, split them into quartiles with <code>NTILE</code> and assigned segments with <code>CASE</code>. I fixed three bugs in the brief: frequency counted items instead of orders, recency was inverted and the <code>CASE</code> had no <code>ELSE</code>."),
        "result": L(f"Con los datos públicos de los últimos 12 meses ({num(K['customers_12m'], 'es')} clientes): el segmento <strong>High Value</strong> es el {pct(RFM['High Value']['customers'] / RFM_CUST * 100, 'es', 0)} de los clientes y genera el <strong>{pct(RFM['High Value']['revenue'] / RFM_REV * 100, 'es', 0)} de los ingresos</strong>; el {pct(FREQ1 / RFM_CUST * 100, 'es', 0)} solo compró una vez.",
                    f"On the last 12 months of public data ({num(K['customers_12m'], 'en')} customers): the <strong>High Value</strong> segment is {pct(RFM['High Value']['customers'] / RFM_CUST * 100, 'en', 0)} of customers and drives <strong>{pct(RFM['High Value']['revenue'] / RFM_REV * 100, 'en', 0)} of revenue</strong>; {pct(FREQ1 / RFM_CUST * 100, 'en', 0)} bought only once."),
        "learn": L(f"<code>NTILE</code> reparte los empates al azar: {num(MISCL, 'es')} clientes con un solo pedido acababan en los cuartiles «altos» de frecuencia. Para variables con muchos empates uso umbrales (1, 2, 3+ pedidos).",
                   f"<code>NTILE</code> splits ties arbitrarily: {num(MISCL, 'en')} one-order customers ended up in the 'high' frequency quartiles. For heavily tied variables I use thresholds (1, 2, 3+ orders)."),
        "chart": f'<p class="ctitle">{L("Peso de cada segmento", "Share of each segment")}</p><p class="csub">{L("% de clientes frente a % de ingresos · 12 meses a sep-2026", "% of customers vs % of revenue · 12 months to Sep 2026")}</p>' + rfm_chart,
        "code": (c["lbl_sql"], SQL_RFM, "sql"),
        "tools": ["BigQuery", "SQL", "CTE", "NTILE", "CASE"],
    }

    # eCommerce dashboard
    pts = []
    for i, m in enumerate(MONTHLY):
        y, mo = m["month"].split("-")
        mname = (["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"] if es else
                 ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])[int(mo) - 1]
        tip = f"<b>{mname} {y}</b><br>{kusd(m['revenue'], lang)} · {num(m['orders'], lang)} {L('pedidos', 'orders')}"
        pts.append((f"{mname} {y}", m["revenue"], tip))
    xl = [(0, L("oct 24", "Oct 24")), (6, L("abr 25", "Apr 25")), (12, L("oct 25", "Oct 25")), (18, L("abr 26", "Apr 26")), (23, L("sep 26", "Sep 26"))]
    lc = line_chart(pts, lang, f"rev-{lang}", L("Ingresos mensuales de TheLook eCommerce", "TheLook eCommerce monthly revenue"),
                    L("Línea de 24 meses, de octubre de 2024 a septiembre de 2026, que crece de 113 mil a 380 mil dólares al mes.",
                      "24-month line from October 2024 to September 2026, growing from $113K to $380K per month."),
                    kusd(MONTHLY[-1]["revenue"], lang, 0), lambda g: ("0" if g == 0 else (f"{g // 1000}K")), xl)
    mrows = "".join(f"<tr><td>{m['month']}</td><td class=\"r\">{num(m['revenue'], lang)}</td><td class=\"r\">{num(m['orders'], lang)}</td></tr>" for m in MONTHLY)
    dash = {
        "id": "dash", "stages": "analyze activate", "src": L("Curso 4 · labs", "Course 4 · labs"),
        "title": L("Dashboard de ventas de TheLook eCommerce", "TheLook eCommerce sales dashboard"),
        "desc": L("La VP de Finanzas quería ver ingresos, tendencias y KPIs en un solo sitio, con filtro por país.",
                  "The VP of Finance wanted revenue, trends and KPIs in one place, filterable by country."),
        "did": L("Construí el dashboard <em>Business Insights</em> en Looker Enterprise (valor único, líneas con pivote por categoría, barras, columnas y filtro por país) y modelé en LookML las métricas <code>total_revenue</code> y <code>revenue_per_user</code>, con un <em>Explore</em> que une pedidos y usuarios.",
                 "I built the <em>Business Insights</em> dashboard in Looker Enterprise (single value, category-pivoted lines, bars, columns and a country filter) and modelled the <code>total_revenue</code> and <code>revenue_per_user</code> measures in LookML, with an <em>Explore</em> joining orders and users."),
        "result": L(f"Rehecho con los datos actuales: <strong>{musd(K['revenue_12m'], 'es', 2)}</strong> en 12 meses (<strong>+{pct((LAST12 / PREV12 - 1) * 100, 'es', 0)}</strong> frente al año anterior), ticket medio de {num(K['aov_12m'], 'es', 2)} $ y margen bruto del {pct(K['margin_pct_12m'], 'es')}. Uno de cada cuatro pedidos se cancela o se devuelve.",
                    f"Rebuilt on current data: <strong>{musd(K['revenue_12m'], 'en', 2)}</strong> over 12 months (<strong>+{pct((LAST12 / PREV12 - 1) * 100, 'en', 0)}</strong> year on year), ${num(K['aov_12m'], 'en', 2)} average order and {pct(K['margin_pct_12m'], 'en')} gross margin. One in four orders is cancelled or returned."),
        "learn": L("Una métrica bien definida en LookML evita diez versiones distintas del mismo número. Y en LookML los campos se referencian con <code>${}</code>: el lab lo hacía mal.",
                   "A metric defined once in LookML prevents ten versions of the same number. And LookML fields must be referenced with <code>${}</code> — the lab got it wrong."),
        "chart": (f'<p class="ctitle">{L("Ingresos mensuales", "Monthly revenue")}</p><p class="csub">{L("Ventas válidas (sin canceladas ni devueltas) · oct-2024 a sep-2026", "Valid sales (excl. cancelled and returned) · Oct 2024 – Sep 2026")}</p>'
                  f'<div class="chart">{lc}<details class="table"><summary>{L("Ver los datos", "Show the data")}</summary><table><thead><tr><th>{L("Mes", "Month")}</th><th class="r">{L("Ingresos ($)", "Revenue ($)")}</th><th class="r">{L("Pedidos", "Orders")}</th></tr></thead><tbody>{mrows}</tbody></table></details></div>'),
        "code": (c["lbl_lkml"], LKML_DASH, "lookml"),
        "tools": ["Looker Enterprise", "LookML", "Data Studio", "BigQuery"],
    }

    # Pipeline
    pipe_svg = (
        '<svg class="arch-mini" viewBox="0 0 460 170" role="img" aria-labelledby="pipe-t-' + lang + '">'
        f'<title id="pipe-t-{lang}">{esc(L("Flujo del pipeline: tablas públicas, transformación geográfica, tres tablas de destino y un procedimiento almacenado que lo reejecuta todo.", "Pipeline flow: public tables, geography transformation, three target tables and a stored procedure that re-runs everything."))}</title>'
        '<defs><marker id="ah-' + lang + '" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0l8 4-8 4z" fill="var(--accent)"/></marker></defs>'
        '<rect x="2" y="50" width="96" height="58" rx="10" fill="var(--surface-2)" stroke="var(--line-strong)"/>'
        f'<text x="50" y="75" text-anchor="middle" font-size="12" font-weight="650" fill="var(--ink)" font-family="var(--sans)">{L("Dataset", "Public")}</text>'
        f'<text x="50" y="91" text-anchor="middle" font-size="12" font-weight="650" fill="var(--ink)" font-family="var(--sans)">{L("público", "dataset")}</text>'
        '<path d="M98 79h34" stroke="var(--accent)" stroke-width="1.6" fill="none" marker-end="url(#ah-' + lang + ')"/>'
        '<rect x="138" y="46" width="124" height="66" rx="10" fill="var(--surface-2)" stroke="var(--accent)"/>'
        '<text x="200" y="70" text-anchor="middle" font-size="11" font-family="var(--mono)" fill="var(--ink)">ST_GEOGPOINT</text>'
        '<text x="200" y="86" text-anchor="middle" font-size="11" font-family="var(--mono)" fill="var(--ink)">ST_DISTANCE</text>'
        '<text x="200" y="102" text-anchor="middle" font-size="10.5" font-family="var(--mono)" fill="var(--muted)">JOIN products</text>'
        '<path d="M262 79c24 0 24-54 46-54M262 79h46M262 79c24 0 24 54 46 54" stroke="var(--accent)" stroke-width="1.6" fill="none"/>'
        '<rect x="310" y="8" width="146" height="34" rx="8" fill="var(--surface-2)" stroke="var(--line-strong)"/><text x="383" y="29" text-anchor="middle" font-size="11" font-family="var(--mono)" fill="var(--ink)">customers</text>'
        '<rect x="310" y="62" width="146" height="34" rx="8" fill="var(--surface-2)" stroke="var(--line-strong)"/><text x="383" y="83" text-anchor="middle" font-size="11" font-family="var(--mono)" fill="var(--ink)">centers</text>'
        '<rect x="310" y="116" width="146" height="34" rx="8" fill="var(--surface-2)" stroke="var(--line-strong)"/><text x="383" y="137" text-anchor="middle" font-size="10.5" font-family="var(--mono)" fill="var(--ink)">orders_fulfillment</text>'
        '<text x="2" y="160" font-size="10.5" font-family="var(--mono)" fill="var(--muted)">CALL sp_create_load_tables()  ↻</text>'
        '</svg>')
    pipe = {
        "id": "pipe", "stages": "collect process store", "src": L("Curso 3 · lab", "Course 3 · lab"),
        "title": L("Pipeline SQL con stored procedure", "SQL pipeline with a stored procedure"),
        "desc": L("Logística necesitaba saber a qué distancia está cada cliente de su centro de distribución más cercano, y poder recalcularlo sin repetir pasos a mano.",
                  "Logistics needed the distance from every customer to their closest distribution centre — and a way to recompute it without manual steps."),
        "did": L("Definí los esquemas, convertí coordenadas en <code>GEOGRAPHY</code> con <code>ST_GEOGPOINT</code>, calculé la distancia mínima con <code>ST_DISTANCE</code> en una subconsulta escalar y empaqueté la carga en un <em>stored procedure</em> que se lanza con un <code>CALL</code>.",
                 "I defined the schemas, turned coordinates into <code>GEOGRAPHY</code> with <code>ST_GEOGPOINT</code>, computed the minimum distance with <code>ST_DISTANCE</code> in a scalar subquery and wrapped the load in a stored procedure triggered by a single <code>CALL</code>."),
        "result": L("Seis sentencias manuales convertidas en un procedimiento reejecutable y programable, y una distancia por cliente lista para decidir dónde abrir o mover centros.",
                    "Six manual statements turned into one re-runnable, schedulable procedure, and a per-customer distance ready to decide where to open or move centres."),
        "learn": L("Detecté que el <code>CREATE OR REPLACE … AS SELECT</code> del enunciado descartaba el esquema definido antes (y con él <code>distribution_center_id</code>); con <code>INSERT INTO … SELECT</code> se respeta.",
                   "I noticed the brief's <code>CREATE OR REPLACE … AS SELECT</code> silently discarded the schema defined just before (losing <code>distribution_center_id</code>); <code>INSERT INTO … SELECT</code> keeps it."),
        "chart": f'<div class="chart">{pipe_svg}</div>',
        "code": (c["lbl_sql"], SQL_PIPE, "sql"),
        "tools": ["BigQuery", "SQL", "GEOGRAPHY", "Stored procedures"],
    }

    # Partitioning
    part_items = [
        (L("Sin filtro de partición", "No partition filter"), 489, "≈489 MB", L("ORDER BY … LIMIT 100 · ≈489 MB", "ORDER BY … LIMIT 100 · ≈489 MB")),
        (L("Filtro > 2022-11-01", "Filter > 2022-11-01"), 10, "≈10 MB", L("Solo particiones de nov-dic 2022 · ≈10 MB", "Only Nov–Dec 2022 partitions · ≈10 MB")),
        (L("Filtro > 1900-01-01", "Filter > 1900-01-01"), 489, "≈489 MB", L("El filtro no descarta ninguna partición · ≈489 MB", "The filter prunes nothing · ≈489 MB")),
    ]
    part_chart = bars(part_items, lang, label_w=150, hl=[1], muted=[0, 2],
                      title=L("Datos escaneados por consulta", "Data scanned per query"),
                      sub=L("Tabla taxi_trips particionada por día · caché desactivada", "taxi_trips table partitioned by day · cache disabled"))
    part = {
        "id": "part", "stages": "store analyze", "src": L("Curso 2 · lab", "Course 2 · lab"),
        "title": L("Particionado: 50 veces menos datos por consulta", "Partitioning: 50× less data per query"),
        "desc": L("Un dashboard de TheLook sobre viajes en taxi cerca de las tiendas iba lento y costaba demasiado.",
                  "A TheLook dashboard on taxi drop-offs near stores was slow and too expensive."),
        "did": L("Comparé la misma consulta con y sin filtro sobre la columna de partición (<code>pickup_datetime</code>), desactivando la caché para medir bien los bytes procesados.",
                 "I compared the same query with and without a filter on the partitioning column (<code>pickup_datetime</code>), with the cache disabled to measure bytes processed properly."),
        "result": L("De <strong>≈489 MB a ≈10 MB</strong> por consulta (−98 %). En BigQuery bajo demanda se paga por bytes leídos, así que es también un 98 % menos de coste por consulta.",
                    "From <strong>≈489 MB to ≈10 MB</strong> per query (−98%). With on-demand BigQuery you pay per byte read, so it's also 98% less cost per query."),
        "learn": L("<code>LIMIT</code> no ahorra nada, y un <code>WHERE</code> que no descarta particiones tampoco. Lo que ahorra es filtrar por la columna de partición.",
                   "<code>LIMIT</code> saves nothing, and neither does a <code>WHERE</code> that prunes no partitions. Filtering on the partition column is what saves."),
        "chart": part_chart,
        "code": (c["lbl_sql"], SQL_PART, "sql"),
        "tools": ["BigQuery", L("Tablas particionadas", "Partitioned tables"), "Query plan"],
    }
    return [rfm, dash, pipe, part]


def project_card(p, c):
    stages_order = ["collect", "process", "store", "analyze", "activate"]
    on = set(p["stages"].split())
    mini = "".join(f'<i class="{"on" if s in on else ""}"></i>' for s in stages_order)
    names = ", ".join(st[1] for st in c["stages"] if st[0] in on)
    tools = "".join(f'<li class="chip">{esc(t)}</li>' for t in p["tools"])
    summary, code, lang = p["code"]
    return f"""
<article class="project rv" id="p-{p['id']}" data-stages="{p['stages']}">
  <header><h3>{p['title']}</h3><span class="src">{p['src']}</span></header>
  <p class="pdesc">{p['desc']}</p>
  {p['chart']}
  <dl>
    <div><dt>{c['lbl_did']}</dt><dd>{p['did']}</dd></div>
    <div class="result"><dt>{c['lbl_result']}</dt><dd>{p['result']}</dd></div>
    <div><dt>{c['lbl_learn']}</dt><dd>{p['learn']}</dd></div>
  </dl>
  {sql_details(summary, code, lang)}
  <ul class="chips" aria-label="Tools">{tools}</ul>
  <div class="stages-mini" role="img" aria-label="{c['lbl_stages']}: {esc(names)}">{mini}</div>
</article>"""


# ---------------------------------------------------------------- page chrome
def head(lang, title, desc, path, alt_path, og):
    other = "en" if lang == "es" else "es"
    url = SITE_URL + path
    alt = SITE_URL + alt_path
    ld = {
        "@context": "https://schema.org", "@type": "Person", "name": "Daniel Galea Romero",
        "jobTitle": "Junior Data Analyst", "url": SITE_URL + "/",
        "email": f"mailto:{EMAIL}", "address": {"@type": "PostalAddress", "addressLocality": "Granada", "addressCountry": "ES"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Universidad de Granada"},
        "knowsAbout": ["SQL", "BigQuery", "Looker", "LookML", "Data analysis", "Google Cloud"],
        "sameAs": [LINKEDIN, GITHUB, CREDLY],
    }
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{lang}" href="{url}">
<link rel="alternate" hreflang="{other}" href="{alt}">
<link rel="alternate" hreflang="x-default" href="{SITE_URL}/">
<meta name="theme-color" content="#f7f6f2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121211" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Daniel Galea Romero">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE_URL}/assets/img/{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(title)}">
<meta property="og:locale" content="{'es_ES' if lang == 'es' else 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE_URL}/assets/img/{og}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/inter-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-serif-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={VERSION}">
<script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}document.documentElement.classList.add("js");</script>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
"""


def header(c, alt_href, nav=True, home_href="/"):
    navh = ""
    if nav:
        links = "".join(f'<a href="{h}">{t}</a>' for h, t in c["nav"])
        navh = f'<nav class="nav" aria-label="{"Secciones" if c["lang"] == "es" else "Sections"}">{links}</nav>'
    return f"""<body>
<a class="skip" href="#main">{c['skip']}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{home_href}">{BRAND}<span>Daniel Galea</span><small>· Data Analyst</small><span class="sr-only"> · {'inicio' if c['lang'] == 'es' else 'home'}</span></a>
    {navh}
    <div class="tools">
      <a class="lang" href="{alt_href}" hreflang="{c['other']}" lang="{c['other']}" title="{c['lang_label']}"><span aria-hidden="true">{c['lang_short']}</span><span class="sr-only">{c['lang_short']} · {c['lang_label']}</span></a>
      <button class="icon-btn theme-toggle" type="button" aria-label="{c['theme']}"><span class="sun">{icon('sun')}</span><span class="moon">{icon('moon')}</span></button>
    </div>
  </div>
</header>
"""


def footer(c):
    return f"""<footer class="site-footer">
  <div class="wrap">
    <p>{c['footer']}</p>
    <p>© 2026 Daniel Galea Romero</p>
  </div>
</footer>
<script src="/assets/js/site.js?v={VERSION}" defer></script>
</body>
</html>
"""


VERSION = "1"


# ---------------------------------------------------------------- home
def home(lang):
    c = C(lang)
    es = lang == "es"
    L = lambda a, b: a if es else b  # noqa: E731
    # hero chart: loans per year
    hero_items = [(r["issue_year"], r["loans"], num(r["loans"], lang), f"<b>{r['issue_year']}</b><br>{num(r['loans'], lang)} {L('préstamos', 'loans')}") for r in BY]
    hero_chart = cols(hero_items, label_idx=[0, len(BY) - 1], height=150)
    feat_items = [(r["issue_year"], r["total_amount"], musd(r["total_amount"], lang, 0), f"<b>{r['issue_year']}</b><br>{musd(r['total_amount'], lang)}") for r in BY]
    feat_chart = cols(feat_items, label_idx=[0, len(BY) - 1], title=c["feat_chart_t"], sub=c["feat_chart_s"], height=170,
                      table_head=(L("Ver los datos", "Show the data"), L("Año", "Year"), L("Importe", "Amount")))
    meter_v = OUT_TOTAL / 3.5e9 * 100
    meter_t = 3e9 / 3.5e9 * 100
    feat_meter = f"""<div class="chart"><p class="ctitle">{L("Saldo pendiente frente al límite", "Outstanding balance vs the limit")}</p>
      <p class="csub">{L("3.080,6 M$ pendientes · límite de Tesorería: 3.000 M$", "$3.08B outstanding · Treasury limit: $3.0B")}</p>
      <div class="meter" role="img" aria-label="{L('3.080,6 millones pendientes frente a un límite de 3.000 millones', '$3.08 billion outstanding against a $3.0 billion limit')}">
        <div class="track"><div class="fill" style="--v:{meter_v:.2f}%"></div><div class="mark" style="--t:{meter_t:.2f}%"><span>{L('límite', 'limit')}</span></div></div>
        <div class="scale"><span>0</span><span>{L('1.000', '1,000')}</span><span>{L('2.000', '2,000')}</span><span>{L('3.000', '3,000')}</span><span>{L('3.500 M$', '$3,500M')}</span></div>
      </div></div>"""
    stages = []
    for i, (key, name, what, tools) in enumerate(c["stages"]):
        stages.append(f"""<li><button class="stage" type="button" data-stage="{key}" aria-pressed="false">
          <span class="idx">0{i + 1}</span><span class="ico">{STAGE_ICONS[key]}</span><span class="name">{name}</span>
          <span class="what">{what}</span><span class="tools-l">{tools}</span></button>{LINK_ARROW}</li>""")
    kpis = "".join(f'<div class="kpi"><div class="v{(" " + cl) if cl else ""}">{v}</div><div class="l">{l}</div></div>' for v, l, cl in c["feat_kpis"])
    tools_feat = "".join(f'<li class="chip">{t}</li>' for t in c["tools_feat"])
    cards = "".join(project_card(p, c) for p in projects(lang))
    groups = []
    for gi, (ic, gname, items) in enumerate(c["stack_groups"]):
        chips = []
        for name, was in items:
            old = " old" if gi == c["stack_old_group"] else ""
            w = f' <span class="was">({was})</span>' if was else ""
            chips.append(f'<li class="chip{old}">{esc(name)}{w}</li>')
        groups.append(f'<section><h3>{icon(ic)}{gname}</h3><ul class="chips">{"".join(chips)}</ul></section>')
    courses = "".join(f"<li>{esc(x)}</li>" for x in c["courses"])
    facts = "".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in c["facts"])
    about_p = "".join(f"<p>{p}</p>" for p in c["about_p"])
    links = "".join(f'<li><a href="{h}"{" download" if h.endswith(".pdf") else ""}{" rel=\"me noopener\" target=\"_blank\"" if h.startswith("http") else ""}>{t}<span>{s}</span>{icon("arrow")}</a></li>' for t, s, h in c["links"])
    seal = f"""<svg class="seal" viewBox="0 0 300 300" role="img" aria-label="Google Cloud Data Analytics Certificate · 5/5">
      <defs><path id="circ-{lang}" d="M150 150 m-112 0 a112 112 0 1 1 224 0 a112 112 0 1 1 -224 0"/></defs>
      <circle class="ring" cx="150" cy="150" r="140"/><circle class="ring2" cx="150" cy="150" r="128"/><circle class="ring" cx="150" cy="150" r="92"/>
      <text><textPath href="#circ-{lang}" startOffset="0" textLength="700" lengthAdjust="spacing">GOOGLE CLOUD · DATA ANALYTICS CERTIFICATE · 2026 ·</textPath></text>
      <text class="big" x="150" y="160" text-anchor="middle">5/5</text>
      <text class="mid" x="150" y="184" text-anchor="middle">{c['seal_mid']}</text>
      <text x="150" y="208" text-anchor="middle">{c['seal_date']}</text>
    </svg>"""
    body = f"""
<main id="main">
  <section class="hero">
    <div class="wrap hero-grid">
      <div>
        <p class="eyebrow">{c['eyebrow']}</p>
        <h1>{c['h1']}</h1>
        <p class="lead">{c['lead']}</p>
        <p class="pill"><span class="pulse" aria-hidden="true"></span>{c['avail']}</p>
        <div class="cta">
          <a class="btn primary" href="{CV[lang]}" download>{icon('down')}{c['cta_cv']}</a>
          <a class="btn" href="{LINKEDIN}" rel="me noopener" target="_blank">LinkedIn{icon('arrow')}</a>
          <a class="btn" href="mailto:{EMAIL}">{icon('mail')}{c['cta_mail']}</a>
        </div>
      </div>
      <figure class="qcard rv" aria-labelledby="qcap-{lang}">
        <div class="qcard-bar"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>{c['qcard_file']}<span class="run">● {c['qcard_run']}</span></div>
        {code_block(SQL_HERO, 'sql', copy=False)}
        <div class="qbody">{hero_chart}</div>
        <figcaption id="qcap-{lang}">{c['qcard_cap']}</figcaption>
      </figure>
    </div>
  </section>

  <section class="section" id="sobre-mi" aria-labelledby="about-h">
    <div class="wrap">
      <div class="section-head"><p class="kicker">{c['about_k']}</p><h2 id="about-h">{c['about_h']}</h2></div>
      <div class="about">
        <div class="spacer"></div>
        <div class="text rv">{about_p}</div>
        <dl class="facts rv">{facts}</dl>
      </div>
    </div>
  </section>

  <section class="section" id="data-journey" aria-labelledby="journey-h">
    <div class="wrap">
      <div class="section-head"><p class="kicker">{c['journey_k']}</p><div><h2 id="journey-h">{c['journey_h']}</h2><p class="section-intro">{c['journey_intro']}</p></div></div>
      <ol class="journey">{''.join(stages)}</ol>
      <p class="journey-hint"><button type="button" data-journey-reset hidden>{c['journey_reset']}</button></p>
    </div>
  </section>

  <section class="section" id="proyectos" aria-labelledby="proj-h">
    <div class="wrap">
      <div class="section-head"><p class="kicker">{c['proj_k']}</p><div><h2 id="proj-h">{c['proj_h']}</h2><p class="section-intro">{c['proj_intro']}</p></div></div>
      <article class="featured rv" id="p-capstone" data-stages="collect process store analyze activate">
        <div class="fx">
          <p class="tag">{c['feat_tag']}</p>
          <h3>{c['feat_h']}</h3>
          <p>{c['feat_p']}</p>
          <div class="kpis">{kpis}</div>
          <ul class="chips" aria-label="Tools">{tools_feat}</ul>
          <div class="cta"><a class="btn primary" href="{CASE[lang]}">{c['feat_cta']}{icon('arrow')}</a></div>
        </div>
        <div class="fx viz">{feat_chart}{feat_meter}</div>
      </article>
      <div class="projects" style="margin-top:20px">{cards}</div>
    </div>
  </section>

  <section class="section" id="stack" aria-labelledby="stack-h">
    <div class="wrap">
      <div class="section-head"><p class="kicker">{c['stack_k']}</p><h2 id="stack-h">{c['stack_h']}</h2></div>
      <div class="stack-grid rv">{''.join(groups)}</div>
      <p class="stack-legend">{c['stack_note']}</p>
    </div>
  </section>

  <section class="section" id="certificado" aria-labelledby="cert-h">
    <div class="wrap cert">
      <div class="rv">{seal}</div>
      <div>
        <p class="kicker">{c['cert_k']}</p>
        <h2 id="cert-h" style="margin-top:14px">{c['cert_h']}</h2>
        <p class="section-intro">{c['cert_p']}</p>
        <ol class="courses">{courses}</ol>
        <a class="btn" href="{CREDLY}" rel="noopener" target="_blank">{c['cert_btn']}{icon('arrow')}</a>
      </div>
    </div>
  </section>

  <section class="section" id="contacto" aria-labelledby="contact-h">
    <div class="wrap contact">
      <div>
        <p class="kicker">{c['contact_k']}</p>
        <h2 id="contact-h" style="margin-top:14px">{c['contact_h']}</h2>
        <p class="section-intro">{c['contact_p']}</p>
      </div>
      <ul class="links">{links}</ul>
    </div>
  </section>
</main>
"""
    alt = HOME[c["other"]]
    og = f"og-{lang}.png"
    return head(lang, c["title_home"], c["desc_home"], HOME[lang], alt, og) + header(c, alt, home_href=HOME[lang]) + body + footer(c)


# ---------------------------------------------------------------- case study
def case(lang):
    es = lang == "es"
    L = lambda a, b: a if es else b  # noqa: E731
    c = C(lang)
    title = L("TheLook Fintech · Caso: salud de la cartera de préstamos · Daniel Galea Romero",
              "TheLook Fintech · Case study: loan-portfolio health · Daniel Galea Romero")
    desc = L("Caso completo del capstone del Google Cloud Data Analytics Certificate: BigQuery, SQL, Looker Enterprise y LookML sobre 270.299 préstamos, con insights y recomendaciones.",
             "Full case study of the Google Cloud Data Analytics Certificate capstone: BigQuery, SQL, Looker Enterprise and LookML on 270,299 loans, with insights and recommendations.")

    # charts
    amount_items = [(r["issue_year"], r["total_amount"], musd(r["total_amount"], lang, 0), f"<b>{r['issue_year']}</b><br>{musd(r['total_amount'], lang)} · {num(r['loans'], lang)} {L('préstamos', 'loans')}") for r in BY]
    loans_items = [(r["issue_year"], r["loans"], num(r["loans"], lang), f"<b>{r['issue_year']}</b><br>{num(r['loans'], lang)} {L('préstamos', 'loans')}") for r in BY]
    ch_amount = cols(amount_items, label_idx=[0, 7], title=L("Importe prestado por año", "Amount lent per year"), sub=L("Millones de dólares", "Millions of dollars"),
                     table_head=(L("Ver los datos", "Show the data"), L("Año", "Year"), L("Importe", "Amount")))
    ch_loans = cols(loans_items, label_idx=[0, 7], title=L("Préstamos emitidos por año", "Loans issued per year"), sub=L("Número de préstamos · tabla loan_count_by_year", "Number of loans · loan_count_by_year table"),
                    table_head=(L("Ver los datos", "Show the data"), L("Año", "Year"), L("Préstamos", "Loans")))
    status_names = {
        "Current": L("Al corriente", "Current"), "Charged Off": L("Fallido (charged off)", "Charged off"),
        "Late (31-120 days)": L("Retraso 31–120 días", "Late 31–120 days"), "In Grace Period": L("Periodo de gracia", "Grace period"),
        "Late (16-30 days)": L("Retraso 16–30 días", "Late 16–30 days"), "Default": L("Impago (default)", "Default"),
    }
    st_items = [(status_names[r["loan_status"]], r["amount"], f'{musd(r["amount"], lang, 1)} · {pct(r["amount"] / OUT_TOTAL * 100, lang, 2)}',
                 f'{status_names[r["loan_status"]]}: {musd(r["amount"], lang, 1)}') for r in OUT]
    ch_status = bars(st_items, lang, label_w=150, muted=[0], crit=[1, 2, 3, 4, 5],
                     title=L("Saldo pendiente por estado del préstamo", "Outstanding balance by loan status"),
                     sub=L("Millones de dólares y % del total pendiente", "Millions of dollars and % of total outstanding"),
                     table_head=(L("Ver los datos", "Show the data"), L("Estado", "Status"), L("Importe", "Amount")))
    purpose_names = {
        "debt_consolidation": L("Consolidación de deuda", "Debt consolidation"), "credit_card": L("Tarjeta de crédito", "Credit card"),
        "home_improvement": L("Reformas del hogar", "Home improvement"), "other": L("Otros", "Other"), "major_purchase": L("Compra importante", "Major purchase"),
    }
    tp = FT["top_purposes"]
    shown = tp[:5]
    rest = TOTAL_LOANS - sum(r["loans"] for r in shown)
    pur_items = [(purpose_names[r["purpose"]], r["loans"], f'{num(r["loans"], lang)} · {pct(r["loans"] / TOTAL_LOANS * 100, lang, 0)}', f'{purpose_names[r["purpose"]]}: {num(r["loans"], lang)}') for r in shown]
    pur_items.append((L("Resto de finalidades", "All other purposes"), rest, f'{num(rest, lang)} · {pct(rest / TOTAL_LOANS * 100, lang, 0)}', L("Resto", "Rest")))
    ch_purpose = bars(pur_items, lang, label_w=170, hl=[0, 1], muted=[2, 3, 4, 5],
                      title=L("Préstamos por finalidad", "Loans by purpose"), sub=L("Columna anidada application.purpose · 2012–2019", "Nested column application.purpose · 2012–2019"),
                      table_head=(L("Ver los datos", "Show the data"), L("Finalidad", "Purpose"), L("Préstamos", "Loans")))
    sts = FT["top_states_outstanding"]
    state_items = [(r["state"], r["outstanding_loans"], num(r["outstanding_loans"], lang), f'{r["state"]}: {num(r["outstanding_loans"], lang)} {L("préstamos pendientes", "outstanding loans")}') for r in sts]
    ch_states = bars(state_items, lang, label_w=40, hl=[0, 1, 2, 3], muted=[4, 5, 6, 7, 8, 9],
                     title=L("Top 10 estados por préstamos pendientes", "Top 10 states by outstanding loans"), sub=L("Número de préstamos no pagados del todo", "Number of loans not fully paid"),
                     table_head=(L("Ver los datos", "Show the data"), L("Estado", "State"), L("Préstamos", "Loans")))
    top4 = sum(r["outstanding_loans"] for r in sts[:4])
    next6 = sum(r["outstanding_loans"] for r in sts[4:])
    meter_v = OUT_TOTAL / 3.5e9 * 100
    meter_t = 3e9 / 3.5e9 * 100
    meter = f"""<div class="chart"><p class="ctitle">{L("Saldo pendiente frente al límite de Tesorería", "Outstanding balance vs Treasury's limit")}</p>
      <p class="csub">{L("Escala de 0 a 3.500 M$", "Scale from $0 to $3.5B")}</p>
      <div class="meter" role="img" aria-label="{L('3.080,6 millones pendientes frente a un límite de 3.000 millones', '$3.08 billion outstanding against a $3.0 billion limit')}">
        <div class="track"><div class="fill" style="--v:{meter_v:.2f}%"></div><div class="mark" style="--t:{meter_t:.2f}%"><span>{L('límite 3.000 M$', 'limit $3.0B')}</span></div></div>
        <div class="scale"><span>0</span><span>{L('1.000', '1,000')}</span><span>{L('2.000', '2,000')}</span><span>{L('3.000', '3,000')}</span><span>{L('3.500 M$', '$3,500M')}</span></div>
      </div></div>"""

    # dashboard recreation
    seg_cls = {"Current": "sm", "Charged Off": "sc", "Late (31-120 days)": "s2", "In Grace Period": "s4", "Late (16-30 days)": "s5", "Default": "s1"}
    stack_spans = "".join(f'<span class="{seg_cls[r["loan_status"]]}" style="flex:{r["amount"] / OUT_TOTAL * 100:.3f}" data-tip="{esc(status_names[r["loan_status"]])}: {pct(r["amount"] / OUT_TOTAL * 100, lang, 2)}"></span>' for r in OUT)
    stack_leg = "".join(f'<li><i class="{seg_cls[r["loan_status"]]}"></i>{esc(status_names[r["loan_status"]])} <span class="num">{pct(r["amount"] / OUT_TOTAL * 100, lang, 2)}</span></li>' for r in OUT)
    mini_states = bars([(r["state"], r["outstanding_loans"], num(r["outstanding_loans"], lang), f'{r["state"]}: {num(r["outstanding_loans"], lang)}') for r in sts], lang, label_w=28)
    red_rows = "".join(f'<tr><td><span class="redact" style="width:{w1}px"></span></td><td><span class="redact" style="width:{w2}px"></span></td><td><span class="redact" style="width:22px"></span></td><td><span class="redact" style="width:30px"></span></td></tr>' for w1, w2 in [(70, 52), (58, 50), (64, 48), (52, 46), (66, 44)])
    dashboard = f"""<div class="dash" role="group" aria-label="{L('Recreación del dashboard Loan Insights', 'Recreation of the Loan Insights dashboard')}">
      <div class="dash-top"><strong>Loan Insights</strong><span class="filters"><span>Cross-filtering: on</span><span>{L('Refresco: 1 h', 'Refresh: 1 h')}</span></span></div>
      <div class="tiles">
        <div class="tile single"><h3>Total Amount of Outstanding Loans <small>single value</small></h3>
          <div class="val">{L('3.080.553.000', '3,080,553,000')}</div>
          <p class="rule">{L('Formato condicional: fondo rojo si &gt; 3.000.000.000', 'Conditional formatting: red background if &gt; 3,000,000,000')}</p></div>
        <div class="tile"><h3>Percentage of Outstanding Loans <small>{L('pie → barra', 'pie → bar')}</small></h3>
          <div class="stack" style="height:26px">{stack_spans}</div><ul class="legend">{stack_leg}</ul></div>
        <div class="tile"><h3>Total Count of Outstanding Loans <small>bar · top 10</small></h3>{mini_states}</div>
        <div class="tile"><h3>Top 10 Customers by Highest Income <small>table</small></h3>
          <table class="ptable"><thead><tr><th>Customer ID</th><th>Annual Income</th><th>State</th><th>Rate</th></tr></thead><tbody>{red_rows}</tbody></table>
          <p class="rule" style="font-size:12px;color:var(--muted);margin:8px 0 0">{L('Filtros: Home Ownership = OWN · Loan Status = Current. Filas ocultas a propósito: no publico datos de clientes, aunque sean ficticios.', 'Filters: Home Ownership = OWN · Loan Status = Current. Rows hidden on purpose: I don’t publish customer-level data, even fictional.')}</p></div>
      </div>
    </div>
    <p class="dash-note">{L('Recreación en HTML con los datos reales del dataset, a partir del dashboard que construí en Looker Enterprise dentro del entorno del lab (que no se puede compartir fuera de él). En Looker el reparto por estado era un gráfico circular; aquí lo muestro como barra apilada, que se lee mejor con porcentajes tan pequeños.', 'HTML recreation with the dataset’s real figures, based on the dashboard I built in Looker Enterprise inside the lab environment (which can’t be shared outside it). In Looker the status split was a pie chart; here it’s a stacked bar, which reads better with such small percentages.')}</p>"""

    refresh = f"""<div class="tablewrap"><table class="refresh"><thead><tr><th>Tile</th><th>{L('Frecuencia', 'Frequency')}</th><th>{L('Por qué', 'Why')}</th></tr></thead><tbody>
      <tr><td>Total Amount of Outstanding Loans</td><td>{L('Cada hora', 'Hourly')}</td><td>{L('Es la alerta de riesgo: tiene que estar al día', 'It is the risk alert: it must be fresh')}</td></tr>
      <tr><td>Percentage of Outstanding Loans</td><td>{L('Diaria', 'Daily')}</td><td>{L('El reparto por estado cambia despacio', 'The status mix moves slowly')}</td></tr>
      <tr><td>Top 10 Customers by Highest Income</td><td>{L('Diaria', 'Daily')}</td><td>{L('Ahorra consultas sin perder utilidad', 'Saves queries without losing usefulness')}</td></tr>
      <tr><td>{L('Dashboard completo', 'Whole dashboard')}</td><td>{L('Cada hora', 'Hourly')}</td><td>{L('Coherente con el tile más exigente', 'Matches the most demanding tile')}</td></tr></tbody></table></div>"""

    # architecture diagram (horizontal + vertical)
    def arch_h():
        boxes = [
            (20, L("RECOGER", "COLLECT"), "Cloud Storage", "LOAD DATA · *.csv", False),
            (210, L("PROCESAR", "PROCESS"), "BigQuery · SQL", "JOIN · DISTINCT", True),
            (400, L("ALMACENAR", "STORE"), L("Tablas fintech", "fintech tables"), L("4 tablas · 3 CTAS", "4 tables · 3 CTAS"), False),
            (590, L("ANALIZAR", "ANALYZE"), "LookML", "loan.view · Explore", True),
            (780, L("ACTIVAR", "ACTIVATE"), L("Tesorería", "Treasury"), "Dashboard · Sheets", False),
        ]
        g = []
        for x, k, t1, t2, acc in boxes:
            g.append(f'<rect class="box{" acc" if acc else ""}" x="{x}" y="40" width="160" height="96" rx="12"/>'
                     f'<text class="t3" x="{x + 16}" y="66">{k}</text><text class="t1" x="{x + 16}" y="94">{esc(t1)}</text><text class="t2" x="{x + 16}" y="116">{esc(t2)}</text>')
        wires = "".join(f'<path class="wire" d="M{x + 160} 88h30"/><path class="flow" d="M{x + 160} 88h30"/>' for x in (20, 210, 400, 590))
        under = (f'<text class="t2" x="400" y="170">{L("loan_with_region · loan_purposes · loan_count_by_year · state_region", "loan_with_region · loan_purposes · loan_count_by_year · state_region")}</text>'
                 f'<path class="wire" d="M480 136v18"/>')
        return (f'<svg class="h" viewBox="0 0 960 180" role="img" aria-labelledby="arch-t-{lang}"><title id="arch-t-{lang}">'
                f'{esc(L("Arquitectura del capstone: CSV en Cloud Storage, procesado con SQL en BigQuery, cuatro tablas de resultado, modelo LookML y dashboard para Tesorería.", "Capstone architecture: CSV in Cloud Storage, SQL processing in BigQuery, four result tables, a LookML model and a dashboard for Treasury."))}'
                f'</title>{"".join(g)}{wires}{under}</svg>')

    def arch_v():
        boxes = [
            (L("RECOGER", "COLLECT"), "Cloud Storage", "LOAD DATA · *.csv", False),
            (L("PROCESAR", "PROCESS"), "BigQuery · SQL", "JOIN · DISTINCT", True),
            (L("ALMACENAR", "STORE"), L("Tablas fintech", "fintech tables"), L("4 tablas · 3 CTAS", "4 tables · 3 CTAS"), False),
            (L("ANALIZAR", "ANALYZE"), "LookML", "loan.view · Explore", True),
            (L("ACTIVAR", "ACTIVATE"), L("Tesorería", "Treasury"), "Dashboard · Sheets", False),
        ]
        g = []
        for i, (k, t1, t2, acc) in enumerate(boxes):
            y = 10 + i * 124
            g.append(f'<rect class="box{" acc" if acc else ""}" x="20" y="{y}" width="320" height="92" rx="12"/>'
                     f'<text class="t3" x="40" y="{y + 28}">{k}</text><text class="t1" x="40" y="{y + 56}">{esc(t1)}</text><text class="t2" x="40" y="{y + 76}">{esc(t2)}</text>')
            if i < 4:
                g.append(f'<path class="wire" d="M180 {y + 92}v32"/><path class="flow" d="M180 {y + 92}v32"/>')
        return (f'<svg class="v" viewBox="0 0 360 620" role="img" aria-labelledby="archv-t-{lang}"><title id="archv-t-{lang}">'
                f'{esc(L("Arquitectura del capstone en cinco pasos", "Capstone architecture in five steps"))}</title>{"".join(g)}</svg>')

    toc_items = [("problema", L("El problema", "The problem")), ("datos", L("Los datos", "The data")), ("proceso", L("Proceso en BigQuery", "BigQuery process")),
                 ("dashboard", L("Dashboard en Looker", "Looker dashboard")), ("insights", "Insights"), ("recomendaciones", L("Recomendaciones", "Recommendations")),
                 ("aprendizajes", L("Qué aprendí", "What I learned"))]
    toc = "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in toc_items)

    steps = [
        (L("Importar la clasificación de estados desde Cloud Storage", "Import the state classification from Cloud Storage"),
         L("Trevor nos dio un CSV que asigna región y subregión a cada estado. Lo cargué como tabla estándar con <code>LOAD DATA OVERWRITE</code> y un esquema explícito, usando un comodín para leer todos los ficheros.",
           "Trevor gave us a CSV mapping each state to a region and subregion. I loaded it as a standard table with <code>LOAD DATA OVERWRITE</code> and an explicit schema, using a wildcard to read every file."),
         SQL_LOAD, None),
        (L("Unir por la clave correcta y guardar el informe", "Join on the right key and save the report"),
         L("El informe necesitaba <code>loan_id</code>, <code>loan_amount</code> y la región nueva. Había dos consultas candidatas: la que unía por <code>region</code> parecía razonable, pero la clave que comparten las dos tablas es <code>state</code>. Guardé el resultado con un CTAS y lo abrí en <strong>Connected Sheets</strong> para que Tesorería lo filtrara en una hoja de cálculo (unas 270.000 filas).",
           "The report needed <code>loan_id</code>, <code>loan_amount</code> and the new region. There were two candidate queries: joining on <code>region</code> looked plausible, but the key both tables share is <code>state</code>. I saved the result with CTAS and opened it in <strong>Connected Sheets</strong> so Treasury could filter it as a spreadsheet (about 270,000 rows)."),
         SQL_JOIN, L("Unir por <code>region</code> habría usado la clasificación antigua (o ninguna). El JOIN decide qué dice el informe.", "Joining on <code>region</code> would have used the old classification (or none). The JOIN decides what the report says.")),
        (L("Datos anidados y deduplicación", "Nested data and deduplication"),
         L("La finalidad del préstamo vive dentro del registro anidado <code>application</code>. <code>SELECT purpose</code> falla; hay que usar notación de punto. Con <code>DISTINCT</code> y un CTAS dejé una tabla limpia de finalidades únicas.",
           "The loan purpose lives inside the nested <code>application</code> record. <code>SELECT purpose</code> fails; you need dot notation. With <code>DISTINCT</code> and CTAS I left a clean table of unique purposes."),
         SQL_DEDUP, None),
        (L("Informe de flujo de caja por año", "Cash-flow report by year"),
         L("Para la pregunta del flujo de caja, Trevor quería una fila por año. <code>GROUP BY</code> con <code>COUNT</code> y <code>SUM</code>, guardado como tabla para reutilizarlo.",
           "For the cash-flow question Trevor wanted one row per year. <code>GROUP BY</code> with <code>COUNT</code> and <code>SUM</code>, saved as a table for reuse."),
         SQL_YEAR, None),
    ]
    steps_html = ""
    for t, p, sql, why in steps:
        w = f'<p class="why">{why}</p>' if why else ""
        steps_html += f'<div class="stepcard"><h3>{t}</h3><p>{p}</p>{w}{code_block(sql)}</div>'

    qrows = [
        (L("¿Cómo vigilamos el flujo de caja?", "How do we watch cash flow?"), L("Importe prestado por año", "Amount lent per year"), L("Lo que sale no debe superar lo que entra.", "Cash out must not exceed cash in.")),
        (L("¿Para qué piden los préstamos?", "Why do customers borrow?"), L("Finalidad (<code>application.purpose</code>)", "Purpose (<code>application.purpose</code>)"), L("La finalidad está muy relacionada con la probabilidad de devolver.", "Purpose is strongly linked to the likelihood of repayment.")),
        (L("¿Dónde están los prestatarios?", "Where are the borrowers?"), L("Ubicación (estado → región)", "Location (state → region)"), L("La concentración geográfica aumenta el riesgo de impagos colectivos.", "Geographic concentration raises the risk of collective defaults.")),
        (L("¿Cuánto tenemos pendiente?", "How much is outstanding?"), L("Saldo pendiente vs límite de 3.000 M$", "Outstanding balance vs $3B limit"), L("Es el máximo que el equipo considera prudente prestar.", "It is the most the team considers prudent to lend.")),
        (L("¿Qué parte va mal?", "Which part is going wrong?"), L("% del saldo por estado del préstamo", "% of balance by loan status"), L("Retrasos, fallidos e impagos son el riesgo real.", "Late, charged-off and defaulted loans are the real risk.")),
    ]
    qtable = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{d}</td></tr>" for a, b, d in qrows)

    rec_mine = [
        L("<strong>Frenar la emisión nueva mientras el saldo supere el límite</strong> y priorizar el cobro: hoy está 80,6 M$ por encima.", "<strong>Slow new lending while the balance is over the limit</strong> and prioritise collections: it is $80.6M over today."),
        L(f"<strong>Vigilar la concentración</strong> en California, Texas, Nueva York y Florida ({num(top4, 'es')} préstamos pendientes, más que los otros seis estados del top 10 juntos).", f"<strong>Watch concentration</strong> in California, Texas, New York and Florida ({num(top4, 'en')} outstanding loans, more than the other six top-10 states combined)."),
        L("<strong>Revisar el riesgo por finalidad</strong>: el 80 % de los préstamos son para consolidar deudas o pagar tarjetas.", "<strong>Review risk by purpose</strong>: 80% of loans are for debt consolidation or credit cards."),
    ]
    next_steps = [
        L("Añadir una <strong>alerta</strong> automática cuando el saldo cruce el umbral, además del color.", "Add an automatic <strong>alert</strong> when the balance crosses the threshold, not just a colour."),
        L("Incorporar los <strong>cobros</strong> (entradas de caja) para ver el flujo de caja completo, no solo las salidas.", "Bring in <strong>repayments</strong> (cash in) to see the full cash-flow picture, not just the outflows."),
        L("Recoger <strong>feedback</strong> de Tesorería sobre el dashboard e iterar, y <strong>segmentar a los prestatarios</strong> por comportamiento (como en mi proyecto RFM).", "Collect Treasury's <strong>feedback</strong> on the dashboard and iterate, and <strong>segment borrowers</strong> by behaviour (as in my RFM project)."),
    ]
    learn = [
        (L("La clave del JOIN es una decisión de negocio", "The JOIN key is a business decision"), L("Dos consultas casi iguales daban informes distintos. Ahora compruebo qué columna comparten de verdad las tablas antes de unir.", "Two almost identical queries produced different reports. I now check which column the tables truly share before joining.")),
        (L("Una métrica no es una columna", "A metric is not a column"), L("«Saldo pendiente» en el lab suma el importe original de los préstamos no pagados del todo, no el capital vivo. En un caso real pediría el saldo vivo y lo documentaría en LookML.", "'Outstanding balance' in the lab sums the original amount of loans not fully paid, not the remaining principal. In a real job I'd ask for the live balance and document it in LookML.")),
        (L("Un umbral visible vale más que una tabla", "A visible threshold beats a table"), L("El formato condicional convierte la regla de Tesorería (3.000 M$) en algo que se ve en un segundo.", "Conditional formatting turns Treasury's rule ($3B) into something you see in one second.")),
        (L("Refrescar cuesta", "Refreshing has a cost"), L("Cada tile se actualiza según lo rápido que cambia su dato: rendimiento y coste, no solo frescura.", "Each tile refreshes as fast as its data changes: performance and cost, not just freshness.")),
        (L("Escribir para quien decide", "Write for the decision-maker"), L("El resumen ejecutivo cabe en una diapositiva: título, contexto, objetivo, resultados con cifras y un siguiente paso. Sin jerga.", "The executive summary fits on one slide: title, context, goal, results with numbers and a next step. No jargon.")),
    ]
    learn_html = "".join(f'<li><span class="ix">0{i + 1}</span><div><b>{a}</b>{b}</div></li>' for i, (a, b) in enumerate(learn))

    body = f"""
<main id="main">
  <section class="case-hero">
    <div class="wrap">
      <p class="crumbs"><a href="{HOME[lang]}#proyectos">{icon('back')}{L('Volver a proyectos', 'Back to projects')}</a></p>
      <p class="eyebrow">{L('Caso · Proyecto final del Google Cloud Data Analytics Certificate', 'Case study · Google Cloud Data Analytics Certificate capstone')}</p>
      <h1>{L('La salud de una cartera de <em>préstamos</em>, de BigQuery a Looker', 'The health of a <em>loan</em> portfolio, from BigQuery to Looker')}</h1>
      <p class="lead">{L('TheLook Fintech es una fintech ficticia que presta a tiendas online independientes para comprar inventario. Tesorería necesitaba saber, rápido y sin pedir informes, si estaban prestando más de lo prudente.', 'TheLook Fintech is a fictional fintech that lends to independent online stores so they can buy inventory. Treasury needed to know, quickly and without asking for reports, whether they were lending more than was prudent.')}</p>
      <dl class="meta">
        <div><dt>{L('Rol', 'Role')}</dt><dd>Cloud Data Analyst ({L('proyecto', 'project')})</dd></div>
        <div><dt>{L('Cliente interno', 'Stakeholder')}</dt><dd>{L('Tesorería (Trevor)', 'Treasury (Trevor)')}</dd></div>
        <div><dt>{L('Herramientas', 'Tools')}</dt><dd>BigQuery · SQL · Cloud Storage · Connected Sheets · Looker · LookML</dd></div>
        <div><dt>{L('Entregables', 'Deliverables')}</dt><dd>{L('4 tablas · dashboard · resumen ejecutivo', '4 tables · dashboard · executive summary')}</dd></div>
      </dl>
    </div>
  </section>
  <div class="wrap case-layout">
    <aside class="toc" aria-label="{L('En esta página', 'On this page')}"><p>{L('En esta página', 'On this page')}</p><ol>{toc}</ol></aside>
    <article class="article">
      <section aria-label="TL;DR">
        <div class="tldr"><h2>{L('En 20 segundos', 'In 20 seconds')}</h2><ul>
          <li>{L(f'Procesé en BigQuery {num(TOTAL_LOANS, "es")} préstamos (4.166 M$) y los dejé en tablas listas para Tesorería, una de ellas conectada a Google Sheets.', f'I processed {num(TOTAL_LOANS, "en")} loans ($4.17B) in BigQuery into tables ready for Treasury, one of them connected to Google Sheets.')}</li>
          <li>{L('Construí en Looker un dashboard de autoservicio que pinta en rojo el saldo pendiente cuando supera el límite: hoy, <strong>3.080,6 M$ frente a 3.000 M$</strong>.', 'I built a self-service Looker dashboard that turns the outstanding balance red when it breaks the limit: today, <strong>$3.08B against $3.0B</strong>.')}</li>
          <li>{L('Recomendación: frenar la emisión nueva, vigilar la concentración en 4 estados y revisar el riesgo de los préstamos para consolidar deuda (56 % del total).', 'Recommendation: slow new lending, watch concentration in 4 states and review the risk of debt-consolidation loans (56% of the total).')}</li>
        </ul></div>
      </section>

      <section id="problema" aria-labelledby="h-problema">
        <h2 id="h-problema"><span class="step">01</span>{L('El problema', 'The problem')}</h2>
        <div class="prose"><p>{L('La empresa está en fase de crecimiento y quiere escalar rápido. En una reunión con Trevor, jefe de Tesorería, salieron estas preguntas, cada una con su métrica:', 'The company is in its growth stage and wants to scale fast. In a meeting with Trevor, head of Treasury, these questions came up, each with its metric:')}</p></div>
        <div class="tablewrap"><table class="qtable"><thead><tr><th>{L('Pregunta', 'Question')}</th><th>{L('Métrica', 'Metric')}</th><th>{L('Por qué importa', 'Why it matters')}</th></tr></thead><tbody>{qtable}</tbody></table></div>
      </section>

      <section id="datos" aria-labelledby="h-datos">
        <h2 id="h-datos"><span class="step">02</span>{L('Los datos', 'The data')}</h2>
        <div class="prose">
          <p>{L('El <em>dataset</em> <code>fintech</code> de BigQuery, con dos tablas y un CSV externo:', 'The <code>fintech</code> BigQuery dataset, with two tables and an external CSV:')}</p>
          <ul class="clean">
            <li>{L(f'<code>loan</code>: {num(TOTAL_LOANS, "es")} préstamos de 2012 a 2019 con importe, tipo de interés, fecha y año de emisión, estado del préstamo, estado (territorio) y un registro anidado <code>application</code> con la finalidad.', f'<code>loan</code>: {num(TOTAL_LOANS, "en")} loans from 2012 to 2019 with amount, interest rate, issue date and year, loan status, state and a nested <code>application</code> record holding the purpose.')}</li>
            <li>{L('<code>customers</code>: ingresos anuales, propiedad de la vivienda, antigüedad laboral y estado de residencia.', '<code>customers</code>: annual income, home ownership, employment length and state of residence.')}</li>
            <li>{L('Un CSV en Cloud Storage con la nueva clasificación de estados en regiones y subregiones.', 'A CSV in Cloud Storage with the new classification of states into regions and subregions.')}</li>
          </ul>
          <p>{L('Limitaciones: los datos son ficticios (Google Cloud Training), llegan hasta 2019 y no incluyen los cobros, así que el flujo de caja solo se ve por el lado de las salidas.', 'Limitations: the data is fictional (Google Cloud Training), stops in 2019 and has no repayments, so cash flow can only be seen from the outflow side.')}</p>
        </div>
        <div class="arch">{arch_h()}{arch_v()}</div>
      </section>

      <section id="proceso" aria-labelledby="h-proceso">
        <h2 id="h-proceso"><span class="step">03</span>{L('Proceso en BigQuery', 'Process in BigQuery')}</h2>
        <p class="prose">{L('Parte 1 del capstone: recoger, procesar y almacenar. El SQL es el que usé en el lab.', 'Capstone part 1: collect, process and store. The SQL is what I ran in the lab.')}</p>
        <div class="steps">{steps_html}</div>
        <div class="grid2" style="margin-top:28px"><div class="card">{ch_loans}</div><div class="card">{ch_amount}</div></div>
      </section>

      <section id="dashboard" aria-labelledby="h-dash">
        <h2 id="h-dash"><span class="step">04</span>{L('Dashboard en Looker', 'Looker dashboard')}</h2>
        <p class="prose">{L('Parte 2: analizar y activar. Un dashboard de autoservicio, <em>Loan Insights</em>, con cuatro visualizaciones sobre la <em>view</em> <code>loan</code> de LookML, <em>cross-filtering</em> (al pulsar un valor se filtran los demás tiles) y frecuencias de refresco por tile.', 'Part 2: analyse and activate. A self-service dashboard, <em>Loan Insights</em>, with four visualisations on the LookML <code>loan</code> view, cross-filtering (clicking a value filters the other tiles) and per-tile refresh schedules.')}</p>
        {dashboard}
        <h3>{L('La métrica por dentro', 'Inside the metric')}</h3>
        <p class="prose">{L('El tile principal usa la métrica de LookML <em>Outstanding Loans Amount</em>. Este es el SQL que genera Looker: suma el importe de todo préstamo cuyo estado no sea <em>Fully Paid</em>.', 'The main tile uses the LookML measure <em>Outstanding Loans Amount</em>. This is the SQL Looker generates: it sums the amount of every loan whose status is not <em>Fully Paid</em>.')}</p>
        {code_block(SQL_LOOKER)}
        <h3>{L('Refresco por tile', 'Per-tile refresh')}</h3>
        {refresh}
      </section>

      <section id="insights" aria-labelledby="h-ins">
        <h2 id="h-ins"><span class="step">05</span>Insights</h2>
        <div class="insight">
          <div><h3>{L('El saldo pendiente ya supera el límite', 'The outstanding balance is already over the limit')}</h3>
            <p class="big alert num">{L('3.080,6 M$', '$3.08B')}</p>
            <p>{L('Un 2,7 % por encima de los 3.000 M$ que Tesorería considera prudentes. El 87,9 % está al corriente, pero <strong>373 M$ (12,1 %)</strong> no: sobre todo préstamos fallidos (279 M$).', '2.7% above the $3B Treasury considers prudent. 87.9% is current, but <strong>$373M (12.1%)</strong> is not — mostly charged-off loans ($279M).')}</p></div>
          <div>{meter}<div style="height:18px"></div>{ch_status}</div>
        </div>
        <div class="insight">
          <div><h3>{L('Crecimiento muy rápido', 'Very fast growth')}</h3>
            <p class="big num">×24</p>
            <p>{L('El importe prestado pasó de 35,5 M$ en 2012 a <strong>852,4 M$ en 2019</strong> (2.594 → 51.737 préstamos). Crecer así exige vigilar el riesgo a la vez.', 'Lending grew from $35.5M in 2012 to <strong>$852.4M in 2019</strong> (2,594 → 51,737 loans). Growing this fast requires watching risk at the same time.')}</p></div>
          <div class="card">{ch_amount}</div>
        </div>
        <div class="insight">
          <div><h3>{L('La mayoría refinancia deuda', 'Most borrowers refinance debt')}</h3>
            <p class="big num">{L('80 %', '80%')}</p>
            <p>{L('de los préstamos son para consolidar deudas (56 %) o pagar tarjetas de crédito (24 %). La finalidad está muy ligada a la probabilidad de devolver: es la primera palanca de riesgo.', 'of loans are for debt consolidation (56%) or credit-card payoff (24%). Purpose is closely tied to repayment likelihood: it is the first risk lever.')}</p></div>
          <div class="card">{ch_purpose}</div>
        </div>
        <div class="insight">
          <div><h3>{L('Cuatro estados concentran el riesgo', 'Four states concentrate the risk')}</h3>
            <p class="big num">{num(top4, lang)}</p>
            <p>{L(f'préstamos pendientes en California, Texas, Nueva York y Florida: más que los otros seis estados del top 10 juntos ({num(next6, "es")}).', f'outstanding loans in California, Texas, New York and Florida — more than the other six top-10 states combined ({num(next6, "en")}).')}</p></div>
          <div class="card">{ch_states}</div>
        </div>
      </section>

      <section id="recomendaciones" aria-labelledby="h-rec">
        <h2 id="h-rec"><span class="step">06</span>{L('Recomendaciones', 'Recommendations')}</h2>
        <p class="prose">{L('Lo cerré con un resumen ejecutivo de una diapositiva para la dirección, sin jerga técnica:', 'I closed it with a one-slide executive summary for leadership, with no technical jargon:')}</p>
        <div class="slide">
          <div class="slide-head"><h3>{L('Préstamos bajo control: lo que Tesorería necesita ver', 'Lending under control: what Treasury needs to see')}</h3><span>{L('Para: equipo directivo de TheLook Fintech', 'Prepared for: TheLook Fintech executive team')}</span></div>
          <div class="slide-body">
            <div><h4>Overview</h4><p>{L('TheLook Fintech crece rápido y necesita que lo que presta no supere lo que entra. Reunimos los datos de préstamos en BigQuery y los convertimos en informes y un dashboard para seguir flujo de caja, finalidad y ubicación.', 'TheLook Fintech is growing fast and must make sure what it lends does not exceed what comes in. We brought loan data together in BigQuery and turned it into reports and a dashboard to track cash flow, purpose and location.')}</p></div>
            <div><h4>Objective</h4><ul><li>{L('Meta 1: informe de préstamos emitidos por año.', 'Goal 1: report of loans issued per year.')}</li><li>{L('Meta 2: dashboard de autoservicio con la salud de la cartera.', 'Goal 2: self-service dashboard on portfolio health.')}</li><li>{L('Impacto: decidir a tiempo, reducir riesgo y adaptar la oferta.', 'Impact: decide on time, reduce risk and tailor the offer.')}</li></ul></div>
            <div><h4>Results</h4><ul><li>{L('Préstamos ×20 entre 2012 y 2019 (2.594 → 51.737).', 'Loans ×20 between 2012 and 2019 (2,594 → 51,737).')}</li><li>{L('Saldo pendiente: 3.080,6 M$, por encima del límite y marcado en rojo.', 'Outstanding: $3.08B, above the limit and flagged red.')}</li><li>{L('87,9 % al corriente; 4 estados concentran el riesgo.', '87.9% current; 4 states concentrate the risk.')}</li></ul></div>
            <div><h4>Next steps</h4><ul>{''.join(f'<li>{x}</li>' for x in rec_mine)}</ul></div>
          </div>
        </div>
        <h3>{L('Y después', 'Then')}</h3>
        <ul class="clean prose">{''.join(f'<li>{x}</li>' for x in next_steps)}</ul>
      </section>

      <section id="aprendizajes" aria-labelledby="h-learn">
        <h2 id="h-learn"><span class="step">07</span>{L('Qué aprendí', 'What I learned')}</h2>
        <ul class="learn">{learn_html}</ul>
        <p class="prose" style="margin-top:22px;font-size:14.5px">{L(f'Proyecto final del certificado, con pasos guiados y retos sin instrucciones paso a paso, sobre datos ficticios de Google Cloud Training. Cifras consultadas de nuevo en <code>cloud-training-demos.fintech</code> el 12/10/2026; coinciden con las del lab. El SQL completo está en <a href="{CAPSTONE_REPO}">GitHub</a>.', f'Certificate capstone, mixing guided steps with challenges that had no step-by-step instructions, on fictional Google Cloud Training data. Figures re-queried from <code>cloud-training-demos.fintech</code> on 12 Oct 2026; they match the lab. The full SQL is on <a href="{CAPSTONE_REPO}">GitHub</a>.')}</p>
        <div class="next-case"><a class="btn" href="{HOME[lang]}#proyectos">{icon('back')}{L('Más proyectos', 'More projects')}</a><a class="btn primary" href="mailto:{EMAIL}">{icon('mail')}{L('Hablemos', "Let's talk")}</a></div>
      </section>
    </article>
  </div>
</main>
"""
    alt = CASE[c["other"]]
    return head(lang, title, desc, CASE[lang], alt, f"og-case-{lang}.png") + header(c, alt, nav=False, home_href=HOME[lang]) + body + footer(c)


def not_found():
    c = C("es")
    body = f"""<main id="main"><section class="case-hero"><div class="wrap">
<p class="eyebrow">404</p><h1>Esta página <em>no existe</em></h1>
<p class="lead">This page doesn’t exist.</p>
<div class="cta"><a class="btn primary" href="/">Inicio</a><a class="btn" href="/en/">Home (EN)</a></div>
</div></section></main>"""
    return head("es", "404 · Daniel Galea Romero", "Página no encontrada", "/404", "/en/", "og-es.png").replace('<link rel="canonical" href="' + SITE_URL + '/404">', '<meta name="robots" content="noindex">') + header(c, "/en/", nav=False) + body + footer(c)


def write(path, content):
    full = os.path.join(SITE, path.lstrip("/"))
    if full.endswith("/"):
        full += "index.html"
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    global VERSION
    VERSION = os.environ.get("ASSET_VERSION", "1")
    for lang in ("es", "en"):
        write(HOME[lang], home(lang))
        write(CASE[lang], case(lang))
    write("/404.html", not_found())
    urls = [HOME["es"], HOME["en"], CASE["es"], CASE["en"]]
    sm = "".join(f"<url><loc>{SITE_URL}{u}</loc></url>" for u in urls)
    write("/sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    print("built", SITE_URL)


if __name__ == "__main__":
    sys.exit(main())
