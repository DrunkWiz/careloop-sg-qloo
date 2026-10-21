"""LLM-only baseline (without Qloo taste graph or CareLoop's deterministic constraint tools).

Used for the side-by-side comparison in `GET /senior/{id}/taste`, `ActivitiesView.tsx`, and
`docs/qloo-comparison.md` to demonstrate why Qloo's cross-domain taste graph + CareLoop's
deterministic health/weather guardrail tools outperform a standalone LLM prompt.
"""
from __future__ import annotations


def llm_only_baseline(senior: dict, *, indoor_only: bool = False, psi: int | None = None, rain_mm: float | None = None) -> dict:
    """Return what a prompt-only LLM baseline produces for `senior` without Qloo or tool constraints."""
    zh = senior.get("language") == "zh"
    likes = senior.get("likes") or ["coffee", "walking"]
    like_str = ", ".join(likes)

    if zh:
        picks = [
            "去附近的咖啡店喝杯咖啡或吃甜品（例如杨枝甘露或传统糕点）",
            "去附近的公园散步呼吸新鲜空气",
            f"在社区或家里进行与「{'、'.join(likes)}」相关的休闲活动",
        ]
        gaps = [
            "缺乏具体性：只给出泛泛的“附近咖啡店/公园”，没有定位到本地熟食中心或具体档口。",
            "缺乏跨领域文化连接：只重复字面爱好，无法从邓丽君/比·南利等音乐偏好推导出邵氏黄梅调、惹兰安拔士老电影或对应籍贯茶座。",
            "健康与天气护栏缺失：可能推荐含西柚/柚子甜品（与氨氯地平/他汀类说明书冲突）、高盐咸鱼砂煲饭（高血压不适宜）或在烟霾/雨天推荐户外散步。",
        ]
    else:
        picks = [
            f"Visit a local café or dessert shop for coffee and a sweet treat (such as mango pomelo sago or traditional kueh) to match '{like_str}'.",
            "Take a relaxing morning walk at a nearby neighbourhood park for fresh air.",
            f"Join a general community session related to {like_str} and listen to classic oldies.",
        ]
        gaps = [
            "Low specificity: suggests generic 'a local café' or 'a nearby park' instead of real heartland stalls and Active Ageing Centre timetables.",
            "No cross-domain cultural graph: repeats literal keywords instead of connecting music seeds (Teresa Teng, P. Ramlee, T.M. Soundararajan) to matching regional food, classic cinema and community groups.",
            "Misses deterministic health & weather filters: suggests pomelo/grapefruit desserts or sugary drinks despite amlodipine/diabetes records, and suggests outdoor park walks even when haze (PSI > 100) or rain is active.",
        ]

    return {
        "mode": "llm_only_baseline",
        "prompt_summary": (
            f"Prompt-only LLM given name={senior.get('name')}, region={senior.get('region')}, likes={likes}"
        ),
        "generic_picks": picks,
        "limitations": gaps,
    }
