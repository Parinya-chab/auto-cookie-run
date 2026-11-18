import ctypes
import json
import math
import os
import queue
import random
import sys
import tempfile
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk


def ensure_dpi_awareness():
    """Enable physical screen coordinates before GUI/capture libraries load."""
    user32 = ctypes.windll.user32
    try:
        setter = user32.SetProcessDpiAwarenessContext
        setter.argtypes = [ctypes.c_void_p]
        setter.restype = wintypes.BOOL
        if setter(ctypes.c_void_p(-4)):  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            print("[DPI] เปิดใช้งาน Per-Monitor V2 DPI Awareness แล้ว")
            return True
    except (AttributeError, OSError, ValueError):
        pass

    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:
            print("[DPI] เปิดใช้งาน Per-Monitor DPI Awareness แล้ว")
            return True
    except (AttributeError, OSError, ValueError):
        pass

    try:
        if user32.SetProcessDPIAware():
            print("[DPI] เปิดใช้งาน System DPI Awareness แล้ว")
            return True
    except (AttributeError, OSError, ValueError):
        pass

    print("[DPI WARNING] Windows ล็อก DPI mode ไปแล้ว พิกัดอาจไม่ตรงบนจอหลายสเกล")
    return False


# pyautogui can lock the process into System-DPI mode while it is imported.
# Set Per-Monitor V2 first so capture and click coordinates stay in physical pixels.
DPI_AWARENESS_ENABLED = ensure_dpi_awareness()

try:
    import cv2
    import mss
    import numpy as np
    import pyautogui
    import pygetwindow as gw
    import requests
    from pynput import keyboard, mouse
except ImportError as error:
    missing_package = getattr(error, "name", "unknown")
    print(
        f"[DEPENDENCY ERROR] ไม่พบแพ็กเกจ {missing_package}. "
        "กรุณาติดตั้ง dependency ของโปรเจกต์ก่อนรัน"
    )
    raise SystemExit(1) from error


try:
    from .bot_config import (
        BOT_NAME,
        BOT_VERSION,
        GITHUB_REPO,
        UPDATE_CHECK_ON_START,
        ACTION_BY_NAME,
        BOOTS_BUTTON_ACTIONS,
        BOOTS_SCREEN_TEMPLATE,
        BOOTS_STUCK_ALERT_AFTER,
        BONUS_FLOW_ABSENT_CONFIRM_FRAMES,
        BONUS_FLOW_DELAY_TIERS,
        BONUS_FLOW_MAX_ATTEMPTS,
        BONUS_FLOW_REFERENCE_FRAME_SIZE,
        BONUS_FLOW_TRANSITION_TIMEOUT,
        BONUS_PAUSE_CLICK_AREA,
        BONUS_PAUSE_PRE_CLICK_DELAY_RANGE,
        BONUS_QUIT_1_CLICK_AREA,
        BONUS_QUIT_2_CLICK_AREA,
        BONUS_QUIT_MATCH_THRESHOLD,
        BONUS_QUIT_PRE_CLICK_DELAY_RANGE,
        BONUS_QUIT_SEARCH_PADDING,
        BONUS_QUIT_TEMPLATE,
        BONUS_TRIGGER_MATCH_THRESHOLD,
        BONUS_TRIGGER_SEARCH_AREA,
        BONUS_TRIGGER_TEMPLATE,
        BOOST_TARGET_BASE_SPEED,
        BOOST_TARGET_DOUBLE_COIN,
        BOOST_TARGET_MAGNET,
        BOOST_TARGET_TEMPLATES,
        BOOST_TEMPLATE_STORAGE_DIR,
        BOOST_MODE_ALWAYS,
        BOOST_MODE_NEVER,
        BOOST_MODE_RANDOM,
        BUTTON_ACTIONS,
        ButtonAction,
        CALIBRATION_MODE_AUTO,
        CALIBRATION_MODE_CUSTOM,
        CALIBRATION_MODE_DEFAULT,
        CAPTCHA_ALERT_AFTER,
        CAPTCHA_DIFF_THRESHOLD,
        CAPTCHA_FRAME_INTERVAL,
        CAPTCHA_MOVEMENT_THRESHOLD,
        CAPTCHA_RECHECK_INTERVAL,
        DEFAULT_SCAN_REGION,
        DEFAULT_RANDOM_BOOST_PERCENT,
        DEFAULT_BOOST_TARGET,
        ECO_LOOP_INTERVAL_RANGE,
        ENABLE_CONFIG,
        LOCKED_FEATURES,
        FALLBACK_BUTTON_ACTIONS,
        FALLBACK_MAX_ATTEMPTS,
        FAST_LOOP_INTERVAL,
        FAST_SCAN_AFTER_PLAY,
        FATIGUE_DELAY_RANGE,
        GAME_WINDOW_TITLE,
        INTER_CLICK_DELAY_RANGE,
        LDPLAYER_WINDOW_CLASS,
        MUMU_WINDOW_CLASS_PREFIXES,
        MUMU_WINDOW_TITLE_KEYWORDS,
        MATCH_THRESHOLD,
        MOUSE_HOLD_DELAY_RANGE,
        MULTI_BUY_MAX_ATTEMPTS,
        NO_BUTTON_ALERT_AFTER,
        OK_FATIGUE_ROUND_RANGE,
        PERFORMANCE_LOG_INTERVAL,
        PLAY_CLICK_VERIFY_DELAY,
        PLAY_SUCCESS_CONFIRM_FRAMES,
        PLAY_FATIGUE_ROUND_RANGE,
        PLAY_TRANSITION_MARKER_THRESHOLD,
        PLAY_TRANSITION_TIMEOUT,
        PLAY_TRANSITION_VERIFY_START_DELAY,
        REWARD_PATH_CONFIG_FILE,
        REWARD_RECORDS_DIR,
        PLAY_RETRY_LONG_DELAY_PROBABILITY,
        PLAY_RETRY_LONG_DELAY_RANGE,
        PLAY_RETRY_SHORT_DELAY_RANGE,
        PLAY_STUCK_MAX_ATTEMPTS,
        REPEAT_CLICK_COOLDOWN,
        RuntimeConfig,
        STOP_TEMPLATE,
        STOP_CLOSE_CENTER_DISTANCE,
        STOP_GUARD_MATCH_THRESHOLD,
        START_JUMP_CLICK_AREA,
        START_JUMP_DOUBLE_CLICK_PROBABILITY,
        START_JUMP_FLOW_DURATION_TIERS,
        START_JUMP_GROUP_GAP_RANGE,
        START_JUMP_HOLD_DELAY_RANGE,
        START_JUMP_INITIAL_DELAY_RANGE,
        START_JUMP_INTER_CLICK_DELAY_RANGE,
        START_JUMP_REFERENCE_FRAME_SIZE,
        START_JUMP_TOTAL_CLICKS_RANGE,
        START_JUMP_TRIPLE_CLICK_PROBABILITY,
        TEMPLATE_REFERENCE_FRAME_SIZE,
        TEMPLATE_NAMES,
        TEMPLATE_SOURCE_FRAME_SIZES,
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        TELEGRAM_CONFIG_FILE,
        TELEGRAM_COOLDOWN,
        WINDOW_TITLE_FALLBACK_KEYWORDS,
    )
    from .pause_control import (
        PAUSE_POLL_INTERVAL,
        wait_while_paused,
        wait_with_pause,
        wait_with_pause_status,
    )
    from .frame_normalization import (
        detection_to_source_scale,
        map_detection_point_to_source,
        normalize_for_template_matching,
    )
    from .boost_templates import BoostTemplateDefault, BoostTemplateManager
    from . import updater
except ImportError:
    from bot_config import (
        BOT_NAME,
        BOT_VERSION,
        GITHUB_REPO,
        UPDATE_CHECK_ON_START,
        ACTION_BY_NAME,
        BOOTS_BUTTON_ACTIONS,
        BOOTS_SCREEN_TEMPLATE,
        BOOTS_STUCK_ALERT_AFTER,
        BONUS_FLOW_ABSENT_CONFIRM_FRAMES,
        BONUS_FLOW_DELAY_TIERS,
        BONUS_FLOW_MAX_ATTEMPTS,
        BONUS_FLOW_REFERENCE_FRAME_SIZE,
        BONUS_FLOW_TRANSITION_TIMEOUT,
        BONUS_PAUSE_CLICK_AREA,
        BONUS_PAUSE_PRE_CLICK_DELAY_RANGE,
        BONUS_QUIT_1_CLICK_AREA,
        BONUS_QUIT_2_CLICK_AREA,
        BONUS_QUIT_MATCH_THRESHOLD,
        BONUS_QUIT_PRE_CLICK_DELAY_RANGE,
        BONUS_QUIT_SEARCH_PADDING,
        BONUS_QUIT_TEMPLATE,
        BONUS_TRIGGER_MATCH_THRESHOLD,
        BONUS_TRIGGER_SEARCH_AREA,
        BONUS_TRIGGER_TEMPLATE,
        BOOST_TARGET_BASE_SPEED,
        BOOST_TARGET_DOUBLE_COIN,
        BOOST_TARGET_MAGNET,
        BOOST_TARGET_TEMPLATES,
        BOOST_TEMPLATE_STORAGE_DIR,
        BOOST_MODE_ALWAYS,
        BOOST_MODE_NEVER,
        BOOST_MODE_RANDOM,
        BUTTON_ACTIONS,
        ButtonAction,
        CALIBRATION_MODE_AUTO,
        CALIBRATION_MODE_CUSTOM,
        CALIBRATION_MODE_DEFAULT,
        CAPTCHA_ALERT_AFTER,
        CAPTCHA_DIFF_THRESHOLD,
        CAPTCHA_FRAME_INTERVAL,
        CAPTCHA_MOVEMENT_THRESHOLD,
        CAPTCHA_RECHECK_INTERVAL,
        DEFAULT_SCAN_REGION,
        DEFAULT_RANDOM_BOOST_PERCENT,
        DEFAULT_BOOST_TARGET,
        ECO_LOOP_INTERVAL_RANGE,
        ENABLE_CONFIG,
        LOCKED_FEATURES,
        FALLBACK_BUTTON_ACTIONS,
        FALLBACK_MAX_ATTEMPTS,
        FAST_LOOP_INTERVAL,
        FAST_SCAN_AFTER_PLAY,
        FATIGUE_DELAY_RANGE,
        GAME_WINDOW_TITLE,
        INTER_CLICK_DELAY_RANGE,
        LDPLAYER_WINDOW_CLASS,
        MUMU_WINDOW_CLASS_PREFIXES,
        MUMU_WINDOW_TITLE_KEYWORDS,
        MATCH_THRESHOLD,
        MOUSE_HOLD_DELAY_RANGE,
        MULTI_BUY_MAX_ATTEMPTS,
        NO_BUTTON_ALERT_AFTER,
        OK_FATIGUE_ROUND_RANGE,
        PERFORMANCE_LOG_INTERVAL,
        PLAY_CLICK_VERIFY_DELAY,
        PLAY_SUCCESS_CONFIRM_FRAMES,
        PLAY_FATIGUE_ROUND_RANGE,
        PLAY_TRANSITION_MARKER_THRESHOLD,
        PLAY_TRANSITION_TIMEOUT,
        PLAY_TRANSITION_VERIFY_START_DELAY,
        REWARD_PATH_CONFIG_FILE,
        REWARD_RECORDS_DIR,
        PLAY_RETRY_LONG_DELAY_PROBABILITY,
        PLAY_RETRY_LONG_DELAY_RANGE,
        PLAY_RETRY_SHORT_DELAY_RANGE,
        PLAY_STUCK_MAX_ATTEMPTS,
        REPEAT_CLICK_COOLDOWN,
        RuntimeConfig,
        STOP_TEMPLATE,
        STOP_CLOSE_CENTER_DISTANCE,
        STOP_GUARD_MATCH_THRESHOLD,
        START_JUMP_CLICK_AREA,
        START_JUMP_DOUBLE_CLICK_PROBABILITY,
        START_JUMP_FLOW_DURATION_TIERS,
        START_JUMP_GROUP_GAP_RANGE,
        START_JUMP_HOLD_DELAY_RANGE,
        START_JUMP_INITIAL_DELAY_RANGE,
        START_JUMP_INTER_CLICK_DELAY_RANGE,
        START_JUMP_REFERENCE_FRAME_SIZE,
        START_JUMP_TOTAL_CLICKS_RANGE,
        START_JUMP_TRIPLE_CLICK_PROBABILITY,
        TEMPLATE_REFERENCE_FRAME_SIZE,
        TEMPLATE_NAMES,
        TEMPLATE_SOURCE_FRAME_SIZES,
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        TELEGRAM_CONFIG_FILE,
        TELEGRAM_COOLDOWN,
        WINDOW_TITLE_FALLBACK_KEYWORDS,
    )
    from pause_control import (
        PAUSE_POLL_INTERVAL,
        wait_while_paused,
        wait_with_pause,
        wait_with_pause_status,
    )
    from frame_normalization import (
        detection_to_source_scale,
        map_detection_point_to_source,
        normalize_for_template_matching,
    )
    from boost_templates import BoostTemplateDefault, BoostTemplateManager
    import updater


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def resource_path(relative_path):
    """Resolve an asset beside the script or inside a PyInstaller bundle."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def runtime_data_path(relative_path):
    """Resolve writable user data beside the script or the packaged EXE."""
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def default_reward_root():
    """Return the fallback reward root beside the script or packaged EXE."""
    return os.path.abspath(runtime_data_path(REWARD_RECORDS_DIR))


def normalize_reward_root(value):
    """Normalize a user-selected reward root without creating it."""
    text = str(value or "").strip()
    if not text:
        return default_reward_root()
    return os.path.abspath(os.path.expandvars(os.path.expanduser(text)))


def load_reward_root_setting():
    """Load only the remembered reward root; Telegram lives in telegram_config.json."""
    config_path = runtime_data_path(REWARD_PATH_CONFIG_FILE)
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            payload = json.load(config_file)
    except FileNotFoundError:
        return default_reward_root(), None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return (
            default_reward_root(),
            f"อ่าน {REWARD_PATH_CONFIG_FILE} ไม่สำเร็จ ({type(error).__name__}); "
            "ใช้โฟลเดอร์ reward_records ค่าเริ่มต้น",
        )

    reward_root = payload.get("reward_root") if isinstance(payload, dict) else None
    if not isinstance(reward_root, str) or not reward_root.strip():
        return (
            default_reward_root(),
            f"ข้อมูลใน {REWARD_PATH_CONFIG_FILE} ไม่ถูกต้อง; "
            "ใช้โฟลเดอร์ reward_records ค่าเริ่มต้น",
        )
    return normalize_reward_root(reward_root), None


def save_reward_root_setting(reward_root):
    """Persist the selected reward root atomically beside the EXE."""
    config_path = runtime_data_path(REWARD_PATH_CONFIG_FILE)
    temporary_path = config_path + ".tmp"
    payload = {"reward_root": normalize_reward_root(reward_root)}
    try:
        with open(temporary_path, "w", encoding="utf-8") as config_file:
            json.dump(payload, config_file, ensure_ascii=False, indent=2)
            config_file.write("\n")
        os.replace(temporary_path, config_path)
    except OSError:
        try:
            if os.path.isfile(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass
        raise


def load_telegram_setting():
    """Load Telegram token/chat ID from the local config file beside the EXE."""
    config_path = runtime_data_path(TELEGRAM_CONFIG_FILE)
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            payload = json.load(config_file)
    except FileNotFoundError:
        return TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(
            f"[SETTINGS WARNING] อ่าน {TELEGRAM_CONFIG_FILE} ไม่สำเร็จ "
            f"({type(error).__name__}); ยังไม่ได้ตั้งค่า Telegram"
        )
        return TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    if not isinstance(payload, dict):
        return TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    token = str(payload.get("bot_token") or "").strip()
    chat_id = str(payload.get("chat_id") or "").strip()
    return token, chat_id


def save_telegram_setting(token, chat_id):
    """Persist Telegram token/chat ID atomically beside the EXE."""
    config_path = runtime_data_path(TELEGRAM_CONFIG_FILE)
    temporary_path = config_path + ".tmp"
    payload = {
        "bot_token": str(token or "").strip(),
        "chat_id": str(chat_id or "").strip(),
    }
    try:
        with open(temporary_path, "w", encoding="utf-8") as config_file:
            json.dump(payload, config_file, ensure_ascii=False, indent=2)
            config_file.write("\n")
        os.replace(temporary_path, config_path)
    except OSError:
        try:
            if os.path.isfile(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass
        raise


def probe_reward_root_writable(reward_root, create=False):
    """Verify that reward_root exists and accepts a small temporary file."""
    normalized_root = normalize_reward_root(reward_root)
    if create:
        os.makedirs(normalized_root, exist_ok=True)
    if not os.path.isdir(normalized_root):
        raise FileNotFoundError(f"ไม่พบโฟลเดอร์ {normalized_root}")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=".cookie_reward_probe_",
        dir=normalized_root,
        delete=True,
    ) as probe_file:
        probe_file.write(b"ok")
        probe_file.flush()
    return normalized_root


def resolve_reward_root(configured_root):
    """Resolve one writable root for the whole worker run, with safe fallback."""
    fallback_root = default_reward_root()
    candidate_root = normalize_reward_root(configured_root)
    same_as_fallback = os.path.normcase(candidate_root) == os.path.normcase(
        fallback_root
    )

    try:
        return probe_reward_root_writable(
            candidate_root,
            create=same_as_fallback,
        ), None
    except (OSError, ValueError) as error:
        candidate_error = f"{type(error).__name__}: {error}"

    try:
        resolved_fallback = probe_reward_root_writable(fallback_root, create=True)
    except (OSError, ValueError) as fallback_error:
        raise RuntimeError(
            "ทั้งโฟลเดอร์ภาพที่เลือกและ reward_records ข้างโปรแกรมเขียนไม่ได้: "
            f"{type(fallback_error).__name__}: {fallback_error}"
        ) from fallback_error

    warning = (
        f"โฟลเดอร์ภาพที่เลือกใช้ไม่ได้ ({candidate_error}); "
        f"รอบการรันนี้จะใช้ {resolved_fallback}"
    )
    return resolved_fallback, warning


def safe_path_component(value, fallback="default"):
    """Keep account labels safe and readable as Windows folder names."""
    text = str(value or "").strip()
    safe = "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in text
    ).strip("._ ")
    return safe or fallback


ACTIVE_BOOST_TEMPLATE_IDS = frozenset()
ACTIVE_BOOST_TEMPLATE_LABELS = {}


def create_boost_template_manager():
    """Build the persistent Boots template manager used by UI and workers."""
    defaults = tuple(
        BoostTemplateDefault(
            template_id=template_id,
            label=label,
            source_path=Path(resource_path(source_filename)),
            source_frame_size=TEMPLATE_SOURCE_FRAME_SIZES.get(source_filename),
        )
        for template_id, label, source_filename in (
            (BOOST_TARGET_DOUBLE_COIN, "Double Coins", BOOST_TARGET_TEMPLATES[BOOST_TARGET_DOUBLE_COIN]),
            (BOOST_TARGET_BASE_SPEED, "Base Speed", BOOST_TARGET_TEMPLATES[BOOST_TARGET_BASE_SPEED]),
            (BOOST_TARGET_MAGNET, "Magnet", BOOST_TARGET_TEMPLATES[BOOST_TARGET_MAGNET]),
        )
    )
    return BoostTemplateManager(
        runtime_data_path(BOOST_TEMPLATE_STORAGE_DIR),
        defaults=defaults,
    )


def load_templates(boost_template_manager=None):
    """Load fixed UI templates plus all persistent Boots templates."""
    global ACTIVE_BOOST_TEMPLATE_IDS
    global ACTIVE_BOOST_TEMPLATE_LABELS

    templates = {}
    failed_paths = []
    for template_name in TEMPLATE_NAMES:
        template_path = resource_path(template_name)
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None or template.size == 0:
            failed_paths.append(template_path)
            continue

        source_frame_size = TEMPLATE_SOURCE_FRAME_SIZES.get(template_name)
        if source_frame_size is not None:
            source_width, source_height = source_frame_size
            reference_width, reference_height = TEMPLATE_REFERENCE_FRAME_SIZE
            template_height, template_width = template.shape[:2]
            normalized_size = (
                max(1, round(template_width * reference_width / source_width)),
                max(1, round(template_height * reference_height / source_height)),
            )
            template = cv2.resize(
                template,
                normalized_size,
                interpolation=cv2.INTER_AREA,
            )
            print(
                f"[TEMPLATE] ปรับ {template_name} จากเฟรมต้นฉบับ "
                f"{source_width}x{source_height} -> "
                f"{reference_width}x{reference_height}"
            )

        templates[template_name] = template
        height, width = template.shape[:2]
        print(f"[TEMPLATE] โหลด {template_name} สำเร็จ ({width}x{height})")

    boost_template_manager = (
        create_boost_template_manager()
        if boost_template_manager is None
        else boost_template_manager
    )
    active_boost_ids = []
    active_boost_labels = {}
    for template_info in boost_template_manager.templates:
        template_path = boost_template_manager.path_for(template_info)
        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None or template.size == 0:
            failed_paths.append(str(template_path))
            continue

        source_frame_size = template_info.source_frame_size
        if source_frame_size is not None:
            source_width, source_height = source_frame_size
            reference_width, reference_height = TEMPLATE_REFERENCE_FRAME_SIZE
            template_height, template_width = template.shape[:2]
            normalized_size = (
                max(1, round(template_width * reference_width / source_width)),
                max(1, round(template_height * reference_height / source_height)),
            )
            template = cv2.resize(
                template,
                normalized_size,
                interpolation=cv2.INTER_AREA,
            )
            print(
                f"[TEMPLATE] ปรับ Boots {template_info.label} จากเฟรมต้นฉบับ "
                f"{source_width}x{source_height} -> "
                f"{reference_width}x{reference_height}"
            )

        templates[template_info.template_id] = template
        active_boost_ids.append(template_info.template_id)
        active_boost_labels[template_info.template_id] = template_info.label
        height, width = template.shape[:2]
        print(
            f"[TEMPLATE] โหลด Boots {template_info.label} "
            f"({width}x{height})"
        )

    ACTIVE_BOOST_TEMPLATE_IDS = frozenset(active_boost_ids)
    ACTIVE_BOOST_TEMPLATE_LABELS = active_boost_labels

    if failed_paths:
        raise RuntimeError("ไม่สามารถโหลด Template: " + ", ".join(failed_paths))
    return templates


def build_region(left, top, width, height):
    return {
        "left": int(left),
        "top": int(top),
        "width": int(width),
        "height": int(height),
    }


def get_window_client_region(window):
    """Return the absolute screen region for one window's client area."""
    hwnd = getattr(window, "_hWnd", None)
    if hwnd is None:
        return None

    user32 = ctypes.windll.user32
    client_rect = RECT()
    if user32.GetClientRect(hwnd, ctypes.byref(client_rect)) == 0:
        return None

    top_left = POINT(client_rect.left, client_rect.top)
    bottom_right = POINT(client_rect.right, client_rect.bottom)
    if user32.ClientToScreen(hwnd, ctypes.byref(top_left)) == 0:
        return None
    if user32.ClientToScreen(hwnd, ctypes.byref(bottom_right)) == 0:
        return None

    width = int(bottom_right.x - top_left.x)
    height = int(bottom_right.y - top_left.y)
    if width <= 0 or height <= 0:
        return None
    return build_region(top_left.x, top_left.y, width, height)


def calibrate_screen(stop_event):
    """Collect four game-area corners and return one absolute capture rectangle."""
    clicked_points = []
    labels = (
        "ซ้ายบน (Top-Left)",
        "ขวาบน (Top-Right)",
        "ขวาล่าง (Bottom-Right)",
        "ซ้ายล่าง (Bottom-Left)",
    )

    print("=" * 58)
    print(" [ระบบตั้งค่าขอบเขตหน้าจอแบบ Calibration 4 มุม] ")
    print("=" * 58)
    print("คลิกขอบพื้นที่เกมตามลำดับ: ซ้ายบน -> ขวาบน -> ขวาล่าง -> ซ้ายล่าง")
    print("กด Ctrl+C เพื่อยกเลิกได้ทุกเวลา")
    print("-" * 58)

    def on_click(x, y, button, pressed):
        if not pressed or button != mouse.Button.left or len(clicked_points) >= 4:
            return None
        clicked_points.append((int(x), int(y)))
        index = len(clicked_points) - 1
        print(
            f"[CALIBRATION] มุมที่ {index + 1} {labels[index]} "
            f"-> X={int(x)}, Y={int(y)}"
        )
        if len(clicked_points) == 4:
            return False
        return None

    listener = mouse.Listener(on_click=on_click)
    listener.start()
    try:
        while listener.is_alive() and not stop_event.wait(0.10):
            pass
    finally:
        listener.stop()
        listener.join(timeout=1.0)

    if stop_event.is_set():
        return None
    if len(clicked_points) != 4:
        raise RuntimeError("Calibration ไม่สมบูรณ์: ต้องบันทึกให้ครบ 4 มุม")

    xs = [point[0] for point in clicked_points]
    ys = [point[1] for point in clicked_points]
    left = min(xs)
    top = min(ys)
    width = max(xs) - left
    height = max(ys) - top
    if width <= 0 or height <= 0:
        raise RuntimeError("Calibration ไม่ถูกต้อง: พื้นที่หน้าจอต้องกว้างและสูงกว่า 0")

    region = {"left": left, "top": top, "width": width, "height": height}
    print(f"[CALIBRATION] สำเร็จ: {region}")
    print("[CALIBRATION] ห้ามย้ายหรือย่อ/ขยายหน้าต่างเกมหลังจากนี้")
    return region


def capture_current_region_bgr(screen_capture, scan_region):
    """Capture the calibrated Windows region as one OpenCV BGR frame."""
    try:
        shot = screen_capture.grab(scan_region)
        bgra_frame = np.asarray(shot)
        if bgra_frame.size == 0:
            print("[CAPTURE ERROR] ภาพที่แคปได้ไม่มีข้อมูล")
            return None
        return cv2.cvtColor(bgra_frame, cv2.COLOR_BGRA2BGR)
    except (mss.exception.ScreenShotError, OSError, ValueError) as error:
        print(f"[CAPTURE ERROR] {type(error).__name__}: {error}")
        return None


WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001
PW_RENDERFULLCONTENT = 0x00000002
PW_CLIENTONLY = 0x00000001
BI_RGB = 0
DIB_RGB_COLORS = 0


def _window_client_region_from_hwnd(hwnd):
    """Return the absolute screen rectangle for a native client HWND."""
    if not hwnd or not ctypes.windll.user32.IsWindow(hwnd):
        return None
    client_rect = RECT()
    user32 = ctypes.windll.user32
    if not user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
        return None
    top_left = POINT(client_rect.left, client_rect.top)
    bottom_right = POINT(client_rect.right, client_rect.bottom)
    if not user32.ClientToScreen(hwnd, ctypes.byref(top_left)):
        return None
    if not user32.ClientToScreen(hwnd, ctypes.byref(bottom_right)):
        return None
    width = int(bottom_right.x - top_left.x)
    height = int(bottom_right.y - top_left.y)
    if width <= 0 or height <= 0:
        return None
    return build_region(top_left.x, top_left.y, width, height)


def _window_class_name(hwnd):
    buffer = ctypes.create_unicode_buffer(256)
    copied = ctypes.windll.user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value if copied else ""


def find_render_window_hwnd(game_window):
    """Find the LDPlayer child surface that accepts background mouse messages."""
    parent_hwnd = get_window_handle(game_window)
    if not parent_hwnd:
        return 0
    candidates = []
    enum_proc_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @enum_proc_type
    def enum_child(hwnd, _lparam):
        class_name = _window_class_name(hwnd).lower()
        if class_name in {"renderwindow", "therender"} or "render" in class_name:
            candidates.append(int(hwnd))
        return True

    ctypes.windll.user32.EnumChildWindows(parent_hwnd, enum_child, 0)
    for hwnd in candidates:
        region = _window_client_region_from_hwnd(hwnd)
        if region and region["width"] > 0 and region["height"] > 0:
            return hwnd
    return parent_hwnd if _window_client_region_from_hwnd(parent_hwnd) else 0


def capture_printwindow_client_bgr(hwnd):
    """Capture a native emulator surface without foregrounding it."""
    region = _window_client_region_from_hwnd(hwnd)
    if region is None:
        return None, None
    width, height = int(region["width"]), int(region["height"])
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    window_dc = user32.GetDC(hwnd)
    if not window_dc:
        return None, None
    memory_dc = gdi32.CreateCompatibleDC(window_dc)
    bitmap = gdi32.CreateCompatibleBitmap(window_dc, width, height)
    if not memory_dc or not bitmap:
        if memory_dc:
            gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)
        return None, None
    old_bitmap = gdi32.SelectObject(memory_dc, bitmap)
    try:
        ok = user32.PrintWindow(hwnd, memory_dc, PW_CLIENTONLY | PW_RENDERFULLCONTENT)
        if not ok:
            ok = user32.PrintWindow(hwnd, memory_dc, PW_CLIENTONLY)
        if not ok:
            return None, None

        class BitmapInfoHeader(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD),
            ]

        class BitmapInfo(ctypes.Structure):
            _fields_ = [("bmiHeader", BitmapInfoHeader), ("bmiColors", wintypes.DWORD * 3)]

        info = BitmapInfo()
        info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = BI_RGB
        buffer = ctypes.create_string_buffer(width * height * 4)
        copied = gdi32.GetDIBits(
            memory_dc, bitmap, 0, height, buffer, ctypes.byref(info), DIB_RGB_COLORS
        )
        if copied != height:
            return None, None
        bgra = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
        frame = cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)
        return frame, region
    finally:
        gdi32.SelectObject(memory_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(hwnd, window_dc)


def capture_window_client_bgr(screen_capture, game_window):
    """Capture the LDPlayer render surface using PrintWindow only."""
    render_hwnd = find_render_window_hwnd(game_window)
    if not render_hwnd:
        print("[CAPTURE ERROR] ไม่พบ LDPlayer RenderWindow/TheRender")
        return None, None
    frame, region = capture_printwindow_client_bgr(render_hwnd)
    if frame is None:
        print(f"[CAPTURE ERROR] PrintWindow ล้มเหลวสำหรับ HWND=0x{render_hwnd:X}")
    return frame, region


def convert_client_point_to_screen(
    scan_region,
    detected_center,
    detection_frame_size=None,
):
    """Convert a template-frame point into an absolute Windows screen point."""
    client_point = detected_center
    if detection_frame_size is not None:
        client_point = map_detection_point_to_source(
            detected_center,
            (int(scan_region["width"]), int(scan_region["height"])),
            detection_frame_size,
        )
    return (
        int(scan_region["left"] + client_point[0]),
        int(scan_region["top"] + client_point[1]),
    )


def scan_image_and_get_center(
    shared_frame,
    template,
    template_name,
    threshold=MATCH_THRESHOLD,
):
    """Return a match center from an existing shared frame without recapturing."""
    if shared_frame is None or shared_frame.size == 0:
        return None
    if template is None or template.size == 0:
        return None

    frame_height, frame_width = shared_frame.shape[:2]
    template_height, template_width = template.shape[:2]
    if template_height > frame_height or template_width > frame_width:
        print(
            f"[SCAN ERROR] {template_name} ใหญ่กว่าเฟรม "
            f"({template_width}x{template_height} > {frame_width}x{frame_height})"
        )
        return None

    try:
        result = cv2.matchTemplate(shared_frame, template, cv2.TM_CCOEFF_NORMED)
        _, maximum_value, _, maximum_location = cv2.minMaxLoc(result)
    except cv2.error as error:
        print(f"[SCAN ERROR] {template_name}: {error}")
        return None

    if maximum_value < threshold:
        return None
    return (
        int(maximum_location[0] + template_width / 2),
        int(maximum_location[1] + template_height / 2),
    )


@dataclass(frozen=True)
class AreaTemplateMatch:
    center: tuple
    top_left: tuple
    score: float
    search_area: tuple


def map_reference_rect(reference_rect, reference_size, target_size):
    """Map a left/top/right/bottom rectangle between client-frame sizes."""
    left, top, right, bottom = reference_rect
    reference_width, reference_height = reference_size
    target_width, target_height = target_size
    mapped_left = math.floor(left * target_width / reference_width)
    mapped_top = math.floor(top * target_height / reference_height)
    mapped_right = math.ceil(right * target_width / reference_width)
    mapped_bottom = math.ceil(bottom * target_height / reference_height)
    mapped_left = max(0, min(mapped_left, target_width))
    mapped_top = max(0, min(mapped_top, target_height))
    mapped_right = max(mapped_left, min(mapped_right, target_width))
    mapped_bottom = max(mapped_top, min(mapped_bottom, target_height))
    return mapped_left, mapped_top, mapped_right, mapped_bottom


def pad_reference_rect(reference_rect, padding, reference_size):
    left, top, right, bottom = reference_rect
    reference_width, reference_height = reference_size
    return (
        max(0, left - padding),
        max(0, top - padding),
        min(reference_width, right + padding),
        min(reference_height, bottom + padding),
    )


def scan_image_in_reference_area(
    shared_frame,
    template,
    template_name,
    reference_area,
    reference_size,
    threshold,
):
    """Match one normalized template only inside a mapped reference ROI."""
    if shared_frame is None or shared_frame.size == 0:
        return None
    if template is None or template.size == 0:
        return None

    frame_height, frame_width = shared_frame.shape[:2]
    search_area = map_reference_rect(
        reference_area,
        reference_size,
        (frame_width, frame_height),
    )
    left, top, right, bottom = search_area
    roi = shared_frame[top:bottom, left:right]
    template_height, template_width = template.shape[:2]
    if (
        roi.size == 0
        or template_height > roi.shape[0]
        or template_width > roi.shape[1]
    ):
        print(
            f"[SCAN ERROR] ROI ของ {template_name} เล็กกว่า template "
            f"({roi.shape[1] if roi.size else 0}x{roi.shape[0] if roi.size else 0} < "
            f"{template_width}x{template_height})"
        )
        return None

    try:
        result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _, maximum_value, _, maximum_location = cv2.minMaxLoc(result)
    except cv2.error as error:
        print(f"[SCAN ERROR] {template_name}: {error}")
        return None
    if maximum_value < threshold:
        return None

    top_left = (
        int(left + maximum_location[0]),
        int(top + maximum_location[1]),
    )
    return AreaTemplateMatch(
        center=(
            int(top_left[0] + template_width / 2),
            int(top_left[1] + template_height / 2),
        ),
        top_left=top_left,
        score=float(maximum_value),
        search_area=search_area,
    )


def choose_bonus_flow_delay():
    """Choose a weighted human-like delay before starting Bonus Quit."""
    roll = random.random()
    cumulative = 0.0
    selected_label, selected_range = BONUS_FLOW_DELAY_TIERS[-1][0], BONUS_FLOW_DELAY_TIERS[-1][2]
    for label, probability, delay_range in BONUS_FLOW_DELAY_TIERS:
        cumulative += probability
        if roll < cumulative:
            selected_label, selected_range = label, delay_range
            break
    return random.uniform(*selected_range), selected_label, selected_range


def check_captcha_by_freeze(
    first_frame,
    capture_second_frame,
    stop_event,
    pause_event=None,
    on_pause_interval=None,
):
    """Return (is_frozen, movement_pixels, latest_frame) for two Windows frames."""
    if first_frame is None or first_frame.size == 0:
        return None, None, None
    stopped, paused_during_check = wait_with_pause_status(
        stop_event,
        pause_event,
        CAPTCHA_FRAME_INTERVAL,
        on_pause_interval=on_pause_interval,
    )
    if stopped or paused_during_check:
        return None, None, None

    second_frame = capture_second_frame()
    if second_frame is None or second_frame.size == 0:
        print("[CAPTCHA CHECK] แคปเฟรมที่สองไม่สำเร็จ จึงยังไม่สรุปผล")
        return None, None, None
    if first_frame.shape != second_frame.shape:
        print(
            "[CAPTCHA CHECK] ขนาดสองเฟรมไม่ตรงกัน "
            f"({first_frame.shape} != {second_frame.shape})"
        )
        return None, None, second_frame

    try:
        first_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        second_gray = cv2.cvtColor(second_frame, cv2.COLOR_BGR2GRAY)
        difference = cv2.absdiff(first_gray, second_gray)
        _, threshold_image = cv2.threshold(
            difference,
            CAPTCHA_DIFF_THRESHOLD,
            255,
            cv2.THRESH_BINARY,
        )
        movement_pixels = int(np.count_nonzero(threshold_image))
    except cv2.error as error:
        print(f"[CAPTCHA CHECK ERROR] {error}")
        return None, None, second_frame

    return movement_pixels < CAPTCHA_MOVEMENT_THRESHOLD, movement_pixels, second_frame


class TelegramNotifier:
    """Send bounded-time Telegram messages and screenshots through one HTTP session."""

    def __init__(self, token, chat_id, message_prefix=""):
        self.token = token
        self.chat_id = chat_id
        self.message_prefix = message_prefix.strip()
        self.session = requests.Session()
        self._aborted = threading.Event()

    @property
    def is_configured(self):
        return bool(self.token and self.chat_id)

    def send_message(self, message):
        if not self.is_configured:
            print("[TELEGRAM] ข้ามการส่งข้อความ เพราะยังไม่ได้ตั้งค่า Token/Chat ID")
            return False
        if self._aborted.is_set():
            return False
        if self.message_prefix:
            message = f"{self.message_prefix} {message}"
        try:
            response = self.session.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                data={"chat_id": self.chat_id, "text": message},
                timeout=10,
            )
            response.raise_for_status()
            print("[TELEGRAM] ส่งข้อความสำเร็จ")
            return True
        except requests.RequestException as error:
            print(f"[TELEGRAM ERROR] ส่งข้อความไม่สำเร็จ ({type(error).__name__})")
            return False

    def send_message_async(self, message):
        """Send a non-critical message without delaying worker shutdown."""
        if not self.is_configured:
            return False

        def send_in_background():
            background_notifier = TelegramNotifier(
                self.token,
                self.chat_id,
                message_prefix=self.message_prefix,
            )
            try:
                background_notifier.send_message(message)
            finally:
                background_notifier.close()

        threading.Thread(
            target=send_in_background,
            name="TelegramStopNotification",
            daemon=True,
        ).start()
        return True

    def send_screenshot(self, frame, caption):
        if not self.is_configured:
            return False
        if self._aborted.is_set():
            return False
        if frame is None or frame.size == 0:
            print("[TELEGRAM] ไม่มี Shared Frame สำหรับส่งรูป")
            return False
        try:
            if self.message_prefix:
                caption = f"{self.message_prefix} {caption}"
            encoded, buffer = cv2.imencode(
                ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            )
            if not encoded:
                print("[TELEGRAM] แปลง Shared Frame เป็น JPG ไม่สำเร็จ")
                return False
            response = self.session.post(
                f"https://api.telegram.org/bot{self.token}/sendPhoto",
                data={"chat_id": self.chat_id, "caption": caption},
                files={"photo": ("screen.jpg", buffer.tobytes(), "image/jpeg")},
                timeout=20,
            )
            response.raise_for_status()
            print("[TELEGRAM] ส่งรูปสำเร็จ")
            return True
        except (cv2.error, requests.RequestException) as error:
            print(f"[TELEGRAM ERROR] ส่งรูปไม่สำเร็จ ({type(error).__name__})")
            return False

    def send_alert(self, reason, frame, is_captcha=False, movement_pixels=None):
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if is_captcha:
            movement_text = (
                f" ({movement_pixels:,} movement pixels)"
                if movement_pixels is not None
                else ""
            )
            message = (
                "[ALERT] สงสัยว่าติดหน้าต่าง CAPTCHA\n"
                f"เวลา: {now_text}\n"
                f"สาเหตุ: {reason}{movement_text}"
            )
        else:
            message = (
                f"[ALERT] {BOT_NAME}\n"
                f"เวลา: {now_text}\n"
                f"สาเหตุ: {reason}"
            )
        self.send_message(message)
        self.send_screenshot(frame, "ภาพล่าสุดจากพื้นที่เกมที่ Calibrate")

    def close(self):
        self.session.close()

    def abort(self):
        """Interrupt in-flight Telegram requests when the user presses Stop."""
        self._aborted.set()
        self.session.close()


class FatigueState:
    """Keep PLAY/OK round counters for the lifetime of this process."""

    def __init__(self):
        self._lock = threading.Lock()
        self._generation = 0
        self._reset_event = threading.Event()
        self.play_count = 0
        self.ok_count = 0
        self.target_play_round = random.randint(*PLAY_FATIGUE_ROUND_RANGE)
        self.target_ok_round = random.randint(*OK_FATIGUE_ROUND_RANGE)

    def reset(self):
        """Reset only the fatigue counters and choose fresh pause targets."""
        with self._lock:
            self.play_count = 0
            self.ok_count = 0
            self.target_play_round = random.randint(*PLAY_FATIGUE_ROUND_RANGE)
            self.target_ok_round = random.randint(*OK_FATIGUE_ROUND_RANGE)
            self._generation += 1
            self._reset_event.set()
            targets = (self.target_play_round, self.target_ok_round)
        print(
            "[FATIGUE] รีเซ็ตจำนวนรอบ PLAY/OK แล้ว "
            f"เป้าหมายใหม่ PLAY={targets[0]} รอบ, OK={targets[1]} รอบ"
        )

    def snapshot(self):
        """Read counters consistently while the worker may be updating them."""
        with self._lock:
            return (
                self.play_count,
                self.ok_count,
                self.target_play_round,
                self.target_ok_round,
            )

    @property
    def reset_event(self):
        return self._reset_event

    def consume_reset_event(self):
        was_set = self._reset_event.is_set()
        if was_set:
            self._reset_event.clear()
        return was_set

    def is_decision_current(self, decision):
        if decision is None or len(decision) < 3:
            return True
        with self._lock:
            return decision[2] == self._generation

    def prepare_delay(self, action):
        normal_delay = random.uniform(*action.pre_click_delay)
        with self._lock:
            generation = self._generation
            if action.name == "PLAY":
                next_count = self.play_count + 1
                target_count = self.target_play_round
            elif action.name == "OK":
                next_count = self.ok_count + 1
                target_count = self.target_ok_round
            else:
                return normal_delay, None

        is_fatigue_round = next_count >= target_count
        delay = random.uniform(*FATIGUE_DELAY_RANGE) if is_fatigue_round else normal_delay
        if is_fatigue_round:
            print(
                f"[FATIGUE] {action.name} รอบที่ {next_count} ตรงเป้าหมาย "
                f"พักยาว {delay:.2f}s ก่อนคลิก"
            )
        else:
            print(
                f"[FATIGUE] {action.name} รอบถัดไป "
                f"{next_count}/{target_count} ใช้ Reaction Time ปกติ"
            )
        return delay, (action.name, is_fatigue_round, generation)

    def commit_click(self, decision):
        if decision is None:
            return None
        action_name, was_fatigue_round = decision[:2]
        decision_generation = decision[2] if len(decision) > 2 else None
        with self._lock:
            if action_name == "PLAY":
                self.play_count += 1
                current_count = self.play_count
                target_count = self.target_play_round
                if decision_generation != self._generation:
                    was_fatigue_round = current_count >= target_count
                if was_fatigue_round:
                    self.target_play_round = current_count + random.randint(
                        *PLAY_FATIGUE_ROUND_RANGE
                    )
                next_target = self.target_play_round
            else:
                self.ok_count += 1
                current_count = self.ok_count
                target_count = self.target_ok_round
                if decision_generation != self._generation:
                    was_fatigue_round = current_count >= target_count
                if was_fatigue_round:
                    self.target_ok_round = current_count + random.randint(
                        *OK_FATIGUE_ROUND_RANGE
                    )
                next_target = self.target_ok_round

        print(f"[COUNT] {action_name} กดสำเร็จสะสม {current_count} รอบ")
        if was_fatigue_round:
            print(f"[FATIGUE] เป้าหมายพักยาวครั้งถัดไป: รอบที่ {next_target}")
        return current_count


def calculate_safe_click_area(action, detected_size):
    """Return the usable inner rectangle for a matched button template."""
    if action.click_area is not None:
        x_min, x_max, y_min, y_max = action.click_area
        return (
            max(1, int(x_max - x_min + 1)),
            max(1, int(y_max - y_min + 1)),
        )

    template_width, template_height = detected_size
    width_ratio, height_ratio = action.safe_click_ratio
    return (
        max(1, int(round(template_width * width_ratio))),
        max(1, int(round(template_height * height_ratio))),
    )


def get_click_offset_bounds(action, detected_size):
    """Return inclusive x/y offset bounds relative to the matched template center."""
    if action.click_area is not None:
        return action.click_area

    safe_width, safe_height = calculate_safe_click_area(action, detected_size)
    half_width = max(0.0, (safe_width - 1) / 2.0)
    half_height = max(0.0, (safe_height - 1) / 2.0)
    return (-half_width, half_width, -half_height, half_height)


def sample_safe_click_offset(action, detected_size=None):
    """Sample a broad, center-weighted point inside the matched button area."""
    if detected_size is None:
        return (
            int(random.gauss(0, action.jitter / 2.5)),
            int(random.gauss(0, action.jitter / 3.0)),
            None,
        )

    x_min, x_max, y_min, y_max = get_click_offset_bounds(action, detected_size)
    safe_width, safe_height = calculate_safe_click_area(action, detected_size)

    # Beta(2, 2) covers the usable button area while gently favoring its center.
    offset_x = int(round(x_min + random.betavariate(2.0, 2.0) * (x_max - x_min)))
    offset_y = int(round(y_min + random.betavariate(2.0, 2.0) * (y_max - y_min)))
    return offset_x, offset_y, (safe_width, safe_height)


def build_area_click_target(
    name,
    reference_area,
    reference_size,
    detection_frame_size,
    pre_click_delay,
):
    """Build a one-click action whose sampled points stay inside a mapped area."""
    left, top, right, bottom = map_reference_rect(
        reference_area,
        reference_size,
        detection_frame_size,
    )
    if right <= left or bottom <= top:
        raise ValueError(f"พื้นที่คลิก {name} ไม่ถูกต้อง: {(left, top, right, bottom)}")
    center_x = (left + right - 1) // 2
    center_y = (top + bottom - 1) // 2
    click_area = (
        left - center_x,
        right - 1 - center_x,
        top - center_y,
        bottom - 1 - center_y,
    )
    action = ButtonAction(
        name=name,
        template_name="",
        fixed_position=(center_x, center_y),
        pre_click_delay=pre_click_delay,
        post_click_delay=0.0,
        minimum_clicks=1,
        maximum_clicks=1,
        jitter=0,
        bounds=None,
        safe_click_ratio=(1.0, 1.0),
        click_area=click_area,
    )
    return action, (center_x, center_y), (right - left, bottom - top)


def build_start_jump_click_groups(total_clicks):
    """Split jump clicks into mostly single taps with occasional double/triple taps."""
    remaining = max(0, int(total_clicks))
    groups = []
    while remaining:
        if (
            remaining >= 3
            and random.random() < START_JUMP_TRIPLE_CLICK_PROBABILITY
        ):
            group_size = 3
        elif (
            remaining >= 2
            and random.random() < START_JUMP_DOUBLE_CLICK_PROBABILITY
        ):
            group_size = 2
        else:
            group_size = 1
        groups.append(group_size)
        remaining -= group_size
    return groups


def choose_start_jump_flow_duration():
    """Choose the opening jump window, usually 4-7s with a small late tail."""
    roll = random.random()
    cumulative = 0.0
    selected_label = START_JUMP_FLOW_DURATION_TIERS[-1][0]
    selected_range = START_JUMP_FLOW_DURATION_TIERS[-1][2]
    for label, probability, duration_range in START_JUMP_FLOW_DURATION_TIERS:
        cumulative += probability
        if roll <= cumulative:
            selected_label, selected_range = label, duration_range
            break
    return selected_label, selected_range, random.uniform(*selected_range)


def build_start_jump_group_gaps(click_groups, target_duration):
    """Create varied gaps that fit the planned opening jump window."""
    gap_count = max(0, len(click_groups) - 1)
    if gap_count == 0:
        return []

    hold_mid = sum(START_JUMP_HOLD_DELAY_RANGE) / 2.0
    inter_mid = sum(START_JUMP_INTER_CLICK_DELAY_RANGE) / 2.0
    estimated_click_time = sum(
        group_size * hold_mid + max(0, group_size - 1) * inter_mid
        for group_size in click_groups
    )
    min_gap, max_gap = START_JUMP_GROUP_GAP_RANGE
    target_gap_total = max(
        gap_count * min_gap,
        float(target_duration) - estimated_click_time,
    )
    target_gap_total = min(target_gap_total, gap_count * max_gap)
    extra_gap_total = max(0.0, target_gap_total - gap_count * min_gap)
    gaps = [min_gap] * gap_count
    capacity = max_gap - min_gap
    indices = list(range(gap_count))
    random.shuffle(indices)
    remaining_extra = extra_gap_total
    for position, index in enumerate(indices):
        remaining_slots = gap_count - position - 1
        minimum_take = max(0.0, remaining_extra - remaining_slots * capacity)
        maximum_take = min(capacity, remaining_extra)
        take = random.uniform(minimum_take, maximum_take)
        gaps[index] += take
        remaining_extra -= take
    return [
        round(min(max(gap, min_gap), max_gap), 4)
        for gap in gaps
    ]


def acquire_click_lock(click_lock, stop_event, pause_event=None):
    """Acquire the shared physical-mouse lock without blocking Stop/Pause."""
    if click_lock is None:
        return True

    while not stop_event.is_set():
        if pause_event is not None and pause_event.is_set():
            return False
        if click_lock.acquire(timeout=PAUSE_POLL_INTERVAL):
            return True
    return False


def click_human_like(
    window,
    action,
    stop_event,
    pause_event=None,
    on_pause_interval=None,
    detected_center=None,
    scan_region=None,
    detected_size=None,
    detection_frame_size=None,
    hold_delay_range=None,
    inter_click_delay_range=None,
):
    """Click using the existing timing logic through the background render HWND."""
    render_hwnd = find_render_window_hwnd(window)
    if not render_hwnd:
        print("[INPUT ERROR] ไม่พบ LDPlayer RenderWindow/TheRender; ยกเลิกการคลิก")
        return False
    using_detected_center = detected_center is not None and scan_region is not None
    if using_detected_center:
        source_size = (int(scan_region["width"]), int(scan_region["height"]))
        if detection_frame_size is None:
            detection_frame_size = source_size
        detection_scale_x, detection_scale_y = detection_to_source_scale(
            source_size,
            detection_frame_size,
        )
        client_x, client_y = map_detection_point_to_source(
            detected_center,
            source_size,
            detection_frame_size,
        )
        client_x, client_y = map_detection_point_to_source(
            detected_center,
            source_size,
            detection_frame_size,
        )
        base_x, base_y = int(client_x), int(client_y)
        x_min, y_min = 0, 0
        x_max = int(scan_region["width"] - 1)
        y_max = int(scan_region["height"] - 1)
        window_x, window_y = base_x, base_y
    else:
        # Fixed coordinates are stored in the template reference frame.  The
        # PrintWindow render surface can have a different client size, so map
        # them exactly like a detected template point before sending them to
        # the render child via PostMessage.
        if scan_region is not None:
            source_width = int(scan_region["width"])
            source_height = int(scan_region["height"])
        else:
            render_region = _window_client_region_from_hwnd(render_hwnd)
            source_width = int(render_region["width"]) if render_region else TEMPLATE_REFERENCE_FRAME_SIZE[0]
            source_height = int(render_region["height"]) if render_region else TEMPLATE_REFERENCE_FRAME_SIZE[1]
        reference_width, reference_height = TEMPLATE_REFERENCE_FRAME_SIZE
        fixed_scale_x = source_width / reference_width
        fixed_scale_y = source_height / reference_height
        base_x = int(round(action.fixed_position[0] * fixed_scale_x))
        base_y = int(round(action.fixed_position[1] * fixed_scale_y))
        window_x = int(action.fixed_position[0])
        window_y = int(action.fixed_position[1])
        client_x = None
        client_y = None
        detection_scale_x = 1.0
        detection_scale_y = 1.0
    click_count = random.randint(action.minimum_clicks, action.maximum_clicks)
    actual_hold_delay_range = (
        MOUSE_HOLD_DELAY_RANGE
        if hold_delay_range is None
        else hold_delay_range
    )
    actual_inter_click_delay_range = (
        INTER_CLICK_DELAY_RANGE
        if inter_click_delay_range is None
        else inter_click_delay_range
    )
    mouse_is_down = False
    current_x = base_x
    current_y = base_y

    if using_detected_center:
        safe_area = (
            calculate_safe_click_area(action, detected_size)
            if detected_size is not None
            else None
        )
        if action.click_area is not None:
            spread_text = (
                f"click area {safe_area[0]}x{safe_area[1]}px "
                f"offset={action.click_area}"
            )
        else:
            spread_text = (
                f"safe area {safe_area[0]}x{safe_area[1]}px"
                if safe_area is not None
                else f"legacy jitter ±{action.jitter}px"
            )
    else:
        spread_text = f"legacy jitter ±{action.jitter}px"

    print(
        f"[CLICK] {action.name} screen=({base_x}, {base_y}) "
        f"window=({window_x}, {window_y}) "
        f"detect=({detected_center[0]}, {detected_center[1]}) "
        f"client=({client_x}, {client_y}) "
        if using_detected_center
        else f"[CLICK] {action.name} screen=({base_x}, {base_y}) window=({window_x}, {window_y}) "
    )
    print(
        f"[CLICK] {action.name} "
        f"จำนวน {click_count} ครั้ง | {spread_text}"
    )
    try:
        for click_index in range(click_count):
            if stop_event.is_set():
                return False
            if wait_with_pause(
                stop_event,
                pause_event,
                0,
                on_pause_interval=on_pause_interval,
            ):
                return False
            offset_x, offset_y, _ = sample_safe_click_offset(
                action,
                detected_size if using_detected_center else None,
            )
            if using_detected_center:
                current_x = max(
                    x_min,
                    min(base_x + int(round(offset_x * detection_scale_x)), x_max),
                )
                current_y = max(
                    y_min,
                    min(base_y + int(round(offset_y * detection_scale_y)), y_max),
                )
            else:
                target_rel_x = action.fixed_position[0] + offset_x
                target_rel_y = action.fixed_position[1] + offset_y

                if action.bounds:
                    x_min, x_max, y_min, y_max = action.bounds
                    target_rel_x = max(x_min, min(target_rel_x, x_max))
                    target_rel_y = max(y_min, min(target_rel_y, y_max))

                # PostMessage receives coordinates relative to the render
                # child, not absolute desktop coordinates.
                current_x = int(target_rel_x)
                current_y = int(target_rel_y)
            hold_duration = random.uniform(*actual_hold_delay_range)

            lp = ((int(current_y) & 0xFFFF) << 16) | (int(current_x) & 0xFFFF)
            user32 = ctypes.windll.user32
            user32.PostMessageW(render_hwnd, WM_MOUSEMOVE, 0, lp)
            user32.PostMessageW(render_hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
            mouse_is_down = True
            hold_deadline = time.monotonic() + hold_duration
            interrupted = False
            while True:
                if stop_event.is_set() or (
                    pause_event is not None and pause_event.is_set()
                ):
                    interrupted = True
                    break
                remaining_hold = hold_deadline - time.monotonic()
                if remaining_hold <= 0:
                    break
                if stop_event.wait(min(PAUSE_POLL_INTERVAL, remaining_hold)):
                    interrupted = True
                    break
            user32.PostMessageW(render_hwnd, WM_MOUSEMOVE, MK_LBUTTON, lp)
            user32.PostMessageW(render_hwnd, WM_LBUTTONUP, 0, lp)
            mouse_is_down = False
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] -> CLICK {action.name} "
                f"({current_x}, {current_y}) แช่ {hold_duration:.3f}s"
            )
            if interrupted:
                return False
            if click_index + 1 < click_count:
                if wait_with_pause(
                    stop_event,
                    pause_event,
                    random.uniform(*actual_inter_click_delay_range),
                    on_pause_interval=on_pause_interval,
                ):
                    return False
        return True
    finally:
        if mouse_is_down:
            try:
                lp = ((int(current_y) & 0xFFFF) << 16) | (int(current_x) & 0xFFFF)
                ctypes.windll.user32.PostMessageW(render_hwnd, WM_LBUTTONUP, 0, lp)
            except OSError:
                pass


@dataclass(frozen=True)
class GameWindowInfo:
    """Stable information used to select one LDPlayer instance by HWND."""

    hwnd: int
    title: str
    left: int
    top: int
    width: int
    height: int
    is_minimized: bool

    @property
    def display_label(self):
        state = "minimized" if self.is_minimized else "visible"
        return (
            f"{self.title} | HWND=0x{self.hwnd:X} | "
            f"{self.width}x{self.height} @ ({self.left}, {self.top}) | {state}"
        )


def get_window_handle(window):
    """Read a pygetwindow HWND as a regular positive Python integer."""
    return int(getattr(window, "_hWnd", 0) or 0)


def get_window_class_name(window):
    """Read the native class name used to identify an emulator instance."""
    hwnd = get_window_handle(window)
    if hwnd <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(256)
    copied = ctypes.windll.user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value if copied else ""


def get_game_windows():
    """Return candidate LDPlayer or MuMu windows without choosing arbitrarily."""
    all_windows = gw.getAllWindows()
    expected_title = GAME_WINDOW_TITLE.lower()
    ldplayer_matches = []
    mumu_matches = []
    exact_or_primary_matches = []
    fallback_matches = []

    for window in all_windows:
        title = (window.title or "").strip()
        title_text = title.lower()
        hwnd = get_window_handle(window)
        if not title_text or hwnd <= 0:
            continue

        window_class = get_window_class_name(window)
        if window_class == LDPLAYER_WINDOW_CLASS:
            ldplayer_matches.append(window)
            continue
        if (window_class.startswith(MUMU_WINDOW_CLASS_PREFIXES)
                and any(keyword in title_text for keyword in MUMU_WINDOW_TITLE_KEYWORDS)):
            mumu_matches.append(window)
            continue
        if any(keyword in title_text for keyword in MUMU_WINDOW_TITLE_KEYWORDS):
            mumu_matches.append(window)
            continue
        if title_text == expected_title or expected_title in title_text:
            exact_or_primary_matches.append(window)
            continue
        if any(keyword in title_text for keyword in WINDOW_TITLE_FALLBACK_KEYWORDS):
            fallback_matches.append(window)

    # The native class identifies every LDPlayer instance regardless of its
    # user-chosen instance name, e.g. "main_cookierun" or "second". Title
    # matching remains only as a compatibility fallback for older LDPlayer.
    candidates = (
        ldplayer_matches
        or mumu_matches
        or exact_or_primary_matches
        or fallback_matches
    )
    unique_windows = {}
    for window in candidates:
        unique_windows[get_window_handle(window)] = window
    return tuple(
        unique_windows[hwnd]
        for hwnd in sorted(
            unique_windows,
            key=lambda item: (
                int(unique_windows[item].left),
                int(unique_windows[item].top),
                item,
            ),
        )
    )


def list_game_window_info():
    """Build UI-safe labels for every currently discovered LDPlayer window."""
    return tuple(
        GameWindowInfo(
            hwnd=get_window_handle(window),
            title=(window.title or "").strip(),
            left=int(window.left),
            top=int(window.top),
            width=int(window.width),
            height=int(window.height),
            is_minimized=bool(window.isMinimized),
        )
        for window in get_game_windows()
    )


def find_game_window(target_window_hwnd=None):
    """Find a selected LDPlayer HWND, or preserve the legacy largest-window path."""
    candidates = get_game_windows()
    if target_window_hwnd is not None:
        target_window_hwnd = int(target_window_hwnd)
        for window in candidates:
            if get_window_handle(window) == target_window_hwnd:
                return window
        return None
    if not candidates:
        return None
    return max(candidates, key=lambda window: window.width * window.height)


@dataclass(frozen=True)
class BoostSettingsSnapshot:
    """One immutable set of Boots choices used for one Boots screen."""

    boost_mode: str
    random_boost_percent: float
    boost_target: str


@dataclass(frozen=True)
class ActionSelection:
    action: object | None
    center: tuple | None
    any_button_visible: bool
    boots_visible: bool = False
    boots_ready: bool = False
    boots_purchase_pending: bool = False
    fallback_visible: bool = False
    fallback_exhausted: bool = False
    fallback_visible_actions: tuple = ()


def should_roll_boost_this_boots_screen(boost_mode, random_boost_percent):
    if boost_mode == BOOST_MODE_NEVER:
        return False
    if boost_mode == BOOST_MODE_RANDOM:
        return random.random() < max(0.0, min(100.0, random_boost_percent)) / 100.0
    return True


def get_boost_target_template(boost_target, template_cache=None):
    """Resolve a selected persistent Boots template for this worker."""
    if template_cache is None:
        return BOOST_TARGET_TEMPLATES.get(
            boost_target,
            BOOST_TARGET_TEMPLATES[DEFAULT_BOOST_TARGET],
        )
    if boost_target in ACTIVE_BOOST_TEMPLATE_IDS and boost_target in template_cache:
        return boost_target
    if ACTIVE_BOOST_TEMPLATE_IDS:
        return sorted(ACTIVE_BOOST_TEMPLATE_IDS)[0]
    return None


def get_boost_target_label(boost_target):
    """Return a readable label for a persistent or legacy Boots target."""
    if boost_target in ACTIVE_BOOST_TEMPLATE_LABELS:
        return ACTIVE_BOOST_TEMPLATE_LABELS[boost_target]
    return {
        BOOST_TARGET_DOUBLE_COIN: "Double Coins",
        BOOST_TARGET_BASE_SPEED: "Base Speed",
        BOOST_TARGET_MAGNET: "Magnet",
    }.get(boost_target, str(boost_target))


def play_context_from_boots_visible(boots_visible):
    return "boots" if boots_visible else "normal"


def is_action_on_cooldown(action, last_clicks, now):
    last_click_time = last_clicks.get(action.name)
    return (
        last_click_time is not None
        and now - last_click_time < REPEAT_CLICK_COOLDOWN
    )


def find_boots_screen_action(
    shared_frame,
    template_cache,
    last_clicks,
    now,
    enabled_features,
    boots_purchase_pending=False,
    should_roll_boost=True,
    multi_buy_attempts=0,
    boost_target=DEFAULT_BOOST_TARGET,
):
    boots_center = scan_image_and_get_center(
        shared_frame,
        template_cache[BOOTS_SCREEN_TEMPLATE],
        BOOTS_SCREEN_TEMPLATE,
    )
    multi_buy_center = scan_image_and_get_center(
        shared_frame,
        template_cache[ACTION_BY_NAME["MULTI_BUY"].template_name],
        ACTION_BY_NAME["MULTI_BUY"].template_name,
    )
    boots_visible = boots_center is not None or multi_buy_center is not None
    if not boots_visible:
        return ActionSelection(None, None, False)

    play_action = ACTION_BY_NAME["PLAY"]
    if not should_roll_boost:
        if enabled_features.get("PLAY", False):
            play_center = scan_image_and_get_center(
                shared_frame,
                template_cache[play_action.template_name],
                play_action.template_name,
            )
            if play_center is not None and not is_action_on_cooldown(
                play_action,
                last_clicks,
                now,
            ):
                return ActionSelection(
                    play_action,
                    play_center,
                    True,
                    boots_visible=True,
                    boots_ready=True,
                )
        return ActionSelection(
            None,
            None,
            True,
            boots_visible=True,
            boots_ready=True,
        )

    boost_target_template = get_boost_target_template(boost_target, template_cache)
    boost_target_center = None
    if boost_target_template is not None:
        boost_target_center = scan_image_and_get_center(
            shared_frame,
            template_cache[boost_target_template],
            boost_target_template,
        )
    if boost_target_center is not None:
        if enabled_features.get("PLAY", False):
            play_center = scan_image_and_get_center(
                shared_frame,
                template_cache[play_action.template_name],
                play_action.template_name,
            )
            if play_center is not None and not is_action_on_cooldown(
                play_action,
                last_clicks,
                now,
            ):
                return ActionSelection(
                    play_action,
                    play_center,
                    True,
                    boots_visible=True,
                    boots_ready=True,
                )
        return ActionSelection(
            None,
            None,
            True,
            boots_visible=True,
            boots_ready=True,
        )

    if boots_purchase_pending:
        multi_buy_action = ACTION_BY_NAME["MULTI_BUY"]
        if (
            multi_buy_center is not None
            and multi_buy_attempts < MULTI_BUY_MAX_ATTEMPTS
            and enabled_features.get("MULTI_BUY", True)
            and not is_action_on_cooldown(multi_buy_action, last_clicks, now)
        ):
            return ActionSelection(
                multi_buy_action,
                multi_buy_center,
                True,
                boots_visible=True,
                boots_purchase_pending=True,
            )
        return ActionSelection(
            None,
            None,
            True,
            boots_visible=True,
            boots_purchase_pending=True,
        )

    for action in BOOTS_BUTTON_ACTIONS:
        if not enabled_features.get(action.name, True):
            continue
        if action.name == "MULTI_BUY":
            center = multi_buy_center
        else:
            center = scan_image_and_get_center(
                shared_frame,
                template_cache[action.template_name],
                action.template_name,
            )
        if center is None:
            continue
        if is_action_on_cooldown(action, last_clicks, now):
            continue
        return ActionSelection(
            action,
            center,
            True,
            boots_visible=True,
        )

    return ActionSelection(None, None, True, boots_visible=True)


def find_selected_action(
    shared_frame,
    template_cache,
    last_clicks,
    now,
    enabled_features=None,
    boots_purchase_pending=False,
    should_roll_boost=True,
    multi_buy_attempts=0,
    boost_target=DEFAULT_BOOST_TARGET,
    fallback_attempts=None,
):
    feature_state = ENABLE_CONFIG if enabled_features is None else enabled_features
    boots_selection = find_boots_screen_action(
        shared_frame,
        template_cache,
        last_clicks,
        now,
        feature_state,
        boots_purchase_pending=boots_purchase_pending,
        should_roll_boost=should_roll_boost,
        multi_buy_attempts=multi_buy_attempts,
        boost_target=boost_target,
    )
    if boots_selection.boots_visible:
        return boots_selection

    any_button_visible = False
    for action in BUTTON_ACTIONS:
        if not feature_state.get(action.name, False):
            continue
        center = scan_image_and_get_center(
            shared_frame,
            template_cache[action.template_name],
            action.template_name,
        )
        if center is None:
            continue
        any_button_visible = True
        if is_action_on_cooldown(action, last_clicks, now):
            continue
        return ActionSelection(action, center, any_button_visible)

    if fallback_attempts is None:
        fallback_attempts = {}

    # The in-game pause/stop control is visually close enough to the popup
    # close button that it can produce a false CLOSE match. It is a state
    # marker, not a clickable action. Keep CONFIRM_MAIN available for a real
    # popup, but suppress CLOSE while the game-play stop control is visible.
    stop_center = (
        scan_image_and_get_center(
            shared_frame,
            template_cache[STOP_TEMPLATE],
            STOP_TEMPLATE,
            threshold=STOP_GUARD_MATCH_THRESHOLD,
        )
    )
    stop_visible = stop_center is not None
    fallback_visible = False
    fallback_exhausted = False
    fallback_matches = []
    for action in FALLBACK_BUTTON_ACTIONS:
        if not feature_state.get(action.name, False):
            continue
        center = scan_image_and_get_center(
            shared_frame,
            template_cache[action.template_name],
            action.template_name,
        )
        if center is None:
            continue
        if action.name == "CLOSE" and stop_center is not None:
            center_distance = (
                (center[0] - stop_center[0]) ** 2
                + (center[1] - stop_center[1]) ** 2
            ) ** 0.5
            if center_distance <= STOP_CLOSE_CENTER_DISTANCE:
                print(
                    f"[GUARD] suppress CLOSE at {center}; "
                    f"STOP candidate at {stop_center} "
                    f"distance={center_distance:.1f}px"
                )
                continue
        fallback_matches.append((action, center))

    fallback_visible = bool(fallback_matches)
    any_button_visible = any_button_visible or fallback_visible or stop_visible
    fallback_visible_actions = tuple(action.name for action, _ in fallback_matches)
    for action, center in fallback_matches:
        if fallback_attempts.get(action.name, 0) >= FALLBACK_MAX_ATTEMPTS:
            fallback_exhausted = True
            continue
        if is_action_on_cooldown(action, last_clicks, now):
            continue
        return ActionSelection(
            action,
            center,
            any_button_visible,
            fallback_visible=True,
            fallback_visible_actions=fallback_visible_actions,
        )
    return ActionSelection(
        None,
        None,
        any_button_visible,
        fallback_visible=fallback_visible,
        fallback_exhausted=fallback_exhausted,
        fallback_visible_actions=fallback_visible_actions,
    )


def should_send_no_button_alert(
    now,
    last_button_seen_time,
    last_healthy_activity_time,
    last_alert_time,
):
    """Alert only when both buttons and visible game activity are absent."""
    return (
        now - last_button_seen_time >= NO_BUTTON_ALERT_AFTER
        and now - last_healthy_activity_time >= NO_BUTTON_ALERT_AFTER
        and now - last_alert_time >= TELEGRAM_COOLDOWN
    )


def run_bot_loop(
    scan_region,
    screen_capture,
    template_cache,
    notifier,
    stop_event,
    pause_event=None,
    fatigue=None,
    feature_provider=None,
    calibration_mode=CALIBRATION_MODE_DEFAULT,
    target_run_count=None,
    boost_mode=BOOST_MODE_ALWAYS,
    random_boost_percent=DEFAULT_RANDOM_BOOST_PERCENT,
    boost_target=DEFAULT_BOOST_TARGET,
    boost_provider=None,
    reward_root=None,
    target_window_hwnd=None,
    account_label="",
    click_lock=None,
):
    fatigue = FatigueState() if fatigue is None else fatigue
    if target_run_count is not None and target_run_count <= 0:
        target_run_count = None
    feature_provider = (
        (lambda: ENABLE_CONFIG.copy())
        if feature_provider is None
        else feature_provider
    )
    initial_boost_settings = BoostSettingsSnapshot(
        boost_mode=boost_mode,
        random_boost_percent=float(random_boost_percent),
        boost_target=boost_target,
    )
    boost_provider = (
        (lambda: initial_boost_settings)
        if boost_provider is None
        else boost_provider
    )
    reward_root = normalize_reward_root(reward_root)
    now = time.monotonic()
    last_motion_or_button_time = now
    last_button_seen_time = now
    last_alert_time = float("-inf")
    last_captcha_check_time = float("-inf")
    last_performance_log_time = now
    last_clicks = {}
    latest_frame = None
    fast_scan_until = now + FAST_SCAN_AFTER_PLAY
    waiting_for_play = False
    speed_mode = "FAST"
    capture_time_total = 0.0
    scan_time_total = 0.0
    performance_samples = 0
    session_completed_runs = 0
    boots_stuck_started_at = None
    boots_purchase_pending = False
    multi_buy_attempts = 0
    current_boots_should_roll = None
    current_boots_settings = None
    pending_play_context = None
    pending_play_clicked_at = None
    pending_play_fatigue_decision = None
    pending_play_confirm_frames = 0
    play_input_attempts = 0
    failed_play_attempts = 0
    fallback_attempts = {action.name: 0 for action in FALLBACK_BUTTON_ACTIONS}
    last_detection_source_size = None
    bonus_trigger_latched = False
    start_jump_latched = False
    reward_record_dir = None
    reward_record_index = 0

    account_prefix = f"[{account_label}] " if account_label else ""
    if target_window_hwnd is None:
        print(f"{account_prefix}[BOT] Single-Frame Windows Scanner เริ่มทำงานแล้ว")
    else:
        print(
            f"{account_prefix}[BOT] เริ่มควบคุม LDPlayer HWND="
            f"0x{int(target_window_hwnd):X}"
        )
    play_count, ok_count, play_target, ok_target = fatigue.snapshot()
    print(
        f"[FATIGUE] PLAY {play_count} "
        f"(พักยาวรอบ {play_target}), "
        f"OK {ok_count} (พักยาวรอบ {ok_target})"
    )
    if target_run_count is None:
        print("[RUN LIMIT] เล่นต่อเนื่องแบบไม่จำกัดจำนวนรอบ")
    else:
        print(f"[RUN LIMIT] จะหยุดอัตโนมัติหลังจบ {target_run_count} รอบ")
    if initial_boost_settings.boost_mode == BOOST_MODE_RANDOM:
        print(
            "[BOOST] ค่าเริ่มต้นโหมดสุ่มบางตา: โอกาสสุ่ม "
            f"{initial_boost_settings.random_boost_percent:.1f}%"
        )
    elif initial_boost_settings.boost_mode == BOOST_MODE_NEVER:
        print("[BOOST] โหมดข้าม boots ทุกตา")
    else:
        print("[BOOST] โหมดสุ่ม boots ทุกตา")
    boost_target_template = get_boost_target_template(
        initial_boost_settings.boost_target,
        template_cache,
    )
    boost_target_label = get_boost_target_label(initial_boost_settings.boost_target)
    print(
        f"[BOOST] เป้าหมายผลสุ่ม: {boost_target_label} "
        f"({boost_target_template})"
    )
    print(f"[SPEED] FAST {FAST_LOOP_INTERVAL:.2f}s สำหรับ 5 วินาทีแรก")
    notifier.send_message(f"[START] {BOT_NAME} เริ่มทำงานแล้ว")

    def read_boost_settings_snapshot():
        """Read and validate one atomic Boots configuration snapshot."""
        try:
            snapshot = boost_provider()
        except Exception as error:
            print(
                "[LIVE CONFIG WARNING] อ่านค่า Boots ไม่สำเร็จ "
                f"({type(error).__name__}); ใช้ค่าเริ่มต้นของ worker"
            )
            return initial_boost_settings

        if not isinstance(snapshot, BoostSettingsSnapshot):
            print(
                "[LIVE CONFIG WARNING] รูปแบบค่า Boots ไม่ถูกต้อง; "
                "ใช้ค่าเริ่มต้นของ worker"
            )
            return initial_boost_settings
        if snapshot.boost_mode not in (
            BOOST_MODE_ALWAYS,
            BOOST_MODE_NEVER,
            BOOST_MODE_RANDOM,
        ):
            print("[LIVE CONFIG WARNING] boost_mode ไม่ถูกต้อง; ใช้ค่าเริ่มต้น")
            return initial_boost_settings
        if (
            snapshot.boost_target not in ACTIVE_BOOST_TEMPLATE_IDS
            or snapshot.boost_target not in template_cache
        ):
            print(
                "[LIVE CONFIG WARNING] ไม่พบ Boots template ที่เลือก; "
                "ใช้ค่าเริ่มต้นของ worker"
            )
            return initial_boost_settings
        try:
            percent = float(snapshot.random_boost_percent)
        except (TypeError, ValueError):
            print("[LIVE CONFIG WARNING] เปอร์เซ็นต์ Boots ไม่ถูกต้อง; ใช้ค่าเริ่มต้น")
            return initial_boost_settings
        if percent < 0.0 or percent > 100.0:
            print("[LIVE CONFIG WARNING] เปอร์เซ็นต์ Boots เกิน 0-100; ใช้ค่าเริ่มต้น")
            return initial_boost_settings
        return BoostSettingsSnapshot(
            boost_mode=snapshot.boost_mode,
            random_boost_percent=percent,
            boost_target=snapshot.boost_target,
        )

    def capture_active_frame(game_window):
        # The native render surface is the single source of truth for both
        # background capture and PostMessage client coordinates.  Keep the
        # legacy calibration argument for compatibility, but do not fall back
        # to desktop MSS capture: that would reintroduce foreground coupling.
        return capture_window_client_bgr(screen_capture, game_window)

    def build_detection_frame(source_frame):
        nonlocal last_detection_source_size
        detection_frame = normalize_for_template_matching(
            source_frame,
            TEMPLATE_REFERENCE_FRAME_SIZE,
        )
        source_height, source_width = source_frame.shape[:2]
        detection_height, detection_width = detection_frame.shape[:2]
        source_size = (source_width, source_height)
        if source_size != last_detection_source_size:
            scale_x, scale_y = detection_to_source_scale(
                source_size,
                (detection_width, detection_height),
            )
            print(
                "[DETECTION] client "
                f"{source_width}x{source_height} -> template frame "
                f"{detection_width}x{detection_height} | "
                f"click map x{scale_x:.4f}, y{scale_y:.4f}"
            )
            last_detection_source_size = source_size
        return detection_frame

    def capture_latest_frame_for_check():
        latest_window = find_game_window(target_window_hwnd)
        if latest_window is None or latest_window.isMinimized:
            return None, None, None
        latest_frame, latest_region = capture_active_frame(latest_window)
        return latest_frame, latest_region, latest_window

    def save_reward_record_frame(action_name, frame):
        """Save exactly two PNGs for each Open All -> Confirm cycle."""
        nonlocal reward_record_dir
        nonlocal reward_record_index

        if action_name not in ("OPEN_ALL", "CONFIRM"):
            return None
        if frame is None or frame.size == 0:
            print(f"[REWARD RECORD] ไม่มีภาพสำหรับ {action_name}; ข้ามการบันทึก")
            return None

        if action_name == "OPEN_ALL" and reward_record_dir is None:
            reward_record_index += 1
            timestamp = datetime.now()
            date_name = timestamp.strftime("%Y-%m-%d")
            time_name = timestamp.strftime("%H%M%S")
            account_name = safe_path_component(account_label)
            folder_name = f"round_{reward_record_index:06d}_{time_name}"
            reward_record_dir = os.path.join(
                reward_root,
                date_name,
                f"account_{account_name}",
                folder_name,
            )
            try:
                os.makedirs(reward_record_dir, exist_ok=True)
            except OSError as error:
                print(f"[REWARD RECORD ERROR] สร้างโฟลเดอร์ไม่สำเร็จ: {error}")
                reward_record_dir = None
                return None

        if reward_record_dir is None:
            reward_record_index += 1
            timestamp = datetime.now()
            reward_record_dir = os.path.join(
                reward_root,
                timestamp.strftime("%Y-%m-%d"),
                f"account_{safe_path_component(account_label)}",
                f"round_{reward_record_index:06d}_{timestamp.strftime('%H%M%S')}",
            )
            try:
                os.makedirs(reward_record_dir, exist_ok=True)
            except OSError as error:
                print(f"[REWARD RECORD ERROR] สร้างโฟลเดอร์ไม่สำเร็จ: {error}")
                reward_record_dir = None
                return None

        filename = (
            "01_before_open_all.png"
            if action_name == "OPEN_ALL"
            else "02_before_confirm.png"
        )
        output_path = os.path.join(reward_record_dir, filename)
        try:
            saved = cv2.imwrite(
                output_path,
                frame,
                [cv2.IMWRITE_PNG_COMPRESSION, 3],
            )
        except cv2.error as error:
            print(f"[REWARD RECORD ERROR] บันทึก {filename} ไม่สำเร็จ: {error}")
            return None
        if not saved:
            print(f"[REWARD RECORD ERROR] บันทึก {filename} ไม่สำเร็จ")
            return None
        print(f"[REWARD RECORD] บันทึก {filename} -> {reward_record_dir}")
        return output_path

    def shift_pause_timers(paused_for):
        nonlocal last_motion_or_button_time
        nonlocal last_button_seen_time
        nonlocal last_captcha_check_time
        nonlocal last_performance_log_time
        nonlocal fast_scan_until
        nonlocal pending_play_clicked_at
        if paused_for <= 0:
            return
        last_motion_or_button_time += paused_for
        last_button_seen_time += paused_for
        if last_captcha_check_time != float("-inf"):
            last_captcha_check_time += paused_for
        last_performance_log_time += paused_for
        fast_scan_until += paused_for
        if pending_play_clicked_at is not None:
            pending_play_clicked_at += paused_for

    def wait_for_next_loop():
        nonlocal speed_mode
        current_time = time.monotonic()
        if waiting_for_play or current_time < fast_scan_until:
            delay = FAST_LOOP_INTERVAL
            next_mode = "FAST"
        else:
            delay = random.uniform(*ECO_LOOP_INTERVAL_RANGE)
            next_mode = "ECO"

        if next_mode != speed_mode:
            speed_mode = next_mode
            if speed_mode == "FAST":
                print(f"[SPEED] FAST {FAST_LOOP_INTERVAL:.2f}s เพื่อดัก PLAY/BUFF")
            else:
                print("[SPEED] ECO สุ่มพัก 0.7-0.8s เพื่อลดภาระ CPU")
        return wait_with_pause(
            stop_event,
            pause_event,
            delay,
            on_pause_interval=shift_pause_timers,
        )

    def find_play_transition_marker(detection_frame, pending_context):
        """Return a positive marker for the page expected after PLAY."""
        if pending_context == "normal":
            boots_center = scan_image_and_get_center(
                detection_frame,
                template_cache[BOOTS_SCREEN_TEMPLATE],
                BOOTS_SCREEN_TEMPLATE,
                threshold=PLAY_TRANSITION_MARKER_THRESHOLD,
            )
            if boots_center is not None:
                return "boots"

        stop_center = scan_image_and_get_center(
            detection_frame,
            template_cache[STOP_TEMPLATE],
            STOP_TEMPLATE,
            threshold=PLAY_TRANSITION_MARKER_THRESHOLD,
        )
        if stop_center is not None:
            return "game"
        return None

    def run_start_jump_flow():
        """Tap the gameplay jump area after the first BUFF marker appears."""
        nonlocal latest_frame
        nonlocal last_button_seen_time
        nonlocal last_motion_or_button_time
        nonlocal fast_scan_until

        first_click_delay = random.uniform(*START_JUMP_INITIAL_DELAY_RANGE)
        duration_label, duration_range, target_duration = (
            choose_start_jump_flow_duration()
        )
        total_clicks = random.randint(*START_JUMP_TOTAL_CLICKS_RANGE)
        click_groups = build_start_jump_click_groups(total_clicks)
        group_gaps = build_start_jump_group_gaps(
            click_groups,
            target_duration,
        )
        print(
            "[START JUMP] พบ BUFF ตอนเริ่มเกม; "
            f"เริ่มคลิกใน {first_click_delay:.2f}s แล้วกระจายต่อ "
            f"{target_duration:.2f}s ({duration_label} "
            f"{duration_range[0]:.0f}-{duration_range[1]:.0f}s); "
            f"รวม {total_clicks} ครั้ง ({len(click_groups)} ชุด)"
        )
        if wait_with_pause(
            stop_event,
            pause_event,
            first_click_delay,
            on_pause_interval=shift_pause_timers,
        ):
            return False
        if not feature_provider().get("START_JUMP", False):
            print("[START JUMP] ถูกปิดจาก UI ระหว่างช่วงรอ; ยกเลิก flow รอบนี้")
            return False

        packet = capture_latest_frame_for_check()
        if packet[0] is None or packet[1] is None or packet[2] is None:
            print("[START JUMP] แคปภาพก่อนเริ่มกดโดดไม่สำเร็จ; ข้าม flow รอบนี้")
            return False
        frame, region, window = packet
        latest_frame = frame
        detection_frame = build_detection_frame(frame)
        detection_size = (
            detection_frame.shape[1],
            detection_frame.shape[0],
        )
        base_action, center, area_size = build_area_click_target(
            "START_JUMP",
            START_JUMP_CLICK_AREA,
            START_JUMP_REFERENCE_FRAME_SIZE,
            detection_size,
            (0.0, 0.0),
        )

        for group_index, group_size in enumerate(click_groups, start=1):
            if stop_event.is_set():
                return False
            if not feature_provider().get("START_JUMP", False):
                print("[START JUMP] ถูกปิดจาก UI ระหว่าง flow; หยุดกดโดด")
                return False
            jump_action = ButtonAction(
                name=(
                    "START_JUMP_TRIPLE"
                    if group_size == 3
                    else "START_JUMP_DOUBLE"
                    if group_size == 2
                    else "START_JUMP"
                ),
                template_name="",
                fixed_position=base_action.fixed_position,
                pre_click_delay=(0.0, 0.0),
                post_click_delay=0.0,
                minimum_clicks=group_size,
                maximum_clicks=group_size,
                jitter=0,
                bounds=None,
                safe_click_ratio=(1.0, 1.0),
                click_area=base_action.click_area,
            )
            lock_acquired = False
            if click_lock is not None:
                lock_acquired = acquire_click_lock(
                    click_lock,
                    stop_event,
                    pause_event,
                )
                if not lock_acquired:
                    return False
            try:
                clicked = click_human_like(
                    window,
                    jump_action,
                    stop_event,
                    pause_event=pause_event,
                    on_pause_interval=shift_pause_timers,
                    detected_center=center,
                    scan_region=region,
                    detected_size=area_size,
                    detection_frame_size=detection_size,
                    hold_delay_range=START_JUMP_HOLD_DELAY_RANGE,
                    inter_click_delay_range=START_JUMP_INTER_CLICK_DELAY_RANGE,
                )
            except (OSError, ValueError, pyautogui.FailSafeException) as error:
                print(f"[START JUMP ERROR] {type(error).__name__}: {error}")
                clicked = False
            finally:
                if lock_acquired:
                    click_lock.release()
            if not clicked:
                print(
                    f"[START JUMP] ชุดที่ {group_index}/{len(click_groups)} "
                    "ถูกหยุดหรือส่งคลิกไม่สำเร็จ"
                )
                return False
            if group_index < len(click_groups):
                if wait_with_pause(
                    stop_event,
                    pause_event,
                    group_gaps[group_index - 1],
                    on_pause_interval=shift_pause_timers,
                ):
                    return False

        completed_at = time.monotonic()
        last_button_seen_time = completed_at
        last_motion_or_button_time = completed_at
        fast_scan_until = completed_at + FAST_SCAN_AFTER_PLAY
        print(
            "[START JUMP] จบชุดกดโดดแล้ว; "
            f"สุ่ม double/triple ตามลำดับ {click_groups}"
        )
        return True

    def find_bonus_trigger(detection_frame):
        return scan_image_in_reference_area(
            detection_frame,
            template_cache[BONUS_TRIGGER_TEMPLATE],
            BONUS_TRIGGER_TEMPLATE,
            BONUS_TRIGGER_SEARCH_AREA,
            BONUS_FLOW_REFERENCE_FRAME_SIZE,
            BONUS_TRIGGER_MATCH_THRESHOLD,
        )

    def find_bonus_quit(detection_frame, click_area):
        search_area = pad_reference_rect(
            click_area,
            BONUS_QUIT_SEARCH_PADDING,
            BONUS_FLOW_REFERENCE_FRAME_SIZE,
        )
        return scan_image_in_reference_area(
            detection_frame,
            template_cache[BONUS_QUIT_TEMPLATE],
            BONUS_QUIT_TEMPLATE,
            search_area,
            BONUS_FLOW_REFERENCE_FRAME_SIZE,
            BONUS_QUIT_MATCH_THRESHOLD,
        )

    def capture_bonus_flow_frame():
        nonlocal latest_frame
        frame, region, window = capture_latest_frame_for_check()
        if frame is None or region is None or window is None:
            return None
        latest_frame = frame
        detection_frame = build_detection_frame(frame)
        return frame, region, window, detection_frame

    def wait_for_bonus_flow_match(match_getter, timeout):
        deadline = time.monotonic() + timeout

        def shift_deadline(paused_for):
            nonlocal deadline
            shift_pause_timers(paused_for)
            deadline += paused_for

        last_packet = None
        while not stop_event.is_set() and time.monotonic() < deadline:
            stopped, _ = wait_while_paused(
                stop_event,
                pause_event,
                on_pause_interval=shift_deadline,
            )
            if stopped:
                return None, last_packet
            packet = capture_bonus_flow_frame()
            if packet is not None:
                last_packet = packet
                match = match_getter(packet[3])
                if match is not None:
                    return match, packet
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if wait_with_pause(
                stop_event,
                pause_event,
                min(FAST_LOOP_INTERVAL, remaining),
                on_pause_interval=shift_deadline,
            ):
                return None, last_packet
        return None, last_packet

    def send_bonus_flow_click(name, click_area, pre_click_delay, verify_area=None):
        delay = random.uniform(*pre_click_delay)
        print(f"[BONUS QUIT] {name} รอก่อนคลิก {delay:.2f}s")
        if wait_with_pause(
            stop_event,
            pause_event,
            delay,
            on_pause_interval=shift_pause_timers,
        ):
            return "stopped", None, None

        packet = capture_bonus_flow_frame()
        if packet is None:
            print(f"[BONUS QUIT] แคปภาพยืนยัน {name} ไม่สำเร็จ")
            return "capture_failed", None, None
        _, region, window, detection_frame = packet
        required_match = None
        if verify_area is not None:
            required_match = find_bonus_quit(detection_frame, verify_area)
            if required_match is None:
                print(f"[BONUS QUIT] {name} หายไประหว่างรอ ยกเลิกคลิกเก่า")
                return "missing", packet, None

        detection_size = (
            detection_frame.shape[1],
            detection_frame.shape[0],
        )
        action, center, area_size = build_area_click_target(
            name,
            click_area,
            BONUS_FLOW_REFERENCE_FRAME_SIZE,
            detection_size,
            pre_click_delay,
        )
        lock_acquired = False
        if click_lock is not None:
            lock_acquired = acquire_click_lock(
                click_lock,
                stop_event,
                pause_event,
            )
            if not lock_acquired:
                return "stopped" if stop_event.is_set() else "paused", packet, required_match
        try:
            clicked = click_human_like(
                window,
                action,
                stop_event,
                pause_event=pause_event,
                on_pause_interval=shift_pause_timers,
                detected_center=center,
                scan_region=region,
                detected_size=area_size,
                detection_frame_size=detection_size,
            )
        except (OSError, ValueError, pyautogui.FailSafeException) as error:
            print(f"[CLICK ERROR] {name}: {type(error).__name__}: {error}")
            clicked = False
        finally:
            if lock_acquired:
                click_lock.release()
        return ("clicked" if clicked else "failed"), packet, required_match

    def alert_and_stop_bonus_flow(reason):
        print(f"[BONUS QUIT ERROR] {reason}")
        notifier.send_alert(f"Bonus Quit Flow ล้มเหลว: {reason}", latest_frame)
        stop_event.set()
        return False

    def run_bonus_quit_flow(trigger_match):
        nonlocal fast_scan_until
        nonlocal last_button_seen_time
        nonlocal last_motion_or_button_time
        print(
            "[BONUS QUIT] ตรวจพบ Bonus trigger "
            f"score={trigger_match.score:.4f} center={trigger_match.center}; "
            "ระงับ action อื่นชั่วคราว"
        )
        fast_scan_until = time.monotonic() + FAST_SCAN_AFTER_PLAY

        quit_1_packet = None
        for attempt in range(1, BONUS_FLOW_MAX_ATTEMPTS + 1):
            print(f"[BONUS QUIT] PAUSE attempt {attempt}/{BONUS_FLOW_MAX_ATTEMPTS}")
            status, _, _ = send_bonus_flow_click(
                "BONUS_PAUSE",
                BONUS_PAUSE_CLICK_AREA,
                BONUS_PAUSE_PRE_CLICK_DELAY_RANGE,
            )
            if status == "stopped":
                return False
            if status != "clicked":
                continue
            quit_1_match, quit_1_packet = wait_for_bonus_flow_match(
                lambda frame: find_bonus_quit(frame, BONUS_QUIT_1_CLICK_AREA),
                BONUS_FLOW_TRANSITION_TIMEOUT,
            )
            if quit_1_match is not None:
                print(
                    "[BONUS QUIT] พบ QUIT_1 "
                    f"score={quit_1_match.score:.4f} center={quit_1_match.center}"
                )
                break
            if stop_event.is_set():
                return False
        else:
            return alert_and_stop_bonus_flow(
                f"PAUSE ครบ {BONUS_FLOW_MAX_ATTEMPTS} ครั้งแต่ QUIT_1 ไม่ปรากฏ"
            )

        quit_2_match = None
        quit_2_packet = None
        for attempt in range(1, BONUS_FLOW_MAX_ATTEMPTS + 1):
            print(f"[BONUS QUIT] QUIT_1 attempt {attempt}/{BONUS_FLOW_MAX_ATTEMPTS}")
            status, packet, _ = send_bonus_flow_click(
                "BONUS_QUIT_1",
                BONUS_QUIT_1_CLICK_AREA,
                BONUS_QUIT_PRE_CLICK_DELAY_RANGE,
                verify_area=BONUS_QUIT_1_CLICK_AREA,
            )
            if status == "stopped":
                return False
            if status == "missing":
                detection_frame = packet[3] if packet is not None else None
                quit_2_match = (
                    find_bonus_quit(detection_frame, BONUS_QUIT_2_CLICK_AREA)
                    if detection_frame is not None
                    else None
                )
                if quit_2_match is not None:
                    quit_2_packet = packet
                    break
                return alert_and_stop_bonus_flow(
                    "QUIT_1 หายก่อนคลิกและไม่พบ QUIT_2 ภายในหน้าปัจจุบัน"
                )
            if status != "clicked":
                continue

            deadline = time.monotonic() + BONUS_FLOW_TRANSITION_TIMEOUT

            def shift_quit_1_deadline(paused_for):
                nonlocal deadline
                shift_pause_timers(paused_for)
                deadline += paused_for

            quit_1_still_visible = False
            while not stop_event.is_set() and time.monotonic() < deadline:
                stopped, _ = wait_while_paused(
                    stop_event,
                    pause_event,
                    on_pause_interval=shift_quit_1_deadline,
                )
                if stopped:
                    return False
                packet = capture_bonus_flow_frame()
                if packet is not None:
                    quit_2_match = find_bonus_quit(
                        packet[3], BONUS_QUIT_2_CLICK_AREA
                    )
                    if quit_2_match is not None:
                        quit_2_packet = packet
                        break
                    quit_1_still_visible = find_bonus_quit(
                        packet[3], BONUS_QUIT_1_CLICK_AREA
                    ) is not None
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                if wait_with_pause(
                    stop_event,
                    pause_event,
                    min(FAST_LOOP_INTERVAL, remaining),
                    on_pause_interval=shift_quit_1_deadline,
                ):
                    return False
            if quit_2_match is not None:
                print(
                    "[BONUS QUIT] พบ QUIT_2 "
                    f"score={quit_2_match.score:.4f} center={quit_2_match.center}"
                )
                break
            if not quit_1_still_visible:
                return alert_and_stop_bonus_flow(
                    "QUIT_1 หายแล้วแต่ QUIT_2 ไม่ปรากฏภายใน 5 วินาที"
                )
        else:
            return alert_and_stop_bonus_flow(
                f"QUIT_1 ยังอยู่หลังคลิกครบ {BONUS_FLOW_MAX_ATTEMPTS} ครั้ง"
            )

        quit_2_was_clicked = False
        for attempt in range(1, BONUS_FLOW_MAX_ATTEMPTS + 1):
            print(f"[BONUS QUIT] QUIT_2 attempt {attempt}/{BONUS_FLOW_MAX_ATTEMPTS}")
            status, packet, _ = send_bonus_flow_click(
                "BONUS_QUIT_2",
                BONUS_QUIT_2_CLICK_AREA,
                BONUS_QUIT_PRE_CLICK_DELAY_RANGE,
                verify_area=BONUS_QUIT_2_CLICK_AREA,
            )
            if status == "stopped":
                return False
            if status == "missing":
                return alert_and_stop_bonus_flow("QUIT_2 หายก่อนที่จะส่งคลิกยืนยัน")
            if status != "clicked":
                continue
            quit_2_was_clicked = True

            deadline = time.monotonic() + BONUS_FLOW_TRANSITION_TIMEOUT
            absent_frames = 0

            def shift_quit_2_deadline(paused_for):
                nonlocal deadline
                shift_pause_timers(paused_for)
                deadline += paused_for

            while not stop_event.is_set() and time.monotonic() < deadline:
                stopped, _ = wait_while_paused(
                    stop_event,
                    pause_event,
                    on_pause_interval=shift_quit_2_deadline,
                )
                if stopped:
                    return False
                packet = capture_bonus_flow_frame()
                if packet is not None:
                    if find_bonus_quit(packet[3], BONUS_QUIT_2_CLICK_AREA) is None:
                        absent_frames += 1
                        if (
                            quit_2_was_clicked
                            and absent_frames >= BONUS_FLOW_ABSENT_CONFIRM_FRAMES
                        ):
                            completed_at = time.monotonic()
                            last_button_seen_time = completed_at
                            last_motion_or_button_time = completed_at
                            fast_scan_until = completed_at + FAST_SCAN_AFTER_PLAY
                            print(
                                "[BONUS QUIT] QUIT_2 หายครบ "
                                f"{BONUS_FLOW_ABSENT_CONFIRM_FRAMES} เฟรม; "
                                "กลับสู่ logic ปกติ"
                            )
                            return True
                    else:
                        absent_frames = 0
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                if wait_with_pause(
                    stop_event,
                    pause_event,
                    min(FAST_LOOP_INTERVAL, remaining),
                    on_pause_interval=shift_quit_2_deadline,
                ):
                    return False
        return alert_and_stop_bonus_flow(
            f"QUIT_2 ยังอยู่หลังคลิกครบ {BONUS_FLOW_MAX_ATTEMPTS} ครั้ง"
        )

    while not stop_event.is_set():
        stopped, _ = wait_while_paused(
            stop_event,
            pause_event,
            on_pause_interval=shift_pause_timers,
        )
        if stopped:
            break

        game_window = find_game_window(target_window_hwnd)
        current_time = time.monotonic()
        if game_window is None:
            if current_time - last_alert_time >= TELEGRAM_COOLDOWN:
                missing_target = (
                    f"ไม่พบหน้าต่าง LDPlayer ที่เลือก (HWND=0x{int(target_window_hwnd):X})"
                    if target_window_hwnd is not None
                    else f"ไม่พบหน้าต่าง {GAME_WINDOW_TITLE}"
                )
                notifier.send_alert(
                    missing_target, latest_frame
                )
                last_alert_time = current_time
            if wait_with_pause(
                stop_event,
                pause_event,
                2.0,
                on_pause_interval=shift_pause_timers,
            ):
                break
            continue
        if game_window.isMinimized:
            if current_time - last_alert_time >= TELEGRAM_COOLDOWN:
                notifier.send_alert("หน้าต่างเกมถูก minimize", latest_frame)
                last_alert_time = current_time
            if wait_with_pause(
                stop_event,
                pause_event,
                1.0,
                on_pause_interval=shift_pause_timers,
            ):
                break
            continue

        capture_started = time.perf_counter()
        current_frame, active_scan_region = capture_active_frame(game_window)
        capture_seconds = time.perf_counter() - capture_started
        if current_frame is None or active_scan_region is None:
            if wait_for_next_loop():
                break
            continue
        latest_frame = current_frame
        current_detection_frame = build_detection_frame(current_frame)

        scan_started = time.perf_counter()
        scan_now = time.monotonic()
        enabled_features = feature_provider()
        if pending_play_context is not None:
            # Keep PLAY exclusive while the game is loading. A visible PLAY
            # template during this state is not enough to justify another click.
            last_motion_or_button_time = scan_now
            last_button_seen_time = scan_now
            pending_elapsed = (
                scan_now - pending_play_clicked_at
                if pending_play_clicked_at is not None
                else PLAY_TRANSITION_TIMEOUT
            )
            if pending_elapsed < PLAY_TRANSITION_VERIFY_START_DELAY:
                if wait_for_next_loop():
                    break
                continue

            transition_marker = find_play_transition_marker(
                current_detection_frame,
                pending_play_context,
            )
            if transition_marker is not None:
                pending_play_confirm_frames += 1
                if pending_play_confirm_frames == 1:
                    print(
                        f"[PLAY VERIFY] พบ marker หน้า {transition_marker}; "
                        f"ยืนยัน {pending_play_confirm_frames}/"
                        f"{PLAY_SUCCESS_CONFIRM_FRAMES} เฟรม"
                    )
                if pending_play_confirm_frames >= PLAY_SUCCESS_CONFIRM_FRAMES:
                    success_decision = pending_play_fatigue_decision
                    pending_play_context = None
                    pending_play_clicked_at = None
                    pending_play_fatigue_decision = None
                    pending_play_confirm_frames = 0
                    failed_play_attempts = 0
                    fatigue.commit_click(success_decision)
                    print(
                        "[PLAY SUCCESS] ยืนยันการเปลี่ยนหน้าแล้ว "
                        f"marker={transition_marker} จาก {success_decision[0] if success_decision else 'PLAY'}"
                    )
                    continue
            else:
                pending_play_confirm_frames = 0

            if pending_elapsed >= PLAY_TRANSITION_TIMEOUT:
                failed_play_attempts += 1
                pending_play_context = None
                pending_play_clicked_at = None
                pending_play_fatigue_decision = None
                pending_play_confirm_frames = 0
                print(
                    "[PLAY TIMEOUT] ยังไม่พบ marker หน้าใหม่หลังรอ "
                    f"{PLAY_TRANSITION_TIMEOUT:.1f}s; "
                    f"failure={failed_play_attempts}/{PLAY_STUCK_MAX_ATTEMPTS}"
                )
                if failed_play_attempts >= PLAY_STUCK_MAX_ATTEMPTS:
                    if scan_now - last_alert_time >= TELEGRAM_COOLDOWN:
                        notifier.send_alert(
                            "กด PLAY แล้วไม่พบ marker ของหน้าถัดไปครบ "
                            f"{PLAY_STUCK_MAX_ATTEMPTS} ครั้งติดกัน "
                            "บอทจะรอแล้ว retry ต่อ",
                            latest_frame,
                        )
                        last_alert_time = scan_now
                    if random.random() < PLAY_RETRY_LONG_DELAY_PROBABILITY:
                        retry_delay = random.uniform(*PLAY_RETRY_LONG_DELAY_RANGE)
                        retry_delay_label = "10-30s"
                    else:
                        retry_delay = random.uniform(*PLAY_RETRY_SHORT_DELAY_RANGE)
                        retry_delay_label = "1-5s"
                    print(
                        f"[PLAY RETRY] ครบชุด {PLAY_STUCK_MAX_ATTEMPTS} timeout; "
                        f"รอ {retry_delay:.1f}s ({retry_delay_label}) "
                        "แล้วเริ่มชุดใหม่"
                    )
                    failed_play_attempts = 0
                    if wait_with_pause(
                        stop_event,
                        pause_event,
                        retry_delay,
                        on_pause_interval=shift_pause_timers,
                    ):
                        break
                    fast_scan_until = time.monotonic() + FAST_SCAN_AFTER_PLAY
                    continue
                if wait_for_next_loop():
                    break
                continue

            # A marker was either absent or has not been stable for enough
            # frames yet. Keep the PLAY transition state exclusive and do not
            # let normal action selection click the still-visible PLAY button.
            if wait_for_next_loop():
                break
            continue

        if not enabled_features.get("START_JUMP", False):
            start_jump_latched = False
        else:
            buff_center = scan_image_and_get_center(
                current_detection_frame,
                template_cache[ACTION_BY_NAME["BUFF"].template_name],
                ACTION_BY_NAME["BUFF"].template_name,
            )
            if buff_center is None:
                start_jump_latched = False
            elif not start_jump_latched:
                start_jump_latched = True
                last_button_seen_time = scan_now
                last_motion_or_button_time = scan_now
                if not run_start_jump_flow():
                    if stop_event.is_set():
                        break
                    start_jump_latched = False
                continue

        if not enabled_features.get("BONUS_QUIT_FLOW", False):
            bonus_trigger_latched = False
        else:
            bonus_trigger_match = find_bonus_trigger(current_detection_frame)
            if bonus_trigger_match is None:
                bonus_trigger_latched = False
            elif not bonus_trigger_latched:
                bonus_trigger_latched = True
                bonus_delay, delay_label, delay_range = choose_bonus_flow_delay()
                print(
                    "[BONUS QUIT] พบ Bonus แล้ว; "
                    f"รอสุ่ม {bonus_delay:.2f}s ({delay_label} {delay_range[0]:.0f}-"
                    f"{delay_range[1]:.0f}s) ก่อนกด PAUSE"
                )
                if wait_with_pause(
                    stop_event,
                    pause_event,
                    bonus_delay,
                    on_pause_interval=shift_pause_timers,
                ):
                    break
                # If the user turns the UI option off while this delay is
                # running, cancel this not-yet-started Bonus flow safely.
                if not feature_provider().get("BONUS_QUIT_FLOW", False):
                    bonus_trigger_latched = False
                    print("[BONUS QUIT] ถูกปิดจาก UI ระหว่างรอ; ยกเลิก flow รอบนี้")
                    continue
                if not run_bonus_quit_flow(bonus_trigger_match):
                    if stop_event.is_set():
                        break
                if stop_event.is_set():
                    break
                continue
            else:
                # After a successful quit, keep normal actions suppressed until
                # the trigger has really left the frame so the same Bonus session
                # cannot immediately start a second Pause/Quit sequence.
                if wait_for_next_loop():
                    break
                continue

        if current_boots_should_roll is None:
            provisional_selection = find_boots_screen_action(
                current_detection_frame,
                template_cache,
                last_clicks,
                scan_now,
                enabled_features,
            )
            if provisional_selection.boots_visible:
                current_boots_settings = read_boost_settings_snapshot()
                current_boots_should_roll = should_roll_boost_this_boots_screen(
                    current_boots_settings.boost_mode,
                    current_boots_settings.random_boost_percent,
                )
                decision_text = "สุ่ม boots" if current_boots_should_roll else "ข้าม boots"
                current_target_label = get_boost_target_label(
                    current_boots_settings.boost_target
                )
                percent_text = (
                    f" {current_boots_settings.random_boost_percent:.1f}%"
                    if current_boots_settings.boost_mode == BOOST_MODE_RANDOM
                    else ""
                )
                print(
                    "[BOOST] เข้าหน้า Boots screen รอบนี้: "
                    f"{decision_text}{percent_text}; เป้าหมาย={current_target_label}"
                )
        active_boost_target = (
            current_boots_settings.boost_target
            if current_boots_settings is not None
            else initial_boost_settings.boost_target
        )
        selection = find_selected_action(
            current_detection_frame,
            template_cache,
            last_clicks,
            scan_now,
            enabled_features,
            boots_purchase_pending=boots_purchase_pending,
            should_roll_boost=(
                True if current_boots_should_roll is None else current_boots_should_roll
            ),
            multi_buy_attempts=multi_buy_attempts,
            boost_target=active_boost_target,
            fallback_attempts=fallback_attempts,
        )
        action = selection.action
        detected_center = selection.center
        any_button_visible = selection.any_button_visible
        if not selection.boots_visible:
            visible_fallback_actions = set(selection.fallback_visible_actions)
            for fallback_action in FALLBACK_BUTTON_ACTIONS:
                if fallback_action.name not in visible_fallback_actions:
                    fallback_attempts[fallback_action.name] = 0
        scan_seconds = time.perf_counter() - scan_started

        capture_time_total += capture_seconds
        scan_time_total += scan_seconds
        performance_samples += 1
        if performance_samples == 1:
            print(
                f"[PERF] เฟรมแรก: Capture {capture_seconds * 1000:.0f}ms | "
                f"Scan {scan_seconds * 1000:.0f}ms"
            )
        elif scan_now - last_performance_log_time >= PERFORMANCE_LOG_INTERVAL:
            print(
                f"[PERF] เฉลี่ย {performance_samples} รอบ: Capture "
                f"{capture_time_total / performance_samples * 1000:.0f}ms | Scan "
                f"{scan_time_total / performance_samples * 1000:.0f}ms | "
                f"Mode {speed_mode}"
            )
            last_performance_log_time = scan_now
            capture_time_total = 0.0
            scan_time_total = 0.0
            performance_samples = 0

        if any_button_visible:
            last_motion_or_button_time = scan_now
            last_button_seen_time = scan_now

        if selection.boots_visible:
            if selection.boots_ready:
                boots_purchase_pending = False
                multi_buy_attempts = 0
            if action is None and not selection.boots_ready:
                if boots_stuck_started_at is None:
                    boots_stuck_started_at = scan_now
                    print("[BOOTS] อยู่หน้า Boots flow แต่ยังไม่พบปุ่มที่ต้องกดต่อ")
                elif (
                    scan_now - boots_stuck_started_at >= BOOTS_STUCK_ALERT_AFTER
                    and scan_now - last_alert_time >= TELEGRAM_COOLDOWN
                ):
                    notifier.send_alert(
                        "หน้า Boots flow ค้างเกิน "
                        f"{int(BOOTS_STUCK_ALERT_AFTER)} วินาที "
                        "โดยยังไม่เจอปุ่มที่ต้องกดต่อ",
                        latest_frame,
                    )
                    last_alert_time = scan_now
                    boots_stuck_started_at = scan_now
            else:
                boots_stuck_started_at = None
        else:
            boots_stuck_started_at = None
            boots_purchase_pending = False
            multi_buy_attempts = 0
            current_boots_should_roll = None
            current_boots_settings = None

        if action is not None:
            if action.name == "OK":
                waiting_for_play = bool(enabled_features.get("PLAY", False))
                speed_mode = "FAST"
                print(f"[SPEED] FAST {FAST_LOOP_INTERVAL:.2f}s หลังพบ OK")
            elif selection.boots_visible:
                speed_mode = "FAST"
                print(f"[BOOTS] เลือก action {action.name} ใน Boots flow")

            click_delay, fatigue_decision = fatigue.prepare_delay(action)
            print(
                f"[FOUND] ตรวจพบ {action.name} ที่ {detected_center} จาก Shared Frame "
                f"(จะคลิกตำแหน่งที่หาเจอใน {click_delay:.2f}s)"
            )
            stopped, paused_before_click = wait_with_pause_status(
                stop_event,
                pause_event,
                click_delay,
                on_pause_interval=shift_pause_timers,
                interrupt_event=(
                    fatigue.reset_event if fatigue_decision is not None else None
                ),
            )
            if stopped:
                break
            if fatigue_decision is not None and (
                fatigue.consume_reset_event()
                or not fatigue.is_decision_current(fatigue_decision)
            ):
                print("[FATIGUE] พบการ Reset รอบระหว่างรอ ยกเลิกคลิกรอบเดิม")
                continue
            if paused_before_click:
                print("[PAUSE] มีการพักระหว่างรอคลิก จึงสแกนภาพใหม่ก่อนคลิก")
                continue

            (
                refreshed_frame,
                refreshed_scan_region,
                refreshed_window,
            ) = capture_latest_frame_for_check()
            if refreshed_frame is None or refreshed_scan_region is None:
                print("[CLICK GUARD] แคปภาพก่อนคลิกไม่สำเร็จ ยกเลิกคลิกรอบนี้")
                continue
            latest_frame = refreshed_frame
            refreshed_detection_frame = build_detection_frame(refreshed_frame)
            refreshed_bonus_match = (
                find_bonus_trigger(refreshed_detection_frame)
                if enabled_features.get("BONUS_QUIT_FLOW", False)
                else None
            )
            if refreshed_bonus_match is not None:
                print(
                    f"[CLICK GUARD] พบ Bonus ก่อนกด {action.name}; "
                    "ยกเลิก action เดิมและเข้า Bonus Quit Flow"
                )
                if not bonus_trigger_latched:
                    bonus_trigger_latched = True
                    bonus_delay, delay_label, delay_range = choose_bonus_flow_delay()
                    print(
                        "[BONUS QUIT] พบ Bonus ระหว่างรอ action; "
                        f"รอสุ่ม {bonus_delay:.2f}s ({delay_label} {delay_range[0]:.0f}-"
                        f"{delay_range[1]:.0f}s) ก่อนกด PAUSE"
                    )
                    if wait_with_pause(
                        stop_event,
                        pause_event,
                        bonus_delay,
                        on_pause_interval=shift_pause_timers,
                    ):
                        break
                    if not feature_provider().get("BONUS_QUIT_FLOW", False):
                        bonus_trigger_latched = False
                        print("[BONUS QUIT] ถูกปิดจาก UI ระหว่างรอ; ยกเลิก flow รอบนี้")
                        continue
                    if not run_bonus_quit_flow(refreshed_bonus_match):
                        if stop_event.is_set():
                            break
                if stop_event.is_set():
                    break
                continue

            refreshed_center = detected_center
            if action.name == "PLAY":
                refreshed_center = scan_image_and_get_center(
                    refreshed_detection_frame,
                    template_cache[action.template_name],
                    action.template_name,
                )
                if refreshed_center is None:
                    print("[PLAY CHECK] ปุ่ม PLAY หายไประหว่างรอ ยกเลิกคลิกรอบนี้")
                    continue
                print(f"[PLAY CHECK] ยืนยัน PLAY ยังอยู่ที่ {refreshed_center}")

            lock_acquired = False
            if click_lock is not None:
                print(
                    f"{account_prefix}[INPUT] รอคิวเมาส์กลางก่อนกด {action.name}"
                )
                lock_acquired = acquire_click_lock(
                    click_lock,
                    stop_event,
                    pause_event,
                )
                if not lock_acquired:
                    if stop_event.is_set():
                        break
                    print(
                        f"{account_prefix}[INPUT] Pause ระหว่างรอคิวเมาส์ "
                        "จึงสแกนภาพใหม่ก่อนคลิก"
                    )
                    continue

            if action.name in ("OPEN_ALL", "CONFIRM"):
                save_reward_record_frame(action.name, refreshed_frame)

            try:
                click_completed = click_human_like(
                    refreshed_window,
                    action,
                    stop_event,
                    pause_event=pause_event,
                    on_pause_interval=shift_pause_timers,
                    detected_center=refreshed_center,
                    scan_region=refreshed_scan_region,
                    detected_size=(
                        template_cache[action.template_name].shape[1],
                        template_cache[action.template_name].shape[0],
                    ),
                    detection_frame_size=(
                        refreshed_detection_frame.shape[1],
                        refreshed_detection_frame.shape[0],
                    ),
                )
            except (OSError, ValueError, pyautogui.FailSafeException) as error:
                print(f"[CLICK ERROR] {action.name}: {type(error).__name__}: {error}")
                click_completed = False
            finally:
                if lock_acquired:
                    click_lock.release()

            if not click_completed:
                if stop_event.is_set():
                    break
                if wait_for_next_loop():
                    break
                continue

            clicked_at = time.monotonic()
            last_clicks[action.name] = clicked_at
            if action in FALLBACK_BUTTON_ACTIONS:
                fallback_attempts[action.name] += 1
            if action.name != "PLAY":
                fatigue.commit_click(fatigue_decision)
            if action.name == "MULTI_BUY":
                boots_purchase_pending = True
                multi_buy_attempts += 1
                boots_stuck_started_at = clicked_at
                active_target_label = (
                    "Double Coins"
                    if active_boost_target == BOOST_TARGET_DOUBLE_COIN
                    else "Magnet"
                    if active_boost_target == BOOST_TARGET_MAGNET
                    else "Base Speed"
                )
                print(
                    "[BOOTS] กด MULTI_BUY แล้ว "
                    f"attempt {multi_buy_attempts}/{MULTI_BUY_MAX_ATTEMPTS} "
                    f"รอผลสุ่มจนกว่าจะเจอ {active_target_label}"
                )
            if action.name == "OK" and target_run_count is not None:
                session_completed_runs += 1
                print(
                    f"[RUN LIMIT] จบรอบจาก OK แล้ว {session_completed_runs}/"
                    f"{target_run_count}"
                )
                if session_completed_runs >= target_run_count:
                    print(
                        f"[RUN LIMIT] ครบ {target_run_count} รอบตามที่ตั้งไว้ "
                        "กำลังหยุดบอท"
                    )
                    notifier.send_message(
                        f"[COMPLETE] {BOT_NAME} เล่นครบ {target_run_count} รอบแล้ว"
                    )
                    stop_event.set()
                    break
            if action.name == "CONFIRM":
                reward_record_dir = None
            if action.name == "PLAY":
                play_input_attempts += 1
                pending_play_context = play_context_from_boots_visible(
                    selection.boots_visible
                )
                pending_play_clicked_at = clicked_at
                pending_play_fatigue_decision = fatigue_decision
                pending_play_confirm_frames = 0
                waiting_for_play = False
                fast_scan_until = clicked_at + FAST_SCAN_AFTER_PLAY
                speed_mode = "FAST"
                print(
                    f"[PLAY INPUT] ส่งคลิก PLAY แล้ว attempt={play_input_attempts} "
                    f"context={pending_play_context}; รอยืนยันสูงสุด "
                    f"{PLAY_TRANSITION_TIMEOUT:.1f}s"
                )
                print(
                    f"[SPEED] FAST {FAST_LOOP_INTERVAL:.2f}s ต่ออีก "
                    f"{FAST_SCAN_AFTER_PLAY:.0f}s หลังคลิก PLAY"
                )

            if wait_with_pause(
                stop_event,
                pause_event,
                action.post_click_delay,
                on_pause_interval=shift_pause_timers,
            ):
                break
            continue

        if any_button_visible:
            if wait_for_next_loop():
                break
            continue

        now = time.monotonic()
        no_motion_or_button_duration = now - last_motion_or_button_time
        captcha_due = (
            no_motion_or_button_duration >= CAPTCHA_ALERT_AFTER
            and now - last_captcha_check_time >= CAPTCHA_RECHECK_INTERVAL
        )
        if captcha_due:
            last_captcha_check_time = now
            is_frozen, movement_pixels, second_frame = check_captcha_by_freeze(
                current_frame,
                lambda: capture_latest_frame_for_check()[0],
                stop_event,
                pause_event=pause_event,
                on_pause_interval=shift_pause_timers,
            )
            if stop_event.is_set():
                break
            if second_frame is not None:
                latest_frame = second_frame
            if is_frozen is True:
                print(
                    f"[CAPTCHA] หน้าจอนิ่ง movement_pixels={movement_pixels:,}"
                )
                if now - last_alert_time >= TELEGRAM_COOLDOWN:
                    notifier.send_alert(
                        "ไม่พบปุ่มเกิน 20 วินาทีและหน้าจอนิ่ง",
                        latest_frame,
                        is_captcha=True,
                        movement_pixels=movement_pixels,
                    )
                    last_alert_time = now
            elif is_frozen is False:
                print(
                    f"[RUNNING] หน้าจอยังเคลื่อนไหว movement_pixels="
                    f"{movement_pixels:,}; รีเซ็ตเวลาตรวจ Captcha"
                )
                last_motion_or_button_time = time.monotonic()

        alert_check_time = time.monotonic()
        no_button_duration = alert_check_time - last_button_seen_time
        inactive_duration = alert_check_time - last_motion_or_button_time
        if should_send_no_button_alert(
            alert_check_time,
            last_button_seen_time,
            last_motion_or_button_time,
            last_alert_time,
        ):
            notifier.send_alert(
                "ไม่พบปุ่มหลักและหน้าจอไม่มีการเคลื่อนไหวต่อเนื่อง "
                f"{int(inactive_duration)} วินาที "
                f"(ไม่พบปุ่ม {int(no_button_duration)} วินาที)",
                latest_frame,
            )
            last_alert_time = alert_check_time

        if wait_for_next_loop():
            break


class QueueWriter:
    """Forward stdout/stderr from any thread to the Tkinter log queue."""

    def __init__(self, output_queue):
        self.output_queue = output_queue

    def write(self, text):
        if text:
            self.output_queue.put(text)

    def flush(self):
        pass


class BotController:
    """Own the worker lifecycle and persistent in-process fatigue counters."""

    def __init__(
        self,
        feature_provider,
        on_finished=None,
        on_status=None,
        boost_provider=None,
    ):
        self.feature_provider = feature_provider
        self.boost_provider = boost_provider
        self.on_finished = on_finished
        self.on_status = on_status
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.fatigue = FatigueState()
        self._state_lock = threading.Lock()
        self._thread = None
        self._notify_on_stop = True
        self._notifier = None

    @property
    def is_running(self):
        with self._state_lock:
            return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        runtime_config,
        target_window_hwnd=None,
        account_label="",
        click_lock=None,
    ):
        with self._state_lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            self.stop_event.clear()
            self.pause_event.clear()
            self.fatigue.consume_reset_event()
            self._notify_on_stop = True
            worker = threading.Thread(
                target=self._run_worker,
                args=(runtime_config, target_window_hwnd, account_label, click_lock),
                name=(
                    f"CookieBasicMouseWorker-{account_label}"
                    if account_label
                    else "CookieBasicMouseWorker"
                ),
                daemon=True,
            )
            self._thread = worker
        worker.start()
        return True

    def stop(self, send_notification=True):
        with self._state_lock:
            self._notify_on_stop = bool(send_notification)
            notifier = self._notifier
        self.stop_event.set()
        self.pause_event.clear()
        if notifier is not None:
            if send_notification:
                notifier.send_message_async(f"[STOP] {BOT_NAME} stopped")
                with self._state_lock:
                    self._notify_on_stop = False
            notifier.abort()

    def reset_fatigue(self):
        """Reset PLAY/OK fatigue counters without stopping the worker."""
        self.fatigue.reset()

    def pause(self):
        with self._state_lock:
            if self._thread is None or not self._thread.is_alive():
                return False
            if self.pause_event.is_set():
                return True
            self.pause_event.set()
        print("[PAUSE] ผู้ใช้กดพักชั่วคราว")
        self._emit_status("paused")
        return True

    def resume(self):
        with self._state_lock:
            if self._thread is None or not self._thread.is_alive():
                return False
            if not self.pause_event.is_set():
                return True
            self.pause_event.clear()
        print("[RESUME] ผู้ใช้กดทำงานต่อ")
        self._emit_status("running")
        return True

    def _emit_status(self, status):
        if self.on_status is not None:
            self.on_status(status)

    def _run_worker(
        self,
        runtime_config,
        target_window_hwnd=None,
        account_label="",
        click_lock=None,
    ):
        message_prefix = f"[{account_label}]" if account_label else ""
        notifier = TelegramNotifier(
            runtime_config.token,
            runtime_config.chat_id,
            message_prefix=message_prefix,
        )
        with self._state_lock:
            self._notifier = notifier
        screen_capture = None
        bot_started = False

        try:
            self._emit_status("preparing")
            template_cache = load_templates()
            if self.stop_event.is_set():
                return

            if runtime_config.calibration_mode == CALIBRATION_MODE_AUTO:
                scan_region = None
                print("[CALIBRATION] ใช้การจับ client area ของหน้าต่าง LDPlayer อัตโนมัติ")
            elif runtime_config.calibration_mode == CALIBRATION_MODE_DEFAULT:
                scan_region = DEFAULT_SCAN_REGION.copy()
                print(f"[CALIBRATION] ใช้ค่า Default จากโปรไฟล์: {scan_region}")
            else:
                self._emit_status("calibrating")
                scan_region = calibrate_screen(self.stop_event)
                if scan_region is None or self.stop_event.is_set():
                    return

            screen_capture = mss.MSS()
            bot_started = True
            self._emit_status("paused" if self.pause_event.is_set() else "running")
            run_bot_loop(
                scan_region,
                screen_capture,
                template_cache,
                notifier,
                self.stop_event,
                pause_event=self.pause_event,
                fatigue=self.fatigue,
                feature_provider=self.feature_provider,
                calibration_mode=runtime_config.calibration_mode,
                target_run_count=runtime_config.target_run_count,
                boost_mode=runtime_config.boost_mode,
                random_boost_percent=runtime_config.random_boost_percent,
                boost_target=runtime_config.boost_target,
                boost_provider=self.boost_provider,
                reward_root=runtime_config.reward_root,
                target_window_hwnd=target_window_hwnd,
                account_label=account_label,
                click_lock=click_lock,
            )
        except Exception as error:
            print(f"[FATAL ERROR] {type(error).__name__}: {error}")
            if bot_started:
                notifier.send_message(
                    f"[ERROR] {BOT_NAME} หยุดเพราะ {type(error).__name__}: {error}"
                )
        finally:
            self.stop_event.set()
            with self._state_lock:
                notify_on_stop = self._notify_on_stop
            if bot_started and notify_on_stop:
                notifier.send_message_async(f"[STOP] {BOT_NAME} stopped")
                notify_on_stop = False
            if bot_started and notify_on_stop:
                notifier.send_message(f"[STOP] {BOT_NAME} หยุดทำงานแล้ว")
            if screen_capture is not None:
                screen_capture.close()
            notifier.close()
            print("[STOP] ปิด Mouse Bot และคืนทรัพยากรเรียบร้อย")

            with self._state_lock:
                self._thread = None
                self._notifier = None
            self._emit_status("stopped")
            if self.on_finished is not None:
                self.on_finished()


class CookieBotApp:
    """Tkinter front end with thread-safe live logging and feature switches."""

    BG = "#20252b"
    PANEL = "#2a3139"
    INPUT_BG = "#161a1f"
    TEXT = "#e8edf2"
    MUTED = "#9da9b5"
    ACCENT = "#f4b942"
    BLUE = "#62b6e7"
    GREEN = "#45ad72"
    RED = "#dc5a5a"

    def __init__(self, root):
        self.root = root
        self.running = False
        self.paused = False
        self.closing = False
        self.feature_lock = threading.Lock()
        self.feature_state = ENABLE_CONFIG.copy()
        for locked_key in LOCKED_FEATURES:
            self.feature_state[locked_key] = False
        self.boost_lock = threading.Lock()
        self.boost_template_manager = create_boost_template_manager()
        self.live_boost_state = BoostSettingsSnapshot(
            BOOST_MODE_ALWAYS,
            DEFAULT_RANDOM_BOOST_PERCENT,
            DEFAULT_BOOST_TARGET,
        )
        self.last_valid_random_boost_percent = DEFAULT_RANDOM_BOOST_PERCENT
        self.reward_root_path, self.reward_path_load_warning = (
            load_reward_root_setting()
        )
        self.settings_window = None
        self.update_info = None
        self.update_busy = False
        self.log_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        self.hotkey_listener = None
        self.last_hotkey_time = 0.0
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = QueueWriter(self.log_queue)
        sys.stderr = QueueWriter(self.log_queue)

        self.controller = BotController(
            feature_provider=self._get_feature_snapshot,
            on_finished=lambda: self.ui_queue.put(("finished", None)),
            on_status=lambda status: self.ui_queue.put(("status", status)),
            boost_provider=self._get_live_boost_snapshot,
        )
        self.locked_widgets = []
        self.readonly_locked_widgets = []
        self._build_ui()
        # The selector is restored from disk during _build_ui(). Publish that
        # restored value before a worker can be started.
        self._publish_live_boost_settings()
        self._start_hotkey_listener()
        self._poll_queues()
        print(f"[READY] {BOT_NAME} พร้อมใช้งาน")
        if self.reward_path_load_warning:
            print(f"[SETTINGS WARNING] {self.reward_path_load_warning}")
        if getattr(sys, "frozen", False):
            threading.Thread(target=self._cleanup_old_versions, daemon=True).start()
        if UPDATE_CHECK_ON_START:
            self.root.after(2500, lambda: self.check_for_updates(silent=True))

    def _build_ui(self):
        self.root.title(BOT_NAME)
        self.root.geometry("620x800")
        self.root.minsize(560, 700)
        self.root.configure(bg=self.BG)

        saved_token, saved_chat_id = load_telegram_setting()
        self.token_var = tk.StringVar(value=saved_token)
        self.chat_id_var = tk.StringVar(value=saved_chat_id)

        header_frame = tk.Frame(self.root, bg=self.BG)
        header_frame.pack(fill="x", padx=16, pady=(10, 3))
        header_frame.columnconfigure(0, weight=1)
        title_frame = tk.Frame(header_frame, bg=self.BG)
        title_frame.grid(row=0, column=0, sticky="ew")
        tk.Label(
            title_frame,
            text="COOKIE RUN / MOUSE CONTROL",
            font=("Bahnschrift SemiBold", 18),
            bg=self.BG,
            fg=self.ACCENT,
        ).pack()
        tk.Label(
            title_frame,
            text=f"Windows Shared Frame  |  Gaussian Click Guard  |  v{BOT_VERSION}",
            font=("Segoe UI", 9),
            bg=self.BG,
            fg=self.BLUE,
        ).pack(pady=(1, 0))
        self.settings_button = tk.Button(
            header_frame,
            text="⚙ ตั้งค่า",
            command=self.open_settings,
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground="#39434d",
            activeforeground=self.TEXT,
            relief="flat",
            cursor="hand2",
            padx=9,
            pady=4,
        )
        self.settings_button.grid(row=0, column=2, sticky="e", padx=(6, 0))
        self.locked_widgets.append(self.settings_button)
        self.update_button = tk.Button(
            header_frame,
            text="⟳ อัปเดต",
            command=self.on_update_button,
            font=("Segoe UI", 9, "bold"),
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground="#39434d",
            activeforeground=self.TEXT,
            relief="flat",
            cursor="hand2",
            padx=9,
            pady=4,
        )
        self.update_button.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.locked_widgets.append(self.update_button)

        run_frame = self._make_group(" การตั้งค่าการรัน ")
        run_frame.columnconfigure(1, weight=1)
        tk.Label(
            run_frame,
            text="พื้นที่แคป",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=0, column=0, sticky="w", padx=(10, 5), pady=6)
        self.calibration_mode = tk.StringVar(value=CALIBRATION_MODE_AUTO)
        self.capture_mode_options = (
            ("อัตโนมัติ (ค่าเริ่มต้น)", CALIBRATION_MODE_AUTO),
            ("Default จากจอเดิม", CALIBRATION_MODE_DEFAULT),
            ("Calibrate 4 มุม", CALIBRATION_MODE_CUSTOM),
        )
        self.capture_mode_by_label = dict(self.capture_mode_options)
        self.capture_mode_display = tk.StringVar(value=self.capture_mode_options[0][0])
        style = ttk.Style(self.root)
        style.configure(
            "Cookie.Dark.TCombobox",
            fieldbackground=self.INPUT_BG,
            background=self.PANEL,
            foreground=self.TEXT,
            arrowcolor=self.TEXT,
        )
        self.capture_mode_combo = ttk.Combobox(
            run_frame,
            textvariable=self.capture_mode_display,
            values=[label for label, _ in self.capture_mode_options],
            state="readonly",
            width=25,
            style="Cookie.Dark.TCombobox",
        )
        self.capture_mode_combo.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 12),
            pady=6,
        )
        self.capture_mode_combo.bind(
            "<<ComboboxSelected>>",
            self._on_capture_mode_selected,
        )
        self.locked_widgets.append(self.capture_mode_combo)
        self.readonly_locked_widgets.append(self.capture_mode_combo)

        tk.Label(
            run_frame,
            text="หยุดหลังจบ",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=0, column=2, sticky="w", padx=(0, 5), pady=6)
        self.run_count_var = tk.StringVar(value="0")
        self.run_count_entry = tk.Entry(
            run_frame,
            textvariable=self.run_count_var,
            width=6,
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Consolas", 10),
        )
        self.run_count_entry.grid(row=0, column=3, sticky="w", padx=(0, 5), pady=6)
        tk.Label(
            run_frame,
            text="รอบ  (0 = ไม่จำกัด)",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 8),
        ).grid(row=0, column=4, sticky="w", padx=(0, 10), pady=6)
        self.locked_widgets.append(self.run_count_entry)

        self.capture_frame_button = tk.Button(
            run_frame,
            text="แคปภาพเฟรมเกม",
            command=self.capture_game_frame,
            font=("Segoe UI", 9, "bold"),
            bg=self.BLUE,
            fg="#10212d",
            activebackground="#4f9cca",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
        )
        self.capture_frame_button.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(0, 12),
            pady=(0, 6),
        )
        tk.Label(
            run_frame,
            text="บันทึกเป็นเฟรมเดียวกับที่ใช้ค้นหา",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 8),
        ).grid(row=1, column=2, columnspan=3, sticky="w", pady=(0, 6))

        boost_frame = self._make_group(" การสุ่ม Boots ")
        boost_frame.columnconfigure(1, weight=1)
        self.boost_mode = tk.StringVar(value=BOOST_MODE_ALWAYS)
        boost_options = (
            ("สุ่มทุกตา", BOOST_MODE_ALWAYS, 0),
            ("ข้ามทุกตา", BOOST_MODE_NEVER, 1),
            ("สุ่มบางตา", BOOST_MODE_RANDOM, 2),
        )
        for label, value, column in boost_options:
            radio = tk.Radiobutton(
                boost_frame,
                text=label,
                variable=self.boost_mode,
                value=value,
                command=self._on_boost_mode_changed,
                bg=self.PANEL,
                fg=self.TEXT,
                selectcolor=self.INPUT_BG,
                activebackground=self.PANEL,
                activeforeground=self.TEXT,
                font=("Segoe UI", 9),
            )
            radio.grid(row=0, column=column, sticky="w", padx=12, pady=5)

        self.boost_percent_label = tk.Label(
            boost_frame,
            text="โอกาสสุ่ม",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        )
        self.boost_percent_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=12,
            pady=(0, 6),
        )
        self.random_boost_percent_var = tk.StringVar(
            value=f"{DEFAULT_RANDOM_BOOST_PERCENT:.0f}"
        )
        self.random_boost_percent_entry = tk.Entry(
            boost_frame,
            textvariable=self.random_boost_percent_var,
            width=8,
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Consolas", 10),
        )
        self.random_boost_percent_entry.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(0, 4),
            pady=(0, 6),
        )
        self.random_boost_percent_entry.bind(
            "<Return>",
            self._commit_boost_percent,
        )
        self.random_boost_percent_entry.bind(
            "<FocusOut>",
            self._commit_boost_percent,
        )
        self.boost_percent_suffix = tk.Label(
            boost_frame,
            text="%",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 8),
        )
        self.boost_percent_suffix.grid(
            row=1,
            column=2,
            sticky="w",
            padx=(0, 12),
            pady=(0, 6),
        )

        tk.Label(
            boost_frame,
            text="Boost เป้าหมาย",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 6))
        self.boost_target = tk.StringVar(
            value=self.boost_template_manager.selected_id
        )
        self.boost_target_display = tk.StringVar()
        self.boost_template_combo = ttk.Combobox(
            boost_frame,
            textvariable=self.boost_target_display,
            state="readonly",
            style="Cookie.Dark.TCombobox",
        )
        self.boost_template_combo.grid(
            row=2,
            column=1,
            columnspan=3,
            sticky="ew",
            padx=(0, 12),
            pady=(0, 6),
        )
        self.boost_template_combo.bind(
            "<<ComboboxSelected>>",
            self._on_boost_template_selected,
        )
        self.boost_template_display_by_id = {}
        self.boost_template_id_by_display = {}

        template_actions = tk.Frame(boost_frame, bg=self.PANEL)
        template_actions.grid(
            row=3,
            column=1,
            columnspan=3,
            sticky="w",
            padx=(0, 12),
            pady=(0, 6),
        )
        self.add_boost_template_button = tk.Button(
            template_actions,
            text="เพิ่มรูป",
            command=self._add_boost_template,
            bg=self.GREEN,
            fg="white",
            activebackground="#39945f",
            relief="flat",
            cursor="hand2",
            padx=9,
        )
        self.add_boost_template_button.grid(row=0, column=0, padx=(0, 5))
        self.replace_boost_template_button = tk.Button(
            template_actions,
            text="แทนที่รูปที่เลือก",
            command=self._replace_boost_template,
            bg=self.BLUE,
            fg="#10212d",
            activebackground="#4f9cca",
            relief="flat",
            cursor="hand2",
            padx=9,
        )
        self.replace_boost_template_button.grid(row=0, column=1, padx=(0, 5))
        self.delete_boost_template_button = tk.Button(
            template_actions,
            text="ลบรูป",
            command=self._delete_boost_template,
            bg=self.RED,
            fg="white",
            activebackground="#bf4747",
            relief="flat",
            cursor="hand2",
            padx=9,
        )
        self.delete_boost_template_button.grid(row=0, column=2)
        self.locked_widgets.extend(
            (
                self.boost_template_combo,
                self.add_boost_template_button,
                self.replace_boost_template_button,
                self.delete_boost_template_button,
            )
        )
        self._refresh_boost_template_selector()
        self._sync_boost_percent_visibility()

        feature_frame = self._make_group(" ปุ่มที่ให้บอทควบคุม (ปรับได้ระหว่างรัน) ")
        feature_definitions = (
            ("PLAY", "PLAY", 0, 0),
            ("BUFF", "FAST", 0, 1),
            ("START_JUMP", "START JUMP", 0, 2),
            ("RELAY", "RELAY", 1, 0),
            ("OK", "OK", 1, 1),
            ("OPEN_ALL", "OPEN ALL", 1, 2),
            ("CONFIRM", "CONFIRM", 2, 0),
            ("CONFIRM_MAIN", "CONFIRM MAIN", 2, 1),
            ("CLOSE", "CLOSE", 2, 2),
            ("BONUS_QUIT_FLOW", "BONUS QUIT", 3, 0),
        )
        self.feature_vars = {}
        for key, label, row, column in feature_definitions:
            locked = key in LOCKED_FEATURES
            variable = tk.BooleanVar(value=False if locked else self.feature_state[key])
            self.feature_vars[key] = variable
            tk.Checkbutton(
                feature_frame,
                text=label,
                variable=variable,
                command=lambda k=key, v=variable: self._set_feature_state(k, v.get()),
                state="disabled" if locked else "normal",
                bg=self.PANEL,
                fg=self.TEXT,
                selectcolor=self.INPUT_BG,
                activebackground=self.PANEL,
                activeforeground=self.TEXT,
                disabledforeground="#6b7280",
                font=("Segoe UI", 9, "bold"),
            ).grid(row=row, column=column, sticky="w", padx=18, pady=3)

        self.status_var = tk.StringVar(value="บอทหยุดทำงาน")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "bold"),
            bg=self.BG,
            fg=self.RED,
        )
        self.status_label.pack(pady=(7, 3))

        control_frame = tk.Frame(self.root, bg=self.BG)
        control_frame.pack(pady=3)

        self.toggle_button = tk.Button(
            control_frame,
            text="เริ่มทำงาน",
            command=self.toggle_bot,
            font=("Segoe UI", 12, "bold"),
            bg=self.GREEN,
            fg="white",
            activebackground="#39945f",
            activeforeground="white",
            width=18,
            relief="flat",
            cursor="hand2",
            pady=6,
        )
        self.toggle_button.grid(row=0, column=0, padx=(0, 8))

        self.pause_button = tk.Button(
            control_frame,
            text="พักชั่วคราว",
            command=self.toggle_pause,
            font=("Segoe UI", 12, "bold"),
            bg=self.ACCENT,
            fg="#181b20",
            activebackground="#d9a636",
            activeforeground="#181b20",
            width=14,
            relief="flat",
            cursor="hand2",
            pady=6,
            state="disabled",
        )
        self.pause_button.grid(row=0, column=1)

        self.reset_rounds_button = tk.Button(
            control_frame,
            text="Reset รอบ",
            command=self.reset_fatigue_rounds,
            font=("Segoe UI", 11, "bold"),
            bg=self.BLUE,
            fg="#10212d",
            activebackground="#4f9cca",
            activeforeground="#10212d",
            width=12,
            relief="flat",
            cursor="hand2",
            pady=5,
        )
        self.reset_rounds_button.grid(row=0, column=2, padx=(8, 0))

        tk.Label(
            self.root,
            text="Hotkey: F8 = Pause / Resume ระหว่างเล่นเอง",
            font=("Segoe UI", 8),
            bg=self.BG,
            fg=self.MUTED,
        ).pack(pady=(0, 4))

        tk.Label(
            self.root,
            text="REAL-TIME LOG",
            font=("Bahnschrift SemiBold", 9),
            bg=self.BG,
            fg=self.MUTED,
        ).pack(anchor="w", padx=18, pady=(7, 1))
        self.log = scrolledtext.ScrolledText(
            self.root,
            height=14,
            bg="#11161b",
            fg="#d7e0e8",
            insertbackground="white",
            font=("Consolas", 9),
            relief="flat",
            wrap="word",
        )
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _make_group(self, title):
        frame = tk.LabelFrame(
            self.root,
            text=title,
            bg=self.PANEL,
            fg=self.ACCENT,
            font=("Segoe UI", 9, "bold"),
            bd=1,
            relief="solid",
        )
        frame.pack(fill="x", padx=16, pady=5, ipady=3)
        return frame

    def _on_capture_mode_selected(self, _event=None):
        selected_label = self.capture_mode_display.get()
        self.calibration_mode.set(
            self.capture_mode_by_label.get(selected_label, CALIBRATION_MODE_AUTO)
        )

    def _refresh_boost_template_selector(self, selected_id=None):
        """Refresh the Boots template combobox from persistent storage."""
        displays = []
        self.boost_template_display_by_id = {}
        self.boost_template_id_by_display = {}
        for template in self.boost_template_manager.templates:
            display = f"{template.label}  [{template.filename}]"
            if not self.boost_template_manager.path_for(template).is_file():
                display += "  (ไฟล์หาย)"
            displays.append(display)
            self.boost_template_display_by_id[template.template_id] = display
            self.boost_template_id_by_display[display] = template.template_id

        self.boost_template_combo.configure(values=displays)
        chosen_id = selected_id or self.boost_target.get()
        available_ids = {
            template.template_id for template in self.boost_template_manager.templates
        }
        if chosen_id not in available_ids:
            chosen_id = self.boost_template_manager.selected_id
        if chosen_id not in available_ids and displays:
            chosen_id = self.boost_template_manager.templates[0].template_id
        self.boost_target.set(chosen_id or "")
        self.boost_target_display.set(
            self.boost_template_display_by_id.get(chosen_id, "")
        )

    def _on_boost_template_selected(self, _event=None):
        selected_id = self.boost_template_id_by_display.get(
            self.boost_target_display.get()
        )
        if not selected_id:
            return
        try:
            self.boost_template_manager.select(selected_id)
        except (KeyError, OSError) as error:
            messagebox.showerror(
                "เลือก Boots template ไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=self.root,
            )
            self._refresh_boost_template_selector()
            return
        self.boost_target.set(selected_id)
        self._publish_live_boost_settings(announce=True)

    @staticmethod
    def _image_filetypes():
        return (
            ("รูปภาพ", "*.png *.jpg *.jpeg *.bmp *.webp"),
            ("ไฟล์ทั้งหมด", "*.*"),
        )

    def _choose_boost_image(self, title):
        return filedialog.askopenfilename(
            parent=self.root,
            title=title,
            filetypes=self._image_filetypes(),
        )

    def _add_boost_template(self):
        source_path = self._choose_boost_image("เลือกภาพ Boots ที่ต้องการเพิ่ม")
        if not source_path:
            return
        try:
            template = self.boost_template_manager.add_from_file(source_path)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "เพิ่ม Boots template ไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=self.root,
            )
            return
        self._refresh_boost_template_selector(template.template_id)
        self._publish_live_boost_settings(announce=True)
        print(
            f"[BOOST TEMPLATE] เพิ่ม {template.label} จาก {source_path}; "
            "จะเริ่มใช้เมื่อเริ่มบอทรอบถัดไป"
        )

    def _replace_boost_template(self):
        selected_id = self.boost_target.get()
        if not selected_id:
            messagebox.showwarning(
                "ยังไม่ได้เลือก Boots template",
                "กรุณาเลือก template ที่ต้องการแทนที่ก่อน",
                parent=self.root,
            )
            return
        source_path = self._choose_boost_image(
            "เลือกภาพใหม่เพื่อแทนที่ Boots template ที่เลือก"
        )
        if not source_path:
            return
        try:
            template = self.boost_template_manager.replace_from_file(
                selected_id,
                source_path,
            )
        except (KeyError, OSError, ValueError) as error:
            messagebox.showerror(
                "แทนที่ Boots template ไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=self.root,
            )
            return
        self._refresh_boost_template_selector(template.template_id)
        self._publish_live_boost_settings(announce=True)
        print(
            f"[BOOST TEMPLATE] แทนที่ {template.label} จาก {source_path}; "
            "จะเริ่มใช้เมื่อเริ่มบอทรอบถัดไป"
        )

    def _delete_boost_template(self):
        selected_id = self.boost_target.get()
        if not selected_id:
            return
        selected = next(
            (
                template
                for template in self.boost_template_manager.templates
                if template.template_id == selected_id
            ),
            None,
        )
        if selected is None:
            self._refresh_boost_template_selector()
            return
        if not messagebox.askyesno(
            "ลบ Boots template",
            f"ต้องการลบ {selected.label} ใช่หรือไม่?",
            parent=self.root,
        ):
            return
        try:
            self.boost_template_manager.delete(selected_id)
        except (KeyError, OSError) as error:
            messagebox.showerror(
                "ลบ Boots template ไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=self.root,
            )
            return
        self._refresh_boost_template_selector()
        self._publish_live_boost_settings(announce=True)
        print(f"[BOOST TEMPLATE] ลบ {selected.label} แล้ว")

    def capture_game_frame(self):
        """Save the normalized client frame used by live image detection."""
        game_window = find_game_window()
        if game_window is None:
            messagebox.showwarning(
                "ไม่พบหน้าต่างเกม",
                f"ไม่พบหน้าต่าง {GAME_WINDOW_TITLE}; กรุณาเปิดเกมก่อน",
                parent=self.root,
            )
            return
        if game_window.isMinimized:
            messagebox.showwarning(
                "หน้าต่างเกมถูก minimize",
                "กรุณา restore หน้าต่างเกมก่อนจับภาพ",
                parent=self.root,
            )
            return

        frame, _region = capture_window_client_bgr(None, game_window)
        if frame is None or frame.size == 0:
            messagebox.showerror(
                "จับภาพไม่สำเร็จ",
                "ไม่สามารถอ่านภาพจากพื้นที่เกมได้",
                parent=self.root,
            )
            return

        detection_frame = normalize_for_template_matching(
            frame,
            TEMPLATE_REFERENCE_FRAME_SIZE,
        )
        output_dir = Path(runtime_data_path("captured_frames"))
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        output_path = output_dir / f"boots_capture_{timestamp}.png"
        try:
            saved = cv2.imwrite(str(output_path), detection_frame)
        except cv2.error as error:
            messagebox.showerror(
                "บันทึกภาพไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=self.root,
            )
            return
        if not saved:
            messagebox.showerror(
                "บันทึกภาพไม่สำเร็จ",
                f"ไม่สามารถเขียนไฟล์ {output_path}",
                parent=self.root,
            )
            return
        print(
            f"[CAPTURE] บันทึกเฟรม image search แล้ว: {output_path} "
            f"({detection_frame.shape[1]}x{detection_frame.shape[0]})"
        )
        messagebox.showinfo(
            "จับภาพสำเร็จ",
            f"บันทึกภาพแล้ว:\n{output_path}",
            parent=self.root,
        )

    def _close_settings_window(self, window):
        if window is None or not window.winfo_exists():
            self.settings_window = None
            return
        try:
            window.grab_release()
        except tk.TclError:
            pass
        window.destroy()
        self.settings_window = None

    def _choose_reward_root(self, window, path_variable):
        initial_directory = normalize_reward_root(path_variable.get())
        if not os.path.isdir(initial_directory):
            initial_directory = os.path.dirname(initial_directory)
        if not os.path.isdir(initial_directory):
            initial_directory = runtime_data_path("")
        selected = filedialog.askdirectory(
            parent=window,
            title="เลือกโฟลเดอร์หลักสำหรับเก็บภาพรางวัล",
            initialdir=initial_directory,
            mustexist=True,
        )
        if selected:
            path_variable.set(normalize_reward_root(selected))

    def _open_reward_root(self, window, path_variable):
        selected_path = normalize_reward_root(path_variable.get())
        if not os.path.isdir(selected_path):
            messagebox.showwarning(
                "ไม่พบโฟลเดอร์",
                f"ไม่พบโฟลเดอร์นี้:\n{selected_path}",
                parent=window,
            )
            return
        try:
            os.startfile(selected_path)
        except OSError as error:
            messagebox.showerror(
                "เปิดโฟลเดอร์ไม่สำเร็จ",
                f"{type(error).__name__}: {error}",
                parent=window,
            )

    def _save_settings_window(
        self,
        window,
        token_variable,
        chat_id_variable,
        path_variable,
    ):
        selected_root = normalize_reward_root(path_variable.get())
        try:
            save_reward_root_setting(selected_root)
        except OSError as error:
            messagebox.showerror(
                "บันทึกการตั้งค่าไม่สำเร็จ",
                f"เขียน {REWARD_PATH_CONFIG_FILE} ไม่สำเร็จ:\n"
                f"{type(error).__name__}: {error}",
                parent=window,
            )
            return

        new_token = token_variable.get().strip()
        new_chat_id = chat_id_variable.get().strip()
        try:
            save_telegram_setting(new_token, new_chat_id)
        except OSError as error:
            messagebox.showerror(
                "บันทึกการตั้งค่าไม่สำเร็จ",
                f"เขียน {TELEGRAM_CONFIG_FILE} ไม่สำเร็จ:\n"
                f"{type(error).__name__}: {error}",
                parent=window,
            )
            return

        self.token_var.set(new_token)
        self.chat_id_var.set(new_chat_id)
        self.reward_root_path = selected_root
        print(f"[SETTINGS] จำโฟลเดอร์ภาพแล้ว: {selected_root}")
        self._close_settings_window(window)

    def open_settings(self):
        if self.running:
            print("[SETTINGS] ปิดการแก้ไข Settings ระหว่างบอททำงาน")
            return
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        self.settings_window = window
        window.title("ตั้งค่า CookieRun Basic Mouse")
        window.configure(bg=self.BG)
        window.transient(self.root)
        window.resizable(True, False)

        token_variable = tk.StringVar(value=self.token_var.get())
        chat_id_variable = tk.StringVar(value=self.chat_id_var.get())
        path_variable = tk.StringVar(value=self.reward_root_path)

        content = tk.Frame(window, bg=self.BG)
        content.pack(fill="both", expand=True, padx=16, pady=14)
        content.columnconfigure(1, weight=1)

        for row, (label, variable) in enumerate(
            (("Bot Token", token_variable), ("Chat ID", chat_id_variable))
        ):
            tk.Label(
                content,
                text=label,
                bg=self.BG,
                fg=self.MUTED,
                font=("Segoe UI", 9),
            ).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=5)
            entry = tk.Entry(
                content,
                textvariable=variable,
                bg=self.INPUT_BG,
                fg=self.TEXT,
                insertbackground=self.TEXT,
                relief="flat",
                font=("Consolas", 9),
            )
            entry.grid(
                row=row,
                column=1,
                columnspan=2,
                sticky="ew",
                pady=5,
            )

        tk.Label(
            content,
            text="โฟลเดอร์ภาพ",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        path_entry = tk.Entry(
            content,
            textvariable=path_variable,
            state="readonly",
            readonlybackground=self.INPUT_BG,
            fg=self.TEXT,
            relief="flat",
            font=("Consolas", 9),
        )
        path_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

        path_buttons = tk.Frame(content, bg=self.BG)
        path_buttons.grid(row=3, column=1, columnspan=2, sticky="w", pady=(2, 10))
        tk.Button(
            path_buttons,
            text="เลือกโฟลเดอร์",
            command=lambda: self._choose_reward_root(window, path_variable),
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground="#39434d",
            activeforeground=self.TEXT,
            relief="flat",
            cursor="hand2",
            padx=10,
        ).grid(row=0, column=0, padx=(0, 7))
        tk.Button(
            path_buttons,
            text="เปิดโฟลเดอร์",
            command=lambda: self._open_reward_root(window, path_variable),
            bg=self.BLUE,
            fg="#10212d",
            activebackground="#4f9cca",
            relief="flat",
            cursor="hand2",
            padx=10,
        ).grid(row=0, column=1)

        actions = tk.Frame(content, bg=self.BG)
        actions.grid(row=4, column=0, columnspan=3, sticky="e")
        tk.Button(
            actions,
            text="บันทึก",
            command=lambda: self._save_settings_window(
                window,
                token_variable,
                chat_id_variable,
                path_variable,
            ),
            bg=self.GREEN,
            fg="white",
            activebackground="#39945f",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=10,
        ).grid(row=0, column=0, padx=(0, 7))
        tk.Button(
            actions,
            text="ยกเลิก",
            command=lambda: self._close_settings_window(window),
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground="#39434d",
            activeforeground=self.TEXT,
            relief="flat",
            cursor="hand2",
            width=10,
        ).grid(row=0, column=1)

        window.protocol("WM_DELETE_WINDOW", lambda: self._close_settings_window(window))
        window.update_idletasks()
        width = max(560, window.winfo_reqwidth())
        height = window.winfo_reqheight()
        left = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - width) // 2)
        top = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - height) // 2)
        window.geometry(f"{width}x{height}+{left}+{top}")
        window.grab_set()
        window.focus_force()

    def _set_feature_state(self, key, enabled):
        if key in LOCKED_FEATURES:
            enabled = False
        with self.feature_lock:
            self.feature_state[key] = bool(enabled)
        print(f"[LIVE CONFIG] {key} = {bool(enabled)}")

    def _get_feature_snapshot(self):
        with self.feature_lock:
            return self.feature_state.copy()

    def _get_live_boost_snapshot(self):
        with self.boost_lock:
            return self.live_boost_state

    def _publish_live_boost_settings(self, announce=False):
        snapshot = BoostSettingsSnapshot(
            boost_mode=self.boost_mode.get(),
            random_boost_percent=self.last_valid_random_boost_percent,
            boost_target=self.boost_target.get(),
        )
        with self.boost_lock:
            self.live_boost_state = snapshot
        if announce:
            print(
                "[LIVE CONFIG] Boots ชุดใหม่จะเริ่มใช้เมื่อเข้าหน้า Boots รอบถัดไป: "
                f"mode={snapshot.boost_mode}, "
                f"percent={snapshot.random_boost_percent:.1f}, "
                f"target={snapshot.boost_target}"
            )
        return snapshot

    def _on_boost_mode_changed(self):
        self._sync_boost_percent_visibility()
        self._publish_live_boost_settings(announce=True)

    def _on_boost_target_changed(self):
        self._publish_live_boost_settings(announce=True)

    def _commit_boost_percent(self, event=None):
        raw_value = self.random_boost_percent_var.get().strip()
        try:
            percent = float(raw_value)
        except ValueError:
            percent = None
        if percent is None or percent < 0.0 or percent > 100.0:
            print(
                "[LIVE CONFIG WARNING] เปอร์เซ็นต์ Boots ต้องอยู่ระหว่าง 0-100; "
                f"ใช้ค่าล่าสุด {self.last_valid_random_boost_percent:g}%"
            )
            self.random_boost_percent_var.set(
                f"{self.last_valid_random_boost_percent:g}"
            )
        else:
            self.last_valid_random_boost_percent = percent
            self.random_boost_percent_var.set(f"{percent:g}")
            self._publish_live_boost_settings(announce=self.running)
        if event is not None and getattr(event, "keysym", "") == "Return":
            return "break"
        return None

    def _set_locked_widgets(self, state):
        for widget in self.locked_widgets:
            restored_state = (
                "readonly"
                if state == "normal" and widget in self.readonly_locked_widgets
                else state
            )
            widget.config(state=restored_state)

    def _sync_boost_percent_visibility(self):
        if not hasattr(self, "random_boost_percent_entry"):
            return
        widgets = (
            self.boost_percent_label,
            self.random_boost_percent_entry,
            self.boost_percent_suffix,
        )
        if self.boost_mode.get() == BOOST_MODE_RANDOM:
            for widget in widgets:
                widget.grid()
        else:
            for widget in widgets:
                widget.grid_remove()

    def _start_hotkey_listener(self):
        try:
            self.hotkey_listener = keyboard.Listener(on_press=self._on_hotkey_press)
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()
            print("[HOTKEY] เปิดใช้ F8 สำหรับ Pause/Resume แล้ว")
        except (OSError, RuntimeError) as error:
            print(f"[HOTKEY WARNING] เปิดใช้ F8 ไม่สำเร็จ: {type(error).__name__}")

    def _stop_hotkey_listener(self):
        listener = self.hotkey_listener
        self.hotkey_listener = None
        if listener is None:
            return
        try:
            listener.stop()
        except (OSError, RuntimeError):
            pass

    def _on_hotkey_press(self, key):
        if key != keyboard.Key.f8:
            return None
        now = time.monotonic()
        if now - self.last_hotkey_time < 0.35:
            return None
        self.last_hotkey_time = now
        if self.closing:
            return False
        self.root.after(0, self._toggle_pause_from_hotkey)
        return None

    def _toggle_pause_from_hotkey(self):
        if not self.running:
            return
        if str(self.pause_button.cget("state")) != "normal":
            return
        print("[HOTKEY] F8 -> Toggle Pause/Resume")
        self.toggle_pause()

    def _get_target_run_count(self):
        raw_value = self.run_count_var.get().strip()
        if not raw_value:
            return None
        try:
            numeric_value = float(raw_value)
        except ValueError:
            print("[CONFIG ERROR] จำนวนรอบต้องเป็นตัวเลข เช่น 0, 5, 10")
            return False
        if not numeric_value.is_integer():
            print("[CONFIG ERROR] จำนวนรอบต้องเป็นเลขเต็ม เช่น 0, 5, 10")
            return False
        run_count = int(numeric_value)
        if run_count < 0:
            print("[CONFIG ERROR] จำนวนรอบต้องไม่ติดลบ")
            return False
        return run_count or None

    def _get_random_boost_percent(self):
        self._commit_boost_percent()
        return self._get_live_boost_snapshot().random_boost_percent

    def toggle_bot(self):
        if self.running:
            self.controller.stop(send_notification=True)
            self.paused = False
            self.status_var.set("กำลังหยุดและคืนทรัพยากร...")
            self.status_label.config(fg=self.ACCENT)
            self.toggle_button.config(state="disabled")
            self.pause_button.config(
                text="พักชั่วคราว",
                bg=self.ACCENT,
                activebackground="#d9a636",
                state="disabled",
            )
            return

        target_run_count = self._get_target_run_count()
        if target_run_count is False:
            return
        self._on_capture_mode_selected()
        self._get_random_boost_percent()
        boost_snapshot = self._get_live_boost_snapshot()
        available_boost_ids = {
            template.template_id
            for template in self.boost_template_manager.templates
            if self.boost_template_manager.path_for(template).is_file()
        }
        if (
            boost_snapshot.boost_mode != BOOST_MODE_NEVER
            and boost_snapshot.boost_target not in available_boost_ids
        ):
            print(
                "[CONFIG ERROR] กรุณาเพิ่มหรือเลือก Boots template "
                "ที่ยังมีไฟล์อยู่ก่อนเริ่ม"
            )
            return
        try:
            resolved_reward_root, reward_warning = resolve_reward_root(
                self.reward_root_path
            )
        except RuntimeError as error:
            print(f"[CONFIG ERROR] {error}")
            return
        if reward_warning:
            print(f"[REWARD RECORD WARNING] {reward_warning}")

        runtime_config = RuntimeConfig(
            token=self.token_var.get().strip(),
            chat_id=self.chat_id_var.get().strip(),
            calibration_mode=self.calibration_mode.get(),
            target_run_count=target_run_count,
            boost_mode=boost_snapshot.boost_mode,
            random_boost_percent=boost_snapshot.random_boost_percent,
            boost_target=boost_snapshot.boost_target,
            reward_root=resolved_reward_root,
        )
        if runtime_config.calibration_mode not in (
            CALIBRATION_MODE_AUTO,
            CALIBRATION_MODE_DEFAULT,
            CALIBRATION_MODE_CUSTOM,
        ):
            print("[CONFIG ERROR] กรุณาเลือกโหมดพื้นที่แคปหน้าจอ")
            return
        if runtime_config.boost_mode not in (
            BOOST_MODE_ALWAYS,
            BOOST_MODE_NEVER,
            BOOST_MODE_RANDOM,
        ):
            print("[CONFIG ERROR] กรุณาเลือกโหมดสุ่ม Boots")
            return
        if not self.controller.start(runtime_config):
            print("[BOT] Worker เดิมยังหยุดไม่สมบูรณ์ กรุณารอสักครู่")
            return

        self.running = True
        self.paused = False
        self._set_locked_widgets("disabled")
        self.toggle_button.config(
            text="หยุดการทำงาน",
            bg=self.RED,
            activebackground="#bf4747",
            state="normal",
        )
        self.pause_button.config(
            text="พักชั่วคราว",
            bg=self.ACCENT,
            activebackground="#d9a636",
            state="normal",
        )
        if runtime_config.calibration_mode == CALIBRATION_MODE_CUSTOM:
            self.status_var.set("กำลังเตรียม Calibration 4 มุม...")
        elif runtime_config.calibration_mode == CALIBRATION_MODE_AUTO:
            self.status_var.set("กำลังจับหน้าต่าง LDPlayer อัตโนมัติ...")
        else:
            self.status_var.set("กำลังเตรียมระบบ...")
        if target_run_count is not None:
            print(f"[CONFIG] ตั้งให้หยุดหลังจบ {target_run_count} รอบ")
        else:
            print("[CONFIG] จำนวนรอบ = ไม่จำกัด")
        if runtime_config.boost_mode == BOOST_MODE_RANDOM:
            print(
                f"[CONFIG] Boots = สุ่มบางตา "
                f"({runtime_config.random_boost_percent:.1f}%)"
            )
        elif runtime_config.boost_mode == BOOST_MODE_NEVER:
            print("[CONFIG] Boots = ข้ามทุกตา")
        else:
            print("[CONFIG] Boots = สุ่มทุกตา")
        boost_target_label = get_boost_target_label(runtime_config.boost_target)
        print(f"[CONFIG] Boost เป้าหมาย = {boost_target_label}")
        print(f"[CONFIG] โฟลเดอร์ภาพรางวัล = {runtime_config.reward_root}")
        print(
            f"[CONFIG] Relay = "
            f"{'เปิด' if self.feature_state.get('RELAY', False) else 'ปิด'}"
        )
        self.status_label.config(fg=self.ACCENT)

    def toggle_pause(self):
        if not self.running:
            return

        if self.paused:
            if not self.controller.resume():
                return
            self.paused = False
            self.pause_button.config(
                text="พักชั่วคราว",
                bg=self.ACCENT,
                activebackground="#d9a636",
            )
            self.status_var.set("บอทกำลังทำงาน")
            self.status_label.config(fg=self.GREEN)
            return

        if not self.controller.pause():
            return
        self.paused = True
        self.pause_button.config(
            text="ทำงานต่อ",
            bg=self.BLUE,
            activebackground="#4f9cca",
        )
        self.status_var.set("บอทพักชั่วคราว")
        self.status_label.config(fg=self.BLUE)

    def reset_fatigue_rounds(self):
        self.controller.reset_fatigue()

    def _apply_worker_status(self, status):
        if status == "preparing":
            self.status_var.set("กำลังโหลด Template...")
            self.status_label.config(fg=self.ACCENT)
        elif status == "calibrating":
            self.status_var.set("รอคลิก Calibration ให้ครบ 4 มุม")
            self.status_label.config(fg=self.BLUE)
        elif status == "running":
            self.paused = False
            self.status_var.set("บอทกำลังทำงาน")
            self.status_label.config(fg=self.GREEN)
            if self.running:
                self.pause_button.config(
                    text="พักชั่วคราว",
                    bg=self.ACCENT,
                    activebackground="#d9a636",
                    state="normal",
                )
        elif status == "paused":
            self.paused = True
            self.status_var.set("บอทพักชั่วคราว")
            self.status_label.config(fg=self.BLUE)
            if self.running:
                self.pause_button.config(
                    text="ทำงานต่อ",
                    bg=self.BLUE,
                    activebackground="#4f9cca",
                    state="normal",
                )
        elif status == "stopped":
            self.paused = False
            self.status_var.set("บอทหยุดทำงาน")
            self.status_label.config(fg=self.RED)

    def _reset_stopped_ui(self):
        self.running = False
        self.paused = False
        self._set_locked_widgets("normal")
        self.toggle_button.config(
            text="เริ่มทำงาน",
            bg=self.GREEN,
            activebackground="#39945f",
            state="normal",
        )
        self.pause_button.config(
            text="พักชั่วคราว",
            bg=self.ACCENT,
            activebackground="#d9a636",
            state="disabled",
        )
        self.status_var.set("บอทหยุดทำงาน")
        self.status_label.config(fg=self.RED)

    def _poll_queues(self):
        inserted = False
        while True:
            try:
                text = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log.insert("end", text)
            inserted = True
        if inserted:
            self.log.see("end")
            if int(self.log.index("end-1c").split(".")[0]) > 1000:
                self.log.delete("1.0", "350.0")

        while True:
            try:
                action, value = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if action == "status":
                self._apply_worker_status(value)
            elif action == "finished":
                self._reset_stopped_ui()
            elif action == "update_checked":
                self._on_update_checked(*value)
            elif action == "update_progress":
                done, total = value
                percent = f" {done * 100 // total}%" if total else ""
                self.update_button.config(text=f"⬇ กำลังโหลด{percent}")
            elif action == "update_downloaded":
                self._on_update_downloaded(value)
            elif action == "update_failed":
                self._on_update_failed(value)

        if not self.closing:
            self.root.after(100, self._poll_queues)

    # ------------------------------------------------------------ self-update
    def _cleanup_old_versions(self):
        try:
            removed = updater.cleanup_old_versions(Path(sys.executable), BOT_VERSION)
        except Exception as error:  # cleanup is best-effort only
            print(f"[UPDATE] ลบเวอร์ชันเก่าไม่สำเร็จ: {type(error).__name__}")
            return
        for name in removed:
            print(f"[UPDATE] ลบเวอร์ชันเก่าแล้ว: {name}")

    def check_for_updates(self, silent=False):
        if self.update_busy or self.closing:
            return
        self.update_busy = True
        if not silent:
            self.update_button.config(text="⟳ กำลังตรวจ...")

        def worker():
            try:
                result = updater.fetch_latest(GITHUB_REPO)
            except updater.UpdateError as error:
                result = error
            except Exception as error:
                result = updater.UpdateError(f"ตรวจอัปเดตไม่สำเร็จ ({type(error).__name__})")
            self.ui_queue.put(("update_checked", (silent, result)))

        threading.Thread(target=worker, daemon=True).start()

    def on_update_button(self):
        if self.update_info is not None:
            self._ask_install_update(self.update_info)
        else:
            self.check_for_updates(silent=False)

    def _on_update_checked(self, silent, result):
        self.update_busy = False
        if isinstance(result, updater.UpdateError):
            self.update_button.config(text="⟳ อัปเดต")
            print(f"[UPDATE] {result}")
            if not silent:
                messagebox.showwarning("ตรวจอัปเดต", str(result), parent=self.root)
            return
        if not updater.is_newer(result.version, BOT_VERSION):
            self.update_button.config(text="⟳ อัปเดต")
            print(f"[UPDATE] ใช้เวอร์ชันล่าสุดอยู่แล้ว (v{BOT_VERSION})")
            if not silent:
                messagebox.showinfo("ตรวจอัปเดต", f"ใช้เวอร์ชันล่าสุดอยู่แล้ว (v{BOT_VERSION})", parent=self.root)
            return
        self.update_info = result
        self.update_button.config(text=f"⬆ v{result.version}", bg=self.ACCENT, fg="#1b1b1b")
        print(f"[UPDATE] มีเวอร์ชันใหม่ v{result.version} (ตอนนี้ v{BOT_VERSION}) กดปุ่ม ⬆ เพื่ออัปเดต")
        if not self.running:
            self._ask_install_update(result)

    def _ask_install_update(self, info):
        if self.running:
            messagebox.showinfo("อัปเดต", "กด \"หยุดการทำงาน\" ก่อน แล้วค่อยกดอัปเดต", parent=self.root)
            return
        notes = info.notes
        if len(notes) > 700:
            notes = notes[:700].rstrip() + " ..."
        if not getattr(sys, "frozen", False):
            messagebox.showinfo(
                "มีเวอร์ชันใหม่",
                f"มีเวอร์ชันใหม่ v{info.version}\n\nตอนนี้รันจากซอร์สโค้ด ให้อัปเดตด้วย git pull\n{info.page_url}",
                parent=self.root,
            )
            return
        size_mb = info.zip_size / (1024 * 1024) if info.zip_size else 0
        if not messagebox.askyesno(
            "มีเวอร์ชันใหม่",
            f"มีเวอร์ชันใหม่ v{info.version} (ตอนนี้ v{BOT_VERSION})\n\n{notes}\n\n"
            f"ดาวน์โหลด {size_mb:.0f} MB และอัปเดตเลยไหม?\n"
            "(การตั้งค่าและ Telegram ที่บันทึกไว้จะใช้ต่อได้เหมือนเดิม)",
            parent=self.root,
        ):
            return
        self._start_update_download(info)

    def _start_update_download(self, info):
        if self.update_busy:
            return
        self.update_busy = True
        self.update_button.config(text="⬇ กำลังโหลด", state="disabled")
        target_dir = Path(sys.executable).resolve().parent

        def progress(done, total):
            self.ui_queue.put(("update_progress", (done, total)))

        def worker():
            try:
                new_exe = updater.download_update(info, target_dir, progress=progress)
            except updater.UpdateError as error:
                self.ui_queue.put(("update_failed", str(error)))
                return
            except Exception as error:
                self.ui_queue.put(("update_failed", f"อัปเดตไม่สำเร็จ ({type(error).__name__})"))
                return
            self.ui_queue.put(("update_downloaded", new_exe))

        print(f"[UPDATE] กำลังดาวน์โหลด v{info.version} ...")
        threading.Thread(target=worker, daemon=True).start()

    def _on_update_failed(self, message):
        self.update_busy = False
        self.update_button.config(text="⬆ ลองอีกครั้ง", state="normal")
        print(f"[UPDATE] {message}")
        messagebox.showerror("อัปเดตไม่สำเร็จ", message, parent=self.root)

    def _on_update_downloaded(self, new_exe):
        self.update_busy = False
        print(f"[UPDATE] ดาวน์โหลดเสร็จ: {new_exe.name}")
        messagebox.showinfo(
            "อัปเดตเสร็จแล้ว",
            f"กด OK เพื่อเปิดเวอร์ชันใหม่\n({new_exe.name})\n\nเวอร์ชันเก่าจะถูกลบให้อัตโนมัติ",
            parent=self.root,
        )
        try:
            updater.launch(new_exe)
        except OSError as error:
            self._on_update_failed(f"เปิดเวอร์ชันใหม่ไม่ได้ ({type(error).__name__}) ลองเปิด {new_exe.name} เอง")
            return
        self.on_close()

    def on_close(self):
        if self.closing:
            return
        self.closing = True
        self.running = False
        self.paused = False
        if self.settings_window is not None:
            try:
                self._close_settings_window(self.settings_window)
            except tk.TclError:
                self.settings_window = None
        self._stop_hotkey_listener()
        self.controller.stop(send_notification=False)
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.root.destroy()


def main():
    root = tk.Tk()
    CookieBotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
