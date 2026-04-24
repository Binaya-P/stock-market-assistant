from datetime import datetime, time


def is_trading_hours(now: datetime) -> bool:
    return time(10, 0) <= now.time() <= time(15, 0)


def is_buffer_window(now: datetime) -> bool:
    return time(15, 0) <= now.time() <= time(16, 0)


def is_collection_window(nepse) -> bool:
    now = datetime.now()

    try:
        market_status = nepse.isNepseOpen()
        is_open = market_status.get("isOpen", False)
    except Exception:
        is_open = False  # fail-safe

    if is_trading_hours(now):
        return True

    if is_buffer_window(now):
        return True

    if is_open:
        return True

    return False