#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROHACELL Qualification Radar - static site generator.

Usage:  python3 build_site.py companies.json ./out
Rebuilds the whole site from the JSON database. The database is the only state;
it is published at /data/companies.json so the next run can fetch it back.
"""
import json, os, sys, html as H, datetime, shutil

STATUS = {
 'new':          ('New',           'st-new'),
 'contacted':    ('Contacted',     'st-contacted'),
 'in_discussion':('In discussion',  'st-disc'),
 'qualified':    ('Qualified',     'st-qual'),
 'dead':         ('Dead',          'st-dead'),
 'watch':        ('Watch only',    'st-watch'),
}
TIERNAME = {'A':'Contact now','B':'Worth a call','C':'Watch list'}

CSS = """
:root{color-scheme:light;
--bg:#f6f6f3; --card:#fff; --alt:#f0f0ec; --ink:#111110; --ink2:#4a4945; --muted:#7a7973;
--line:rgba(17,17,16,.10); --rule:#e4e3dc; --accent:#1b5fa8; --accent-soft:rgba(27,95,168,.09);
--good:#0a7d0a; --warn:#8a6a00; --dead:#a8332f; --shadow:0 1px 2px rgba(17,17,16,.05),0 4px 16px rgba(17,17,16,.04)}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;
--bg:#0e0e0d; --card:#191918; --alt:#232322; --ink:#f7f7f4; --ink2:#c0bfb6; --muted:#8b8a82;
--line:rgba(255,255,255,.10); --rule:#2b2b29; --accent:#78b4ff; --accent-soft:rgba(120,180,255,.12);
--good:#4ec44e; --warn:#e0b545; --dead:#e58480; --shadow:none}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.6 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.wrap{max-width:940px;margin:0 auto;padding:0 18px 80px}

/* nav */
nav.top{position:sticky;top:0;z-index:20;display:flex;gap:2px;overflow-x:auto;scrollbar-width:none;
margin:0 -18px 24px;padding:10px 18px;background:color-mix(in srgb,var(--bg) 88%,transparent);
backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--rule)}
nav.top::-webkit-scrollbar{display:none}
nav.top a{flex:0 0 auto;font-size:14px;font-weight:500;color:var(--ink2);text-decoration:none;
padding:7px 13px;border-radius:8px;transition:background .15s,color .15s}
nav.top a:hover{background:var(--alt);color:var(--ink)}
nav.top a.on{background:var(--accent);color:#fff}

h1{font-size:clamp(24px,4.4vw,31px);line-height:1.15;margin:26px 0 8px;letter-spacing:-.022em;font-weight:650}
h1 b{color:var(--accent);font-weight:650}
.sub{color:var(--muted);font-size:14px;margin:0 0 26px}
h2{font-size:12.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-weight:650;
margin:44px 0 0;padding-bottom:10px;border-bottom:1px solid var(--rule)}
h2+.note{color:var(--ink2);font-size:14.5px;margin:12px 0 18px}

.summary{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:14px;padding:18px 20px;margin-bottom:8px;box-shadow:var(--shadow)}
.summary p{margin:0 0 10px}.summary p:last-child{margin:0}

/* cards */
.card{position:relative;background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:20px 22px 18px;margin-bottom:14px;box-shadow:var(--shadow);
transition:border-color .15s,transform .15s,box-shadow .15s}
.card:hover{border-color:color-mix(in srgb,var(--accent) 35%,var(--line))}
.card:before{content:"";position:absolute;left:0;top:18px;bottom:18px;width:3px;border-radius:0 3px 3px 0;background:var(--rule)}
.card.tA:before{background:var(--good)} .card.tB:before{background:var(--warn)}
.card h3{font-size:20.5px;margin:0 0 12px;letter-spacing:-.015em;font-weight:640;line-height:1.25}
.card h3 a{color:inherit;text-decoration:none}
.card h3 a:hover{color:var(--accent)}

.tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px}
.tag{font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
border:1px solid var(--line);border-radius:100px;padding:3px 9px;color:var(--muted);white-space:nowrap}
.tag.score{color:var(--good);border-color:color-mix(in srgb,var(--good) 45%,transparent);
background:color-mix(in srgb,var(--good) 8%,transparent)}
.st-new{color:var(--accent);border-color:color-mix(in srgb,var(--accent) 45%,transparent);background:var(--accent-soft)}
.st-contacted,.st-disc{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 45%,transparent)}
.st-qual{color:var(--good);border-color:var(--good);font-weight:700}
.st-dead{color:var(--dead);border-color:color-mix(in srgb,var(--dead) 45%,transparent);text-decoration:line-through}
.st-watch{color:var(--muted)}

.bar{height:5px;background:var(--rule);border-radius:100px;overflow:hidden;margin:0 0 15px}
.bar i{display:block;height:100%;border-radius:100px;background:var(--accent)}

dl{margin:0;display:grid;grid-template-columns:128px 1fr;gap:12px 18px}
dt{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);padding-top:4px;font-weight:600}
dd{margin:0;color:var(--ink2)}
dd.opp{color:var(--ink)}
dd.src{font-size:13.5px}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
a:hover{text-decoration-thickness:2px}
.li{display:inline-flex;align-items:center;gap:5px;font-size:13.5px;background:var(--accent-soft);
border-radius:7px;padding:3px 9px;text-decoration:none;margin:2px 6px 2px 0}
.li:hover{background:color-mix(in srgb,var(--accent) 18%,transparent);text-decoration:none}

/* tables */
table{width:100%;border-collapse:separate;border-spacing:0;background:var(--card);
border:1px solid var(--line);border-radius:14px;overflow:hidden;font-size:14.5px;box-shadow:var(--shadow)}
th,td{text-align:left;padding:13px 15px;vertical-align:top;border-bottom:1px solid var(--rule)}
thead th{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);
font-weight:650;background:var(--alt)}
tr:last-child th,tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--alt)}
th[scope=row]{font-weight:600;color:var(--ink);width:25%}
th[scope=row] a{color:inherit;text-decoration:none}
th[scope=row] a:hover{color:var(--accent)}
.loc{display:block;font-weight:400;font-size:12.5px;color:var(--muted);margin-top:2px}
td{color:var(--ink2)}

ul.plain{list-style:none;padding:0;margin:0;background:var(--card);border:1px solid var(--line);
border-radius:14px;overflow:hidden;box-shadow:var(--shadow)}
ul.plain li{padding:13px 16px;border-bottom:1px solid var(--rule);color:var(--ink2);font-size:14.5px}
ul.plain li:last-child{border-bottom:0}
ul.plain li:hover{background:var(--alt)}
ul.plain .loc{display:inline;color:var(--muted);font-size:13px}

.method{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;
font-size:14.5px;color:var(--ink2);box-shadow:var(--shadow)}
.method b{color:var(--ink)}

/* timeline */
.tl{list-style:none;padding:0;margin:18px 0 0}
.tl li{position:relative;padding:0 0 22px 24px;border-left:2px solid var(--rule)}
.tl li:last-child{border-left-color:transparent;padding-bottom:0}
.tl li:before{content:"";position:absolute;left:-6px;top:6px;width:10px;height:10px;border-radius:50%;
background:var(--accent);box-shadow:0 0 0 3px var(--bg)}
.tl .d{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;font-weight:600}
.tl .k{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin-left:9px}
.tl .t{color:var(--ink2);margin-top:3px}

/* search */
#q{width:100%;font-size:16px;padding:14px 16px;border-radius:12px;border:1px solid var(--line);
background:var(--card);color:var(--ink);margin-bottom:10px;box-shadow:var(--shadow)}
#q:focus{outline:2px solid var(--accent);outline-offset:-1px;border-color:transparent}
.hint{font-size:13.5px;color:var(--muted);margin:0 0 20px}
.hit{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;
margin-bottom:10px;box-shadow:var(--shadow)}
.hit h4{margin:0 0 3px;font-size:16.5px;font-weight:620}
.hit h4 a{color:inherit;text-decoration:none}
.hit h4 a:hover{color:var(--accent)}
.hit .m{font-size:12.5px;color:var(--muted)}
.hit .x{font-size:14.5px;color:var(--ink2);margin-top:7px}
mark{background:color-mix(in srgb,var(--accent) 26%,transparent);color:inherit;padding:0 2px;border-radius:3px}

/* sector filter chips */
.chips{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 20px}
.chip{font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--ink2);
border-radius:100px;padding:7px 14px;cursor:pointer;font-family:inherit;transition:all .15s}
.chip:hover{border-color:var(--accent);color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}

/* compact expandable rows */
.legend{display:grid;grid-template-columns:1fr 148px 148px 86px 30px 92px;gap:12px;padding:0 16px 8px;
font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:650}
.row.umd .rn:before{background:var(--rule)}
.row.uhi .rn:before{background:var(--good)}
.ulegend{grid-template-columns:1fr 165px 175px 96px}
.rlegend{grid-template-columns:1fr 150px 92px 110px}
.shlegend{grid-template-columns:1fr 210px 190px 96px}
#rows.users .row.uhi>summary,#rows.users .row.umd>summary{grid-template-columns:1fr 210px 190px 96px}
@media (max-width:760px){#rows.users .row.uhi>summary,#rows.users .row.umd>summary{grid-template-columns:1fr 92px}
 .shlegend{display:none}}
#rows.users .row[data-kind]>summary{grid-template-columns:1fr 150px 92px 110px}
@media (max-width:760px){#rows.users .row[data-kind]>summary{grid-template-columns:1fr}
 .rlegend{display:none}}
.users .row>summary{grid-template-columns:1fr 165px 175px 96px}
@media (max-width:760px){.users .row>summary{grid-template-columns:1fr 92px}
 .users .rm{grid-column:1;grid-row:2}.users .rw{grid-column:1;grid-row:3}
 .users .row>summary .tag{grid-column:2;grid-row:1;justify-self:end}}
#rows{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow)}
.row{border-bottom:1px solid var(--rule)}
.row:last-child{border-bottom:0}
.row>summary{display:grid;grid-template-columns:1fr 148px 148px 86px 30px 92px;gap:12px;align-items:center;
padding:13px 16px;cursor:pointer;list-style:none;transition:background .12s}
.row>summary::-webkit-details-marker{display:none}
.row>summary:hover{background:var(--alt)}
.row[open]>summary{background:var(--alt)}
.row>summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.rn{font-weight:620;color:var(--ink);font-size:15.5px;line-height:1.3;position:relative;padding-left:12px}
.rn:before{content:"";position:absolute;left:0;top:4px;bottom:4px;width:3px;border-radius:3px;background:var(--rule)}
.row.tA .rn:before{background:var(--good)} .row.tB .rn:before{background:var(--warn)}
.rm,.rw{font-size:12.5px;color:var(--muted);line-height:1.35}
.rbar{height:5px;background:var(--rule);border-radius:100px;overflow:hidden}
.rbar i{display:block;height:100%;background:var(--accent);border-radius:100px}
.rs{font-size:13px;color:var(--ink2);font-variant-numeric:tabular-nums;font-weight:600;text-align:right}
.rbody{padding:4px 16px 20px 28px;border-top:1px solid var(--rule);background:var(--alt)}
.rbody .opp{margin:14px 0 16px;color:var(--ink);font-size:15px}
.rbody dl{grid-template-columns:120px 1fr;gap:10px 16px}
.rbody .more{margin:16px 0 0;font-size:14px}
.count{font-size:12.5px;color:var(--muted);margin:0 0 10px}
.chipgap{flex-basis:100%;height:0}
.cn{opacity:.6;font-variant-numeric:tabular-nums;margin-left:3px}
@media (max-width:760px){
 .legend{display:none}
 .row>summary{grid-template-columns:1fr 74px;gap:8px 10px;padding:12px 14px}
 .rn{grid-column:1;padding-left:11px}
 .rs{display:block;grid-column:2;grid-row:1;align-self:start}
 .rm{grid-column:1;grid-row:2;padding-left:11px}
 .rw{grid-column:1;grid-row:3;padding-left:11px}
 .rbar{grid-column:2;grid-row:2}
 .row>summary .tag{grid-column:2;grid-row:3;justify-self:end}
 .rbody{padding:4px 14px 18px 14px}
}

/* ---- directory ---- */
.dlegend{grid-template-columns:1fr 118px 168px 44px 128px}
.dirrows{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow)}
.dirrows .row>summary{grid-template-columns:1fr 118px 168px 44px 128px}
.pri{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:7px;
font-size:12.5px;font-weight:700;font-variant-numeric:tabular-nums}
.p1{background:var(--good);color:#fff}
.p2{background:color-mix(in srgb,var(--good) 26%,transparent);color:var(--good)}
.p3{background:var(--alt);color:var(--ink2);border:1px solid var(--line)}
.p4{background:transparent;color:var(--muted);border:1px dashed var(--line)}
.tag.e-confirmed{color:var(--good);border-color:var(--good);background:color-mix(in srgb,var(--good) 10%,transparent)}
.tag.e-conversion{color:var(--warn);border-color:var(--warn);background:color-mix(in srgb,var(--warn) 12%,transparent)}
.tag.e-inferred{color:var(--muted)}
.tag.e-direct{color:var(--muted);border-style:dashed}
.row.ev-confirmed .rn:before{background:var(--good)}
.row.ev-conversion .rn:before{background:var(--warn)}
.row.ev-inferred .rn:before{background:var(--rule)}
.row.ev-direct .rn:before{background:transparent;border-left:3px dashed var(--rule)}

/* ---- playbook ---- */
.callout{border-radius:14px;padding:17px 20px;margin:22px 0;border:1px solid var(--line);background:var(--card);box-shadow:var(--shadow)}
.callout.warn{border-left:3px solid var(--warn);background:color-mix(in srgb,var(--warn) 7%,var(--card))}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin:16px 0 6px}
.pcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px 19px;box-shadow:var(--shadow)}
.pcard h3{margin:0 0 9px;font-size:16px;font-weight:620;display:flex;align-items:center;gap:9px}
.pcard .rule{color:var(--ink);font-weight:520;margin:0 0 8px}
.pcard p{margin:0;color:var(--ink2);font-size:14.5px}
.pcard.ev-confirmed{border-left:3px solid var(--good)}
.pcard.ev-conversion{border-left:3px solid var(--warn)}
.pcard.ev-inferred{border-left:3px solid var(--rule)}
.pcard.ev-direct{border-left:3px dashed var(--rule)}
ol.qs{list-style:none;padding:0;margin:16px 0 0;counter-reset:q}
ol.qs li{display:flex;gap:15px;background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:16px 19px;margin-bottom:10px;box-shadow:var(--shadow)}
.qn{flex:0 0 30px;height:30px;border-radius:9px;background:var(--accent);color:#fff;
display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14.5px}
ol.qs strong{display:block;font-size:16px;font-weight:600;letter-spacing:-.01em;margin-bottom:5px}
ol.qs p{margin:0;color:var(--ink2);font-size:14.5px}
dl.gloss{display:grid;grid-template-columns:180px 1fr;gap:0;background:var(--card);
border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow);margin-top:16px}
dl.gloss dt{padding:14px 16px;font-weight:640;color:var(--ink);font-size:15px;text-transform:none;
letter-spacing:0;border-top:1px solid var(--rule);background:var(--alt)}
dl.gloss dd{padding:14px 18px;margin:0;color:var(--ink2);border-top:1px solid var(--rule);font-size:14.5px}
dl.gloss dt:first-of-type,dl.gloss dd:first-of-type{border-top:0}
@media (max-width:760px){
 .dlegend{display:none}
 .dirrows .row>summary{grid-template-columns:1fr 30px 110px;gap:7px 9px}
 .dirrows .rn{grid-column:1;grid-row:1}
 .dirrows .pri{grid-column:2;grid-row:1;justify-self:end}
 .dirrows .rm{grid-column:1;grid-row:2}
 .dirrows .rw{grid-column:1;grid-row:3}
 .dirrows .row>summary .tag{grid-column:2/4;grid-row:2;justify-self:end}
 dl.gloss{grid-template-columns:1fr}
 dl.gloss dd{padding-top:0;border-top:0}
 dl.gloss dt{border-top:1px solid var(--rule)}
 ol.qs li{padding:14px 15px;gap:12px}
}

footer{margin-top:44px;padding-top:20px;border-top:1px solid var(--rule);
font-size:12.5px;color:var(--muted);line-height:1.65}
.top-link{display:inline-block;margin-top:14px;font-size:13px}

@media (max-width:640px){
 .wrap{padding:0 14px 70px}
 nav.top{margin:0 -14px 20px;padding:9px 14px}
 dl{grid-template-columns:1fr;gap:3px}
 dt{margin-top:14px}
 .card{padding:17px 17px 15px;border-radius:12px}
 table,thead,tbody,tr,th,td{display:block;width:auto!important}
 thead{display:none}
 tr{border-bottom:1px solid var(--rule);padding:6px 0}
 tr:last-child{border-bottom:0}
 th,td{border:0;padding:4px 15px}
 td[data-label]:before{content:attr(data-label);display:block;font-size:10.5px;
 text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:600;margin-top:6px}
 td[data-label=""]:before{display:none}
 th[scope=row]{padding-top:14px;font-size:16.5px}
 td:last-child{padding-bottom:14px}
}
@media print{
 nav.top,.chips,#q{display:none}
 .card,table,ul.plain,.summary,.method{box-shadow:none;break-inside:avoid}
 body{background:#fff}
}
"""

def page(title, body, depth=0, active=""):
    up = "../" * depth
    nav = [("index.html","Opportunities","opps"),("directory.html","Directory","dir"),
           ("playbook.html","Playbook","play"),
           ("shows.html","Shows","shows"),("research.html","Research","res"),
           ("search.html","Search","search")]
    navhtml = "".join('<a href="%s%s"%s>%s</a>' % (up, h, ' class="on"' if k==active else '', l)
                      for h,l,k in nav)
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive,nosnippet">
<title>%s</title><link rel="stylesheet" href="%sassets/style.css"></head>
<body><div class="wrap"><nav class="top">%s</nav>
%s
<footer>
<p>Contact links go to official company pages. No individual names or personal email addresses are listed — ask for the role named on each card.</p>
<p>Material and process detail is marked High confidence only where a primary or trade source confirms it. Medium and Low are inferences from platform type — questions for the first call, not facts to quote.</p>
<p><strong>Unlisted.</strong> This page is excluded from search engines and is not linked from anywhere public &mdash; only people you send the link to can reach it. Treat the link itself as the key.</p>
<p>ROHACELL&reg; is a registered trademark of Evonik. Independent business-development aid compiled from public sources.</p>
</footer></div></body></html>""" % (H.escape(title), up, navhtml, body)

def tags(c):
    sl, cl = STATUS.get(c.get('status','new'), STATUS['new'])
    return ('<div class="tags"><span class="tag score">Fit %d/25</span>'
            '<span class="tag %s">%s</span><span class="tag">%s</span>'
            '<span class="tag">%s</span><span class="tag">%s confidence</span></div>'
            % (c['total'], cl, sl, H.escape(c.get('sector','Aerospace')),
               H.escape(c['segment']), H.escape(c.get('confidence','Low'))))

import urllib.parse as _up

def linkedin_html(c):
    """Verified company page when we have one, otherwise an honest LinkedIn search.
    Plus a people search pre-filled with the role worth asking for."""
    out = []
    if c.get('linkedin'):
        out.append('<a class="li" href="%s">LinkedIn &mdash; company page</a>' % c['linkedin'])
    else:
        q = _up.quote(c['name'])
        out.append('<a class="li" href="https://www.linkedin.com/search/results/companies/?keywords=%s">'
                   'LinkedIn &mdash; find the company</a>' % q)
    roles = c.get('role_keywords') or 'composites materials structures'
    pq = _up.quote('%s %s' % (c['name'], roles))
    out.append('<a class="li" href="https://www.linkedin.com/search/results/people/?keywords=%s">'
               'LinkedIn &mdash; find the right person</a>' % pq)
    return ''.join(out)

def contacts_html(c):
    base = " &nbsp;·&nbsp; ".join('<a href="%s">%s</a>' % (u, l) for l, u in c['contacts'])
    return base + '<div style="margin-top:9px">' + linkedin_html(c) + '</div>' 

def latest_src(c):
    ev = c.get('events') or []
    if not ev: return ""
    return "<br>".join('<a href="%s">%s — %s</a>' % (e['src'], e['date'], H.escape(e['kind']))
                       for e in sorted(ev, key=lambda z: z['date'], reverse=True)[:3])

def card(c, depth=0):
    up = "../" * depth
    return """
<article class="card t%s" data-sector="%s">
  <h3><a href="%scompany/%s.html">%s</a></h3>
  %s
  <div class="bar"><i style="width:%.0f%%"></i></div>
  <dl>
    <dt>What they build</dt><dd>%s</dd>
    <dt>Where</dt><dd>%s</dd>
    <dt>The opportunity</dt><dd class="opp">%s</dd>
    <dt>Who to ask for</dt><dd>%s</dd>
    <dt>Contact</dt><dd>%s</dd>
    <dt>Latest source</dt><dd class="src">%s</dd>
  </dl>
</article>""" % (c['tier'], H.escape(c.get('sector','')), up, c['slug'], H.escape(c['name']), tags(c),
                 c['total'] / 25.0 * 100, c['what'], c['where'],
                 c['opp'], c['ask'], contacts_html(c), latest_src(c))

def row(c, depth=0):
    """One dense, expandable line. Native <details> — no JavaScript needed to open it."""
    up = "../" * depth
    sl, cl = STATUS.get(c.get('status','new'), STATUS['new'])
    return """
<details class="row t%s" data-sector="%s" data-tier="%s" data-status="%s">
  <summary>
    <span class="rn">%s</span>
    <span class="rm">%s</span>
    <span class="rw">%s</span>
    <span class="rbar" title="%d out of 25"><i style="width:%.0f%%"></i></span>
    <span class="rs">%d</span>
    <span class="tag %s">%s</span>
  </summary>
  <div class="rbody">
    <p class="opp">%s</p>
    <dl>
      <dt>What they build</dt><dd>%s</dd>
      <dt>Who to ask for</dt><dd>%s</dd>
      <dt>Materials</dt><dd>%s <em>(%s confidence)</em></dd>
      <dt>Contact</dt><dd>%s</dd>
      <dt>Fit</dt><dd>Structure %d &middot; Process %d &middot; Volume %d &middot; Timing %d &middot; Access %d</dd>
    </dl>
    <p class="more"><a href="%scompany/%s.html">Full page and history &rarr;</a></p>
  </div>
</details>""" % (c['tier'], H.escape(c.get('sector','')), c['tier'], c.get('status','new'),
                 H.escape(c['name']), H.escape(c.get('sector','')), H.escape(c['hq']),
                 c['total'], c['total']/25.0*100, c['total'], cl, sl,
                 c['opp'], c['what'], c['ask'],
                 H.escape(c['materials']), H.escape(c.get('confidence','Low')),
                 contacts_html(c),
                 c['scores']['structure'], c['scores']['process'], c['scores']['volume'],
                 c['scores']['timing'], c['scores']['access'], up, c['slug'])


def build(dbpath, outdir):
    db = json.load(open(dbpath, encoding='utf-8'))
    comps = sorted(db['companies'], key=lambda z: (-z['total'], z['name']))
    _bl = db.get('briefs', [])
    briefs = [b for _, b in sorted(enumerate(_bl), key=lambda t: (t[1]['date'], t[0]), reverse=True)]
    updated = db['meta'].get('updated', datetime.date.today().isoformat())
    for d in ('assets','company','data','_src'):
        os.makedirs(os.path.join(outdir, d), exist_ok=True)
    open(os.path.join(outdir,'assets','style.css'),'w').write(CSS)
    open(os.path.join(outdir,'robots.txt'),'w').write('User-agent: *\nDisallow: /\n')
    open(os.path.join(outdir,'_headers'),'w').write('/*\n  X-Robots-Tag: noindex, nofollow, noarchive\n  Referrer-Policy: no-referrer\n')

    A = [c for c in comps if c['tier']=='A']
    head = ('<h1><b>ROHACELL&reg;</b> qualification &mdash; the opportunity list</h1>'
            '<p class="sub">%d companies across %d markets &middot; Europe &amp; UK &middot; last updated %s</p>'
            % (len(comps), len(db['meta'].get('sectors', [])) or 1, updated))
    topb = briefs[0] if briefs else None
    summ = ('<div class="summary"><p><strong>%d companies tracked. %d worth contacting now.</strong> '
            'Ranking is driven above all by whether a company is choosing materials <em>right now</em> &mdash; '
            'a frozen design is a much harder sell than one six months from first article, however big.</p>'
            '<p><strong>Latest scan (%s):</strong> %s</p></div>'
            % (len(comps), len(A), topb['date'] if topb else '&mdash;',
               H.escape(topb['headline']) if topb else 'No scans yet.'))

    secmap = {}
    for c in comps:
        secmap.setdefault(c.get('sector','Aerospace — UAV & AAM'), []).append(c)

    chips = '<div class="chips" id="chips">'
    chips += '<button class="chip" data-k="all" data-v="all" aria-pressed="true">Everything <span class="cn">%d</span></button>' % len(comps)
    for lab, v in (('Contact now','A'), ('Worth a call','B'), ('Watch only','C')):
        n = len([c for c in comps if c['tier']==v])
        chips += '<button class="chip" data-k="tier" data-v="%s">%s <span class="cn">%d</span></button>' % (v, lab, n)
    chips += '<span class="chipgap"></span>'
    for sname in sorted(secmap, key=lambda k: -max(g['total'] for g in secmap[k])):
        short = sname.split(' — ')[0].split(',')[0]
        chips += ('<button class="chip" data-k="sector" data-v="%s">%s <span class="cn">%d</span></button>'
                  % (H.escape(sname), H.escape(short), len(secmap[sname])))
    chips += '</div>'

    legend = ('<div class="legend"><span>Company</span><span>Market</span>'
              '<span>Where</span><span>Fit</span><span></span><span>Status</span></div>')

    rowhtml = "".join(row(c) for c in comps)

    method = ('<h2>How the fit score works</h2><div class="method">'
      '<p>Five factors, nought to five each, twenty-five maximum. <b>Structure</b> &mdash; sandwich panels, wings, '
      'control surfaces, torsion boxes, monocoque tubs, satellite panels and radomes score high; tubular frames and '
      'multirotor arms score low. <b>Process</b> &mdash; prepreg autoclave or hot oven cure and elevated service '
      'temperature score high, because that is where PMI beats PET, PVC and SAN foam rather than competing on price. '
      '<b>Volume</b> &mdash; programme size and rate. <b>Timing</b> &mdash; is the design still open? '
      '<b>Access</b> &mdash; reachable, and not locked to an incumbent.</p>'
      '<p style="margin-bottom:0">Twenty and above means contact now. Fifteen to nineteen is worth a call. '
      'Below fifteen is watch only. Material detail is marked <b>High</b> confidence only where a trade or primary '
      'source confirms it &mdash; Medium and Low are inferences, so treat them as questions for the first call.</p></div>')

    body = (head + summ
      + '<h2>All targets</h2>'
      + '<p class="note">Everything in one list, best fit first. Tap a row to open it. '
        'See also <a href="research.html">research</a> and '
        '<a href="shows.html">trade shows</a>.</p>'
      + chips + '<p class="count" id="count"></p>' + legend
      + '<div id="rows">' + rowhtml + '</div>'
      + method)
    body += ('<p class="top-link"><a href="#">Back to top</a></p>'
      '<script>(function(){'
      'var chips=[].slice.call(document.querySelectorAll("#chips .chip")),'
      'rows=[].slice.call(document.querySelectorAll("#rows .row")),'
      'cnt=document.getElementById("count");'
      'function show(k,v){var n=0;rows.forEach(function(r){'
      'var ok=(k==="all")||(k==="tier"&&r.dataset.tier===v)||(k==="sector"&&r.dataset.sector===v);'
      'r.style.display=ok?"":"none";r.open=false;if(ok)n++;});'
      'cnt.textContent=n+" of "+rows.length+" shown";}'
      'chips.forEach(function(c){c.addEventListener("click",function(){'
      'chips.forEach(function(o){o.setAttribute("aria-pressed",o===c?"true":"false")});'
      'show(c.dataset.k,c.dataset.v);});});'
      'show("all","all");})();</script>')

    open(os.path.join(outdir,'index.html'),'w').write(page('ROHACELL Qualification Radar', body, 0, 'opps'))

    # company pages
    for c in comps:
        ev = sorted(c.get('events', []), key=lambda z: z['date'], reverse=True)
        tl = "".join('<li><span class="d">%s</span><span class="k">%s</span>'
                     '<div class="t">%s <a href="%s">source</a></div></li>'
                     % (e['date'], H.escape(e['kind']), H.escape(e['text']), e['src']) for e in ev)
        s = c['scores']
        cbody = ('<h1>%s</h1><p class="sub">%s &middot; %s</p>' % (H.escape(c['name']), H.escape(c['hq']), H.escape(c['segment']))
          + tags(c)
          + '<div class="card"><dl>'
          + '<dt>What they build</dt><dd>%s</dd>' % c['what']
          + '<dt>Where</dt><dd>%s</dd>' % c['where']
          + '<dt>Sector</dt><dd>%s</dd>' % H.escape(c.get('sector','Aerospace — UAV & AAM'))
          + '<dt>Stage</dt><dd>%s</dd>' % H.escape(c['stage'])
          + '<dt>The opportunity</dt><dd class="opp">%s</dd>' % c['opp']
          + '<dt>Who to ask for</dt><dd>%s</dd>' % c['ask']
          + '<dt>Materials</dt><dd>%s <em>(%s confidence)</em></dd>' % (H.escape(c['materials']), H.escape(c.get('confidence','Low')))
          + '<dt>Contact</dt><dd>%s</dd>' % contacts_html(c)
          + '<dt>Fit breakdown</dt><dd>Structure %d &middot; Process %d &middot; Volume %d &middot; Timing %d &middot; Access %d &nbsp;=&nbsp; <strong>%d/25</strong></dd>'
            % (s['structure'], s['process'], s['volume'], s['timing'], s['access'], c['total'])
          + '</dl></div>'
          + '<h2>History</h2><ul class="tl">%s</ul>' % tl)
        open(os.path.join(outdir,'company','%s.html' % c['slug']),'w').write(
            page('%s — ROHACELL Radar' % c['name'], cbody, 1, 'opps'))

    # ---------------- DIRECTORY ----------------
    drow = db.get('directory', [])
    EVORD = {'confirmed':0,'conversion':1,'inferred':2,'direct':3}
    drow = sorted(drow, key=lambda d: (str(d.get('priority') or '9'),
                                       EVORD.get(d.get('ev','inferred'),9), d['name']))
    dsecs, dcountries = [], []
    for d in drow:
        if d['sector'] not in dsecs: dsecs.append(d['sector'])
        if d['country'] and d['country'] not in dcountries: dcountries.append(d['country'])
    dchips = ('<div class="chips" id="dchips">'
              '<button class="chip" data-k="all" data-v="all" aria-pressed="true">Everyone <span class="cn">%d</span></button>'
              % len(drow))
    for p in ('1','2','3','4'):
        n = len([x for x in drow if str(x.get('priority'))==p])
        if n: dchips += ('<button class="chip" data-k="pri" data-v="%s">Priority %s <span class="cn">%d</span></button>' % (p,p,n))
    dchips += '<span class="chipgap"></span>'
    for k, lab in (('confirmed','Confirmed'),('conversion','Conversion targets'),('inferred','Inferred'),('direct','Deprioritised')):
        n = len([x for x in drow if x.get('ev')==k])
        if n: dchips += ('<button class="chip" data-k="ev" data-v="%s">%s <span class="cn">%d</span></button>' % (k, lab, n))
    dchips += '<span class="chipgap"></span>'
    for sname in dsecs:
        n = len([x for x in drow if x['sector']==sname])
        dchips += ('<button class="chip" data-k="sec" data-v="%s">%s <span class="cn">%d</span></button>'
                   % (H.escape(sname), H.escape(sname), n))
    dchips += '</div>'

    dbody = ('<h1>Directory &mdash; who&rsquo;s who</h1>'
      '<p class="sub">%d companies across %d countries &middot; priority order</p>'
      '<div class="summary"><p>%s</p></div>'
      % (len(drow), len(dcountries), db.get('directory_note','')))
    dbody += ('<p class="note">New to this? Read the <a href="playbook.html">Playbook</a> first &mdash; '
              'it explains the evidence tags, the priority numbers and the six questions that qualify a lead in two minutes.</p>')
    dbody += dchips + '<p class="count" id="dcount"></p>'
    dbody += ('<div class="legend dlegend"><span>Company</span><span>Sector</span>'
              '<span>Where</span><span>Pri</span><span>Evidence</span></div>')
    dbody += '<div id="rows" class="dirrows">'
    for d in drow:
        cross = ''
        if d.get('slug'):
            cross = ('<dt>Also tracked</dt><dd><a href="company/%s.html">On the scored radar &rarr;</a></dd>' % d['slug'])
        pri = str(d.get('priority') or '—')
        dbody += ("""
<details class="row ev-%s" data-pri="%s" data-ev="%s" data-sec="%s">
  <summary>
    <span class="rn">%s</span>
    <span class="rm">%s</span>
    <span class="rw">%s</span>
    <span class="pri p%s">%s</span>
    <span class="tag e-%s">%s</span>
  </summary>
  <div class="rbody"><dl>
    <dt>What they make</dt><dd>%s</dd>
    <dt>Why ROHACELL fits</dt><dd class="opp">%s</dd>
    <dt>Evidence</dt><dd>%s</dd>
    <dt>Size / type</dt><dd>%s</dd>%s
    <dt>Find them</dt><dd>%s</dd>
  </dl></div>
</details>""" % (d.get('ev','inferred'), pri, d.get('ev','inferred'), H.escape(d['sector']),
                 H.escape(d['name']), H.escape(d['sector']),
                 H.escape((d['location'] or d['country'])[:46]),
                 pri, pri, d.get('ev','inferred'), H.escape(d.get('evlabel','')),
                 H.escape(d['makes']) or '&mdash;', H.escape(d['fit']) or '&mdash;',
                 H.escape(d['evidence']) or '&mdash;', H.escape(d['size']) or '&mdash;', cross,
                 '<a class="li" href="https://www.linkedin.com/search/results/companies/?keywords=%s">LinkedIn</a>'
                 '<a class="li" href="https://duckduckgo.com/?q=%s">Web search</a>'
                 % (_up.quote(d['name']), _up.quote(d['name'] + ' ' + (d['country'] or '')))))
    dbody += '</div>'
    dbody += ('<script>(function(){var ch=[].slice.call(document.querySelectorAll("#dchips .chip")),'
      'rs=[].slice.call(document.querySelectorAll("#rows .row")),c=document.getElementById("dcount");'
      'function go(k,v){var n=0;rs.forEach(function(r){var ok=(k==="all")||(k==="pri"&&r.dataset.pri===v)'
      '||(k==="ev"&&r.dataset.ev===v)||(k==="sec"&&r.dataset.sec===v);'
      'r.style.display=ok?"":"none";r.open=false;if(ok)n++;});c.textContent=n+" of "+rs.length+" shown";}'
      'ch.forEach(function(x){x.addEventListener("click",function(){'
      'ch.forEach(function(o){o.setAttribute("aria-pressed",o===x?"true":"false")});go(x.dataset.k,x.dataset.v);});});'
      'go("all","all");})();</script>')
    open(os.path.join(outdir,'directory.html'),'w').write(
        page('Directory — ROHACELL Radar', dbody, 0, 'dir'))

    # ---------------- PLAYBOOK ----------------
    pb = db.get('playbook', {})
    pbody = ('<h1>Playbook</h1><p class="sub">How to read the list, how to qualify a lead, and what the words mean.</p>'
             '<div class="summary"><p>%s</p></div>' % H.escape(pb.get('intro','')))
    if pb.get('honesty'):
        pbody += ('<div class="callout warn"><strong>The honesty rule.</strong> %s</div>' % pb['honesty'])
    pbody += '<h2>Evidence tags</h2><p class="note">On every directory entry. This is the most important thing on the page.</p><div class="grid2">'
    for e in pb.get('evidence', []):
        pbody += ('<div class="pcard ev-%s"><h3><span class="tag e-%s">%s</span></h3>'
                  '<p class="rule">%s</p><p>%s</p></div>'
                  % (e['key'], e['key'], H.escape(e['label']), H.escape(e['rule']), H.escape(e['do'])))
    pbody += '</div>'
    pbody += '<h2>Priority numbers</h2><div class="grid2">'
    for p in pb.get('priority', []):
        pbody += ('<div class="pcard"><h3><span class="pri p%s">%s</span> %s</h3><p>%s</p></div>'
                  % (p['n'], p['n'], H.escape(p['label']), H.escape(p['text'])))
    pbody += '</div>'
    pbody += ('<h2>Six questions that qualify any lead in two minutes</h2>'
              '<p class="note">Ask these in order. By question three you usually know whether it is real.</p><ol class="qs">')
    for i, q in enumerate(pb.get('questions', []), 1):
        pbody += ('<li><span class="qn">%d</span><div><strong>%s</strong><p>%s</p></div></li>'
                  % (i, H.escape(q['q']), H.escape(q['why'])))
    pbody += '</ol>'
    pbody += ('<h2>Glossary</h2><p class="note">The vocabulary a new starter needs before their first technical call.</p>'
              '<dl class="gloss">')
    for t in pb.get('terms', []):
        pbody += '<dt>%s</dt><dd>%s</dd>' % (H.escape(t['t']), H.escape(t['d']))
    pbody += '</dl>'
    open(os.path.join(outdir,'playbook.html'),'w').write(
        page('Playbook — ROHACELL Radar', pbody, 0, 'play'))

    # trade shows
    shows = sorted(db.get('shows', []), key=lambda x: x.get('date','9999'))
    shbody = ('<h1>Trade shows worth working</h1>'
      '<p class="sub">Nearest first &middot; %d shows across all nine markets</p>'
      '<div class="summary"><p>%s</p></div>' % (len(shows), db.get('shows_note','')))
    if shows:
        shbody += ('<div class="legend shlegend"><span>Show</span><span>When</span>'
                   '<span>Where</span><span>Dates</span></div>')
        shbody += '<div id="rows" class="users">'
        for sh in shows:
            ok = sh.get('confirmed','') == 'Confirmed'
            shbody += ("""
<details class="row %s">
  <summary><span class="rn">%s</span><span class="rm">%s</span><span class="rw">%s</span>
  <span class="tag %s">%s</span></summary>
  <div class="rbody"><p class="opp">%s</p><dl>
  <dt>Markets</dt><dd>%s</dd>
  <dt>What it is</dt><dd>%s</dd>
  <dt>What to do</dt><dd>%s</dd>
  <dt>Links</dt><dd><a href="%s">Organiser</a> &nbsp;&middot;&nbsp; <a href="%s">Exhibitor list</a></dd>
  </dl></div>
</details>""" % ('uhi' if ok else 'umd', H.escape(sh['name']), H.escape(sh['when']),
                 H.escape(sh['where']), 'st-qual' if ok else 'st-watch',
                 H.escape('Confirmed' if ok else 'To confirm'),
                 sh['why'], H.escape(sh.get('markets','')), H.escape(sh['what']),
                 H.escape(sh['todo']), sh['src'], sh['exlist']))
        shbody += '</div>'
    else:
        shbody += '<p class="note">Nothing logged yet.</p>'
    open(os.path.join(outdir,'shows.html'),'w').write(
        page('Trade shows — ROHACELL Radar', shbody, 0, 'shows'))

    # research signals page
    RK = {'Supply news':0,'Paper':1,'Patent':2,'EU project':3,'Research institute':4,
          'Conference':5,'Market report':6}
    res = sorted(db.get('research', []),
                 key=lambda r: (0 if str(r.get('date','')).lower().startswith('hist') else 1,
                                str(r.get('date',''))), reverse=True)
    rkinds = []
    for r in res:
        if r.get('kind','') not in rkinds: rkinds.append(r.get('kind',''))
    rchips = ('<div class="chips" id="rchips"><button class="chip" data-v="all" aria-pressed="true">'
              'Everything <span class="cn">%d</span></button>' % len(res))
    for k in sorted(rkinds, key=lambda k: RK.get(k, 9)):
        rchips += ('<button class="chip" data-v="%s">%s <span class="cn">%d</span></button>'
                   % (H.escape(k), H.escape(k), len([x for x in res if x.get('kind')==k])))
    rchips += '</div>'

    rbody = ('<h1>Research and publications</h1>'
      '<p class="sub">Papers, patents, agency reports, EU projects and supply news &mdash; swept every weekday.</p>'
      '<div class="summary"><p>A company that files a patent or publishes a paper naming ROHACELL has '
      '<strong>already had the material in a lab</strong>. That is a warmer lead than any funding announcement, '
      'and it is invisible to anyone only reading trade press.</p>'
      '<p>Entries marked as a <strong>threat</strong> are logged deliberately &mdash; research that undermines the '
      'PMI case is worth meeting prepared for, not filtering out.</p></div>')
    rbody += rchips + '<p class="count" id="rcount"></p>'
    rbody += ('<div class="legend rlegend"><span>Title</span><span>Type</span><span>Date</span>'
              '<span>Where</span></div>')
    rbody += '<div id="rows" class="users">'
    for r in res:
        link = ''
        if r.get('slug') and r['slug'] in {c['slug'] for c in comps}:
            nm = [c['name'] for c in comps if c['slug'] == r['slug']][0]
            link = ('<dt>Relevant to</dt><dd><a href="company/%s.html">%s</a></dd>'
                    % (r['slug'], H.escape(nm)))
        rbody += ("""
<details class="row" data-kind="%s">
  <summary><span class="rn">%s</span><span class="rm">%s</span>
  <span class="rw">%s</span><span class="rw">%s</span></summary>
  <div class="rbody"><p class="opp">%s</p><dl>
  <dt>Who</dt><dd>%s</dd>
  <dt>What it says</dt><dd>%s</dd>%s
  <dt>Source</dt><dd><a href="%s">%s</a></dd>
  </dl></div>
</details>""" % (H.escape(r.get('kind','')), H.escape(r['title']), H.escape(r.get('kind','')),
                 H.escape(str(r.get('date',''))), H.escape(r.get('country','')),
                 r.get('why',''), H.escape(r.get('org','')), H.escape(r.get('summary','')),
                 link, r['src'], H.escape(r['src'].replace('https://','').split('/')[0])))
    rbody += '</div>'
    rbody += ('<script>(function(){var ch=[].slice.call(document.querySelectorAll("#rchips .chip")),'
      'rs=[].slice.call(document.querySelectorAll("#rows .row")),c=document.getElementById("rcount");'
      'function go(v){var n=0;rs.forEach(function(r){var ok=(v==="all"||r.dataset.kind===v);'
      'r.style.display=ok?"":"none";r.open=false;if(ok)n++;});c.textContent=n+" of "+rs.length+" shown";}'
      'ch.forEach(function(x){x.addEventListener("click",function(){'
      'ch.forEach(function(o){o.setAttribute("aria-pressed",o===x?"true":"false")});go(x.dataset.v);});});'
      'go("all");})();</script>')
    open(os.path.join(outdir,'research.html'),'w').write(
        page('Research and publications — Radar', rbody, 0, 'res'))

    # search index
    idx = []
    for r in res:
        idx.append(dict(t='research', n='%s — %s' % (r['kind'], r['title']),
                        u='research.html', m='%s · %s' % (r.get('date',''), r.get('org','')),
                        x='%s %s' % (r.get('summary',''), r.get('why',''))))
    for c in comps:
        idx.append(dict(t='company', n=c['name'], u='company/%s.html' % c['slug'],
                        m='%s · %s · fit %d/25' % (c['hq'], c['segment'], c['total']),
                        x=' '.join([c.get('sector',''), c['platform'], c['stage'], c['materials'],
                                    strip(c['opp']), c['segment'], c['hq'], STATUS.get(c.get('status','new'),('',''))[0]])))
        for e in c.get('events', []):
            idx.append(dict(t='event', n='%s — %s' % (c['name'], e['kind']), u='company/%s.html' % c['slug'],
                            m=e['date'], x=e['text']))
    for d in drow:
        idx.append(dict(t='directory', n=d['name'], u='directory.html',
                        m='%s · %s · %s' % (d['sector'], d.get('location') or d.get('country',''), d.get('evlabel','')),
                        x='%s %s %s' % (d.get('makes',''), d.get('fit',''), d.get('size',''))))
    for t in db.get('playbook',{}).get('terms',[]):
        idx.append(dict(t='glossary', n=t['t'], u='playbook.html', m='Glossary', x=t['d']))
    for sh in shows:
        idx.append(dict(t='show', n=sh['name'], u='shows.html',
                        m='%s · %s' % (sh['when'], sh['where']),
                        x='%s %s' % (sh.get('what',''), strip(sh.get('why','')))))
    sbody = ('<h1>Search</h1>'
      '<input id="q" type="search" placeholder="Company, country, platform, keyword&hellip;" autofocus>'
      '<p class="hint">Searches every company, every logged event, the directory, research, shows and the glossary. '
      'Try &ldquo;Swindon&rdquo;, &ldquo;autoclave&rdquo;, &ldquo;cargo&rdquo; or &ldquo;Germany&rdquo;.</p>'
      '<div id="r"></div>'
      '<noscript><p class="hint">Search needs JavaScript. Everything is also browsable from '
      '<a href="index.html">Opportunities</a>.</p></noscript>'
      '<script>var IDX=' + json.dumps(idx, ensure_ascii=False) + ';' + SEARCH_JS + '</script>')
    open(os.path.join(outdir,'search.html'),'w').write(page('Search — ROHACELL Radar', sbody, 0, 'search'))

    json.dump(db, open(os.path.join(outdir,'data','companies.json'),'w'), ensure_ascii=False, indent=1)
    shutil.copy(os.path.abspath(__file__), os.path.join(outdir,'_src','build_site.py'))
    print('built %d companies, %d briefs -> %s' % (len(comps), len(briefs), outdir))

def strip(s):
    out=[];skip=False
    for ch in s:
        if ch=='<': skip=True
        elif ch=='>': skip=False
        elif not skip: out.append(ch)
    return ''.join(out)

SEARCH_JS = """
var q=document.getElementById('q'),r=document.getElementById('r');
function esc(s){return String(s).replace(/[&<>]/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[m]})}
function hl(s,t){if(!t)return esc(s);var i=s.toLowerCase().indexOf(t);if(i<0)return esc(s);
 var a=Math.max(0,i-70),b=Math.min(s.length,i+t.length+140);
 return (a>0?'&hellip;':'')+esc(s.slice(a,i))+'<mark>'+esc(s.slice(i,i+t.length))+'</mark>'+esc(s.slice(i+t.length,b))+(b<s.length?'&hellip;':'')}
function go(){var t=q.value.trim().toLowerCase();
 if(!t){r.innerHTML='';return}
 var hits=IDX.filter(function(o){return (o.n+' '+o.m+' '+o.x).toLowerCase().indexOf(t)>-1});
 hits.sort(function(a,b){var A=a.n.toLowerCase().indexOf(t)>-1?0:1,B=b.n.toLowerCase().indexOf(t)>-1?0:1;return A-B});
 if(!hits.length){r.innerHTML='<p class="hint">Nothing matches &ldquo;'+esc(t)+'&rdquo;.</p>';return}
 r.innerHTML='<p class="hint">'+hits.length+' result'+(hits.length==1?'':'s')+'</p>'+hits.slice(0,80).map(function(o){
  return '<div class="hit"><h4><a href="'+o.u+'">'+hl(o.n,t)+'</a></h4>'
   +'<div class="m">'+esc(o.m)+'</div><div class="x">'+hl(o.x,t)+'</div></div>'}).join('')}
q.addEventListener('input',go);
var p=new URLSearchParams(location.search).get('q');if(p){q.value=p;go()}
"""

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv)>1 else 'companies.json',
          sys.argv[2] if len(sys.argv)>2 else 'out')
