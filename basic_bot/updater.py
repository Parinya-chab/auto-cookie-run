"""Self-update from GitHub Releases.

Flow: ask GitHub for the latest release -> compare its tag with BOT_VERSION ->
(user confirms) download the release .zip -> check its SHA-256 against the
release's SHA256SUMS.txt -> extract the new .exe beside the running one ->
start it and exit. Settings files (telegram_config.json, reward_path.json,
boost templates ...) live beside the exe, so the new version keeps them.

Nothing is installed silently: the UI always asks before downloading.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests

API_LATEST = "https://api.github.com/repos/{repo}/releases/latest"
EXE_PATTERN = re.compile(r"^CookieRunBasicMouse_v(\d+(?:\.\d+)*)\.exe$", re.IGNORECASE)
SUMS_NAME = "SHA256SUMS.txt"
USER_AGENT = "AutoCookieRun-Updater"


class UpdateError(Exception):
    """Raised with a Thai, user-facing message."""


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    notes: str
    page_url: str
    zip_name: str
    zip_url: str
    zip_size: int
    sums_url: str | None


def parse_version(text: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", text or "")
    return tuple(int(n) for n in numbers) if numbers else (0,)


def is_newer(remote: str, local: str) -> bool:
    a, b = parse_version(remote), parse_version(local)
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))


def fetch_latest(repo: str, timeout: float = 10.0) -> ReleaseInfo:
    try:
        response = requests.get(
            API_LATEST.format(repo=repo),
            headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
            timeout=timeout,
        )
    except requests.RequestException as error:
        raise UpdateError(f"เชื่อมต่อ GitHub ไม่ได้ ({type(error).__name__})") from error
    if response.status_code == 404:
        raise UpdateError("ยังไม่มีเวอร์ชันที่เผยแพร่บน GitHub")
    if response.status_code == 403:
        raise UpdateError("GitHub จำกัดจำนวนครั้งที่ตรวจชั่วคราว ลองใหม่ภายหลัง")
    if response.status_code != 200:
        raise UpdateError(f"GitHub ตอบกลับผิดปกติ (HTTP {response.status_code})")
    data = response.json()
    assets = data.get("assets") or []
    zip_asset = next((a for a in assets if str(a.get("name", "")).lower().endswith(".zip")), None)
    if zip_asset is None:
        raise UpdateError("เวอร์ชันล่าสุดบน GitHub ไม่มีไฟล์ .zip ให้ดาวน์โหลด")
    sums_asset = next((a for a in assets if a.get("name") == SUMS_NAME), None)
    tag = str(data.get("tag_name") or "")
    return ReleaseInfo(
        version=tag.lstrip("vV"),
        tag=tag,
        notes=str(data.get("body") or "").strip(),
        page_url=str(data.get("html_url") or ""),
        zip_name=str(zip_asset["name"]),
        zip_url=str(zip_asset["browser_download_url"]),
        zip_size=int(zip_asset.get("size") or 0),
        sums_url=str(sums_asset["browser_download_url"]) if sums_asset else None,
    )


def _expected_sha256(sums_text: str, file_name: str) -> str | None:
    for line in sums_text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[-1].lstrip("*").split("/")[-1] == file_name:
            return parts[0].lower()
    return None


def download_update(info: ReleaseInfo, target_dir: Path, progress=None, timeout: float = 30.0) -> Path:
    """Download + verify the release zip and extract the exe into target_dir. Returns the new exe path."""
    if not info.sums_url:
        raise UpdateError("เวอร์ชันนี้ไม่มีไฟล์ตรวจสอบ SHA256SUMS.txt จึงไม่ติดตั้งให้อัตโนมัติ")
    headers = {"User-Agent": USER_AGENT}
    try:
        sums = requests.get(info.sums_url, headers=headers, timeout=timeout)
        sums.raise_for_status()
    except requests.RequestException as error:
        raise UpdateError(f"ดาวน์โหลดไฟล์ตรวจสอบไม่สำเร็จ ({type(error).__name__})") from error
    expected = _expected_sha256(sums.text, info.zip_name)
    if not expected:
        raise UpdateError("ไม่พบค่า SHA-256 ของไฟล์ zip ใน SHA256SUMS.txt")

    work = Path(tempfile.mkdtemp(prefix="autocookierun_update_"))
    try:
        zip_path = _download_verified(info, work, expected, headers, progress, timeout)
        return _extract_exe(zip_path, target_dir)
    finally:
        shutil.rmtree(work, ignore_errors=True)  # never leave the 70+ MB zip in %TEMP%


def _download_verified(info, work, expected, headers, progress, timeout):
    zip_path = work / info.zip_name
    digest = hashlib.sha256()
    done = 0
    try:
        with requests.get(info.zip_url, headers=headers, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length") or info.zip_size or 0)
            with open(zip_path, "wb") as handle:
                for chunk in response.iter_content(chunk_size=256 * 1024):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    digest.update(chunk)
                    done += len(chunk)
                    if progress is not None:
                        progress(done, total)
    except (requests.RequestException, OSError) as error:
        raise UpdateError(f"ดาวน์โหลดไม่สำเร็จ ({type(error).__name__})") from error
    if digest.hexdigest().lower() != expected:
        raise UpdateError("ไฟล์ที่ดาวน์โหลดไม่ตรงกับค่าตรวจสอบ SHA-256 (อาจเสียหาย) จึงยกเลิกการอัปเดต")
    return zip_path


def _extract_exe(zip_path, target_dir):
    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [m for m in archive.namelist() if EXE_PATTERN.match(Path(m).name)]
            if not members:
                raise UpdateError("ในไฟล์ zip ไม่มีตัวโปรแกรม .exe")
            member = members[0]
            target_dir.mkdir(parents=True, exist_ok=True)
            new_exe = target_dir / Path(member).name
            if new_exe.exists():
                new_exe = target_dir / (new_exe.stem + "_new.exe")
            partial = new_exe.with_suffix(".exe.part")
            with archive.open(member) as source, open(partial, "wb") as out:
                shutil.copyfileobj(source, out, 1024 * 1024)
            os.replace(partial, new_exe)
    except (zipfile.BadZipFile, OSError) as error:
        raise UpdateError(f"แตกไฟล์อัปเดตไม่สำเร็จ ({type(error).__name__})") from error
    return new_exe


def launch(exe_path: Path) -> None:
    """Start the new version as an independent process (the caller then exits)."""
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent), creationflags=flags, close_fds=True)


def cleanup_old_versions(current_exe: Path, current_version: str, wait_seconds: float = 8.0) -> list[str]:
    """Delete older CookieRunBasicMouse_v*.exe beside the running exe (called by the new version)."""
    time.sleep(wait_seconds)  # give the old process time to exit
    removed = []
    for path in current_exe.parent.glob("CookieRunBasicMouse_v*.exe"):
        match = EXE_PATTERN.match(path.name)
        if not match or path.resolve() == current_exe.resolve():
            continue
        if is_newer(current_version, match.group(1)):
            try:
                path.unlink()
                removed.append(path.name)
            except OSError:
                pass  # still running or locked: leave it
    return removed
