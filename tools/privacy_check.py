#!/usr/bin/env python3
"""Scan a folder for things that should never be in a shareable kit: email addresses, Google Drive/Docs/Sheets IDs,
links to someone's files or artifacts, and any extra terms you list in a private file (one per line; plain text
matches anywhere ignoring case, a line starting with re: is a regular expression).

  python3 tools/privacy_check.py <folder> [private-terms.txt]

Exit code 0 = clean. The private terms file is yours alone: keep it out of anything you share.
"""
import os, re, sys

ALLOWED_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com", "cdn.jsdelivr.net", "www.w3.org",
                 "docs.google.com", "drive.google.com", "claude.ai", "developers.google.com"}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL = re.compile(r"https?://[^\s\"'`<>)\\]+")
# Drive file/folder IDs are 25+ url-safe characters mixing cases and digits
IDLIKE = re.compile(r"(?<![A-Za-z0-9_\-/+=.])[A-Za-z0-9_-]{25,60}(?![A-Za-z0-9_\-/+=])")
LONGNUM = re.compile(r"(?<!\d)\d{15,25}(?!\d)")
SESSION = re.compile(r"\b(trig|session|cse|env|ccpool)_[A-Za-z0-9]{12,}\b")
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def idlike(tok):
    if tok.startswith(("PASTE_", "PENDING", "TESTID")):
        return False
    has = lambda pat: re.search(pat, tok) is not None
    if not (has(r"[a-z]") and has(r"[A-Z]") and has(r"\d")):
        return False
    # words glued with - or _ (CSS classes, identifiers) are not IDs
    parts = re.split(r"[-_]", tok)
    return not all(re.fullmatch(r"[A-Za-z]+\d{0,3}|\d+", p) for p in parts if p)


def scan(root, terms):
    findings = []
    for dirpath, _, files in os.walk(root):
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            data = open(p, "rb").read()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                findings.append((rel, "binary file (review by hand)", ""))
                continue
            low = text.lower()
            for i, t in enumerate(terms):
                if t.startswith("re:"):
                    hit = re.search(t[3:], text) or re.search(t[3:], rel)
                else:
                    hit = t.lower() in low or t.lower() in rel.lower()
                if hit:
                    findings.append((rel, "private term", "#%d" % (i + 1)))
            for m in EMAIL.finditer(text):
                if not m.group(0).lower().endswith("@example.com"):
                    findings.append((rel, "email address", m.group(0)))
            for m in URL.finditer(text):
                u = m.group(0)
                host = re.sub(r"^https?://", "", u).split("/")[0].split(":")[0].lower()
                if host not in ALLOWED_HOSTS:
                    findings.append((rel, "link to an unexpected host", u[:80]))
                elif host in ("docs.google.com", "drive.google.com", "claude.ai") and re.search(r"/(d|folders|artifact|chat|code)/[A-Za-z0-9_-]{12,}", u) and "EXAMPLEONLY" not in u:
                    findings.append((rel, "link to a specific file or artifact", u[:100]))
            for m in IDLIKE.finditer(text):
                if idlike(m.group(0)):
                    findings.append((rel, "looks like a Google file ID", m.group(0)))
            for pat, why in ((LONGNUM, "long account-style number"), (SESSION, "session or task identifier"), (UUID, "uuid")):
                for m in pat.finditer(text):
                    findings.append((rel, why, m.group(0)))
    return findings


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    terms = []
    if len(sys.argv) > 2:
        terms = [l.strip() for l in open(sys.argv[2], encoding="utf-8") if l.strip() and not l.startswith("#")]
    f = scan(sys.argv[1], terms)
    n = sum(len(fs) for _, _, fs in os.walk(sys.argv[1]))
    for rel, why, what in f:
        print(f"{rel}: {why}: {what}")
    print(f"{n} files scanned, {len(terms)} private terms, {len(f)} finding(s)")
    sys.exit(1 if f else 0)


if __name__ == "__main__":
    main()
