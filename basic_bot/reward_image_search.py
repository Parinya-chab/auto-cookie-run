"""Search reward-box templates in recorded ``01_before_open_all.png`` images.

The script treats every template occurrence as one match.  This is important
because a screenshot can contain two, three, or four boxes, and the same box
type can appear more than once in one screenshot.

Example::

    uv run python basic_bot/reward_image_search.py --date 2026-08-15
    uv run python basic_bot/reward_image_search.py --manage-love

Reports are written to ``<date>/image_search_reports`` by default:

* ``image_search_by_image.csv`` - one row per round with counts per template
* ``image_search_summary.md`` - aggregate summary and scan diagnostics
* ``supream_treasue_search.csv`` - search results for the treasure-ticket image
* ``supream_treasue_summary.md`` - daily and ``imageLove`` totals
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


DEFAULT_DATE = "2026-09-05"
TARGET_FILENAME = "01_before_open_all.png"
SECOND_IMAGE_FILENAME = "02_before_confirm.png"
LOVE_TEMPLATE_NAME = "love"
LOVE_OUTPUT_DIR_NAME = "imageLove"
ROUND_PREFIX = "round_"
DEFAULT_THRESHOLD = 0.95
DEFAULT_SUPPRESSION_FACTOR = 0.55
CAPTURED_FRAME_DIR_NAME = "captured_frames"


@dataclass(frozen=True)
class Template:
    name: str
    path: Path
    image: np.ndarray

    @property
    def width(self) -> int:
        return int(self.image.shape[1])

    @property
    def height(self) -> int:
        return int(self.image.shape[0])


@dataclass(frozen=True)
class Match:
    score: float
    top_left_x: int
    top_left_y: int
    center_x: int
    center_y: int


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    default_records_root = script_dir / "dist" / "reward_records"

    parser = argparse.ArgumentParser(
        description=(
            "Search reward templates in 01_before_open_all.png files and "
            "write per-image and aggregate reports."
        )
    )
    parser.add_argument(
        "--records-root",
        type=Path,
        default=default_records_root,
        help=f"Reward records root (default: {default_records_root})",
    )
    parser.add_argument(
        "--date",
        default=DEFAULT_DATE,
        help=f"Date folder under records root (default: {DEFAULT_DATE})",
    )
    parser.add_argument(
        "--templates-dir",
        type=Path,
        help="Template directory (default: <records-root>/image_search)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Report directory (default: <date>/image_search_reports)",
    )
    parser.add_argument(
        "--target-name",
        default=TARGET_FILENAME,
        help=f"Target filename (default: {TARGET_FILENAME})",
    )
    parser.add_argument(
        "--love-output-dir",
        type=Path,
        help=(
            "Directory for both images from love-detected rounds "
            f"(default: <records-root>/{LOVE_OUTPUT_DIR_NAME})"
        ),
    )
    parser.add_argument(
        "--love-second-name",
        default=SECOND_IMAGE_FILENAME,
        help=(
            "Second image copied from a love-detected round "
            f"(default: {SECOND_IMAGE_FILENAME})"
        ),
    )
    parser.add_argument(
        "--love-template",
        type=Path,
        help=(
            "Use this image as the love template for this run only; the existing "
            "love.png is left unchanged."
        ),
    )
    parser.add_argument(
        "--manage-love",
        action="store_true",
        help=(
            "Open a small window to upload/replace/delete the persistent love "
            "template and capture a live game frame."
        ),
    )
    parser.add_argument(
        "--capture-game-frame",
        action="store_true",
        help=(
            "Capture one normalized game frame using the same client-area "
            "detection frame as the bot, then exit."
        ),
    )
    parser.add_argument(
        "--capture-output-dir",
        type=Path,
        help=(
            "Folder for --capture-game-frame output "
            f"(default: <script-dir>/{CAPTURED_FRAME_DIR_NAME})"
        ),
    )
    parser.add_argument(
        "--treasure-template",
        type=Path,
        default=script_dir / "supream_treasue.png",
        help="Additional template to search (default: <basic_bot>/supream_treasue.png)",
    )
    parser.add_argument(
        "--treasure-threshold",
        type=float,
        default=0.90,
        help="Threshold for the additional treasure template (default: 0.90)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"TM_CCOEFF_NORMED threshold (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--suppression-factor",
        type=float,
        default=DEFAULT_SUPPRESSION_FACTOR,
        help=(
            "Center-distance factor for collapsing duplicate peaks from the "
            f"same object (default: {DEFAULT_SUPPRESSION_FACTOR})"
        ),
    )
    return parser.parse_args()


def load_templates(
    template_dir: Path,
    *,
    love_template_path: Path | None = None,
) -> list[Template]:
    """Load the normal template set, optionally replacing only ``love``."""

    template_paths = sorted(template_dir.glob("*.png"))
    if love_template_path is not None:
        love_template_path = validate_image_path(love_template_path)
        template_paths = [
            path for path in template_paths if path.stem != LOVE_TEMPLATE_NAME
        ]
    if not template_paths:
        if love_template_path is None:
            raise FileNotFoundError(f"No PNG templates found in: {template_dir}")

    templates: list[Template] = []
    for path in template_paths:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            raise ValueError(f"Could not read template image: {path}")
        templates.append(Template(name=path.stem, path=path, image=image))

    if love_template_path is not None:
        love_image = cv2.imread(str(love_template_path), cv2.IMREAD_COLOR)
        if love_image is None or love_image.size == 0:
            raise ValueError(f"Could not read love template image: {love_template_path}")
        templates.append(
            Template(
                name=LOVE_TEMPLATE_NAME,
                path=love_template_path,
                image=love_image,
            )
        )
        templates.sort(key=lambda template: template.name)
    return templates


def validate_image_path(path: Path) -> Path:
    """Resolve and validate an image selected by the user."""

    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Image file not found: {resolved}")
    image = cv2.imread(str(resolved), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError(f"Could not read image: {resolved}")
    return resolved


def persistent_love_template_path(template_dir: Path) -> Path:
    """Return the persistent template path used by the existing search flow."""

    return template_dir / f"{LOVE_TEMPLATE_NAME}.png"


def install_love_template(source_path: Path, template_dir: Path) -> Path:
    """Atomically replace the persistent ``love.png`` with a user image."""

    source = validate_image_path(source_path)
    template_dir.mkdir(parents=True, exist_ok=True)
    destination = persistent_love_template_path(template_dir)
    temporary_path = template_dir / f".{destination.name}.tmp"
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, destination)
    except OSError:
        try:
            temporary_path.unlink()
        except OSError:
            pass
        raise
    return destination


def delete_love_template(template_dir: Path) -> bool:
    """Delete the persistent love template; return whether it existed."""

    path = persistent_love_template_path(template_dir)
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    return True


def find_round_directories(date_dir: Path, target_name: str) -> list[Path]:
    """Find round folders, including folders whose target image is missing."""

    round_dirs = sorted(
        path
        for path in date_dir.rglob("*")
        if path.is_dir() and path.name.startswith(ROUND_PREFIX)
    )
    if round_dirs:
        return round_dirs

    # A useful fallback for a differently named dataset.
    return sorted({path.parent for path in date_dir.rglob(target_name)})


def find_matches(
    result: np.ndarray,
    template: Template,
    threshold: float,
    suppression_factor: float,
) -> list[Match]:
    """Return high-confidence local peaks, with duplicate peaks suppressed."""

    y_positions, x_positions = np.where(result >= threshold)
    if len(x_positions) == 0:
        return []

    scores = result[y_positions, x_positions]
    order = np.argsort(scores)[::-1]
    suppression_radius = max(template.width, template.height) * suppression_factor
    suppression_radius_squared = suppression_radius**2

    selected: list[Match] = []
    for index in order:
        x = int(x_positions[index])
        y = int(y_positions[index])
        score = float(result[y, x])
        center_x = x + template.width // 2
        center_y = y + template.height // 2

        is_duplicate = any(
            (center_x - match.center_x) ** 2
            + (center_y - match.center_y) ** 2
            < suppression_radius_squared
            for match in selected
        )
        if is_duplicate:
            continue

        selected.append(
            Match(
                score=score,
                top_left_x=x,
                top_left_y=y,
                center_x=center_x,
                center_y=center_y,
            )
        )

    return selected


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def copy_love_images(
    round_dir: Path,
    *,
    records_root: Path,
    output_dir: Path,
    target_name: str,
    second_name: str,
) -> tuple[list[str], list[str], list[str]]:
    """Copy both images from a love-detected round with stable unique names."""

    copied: list[str] = []
    missing: list[str] = []
    errors: list[str] = []
    round_slug = "__".join(relative_path(round_dir, records_root).split("/"))

    for source_name in (target_name, second_name):
        source_path = round_dir / source_name
        if not source_path.is_file():
            missing.append(relative_path(source_path, records_root))
            continue

        destination_path = output_dir / f"{round_slug}__{source_name}"
        try:
            # The destination name is deterministic, so rerunning updates the
            # same file instead of creating duplicate copies.
            shutil.copy2(source_path, destination_path)
        except OSError as error:
            errors.append(f"{relative_path(source_path, records_root)}: {error}")
            continue
        copied.append(relative_path(destination_path, records_root))

    return copied, missing, errors


def write_by_image_report(
    path: Path,
    rows: list[dict[str, object]],
    template_names: list[str],
) -> None:
    fieldnames = [
        "round_folder",
        "target_relative_path",
        "status",
        "image_width",
        "image_height",
        *[f"{name}_count" for name in template_names],
        "total_matches",
        "matched_templates",
        "love_copy_status",
        "love_copied_count",
        "love_copied_files",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_report(
    path: Path,
    *,
    records_root: Path,
    date_dir: Path,
    template_dir: Path,
    love_template_path: Path | None,
    target_name: str,
    threshold: float,
    suppression_factor: float,
    template_names: list[str],
    rows: list[dict[str, object]],
    matches_by_template: dict[str, list[Match]],
    missing_targets: list[str],
    errors: list[str],
    love_output_dir: Path,
    love_round_count: int,
    love_copied_count: int,
    love_copy_missing: list[str],
    love_copy_errors: list[str],
) -> None:
    total_rounds = len(rows)
    scanned_rows = [row for row in rows if row["status"] == "scanned"]
    total_matches = sum(len(matches) for matches in matches_by_template.values())
    box_count_distribution = Counter(
        int(row["total_matches"]) for row in scanned_rows
    )
    love_template_description = (
        str(love_template_path)
        if love_template_path is not None
        else str(persistent_love_template_path(template_dir))
    )

    lines = [
        "# Image Search Summary",
        "",
        "## สรุปการค้นหา",
        "",
        f"- โฟลเดอร์ข้อมูล: `{date_dir}`",
        f"- ภาพอ้างอิง: `{template_dir}` ({len(template_names)} รูป)",
        f"- รูป love ที่ใช้ค้นหา: `{love_template_description}`",
        f"- ภาพที่ค้นหา: `{target_name}` เท่านั้น",
        f"- จำนวนโฟลเดอร์รอบทั้งหมด: **{total_rounds}**",
        f"- จำนวนภาพที่อ่านและค้นหาสำเร็จ: **{len(scanned_rows)}**",
        f"- จำนวนภาพที่ไม่พบไฟล์เป้าหมาย: **{len(missing_targets)}**",
        f"- จำนวน match รวมทุกชนิด: **{total_matches} กล่อง**",
        f"- วิธีค้นหา: `cv2.TM_CCOEFF_NORMED`, threshold **{threshold:.4f}**",
        f"- ระยะรวมจุดซ้ำ: `{suppression_factor:.2f} x max(template width, height)`",
        f"- รอบที่พบ love และคัดลอกภาพ: **{love_round_count} รอบ**",
        f"- จำนวนไฟล์ที่คัดลอกไป `imageLove`: **{love_copied_count} ไฟล์**",
        f"- โฟลเดอร์ปลายทาง: `{love_output_dir}`",
        "",
        "## รายงานแยกตามรูปอ้างอิง",
        "",
        "| รูปอ้างอิง | จำนวนกล่องที่พบ | จำนวนภาพที่พบ | สัดส่วนภาพที่พบ | เฉลี่ยต่อภาพที่พบ |",
        "|---|---:|---:|---:|---:|",
    ]

    for name in template_names:
        template_matches = matches_by_template[name]
        image_count = sum(
            int(row[f"{name}_count"]) > 0 for row in scanned_rows
        )
        average = len(template_matches) / image_count if image_count else 0.0
        percentage = image_count / len(scanned_rows) * 100 if scanned_rows else 0.0
        lines.append(
            f"| `{name}.png` | {len(template_matches)} | {image_count} | "
            f"{percentage:.2f}% | {average:.2f} |"
        )

    lines.extend(
        [
            "",
            "## จำนวนกล่องต่อภาพ",
            "",
            "| จำนวน match ในภาพ | จำนวนภาพ |",
            "|---:|---:|",
        ]
    )
    for count, image_count in sorted(box_count_distribution.items()):
        lines.append(f"| {count} | {image_count} |")

    if missing_targets:
        lines.extend(["", "## โฟลเดอร์ที่ไม่มีภาพเป้าหมาย", ""])
        lines.extend(f"- `{item}`" for item in missing_targets)

    if errors:
        lines.extend(["", "## รายการที่อ่านไม่ได้", ""])
        lines.extend(f"- `{item}`" for item in errors)

    if love_copy_missing:
        lines.extend(["", "## ไฟล์ที่ขาดจากรอบที่พบ love", ""])
        lines.extend(f"- `{item}`" for item in love_copy_missing)

    if love_copy_errors:
        lines.extend(["", "## รายการคัดลอกที่มีข้อผิดพลาด", ""])
        lines.extend(f"- `{item}`" for item in love_copy_errors)

    lines.extend(
        [
            "",
            "## หมายเหตุ",
            "",
            "- จำนวนกล่องคือจำนวน occurrence ที่ผ่าน threshold; ถ้าชนิดเดียวกันซ้ำในภาพเดียวจะนับซ้ำทุกกล่อง",
            "- รายละเอียดนับแยกรอบอยู่ใน `image_search_by_image.csv`",
            f"- Root ที่ใช้ค้นหา: `{records_root}`",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def search_template_files(
    paths: list[Path],
    *,
    scope: str,
    root: Path,
    template: Template,
    threshold: float,
    suppression_factor: float,
) -> list[dict[str, object]]:
    """Search one template in an explicit list of image files."""

    rows: list[dict[str, object]] = []
    for path in paths:
        row: dict[str, object] = {
            "scope": scope,
            "file_path": relative_path(path, root),
            "status": "read_error",
            "image_width": "",
            "image_height": "",
            "best_score": "",
            "match_count": 0,
            "match_centers": "",
            "match_top_lefts": "",
        }
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            rows.append(row)
            continue
        if template.height > image.shape[0] or template.width > image.shape[1]:
            row["status"] = "template_too_large"
            rows.append(row)
            continue

        result = cv2.matchTemplate(image, template.image, cv2.TM_CCOEFF_NORMED)
        _, best_score, _, _ = cv2.minMaxLoc(result)
        matches = find_matches(
            result,
            template,
            threshold=threshold,
            suppression_factor=suppression_factor,
        )
        row["status"] = "match" if matches else "no_match"
        row["image_width"] = int(image.shape[1])
        row["image_height"] = int(image.shape[0])
        row["best_score"] = f"{float(best_score):.6f}"
        row["match_count"] = len(matches)
        row["match_centers"] = ";".join(
            f"{match.center_x},{match.center_y}" for match in matches
        )
        row["match_top_lefts"] = ";".join(
            f"{match.top_left_x},{match.top_left_y}" for match in matches
        )
        rows.append(row)
    return rows


def write_treasure_report(
    csv_path: Path,
    summary_path: Path,
    *,
    template_path: Path,
    date_name: str,
    image_love_dir: Path,
    threshold: float,
    rows: list[dict[str, object]],
) -> None:
    """Write detailed and aggregate reports for the additional template."""

    fieldnames = [
        "scope",
        "file_path",
        "status",
        "image_width",
        "image_height",
        "best_score",
        "match_count",
        "match_centers",
        "match_top_lefts",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    scope_names = [("date", f"วันที่ {date_name}"), ("imageLove", "imageLove")]
    lines = [
        "# supream_treasue Image Search Summary",
        "",
        f"- Template: `{template_path}`",
        f"- Threshold: **{threshold:.4f}** (`cv2.TM_CCOEFF_NORMED`)",
        f"- Daily search scope: all `.png` files under `{date_name}`",
        f"- imageLove search scope: all `.png` files under `{image_love_dir}`",
        "",
        "| ขอบเขต | จำนวนภาพ | ภาพที่พบ | จำนวน occurrence |",
        "|---|---:|---:|---:|",
    ]
    for scope, label in scope_names:
        scope_rows = [row for row in rows if row["scope"] == scope]
        matched_rows = [row for row in scope_rows if row["status"] == "match"]
        occurrences = sum(int(row["match_count"]) for row in scope_rows)
        lines.append(
            f"| {label} | {len(scope_rows)} | {len(matched_rows)} | {occurrences} |"
        )

    lines.extend(["", "## ไฟล์ที่พบ", ""])
    for scope, label in scope_names:
        lines.extend([f"### {label}", ""])
        matched_rows = [
            row for row in rows if row["scope"] == scope and row["status"] == "match"
        ]
        if not matched_rows:
            lines.append("- ไม่พบ")
            lines.append("")
            continue
        for row in matched_rows:
            lines.append(
                f"- `{row['file_path']}` — {row['match_count']} match "
                f"(best score {row['best_score']})"
            )
        lines.append("")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def capture_game_frame(output_dir: Path) -> Path:
    """Capture the normalized client frame used by the live bot detector."""

    try:
        from .bot_config import TEMPLATE_REFERENCE_FRAME_SIZE
        from .cookie_bot import capture_window_client_bgr, find_game_window
        from .frame_normalization import normalize_for_template_matching
    except ImportError:
        from bot_config import TEMPLATE_REFERENCE_FRAME_SIZE
        from cookie_bot import capture_window_client_bgr, find_game_window
        from frame_normalization import normalize_for_template_matching

    game_window = find_game_window()
    if game_window is None:
        raise RuntimeError("ไม่พบหน้าต่างเกมสำหรับ capture")
    if game_window.isMinimized:
        raise RuntimeError("หน้าต่างเกมถูก minimize อยู่")

    frame, _region = capture_window_client_bgr(None, game_window)
    if frame is None or frame.size == 0:
        raise RuntimeError("ไม่สามารถอ่านภาพจากพื้นที่เกมได้")

    detection_frame = normalize_for_template_matching(
        frame,
        TEMPLATE_REFERENCE_FRAME_SIZE,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    output_path = output_dir / f"love_capture_{timestamp}.png"
    if not cv2.imwrite(str(output_path), detection_frame):
        raise RuntimeError(f"บันทึกภาพไม่สำเร็จ: {output_path}")
    return output_path


def launch_love_template_manager(
    template_dir: Path,
    capture_output_dir: Path,
) -> int:
    """Open a small GUI for persistent love-template management."""

    import tkinter as tk
    from tkinter import filedialog, messagebox

    template_dir.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.title("Love Image Search Template")
    root.geometry("650x250")
    root.minsize(560, 220)
    root.columnconfigure(0, weight=1)

    path_var = tk.StringVar()
    status_var = tk.StringVar()

    content = tk.Frame(root, padx=16, pady=14)
    content.grid(row=0, column=0, sticky="nsew")
    content.columnconfigure(0, weight=1)
    tk.Label(
        content,
        text="จัดการรูป love ที่ใช้ค้นหาใน reward_image_search",
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", pady=(0, 8))
    tk.Label(
        content,
        textvariable=path_var,
        anchor="w",
        justify="left",
        wraplength=610,
    ).grid(row=1, column=0, sticky="ew", pady=(0, 4))
    tk.Label(
        content,
        textvariable=status_var,
        anchor="w",
        justify="left",
        wraplength=610,
    ).grid(row=2, column=0, sticky="ew", pady=(0, 12))

    actions = tk.Frame(content)
    actions.grid(row=3, column=0, sticky="w")

    def refresh_status():
        path = persistent_love_template_path(template_dir)
        path_var.set(f"ไฟล์ถาวร: {path}")
        if not path.is_file():
            status_var.set("สถานะ: ยังไม่มีรูป love — การค้นหาจะข้าม love")
            return
        try:
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None or image.size == 0:
                raise ValueError("อ่านรูปไม่ได้")
            status_var.set(
                f"สถานะ: พร้อมใช้งาน ({image.shape[1]}x{image.shape[0]})"
            )
        except (OSError, ValueError):
            status_var.set("สถานะ: ไฟล์มีปัญหา กรุณาอัปโหลดใหม่")

    def upload():
        source_path = filedialog.askopenfilename(
            parent=root,
            title="เลือกรูป love ใหม่",
            filetypes=(
                ("รูปภาพ", "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("ไฟล์ทั้งหมด", "*.*"),
            ),
        )
        if not source_path:
            return
        try:
            destination = install_love_template(Path(source_path), template_dir)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "อัปโหลดรูปไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=root,
            )
            return
        refresh_status()
        messagebox.showinfo(
            "บันทึกรูปสำเร็จ",
            f"บันทึกเป็น template ถาวรแล้ว:\n{destination}",
            parent=root,
        )

    def remove():
        path = persistent_love_template_path(template_dir)
        if not path.is_file():
            refresh_status()
            return
        if not messagebox.askyesno(
            "ลบรูป love",
            f"ต้องการลบรูปนี้ใช่หรือไม่?\n{path}",
            parent=root,
        ):
            return
        try:
            delete_love_template(template_dir)
        except OSError as error:
            messagebox.showerror(
                "ลบรูปไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=root,
            )
            return
        refresh_status()

    def capture():
        try:
            path = capture_game_frame(capture_output_dir)
        except (OSError, RuntimeError, ValueError) as error:
            messagebox.showerror(
                "แคปภาพไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=root,
            )
            return
        messagebox.showinfo(
            "แคปภาพสำเร็จ",
            f"บันทึกเฟรมเดียวกับ image search แล้ว:\n{path}\n\n"
            "ให้นำไฟล์นี้ไปกดอัปโหลด หากต้องการใช้เป็นรูป love",
            parent=root,
        )

    tk.Button(actions, text="อัปโหลด/แทนที่รูป love", command=upload).grid(
        row=0, column=0, padx=(0, 6)
    )
    tk.Button(actions, text="ลบรูป love", command=remove).grid(
        row=0, column=1, padx=(0, 6)
    )
    tk.Button(actions, text="แคปเฟรมเกม", command=capture).grid(
        row=0, column=2
    )
    tk.Label(
        content,
        text=(
            "หลังอัปโหลดแล้ว ปิดหน้าต่างนี้และรันคำสั่งค้นหาเดิมได้เลย "
            "ระบบจะใช้ไฟล์ love.png ใหม่นี้อัตโนมัติ"
        ),
        anchor="w",
        justify="left",
        wraplength=610,
    ).grid(row=4, column=0, sticky="ew", pady=(14, 0))
    refresh_status()
    root.mainloop()
    return 0


def run() -> int:
    args = parse_args()
    if args.manage_love and args.capture_game_frame:
        raise ValueError("ใช้ --manage-love หรือ --capture-game-frame อย่างใดอย่างหนึ่ง")

    script_dir = Path(__file__).resolve().parent
    records_root = args.records_root.resolve()
    date_dir = (records_root / args.date).resolve()
    template_dir = (
        args.templates_dir.resolve()
        if args.templates_dir
        else records_root / "image_search"
    )
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else date_dir / "image_search_reports"
    )
    love_output_dir = (
        args.love_output_dir.resolve()
        if args.love_output_dir
        else records_root / LOVE_OUTPUT_DIR_NAME
    )
    capture_output_dir = (
        args.capture_output_dir.resolve()
        if args.capture_output_dir
        else script_dir / CAPTURED_FRAME_DIR_NAME
    )

    if args.manage_love:
        if args.love_template:
            raise ValueError("ไม่ควรใช้ --love-template พร้อม --manage-love")
        return launch_love_template_manager(template_dir, capture_output_dir)
    if args.capture_game_frame:
        if args.love_template:
            raise ValueError(
                "ไม่ควรใช้ --love-template พร้อม --capture-game-frame"
            )
        output_path = capture_game_frame(capture_output_dir)
        print(f"[CAPTURE] บันทึกเฟรม image search แล้ว: {output_path}")
        return 0

    if not 0.0 <= args.threshold <= 1.0:
        raise ValueError("--threshold must be between 0 and 1")
    if not 0.0 <= args.treasure_threshold <= 1.0:
        raise ValueError("--treasure-threshold must be between 0 and 1")
    if args.suppression_factor <= 0:
        raise ValueError("--suppression-factor must be greater than 0")
    if not date_dir.is_dir():
        raise FileNotFoundError(f"Date directory not found: {date_dir}")
    treasure_template_path = args.treasure_template.resolve()
    treasure_image = cv2.imread(str(treasure_template_path), cv2.IMREAD_COLOR)
    if treasure_image is None or treasure_image.size == 0:
        raise FileNotFoundError(
            f"Could not read treasure template: {treasure_template_path}"
        )
    # The destination is also the second search scope.  Create it on the
    # first run so a missing imageLove folder does not prevent the normal
    # reward scan from running.
    image_love_dir = love_output_dir
    image_love_dir.mkdir(parents=True, exist_ok=True)

    templates = load_templates(
        template_dir,
        love_template_path=args.love_template,
    )
    template_names = [template.name for template in templates]
    round_dirs = find_round_directories(date_dir, args.target_name)
    if not round_dirs:
        raise FileNotFoundError(f"No round directories found in: {date_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    love_output_dir.mkdir(parents=True, exist_ok=True)
    matches_by_template: dict[str, list[Match]] = {
        name: [] for name in template_names
    }
    rows: list[dict[str, object]] = []
    missing_targets: list[str] = []
    errors: list[str] = []
    love_copy_missing: list[str] = []
    love_copy_errors: list[str] = []
    love_round_count = 0
    love_copied_count = 0

    for round_dir in round_dirs:
        target_path = round_dir / args.target_name
        round_name = relative_path(round_dir, date_dir)
        row: dict[str, object] = {
            "round_folder": round_name,
            "target_relative_path": relative_path(target_path, date_dir),
            "status": "missing_target",
            "image_width": "",
            "image_height": "",
            "total_matches": 0,
            "matched_templates": "",
            "love_copy_status": "not_detected",
            "love_copied_count": 0,
            "love_copied_files": "",
        }
        for name in template_names:
            row[f"{name}_count"] = 0

        if not target_path.is_file():
            missing_targets.append(round_name)
            rows.append(row)
            continue

        image = cv2.imread(str(target_path), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            row["status"] = "read_error"
            errors.append(relative_path(target_path, date_dir))
            rows.append(row)
            continue

        row["status"] = "scanned"
        row["image_width"] = int(image.shape[1])
        row["image_height"] = int(image.shape[0])
        matched_template_names: list[str] = []

        for template in templates:
            if template.height > image.shape[0] or template.width > image.shape[1]:
                errors.append(
                    f"{relative_path(target_path, date_dir)}: "
                    f"template {template.name} is larger than target"
                )
                continue

            result = cv2.matchTemplate(
                image, template.image, cv2.TM_CCOEFF_NORMED
            )
            matches = find_matches(
                result,
                template,
                threshold=args.threshold,
                suppression_factor=args.suppression_factor,
            )
            row[f"{template.name}_count"] = len(matches)
            if matches:
                matched_template_names.append(template.name)
                matches_by_template[template.name].extend(matches)

        row["total_matches"] = sum(
            int(row[f"{name}_count"]) for name in template_names
        )
        row["matched_templates"] = ",".join(matched_template_names)

        if int(row.get(f"{LOVE_TEMPLATE_NAME}_count", 0)) > 0:
            copied, missing, copy_errors = copy_love_images(
                round_dir,
                records_root=records_root,
                output_dir=love_output_dir,
                target_name=args.target_name,
                second_name=args.love_second_name,
            )
            love_round_count += 1
            love_copied_count += len(copied)
            love_copy_missing.extend(missing)
            love_copy_errors.extend(copy_errors)
            row["love_copy_status"] = "copied" if copied else "copy_error"
            row["love_copied_count"] = len(copied)
            row["love_copied_files"] = ";".join(copied)
        rows.append(row)

    by_image_path = output_dir / "image_search_by_image.csv"
    summary_path = output_dir / "image_search_summary.md"
    write_by_image_report(by_image_path, rows, template_names)
    write_summary_report(
        summary_path,
        records_root=records_root,
        date_dir=date_dir,
        template_dir=template_dir,
        love_template_path=(
            args.love_template.resolve() if args.love_template else None
        ),
        target_name=args.target_name,
        threshold=args.threshold,
        suppression_factor=args.suppression_factor,
        template_names=template_names,
        rows=rows,
        matches_by_template=matches_by_template,
        missing_targets=missing_targets,
        errors=errors,
        love_output_dir=love_output_dir,
        love_round_count=love_round_count,
        love_copied_count=love_copied_count,
        love_copy_missing=love_copy_missing,
        love_copy_errors=love_copy_errors,
    )

    treasure_template = Template(
        name=treasure_template_path.stem,
        path=treasure_template_path,
        image=treasure_image,
    )
    treasure_rows = search_template_files(
        sorted(date_dir.rglob("*.png")),
        scope="date",
        root=records_root,
        template=treasure_template,
        threshold=args.treasure_threshold,
        suppression_factor=args.suppression_factor,
    )
    treasure_rows.extend(
        search_template_files(
            sorted(image_love_dir.rglob("*.png")),
            scope="imageLove",
            root=records_root,
            template=treasure_template,
            threshold=args.treasure_threshold,
            suppression_factor=args.suppression_factor,
        )
    )
    treasure_csv_path = output_dir / "supream_treasue_search.csv"
    treasure_summary_path = output_dir / "supream_treasue_summary.md"
    write_treasure_report(
        treasure_csv_path,
        treasure_summary_path,
        template_path=treasure_template_path,
        date_name=args.date,
        image_love_dir=image_love_dir,
        threshold=args.treasure_threshold,
        rows=treasure_rows,
    )

    scanned_count = sum(row["status"] == "scanned" for row in rows)
    total_matches = sum(len(matches) for matches in matches_by_template.values())
    print(f"[DONE] rounds={len(rows)} scanned={scanned_count}")
    print(f"[DONE] missing_target={len(missing_targets)} errors={len(errors)}")
    for name in template_names:
        image_count = sum(
            int(row[f"{name}_count"]) > 0
            for row in rows
            if row["status"] == "scanned"
        )
        print(
            f"[MATCH] {name}: occurrences={len(matches_by_template[name])} "
            f"images={image_count}"
        )
    print(f"[DONE] total_occurrences={total_matches}")
    print(
        f"[LOVE] rounds={love_round_count} copied_files={love_copied_count} "
        f"output={love_output_dir}"
    )
    for scope in ("date", "imageLove"):
        scope_rows = [row for row in treasure_rows if row["scope"] == scope]
        print(
            f"[TREASURE] {scope}: files={len(scope_rows)} "
            f"matched_files={sum(row['status'] == 'match' for row in scope_rows)} "
            f"occurrences={sum(int(row['match_count']) for row in scope_rows)}"
        )
    print(f"[REPORT] {by_image_path}")
    print(f"[REPORT] {summary_path}")
    print(f"[REPORT] {treasure_csv_path}")
    print(f"[REPORT] {treasure_summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except (FileNotFoundError, ValueError) as error:
        print(f"[ERROR] {error}")
        raise SystemExit(1)
