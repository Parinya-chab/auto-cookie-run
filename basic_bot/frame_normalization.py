"""Keep template matching independent from the current LDPlayer window size."""

import cv2


def normalize_for_template_matching(frame, reference_size):
    """Resize one captured client frame to the template reference size."""
    if frame is None or frame.size == 0:
        return frame

    reference_width, reference_height = reference_size
    frame_height, frame_width = frame.shape[:2]
    if (frame_width, frame_height) == (reference_width, reference_height):
        return frame

    interpolation = (
        cv2.INTER_AREA
        if frame_width >= reference_width and frame_height >= reference_height
        else cv2.INTER_LINEAR
    )
    return cv2.resize(
        frame,
        (int(reference_width), int(reference_height)),
        interpolation=interpolation,
    )


def detection_to_source_scale(source_size, detection_size):
    """Return x/y factors that map template-frame pixels back to live pixels."""
    source_width, source_height = source_size
    detection_width, detection_height = detection_size
    if detection_width <= 0 or detection_height <= 0:
        raise ValueError("detection frame size must be positive")
    return source_width / detection_width, source_height / detection_height


def map_detection_point_to_source(point, source_size, detection_size):
    """Map one template-match point into the unscaled captured client frame."""
    scale_x, scale_y = detection_to_source_scale(source_size, detection_size)
    return (
        int(round(point[0] * scale_x)),
        int(round(point[1] * scale_y)),
    )
