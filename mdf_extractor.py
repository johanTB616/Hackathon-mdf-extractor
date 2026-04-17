#!/usr/bin/env python3
"""
MDF Extractor v2 – Coventidor de diccionarios (.docx, .pdf, .txt
MDF (Machine-Readable Dictionary Format) salidas en YAML, JSON o MDF text.

Modo de uso
    python mdf_extractor.py <input_file> [--format yaml|json|mdf] [--output <file>]

Se requiere instalar la libreria de:
    pip install python-docx PyMuPDF pyyaml
"""

import re
import sys
import json
import argparse
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import fitz
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


MDF_FIELDS = [
    "id", "lx", "ps", "sn", "se", "ph", "mr",
    "de", "dn", "ge", "gn",
    "xv", "xe", "xn", "rf",
    "cf", "lf", "lv", "wv", "vd",
    "nt", "et", "sc", "lo", "pc"
]
REPEATABLE = {"xv", "xe", "xn", "rf"}


def read_txt(fp):
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def read_docx(fp):
    if not DOCX_AVAILABLE:
        raise ImportError("Install python-docx: pip install python-docx")
    doc = docx.Document(fp)
    parts = [p.text for p in doc.paragraphs]
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)

def read_pdf(fp):
    if not PDF_AVAILABLE:
        raise ImportError("Install PyMuPDF: pip install PyMuPDF")
    doc = fitz.open(fp)
    text = "".join(page.get_text() for page in doc)
    doc.close()
    return text

def detect_format(text):
    hits = len(re.findall(r'^\\(lx|ps|de|dn|xv|sn)\b', text, re.MULTILINE))
    return "mdf_tagged" if hits >= 3 else "raw"

def new_entry():
    return {f: ([] if f in REPEATABLE else "") for f in MDF_FIELDS}

def parse_mdf_tagged(text):
    entries = []
    current = None
    last_tag = None
    pending_id = None   # \id can appear before \lx

    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r'^\\(\w+)\s*(.*)', line)
        if m:
            tag, value = m.group(1).lower(), m.group(2).strip()

            if tag == "id":
                if current is not None:
                    current["id"] = value
                else:
                    pending_id = value
                last_tag = "id"
                continue

            if tag == "lx":
                if current is not None:
                    entries.append(current)
                current = new_entry()
                current["lx"] = value
                if pending_id is not None:
                    current["id"] = pending_id
                    pending_id = None
                last_tag = "lx"
                continue

            if current is None:
                continue

            if tag in REPEATABLE:
                current[tag].append(value)
            elif tag in MDF_FIELDS:
                current[tag] = value
            last_tag = tag

        elif current and last_tag and line.strip():
            if last_tag in REPEATABLE and current[last_tag]:
                current[last_tag][-1] += " " + line.strip()
            elif last_tag not in REPEATABLE:
                current[last_tag] += " " + line.strip()

    if current is not None:
        entries.append(current)

    auto_id = 1
    for entry in entries:
        if not entry.get("id"):
            entry["id"] = str(auto_id)
        auto_id += 1
        if not entry.get("sn"):
            entry["sn"] = "1"
        for f in REPEATABLE:
            entry[f] = [v for v in entry[f] if v]

    return entries


def parse_raw_dictionary(text):
    entries = []
    blocks = re.split(r'\n{2,}', text.strip())
    eid = 1
    POS_RE = re.compile(
        r'^[\[\(]?(s\.|st\.|n\.|v\.?\d?|vt\.|vi\.|vp\.|adj\.|adv\.|cont\.|prep\.|conj\.|pron\.?)[\]\)]?$',
        re.IGNORECASE
    )
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 2:
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        entry = new_entry()
        entry["id"] = str(eid)
        entry["sn"] = "1"
        entry["lx"] = lines[0]
        rest = lines[1:]
        idx = 0
        if rest and POS_RE.match(rest[0]):
            entry["ps"] = rest[0]
            idx = 1
        def_en, def_es = [], []
        ex_en, ex_es = [], []
        for line in rest[idx:]:
            if re.match(r'^\[.+\]$', line):
                entry["ph"] = line
            elif re.match(r'^(R\.|Nota|Note)', line, re.I):
                entry["nt"] = line
            elif re.search(r'\b(el|la|un|una|de|del|que|se|es|los)\b', line, re.I):
                if len(line) > 30:
                    ex_es.append(line)
                else:
                    def_es.append(line)
            else:
                if len(line) > 30:
                    ex_en.append(line)
                else:
                    def_en.append(line)
        entry["de"] = " ".join(def_en)
        entry["dn"] = " ".join(def_es)
        entry["xe"] = ex_en[:3]
        entry["xn"] = ex_es[:3]
        if entry["lx"]:
            entries.append(entry)
            eid += 1
    return entries


def extract(filepath):
    ext = Path(filepath).suffix.lower()
    if ext == ".txt":
        text = read_txt(filepath)
    elif ext == ".docx":
        text = read_docx(filepath)
    elif ext == ".pdf":
        text = read_pdf(filepath)
    else:
        raise ValueError(f"Unsupported format '{ext}'. Use .txt, .docx, or .pdf")
    fmt = detect_format(text)
    return parse_mdf_tagged(text) if fmt == "mdf_tagged" else parse_raw_dictionary(text)


def entries_to_dicts(entries):
    result = []
    for e in entries:
        clean = {}
        for f in MDF_FIELDS:
            default = [] if f in REPEATABLE else ""
            clean[f] = e.get(f, default) or default
        result.append(clean)
    return result

def to_json(entries, indent=2):
    return json.dumps(entries_to_dicts(entries), ensure_ascii=False, indent=indent)

def to_yaml(entries):
    if not YAML_AVAILABLE:
        raise ImportError("Install PyYAML: pip install pyyaml")
    return yaml.dump(entries_to_dicts(entries), allow_unicode=True,
                     sort_keys=False, default_flow_style=False)

def to_mdf_text(entries):
    lines = []
    for entry in entries:
        for f in MDF_FIELDS:
            if f in REPEATABLE:
                vals = entry.get(f, [])
                for v in (vals or [""]):
                    lines.append(f"\\{f} {v}" if v else f"\\{f} ")
            else:
                v = entry.get(f, "")
                lines.append(f"\\{f} {v}" if v else f"\\{f} ")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="MDF Extractor – Converts .txt/.docx/.pdf dictionaries to structured MDF (YAML/JSON).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mdf_extractor.py dictionary.txt
  python mdf_extractor.py dictionary.pdf --format json --output output.json
  python mdf_extractor.py dictionary.docx --format yaml --output output.yaml
  python mdf_extractor.py dictionary.txt --format mdf --output output.txt
        """
    )
    parser.add_argument("input", help="Input dictionary file (.txt, .docx, or .pdf)")
    parser.add_argument("--format", "-f", choices=["yaml", "json", "mdf"], default="json",
                        help="Output format: yaml, json, or mdf (default: json)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent (default: 2)")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        entries = extract(args.input)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print("Warning: No entries extracted.", file=sys.stderr)
        sys.exit(0)

    try:
        if args.format == "json":
            output = to_json(entries, args.indent)
        elif args.format == "yaml":
            output = to_yaml(entries)
        else:
            output = to_mdf_text(entries)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✓ {len(entries)} entries saved to: {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
