# LLM-Only Baseline vs. Fondly + Qloo Taste AI

Qloo's core rule for the Agentic Hackathon is simple: **if it would work the same without Qloo, it's the wrong thing.**

Fondly includes a reproducible offline baseline (`backend/taste/baseline_llm.py`) and exposes the side-by-side comparison on every senior's `/senior/{id}/taste` and `/senior/{id}/activities` response (and in the **"Why Qloo? (LLM-only baseline vs Fondly + Qloo)"** panel in the Caregiver app).

---

## 1. Side-by-Side Comparison: Three Demo Seniors

All people below are synthetic (`backend/api/demo.py`).

### Case A — Mr Tan (`tan`, age 74, Toa Payoh, Singlish/English)
- **Context:** High blood pressure; takes **amlodipine 5 mg** every morning; likes `kopitiam` and `mahjong`; taste seeds include **Teresa Teng**, **Fong Fei-Fei**, **Teochew steamed fish porridge**, and **The Love Eterne (梁山伯与祝英台)**.
- **Today's environment:** PSI 112 (unhealthy haze; `indoor_only = True`).

| Dimension | Prompt-Only LLM Baseline (`llm_only_baseline`) | Fondly + Qloo Taste AI (`build_taste_plan`) |
|---|---|---|
| **Place / Food pick** | *"Take a morning walk at Bishan-Ang Mo Kio Park or try a local dessert shop (e.g. mango pomelo sago)."* | **Toa Payoh Central Teochew Fish Porridge & Kopi Corner** (`qloo-tp-teochew-porridge`, 95% Qloo affinity) — sheltered indoor hawker stall, steamed fish & kopi-O siew dai. |
| **Music pick** | *"Listen to relaxing classic Chinese music."* | **Fong Fei-Fei (凤飞飞)** (`qloo-artist-fong-fei-fei`, 95% affinity) — cross-domain match from `urn:entity:artist:teresa-teng` + `urn:entity:movie:love-eterne`. |
| **Classic film pick** | *"Watch an old movie on TV."* | **The Love Eterne (梁山伯与祝英台, 1963)** (`qloo-movie-love-eterne`, 94% affinity) — Shaw Brothers Huangmei opera classic. |
| **Health & weather filtering** | **None (unsafe):** suggests outdoor park walk during PSI 112 haze and misses the **amlodipine + pomelo/grapefruit** leaflet conflict. | **3 candidates explicitly filtered out:**<br>1. *Ah Chew Desserts — Mango Pomelo Sago* (`med_amlodipine`: contains pomelo/grapefruit — PLACEHOLDER)<br>2. *Old Street Salted Fish Claypot Rice* (`cond_hypertension`: high sodium preserved food — PLACEHOLDER)<br>3. *Toa Payoh Town Park Sensory Walk* (`weather_indoor_only`: outdoor during PSI 112) |

---

### Case B — Mdm Wong (`wong`, age 71, Jurong West, Mandarin `zh`)
- **Context:** High blood pressure + type 2 diabetes; takes **losartan 50 mg** and **metformin 500 mg**; likes `karaoke` and `tai chi`; taste seeds include **Teresa Teng**, **Frances Yip**, **Fei Yu-ching**, and **Chinese jasmine tea**.

| Dimension | Prompt-Only LLM Baseline (`llm_only_baseline`) | Fondly + Qloo Taste AI (`build_taste_plan`) |
|---|---|---|
| **Place / Food pick** | *"Go for dim sum and sweet dessert soup near Jurong."* | **裕华巴刹早茶与清蒸粿品角 / Yuhua Hawker Centre — Morning Tea & Steamed Kueh** (`qloo-jurong-yuhua-tea`, 92% affinity) — indoor, low-sodium & unsweetened tea options. |
| **Music pick** | *"Sing Mandarin oldies."* | **费玉清 / Fei Yu-ching** (`qloo-artist-fei-yu-ching`, 93% affinity) & **凤飞飞 / Fong Fei-Fei** (`qloo-artist-fong-fei-fei`, 95% affinity). |
| **Health & weather filtering** | Misses high-sugar syrup drinks for diabetes (`metformin` / `type 2 diabetes`). | Filters out **玫瑰露甜品屋 / Kampung Syrup Bandung & Sweet Dessert Stall** (`cond_diabetes`: `high_sugar_syrup` — PLACEHOLDER) and high-sodium salted fish claypot. |

---

### Case C — Pak Rahman (`rahman`, age 73, Taman Jurong, English/Malay roots)
- **Context:** High blood pressure; takes **amlodipine 5 mg**; likes `walking` and `kopitiam`; taste seeds include **P. Ramlee**, **Saloma**, **M. Nasir**, **kopi-O kosong**, and **Bujang Lapok (1957)**.

| Dimension | Prompt-Only LLM Baseline (`llm_only_baseline`) | Fondly + Qloo Taste AI (`build_taste_plan`) |
|---|---|---|
| **Place / Food pick** | *"Visit a nearby coffee shop or community centre."* | **Taman Jurong Market — Warung Kopi & Ikan Bakar (Light Spice)** (`qloo-taman-jurong-warung`, 94% affinity) — matched via Qloo's regional + cultural affinity to `urn:entity:artist:p-ramlee`. |
| **Music & Film picks** | *"Listen to traditional Malay songs."* | **P. Ramlee & Saloma** (`qloo-artist-p-ramlee`, 96% affinity) + **Tiga Abdul (1964)** (`qloo-movie-tiga-abdul`, 95% affinity) — cross-domain Jalan Ampas golden-era connection from *Bujang Lapok*. |
| **Health & weather filtering** | Generic prompt does not inspect ingredient tags against `amlodipine`. | Filters out pomelo dessert (`med_amlodipine`) and high-sodium preserved dishes (`cond_hypertension`). |

---

## 2. Offline Evaluation Across All 13 Synthetic Demo Seniors

Tested deterministically in `backend/taste/tests/test_agent.py` with zero network calls and zero API keys:

| Metric | Prompt-Only LLM Baseline | Fondly + Qloo Taste AI + Constraints |
|---|---|---|
| **Named local Singapore entities (places, singers, classic films)** | 0 / 13 seniors (generic categories only) | **13 / 13 seniors** (every senior gets named neighbourhood places, artists, and classic films) |
| **Cross-domain graph leap (`artist`/`movie` seed → `place`/`food` & vice versa)** | Noentity graph | **3 domains per senior** (`urn:entity:place`, `urn:entity:artist`, `urn:entity:movie`) |
| **Hypertension low-sodium constraint respected** | Unchecked | **100% enforced** (`cond_hypertension` blocks `high_sodium_preserved`) |
| **Medicine leaflet food conflict blocked (`amlodipine` + grapefruit/pomelo)** | Unchecked | **100% enforced** (`med_amlodipine` blocks `contains_grapefruit_pomelo`) |
| **Rain / Haze (`PSI > 100` or `rain >= 5 mm`) indoor-only respected** | Unchecked | **100% enforced** (`weather_indoor_only` removes outdoor parks/gardens) |
| **Senior's "Not for me" & `/knows` erasure respected** | Unchecked | **100% enforced** (`hidden_suggestions` and `DELETE /senior/{id}/knows/taste:...`) |
| **Passes `backend/language/guardrail.py`** | Not guaranteed without post-filter | **100% verified** (Step 4 of agent trace checks every explanation string) |

---

## 3. Honest Limitations: Where Qloo + Rules Can Lose

1. **Micro-local stall turnover:** Hawker stalls in Singapore change hands or close on Mondays/Tuesdays faster than any global taste graph updates. Fondly pairs Qloo's taste picks with the senior's own Active Ageing Centre timetable and data.gov.sg Community Clubs so the senior always has a reliable fallback.
2. **Dish-level sodium & preparation variance:** Qloo knows cultural and venue affinity, not how much soy sauce or salt a specific hawker stall uses today. Fondly's health constraint table (`backend/taste/constraints.py`, marked `PLACEHOLDER`) filters out overtly high-salt/preserved categories and adds a reminder badge (`Lower-salt options`), but cannot replace clinical dietetics or asking the stall for *siew dai / less salt*.
3. **Cold-start for newly paired seniors:** If a newly paired senior has not shared any likes or favourite singers yet, Qloo has fewer signal entities to work from. Fondly falls back to regional Singapore classics for their postal code and lets family or AAC staff add favourites via `GET /taste/search` and `POST /senior/{id}/taste`.
