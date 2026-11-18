import argparse
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path


if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    import cv2
    import mss
except ImportError as error:
    missing_package = getattr(error, "name", "unknown")
    print(
        f"[DEPENDENCY ERROR] ไม่พบแพ็กเกจ {missing_package}. "
        "กรุณาใช้ virtualenv ของโปรเจกต์ก่อนรัน"
    )
    raise SystemExit(1) from error

try:
    from .bot_config import (
        BOT_VERSION,
        CALIBRATION_MODE_AUTO,
        CALIBRATION_MODE_CUSTOM,
        CALIBRATION_MODE_DEFAULT,
        DEFAULT_SCAN_REGION,
        GAME_WINDOW_TITLE,
    )
    from .cookie_bot import (
        calibrate_screen,
        capture_current_region_bgr,
        capture_window_client_bgr,
        find_game_window,
    )
except ImportError:
    from basic_bot.bot_config import (
        BOT_VERSION,
        CALIBRATION_MODE_AUTO,
        CALIBRATION_MODE_CUSTOM,
        CALIBRATION_MODE_DEFAULT,
        DEFAULT_SCAN_REGION,
        GAME_WINDOW_TITLE,
    )
    from basic_bot.cookie_bot import (
        calibrate_screen,
        capture_current_region_bgr,
        capture_window_client_bgr,
        find_game_window,
    )


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "captured_frames"


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Capture the exact frame shape used by the bot's image detection."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "default", "custom"),
        default="auto",
        help=(
            "auto = LDPlayer client area, default = saved DEFAULT_SCAN_REGION, "
            "custom = click 4 corners before capture"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Folder for saved PNG frames and JSON metadata.",
    )
    parser.add_argument(
        "--prefix",
        default="detect_frame",
        help="Filename prefix for saved captures.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="How many frames to capture.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between frames when --count is greater than 1.",
    )
    return parser


def normalize_mode(mode):
    mode = mode.lower()
    if mode == "auto":
        return CALIBRATION_MODE_AUTO
    if mode == "default":
        return CALIBRATION_MODE_DEFAULT
    if mode == "custom":
        return CALIBRATION_MODE_CUSTOM
    raise ValueError(f"unknown capture mode: {mode}")


def get_capture_region(screen_capture, mode, custom_region=None):
    if mode == CALIBRATION_MODE_AUTO:
        game_window = find_game_window()
        if game_window is None:
            raise RuntimeError(f"ไม่พบหน้าต่าง {GAME_WINDOW_TITLE}")
        if game_window.isMinimized:
            raise RuntimeError("หน้าต่างเกมถูก minimize อยู่")
        frame, region = capture_window_client_bgr(screen_capture, game_window)
        window_title = game_window.title
        return frame, region, window_title

    if mode == CALIBRATION_MODE_DEFAULT:
        region = DEFAULT_SCAN_REGION.copy()
    elif mode == CALIBRATION_MODE_CUSTOM:
        if custom_region is None:
            raise RuntimeError("custom mode ต้องมี custom_region ก่อน capture")
        region = custom_region.copy()
    else:
        raise ValueError(f"unsupported mode: {mode}")

    frame = capture_current_region_bgr(screen_capture, region)
    return frame, region, None


def save_capture(frame, region, output_dir, prefix, mode, index, window_title):
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    suffix = f"_{index:03d}" if index is not None else ""
    image_path = output_dir / f"{prefix}_{mode.lower()}_{timestamp}{suffix}.png"
    metadata_path = image_path.with_suffix(".json")

    if frame is None or frame.size == 0:
        raise RuntimeError("ภาพที่แคปได้ไม่มีข้อมูล")
    if not cv2.imwrite(str(image_path), frame):
        raise RuntimeError(f"บันทึกรูปไม่สำเร็จ: {image_path}")

    height, width = frame.shape[:2]
    metadata = {
        "bot_version": BOT_VERSION,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "capture_mode": mode,
        "window_title": window_title,
        "region": {
            "left": int(region["left"]),
            "top": int(region["top"]),
            "width": int(region["width"]),
            "height": int(region["height"]),
        },
        "image": {
            "width": int(width),
            "height": int(height),
            "channels": int(frame.shape[2]) if len(frame.shape) == 3 else 1,
            "color_space": "BGR source saved as PNG",
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return image_path, metadata_path, metadata


def main():
    args = build_parser().parse_args()
    if args.count <= 0:
        raise SystemExit("[CONFIG ERROR] --count ต้องมากกว่า 0")
    if args.interval < 0:
        raise SystemExit("[CONFIG ERROR] --interval ต้องไม่ติดลบ")

    mode = normalize_mode(args.mode)
    output_dir = Path(args.output_dir)
    stop_event = threading.Event()

    custom_region = None
    if mode == CALIBRATION_MODE_CUSTOM:
        custom_region = calibrate_screen(stop_event)
        if custom_region is None:
            raise SystemExit("[CAPTURE] ยกเลิก เพราะ calibration ไม่สำเร็จ")

    saved_paths = []
    with mss.MSS() as screen_capture:
        for index in range(1, args.count + 1):
            frame, region, window_title = get_capture_region(
                screen_capture,
                mode,
                custom_region=custom_region,
            )
            image_path, metadata_path, metadata = save_capture(
                frame,
                region,
                output_dir,
                args.prefix,
                mode,
                index if args.count > 1 else None,
                window_title,
            )
            saved_paths.append(image_path)
            print(
                "[CAPTURE] saved "
                f"{image_path} | size={metadata['image']['width']}x"
                f"{metadata['image']['height']} | region={metadata['region']}"
            )
            print(f"[CAPTURE] metadata {metadata_path}")

            if index < args.count:
                stop_event.wait(args.interval)

    print(f"[CAPTURE] เสร็จแล้วทั้งหมด {len(saved_paths)} รูป")


if __name__ == "__main__":
    main()
