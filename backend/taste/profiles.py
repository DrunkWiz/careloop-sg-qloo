"""Rich Singapore senior taste profiles for Qloo cross-domain discovery.

Combines each senior's saved `likes` with cultural taste seeds across music, food, films and
neighbourhood outings so Qloo's taste graph (/search and /v2/insights) can connect across domains.
"""
from __future__ import annotations

# Rich cultural taste seeds for the 13 demo seniors in backend/api/demo.py.
# All people are synthetic. Any item erased by the senior in /knows is filtered out before querying Qloo.
SENIOR_TASTE_PROFILES: dict[str, dict] = {
    "tan": {
        "neighbourhood": "Toa Payoh Central",
        "music_seeds": ["Teresa Teng", "Fong Fei-Fei"],
        "food_seeds": ["Teochew steamed fish porridge", "kopi-O siew dai"],
        "film_seeds": ["The Love Eterne (梁山伯与祝英台)"],
        "outings": ["morning kopitiam kakis", "community mahjong table"],
        "summary_en": "Enjoys 1970s Hokkien & Mandarin classics (Teresa Teng, Fong Fei-Fei), Teochew steamed fish porridge, morning kopi-O siew dai, and mahjong with kakis in Toa Payoh.",
        "summary_zh": "喜爱70年代闽南与华语金曲（邓丽君、凤飞飞）、潮州清蒸鱼糜、早市咖啡乌少糖，以及在大巴窑与老友打麻将。",
    },
    "wong": {
        "neighbourhood": "Jurong West / Yuhua",
        "music_seeds": ["Teresa Teng", "Frances Yip", "Fei Yu-ching"],
        "food_seeds": ["Chinese jasmine tea", "steamed Teochew kueh"],
        "film_seeds": ["The Love Eterne (梁山伯与祝英台)"],
        "outings": ["AAC karaoke sing-along", "morning tea house"],
        "summary_en": "Loves singing 1970s–80s Mandopop & Cantopop (Teresa Teng, Frances Yip, Fei Yu-ching), jasmine tea and steamed kueh around Yuhua.",
        "summary_zh": "热爱演唱70至80年代华语与粤语经典（邓丽君、叶丽仪、费玉清），喜欢裕华巴刹的清香茉莉花茶与清蒸粿品。",
    },
    "teo": {
        "neighbourhood": "Woodlands / Marsiling",
        "music_seeds": ["Cliff Richard", "Teresa Teng"],
        "food_seeds": ["kopi-O kosong", "pandan chiffon"],
        "film_seeds": ["The Young Ones (1961)"],
        "outings": ["community herb & orchid garden", "quiet morning kopi"],
        "summary_en": "Enjoys orchid and herb gardening, 1960s Rediffusion oldies (Cliff Richard) and quiet morning kopi.",
        "summary_zh": "喜爱胡姬花与香草园艺、60年代怀旧老歌，以及清静的晨间咖啡时光。",
    },
    "lee": {
        "neighbourhood": "Tampines East",
        "music_seeds": ["Cliff Richard", "Teresa Teng"],
        "food_seeds": ["barley water (less sweet)", "steamed soon kueh"],
        "film_seeds": ["The Young Ones (1961)"],
        "outings": ["rattan & patchwork craft circle", "afternoon tea chat"],
        "summary_en": "Enjoys patchwork and handicraft circles, 1960s English & Mandarin melodies, and chatting with neighbours in Tampines.",
        "summary_zh": "喜欢拼布手工班、60年代怀旧旋律，以及在淡滨尼与街坊下午茶叙旧。",
    },
    "goh": {
        "neighbourhood": "Tampines / Bedok Reservoir",
        "music_seeds": ["Fong Fei-Fei", "Fei Yu-ching"],
        "food_seeds": ["sliced fish bee hoon (clear soup)", "Chinese oolong tea"],
        "film_seeds": ["The Love Eterne (梁山伯与祝英台)"],
        "outings": ["morning qigong & brisk walk", "park pavilion tea"],
        "summary_en": "Active morning walker who enjoys qigong, Hokkien & Mandarin classics (Fong Fei-Fei), and clear-soup fish bee hoon.",
        "summary_zh": "热爱晨运健走与气功，喜欢凤飞飞与费玉清金曲，以及清汤鱼片米粉与乌龙茶。",
    },
    "ng": {
        "neighbourhood": "Tampines / Simei",
        "music_seeds": ["Teresa Teng", "Fong Fei-Fei"],
        "food_seeds": ["kopi-O siew dai", "soft-boiled eggs & steamed bread"],
        "film_seeds": ["The Love Eterne (梁山伯与祝英台)"],
        "outings": ["void deck & kopitiam kakis corner", "short sheltered stroll"],
        "summary_en": "Prefers unhurried kopitiam chats over kopi-O siew dai and classic Hokkien radio tunes close to home.",
        "summary_zh": "喜欢在住家附近咖啡店喝少糖咖啡乌、听闽南老歌，与老街坊轻松闲聊。",
    },
    "kaur": {
        "neighbourhood": "Bedok / East Coast",
        "music_seeds": ["Gurdas Maan", "T.M. Soundararajan"],
        "food_seeds": ["fresh chapati & light dhal", "masala ginger tea (unsweetened)"],
        "film_seeds": ["Pasamalar (1961)"],
        "outings": ["community allotment gardening", "morning brisk walk with neighbours"],
        "summary_en": "Active walker and gardener who loves Punjabi folk melodies (Gurdas Maan), unsweetened ginger masala tea, and fresh chapati.",
        "summary_zh": "热爱晨间散步与社区园艺，喜欢旁遮普传统民谣、无糖姜茶与现烙印度麦饼。",
    },
    "rahman": {
        "neighbourhood": "Jurong West / Taman Jurong",
        "music_seeds": ["P. Ramlee", "Saloma", "M. Nasir"],
        "food_seeds": ["kopi-O kosong", "ikan bakar (lightly spiced grilled fish)"],
        "film_seeds": ["Bujang Lapok (1957)"],
        "outings": ["morning stretching & brisk walk", "Taman Jurong warung kopi chat"],
        "summary_en": "Enjoys Jalan Ampas golden-era Malay classics (P. Ramlee, Saloma), morning exercise, and kopi-O kosong with friends in Taman Jurong.",
        "summary_zh": "喜爱惹兰安拔士黄金年代马来经典（比·南利、莎萝玛）、晨间运动，以及在达曼裕廊喝无糖咖啡乌叙旧。",
    },
    "chua": {
        "neighbourhood": "Toa Payoh / Balestier",
        "music_seeds": ["Frances Yip", "Teresa Teng", "Fei Yu-ching"],
        "food_seeds": ["steamed dim sum (low salt)", "chrysanthemum tea (unsweetened)"],
        "film_seeds": ["The Love Eterne (梁山伯与祝英台)"],
        "outings": ["karaoke sing-along", "afternoon mahjong circle"],
        "summary_en": "Enjoys karaoke classics (Frances Yip, Teresa Teng), mahjong with friends, and unsweetened chrysanthemum tea in Toa Payoh.",
        "summary_zh": "喜爱卡拉OK经典金曲（叶丽仪、邓丽君）、与牌友打麻将，以及大巴窑的无糖菊花茶点。",
    },
    "lim": {
        "neighbourhood": "Tampines North",
        "music_seeds": ["Fong Fei-Fei", "Teresa Teng"],
        "food_seeds": ["kopi-O kosong", "Teochew fish porridge"],
        "film_seeds": ["The Love Eterne (梁山伯与祝英台)"],
        "outings": ["morning park connector walk", "kopitiam newspaper & kopi"],
        "summary_en": "Likes independent morning walks along Tampines park connectors, kopi-O kosong, and 1970s Hokkien classics.",
        "summary_zh": "喜欢独自在淡滨尼公园连道晨走、喝无糖咖啡乌，听70年代闽南老歌。",
    },
    "chandran": {
        "neighbourhood": "Tampines / Pasir Ris",
        "music_seeds": ["T.M. Soundararajan", "P. Susheela"],
        "food_seeds": ["plain thosai & sambar (light salt)", "sukku malli ginger coffee (less sugar)"],
        "film_seeds": ["Pasamalar (1961)"],
        "outings": ["AAC morning stretching & health circle", "Tampines Round Market thosai morning"],
        "summary_en": "Enjoys 1960s Tamil golden melodies (T.M. Soundararajan, P. Susheela), morning exercise, and fresh thosai at Tampines Round Market.",
        "summary_zh": "喜爱60年代泰米尔经典金曲、乐龄中心晨间健身操，以及淡滨尼圆巴刹的现烙薄饼。",
    },
    "yeo": {
        "neighbourhood": "Ang Mo Kio / Toa Payoh",
        "music_seeds": ["Fei Yu-ching", "Teresa Teng"],
        "food_seeds": ["warm soy milk (unsweetened)", "steamed vegetable bun"],
        "film_seeds": ["The Love Eterne (梁山伯与祝英台)"],
        "outings": ["community choir & singing", "handicraft & folding circle"],
        "summary_en": "Enjoys Mandarin choir singing (Fei Yu-ching, Teresa Teng), paper and fabric crafts, and unsweetened warm soy milk.",
        "summary_zh": "喜爱华语合唱班（费玉清、邓丽君）、手工折纸与布艺，以及无糖温豆浆。",
    },
    "osman": {
        "neighbourhood": "Ang Mo Kio / Bishan",
        "music_seeds": ["P. Ramlee", "M. Nasir"],
        "food_seeds": ["kopi-O siew dai", "roti bakar (light kaya)"],
        "film_seeds": ["Bujang Lapok (1957)"],
        "outings": ["void deck chess & tile table", "morning warung kopi"],
        "summary_en": "Enjoys P. Ramlee films and songs, tile games with neighbours, and morning kopi-O siew dai.",
        "summary_zh": "喜欢比·南利经典电影与老歌、与街坊下棋打牌，以及早上一杯少糖咖啡乌。",
    },
}


def build_taste_profile(senior: dict, erased_keys: set[str] | None = None) -> dict:
    """Return the combined taste profile for `senior`, merging saved `likes` with cultural taste seeds."""
    sid = senior.get("id", "")
    erased = erased_keys or set()
    base = SENIOR_TASTE_PROFILES.get(sid)
    likes = [str(x) for x in (senior.get("likes") or []) if f"like:{x}" not in erased]

    if base is None:
        zh = senior.get("language") == "zh"
        music = ["Teresa Teng", "Fei Yu-ching"] if zh else ["Cliff Richard", "Teresa Teng"]
        food = ["kopi-O siew dai", "steamed fish porridge"]
        films = ["The Love Eterne (梁山伯与祝英台)"] if zh else ["The Young Ones (1961)"]
        outings = list(likes) or ["morning neighbourhood stroll", "kopitiam chat"]
        summary_en = f"Taste profile built from {senior.get('name') or 'senior'}'s saved preferences ({', '.join(outings)}) and regional Singapore classics."
        summary_zh = f"根据{senior.get('name') or '长者'}保存的偏好（{'、'.join(outings)}）建立的新加坡本地品味档案。"
        neighbourhood = f"{(senior.get('region') or 'central').title()} Singapore"
    else:
        music = [m for m in base["music_seeds"] if m not in erased]
        food = [f for f in base["food_seeds"] if f not in erased]
        films = [f for f in base["film_seeds"] if f not in erased]
        outings = [o for o in base["outings"] if o not in erased]
        summary_en = base["summary_en"]
        summary_zh = base["summary_zh"]
        neighbourhood = base["neighbourhood"]

    # Combine all query seeds for Qloo /search and /v2/insights
    all_seeds: list[str] = []
    for item in [*likes, *music, *[o.split()[0] for o in outings]]:
        norm = item.strip().lower()
        if norm and norm not in all_seeds:
            all_seeds.append(norm)

    return {
        "senior_id": sid,
        "neighbourhood": neighbourhood,
        "likes": likes,
        "music_seeds": music,
        "food_seeds": food,
        "film_seeds": films,
        "outings": outings,
        "all_seeds": all_seeds,
        "summary_en": summary_en,
        "summary_zh": summary_zh,
    }


def taste_knows_entries(senior: dict, erased_keys: set[str] | None = None) -> list[dict]:
    """Plain-language entries for GET /senior/{id}/knows so the senior can inspect and erase any taste seed."""
    erased = erased_keys or set()
    profile = build_taste_profile(senior, erased_keys=erased)
    zh = senior.get("language") == "zh"
    items: list[dict] = []
    for m in profile["music_seeds"]:
        if m not in erased:
            items.append({
                "id": f"taste:{m}",
                "kind": "like",
                "text": f"喜欢听 {m} 的歌（Qloo 品味档案）" if zh else f"Enjoys music by {m} (Fondly taste profile)",
            })
    for f in profile["food_seeds"]:
        if f not in erased:
            items.append({
                "id": f"taste:{f}",
                "kind": "like",
                "text": f"偏好食物：{f}" if zh else f"Fond of {f}",
            })
    return items
