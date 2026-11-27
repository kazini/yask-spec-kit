"""Parser for the flat YAML subset used by manifests, config and front matter:
block mappings, block lists, inline lists and maps, quoted strings, `|` blocks, comments."""
import re

_NUM = re.compile(r"^-?\d+(\.\d+)?$")


def _strip_comment(line):
    q = None
    for i, c in enumerate(line):
        if q:
            if c == q:
                q = None
        elif c in "\"'" and (i == 0 or line[:i].rstrip()[-1:] in (":", "[", "{", ",", "-", "")):
            q = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def _scalar(s):
    s = s.strip()
    if s == "":
        return None
    if s[0] == '"' and s[-1] == '"' and len(s) > 1:
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if s[0] == "'" and s[-1] == "'" and len(s) > 1:
        return s[1:-1].replace("''", "'")
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s in ("null", "~", "Null"):
        return None
    if _NUM.match(s):
        return float(s) if "." in s else int(s)
    return s


def _flow(s, i=0):
    """Parse one flow value starting at s[i]; return (value, next_index)."""
    n = len(s)
    while i < n and s[i] in " \t":
        i += 1
    if i >= n:
        return None, i
    if s[i] == "[":
        out, i = [], i + 1
        while True:
            while i < n and s[i] in " \t,":
                i += 1
            if i >= n or s[i] == "]":
                return out, i + 1
            v, i = _flow(s, i)
            out.append(v)
    if s[i] == "{":
        out, i = {}, i + 1
        while True:
            while i < n and s[i] in " \t,":
                i += 1
            if i >= n or s[i] == "}":
                return out, i + 1
            j = i
            if s[j] in "\"'":
                k, _ = _quoted(s, j)
                key = _scalar(s[j:k])
                i = k
            else:
                while i < n and s[i] != ":":
                    i += 1
                key = s[j:i].strip()
            i += 1  # ':'
            v, i = _flow(s, i)
            out[key] = v
    if s[i] in "\"'":
        k, _ = _quoted(s, i)
        return _scalar(s[i:k]), k
    j = i
    while i < n and s[i] not in ",]}":
        i += 1
    return _scalar(s[j:i]), i


def _quoted(s, i):
    q = s[i]
    j = i + 1
    while j < len(s):
        if s[j] == "\\" and q == '"':
            j += 2
            continue
        if s[j] == q:
            if q == "'" and j + 1 < len(s) and s[j + 1] == "'":
                j += 2
                continue
            return j + 1, q
        j += 1
    return len(s), q


def _value(rest):
    rest = rest.strip()
    if rest[:1] in "[{":
        return _flow(rest)[0]
    return _scalar(rest)


def loads(text):
    raw = text.split("\n")
    pos = [0]

    def peek():
        """Next meaningful line as (index, indent, stripped-comment text) or None."""
        i = pos[0]
        while i < len(raw):
            t = _strip_comment(raw[i])
            if t.strip():
                return i, len(raw[i]) - len(raw[i].lstrip(" ")), t.strip()
            i += 1
        return None

    def block(min_indent):
        p = peek()
        if p is None or p[1] < min_indent:
            return None
        return (lst if p[2].startswith("- ") or p[2] == "-" else mp)(p[1])

    def lst(ind):
        out = []
        while True:
            p = peek()
            if p is None or p[1] != ind or not (p[2].startswith("- ") or p[2] == "-"):
                return out
            pos[0] = p[0] + 1
            rest = p[2][1:].strip()
            out.append(_value(rest) if rest else block(ind + 1))

    def mp(ind):
        out = {}
        while True:
            p = peek()
            if p is None or p[1] != ind or p[2].startswith("- "):
                return out
            i, _, t = p
            m = re.match(r'^("[^"]*"|\'[^\']*\'|[^:]+?):(?:\s+(.*))?$', t)
            if not m:
                raise ValueError(f"line {i + 1}: cannot parse {t!r}")
            key = _scalar(m.group(1)) if m.group(1)[0] in "\"'" else m.group(1).strip()
            rest = (m.group(2) or "").strip()
            pos[0] = i + 1
            if rest in ("|", ">", "|-", ">-"):
                lines = []
                while pos[0] < len(raw):
                    ln = raw[pos[0]]
                    if ln.strip() and len(ln) - len(ln.lstrip(" ")) <= ind:
                        break
                    lines.append(ln[ind + 2:] if ln.strip() else "")
                    pos[0] += 1
                out[key] = ("\n".join(lines).rstrip() + "\n") if rest[0] == "|" else " ".join(l for l in lines if l)
            elif rest == "":
                q = peek()
                out[key] = block(ind + 1) if q and q[1] > ind else (block(ind) if q and q[1] == ind and q[2].startswith("- ") else None)
            else:
                out[key] = _value(rest)

    return block(0) or {}
