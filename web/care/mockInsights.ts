// Offline mocks for /insights, /activities, /senior/{id}/taste, and /senior/{id}/taste/dietary:
// real API output from the demo (seed, then +11 days), recorded into fixtures/insights-demo.json.
import type { Activities, Insights, TastePlan } from '../shared/contract';
import fixtures from './fixtures/insights-demo.json';
import { delay } from './mock';

const SOURCE: Record<string, string> = {
  tan: 'tan',
  wong: 'lee',
  teo: 'goh',
  kaur: 'goh',
  rahman: 'tan',
  chua: 'lee',
  lee: 'lee',
  goh: 'goh',
  ng: 'ng',
  lim: 'goh',
  chandran: 'tan',
  yeo: 'lee',
  osman: 'ng',
  ong: 'tan',
  aminah: 'ng',
};

const SENIOR_NAMES: Record<string, string> = {
  tan: 'Mr Tan',
  wong: 'Mdm Wong',
  teo: 'Mrs Teo',
  kaur: 'Mdm Kaur',
  rahman: 'Encik Rahman',
  chua: 'Mdm Chua',
  lee: 'Mdm Lee',
  goh: 'Mr Goh',
  ng: 'Mr Ng',
  lim: 'Mr Lim',
  chandran: 'Mr Chandran',
  yeo: 'Mdm Yeo',
  osman: 'Mr Osman',
  ong: 'Mr Ong',
  aminah: 'Mdm Aminah',
};

const DEFAULT_CONDITIONS: Record<string, string[]> = {
  tan: ['hypertension', 'amlodipine'],
  wong: ['hypertension', 'amlodipine'],
  teo: ['hypertension', 'amlodipine'],
  kaur: ['hypertension', 'atorvastatin', 'vegetarian'],
  rahman: ['hypertension', 'diabetes', 'halal', 'amlodipine'],
  chua: ['hypertension', 'gout'],
  lee: ['hypertension', 'wheelchair'],
  goh: ['hypertension', 'gout'],
  ng: ['hypertension'],
  lim: ['hypertension'],
  chandran: ['hypertension', 'amlodipine'],
  yeo: ['hypertension'],
  osman: ['hypertension', 'halal'],
  ong: ['hypertension', 'amlodipine'],
  aminah: ['hypertension', 'diabetes', 'halal'],
};

const customConditions = new Map<string, string[]>();

function getConditionsFor(seniorId: string): string[] {
  if (!customConditions.has(seniorId)) {
    customConditions.set(seniorId, [...(DEFAULT_CONDITIONS[seniorId] ?? ['hypertension', 'amlodipine'])]);
  }
  return customConditions.get(seniorId)!;
}

const data = fixtures as unknown as { insights: Record<string, Insights>; activities: Record<string, Activities> };

const MOCK_TASTE_PLAN: TastePlan = {
  senior_id: 'tan',
  date: '2026-10-21',
  qloo_mode: 'fixture',
  profile: {
    neighbourhood: 'Ang Mo Kio / Kebun Baru',
    likes: ['tai chi', 'kopitiam'],
    music_seeds: ['Teresa Teng', 'Fei Yu-ching'],
    food_seeds: ['Clear fish soup', 'Teochew porridge'],
    film_seeds: ['1960s Cathay Mandarin classics'],
    outings: ['Kebun Baru kopitiam', 'Ang Mo Kio library'],
    summary: 'Enjoys morning kopitiam chats, classic Mandarin songs, and light low-salt Teochew dishes.',
    conditions: ['hypertension', 'amlodipine'],
  },
  constraints: {
    indoor_only: true,
    rain_mm: null,
    psi: 112,
    badges: ['Low-sodium options', 'No grapefruit/pomelo (amlodipine)', 'Indoor-only (PSI 112)'],
    active_rules: [
      { rule_id: 'cond_hypertension', kind: 'condition', trigger: 'High blood pressure', badge: 'Low-sodium options', explanation: 'Prefer low-sodium food options; avoid salted fish and heavy preserved dishes (PLACEHOLDER)' },
      { rule_id: 'med_amlodipine', kind: 'medicine', trigger: 'amlodipine', badge: 'No grapefruit/pomelo (amlodipine)', explanation: 'Medicine leaflet check (amlodipine): avoid grapefruit and pomelo (PLACEHOLDER)' },
      { rule_id: 'weather_indoor_only', kind: 'weather', trigger: 'PSI 112', badge: 'Indoor-only (PSI 112)', explanation: 'PSI is 112 (>100): indoor-only places and activities' },
    ],
  },
  recommendations: {
    places: [
      {
        entity_id: 'qloo-kebun-baru-kopitiam',
        name: 'Kebun Baru Kopitiam & Community Corner',
        category: 'food_and_social',
        indoor: true,
        free: false,
        affinity: 0.94,
        matched_seeds: ['Teresa Teng', 'Clear fish soup'],
        fit_badges: ['Indoor', 'Low-sodium available'],
        why: 'Because Mr Tan enjoys Teresa Teng and Clear fish soup, Qloo matched this sheltered place in their area (low-salt options available).',
        bridge: {
          seed: 'Teresa Teng',
          shared_tags: ['mandopop', '1970s_nostalgia', 'kopitiam'],
          target_domain: 'food_and_social',
          safety_check: 'Indoor · Low-sodium available',
          path_label: 'Teresa Teng → mandopop, 1970s_nostalgia → food_and_social → Indoor · Low-sodium available',
        },
      },
    ],
    music: [
      {
        entity_id: 'qloo-artist-fei-yu-ching',
        name: 'Fei Yu-ching (费玉清)',
        affinity: 0.96,
        matched_seeds: ['Teresa Teng'],
        why: 'Because Mr Tan enjoys Teresa Teng, Qloo matched this artist for their day.',
        bridge: {
          seed: 'Teresa Teng',
          shared_tags: ['mandopop', 'ballad', '1970s'],
          target_domain: 'music_artist',
          safety_check: 'Guardrail & health check passed',
          path_label: 'Teresa Teng → mandopop, ballad → music_artist → Guardrail & health check passed',
        },
      },
    ],
    movies: [
      {
        entity_id: 'qloo-movie-cathay-1960s',
        name: 'Mambo Girl (曼波女郎) — Cathay Classics',
        affinity: 0.91,
        matched_seeds: ['Teresa Teng', '1960s Cathay Mandarin classics'],
        why: 'Because Mr Tan enjoys Teresa Teng and 1960s Cathay Mandarin classics, Qloo matched this classic film.',
        bridge: {
          seed: 'Teresa Teng',
          shared_tags: ['mandopop', 'cathay_classics', 'nostalgia_sg'],
          target_domain: 'classic_film',
          safety_check: 'Guardrail & health check passed',
          path_label: 'Teresa Teng → mandopop, cathay_classics → classic_film → Guardrail & health check passed',
        },
      },
    ],
  },
  low_day_nudge: {
    place: 'Kebun Baru Kopitiam & Community Corner',
    music: 'Fei Yu-ching (费玉清)',
    text: 'If today feels a bit quiet, you could put on Fei Yu-ching (费玉清) or drop by Kebun Baru Kopitiam & Community Corner.',
    guardrail_passed: true,
  },
  visit_kit: {
    treat: 'Kebun Baru Kopitiam & Community Corner (Indoor, Low-sodium available)',
    music: 'Fei Yu-ching (费玉清)',
    film: 'Mambo Girl (曼波女郎) — Cathay Classics',
    safety_note: 'Low-sodium options, No grapefruit/pomelo (amlodipine), Indoor-only (PSI 112)',
    summary: 'Visiting Mr Tan today: bring a light treat from Kebun Baru Kopitiam & Community Corner, put on Fei Yu-ching (费玉清), and chat about Mambo Girl (曼波女郎) — Cathay Classics.',
    whatsapp_text:
      'Visiting Mr Tan — CareLoop + Qloo Visit Kit:\n• Takeaway / Outing: Kebun Baru Kopitiam & Community Corner (Indoor, Low-sodium available)\n• Put on music: Fei Yu-ching (费玉清)\n• Nostalgia film / topic: Mambo Girl (曼波女郎) — Cathay Classics\n• Health & medicine checks applied: Low-sodium options, No grapefruit/pomelo (amlodipine), Indoor-only (PSI 112)',
  },
  filtered_out: [
    {
      entity_id: 'qloo-pomelo-dessert',
      name: 'Ah Chew Desserts — Mango Pomelo Sago',
      rule_id: 'med_amlodipine',
      reason: 'Medicine leaflet check (amlodipine): avoid grapefruit and pomelo (PLACEHOLDER)',
    },
    {
      entity_id: 'qloo-salted-fish-claypot',
      name: 'Old Street Salted Fish Claypot Rice',
      rule_id: 'cond_hypertension',
      reason: 'Health check (High blood pressure): Prefer low-sodium food options; avoid salted fish and heavy preserved dishes (PLACEHOLDER)',
    },
    {
      entity_id: 'qloo-bishan-amk-park',
      name: 'Bishan-Ang Mo Kio Park Morning Stroll',
      rule_id: 'weather_indoor_only',
      reason: 'Weather/haze check (PSI 112): outdoor place filtered out; indoor-only active',
    },
  ],
  trace: [
    {
      step: 1,
      tool: 'qloo_search',
      title: 'Resolve taste seeds (Qloo /search)',
      input_summary: 'Teresa Teng, Fei Yu-ching, Clear fish soup, Teochew porridge',
      output_summary: 'Resolved 6 Qloo entity IDs in Singapore (mode: fixture)',
      details: ['Teresa Teng -> urn:entity:artist:teresa-teng', 'Clear fish soup -> urn:entity:place:teochew-fish-soup'],
    },
    {
      step: 2,
      tool: 'qloo_insights',
      title: 'Cross-domain taste discovery (Qloo /v2/insights)',
      input_summary: 'domains=[place, artist, movie], region=central, seeds=6',
      output_summary: 'Retrieved 6 place/food candidates, 2 music artists, and 2 classic films',
      details: ['Kebun Baru Kopitiam & Community Corner', 'Ah Chew Desserts — Mango Pomelo Sago', 'Old Street Salted Fish Claypot Rice'],
    },
    {
      step: 3,
      tool: 'check_health_constraints',
      title: 'Apply health, medicine-leaflet & weather constraints',
      input_summary: 'cond_hypertension, med_amlodipine, weather_indoor_only',
      output_summary: 'Kept 3 safe place picks; filtered out 3 conflicting candidates',
      details: [
        'Ah Chew Desserts — Mango Pomelo Sago: Medicine leaflet check (amlodipine): avoid grapefruit and pomelo (PLACEHOLDER)',
        'Old Street Salted Fish Claypot Rice: Health check (High blood pressure): Prefer low-sodium food options (PLACEHOLDER)',
      ],
    },
    {
      step: 4,
      tool: 'guardrail_check',
      title: 'Language safety guardrail check',
      input_summary: '5 explanation strings',
      output_summary: 'All 5 explanation strings passed guardrail.py (no diagnosis, no dose advice)',
      details: [],
    },
  ],
  guardrail: { passed: true, checked_count: 5, reasons: [] },
  comparison: {
    llm_only: {
      mode: 'llm_only_baseline',
      prompt_summary: 'Prompt-only LLM baseline without Qloo entity resolution, cross-domain taste graph, or explicit health/medicine filter step.',
      generic_picks: [
        'Walk at East Coast Park or Bishan Park',
        'Local hawker food or mango pomelo dessert',
        'Relaxing instrumental music',
      ],
      limitations: [
        'Unsafe on hazy/rainy days (PSI 112); ignores indoor-only requirement.',
        'Misses amlodipine leaflet check (pomelo/grapefruit) and low-sodium need for hypertension.',
        'Loses cultural specificity (Teresa Teng -> Fei Yu-ching / 1960s Cathay classics).',
      ],
    },
    careloop_with_qloo: {
      mode: 'careloop_qloo_fixture',
      picks: [
        'Kebun Baru Kopitiam & Community Corner (Indoor, Low-sodium available)',
        'Music: Fei Yu-ching (费玉清)',
        'Film: Mambo Girl (曼波女郎) — Cathay Classics',
      ],
      filtered_count: 3,
      filtered_examples: ['Ah Chew Desserts — Mango Pomelo Sago (med_amlodipine)', 'Old Street Salted Fish Claypot Rice (cond_hypertension)'],
    },
  },
};

function buildMockTastePlan(seniorId: string, opts?: { psi?: number; rain_mm?: number }): TastePlan {
  const conds = getConditionsFor(seniorId);
  const name = SENIOR_NAMES[seniorId] ?? 'Mr Tan';
  const psi = opts?.psi ?? 112;
  const indoorOnly = psi > 100 || (opts?.rain_mm ?? 0) >= 5;
  const filtered = [...MOCK_TASTE_PLAN.filtered_out];
  const badges = ['Low-sodium options', 'No grapefruit/pomelo (amlodipine)'];
  if (conds.includes('gout')) {
    badges.push('Low-purine (gout-safe)');
    filtered.push({
      entity_id: 'qloo-bak-kut-teh',
      name: 'Song Fa Style Bak Kut Teh & Organ Broth Stall',
      rule_id: 'cond.gout',
      reason: 'Clinical check (Gout): high-purine organ broth filtered out (PLACEHOLDER)',
    });
  }
  if (conds.includes('diabetes')) {
    badges.push('Siew dai / kosong');
  }
  if (conds.includes('halal')) {
    badges.push('Halal-certified');
  }
  if (indoorOnly) {
    badges.push(`Indoor-only (PSI ${psi})`);
  }
  return {
    ...MOCK_TASTE_PLAN,
    senior_id: seniorId,
    profile: {
      ...MOCK_TASTE_PLAN.profile,
      conditions: [...conds],
    },
    constraints: {
      ...MOCK_TASTE_PLAN.constraints,
      indoor_only: indoorOnly,
      psi,
      rain_mm: opts?.rain_mm ?? null,
      badges,
    },
    visit_kit: MOCK_TASTE_PLAN.visit_kit
      ? {
          ...MOCK_TASTE_PLAN.visit_kit,
          summary: MOCK_TASTE_PLAN.visit_kit.summary.replace('Mr Tan', name),
          whatsapp_text: MOCK_TASTE_PLAN.visit_kit.whatsapp_text.replace('Mr Tan', name),
        }
      : undefined,
    filtered_out: filtered,
  };
}

export function getSeniorTasteMock(seniorId: string, opts?: { psi?: number; rain_mm?: number; lang?: string }): Promise<TastePlan> {
  return delay(buildMockTastePlan(seniorId, opts));
}

export function toggleSeniorDietaryMock(
  seniorId: string,
  condition: string,
  opts?: { psi?: number; rain_mm?: number; lang?: string },
): Promise<TastePlan> {
  const conds = getConditionsFor(seniorId);
  const key = condition.toLowerCase();
  const idx = conds.indexOf(key);
  if (idx >= 0) conds.splice(idx, 1);
  else conds.push(key);
  return delay(buildMockTastePlan(seniorId, opts));
}

export function getInsights(seniorId: string, days = 30): Promise<Insights> {
  const base = data.insights[SOURCE[seniorId] ?? 'lee'];
  if (days >= 30 || !base) return delay(base);
  const bpSeries = base.bp.series.slice(-days);
  const cal = base.adherence.calendar.slice(-days);
  const taken = cal.filter((c) => c.pills === 'taken').length;
  const missed = cal.filter((c) => c.pills === 'missed').length;
  return delay({
    ...base,
    period: {
      days,
      from: bpSeries[0]?.date ?? base.period.from,
      to: base.period.to,
    },
    bp: {
      ...base.bp,
      series: bpSeries,
      readings_days: bpSeries.filter((p) => p.systolic != null).length,
    },
    adherence: {
      ...base.adherence,
      calendar: cal,
      taken_days: taken,
      missed_days: missed,
      reported_days: taken + missed,
    },
    activity: base.activity
      ? {
          ...base.activity,
          steps: base.activity.steps.slice(-days),
        }
      : null,
  });
}

export function getActivities(seniorId: string): Promise<Activities> {
  const base = data.activities[SOURCE[seniorId] ?? 'lee'];
  return delay({ ...base, taste_plan: buildMockTastePlan(seniorId) });
}
