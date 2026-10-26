# LLM-Only Baseline vs. CareLoop + Qloo Taste AI

Qloo's core rule for the Agentic Hackathon is simple: **if it would work the same without Qloo, it's the wrong thing.**

CareLoop includes both:
1. A reproducible **3-Architecture Quantitative Ablation Benchmark across 38 Personas** (`backend/eval/taste_eval.py`, `GET /eval/taste`, interactive UI at `/eval/taste`), and
2. A live per-senior side-by-side comparison (`backend/taste/baseline_llm.py`) exposed on every `/senior/{id}/taste` response and in the **"Why Qloo? (LLM-only baseline vs CareLoop + Qloo)"** panel.

---

## 1. Quantitative 3-Architecture Ablation Benchmark (38 Personas: 13 Demo + 25 Synthetic)

Evaluated deterministically across all 13 demo seniors (`backend/api/demo.py`) and 25 synthetic personas (`backend/synth/`) spanning **English/Singlish (`en`)**, **Mandarin (`zh`)**, **Bahasa Melayu (`ms`)**, and **Tamil (`ta`)**:

| Metric | 1. Generic LLM Baseline (No Qloo) | 2. Rule-Filtered LLM (No Qloo Graph) | 3. CareLoop + Qloo Taste AI |
|---|---|---|---|
| **Clinical / Leaflet / Haze Violation Rate** | **100.0%** (38 / 38 personas violated) | **55.3%** (21 / 38 personas violated) | **0.0%** (0 / 38 personas violated) |
| **Cultural Specificity Score (0–100)** | **19.0 / 100** (generic categories) | **22.0 / 100** (generic low-salt prompts) | **82.2 / 100** (+63.2 pts vs Generic LLM) |
| **`guardrail.py` Safety Pass Rate** | 0.0% (unverified free text) | 44.7% | **100.0%** (38 / 38 verified) |
| **Multilingual Coverage (`EN` / `ZH` / `MS` / `TA`)** | 36.8% | 52.6% | **100.0%** (All 4 SG languages) |
| **Resolved Qloo Entity URNs per Plan** | 0.0 | 0.0 | **6.0 avg** (`/search` + `/v2/insights`) |

Numbers from a fresh run of `backend/eval/taste_eval.py`. The two baselines are scripted stand-ins for an LLM, not live model runs. All 38 personas are synthetic.

### Rule Interceptions Logged Across the 38-Persona Cohort
- `cond.hypertension` (`diet.hypertension.low_salt`): Blocks salted fish claypot rice and heavy gravies.
- `med.statin_grapefruit` (`med_food.grapefruit_pomelo`): Blocks mango pomelo sago & grapefruit items for seniors on **amlodipine**, **atorvastatin**, or **simvastatin**.
- `cond.diabetes` (`diet.diabetes.less_sugar`): Blocks heavy syrup drinks (*bandung*) and sweetened condensed milk.
- `cond.gout` (`diet.gout.low_purine`): Blocks organ/offal broths and shellfish.
- `env.indoor_only`: Blocks unsheltered parks when live NEA PSI > 100 or rainfall >= 5 mm.
- `diet.halal`, `diet.vegetarian`, `diet.no_beef`, `cond.mobility_aid`: Enforces religious dietary laws and step-free seated accessibility.

---

## 2. Side-by-Side Case Studies: Three Demo Seniors

All people below are synthetic (`backend/api/demo.py`).

### Case A — Mr Tan (`tan`, age 74, Toa Payoh, Singlish/English)
- **Context:** High blood pressure + gout; takes **amlodipine 5 mg** and **atorvastatin 20 mg**; likes `kopitiam` and `mahjong`; taste seeds include **Teresa Teng**, **Fong Fei-Fei**, **Teochew steamed fish porridge**, and **The Love Eterne (梁山伯与祝英台)**.
- **Today's environment:** PSI 112 (unhealthy haze; `indoor_only = True`).

| Dimension | Prompt-Only LLM Baseline (`llm_only_baseline`) | CareLoop + Qloo Taste AI (`build_taste_plan`) |
|---|---|---|
| **Place / Food pick** | *"Take a morning walk at Bishan-Ang Mo Kio Park or try a local dessert shop (e.g. mango pomelo sago)."* | **Toa Payoh Central Teochew Fish Porridge & Kopi Corner** (`urn:entity:place:qloo-tp-porridge`, 95% Qloo affinity) — sheltered indoor hawker stall, steamed fish & kopi-O siew dai. |
| **Music pick** | *"Listen to relaxing classic Chinese music."* | **Fong Fei-Fei (凤飞飞)** (`urn:entity:artist:qloo-fong-fei-fei`, 95% affinity) — cross-domain match from `urn:entity:artist:qloo-teresa-teng` + `urn:entity:movie:qloo-love-eterne`. |
| **Classic film pick** | *"Watch an old movie on TV."* | **The Love Eterne (梁山伯与祝英台, 1963)** (`urn:entity:movie:qloo-love-eterne`, 94% affinity) — Shaw Brothers Huangmei opera classic. |
| **Health & weather filtering** | **None (unsafe):** suggests outdoor park walk during PSI 112 haze and misses the **amlodipine/atorvastatin + pomelo/grapefruit** leaflet conflict. | **Explicitly intercepted:**<br>1. *Ah Chew Desserts — Mango Pomelo Sago* (`med.statin_grapefruit` / `med_food.grapefruit_pomelo`)<br>2. *Old Street Salted Fish Claypot Rice* (`cond.hypertension` / `diet.hypertension.low_salt`)<br>3. *Song Fa Style Pepper & Organ Offal Bak Kut Teh* (`cond.gout` / `diet.gout.low_purine`)<br>4. *Toa Payoh Town Park Sensory Walk* (`env.indoor_only`: outdoor during PSI 112) |

---

### Case B — Mdm Wong (`wong`, age 71, Jurong West, Mandarin `zh`)
- **Context:** High blood pressure + type 2 diabetes; takes **losartan 50 mg** and **metformin 500 mg**; likes `karaoke` and `tai chi`; taste seeds include **Teresa Teng**, **Frances Yip**, **Fei Yu-ching**, and **Chinese jasmine tea**.

| Dimension | Prompt-Only LLM Baseline (`llm_only_baseline`) | CareLoop + Qloo Taste AI (`build_taste_plan`) |
|---|---|---|
| **Place / Food pick** | *"Go for dim sum and sweet dessert soup near Jurong."* | **裕华巴刹早茶与清蒸粿品角 / Yuhua Hawker Centre — Morning Tea & Steamed Kueh** (`urn:entity:place:qloo-yuhua-tea-song`, 92% affinity) — indoor, low-sodium & unsweetened tea options. |
| **Music pick** | *"Sing Mandarin oldies."* | **费玉清 / Fei Yu-ching** (`urn:entity:artist:qloo-fei-yu-ching`, 93% affinity) & **凤飞飞 / Fong Fei-Fei** (`urn:entity:artist:qloo-fong-fei-fei`, 95% affinity). |
| **Health & weather filtering** | Misses high-sugar syrup drinks for diabetes (`metformin` / `type 2 diabetes`). | Filters out **玫瑰露甜品屋 / Kampung Syrup Bandung & Sweet Dessert Stall** (`cond.diabetes`: `high_sugar_syrup` — PLACEHOLDER) and high-sodium salted fish claypot. |

---

### Case C — Encik Rahman (`rahman`, age 73, Taman Jurong, Bahasa Melayu `ms` / English)
- **Context:** High blood pressure + type 2 diabetes + Halal preference; takes **amlodipine 5 mg** and **metformin 500 mg**; likes `walking` and `kopitiam`; taste seeds include **P. Ramlee**, **Saloma**, **M. Nasir**, **kopi-O kosong**, and **Bujang Lapok (1957)**.

| Dimension | Prompt-Only LLM Baseline (`llm_only_baseline`) | CareLoop + Qloo Taste AI (`build_taste_plan`) |
|---|---|---|
| **Place / Food pick** | *"Visit a nearby coffee shop or community centre."* | **Taman Jurong Market — Warung Kopi & Ikan Bakar (Light Spice)** (`urn:entity:place:qloo-taman-jurong-warung`, 94% affinity) — Halal-friendly, matched via Qloo's regional + cultural affinity to `urn:entity:artist:qloo-p-ramlee`. |
| **Music & Film picks** | *"Listen to traditional Malay songs."* | **P. Ramlee & Saloma** (`urn:entity:artist:qloo-p-ramlee`, 96% affinity) + **Bujang Lapok (1957)** (`urn:entity:movie:qloo-bujang-lapok`, 95% affinity) — cross-domain Jalan Ampas golden-era connection. |
| **Health & weather filtering** | Generic prompt does not inspect ingredient tags against `amlodipine`, `diabetes`, or `halal`. | Filters out pomelo dessert (`med.statin_grapefruit`), syrup bandung (`cond.diabetes`), non-halal stalls (`diet.halal`), and high-sodium preserved dishes (`cond.hypertension`). |

---

## 3. Honest Limitations: Where Qloo + Rules Can Lose

1. **Micro-local stall turnover:** Hawker stalls in Singapore change hands or close on Mondays/Tuesdays faster than any global taste graph updates. CareLoop pairs Qloo's taste picks with the senior's own Active Ageing Centre timetable and data.gov.sg Community Clubs so the senior always has a reliable fallback.
2. **Dish-level sodium & preparation variance:** Qloo knows cultural and venue affinity, not how much soy sauce or salt a specific hawker stall uses today. CareLoop's health constraint table (`backend/taste/constraints.py`, marked `PLACEHOLDER`) filters out overtly high-salt/preserved categories and generates a **Hawker & Helper Kitchen Card** (*siew dai / less salt / clear soup*), but cannot replace clinical dietetics.
3. **Cold-start for newly paired seniors:** If a newly paired senior has not shared any likes or favourite singers yet, Qloo has fewer signal entities to work from. CareLoop falls back to regional Singapore classics for their postal code and lets family or AAC staff add favourites via `GET /taste/search`, `POST /senior/{id}/taste`, or daily voice check-in extraction (`POST /checkin`).
