import argparse
import html
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from tempfile import TemporaryDirectory


RISK_CLASS = {"高": "high", "中": "mid", "低": "low"}
RISK_EN = {"高": "High", "中": "Medium", "低": "Low"}
TYPE_CLASS = {"漏洞": "gap", "差距": "diff", "冲突": "conflict", "重复控制": "repeat", "过度控制": "over", "责任缺口": "owner", "证据缺口": "evidence"}
TYPE_EN = {"漏洞": "Loophole", "差距": "Gap", "冲突": "Conflict", "重复控制": "Duplicate control", "过度控制": "Excessive control", "责任缺口": "Accountability gap", "证据缺口": "Evidence gap"}

CSS = r"""
:root{--ink:#20264b;--muted:#77809c;--line:#e3e7f3;--soft:#f6f7fc;--navy:#26345f;--accent:#4d6bfe;--high:#d95368;--mid:#b57a12;--low:#3c9670}
*{box-sizing:border-box}[hidden]{display:none!important}body{margin:0;background:radial-gradient(circle at 8% 0%,#e4eaff 0,transparent 34%),radial-gradient(circle at 92% 18%,#edf7f2 0,transparent 32%),linear-gradient(145deg,#f5f7ff 0%,#f8f9fd 52%,#eef3fb 100%);color:var(--ink);font:14px/1.7 Arial,"Microsoft YaHei",sans-serif}button,input,select{font:inherit}button{cursor:pointer}.lang-en{display:none}html[lang="en"] .lang-en{display:inline}html[lang="en"] .lang-zh{display:none}.page{max-width:1240px;margin:auto;padding:34px 26px 48px}.hero{padding:30px 32px;color:var(--ink);background:rgba(255,255,255,.82);border:1px solid rgba(255,255,255,.95);border-radius:24px;box-shadow:0 18px 46px rgba(69,83,150,.09);backdrop-filter:blur(12px)}.hero-top{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}.eyebrow{margin-bottom:7px;color:var(--accent);font-size:11px;font-weight:700;letter-spacing:.16em}.hero h1{margin:0;font-size:29px;letter-spacing:-.02em}.hero p{margin:9px 0 0;color:var(--muted)}.lang-switch{display:flex;flex:none;padding:4px;background:#eef1fb;border:1px solid #e0e5f5;border-radius:11px}.lang-switch button{padding:6px 12px;color:var(--muted);background:transparent;border:0;border-radius:8px}.lang-switch button[aria-pressed="true"]{color:#fff;background:var(--accent);font-weight:700;box-shadow:0 4px 12px rgba(77,107,254,.22)}.summary{display:flex;flex-wrap:wrap;gap:25px;margin:14px 0;padding:14px 24px;color:var(--muted);background:rgba(255,255,255,.65);border:1px solid rgba(255,255,255,.9);border-radius:17px;font-size:13px}.summary strong{margin-right:6px;color:var(--accent);font-size:20px}.workspace{overflow:hidden;background:rgba(255,255,255,.9);border:1px solid rgba(255,255,255,.95);border-radius:24px;box-shadow:0 20px 50px rgba(69,83,150,.09);backdrop-filter:blur(10px)}.toolbar{display:flex;flex-wrap:wrap;gap:10px;padding:17px 20px;border-bottom:1px solid var(--line);background:rgba(250,251,255,.9)}.search-wrap{position:relative;flex:1 1 280px}.search-wrap::before{content:"⌕";position:absolute;left:12px;top:4px;color:var(--muted);font-size:22px}#search{width:100%;padding:10px 38px;color:var(--ink);background:#fff;border:1px solid #dfe4f1;border-radius:10px;outline:none}#search:focus{border-color:#aebdfd;box-shadow:0 0 0 3px rgba(77,107,254,.08)}#clear-search{position:absolute;right:7px;top:7px;padding:4px 7px;color:var(--muted);background:transparent;border:0}.toolbar select,.tool-btn{padding:10px 12px;color:var(--navy);background:#fff;border:1px solid #dfe4f1;border-radius:10px}.tool-btn:hover,.toolbar select:hover{border-color:#b9c5f8;background:#f7f8ff}.tool-btn#expand-all{color:#fff;background:var(--accent);border-color:var(--accent);box-shadow:0 5px 14px rgba(77,107,254,.2)}.file-tabs{display:flex;padding:0 20px;border-bottom:1px solid var(--line);overflow-x:auto;background:rgba(255,255,255,.55)}.file-tab{padding:15px 17px 13px;color:var(--muted);background:transparent;border:0;border-bottom:3px solid transparent;white-space:nowrap}.file-tab[aria-selected="true"]{color:var(--accent);border-bottom-color:var(--accent);font-weight:700}.file-panel{padding:22px}.file-heading{display:flex;gap:12px;align-items:flex-start;margin-bottom:20px}.file-icon{display:grid;place-items:center;width:38px;height:38px;color:var(--accent);background:#eaf0ff;border-radius:11px}.file-heading h2{margin:0;font-size:18px;overflow-wrap:anywhere}.file-heading p{margin:2px 0 0;color:var(--muted);font-size:12px}.area-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin:18px 0 12px;padding-bottom:10px;border-bottom:1px solid var(--line)}.area-heading h3{margin:0;font-size:18px}.area-heading p{margin:0;max-width:560px;color:var(--muted);font-size:12px;text-align:right}.area-kicker{color:var(--accent);font-size:10px;font-weight:700;letter-spacing:.13em}.gap-heading{margin-top:30px;padding-top:18px;border-top:3px solid #dbe3ff}.record{margin:0 0 13px;background:#fff;border:1px solid #e6eaf4;border-radius:15px;box-shadow:0 4px 14px rgba(52,65,120,.035)}.record.open{border-color:#c6d1fc;box-shadow:0 9px 24px rgba(77,107,254,.08)}.record-toggle{display:grid;grid-template-columns:24px minmax(0,1fr) auto;gap:10px;align-items:start;width:100%;padding:16px;text-align:left;color:var(--ink);background:transparent;border:0;border-radius:15px}.record-toggle:hover{background:#fafbff}.chevron{margin-top:4px;color:var(--accent);transition:transform .15s}.record.open .chevron{transform:rotate(90deg)}.badges{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin-bottom:7px}.risk-badge,.type-badge{padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700}.risk-badge.high{color:#a93549;background:#fdecef}.risk-badge.mid{color:#855b0c;background:#fff3d8}.risk-badge.low{color:#287454;background:#e4f4ec}.type-badge.conflict{color:#7150a5;background:#f0e9fa}.type-badge.diff{color:#486899;background:#e8effa}.type-badge.gap{color:#a93549;background:#fdecef}.type-badge.repeat{color:#287e8c;background:#e5f4f5}.type-badge.over{color:#95600b;background:#fff0dd}.type-badge.owner{color:#806051;background:#f2e9e5}.type-badge.evidence{color:#5e6c81;background:#eaf0f5}.clause-number{color:var(--navy);font-weight:700}.internal-text{display:block;color:#4d5975;font-size:13px;overflow-wrap:anywhere}.count{padding:3px 10px;color:var(--accent);background:#edf1ff;border-radius:999px;font-size:11px;white-space:nowrap}.detail{padding:0 16px 16px 50px}.detail-section{margin:0 0 12px;padding:14px 15px;background:#f7f8fc;border:1px solid #e8ebf4;border-radius:12px}.detail-section h4{display:flex;align-items:center;gap:8px;margin:0 0 11px;color:var(--navy);font-size:14px}.step{display:grid;place-items:center;width:25px;height:25px;color:#fff;background:var(--accent);border-radius:50%;font-size:10px;box-shadow:0 3px 8px rgba(77,107,254,.18)}.internal-card{margin:0 0 9px;padding:13px;background:#fff;border:1px solid #e5e9f3;border-radius:10px;overflow-wrap:anywhere}.internal-file{color:var(--navy);font-weight:700}.internal-clause{margin:2px 0 6px;color:var(--accent);font-size:12px}.external-text,.long-text{color:#43506d;font-size:13px;overflow-wrap:anywhere}.risk-summary{margin:0 0 11px;padding:11px 12px;color:#7c3b49;background:#fff3f5;border-left:3px solid var(--high);border-radius:0 8px 8px 0;font-size:13px}.advice{background:#f0f8f4;border-color:#d7ede1}.advice h4{color:#2f6f53}.external-standalone{padding:11px 12px;background:#fff;border:1px solid #e5e9f3;border-radius:9px}.gap-record{background:#fdfdfe}.empty{padding:20px;color:var(--muted);text-align:center;background:#f7f8fc;border-radius:12px}.result-line{padding:0 22px 13px;color:var(--muted);font-size:12px}.no-result{margin:12px 20px 20px;padding:20px;text-align:center;color:var(--muted);background:#f7f8fc;border-radius:12px}.footnote{margin:16px 2px 0;color:var(--muted);font-size:12px}
@media(max-width:700px){.page{padding:16px 10px 30px}.hero{padding:22px;border-radius:19px}.hero-top{display:block}.lang-switch{width:max-content;margin-top:15px}.hero h1{font-size:24px}.file-panel{padding:12px}.area-heading{display:block}.area-heading p{margin-top:5px;text-align:left}.record-toggle{grid-template-columns:21px minmax(0,1fr)}.count{grid-column:2;justify-self:start}.detail{padding-left:25px;padding-right:10px}}
@media print{body{background:#fff}.page{max-width:none;padding:0}.hero{color:#000;background:#fff;border:0;border-bottom:2px solid #000;box-shadow:none}.hero p,.eyebrow,.summary{color:#333}.summary{background:#fff}.summary strong{color:#000}.workspace{border:0;box-shadow:none}.toolbar,.file-tabs,.result-line,.no-result,.lang-switch{display:none!important}.file-panel[hidden],.record[hidden],.detail[hidden]{display:block!important}.record{break-inside:avoid}.file-panel{padding:10px 0}}
"""

JS = r"""
const tabs=[...document.querySelectorAll('.file-tab')],panels=[...document.querySelectorAll('.file-panel')],search=document.getElementById('search'),risk=document.getElementById('risk-filter'),type=document.getElementById('type-filter'),line=document.getElementById('result-line'),empty=document.getElementById('no-result');let currentLang='zh-CN';
function setRecord(record,open){const button=record.querySelector('.record-toggle'),detail=record.querySelector('.detail');record.classList.toggle('open',open);button.setAttribute('aria-expanded',String(open));detail.hidden=!open;}
document.querySelectorAll('.record').forEach(record=>{const button=record.querySelector('.record-toggle');setRecord(record,record.dataset.open==='true');button.addEventListener('click',()=>setRecord(record,button.getAttribute('aria-expanded')!=='true'));});
function activePanel(){return panels.find(panel=>!panel.hidden);}
function applyFilters(){const query=search.value.trim().toLowerCase();let shown=0,total=0;activePanel().querySelectorAll('.record').forEach(record=>{total++;const types=record.dataset.type.split(' ');const match=(!query||record.textContent.toLowerCase().includes(query))&&(!risk.value||record.dataset.risk===risk.value)&&(!type.value||types.includes(type.value));record.hidden=!match;if(match){shown++;if(query)setRecord(record,true);}});line.textContent=(query||risk.value||type.value)?(currentLang==='en'?`Showing ${shown} of ${total} records in this external regulation`:`当前外规显示 ${shown}／${total} 条记录`):'';empty.hidden=shown!==0;}
tabs.forEach(tab=>tab.addEventListener('click',()=>{tabs.forEach(item=>item.setAttribute('aria-selected',String(item===tab)));panels.forEach(panel=>panel.hidden=panel.dataset.panel!==tab.dataset.file);applyFilters();window.scrollTo({top:0,behavior:'smooth'});}));
document.getElementById('expand-all').addEventListener('click',()=>activePanel().querySelectorAll('.record').forEach(record=>setRecord(record,true)));
document.getElementById('collapse-all').addEventListener('click',()=>activePanel().querySelectorAll('.record').forEach(record=>setRecord(record,false)));
search.addEventListener('input',applyFilters);risk.addEventListener('input',applyFilters);type.addEventListener('input',applyFilters);
document.getElementById('clear-search').addEventListener('click',()=>{search.value='';applyFilters();search.focus();});
document.getElementById('clear').addEventListener('click',()=>{search.value='';risk.value='';type.value='';applyFilters();});
function setLanguage(lang){currentLang=lang;document.documentElement.lang=lang;document.title=lang==='en'?'External Regulation Internalization Review':'外规内化审查结果';search.placeholder=lang==='en'?'Search clauses, internal policies, differences or recommendations':'搜索当前外规的条款、内规、差异或建议';document.querySelectorAll('option[data-zh]').forEach(option=>option.textContent=lang==='en'?option.dataset.en:option.dataset.zh);document.querySelectorAll('[data-lang]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.lang===lang)));applyFilters();}
document.querySelectorAll('[data-lang]').forEach(button=>button.addEventListener('click',()=>setLanguage(button.dataset.lang)));
window.addEventListener('beforeprint',()=>document.querySelectorAll('.record').forEach(record=>setRecord(record,true)));
"""


def text(value):
    if value is None:
        return ""
    return html.escape(str(value), quote=True).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def dual(zh, en=None):
    english = en if en not in (None, "") else zh
    return f'<span class="lang-zh">{text(zh)}</span><span class="lang-en">{text(english)}</span>'


def field(item, name):
    return str(item.get(name) or ""), str(item.get(name + "_en") or "")


def risk_level(item):
    level = str(item.get("风险等级") or "").strip()
    if level.endswith("风险"):
        level = level[:-2]
    return level if level in RISK_CLASS else ""


def read_findings(path):
    spec = {"title": path.stem, "forward": [], "reverse": []}
    try:
        records = path.open("rb")
    except OSError as error:
        print(f"无法读取 {path.name}：{error}。其他内规继续导出。", file=sys.stderr)
        return spec
    with records:
        for line_number, line in enumerate(records, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line.decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                print(f"{path.name} 第 {line_number} 行无法读取，请补写这一行。其他行继续导出。", file=sys.stderr)
                continue
            if not isinstance(item, dict):
                print(f"{path.name} 第 {line_number} 行应填写一个问题。其他行继续导出。", file=sys.stderr)
                continue
            if item.get("区域") == "制度级缺口":
                spec["reverse"].append(item)
            else:
                spec["forward"].append(item)
    return spec


def external_groups(value):
    raw = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", raw) if part.strip()]
    if len(paragraphs) > 1:
        return [[line for line in part.split("\n") if line.strip()] for part in paragraphs]
    groups, current = [], []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        if "｜" in line and current:
            groups.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        groups.append(current)
    return groups


def parse_reference(lines):
    if not lines:
        return "", "", ""
    if "｜" in lines[0]:
        filename, clause = lines[0].split("｜", 1)
    else:
        filename, clause = "关联外规", lines[0]
    return filename.strip(), clause.strip(), "\n".join(lines[1:])


def references(item):
    groups = external_groups(item.get("外规依据"))
    english_groups = external_groups(item.get("外规依据_en"))
    if not groups:
        return [("未填写外规文件", "External file not provided", "未填写外规条款", "External clause not provided", "本条记录未填写外规依据。", "External basis not provided.")]
    result = []
    for index, lines in enumerate(groups):
        filename, clause, body = parse_reference(lines)
        en_filename, en_clause, en_body = filename, clause, body
        if len(english_groups) == len(groups):
            en_filename, en_clause, en_body = parse_reference(english_groups[index])
        result.append((filename, en_filename, clause, en_clause, body, en_body))
    return result


def build_external(data):
    files = OrderedDict()
    for spec in data:
        for item in spec["forward"]:
            if not risk_level(item):
                continue
            for filename, en_filename, clause, en_clause, body, en_body in references(item):
                file_key = filename
                file_spec = files.setdefault(file_key, {"title": filename, "title_en": en_filename, "clauses": OrderedDict(), "gaps": []})
                clause_key = (clause, body)
                clause_spec = file_spec["clauses"].setdefault(clause_key, {"clause": clause, "clause_en": en_clause, "body": body, "body_en": en_body, "items": []})
                clause_spec["items"].append({"internal": spec["title"], "item": item})
        for item in spec["reverse"]:
            if not risk_level(item):
                continue
            filename, en_filename = field(item, "外规文件名")
            clause, en_clause = field(item, "外规条款号")
            body, en_body = field(item, "外规正文")
            filename = filename or "未填写外规文件"
            file_key = filename
            file_spec = files.setdefault(file_key, {"title": filename, "title_en": en_filename or filename, "clauses": OrderedDict(), "gaps": []})
            file_spec["gaps"].append({"internal": spec["title"], "item": item, "clause": clause, "clause_en": en_clause, "body": body, "body_en": en_body})
    return list(files.values())


def badges(items):
    levels = [risk_level(entry["item"]) for entry in items]
    level = next((candidate for candidate in ("高", "中", "低") if candidate in levels), "中")
    types = list(dict.fromkeys(str(entry["item"].get("差异类型") or "") for entry in items))
    result = [f'<span class="risk-badge {RISK_CLASS[level]}">{dual(level + "风险", RISK_EN[level] + " risk")}</span>']
    for kind in types:
        result.append(f'<span class="type-badge {TYPE_CLASS.get(kind, "diff")}">{dual(kind, TYPE_EN.get(kind, kind))}</span>')
    return level, types, "".join(result)


def render_clause_group(group, opened):
    level, types, badge_html = badges(group["items"])
    records = []
    for entry in group["items"]:
        item = entry["item"]
        summary, summary_en = field(item, "风险简述")
        clause_number, clause_number_en = field(item, "内规条款号")
        internal, internal_en = field(item, "内规正文")
        difference, difference_en = field(item, "具体差异")
        advice, advice_en = field(item, "修改建议")
        kind = str(item.get("差异类型") or "")
        records.append(f'''<section class="detail-section"><h4><span class="step">01</span>{dual("相关内规", "Related internal policy")}</h4><div class="internal-card"><div class="internal-file">{text(entry["internal"])}</div><div class="internal-clause">{dual(clause_number, clause_number_en)}</div><div class="long-text">{dual(internal, internal_en)}</div></div></section>
<section class="detail-section reason"><h4><span class="step">02</span>{dual("风险／" + kind + "原因", "Risk / " + TYPE_EN.get(kind, kind) + " reason")}</h4><div class="risk-summary">{dual(summary, summary_en)}</div><div class="long-text">{dual(difference, difference_en)}</div></section>
<section class="detail-section advice"><h4><span class="step">03</span>{dual("改进意见", "Recommendations")}</h4><div class="long-text">{dual(advice, advice_en)}</div></section>''')
    open_text = "true" if opened else "false"
    hidden = "" if opened else " hidden"
    count = len(group["items"])
    return f'''<article class="record clause risk-{RISK_CLASS[level]}" data-risk="{level}" data-type="{text(" ".join(types))}" data-open="{open_text}"><button class="record-toggle" type="button" aria-expanded="{open_text}"><span class="chevron">▶</span><span class="record-main"><span class="badges">{badge_html}<span class="clause-number">{dual(group["clause"], group["clause_en"])}</span></span><span class="internal-text">{dual(group["body"], group["body_en"])}</span></span><span class="count">{dual(str(count) + " 项内规记录", str(count) + " internal records")}</span></button><div class="detail"{hidden}>{"".join(records)}</div></article>'''


def render_gap(entry):
    item = entry["item"]
    level = risk_level(item)
    kind = str(item.get("差异类型") or "")
    analysis, analysis_en = field(item, "缺失分析")
    return f'''<article class="record gap-record risk-{RISK_CLASS[level]}" data-risk="{level}" data-type="{text(kind)}" data-open="false"><button class="record-toggle" type="button" aria-expanded="false"><span class="chevron">▶</span><span class="record-main"><span class="badges"><span class="risk-badge {RISK_CLASS[level]}">{dual(level + "风险", RISK_EN[level] + " risk")}</span><span class="type-badge {TYPE_CLASS.get(kind, "diff")}">{dual(kind, TYPE_EN.get(kind, kind))}</span><span class="clause-number">{dual(entry["clause"], entry["clause_en"])}</span></span><span class="internal-text">{dual(entry["body"], entry["body_en"])}</span></span><span class="count">{dual("未有效承接", "No effective coverage")}</span></button><div class="detail" hidden><section class="detail-section"><h4><span class="step">01</span>{dual("主承接内规", "Primary internal policy")}</h4><div class="internal-card"><div class="internal-file">{text(entry["internal"])}</div></div></section><section class="detail-section reason"><h4><span class="step">02</span>{dual("缺失分析", "Gap analysis")}</h4><div class="long-text">{dual(analysis, analysis_en)}</div></section></div></article>'''


def render_sheet(spec, index):
    groups = list(spec["clauses"].values())
    cards = "".join(render_clause_group(group, index == 1 and row == 1) for row, group in enumerate(groups, 1))
    cards += "".join(render_gap(entry) for entry in spec["gaps"])
    if not cards:
        cards = f'<div class="empty">{dual("暂无记录", "No records")}</div>'
    hidden = "" if index == 1 else " hidden"
    card_count = len(groups) + len(spec["gaps"])
    return f'''<section class="file-panel" data-panel="sheet{index}"{hidden}><div class="file-heading"><span class="file-icon">▤</span><div><h2>{dual(spec["title"], spec["title_en"])}</h2><p>{dual(f"{card_count} 张外规条款卡片", f"{card_count} external clause cards")}</p></div></div><div class="area-heading"><div><span class="area-kicker">EXTERNAL CLAUSES</span><h3>{dual("外规条款映射", "External clause mapping")}</h3></div><p>{dual("逐条展开相关内规、差异原因、改进意见或缺失分析。", "Expand each clause for related internal policies, reasons, recommendations or gap analysis.")}</p></div>{cards}</section>'''


def write_report(data, destination):
    external = build_external(data)
    if not external:
        external = [{"title": "外规审查结果", "title_en": "External regulation review", "clauses": OrderedDict(), "gaps": []}]
    tabs = "".join(f'<button class="file-tab" type="button" data-file="sheet{index}" aria-selected="{str(index == 1).lower()}">{dual(spec["title"], spec["title_en"])}</button>' for index, spec in enumerate(external, 1))
    sheets = "".join(render_sheet(spec, index) for index, spec in enumerate(external, 1))
    forward_count = sum(1 for spec in data for item in spec["forward"] if risk_level(item))
    reverse_count = sum(1 for spec in data for item in spec["reverse"] if risk_level(item))
    clause_count = sum(len(spec["clauses"]) + len(spec["gaps"]) for spec in external)
    risk_options = "".join(f'<option value="{level}" data-zh="{level}" data-en="{RISK_EN[level]}">{level}</option>' for level in ("高", "中", "低"))
    type_options = "".join(f'<option value="{kind}" data-zh="{kind}" data-en="{TYPE_EN[kind]}">{kind}</option>' for kind in TYPE_EN)
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>外规内化审查结果</title><style>{CSS}</style></head><body><main class="page"><header class="hero"><div class="hero-top"><div><div class="eyebrow">REGULATORY MAPPING</div><h1>{dual("外规内化审查报告", "Regulatory Internalization Review")}</h1></div><div class="lang-switch" aria-label="Language"><button type="button" data-lang="zh-CN" aria-pressed="true">中文</button><button type="button" data-lang="en" aria-pressed="false">English</button></div></div><p>{dual("外规条款为根节点 · 相关内规 → 差异原因 → 改进意见", "External clauses as root nodes · Internal policies → Reasons → Recommendations")}</p></header><div class="summary"><span><strong>{len(external)}</strong>{dual("份外规文件", "external files")}</span><span><strong>{clause_count}</strong>{dual("张外规卡片", "external clause cards")}</span><span><strong>{forward_count + reverse_count}</strong>{dual("条问题记录", "issue records")}</span></div><section class="workspace"><div class="toolbar"><div class="search-wrap"><input id="search" type="search" placeholder="搜索当前外规的条款、内规、差异或建议" aria-label="Search"><button id="clear-search" type="button" aria-label="Clear search">×</button></div><select id="risk-filter" aria-label="Risk"><option value="" data-zh="全部风险等级" data-en="All risk levels">全部风险等级</option>{risk_options}</select><select id="type-filter" aria-label="Difference type"><option value="" data-zh="全部差异类型" data-en="All difference types">全部差异类型</option>{type_options}</select><button class="tool-btn" id="expand-all" type="button">{dual("全部展开", "Expand all")}</button><button class="tool-btn" id="collapse-all" type="button">{dual("全部收起", "Collapse all")}</button><button class="tool-btn" id="clear" type="button">{dual("清除筛选", "Clear filters")}</button></div><nav class="file-tabs" aria-label="External regulations">{tabs}</nav>{sheets}<div class="result-line" id="result-line" aria-live="polite"></div><div class="no-result" id="no-result" hidden>{dual("当前筛选条件下没有记录。", "No records match the current filters.")}</div></section><p class="footnote">{dual("仅改变展示层级，原问题记录及全部分析字段完整保留；支持中英文界面切换。", "Only the presentation hierarchy changes; every source record and analytical field is retained. Chinese and English interfaces are supported.")}</p></main><script>{JS}</script></body></html>'''
    target = Path(destination).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".review-html-", dir=target.parent) as folder:
        staged = Path(folder) / target.name
        staged.write_text(document, encoding="utf-8", newline="\n")
        staged.replace(target)


def main():
    parser = argparse.ArgumentParser(description="把风险记录写成独立外规树形 HTML，每份外规一个页签")
    parser.add_argument("inputs", nargs="+", type=Path, help="按内规命名的 JSONL 文件")
    parser.add_argument("-o", "--output", type=Path, required=True, help="结果 .html 路径")
    args = parser.parse_args()
    write_report([read_findings(path) for path in args.inputs], args.output)
    print(f"已写入 {args.output}")


if __name__ == "__main__":
    main()
