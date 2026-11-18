import argparse
import json
import sys
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
        TEMPLATE_REFERENCE_FRAME_SIZE,
    )
    from .capture_detect_frame import get_capture_region, normalize_mode
    from .frame_normalization import normalize_for_template_matching
except ImportError:
    from basic_bot.bot_config import (
        BOT_VERSION,
        CALIBRATION_MODE_AUTO,
        TEMPLATE_REFERENCE_FRAME_SIZE,
    )
    from basic_bot.capture_detect_frame import get_capture_region, normalize_mode
    from basic_bot.frame_normalization import normalize_for_template_matching


WINDOW_NAME = "Select click bounds - drag rectangle, Enter=print JSON, Esc=cancel"
BOX_COLOR = (60, 230, 120)
TEMPLATE_COLOR = (80, 180, 255)
TEXT_COLOR = (245, 245, 245)


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Select a click bounds rectangle on the same frame shape used by "
            "the bot's normalized image detection."
        )
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Use an existing captured frame instead of capturing LDPlayer live.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Template image used as the anchor for template-relative click_area.",
    )
    parser.add_argument(
        "--name",
        default="UNNAMED_ACTION",
        help="Action/template label printed in the JSON output.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "default", "custom"),
        default="auto",
        help="Capture mode when --image is not provided.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.65,
        help="Template match threshold for highlighting the anchor.",
    )
    return parser


def load_frame(args):
    if args.image is not None:
        frame = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
        if frame is None or frame.size == 0:
            raise RuntimeError(f"อ่านภาพไม่สำเร็จ: {args.image}")
        return frame, {
            "source": "image",
            "image_path": str(args.image),
            "capture_mode": None,
            "region": None,
            "window_title": None,
        }

    mode = normalize_mode(args.mode)
    if mode != CALIBRATION_MODE_AUTO:
        raise RuntimeError(
            "select_click_bounds.py รองรับ live capture เฉพาะ --mode auto; "
            "ถ้าต้องใช้ default/custom ให้แคปด้วย capture_detect_frame.py ก่อน"
        )

    with mss.MSS() as screen_capture:
        frame, region, window_title = get_capture_region(screen_capture, mode)
    if frame is None or frame.size == 0:
        raise RuntimeError("ภาพที่แคปได้ไม่มีข้อมูล")
    return frame, {
        "source": "live_capture",
        "image_path": None,
        "capture_mode": mode,
        "region": region,
        "window_title": window_title,
    }


def find_template_match(frame, template_path, threshold):
    if template_path is None:
        return None

    template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if template is None or template.size == 0:
        raise RuntimeError(f"อ่าน template ไม่สำเร็จ: {template_path}")

    frame_height, frame_width = frame.shape[:2]
    template_height, template_width = template.shape[:2]
    if template_height > frame_height or template_width > frame_width:
        raise RuntimeError(
            f"template ใหญ่กว่า frame: {template_width}x{template_height} > "
            f"{frame_width}x{frame_height}"
        )

    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, top_left = cv2.minMaxLoc(result)
    center = (
        int(top_left[0] + template_width / 2),
        int(top_left[1] + template_height / 2),
    )
    return {
        "template_path": str(template_path),
        "score": float(score),
        "passed_threshold": bool(score >= threshold),
        "top_left": [int(top_left[0]), int(top_left[1])],
        "center": [center[0], center[1]],
        "size": [int(template_width), int(template_height)],
    }


def normalize_rect(start, end, frame_shape):
    frame_height, frame_width = frame_shape[:2]
    x1, y1 = start
    x2, y2 = end
    left = max(0, min(int(x1), int(x2), frame_width - 1))
    right = max(0, min(max(int(x1), int(x2)), frame_width - 1))
    top = max(0, min(int(y1), int(y2), frame_height - 1))
    bottom = max(0, min(max(int(y1), int(y2)), frame_height - 1))
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom


def build_output(action_name, frame, rect, template_match, frame_source):
    left, top, right, bottom = rect
    output = {
        "bot_version": BOT_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "name": action_name,
        "frame_source": frame_source,
        "frame_size": {
            "width": int(frame.shape[1]),
            "height": int(frame.shape[0]),
        },
        "frame_rect": {
            "left": int(left),
            "top": int(top),
            "right": int(right),
            "bottom": int(bottom),
            "width": int(right - left + 1),
            "height": int(bottom - top + 1),
        },
        "template_match": template_match,
        "click_area": None,
    }

    if template_match is not None:
        center_x, center_y = template_match["center"]
        output["click_area"] = [
            int(left - center_x),
            int(right - center_x),
            int(top - center_y),
            int(bottom - center_y),
        ]
        output["button_action_click_area"] = (
            f"click_area=({output['click_area'][0]}, {output['click_area'][1]}, "
            f"{output['click_area'][2]}, {output['click_area'][3]})"
        )
    return output


def draw_overlay(frame, current_rect, template_match):
    canvas = frame.copy()
    if template_match is not None:
        x, y = template_match["top_left"]
        width, height = template_match["size"]
        cv2.rectangle(
            canvas,
            (x, y),
            (x + width - 1, y + height - 1),
            TEMPLATE_COLOR,
            1,
            cv2.LINE_AA,
        )
        cv2.circle(canvas, tuple(template_match["center"]), 4, TEMPLATE_COLOR, -1)
        cv2.putText(
            canvas,
            f"template score={template_match['score']:.3f}",
            (max(4, x), max(18, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            TEMPLATE_COLOR,
            1,
            cv2.LINE_AA,
        )

    if current_rect is not None:
        left, top, right, bottom = current_rect
        cv2.rectangle(
            canvas,
            (left, top),
            (right, bottom),
            BOX_COLOR,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            f"click bounds {right-left+1}x{bottom-top+1}",
            (left, max(18, top - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            BOX_COLOR,
            1,
            cv2.LINE_AA,
        )

    cv2.putText(
        canvas,
        "Drag click area | Enter=print JSON | Esc=cancel",
        (8, canvas.shape[0] - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        TEXT_COLOR,
        1,
        cv2.LINE_AA,
    )
    return canvas


def select_rect(frame, template_match):
    state = {
        "dragging": False,
        "start": None,
        "end": None,
        "rect": None,
    }

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["dragging"] = True
            state["start"] = (x, y)
            state["end"] = (x, y)
            state["rect"] = None
        elif event == cv2.EVENT_MOUSEMOVE and state["dragging"]:
            state["end"] = (x, y)
            state["rect"] = normalize_rect(
                state["start"],
                state["end"],
                frame.shape,
            )
        elif event == cv2.EVENT_LBUTTONUP and state["dragging"]:
            state["dragging"] = False
            state["end"] = (x, y)
            state["rect"] = normalize_rect(
                state["start"],
                state["end"],
                frame.shape,
            )

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)
    try:
        while True:
            cv2.imshow(WINDOW_NAME, draw_overlay(frame, state["rect"], template_match))
            key = cv2.waitKey(20) & 0xFF
            if key in (13, 10):
                if state["rect"] is None:
                    print("[BOUNDS] กรุณาลากกรอบก่อนกด Enter")
                    continue
                return state["rect"]
            if key == 27:
                return None
    finally:
        cv2.destroyWindow(WINDOW_NAME)


def main():
    args = build_parser().parse_args()
    source_frame, frame_source = load_frame(args)
    source_height, source_width = source_frame.shape[:2]
    frame = normalize_for_template_matching(
        source_frame,
        TEMPLATE_REFERENCE_FRAME_SIZE,
    )
    frame_source["source_frame_size"] = {
        "width": int(source_width),
        "height": int(source_height),
    }
    frame_source["detection_frame_size"] = {
        "width": int(frame.shape[1]),
        "height": int(frame.shape[0]),
    }
    if frame.shape != source_frame.shape:
        print(
            "[FRAME] normalize "
            f"{source_width}x{source_height} -> {frame.shape[1]}x{frame.shape[0]} "
            "เพื่อให้ตรงกับ coordinate space ของ bot"
        )
    template_match = find_template_match(frame, args.template, args.threshold)
    if template_match is not None:
        print(
            "[TEMPLATE] "
            f"{args.template} score={template_match['score']:.4f} "
            f"center={template_match['center']}"
        )
        if not template_match["passed_threshold"]:
            print("[TEMPLATE WARNING] score ต่ำกว่า threshold แต่ยังใช้เป็น anchor ได้")

    print("[BOUNDS] ลากกรอบพื้นที่ที่คลิกได้ แล้วกด Enter เพื่อ print JSON")
    selected_rect = select_rect(frame, template_match)
    if selected_rect is None:
        raise SystemExit("[BOUNDS] ยกเลิก")

    output = build_output(
        args.name,
        frame,
        selected_rect,
        template_match,
        frame_source,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
