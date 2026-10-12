"""Render the web guide from README.md so the documentation has one source."""
from pathlib import Path
from string import Template

import markdown

ROOT = Path(__file__).resolve().parent.parent


def build_guide(output=ROOT):
    renderer = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
        extension_configs={"toc": {"toc_depth": "2-2"}},
    )
    content = renderer.convert((ROOT / "README.md").read_text(encoding="utf-8"))
    template = Template((ROOT / "pages/guide-template.html").read_text(encoding="utf-8"))
    (output / "README.html").write_text(
        template.substitute(content=content, toc=renderer.toc), encoding="utf-8"
    )


if __name__ == "__main__":
    build_guide()
    print("Built web guide: README.html")
