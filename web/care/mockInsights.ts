// Offline mocks for /insights and /activities: real API output from the demo (seed, then +11 days),
// recorded into fixtures/insights-demo.json. Regenerate it the same way if the shapes change.
// The two mock-only AAC seniors borrow a demo senior's data: Mr Ong gets Mr Tan's rising BP, Mdm Aminah Mr Ng's quiet week.
import type { Activities, Insights, TastePlan } from '../shared/contract';
import fixtures from './fixtures/insights-demo.json';
import { delay } from './mock';

const SOURCE: Record<string, string> = { tan: 'tan', lee: 'lee', goh: 'goh', ng: 'ng', ong: 'tan', aminah: 'ng' };
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
      },
    ],
    music: [
      {
        entity_id: 'qloo-artist-fei-yu-ching',
        name: 'Fei Yu-ching (费玉清)',
        affinity: 0.96,
        matched_seeds: ['Teresa Teng'],
        why: 'Because Mr Tan enjoys Teresa Teng, Qloo matched this artist for their day.',
      },
    ],
    movies: [
      {
        entity_id: 'qloo-movie-cathay-1960s',
        name: 'Mambo Girl (曼波女郎) — Cathay Classics',
        affinity: 0.91,
        matched_seeds: ['Teresa Teng', '1960s Cathay Mandarin classics'],
        why: 'Because Mr Tan enjoys Teresa Teng and 1960s Cathay Mandarin classics, Qloo matched this classic film.',
      },
    ],
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
    fondly_with_qloo: {
      mode: 'fondly_qloo_fixture',
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

export function getInsights(seniorId: string): Promise<Insights> {
  return delay(data.insights[SOURCE[seniorId] ?? 'lee']);
}

export function getActivities(seniorId: string): Promise<Activities> {
  const base = data.activities[SOURCE[seniorId] ?? 'lee'];
  return delay({ ...base, taste_plan: base.taste_plan ?? MOCK_TASTE_PLAN });
}
