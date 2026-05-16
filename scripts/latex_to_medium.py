#!/usr/bin/env python3
"""
Convert a LaTeX article into Medium-friendly Markdown + JPEG assets.

Design goals
------------
- DO NOT modify the input .tex
- Reusable for other articles (single CLI)
- Render each figure / table as an isolated JPEG by compiling a
  per-float `standalone` LaTeX document (no page-context bleed)
- Convert structure (title, abstract, sections, lists, quotes) to
  clean Markdown that pastes well into Medium

Pipeline
--------
1. Parse .tex: title, abstract, document body.
2. Strip LaTeX comments first (raw .tex level).
3. Replace each figure/table block with a placeholder, keep raw
   contents for standalone rendering.
4. Convert the rest of the body to Markdown.
5. For each float, build a `standalone` .tex with TikZ/table
   packages, compile with pdflatex, convert PDF -> JPEG.
6. Re-inject image embeds + captions into Markdown placeholders.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # pymupdf


# ---------------------------------------------------------------------------
# Standalone template used to render figures and tables in isolation.
# ---------------------------------------------------------------------------
STANDALONE_PREAMBLE = r"""
\documentclass[border=10pt,varwidth=18cm]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{array}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{ragged2e}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{tikz}
\usetikzlibrary{positioning,shapes,backgrounds,arrows.meta,shadows,fit}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\newcolumntype{L}[1]{>{\RaggedRight\arraybackslash}p{#1}}
\setlength{\textwidth}{18cm}
\setlength{\linewidth}{18cm}
\setlength{\hsize}{18cm}
\begin{document}
%CONTENT%
\end{document}
"""


@dataclass
class FloatBlock:
    idx: int
    kind: str  # figure | table
    placeholder: str
    caption_plain: str
    inner_tex: str            # content used to render the standalone PDF
    image_name: str = ""
    rendered_ok: bool = False
    error: str = ""


# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------
def run_pdflatex(tex_path: Path) -> Tuple[bool, str]:
    cwd = tex_path.parent
    # Two passes help with pgfplots / refs even in standalone snippets.
    for _ in range(2):
        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
    pdf_path = tex_path.with_suffix(".pdf")
    if not pdf_path.exists():
        return False, (proc.stdout or "") + "\n" + (proc.stderr or "")
    return True, ""


# ---------------------------------------------------------------------------
# Brace-aware utilities
# ---------------------------------------------------------------------------
def find_brace_arg(text: str, start: int) -> Tuple[int, int]:
    """Given index of an opening '{' in text, return (start+1, end_of_arg)."""
    assert text[start] == "{"
    depth = 1
    j = start + 1
    while j < len(text) and depth > 0:
        c = text[j]
        if c == "\\" and j + 1 < len(text):
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return start + 1, j
        j += 1
    return start + 1, len(text)


def strip_command_with_arg(text: str, command: str) -> str:
    """Remove every \\command{...} (and its argument), handling nested braces."""
    pattern = "\\" + command + "{"
    out: List[str] = []
    i = 0
    while i < len(text):
        if text.startswith(pattern, i):
            inner_start = i + len(pattern) - 1  # index of '{'
            _, end = find_brace_arg(text, inner_start)
            i = end + 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def extract_command_arg(text: str, command: str) -> Optional[str]:
    pattern = "\\" + command + "{"
    i = text.find(pattern)
    if i == -1:
        return None
    inner_start = i + len(pattern) - 1
    s, e = find_brace_arg(text, inner_start)
    return text[s:e]


# ---------------------------------------------------------------------------
# Comment stripping (raw .tex level)
# ---------------------------------------------------------------------------
def strip_latex_comments(text: str) -> str:
    out: List[str] = []
    for line in text.splitlines():
        chars: List[str] = []
        i = 0
        while i < len(line):
            c = line[i]
            if c == "\\" and i + 1 < len(line):
                chars.append(c)
                chars.append(line[i + 1])
                i += 2
                continue
            if c == "%":
                break
            chars.append(c)
            i += 1
        out.append("".join(chars).rstrip())
    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# Title / abstract / body extraction
# ---------------------------------------------------------------------------
def clean_title_text(raw: str) -> Tuple[str, Optional[str]]:
    """Return (main_title, optional_subtitle) cleaned from \\title{...}."""
    text = raw
    for cmd in ["textbf", "textit", "emph", "large", "Large", "LARGE",
                "huge", "Huge", "small", "normalsize"]:
        text = re.sub(rf"\\{cmd}\b", "", text)
    text = strip_command_with_arg(text, "label")
    text = text.replace("\\\\", "\n")
    text = text.replace("{", "").replace("}", "")
    text = text.replace("~", " ")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "Untitled", None
    if len(lines) == 1:
        return lines[0], None
    return lines[0], " ".join(lines[1:])


def extract_title(tex: str) -> Tuple[str, Optional[str]]:
    raw = extract_command_arg(tex, "title")
    if raw is None:
        return "Untitled", None
    return clean_title_text(raw)


def extract_abstract(body: str) -> Tuple[str, str]:
    """Return (abstract_text_latex, body_without_abstract)."""
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S)
    if not m:
        return "", body
    abstract = m.group(1)
    new_body = body[: m.start()] + body[m.end():]
    return abstract, new_body


def extract_document_body(tex: str) -> str:
    m = re.search(r"\\begin\{document\}(.*)\\end\{document\}", tex, re.S)
    if not m:
        raise ValueError("Could not find \\begin{document} ... \\end{document}")
    body = m.group(1)
    bib_start = re.search(r"\\begin\{thebibliography\}", body)
    if bib_start:
        body = body[: bib_start.start()]
    return body


# ---------------------------------------------------------------------------
# Float extraction (raw inner tex preserved for standalone rendering)
# ---------------------------------------------------------------------------
def extract_caption_plain(block: str) -> str:
    raw = extract_command_arg(block, "caption")
    if raw is None:
        return ""
    return latex_inline_to_text(raw)


def prepare_float_for_standalone(block: str, kind: str) -> str:
    """Strip the float wrapper and caption/label, keep only render content."""
    inner = re.sub(
        rf"\\begin\{{{kind}\}}\s*(\[[^\]]*\])?\s*", "", block, count=1
    )
    inner = re.sub(rf"\s*\\end\{{{kind}\}}\s*$", "", inner)

    inner = strip_command_with_arg(inner, "caption")
    inner = strip_command_with_arg(inner, "label")

    inner = re.sub(r"\\centering\b", "", inner)
    inner = re.sub(r"\n{3,}", "\n\n", inner).strip()
    return inner


def extract_float_blocks(body: str) -> Tuple[str, List[FloatBlock]]:
    floats: List[FloatBlock] = []
    pattern = re.compile(r"\\begin\{(figure|table)\}.*?\\end\{\1\}", re.S)

    idx = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal idx
        kind = m.group(1)
        block = m.group(0)
        caption_plain = extract_caption_plain(block) or f"{kind.title()} {idx + 1}"
        inner = prepare_float_for_standalone(block, kind)
        placeholder = f"@@FLOAT_{idx:03d}@@"
        floats.append(
            FloatBlock(
                idx=idx,
                kind=kind,
                placeholder=placeholder,
                caption_plain=caption_plain,
                inner_tex=inner,
            )
        )
        idx += 1
        return f"\n\n{placeholder}\n\n"

    new_body = pattern.sub(repl, body)
    return new_body, floats


# ---------------------------------------------------------------------------
# Inline LaTeX -> text / markdown
# ---------------------------------------------------------------------------
def _common_inline_cleanup(text: str) -> str:
    text = text.replace("\\ldots", "...")
    text = text.replace("\\dots", "...")
    text = text.replace("---", "—").replace("--", "–")
    text = text.replace("``", '"').replace("''", '"').replace("`", "'")
    text = text.replace("\\%", "%").replace("\\&", "&")
    text = text.replace("\\_", "_").replace("\\$", "$").replace("\\#", "#")
    text = text.replace("~", " ")
    text = re.sub(r"\$\\times\$", "×", text)
    text = re.sub(r"\$\\to\$", "→", text)
    text = re.sub(r"\$\\rightarrow\$", "→", text)
    return text


def latex_inline_to_text(text: str) -> str:
    """Convert inline LaTeX to plain text (used for captions, quotes)."""
    text = text.replace("\\\\", " ")
    text = re.sub(r"~?\\cite\{[^}]*\}", "", text)
    text = re.sub(r"(Figure|Table|Chapter|Section)~?\\ref\{[^}]*\}", r"\1", text)
    text = re.sub(r"\\ref\{[^}]*\}", "", text)
    text = strip_command_with_arg(text, "label")

    for cmd in ("textbf", "textit", "emph", "texttt"):
        text = re.sub(rf"\\{cmd}\{{([^{{}}]*)\}}", r"\1", text)

    text = _common_inline_cleanup(text)
    text = re.sub(r"\\[a-zA-Z]+\b", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def latex_inline_to_markdown(text: str) -> str:
    """Convert inline LaTeX to Markdown (keeps bold/italic/code formatting)."""
    text = re.sub(r"~?\\cite\{[^}]*\}", "", text)
    text = re.sub(r"(Figure|Table|Chapter|Section)~?\\ref\{[^}]*\}", r"\1", text)
    text = re.sub(r"\\ref\{[^}]*\}", "", text)
    text = strip_command_with_arg(text, "label")

    def repl_wrap(cmd: str, wrap: str) -> None:
        nonlocal text
        pattern = re.compile(rf"\\{cmd}\{{([^{{}}]*)\}}")
        text = pattern.sub(lambda m: f"{wrap}{m.group(1)}{wrap}", text)

    for _ in range(3):  # repeat for shallow nesting
        repl_wrap("textbf", "**")
        repl_wrap("textit", "*")
        repl_wrap("emph", "*")
        repl_wrap("texttt", "`")
        repl_wrap("code", "`")

    text = _common_inline_cleanup(text)

    text = re.sub(r"\\(vspace|smallskip|medskip|bigskip|hspace)\{[^}]*\}", "", text)
    text = re.sub(
        r"\\(noindent|centering|sloppy|begingroup|endgroup|maketitle|tableofcontents|"
        r"newpage|cleardoublepage|footnotesize|small|normalsize|large|Large|huge|hfill|"
        r"par|clearpage)\b",
        "",
        text,
    )

    # Drop any remaining \xxx command without args
    text = re.sub(r"\\[a-zA-Z]+\b", "", text)

    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Block-level conversion
# ---------------------------------------------------------------------------
def convert_authorquote(text: str) -> str:
    patt = re.compile(r"\\authorquote\{(.*?)\}\{(.*?)\}\{(.*?)\}", re.S)

    def _r(m: re.Match[str]) -> str:
        q = latex_inline_to_text(m.group(1))
        a = latex_inline_to_text(m.group(2))
        s = latex_inline_to_text(m.group(3))
        return f"\n\n> \"{q}\"\n>\n> — {a}, *{s}*\n\n"

    return patt.sub(_r, text)


def convert_list_env(text: str, name: str, marker_fn) -> str:
    def repl(m: re.Match[str]) -> str:
        content = m.group(1)
        items = re.split(r"\\item\b", content)
        bullets: List[str] = []
        n = 1
        for it in items[1:]:
            it = re.sub(r"^\s*\[[^\]]*\]\s*", "", it, count=1)
            line = latex_inline_to_markdown(it).strip()
            if not line:
                continue
            bullets.append(marker_fn(n) + " " + line)
            n += 1
        return "\n\n" + "\n".join(bullets) + "\n\n"

    return re.sub(
        rf"\\begin\{{{name}\}}(?:\[[^\]]*\])?(.*?)\\end\{{{name}\}}",
        repl,
        text,
        flags=re.S,
    )


def convert_lists(text: str) -> str:
    text = convert_list_env(text, "itemize", lambda n: "-")
    text = convert_list_env(text, "enumerate", lambda n: f"{n}.")
    return text


def convert_headings(text: str) -> str:
    text = re.sub(
        r"\\section\*?\{([^}]*)\}",
        lambda m: f"\n\n## {latex_inline_to_text(m.group(1))}\n\n",
        text,
    )
    text = re.sub(
        r"\\subsection\*?\{([^}]*)\}",
        lambda m: f"\n\n### {latex_inline_to_text(m.group(1))}\n\n",
        text,
    )
    text = re.sub(
        r"\\subsubsection\*?\{([^}]*)\}",
        lambda m: f"\n\n#### {latex_inline_to_text(m.group(1))}\n\n",
        text,
    )
    return text


def drop_front_matter_macros(text: str) -> str:
    text = re.sub(
        r"\\(maketitle|tableofcontents|newpage|cleardoublepage|thispagestyle\{[^}]*\})",
        "",
        text,
    )
    return text


def body_to_markdown(body: str) -> str:
    text = drop_front_matter_macros(body)
    text = convert_authorquote(text)
    text = convert_headings(text)
    text = convert_lists(text)

    # Paragraph by paragraph: preserve structural blocks, apply inline cleanup
    # to free-text paragraphs.
    paragraphs = re.split(r"\n\s*\n", text)
    md_paragraphs: List[str] = []
    for p in paragraphs:
        p_stripped = p.strip()
        if not p_stripped:
            continue
        # Heading / list / blockquote / float placeholder: keep as-is.
        if (
            p_stripped.startswith(("##", "###", "####", "- ", "> ", "@@FLOAT_"))
            or re.match(r"^\d+\.\s", p_stripped)
        ):
            md_paragraphs.append(p_stripped)
            continue
        md_paragraphs.append(latex_inline_to_markdown(p_stripped))

    return "\n\n".join(md_paragraphs).strip() + "\n"


# ---------------------------------------------------------------------------
# Standalone rendering of figures and tables
# ---------------------------------------------------------------------------
def render_float_to_jpeg(fb: FloatBlock, assets_dir: Path, work_dir: Path) -> None:
    tex_doc = STANDALONE_PREAMBLE.replace("%CONTENT%", fb.inner_tex)

    float_dir = work_dir / f"float_{fb.idx:03d}"
    float_dir.mkdir(parents=True, exist_ok=True)
    tex_path = float_dir / "f.tex"
    tex_path.write_text(tex_doc, encoding="utf-8")

    ok, err = run_pdflatex(tex_path)
    if not ok:
        fb.error = err[-2000:]
        return

    pdf_path = tex_path.with_suffix(".pdf")
    out_jpg = assets_dir / fb.image_name
    try:
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
        pix.save(str(out_jpg))
        doc.close()
        fb.rendered_ok = True
    except Exception as e:  # noqa: BLE001
        fb.error = str(e)


def render_all_floats(floats: List[FloatBlock], assets_dir: Path,
                      keep_workdir: Optional[Path] = None) -> None:
    if keep_workdir is not None:
        keep_workdir.mkdir(parents=True, exist_ok=True)
        work_dir = keep_workdir
        for fb in floats:
            kind_prefix = "fig" if fb.kind == "figure" else "tab"
            fb.image_name = f"{kind_prefix}_{fb.idx + 1:03d}.jpg"
            render_float_to_jpeg(fb, assets_dir, work_dir)
            status = "OK" if fb.rendered_ok else "FAIL"
            print(f"  [{status}] {fb.kind} {fb.idx + 1:03d} -> {fb.image_name}")
        return

    with tempfile.TemporaryDirectory(prefix="medium_export_") as tmp:
        work_dir = Path(tmp)
        for fb in floats:
            kind_prefix = "fig" if fb.kind == "figure" else "tab"
            fb.image_name = f"{kind_prefix}_{fb.idx + 1:03d}.jpg"
            render_float_to_jpeg(fb, assets_dir, work_dir)
            status = "OK" if fb.rendered_ok else "FAIL"
            print(f"  [{status}] {fb.kind} {fb.idx + 1:03d} -> {fb.image_name}")


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def inject_float_embeds(md_text: str, floats: List[FloatBlock]) -> str:
    out = md_text
    for fb in floats:
        if fb.rendered_ok:
            embed = (
                f"![{fb.caption_plain}](assets/{fb.image_name})\n\n"
                f"*{fb.caption_plain}*"
            )
        else:
            embed = (
                f"> **[Missing render: {fb.kind} {fb.idx + 1}]** "
                f"{fb.caption_plain}"
            )
        out = out.replace(fb.placeholder, embed)
    return out


def write_float_map(path: Path, floats: List[FloatBlock]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "kind", "caption", "image", "rendered_ok", "error_snippet"])
        for fb in floats:
            w.writerow([
                fb.idx,
                fb.kind,
                fb.caption_plain,
                fb.image_name,
                "yes" if fb.rendered_ok else "no",
                (fb.error[:300] if fb.error else ""),
            ])


BOOK_BANNER = (
    "> **From the book.** This article presents a condensed version of the "
    "theses developed in *Non-Deterministic Spec-Driven Development: "
    "Enterprise Edition* &mdash; available on Amazon.com and all local stores."
)


def build_markdown(title: str, subtitle: Optional[str],
                   abstract_md: str, body_md: str) -> str:
    parts: List[str] = [f"# {title}"]
    if subtitle:
        parts.append(f"### {subtitle}")
    parts.append(BOOK_BANNER)
    if abstract_md.strip():
        parts.append("**Abstract**\n\n" + abstract_md.strip())
        parts.append("---")
    parts.append(body_md.strip())
    return "\n\n".join(parts).rstrip() + "\n"


def rewrite_asset_urls(md: str, base_url: str) -> str:
    """Rewrite ](assets/xxx) to ](<base_url>/assets/xxx) for remote hosting."""
    base = base_url.rstrip("/")
    return re.sub(r"\]\(assets/", f"]({base}/assets/", md)


def convert(tex_path: Path, output_base: Path,
            keep_build: bool = False,
            image_base_url: Optional[str] = None) -> Path:
    if not tex_path.exists():
        raise FileNotFoundError(f"Input .tex not found: {tex_path}")

    slug = tex_path.stem
    out_dir = output_base / slug
    assets_dir = out_dir / "assets"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    raw = tex_path.read_text(encoding="utf-8")
    raw = strip_latex_comments(raw)

    title, subtitle = extract_title(raw)
    body = extract_document_body(raw)
    abstract_raw, body = extract_abstract(body)
    body_with_placeholders, floats = extract_float_blocks(body)

    abstract_md = body_to_markdown(abstract_raw) if abstract_raw else ""
    body_md = body_to_markdown(body_with_placeholders)

    print(f"Title: {title}")
    if subtitle:
        print(f"Subtitle: {subtitle}")
    print(f"Floats found: {len(floats)} (figures+tables)")
    print("Rendering floats via standalone compilation:")
    keep_dir = (out_dir / "_build") if keep_build else None
    render_all_floats(floats, assets_dir, keep_workdir=keep_dir)

    body_md = inject_float_embeds(body_md, floats)
    abstract_md = inject_float_embeds(abstract_md, floats)

    md = build_markdown(title, subtitle, abstract_md, body_md)
    md_out = out_dir / "medium.md"
    md_out.write_text(md, encoding="utf-8")

    if image_base_url:
        md_remote = rewrite_asset_urls(md, image_base_url)
        md_remote_out = out_dir / "medium.remote.md"
        md_remote_out.write_text(md_remote, encoding="utf-8")
        print(f"Remote-asset Markdown -> {md_remote_out}")

    write_float_map(out_dir / "float_map.csv", floats)
    return md_out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a LaTeX article to Medium-friendly Markdown + JPEG assets"
    )
    parser.add_argument("--input", required=True, help="Path to input .tex")
    parser.add_argument("--output-dir", required=True, help="Output base directory")
    parser.add_argument("--keep-build", action="store_true",
                        help="Keep per-float .tex/.pdf build artifacts for debugging")
    parser.add_argument("--image-base-url", default=None,
                        help=("If set, also emit medium.remote.md with image links "
                              "rewritten as <base>/assets/<file> (e.g. a raw GitHub URL)."))
    args = parser.parse_args()

    tex_path = Path(args.input).resolve()
    out_base = Path(args.output_dir).resolve()
    out_base.mkdir(parents=True, exist_ok=True)

    md_out = convert(tex_path, out_base, keep_build=args.keep_build,
                     image_base_url=args.image_base_url)
    print()
    print(f"OK: Markdown -> {md_out}")
    print(f"     Assets -> {md_out.parent / 'assets'}")
    print(f"     Float map -> {md_out.parent / 'float_map.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
