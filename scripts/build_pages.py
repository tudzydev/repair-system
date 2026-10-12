"""Build the public worksheet site without Flask or private runtime files."""
from pathlib import Path
import shutil
from build_guide import build_guide

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "_site"


def build():
    OUTPUT.mkdir(exist_ok=True)
    # Only explicitly public assets enter the Pages artifact.
    for name in ("static", "templates", "pages"):
        shutil.copytree(ROOT / name, OUTPUT / name, dirs_exist_ok=True)
    for name in (
        "README.md", "app.py", "models.py", "services.py", "schema.sql",
        "requirements.txt", "requirements-pdf.txt", "requirements-production.txt",
        "start.command", "school-repair-source.zip",
    ):
        shutil.copy2(ROOT / name, OUTPUT / name)
    index = (ROOT / "index.html").read_text()
    index = index.replace('href="login"', 'href="pages/login.html"')
    index = index.replace("เข้าสู่ระบบแจ้งซ่อม →", "ทดลองระบบแจ้งซ่อม →")
    index = index.replace("เปิดระบบแจ้งซ่อมบนเซิร์ฟเวอร์นี้", "ระบบจำลองบน GitHub Pages · ข้อมูลเก็บในเบราว์เซอร์นี้")
    (OUTPUT / "index.html").write_text(index)
    (OUTPUT / "login").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "pages/login.html", OUTPUT / "login/index.html")
    build_guide(OUTPUT)
    (OUTPUT / ".nojekyll").touch()
    print(f"Built public website: {OUTPUT}")


if __name__ == "__main__":
    build()
