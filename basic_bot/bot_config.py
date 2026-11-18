from dataclasses import dataclass


BOT_VERSION = "2.18.19"
BOT_NAME = f"CookieRun Basic Mouse Bot v{BOT_VERSION}"
MULTI_BOT_NAME = f"CookieRun Multi Mouse Bot v{BOT_VERSION}"
GAME_WINDOW_TITLE = "main_cookierun"
WINDOW_TITLE_FALLBACK_KEYWORDS = ("main_cookierun", "cookierun")
LDPLAYER_WINDOW_CLASS = "LDPlayerMainFrame"
# MuMu may expose the Android display as "Android Device" and uses Qt-based
# window classes in several releases.
MUMU_WINDOW_CLASS_PREFIXES = ("Qt",)
MUMU_WINDOW_TITLE_KEYWORDS = ("android device", "mumu", "ร้าน mumu")
CALIBRATION_MODE_AUTO = "AUTO"
CALIBRATION_MODE_DEFAULT = "DEFAULT"
CALIBRATION_MODE_CUSTOM = "CUSTOM"
DEFAULT_SCAN_REGION = {"left": -959, "top": 174, "width": 835, "height": 466}
BOOST_MODE_ALWAYS = "ALWAYS"
BOOST_MODE_NEVER = "NEVER"
BOOST_MODE_RANDOM = "RANDOM"
DEFAULT_RANDOM_BOOST_PERCENT = 65.0
BOOST_TARGET_DOUBLE_COIN = "DOUBLE_COIN"
BOOST_TARGET_BASE_SPEED = "BASE_SPEED"
DEFAULT_BOOST_TARGET = BOOST_TARGET_DOUBLE_COIN

# Telegram credentials are NOT built into the program. They are loaded at
# runtime from TELEGRAM_CONFIG_FILE beside the script/EXE (or entered in the
# Settings window, which saves them there). Never commit or ship that file.
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
TELEGRAM_CONFIG_FILE = "telegram_config.json"
REWARD_RECORDS_DIR = "reward_records"
REWARD_PATH_CONFIG_FILE = "reward_path.json"

MATCH_THRESHOLD = 0.65
# All current templates were collected from this LDPlayer client-frame size.
# Detection normalizes each live frame to this size and maps the result back
# before clicking, so window placement and supported emulator resolutions work.
TEMPLATE_REFERENCE_FRAME_SIZE = (840, 486)
FAST_LOOP_INTERVAL = 0.15
ECO_LOOP_INTERVAL_RANGE = (0.7, 0.8)
FAST_SCAN_AFTER_PLAY = 5.0
PERFORMANCE_LOG_INTERVAL = 30.0

CAPTCHA_ALERT_AFTER = 20.0
CAPTCHA_FRAME_INTERVAL = 0.5
CAPTCHA_RECHECK_INTERVAL = 5.0
CAPTCHA_DIFF_THRESHOLD = 20
CAPTCHA_MOVEMENT_THRESHOLD = 2500
NO_BUTTON_ALERT_AFTER = 90.0
TELEGRAM_COOLDOWN = 180.0
BOOTS_STUCK_ALERT_AFTER = 90.0
# One initial click plus up to three retries while the Boots screen is still
# loading. Each retry samples a fresh point inside MULTI_BUY's safe click area.
MULTI_BUY_MAX_ATTEMPTS = 4
PLAY_STUCK_MAX_ATTEMPTS = 3
PLAY_CLICK_VERIFY_DELAY = 1.0
PLAY_TRANSITION_VERIFY_START_DELAY = 0.50
PLAY_TRANSITION_TIMEOUT = 5.0
PLAY_SUCCESS_CONFIRM_FRAMES = 3
PLAY_TRANSITION_MARKER_THRESHOLD = 0.65
PLAY_RETRY_SHORT_DELAY_RANGE = (1.0, 5.0)
PLAY_RETRY_LONG_DELAY_RANGE = (10.0, 30.0)
PLAY_RETRY_LONG_DELAY_PROBABILITY = 0.10
FALLBACK_MAX_ATTEMPTS = 10
# CLOSE is rejected when its match lands on a lower-confidence STOP candidate.
# This protects against transient resize/animation differences in live frames.
STOP_GUARD_MATCH_THRESHOLD = 0.45
STOP_CLOSE_CENTER_DISTANCE = 36

PLAY_FATIGUE_ROUND_RANGE = (10, 20)
OK_FATIGUE_ROUND_RANGE = (20, 40)
FATIGUE_DELAY_RANGE = (30.0, 90.0)
MOUSE_HOLD_DELAY_RANGE = (0.15, 0.28)
INTER_CLICK_DELAY_RANGE = (0.15, 0.30)
REPEAT_CLICK_COOLDOWN = 1.0

# In-game Bonus Quit flow. Coordinates were measured from the 949x533
# PrintWindow client frames in dev/captures and are mapped to the normalized
# detection frame before matching/clicking.
BONUS_FLOW_REFERENCE_FRAME_SIZE = (949, 533)
BONUS_TRIGGER_TEMPLATE = "img_bonus2.png"
BONUS_TRIGGER_SEARCH_AREA = (39, 0, 346, 52)
BONUS_TRIGGER_MATCH_THRESHOLD = 0.90
BONUS_PAUSE_CLICK_AREA = (835, 5, 915, 51)
BONUS_QUIT_TEMPLATE = "quit_btn.png"
BONUS_QUIT_1_CLICK_AREA = (351, 281, 580, 347)
BONUS_QUIT_2_CLICK_AREA = (351, 247, 583, 313)
BONUS_QUIT_SEARCH_PADDING = 12
BONUS_QUIT_MATCH_THRESHOLD = 0.90
BONUS_FLOW_MAX_ATTEMPTS = 3
BONUS_FLOW_TRANSITION_TIMEOUT = 5.0
BONUS_FLOW_ABSENT_CONFIRM_FRAMES = 2
# Delay before pressing the in-game Pause button after Bonus is detected:
# common 5-10s, occasional 10-20s, and rare 20-30s.
BONUS_FLOW_DELAY_TIERS = (
    ("COMMON", 0.85, (5.0, 10.0)),
    ("OCCASIONAL", 0.12, (10.0, 20.0)),
    ("RARE", 0.03, (20.0, 30.0)),
)
BONUS_PAUSE_PRE_CLICK_DELAY_RANGE = (0.20, 0.50)
BONUS_QUIT_PRE_CLICK_DELAY_RANGE = (0.40, 0.90)

# Start-of-run jump flow. Coordinates are measured from the same 949x533
# PrintWindow client frame used by the Bonus flow and are mapped to the live
# detection/client frame before each click.
START_JUMP_REFERENCE_FRAME_SIZE = (949, 533)
START_JUMP_CLICK_AREA = (11, 361, 221, 517)
# The first tap should happen as soon as a person notices gameplay. The rest
# of the taps are spread across the opening seconds, with a small late tail.
START_JUMP_INITIAL_DELAY_RANGE = (0.0, 0.5)
START_JUMP_FLOW_DURATION_TIERS = (
    ("NORMAL", 0.95, (4.0, 7.0)),
    ("LATE", 0.05, (7.0, 10.0)),
)
START_JUMP_TOTAL_CLICKS_RANGE = (8, 15)
START_JUMP_GROUP_GAP_RANGE = (0.22, 0.65)
START_JUMP_DOUBLE_CLICK_PROBABILITY = 0.30
START_JUMP_TRIPLE_CLICK_PROBABILITY = 0.06
START_JUMP_HOLD_DELAY_RANGE = (0.08, 0.16)
START_JUMP_INTER_CLICK_DELAY_RANGE = (0.16, 0.30)

ENABLE_CONFIG = {
    "PLAY": True,
    "BUFF": True,
    "START_JUMP": False,
    # Bonus Quit is opt-in from the UI so existing runs keep their behavior.
    "BONUS_QUIT_FLOW": False,
    "RELAY": False,
    "OK": True,
    "OPEN_ALL": True,
    "CONFIRM": True,
    "CONFIRM_MAIN": True,
    "CLOSE": False,
}

# Features that are locked off in this build: the UI checkbox is disabled and
# the bot never runs them, regardless of ENABLE_CONFIG or live UI changes.
LOCKED_FEATURES = frozenset({"START_JUMP", "BONUS_QUIT_FLOW", "CLOSE"})
for _locked_feature in LOCKED_FEATURES:
    ENABLE_CONFIG[_locked_feature] = False

# PLAY fallback in the 840x486 template reference frame.  The previous value
# came from an older 999x579 desktop capture and became out-of-bounds after
# the bot switched to the 840x486-normalized PrintWindow render surface.
PLAY_BTN = (623, 435)
BUFF_BTN = (537, 316)
OK_BTN = (382, 543)
OPEN_ALL_BTN = (530, 561)
CONFIRM_BTN = (530, 561)
CONFIRM_MAIN_BTN = (530, 561)
CLOSE_BTN = (0, 0)

BOOTS_SCREEN_TEMPLATE = "boots_screen.png"
CONFIRM_MAIN_TEMPLATE = "confirm_main_btn.png"
CLOSE_TEMPLATE = "close_btn.png"
STOP_TEMPLATE = "stop_btn.png"
DOUBLE_COIN_TEMPLATE = "double_coin.png"
BASE_SPEED_TEMPLATE = "base_speed.png"
MAGNET_TEMPLATE = "magnet.png"
BOOST_TARGET_MAGNET = "MAGNET"
BOOST_TARGET_TEMPLATES = {
    BOOST_TARGET_DOUBLE_COIN: DOUBLE_COIN_TEMPLATE,
    BOOST_TARGET_BASE_SPEED: BASE_SPEED_TEMPLATE,
    BOOST_TARGET_MAGNET: MAGNET_TEMPLATE,
}
BOOST_TEMPLATE_STORAGE_DIR = "boost_templates"
# base_speed.png was cropped from this raw capture. The loader scales it to the
# same 840x486 reference frame used by live template matching.
TEMPLATE_SOURCE_FRAME_SIZES = {
    BASE_SPEED_TEMPLATE: (1101, 636),
    # magnet.png was cropped from the 999x579 AUTO capture frame. Live frames
    # are normalized to TEMPLATE_REFERENCE_FRAME_SIZE before matching.
    MAGNET_TEMPLATE: (999, 579),
    CONFIRM_MAIN_TEMPLATE: (999, 579),
    CLOSE_TEMPLATE: (999, 579),
    STOP_TEMPLATE: (999, 579),
    BONUS_TRIGGER_TEMPLATE: BONUS_FLOW_REFERENCE_FRAME_SIZE,
    BONUS_QUIT_TEMPLATE: BONUS_FLOW_REFERENCE_FRAME_SIZE,
}
OPTION_BTN = (334, 406)
MULTI_BTN = (693, 204)
MULTI_BUY_BTN = (403, 405)
RELAY_BTN = (407, 254)


@dataclass(frozen=True)
class ButtonAction:
    name: str
    template_name: str
    fixed_position: tuple
    pre_click_delay: tuple
    post_click_delay: float
    minimum_clicks: int
    maximum_clicks: int
    jitter: int
    bounds: tuple | None
    safe_click_ratio: tuple
    click_area: tuple | None = None


@dataclass(frozen=True)
class RuntimeConfig:
    token: str
    chat_id: str
    calibration_mode: str
    target_run_count: int | None
    boost_mode: str
    random_boost_percent: float
    boost_target: str
    reward_root: str | None = None


# BUFF has first priority because it is visible for only a few seconds.
BUTTON_ACTIONS = (
    ButtonAction(
        "BUFF",
        "buff_template.png",
        BUFF_BTN,
        (0.12, 0.28),
        0.10,
        2,
        3,
        5,
        (527, 587, 264, 367),
        (0.55, 0.55),
    ),
    ButtonAction(
        "RELAY",
        "relay_bnt.png",
        RELAY_BTN,
        (0.25, 0.60),
        0.80,
        1,
        1,
        5,
        None,
        (0.68, 0.68),
    ),
    ButtonAction(
        "PLAY",
        "play_template.png",
        PLAY_BTN,
        (0.20, 0.50),
        0.10,
        1,
        1,
        10,
        (642, 868, 537, 568),
        (0.72, 0.58),
    ),
    ButtonAction(
        "OK",
        "ok_template.png",
        OK_BTN,
        (2.00, 5.00),
        2.00,
        1,
        1,
        10,
        (260, 492, 519, 575),
        (0.72, 0.58),
    ),
    ButtonAction(
        "OPEN_ALL",
        "open_all.png",
        OPEN_ALL_BTN,
        (1.50, 3.00),
        2.50,
        1,
        2,
        8,
        (416, 631, 560, 589),
        (0.72, 0.58),
    ),
    ButtonAction(
        "CONFIRM",
        "confirm.png",
        CONFIRM_BTN,
        (1.00, 2.50),
        2.00,
        1,
        1,
        8,
        (416, 631, 560, 589),
        (0.72, 0.58),
    ),
)


# These actions are only considered after the normal actions above have not
# been found. Each popup action is limited independently per popup session.
FALLBACK_BUTTON_ACTIONS = (
    ButtonAction(
        "CONFIRM_MAIN",
        CONFIRM_MAIN_TEMPLATE,
        CONFIRM_MAIN_BTN,
        (0.80, 2.00),
        1.00,
        1,
        1,
        8,
        None,
        (0.72, 0.58),
    ),
    ButtonAction(
        "CLOSE",
        CLOSE_TEMPLATE,
        CLOSE_BTN,
        (0.20, 0.60),
        0.50,
        1,
        1,
        5,
        None,
        (0.72, 0.72),
    ),
)


# Boots-screen actions are only considered while the bot is in the boost screen
# flow. click_area values are template-center-relative bounds measured with
# select_click_bounds.py from the same client-area frame used by detection.
BOOTS_BUTTON_ACTIONS = (
    ButtonAction(
        "MULTI_BUY",
        "multi_buy.png",
        MULTI_BUY_BTN,
        (0.60, 1.20),
        3.00,
        1,
        1,
        6,
        None,
        (0.76, 0.62),
        (-80, 79, -30, 32),
    ),
    ButtonAction(
        "MULTI",
        "multi.png",
        MULTI_BTN,
        (0.40, 0.90),
        0.80,
        1,
        1,
        5,
        None,
        (0.72, 0.58),
        (-29, 34, -27, 24),
    ),
    ButtonAction(
        "OPTION",
        "option.png",
        OPTION_BTN,
        (0.40, 0.90),
        0.80,
        1,
        1,
        5,
        None,
        (0.72, 0.58),
        (-46, 54, -46, 55),
    ),
)

CLICKABLE_ACTIONS = BUTTON_ACTIONS + FALLBACK_BUTTON_ACTIONS + BOOTS_BUTTON_ACTIONS
TEMPLATE_NAMES = tuple(
    dict.fromkeys(
        [action.template_name for action in CLICKABLE_ACTIONS]
        + [
            BOOTS_SCREEN_TEMPLATE,
            STOP_TEMPLATE,
            BONUS_TRIGGER_TEMPLATE,
            BONUS_QUIT_TEMPLATE,
        ]
    )
)
ACTION_BY_NAME = {action.name: action for action in CLICKABLE_ACTIONS}
