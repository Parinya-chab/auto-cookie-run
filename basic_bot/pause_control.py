import time


# Keep Stop/Pause responsive while waiting for click holds, delays, or locks.
PAUSE_POLL_INTERVAL = 0.05


def wait_while_paused(stop_event, pause_event=None, on_pause_interval=None):
    """Block while paused; return (stopped, paused_seconds)."""
    if pause_event is None or not pause_event.is_set():
        return False, 0.0

    paused_started = time.monotonic()
    print("[PAUSE] บอทพักชั่วคราว: หยุดสแกน หยุดคลิก และหยุด alert")
    while pause_event.is_set():
        if stop_event.wait(PAUSE_POLL_INTERVAL):
            paused_for = time.monotonic() - paused_started
            if on_pause_interval is not None:
                on_pause_interval(paused_for)
            return True, paused_for

    paused_for = time.monotonic() - paused_started
    if on_pause_interval is not None:
        on_pause_interval(paused_for)
    print(f"[RESUME] กลับมาทำงานต่อหลัง Pause {paused_for:.1f}s")
    return False, paused_for


def wait_with_pause_status(
    stop_event,
    pause_event,
    duration,
    on_pause_interval=None,
    interrupt_event=None,
):
    """Wait for duration while freezing the countdown during Pause."""
    end_time = time.monotonic() + max(0.0, float(duration))
    paused_during_wait = False

    while True:
        if interrupt_event is not None and interrupt_event.is_set():
            return False, paused_during_wait
        stopped, paused_for = wait_while_paused(
            stop_event,
            pause_event,
            on_pause_interval=on_pause_interval,
        )
        if paused_for > 0:
            paused_during_wait = True
            end_time += paused_for
        if stopped:
            return True, paused_during_wait
        if interrupt_event is not None and interrupt_event.is_set():
            return False, paused_during_wait

        remaining = end_time - time.monotonic()
        if remaining <= 0:
            return False, paused_during_wait
        if stop_event.wait(min(PAUSE_POLL_INTERVAL, remaining)):
            return True, paused_during_wait


def wait_with_pause(stop_event, pause_event, duration, on_pause_interval=None):
    stopped, _ = wait_with_pause_status(
        stop_event,
        pause_event,
        duration,
        on_pause_interval=on_pause_interval,
    )
    return stopped
