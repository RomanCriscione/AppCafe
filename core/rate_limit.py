from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
import time

def rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
    *,
    ajax=False,
    message="Demasiadas acciones. Probá más tarde."
):
    now = int(time.time())
    data = cache.get(key, {"count": 0, "reset": now + window_seconds})

    if now > data["reset"]:
        data = {"count": 0, "reset": now + window_seconds}

    data["count"] += 1
    cache.set(key, data, timeout=window_seconds)

    if data["count"] > limit:
        if ajax:
            return JsonResponse(
                {"ok": False, "error": "rate_limited", "message": message},
                status=429
            )
        messages.warning(None, message)
        return redirect("reviews:cafe_list")

    return None
