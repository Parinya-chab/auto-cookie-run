"""Build and (optionally) publish a new version.

    python release.py            # build + package into release/ (nothing is uploaded)
    python release.py --publish  # ... then push, tag and create the GitHub Release

Before running: set BOT_VERSION in basic_bot/bot_config.py and add a section for it
to CHANGELOG.md (its text becomes the release notes and the in-app update message).
Needs: the venv from requirements.txt, and GitHub CLI (gh) logged in for --publish.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOT = ROOT / "basic_bot"
REPO = re.search(r'^GITHUB_REPO = "([^"]+)"', (BOT / "bot_config.py").read_text(encoding="utf-8"), re.M).group(1)
GH_CANDIDATES = ["gh", r"C:\Program Files\GitHub CLI\gh.exe"]

READ_ME_FIRST = """Auto Cookie Run v{v}

1. เปิด CookieRunBasicMouse_v{v}.exe
2. ถ้าขึ้น "Windows protected your PC" ให้กด More info แล้วกด Run anyway
3. เปิดเกมในอีมู (LDPlayer / MuMu) ไว้หน้าล็อบบี้ แล้วกด "เริ่มทำงาน"
4. กด F8 เพื่อพัก / ทำงานต่อ
5. มีเวอร์ชันใหม่เมื่อไหร่ โปรแกรมจะถามให้อัปเดตเอง (หรือกดปุ่ม "อัปเดต")

แจ้งเตือน Telegram (ไม่บังคับ): กด "ตั้งค่า" ในโปรแกรม แล้วใส่ Bot Token กับ Chat ID
ห้ามแชร์ไฟล์ telegram_config.json ของตัวเองให้ใคร

ซอร์สโค้ดและวิธีใช้แบบละเอียด: https://github.com/{repo}
"""


def run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, **kw)


def find_gh():
    for candidate in GH_CANDIDATES:
        if shutil.which(candidate) or Path(candidate).exists():
            return candidate
    sys.exit("ไม่พบ GitHub CLI (gh)")


def changelog_section(version):
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(rf"^## v?{re.escape(version)}\b.*?$\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match or not match.group(1).strip():
        sys.exit(f"CHANGELOG.md ยังไม่มีหัวข้อ '## v{version}'")
    return match.group(1).strip()


def check_no_secret(exe):
    """Fail if a local telegram_config.json token/chat id ended up inside the exe."""
    data = exe.read_bytes()
    for cfg in list(BOT.glob("telegram_config.json")) + list(ROOT.glob("telegram_config.json")):
        try:
            values = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for key in ("bot_token", "chat_id"):
            value = str(values.get(key) or "").strip()
            if len(value) >= 6 and value.encode() in data:
                sys.exit(f"พบ {key} อยู่ในไฟล์ exe ห้ามปล่อย!")
    config = (BOT / "bot_config.py").read_text(encoding="utf-8")
    if not re.search(r'^TELEGRAM_BOT_TOKEN = ""', config, re.M):
        sys.exit("TELEGRAM_BOT_TOKEN ใน bot_config.py ต้องเป็นค่าว่าง")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", help="push, tag and create the GitHub Release")
    args = parser.parse_args()

    version = re.search(r'^BOT_VERSION = "([^"]+)"', (BOT / "bot_config.py").read_text(encoding="utf-8"), re.M).group(1)
    notes = changelog_section(version)
    tag = f"v{version}"
    print(f"== Auto Cookie Run {tag} ({REPO})")

    if args.publish:
        status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
        if status.strip():
            sys.exit("มีไฟล์ที่ยังไม่ได้ commit ให้ commit ก่อน --publish\n" + status)
        tags = subprocess.run(["git", "tag", "--list", tag], cwd=ROOT, capture_output=True, text=True).stdout
        if tags.strip():
            sys.exit(f"มี tag {tag} อยู่แล้ว ให้เปลี่ยน BOT_VERSION ก่อน")

    out = ROOT / "release"
    # Build into release/ (not basic_bot/dist) so a copy of the bot that is open from dist never blocks the build.
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--distpath", str(out / "dist"),
         "--workpath", str(out / "build"), "CookieRunBasicMouse.spec"], cwd=BOT)
    exe = out / "dist" / f"CookieRunBasicMouse_v{version}.exe"
    if not exe.exists():
        sys.exit(f"ไม่พบ {exe}")
    check_no_secret(exe)

    zip_path = out / f"AutoCookieRun_v{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(exe, exe.name)
        archive.write(ROOT / "telegram_config.example.json", "telegram_config.example.json")
        archive.writestr("อ่านก่อนใช้.txt", READ_ME_FIRST.format(v=version, repo=REPO).replace("\n", "\r\n"))
    sums = out / "SHA256SUMS.txt"
    sums.write_text(
        "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {name}\n" for p, name in ((zip_path, zip_path.name), (exe, exe.name))),
        encoding="utf-8",
    )
    print(f"packaged {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")
    print(sums.read_text(encoding="utf-8"))

    if not args.publish:
        print("ยังไม่ได้อัปโหลด: ตรวจไฟล์แล้วรันอีกครั้งด้วย --publish")
        return
    gh = find_gh()
    notes_file = out / "notes.md"
    notes_file.write_text(notes, encoding="utf-8")
    run(["git", "push", "origin", "HEAD"], cwd=ROOT)
    run([gh, "release", "create", tag, str(zip_path), str(sums), "--repo", REPO, "--target", "main",
         "--title", f"Auto Cookie Run {tag}", "--notes-file", str(notes_file), "--latest"], cwd=ROOT)
    notes_file.unlink()
    run(["git", "fetch", "--tags"], cwd=ROOT)
    print(f"เผยแพร่แล้ว: https://github.com/{REPO}/releases/tag/{tag}")


if __name__ == "__main__":
    main()
