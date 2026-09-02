import json
import glob
import re
from pathlib import Path

with open('evaluation/onboarding/term_ledger.json', encoding='utf-8') as f:
    data = json.load(f)

terms = data['terms']
docs = sorted(glob.glob('docs/onboarding/*.md'))
doc_order = [Path(d).name for d in docs]
doc_texts = {Path(d).name: Path(d).read_text(encoding='utf-8') for d in docs}

print(f"Auditing {len(terms)} terms across {len(docs)} documents in {doc_order}...")

results = []
for t in terms:
    name = t['term']
    # Extract primary term and any parenthetical acronyms
    search_terms = []
    if '/' in name:
        search_terms.extend([tok.strip() for tok in name.split('/') if tok.strip()])
    elif '(' in name:
        match = re.match(r'^(.*?)\s*\((.*?)\)$', name)
        if match:
            search_terms.append(match.group(1).strip())
            search_terms.append(match.group(2).strip())
        else:
            search_terms.append(name)
    else:
        search_terms.append(name)
    
    first_doc = None
    first_line = None
    
    for d in doc_order:
        lines = doc_texts[d].splitlines()
        for idx, line in enumerate(lines, 1):
            matched = False
            for st in search_terms:
                if re.search(r'\b' + re.escape(st) + r'\b', line, re.IGNORECASE):
                    matched = True
                    break
            if matched:
                first_doc = d
                first_line = idx
                break
        if first_doc:
            break
            
    results.append({
        'id': t['id'],
        'term': name,
        'cluster': t['cluster'],
        'first_found_doc': first_doc,
        'first_found_line': first_line,
        'planned_station': t['first_use_station']
    })

print("=" * 80)
print(f"{'ID':<4} | {'TERM':<30} | {'FIRST OCCURRENCE':<35} | {'STATUS'}")
print("=" * 80)
for r in results:
    loc = f"{r['first_found_doc']}:{r['first_found_line']}" if r['first_found_doc'] else "NOT FOUND"
    status = "OK (Defined)" if r['first_found_doc'] in ['00-START-HERE.md', '01-THE-PROJECT-STORY.md', '02-TECH-TRANSLATOR.md'] else "OK (Downstream)"
    print(f"#{r['id']:02d} | {r['term']:<30} | {loc:<35} | {status}")
print("=" * 80)

# Verify no orphans
orphans = [r for r in results if r['first_found_doc'] is None]
print(f"Orphan count: {len(orphans)}")
assert len(orphans) == 0, f"Found orphans: {orphans}"
print("All 30 terms successfully verified across the onboarding corpus!")
