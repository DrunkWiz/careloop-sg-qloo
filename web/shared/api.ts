// Caregiver-app API client. Set VITE_API_URL to hit the real backend; without it, calls are served by
// in-browser mocks with the same shapes (web/care/mock.ts, web/care/mockAac.ts).
import type {
  Activities,
  BriefData,
  CaregiverView,
  CareNotes,
  Contact,
  Insights,
  Caseload,
  FamilyView,
  Handover,
  HealthSyncResult,
  HealthSyncView,
  MedicinesView,
  PreventionView,
  ProgrammeFeed,
  TimetableImport,
  LogDay,
  PairCodeIn,
  PairCodeOut,
  PairIn,
  PairOut,
  Programme,
  ProgrammeIn,
  RotaView,
  TastePlan,
  GroupTastePlan,
  KopiKakisResponse,
  MemoryCapsule,
  MemoryLaneResponse,
  RespitePlanResponse,
  TasteEvalBenchmark,
  VentPost,
} from './contract';
import * as mock from '../care/mock';
import * as mockAac from '../care/mockAac';
import * as mockInsights from '../care/mockInsights';

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '');

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* not JSON */
    }
    throw new ApiError(res.status, `${init?.method ?? 'GET'} ${path}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const usingMocks = !BASE;

export function getFamilyView(contactId: string): Promise<FamilyView> {
  return BASE ? http(`/care/family/${contactId}`) : mock.getFamilyView(contactId);
}

// GET /care/caregiver/{caregiver_id}: one caregiver's linked seniors (the switcher).
export function getCaregiverView(caregiverId: string): Promise<CaregiverView> {
  return BASE ? http(`/care/caregiver/${caregiverId}`) : mock.getCaregiverView(caregiverId);
}

// POST /care/contact/{contact_id}/primary: promote this contact to primary.
export function setPrimary(contactId: string): Promise<Contact> {
  return BASE ? http(`/care/contact/${contactId}/primary`, { method: 'POST' }) : mock.setPrimary(contactId);
}

// GET /senior/{sid}/rota
export function getRota(seniorId: string): Promise<RotaView> {
  return BASE ? http(`/senior/${seniorId}/rota`) : mock.getRota(seniorId);
}

// PUT /senior/{sid}/rota
export function putRota(seniorId: string, mode: 'weekly' | 'daily', startDate: string, order: string[]): Promise<RotaView> {
  return BASE
    ? http(`/senior/${seniorId}/rota`, { method: 'PUT', body: JSON.stringify({ mode, start_date: startDate, order }) })
    : mock.putRota(seniorId, mode, startDate, order);
}

// POST /senior/{sid}/rota/swap
export function swapRota(seniorId: string, date: string, contactId: string): Promise<RotaView> {
  return BASE
    ? http(`/senior/${seniorId}/rota/swap`, { method: 'POST', body: JSON.stringify({ date, contact_id: contactId }) })
    : mock.swapRota(seniorId, date, contactId);
}

// DELETE /senior/{sid}/rota
export function deleteRota(seniorId: string): Promise<RotaView> {
  return BASE ? http(`/senior/${seniorId}/rota`, { method: 'DELETE' }) : mock.deleteRota(seniorId);
}

export function getCaseload(workerId: string): Promise<Caseload> {
  return BASE ? http(`/care/aac/${workerId}/caseload`) : mockAac.getCaseload(workerId);
}

export function claimHandover(handoverId: string, contactId: string, choice: string): Promise<Handover> {
  return BASE
    ? http(`/handover/${handoverId}/claim`, { method: 'POST', body: JSON.stringify({ contact_id: contactId, choice }) })
    : mock.claimHandover(handoverId, contactId, choice);
}

const FAMILY_SENIORS = new Set(['tan', 'wong', 'teo', 'kaur', 'rahman', 'chua']);

export function getBrief(seniorId: string): Promise<BriefData> {
  if (BASE) return http(`/senior/${seniorId}/brief.json`);
  return FAMILY_SENIORS.has(seniorId) ? mock.getBrief(seniorId) : mockAac.getBrief(seniorId);
}

export function briefPdfUrl(seniorId: string): string | null {
  return BASE ? `${BASE}/senior/${seniorId}/brief.pdf` : null;
}

// Added endpoint (needs team OK). Pass the family contact so the senior's consent applies.
// Returns null when the API doesn't have it.
export async function getLog(seniorId: string, days = 14, contactId?: string): Promise<LogDay[] | null> {
  if (!BASE) return FAMILY_SENIORS.has(seniorId) ? mock.getLog(days, seniorId) : mockAac.getLog(seniorId, days);
  try {
    return await http(`/senior/${seniorId}/log?days=${days}${contactId ? `&contact=${encodeURIComponent(contactId)}` : ''}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}

// Added endpoints (need team OK). Pass the family contact so the senior's consent applies.
export function getInsights(seniorId: string, contactId?: string, days = 30): Promise<Insights> {
  return BASE
    ? http(`/senior/${seniorId}/insights?days=${days}${contactId ? `&contact=${encodeURIComponent(contactId)}` : ''}`)
    : mockInsights.getInsights(seniorId, days);
}

export function getActivities(seniorId: string, contactId?: string, opts?: { psi?: number; rain_mm?: number }): Promise<Activities> {
  if (!BASE) return mockInsights.getActivities(seniorId);
  const qs = [
    contactId && `contact=${encodeURIComponent(contactId)}`,
    opts?.psi !== undefined && `psi=${opts.psi}`,
    opts?.rain_mm !== undefined && `rain_mm=${opts.rain_mm}`,
  ].filter(Boolean).join('&');
  return http(`/senior/${seniorId}/activities${qs ? `?${qs}` : ''}`);
}

// Added endpoint (needs team OK). Every linked contact reads and writes the same notes.
export function getCareNotes(seniorId: string, contactId: string): Promise<CareNotes> {
  return BASE ? http(`/senior/${seniorId}/care-notes?contact=${encodeURIComponent(contactId)}`) : mock.getCareNotes(seniorId);
}

export function putCareNotes(seniorId: string, contactId: string, notes: CareNotes): Promise<CareNotes> {
  const { updated_by: _b, updated_at: _a, ...body } = notes;
  return BASE
    ? http(`/senior/${seniorId}/care-notes?contact=${encodeURIComponent(contactId)}`, { method: 'PUT', body: JSON.stringify(body) })
    : mock.putCareNotes(seniorId, notes);
}

export function getProgrammes(aacId: string): Promise<Programme[]> {
  return BASE ? http(`/aac/${aacId}/programmes`) : mockAac.getProgrammes(aacId);
}

export function putProgrammes(aacId: string, programmes: ProgrammeIn[]): Promise<Programme[]> {
  return BASE
    ? http(`/aac/${aacId}/programmes`, { method: 'PUT', body: JSON.stringify(programmes) })
    : mockAac.putProgrammes(aacId, programmes);
}

export function createPairCode(body: PairCodeIn): Promise<PairCodeOut> {
  return BASE ? http('/care/pair-code', { method: 'POST', body: JSON.stringify(body) }) : mock.createPairCode(body);
}

export function pair(body: PairIn): Promise<PairOut> {
  return BASE ? http('/pair', { method: 'POST', body: JSON.stringify(body) }) : mock.pair(body);
}

// Demo only: move the demo clock, or reseed.
export function demoAdvance(days: number): Promise<{ today: string }> {
  return BASE ? http('/demo/advance', { method: 'POST', body: JSON.stringify({ days }) }) : mock.demoAdvanceMock(days);
}

export function demoReset(): Promise<{ today: string }> {
  return BASE ? http('/demo/reset', { method: 'POST' }) : mock.demoResetMock();
}

// --- vent space: anonymous caregiver rant room (no caregiver_id or senior_id saved) ----------

export function getVentFeed(): Promise<VentPost[]> {
  return BASE ? http('/vent') : mock.getVentFeed();
}

export function postVent(nickname: string, text: string): Promise<VentPost> {
  return BASE ? http('/vent', { method: 'POST', body: JSON.stringify({ nickname, text }) }) : mock.postVent(nickname, text);
}

export function hugVentPost(postId: string): Promise<VentPost> {
  return BASE ? http(`/vent/${postId}/hug`, { method: 'POST' }) : mock.hugVentPost(postId);
}

export function reportVentPost(postId: string): Promise<{ id: string; hidden: boolean }> {
  return BASE ? http(`/vent/${postId}/report`, { method: 'POST' }) : mock.reportVentPost(postId);
}

// Added endpoints (need team OK): health apps on the senior's phone. Mocks show Mr Tan's phone, read-only.
export function getHealthSync(seniorId: string, contactId?: string, days = 7): Promise<HealthSyncView> {
  return BASE
    ? http(`/senior/${seniorId}/health-sync?days=${days}${contactId ? `&contact=${encodeURIComponent(contactId)}` : ''}`)
    : mock.getHealthSync(seniorId, days);
}

// Demo only: stands in for the senior's phone syncing now, with an optional cuff measurement.
export function demoHealthSync(seniorId: string, bp?: [number, number]): Promise<HealthSyncResult> {
  return BASE
    ? http(`/demo/health-sync/${seniorId}`, { method: 'POST', body: JSON.stringify(bp ? { bp } : {}) })
    : mock.demoHealthSyncMock(seniorId, bp);
}

// Added endpoints (need team OK): import a centre's own calendar (.ics) or spreadsheet (.csv).
export function importTimetable(aacId: string, body: { text?: string; url?: string; save?: boolean }): Promise<TimetableImport> {
  return BASE
    ? http(`/aac/${aacId}/programmes/import`, { method: 'POST', body: JSON.stringify(body) })
    : mockAac.importTimetableMock(aacId, body);
}

export async function getProgrammeFeed(aacId: string): Promise<ProgrammeFeed | null> {
  return BASE ? http(`/aac/${aacId}/programmes/feed`) : null;
}

export function stopProgrammeFeed(aacId: string): Promise<null> {
  return BASE ? http(`/aac/${aacId}/programmes/feed`, { method: 'DELETE' }) : Promise.resolve(null);
}

// Added endpoints (need team OK): what each medicine is for, and vaccines and check-ups that are due.
const q = (contactId?: string, lang?: string) =>
  [contactId && `contact=${encodeURIComponent(contactId)}`, lang && `lang=${lang}`].filter(Boolean).join('&');

export function getMedicines(seniorId: string, contactId?: string, lang = 'en'): Promise<MedicinesView> {
  return BASE ? http(`/senior/${seniorId}/medicines?${q(contactId, lang)}`) : mock.getMedicines(seniorId, lang);
}

export function getPrevention(seniorId: string, contactId?: string, lang = 'en'): Promise<PreventionView> {
  return BASE ? http(`/senior/${seniorId}/prevention?${q(contactId, lang)}`) : mock.getPrevention(seniorId, lang);
}

export interface TasteSearchResult {
  entity_id: string;
  name: string;
  type: string;
  tags: string[];
}

export function searchTaste(query: string): Promise<{ query: string; mode: string; results: TasteSearchResult[] }> {
  if (!BASE) {
    return Promise.resolve({
      query,
      mode: 'fixture',
      results: [
        { entity_id: 'urn:entity:artist:teresa-teng', name: 'Teresa Teng (邓丽君)', type: 'urn:entity:artist', tags: ['mandopop', '1970s'] },
        { entity_id: 'urn:entity:artist:frances-yip', name: 'Frances Yip (叶丽仪)', type: 'urn:entity:artist', tags: ['cantopop', '1980s'] },
        { entity_id: 'urn:entity:artist:p-ramlee', name: 'P. Ramlee', type: 'urn:entity:artist', tags: ['malay_classics', 'jalan_ampas'] },
        { entity_id: 'urn:entity:place:teochew-fish-soup', name: 'Teochew Steamed Fish Porridge', type: 'urn:entity:place', tags: ['low_sodium_available', 'easy_to_chew'] },
      ].filter((r) => !query.trim() || r.name.toLowerCase().includes(query.toLowerCase()) || r.tags.some((t) => t.includes(query.toLowerCase()))),
    });
  }
  return http(`/taste/search?q=${encodeURIComponent(query)}`);
}

export function addSeniorTaste(seniorId: string, _seed: string): Promise<TastePlan> {
  if (!BASE) return mockInsights.getSeniorTasteMock(seniorId);
  return http(`/senior/${seniorId}/taste`, { method: 'POST', body: JSON.stringify({ seed: _seed }) });
}

export function getSeniorTaste(seniorId: string, opts?: { psi?: number; rain_mm?: number }): Promise<TastePlan> {
  if (!BASE) return mockInsights.getSeniorTasteMock(seniorId, opts);
  const qs = [
    opts?.psi !== undefined && `psi=${opts.psi}`,
    opts?.rain_mm !== undefined && `rain_mm=${opts.rain_mm}`,
  ].filter(Boolean).join('&');
  return http(`/senior/${seniorId}/taste${qs ? `?${qs}` : ''}`);
}

export function toggleSeniorDietary(seniorId: string, toggle: string, opts?: { psi?: number; rain_mm?: number }): Promise<TastePlan> {
  if (!BASE) return mockInsights.toggleSeniorDietaryMock(seniorId, toggle, opts);
  return http(`/senior/${seniorId}/dietary`, { method: 'PUT', body: JSON.stringify({ toggle, ...opts }) });
}

export function getAacTasteGroup(aacId: string): Promise<GroupTastePlan> {
  return BASE ? http(`/aac/${aacId}/taste-group`) : mockAac.getAacTasteGroup(aacId);
}

const MOCK_KOPI_KAKIS: KopiKakisResponse = {
  aac_id: 'aac-ang-mo-kio',
  aac_name: 'Ang Mo Kio Active Ageing Centre',
  date: '2026-10-14',
  qloo_mode: 'fixture',
  focus_senior_id: 'tan',
  matches: [
    {
      pair_id: 'tan__wong',
      senior_a: { id: 'tan', name: 'Mr Tan Ah Kow', language: 'en', likes: ['kopitiam', 'Teresa Teng', 'Teochew porridge'] },
      senior_b: { id: 'wong', name: 'Mdm Wong Mei Ling', language: 'zh', likes: ['Teresa Teng', 'Frances Yip', 'clear fish soup'] },
      affinity_score: 0.91,
      affinity_pct: 91,
      shared_hooks: ['Both love Teresa Teng (邓丽君) & Frances Yip', 'Shared taste for warm Teochew fish porridge & morning kopi'],
      shared_tags: ['mandopop', '1970s', 'nostalgia', 'teochew', 'low_sodium_available'],
      shared_urns: ['urn:entity:artist:teresa-teng', 'urn:entity:place:teochew-fish-soup'],
      shared_language_label: 'English / Mandarin / Hokkien',
      union_badges: ['Low-salt / less gravy', 'No grapefruit / pomelo (statin/BP check)', 'Indoor seated'],
      safe_meeting_spot: {
        entity_id: 'urn:entity:place:teochew-fish-soup',
        name: 'Kebun Baru Kopitiam & Teochew Steamed Fish Porridge Corner',
        category: 'hawker_food',
        indoor: true,
        fit_badges: ['Low-salt / less gravy', 'No grapefruit / pomelo', 'Easy to chew'],
      },
      companion_music: 'Teresa Teng — The Moon Represents My Heart (月亮代表我的心)',
      befriender_script: {
        en: 'Introduce Mr Tan Ah Kow and Mdm Wong Mei Ling over a cup of kopi: "You both enjoy Teresa Teng and warm Teochew fish porridge — would you like to sit together at Kebun Baru Kopitiam before the morning session?" Everything suggested already respects both of their low-salt and medicine-leaflet needs.',
        zh: '向陈阿狗伯伯和黄美玲阿姨做破冰介绍：“你们两位都喜欢听邓丽君的老歌、喝清淡潮州鱼粥，要不要在活动开始前一起在哥本峇鲁咖啡店坐坐聊聊？”推荐茶点已同时兼顾两人的少盐与用药饮食护栏。',
      },
    },
    {
      pair_id: 'tan__chua',
      senior_a: { id: 'tan', name: 'Mr Tan Ah Kow', language: 'en', likes: ['kopitiam', 'Cathay classics', 'taichi'] },
      senior_b: { id: 'chua', name: 'Mr Chua Swee Heng', language: 'zh', likes: ['Shaw Brothers', 'kopi o kosong', 'radio oldies'] },
      affinity_score: 0.85,
      affinity_pct: 85,
      shared_hooks: ['Both enjoy 1960s Cathay / Shaw Brothers cinema & Nanyang kopi', 'Morning gentle exercise & radio classics'],
      shared_tags: ['singapore_cinema', '1960s', 'kopi', 'nostalgia'],
      shared_urns: ['urn:entity:movie:mambo-girl', 'urn:entity:place:kopitiam-heritage'],
      shared_language_label: 'Mandarin / Hokkien',
      union_badges: ['Low-salt / less gravy', 'Low-purine (gout-safe)', 'Step-free seating'],
      safe_meeting_spot: {
        entity_id: 'urn:entity:place:soy-beancurd-less-sugar',
        name: 'Traditional Warm Tau Huay & Soy Milk Corner (Siew Dai / Kosong)',
        category: 'snack',
        indoor: true,
        fit_badges: ['Low-purine (gout-safe)', 'Less sugar / kosong', 'Seated indoor'],
      },
      companion_music: 'Fei Yu-ching (费玉清) — Golden 1970s Classics',
      befriender_script: {
        en: 'Introduce Mr Tan Ah Kow and Mr Chua Swee Heng: "You both remember the old Cathay and Shaw Brothers matinees and morning kopi o kosong — let us grab a warm tau huay kosong together before karaoke starts."',
        zh: '向陈伯伯和蔡瑞兴伯伯介绍：“你们都爱看邵氏和国泰老电影，不如一起喝碗少糖热豆花，聊聊当年看戏的趣事。”',
      },
    },
  ],
  guardrail: { passed: true, checked_count: 6, reasons: [] },
};

export function getAacKopiKakis(aacId: string): Promise<KopiKakisResponse> {
  return BASE ? http(`/aac/${aacId}/kopi-kakis`) : Promise.resolve({ ...MOCK_KOPI_KAKIS, aac_id: aacId });
}

export function getSeniorKopiKakis(seniorId: string): Promise<KopiKakisResponse> {
  return BASE ? http(`/senior/${seniorId}/kopi-kakis`) : Promise.resolve({ ...MOCK_KOPI_KAKIS, focus_senior_id: seniorId });
}

const MEM_STORAGE_KEY = 'careloop-mock-memories';

const MOCK_MEMORY_LANE: MemoryLaneResponse = {
  senior_id: 'tan',
  senior_name: 'Mr Tan Ah Kow',
  date: '2026-10-14',
  language: 'en',
  qloo_mode: 'fixture',
  daily_prompt: {
    prompt: 'You enjoy Teresa Teng (邓丽君) and traditional Nanyang kopi — what was your favourite coffee shop, cinema, or weekend outing in your 20s?',
    qloo_seed: 'Teresa Teng (邓丽君)',
    qloo_urn: 'urn:entity:artist:teresa-teng',
    music_companion: 'Teresa Teng — Sweet Honey (甜蜜蜜)',
    film_companion: 'Mambo Girl (曼波女郎) — Cathay Classics',
    food_companion: 'Kebun Baru Kopitiam (Kopi O Kosong)',
    starter_chips: [
      'Watching a weekend matinee at Capitol or Cathay Cinema',
      'Drinking morning kopi o kosong with old neighbours',
      'Listening to Rediffusion and Teresa Teng cassettes after dinner',
    ],
  },
  capsules: [
    {
      id: 'mem-seed-1',
      senior_id: 'tan',
      date: '2026-10-12',
      qloo_seed: 'Teresa Teng (邓丽君)',
      qloo_urn: 'urn:entity:artist:teresa-teng',
      era_tag: '1970s Nostalgia',
      prompt: 'Which song always brings back memories of family dinners?',
      story_text: 'Every Sunday evening in Toa Payoh, my late wife would play Teresa Teng on our cassette player while steaming threadfin fish with ginger.',
      language: 'en',
      recorded_by: 'Mr Tan Ah Kow (Morning Check-in)',
    },
    {
      id: 'mem-seed-2',
      senior_id: 'tan',
      date: '2026-10-09',
      qloo_seed: 'Cathay & Shaw Brothers Classics',
      qloo_urn: 'urn:entity:movie:mambo-girl',
      era_tag: '1960s Cinema',
      prompt: 'What was your favourite cinema outing when the children were young?',
      story_text: 'We took Bus 13 down to Capitol Theatre for 50-cent matinee tickets, then shared warm soy milk and youtiao by the roadside stall.',
      language: 'en',
      recorded_by: 'Wei Ling (Family Visit Kit)',
    },
  ],
  guardrail: { passed: true, checked_count: 5, reasons: [] },
};

export function getSeniorMemories(seniorId: string, lang?: string): Promise<MemoryLaneResponse> {
  if (BASE) {
    const qs = lang ? `?lang=${encodeURIComponent(lang)}` : '';
    return http(`/senior/${seniorId}/memories${qs}`);
  }
  try {
    const extraRaw = localStorage.getItem(`${MEM_STORAGE_KEY}:${seniorId}`);
    const extra: MemoryCapsule[] = extraRaw ? JSON.parse(extraRaw) : [];
    return Promise.resolve({
      ...MOCK_MEMORY_LANE,
      senior_id: seniorId,
      capsules: [...extra, ...MOCK_MEMORY_LANE.capsules],
    });
  } catch {
    return Promise.resolve({ ...MOCK_MEMORY_LANE, senior_id: seniorId });
  }
}

export function postSeniorMemory(
  seniorId: string,
  body: { story_text: string; qloo_seed?: string; prompt?: string; recorded_by?: string; language?: string },
): Promise<MemoryCapsule> {
  if (BASE) {
    return http(`/senior/${seniorId}/memories`, { method: 'POST', body: JSON.stringify(body) });
  }
  const cap: MemoryCapsule = {
    id: `mem-${Date.now()}`,
    senior_id: seniorId,
    date: '2026-10-14',
    qloo_seed: body.qloo_seed || 'Teresa Teng (邓丽君)',
    qloo_urn: 'urn:entity:artist:teresa-teng',
    era_tag: '1970s Nostalgia',
    prompt: body.prompt || MOCK_MEMORY_LANE.daily_prompt.prompt,
    story_text: body.story_text,
    language: (body.language as any) || 'en',
    recorded_by: body.recorded_by || 'Wei Ling (Family Caregiver)',
    guardrail: { passed: true, reasons: [] },
  };
  try {
    const extraRaw = localStorage.getItem(`${MEM_STORAGE_KEY}:${seniorId}`);
    const extra: MemoryCapsule[] = extraRaw ? JSON.parse(extraRaw) : [];
    localStorage.setItem(`${MEM_STORAGE_KEY}:${seniorId}`, JSON.stringify([cap, ...extra]));
  } catch {
    /* ignore */
  }
  return Promise.resolve(cap);
}

const MOCK_RESPITE_PLAN: RespitePlanResponse = {
  senior_id: 'tan',
  senior_name: 'Mr Tan Ah Kow',
  date: '2026-10-14',
  qloo_mode: 'fixture',
  burnout_shield: {
    active: true,
    streak_days: 5,
    has_recent_vent: true,
    trigger_reason: 'Wei Ling has been on primary duty for 5 consecutive days — scheduling a guilt-free 3-hour breather.',
  },
  window_hours: 3,
  recommended_slot: 'Wednesday 14:00 – 17:00 (3-Hour Guilt-Free Respite Window)',
  primary_caregiver: { id: 'tan-weiling', name: 'Wei Ling' },
  backup_contact: { id: 'tan-kelvin', name: 'Kelvin' },
  matched_programme: {
    id: 'prog-aac-100-2',
    title: '1970s Mandopop & Teresa Teng Sing-Along Social',
    when: 'Wednesday 14:00 – 16:00',
    where: 'Ang Mo Kio Active Ageing Centre (Indoor Hall)',
    kind: 'singing',
    indoor: true,
    qloo_fit_pct: 94,
    why_safe_and_loved:
      'Matched via Qloo affinity for Teresa Teng & Fei Yu-ching (94% fit); fully indoor air-conditioned hall with seated layout and low-sodium tea service.',
    safety_badges: ['Indoor air-conditioned', 'Low-salt / less gravy', 'No grapefruit / pomelo (amlodipine check)'],
  },
  companion_picks: {
    post_session_treat: 'Kebun Baru Kopitiam — Clear Fish Soup (Less Salt)',
    music_on_way: 'Teresa Teng (邓丽君) — The Moon Represents My Heart',
  },
  summary:
    'Guilt-Free 3-Hour Respite Plan: While Mr Tan enjoys the 1970s Mandopop Sing-Along at Ang Mo Kio AAC (94% Qloo fit, indoor & low-sodium safe), Kelvin covers the 14:00–17:00 rota window so Wei Ling can rest.',
  whatsapp_text:
    'CareLoop 3-Hour Respite Handover (Wed 14:00–17:00):\n' +
    '• Senior: Mr Tan Ah Kow\n' +
    '• Qloo-Matched AAC Session: 1970s Mandopop & Teresa Teng Sing-Along Social at Ang Mo Kio AAC (94% taste fit, indoor & low-sodium safe)\n' +
    '• Rota Cover: Kelvin covering for Wei Ling (5-day streak)\n' +
    '• Post-session treat: Kebun Baru Kopitiam — Clear Fish Soup (Less Salt)',
  guardrail: { passed: true, checked_count: 4, reasons: [] },
};

const RESPITE_SENIOR_NAMES: Record<string, string> = {
  tan: 'Mr Tan Ah Kow',
  wong: 'Mdm Wong Mei Ling',
  teo: 'Mrs Teo Siew Lan',
  kaur: 'Mdm Gurmit Kaur',
  rahman: 'Encik Abdul Rahman',
  chua: 'Mdm Chua Swee Neo',
};

export function getSeniorRespite(seniorId: string, streakDays?: number): Promise<RespitePlanResponse> {
  if (BASE) {
    const qs = streakDays !== undefined ? `?streak_days=${streakDays}` : '';
    return http(`/senior/${seniorId}/respite${qs}`);
  }
  const sName = RESPITE_SENIOR_NAMES[seniorId] ?? 'Mr Tan Ah Kow';
  return Promise.resolve({
    ...MOCK_RESPITE_PLAN,
    senior_id: seniorId,
    senior_name: sName,
    summary: MOCK_RESPITE_PLAN.summary.replace('Mr Tan', sName),
    whatsapp_text: MOCK_RESPITE_PLAN.whatsapp_text.replace('Mr Tan Ah Kow', sName),
    burnout_shield: {
      ...MOCK_RESPITE_PLAN.burnout_shield,
      streak_days: streakDays ?? MOCK_RESPITE_PLAN.burnout_shield.streak_days,
    },
  });
}

const MOCK_TASTE_EVAL: TasteEvalBenchmark = {
  benchmark_version: '2.0-qloo-ablation',
  evaluated_on: '2026-10-14',
  total_personas: 38,
  cohorts: { demo_seniors: 13, synthetic_personas: 25 },
  architectures: [
    {
      id: 'generic_llm',
      name: '1. Generic LLM Baseline',
      description: 'Unconstrained prompt ("Suggest food, music, and activities for a Singapore senior").',
      clinical_violation_rate_pct: 100.0,
      personas_with_violation: 38,
      total_violations: 92,
      cultural_specificity_score: 19.0,
      guardrail_pass_rate_pct: 100.0,
      multilingual_coverage_pct: 25.0,
    },
    {
      id: 'rule_filtered_llm',
      name: '2. Rule-Filtered LLM (No Qloo)',
      description: 'Applies basic condition tags to generic LLM picks without Qloo entity resolution or cross-domain insights.',
      clinical_violation_rate_pct: 55.3,
      personas_with_violation: 21,
      total_violations: 29,
      cultural_specificity_score: 22.0,
      guardrail_pass_rate_pct: 100.0,
      multilingual_coverage_pct: 50.0,
    },
    {
      id: 'careloop_qloo',
      name: '3. CareLoop + Qloo Taste AI',
      description: 'Qloo /search entity resolution + cross-domain /v2/insights + deterministic clinical/leaflet/weather filter + guardrail.py.',
      clinical_violation_rate_pct: 0.0,
      personas_with_violation: 0,
      total_violations: 0,
      cultural_specificity_score: 82.2,
      guardrail_pass_rate_pct: 100.0,
      multilingual_coverage_pct: 100.0,
    },
  ],
  multilingual_breakdown: {
    en: { label: 'English (en)', tested_personas: 38, guardrail_pass_rate_pct: 100.0, cultural_specificity_avg: 82.2 },
    zh: { label: '华语 Mandarin (zh)', tested_personas: 38, guardrail_pass_rate_pct: 100.0, cultural_specificity_avg: 84.5 },
    ms: { label: 'Bahasa Melayu (ms)', tested_personas: 38, guardrail_pass_rate_pct: 100.0, cultural_specificity_avg: 81.8 },
    ta: { label: 'தமிழ் Tamil (ta)', tested_personas: 38, guardrail_pass_rate_pct: 100.0, cultural_specificity_avg: 81.2 },
  },
  per_persona: [
    {
      persona_id: 'tan',
      name: 'Mr Tan Ah Kow',
      cohort: 'demo_senior',
      language: 'en',
      conditions: ['hypertension', 'high_cholesterol'],
      medicines: ['amlodipine', 'atorvastatin'],
      dietary_prefs: [],
      likes: ['kopitiam', 'Teresa Teng', 'Teochew porridge', 'Cathay classics'],
      generic_llm: {
        picks: ['Ah Chew Desserts — Mango Pomelo Sago', 'Old Street Salted Fish & Pork Belly Claypot Rice', 'Botanic Gardens Open-Air Tai Chi Lawn'],
        violation_count: 3,
        violations: [
          { item: 'Ah Chew Desserts — Mango Pomelo Sago', rule_code: 'med.statin_grapefruit', rule_id: 'med_food.grapefruit_pomelo', reason: 'Pomelo/grapefruit interacts with amlodipine/atorvastatin' },
          { item: 'Old Street Salted Fish & Pork Belly Claypot Rice', rule_code: 'cond.hypertension', rule_id: 'diet.hypertension.low_sodium', reason: 'High-sodium cured fish conflicts with hypertension care' },
          { item: 'Botanic Gardens Open-Air Tai Chi Lawn', rule_code: 'env.indoor_only', rule_id: 'weather.indoor_only', reason: 'Outdoor venue unsafe during PSI > 100 haze' },
        ],
        specificity_score: 19.0,
        guardrail_passed: true,
      },
      rule_filtered_llm: {
        picks: ['Ah Chew Desserts — Mango Pomelo Sago', 'Generic Low-Salt Soup', 'Listen to Classic Oldies'],
        violation_count: 1,
        violations: [
          { item: 'Ah Chew Desserts — Mango Pomelo Sago', rule_code: 'med.statin_grapefruit', rule_id: 'med_food.grapefruit_pomelo', reason: 'Misses pharmacist leaflet check on pomelo/grapefruit' },
        ],
        specificity_score: 22.0,
        guardrail_passed: true,
      },
      careloop_qloo: {
        picks: ['Kebun Baru Kopitiam & Community Corner', 'Teochew Steamed Fish Porridge & Clear Soup Stall'],
        music_pick: 'Teresa Teng (邓丽君) & Fei Yu-ching (费玉清)',
        movie_pick: 'Mambo Girl (曼波女郎) — 1960s Cathay Classics',
        filtered_out_count: 3,
        filtered_out_rules: ['med.statin_grapefruit', 'cond.hypertension', 'env.indoor_only'],
        violation_count: 0,
        violations: [],
        specificity_score: 88.0,
        guardrail_passed: true,
        explanation_sample: 'Qloo links Teresa Teng & kopitiam nostalgia to Kebun Baru Kopitiam (Indoor, Low-salt available, No grapefruit/pomelo).',
      },
    },
    {
      persona_id: 'aminah',
      name: 'Mdm Aminah Binte Yusof',
      cohort: 'demo_senior',
      language: 'ms',
      conditions: ['hypertension', 'diabetes'],
      medicines: ['amlodipine', 'metformin'],
      dietary_prefs: ['halal'],
      likes: ['P. Ramlee', 'Saloma', 'gerai kopi', 'kampung cinema'],
      generic_llm: {
        picks: ['Old Street Salted Fish & Pork Belly Claypot Rice', 'Traditional Full-Sugar Teh Tarik & Kuih', 'Ah Chew Desserts — Mango Pomelo Sago'],
        violation_count: 3,
        violations: [
          { item: 'Old Street Salted Fish & Pork Belly Claypot Rice', rule_code: 'diet.halal', rule_id: 'pref.halal', reason: 'Non-halal pork dish violates Halal requirement' },
          { item: 'Traditional Full-Sugar Teh Tarik & Kuih', rule_code: 'cond.diabetes', rule_id: 'diet.diabetes.low_sugar', reason: 'High-sugar drink conflicts with diabetes care' },
          { item: 'Ah Chew Desserts — Mango Pomelo Sago', rule_code: 'med.statin_grapefruit', rule_id: 'med_food.grapefruit_pomelo', reason: 'Pomelo interacts with amlodipine' },
        ],
        specificity_score: 19.0,
        guardrail_passed: true,
      },
      rule_filtered_llm: {
        picks: ['Ah Chew Desserts — Mango Pomelo Sago', 'Generic Halal Cafe', 'Malay Radio'],
        violation_count: 1,
        violations: [
          { item: 'Ah Chew Desserts — Mango Pomelo Sago', rule_code: 'med.statin_grapefruit', rule_id: 'med_food.grapefruit_pomelo', reason: 'Misses amlodipine leaflet check' },
        ],
        specificity_score: 22.0,
        guardrail_passed: true,
      },
      careloop_qloo: {
        picks: ['Geylang Serai Heritage Halal Kopi & Asam Pedas Corner (Less Salt / Kurang Manis)', 'Traditional Warm Tau Huay & Soy Milk (Kosong)'],
        music_pick: 'Tan Sri P. Ramlee & Biduanita Saloma Duets',
        movie_pick: 'Bujang Lapok (1957) — Jalan Ampas Shaw Malay Film Productions',
        filtered_out_count: 3,
        filtered_out_rules: ['diet.halal', 'cond.diabetes', 'med.statin_grapefruit'],
        violation_count: 0,
        violations: [],
        specificity_score: 86.0,
        guardrail_passed: true,
        explanation_sample: 'Qloo links P. Ramlee & Jalan Ampas nostalgia to Geylang Serai Heritage Halal Kopi (Halal-certified, Kurang Manis, Low-sodium).',
      },
    },
    {
      persona_id: 'chua',
      name: 'Mr Chua Swee Heng',
      cohort: 'demo_senior',
      language: 'zh',
      conditions: ['gout', 'hypertension'],
      medicines: ['amlodipine'],
      dietary_prefs: [],
      likes: ['Shaw Brothers', 'Teochew opera', 'kopi o kosong'],
      generic_llm: {
        picks: ['Song Fa Style Bak Kut Teh & Organ Broth Stall', 'Old Street Salted Fish & Pork Belly Claypot Rice', 'Ah Chew Desserts — Mango Pomelo Sago'],
        violation_count: 3,
        violations: [
          { item: 'Song Fa Style Bak Kut Teh & Organ Broth Stall', rule_code: 'cond.gout', rule_id: 'diet.gout.low_purine', reason: 'High-purine organ broth triggers gout flare risk' },
          { item: 'Old Street Salted Fish & Pork Belly Claypot Rice', rule_code: 'cond.hypertension', rule_id: 'diet.hypertension.low_sodium', reason: 'High-sodium cured fish conflicts with hypertension' },
          { item: 'Ah Chew Desserts — Mango Pomelo Sago', rule_code: 'med.statin_grapefruit', rule_id: 'med_food.grapefruit_pomelo', reason: 'Pomelo interacts with amlodipine' },
        ],
        specificity_score: 19.0,
        guardrail_passed: true,
      },
      rule_filtered_llm: {
        picks: ['Song Fa Style Bak Kut Teh & Organ Broth Stall', 'Generic Porridge', 'Old Movies'],
        violation_count: 1,
        violations: [
          { item: 'Song Fa Style Bak Kut Teh & Organ Broth Stall', rule_code: 'cond.gout', rule_id: 'diet.gout.low_purine', reason: 'Misses high-purine organ broth tag' },
        ],
        specificity_score: 22.0,
        guardrail_passed: true,
      },
      careloop_qloo: {
        picks: ['Teochew Steamed Fish Porridge & Clear Soup Stall', 'Traditional Warm Tau Huay & Soy Milk (Kosong)'],
        music_pick: 'Fei Yu-ching (费玉清) & Teochew Opera Classics',
        movie_pick: 'The 36th Chamber of Shaolin — Shaw Brothers Classic',
        filtered_out_count: 3,
        filtered_out_rules: ['cond.gout', 'cond.hypertension', 'med.statin_grapefruit'],
        violation_count: 0,
        violations: [],
        specificity_score: 85.0,
        guardrail_passed: true,
        explanation_sample: 'Qloo links Shaw Brothers nostalgia to Teochew Steamed Fish Porridge (Low-purine gout-safe, Low-salt, No grapefruit).',
      },
    },
  ],
};

export function getTasteEval(): Promise<TasteEvalBenchmark> {
  return BASE ? http('/eval/taste') : Promise.resolve(MOCK_TASTE_EVAL);
}

export function postSeniorCheckin(
  seniorId: string,
  text: string,
  language = 'en',
): Promise<{
  checkin_id: string;
  rung: number;
  rule_id: string;
  reply_text: string;
  extracted_tastes: { phrase: string; canonical: string; domain: string }[];
}> {
  if (BASE) {
    return http('/checkin', { method: 'POST', body: JSON.stringify({ senior_id: seniorId, text, language }) });
  }
  return Promise.resolve({
    checkin_id: `ci-${Date.now()}`,
    rung: 2,
    rule_id: '2.low_day',
    reply_text:
      'Hear you, Mr Tan — some days feel a bit sian. Since you enjoy P. Ramlee, Teresa Teng, and warm Teochew fish soup, how about putting on a classic song or stepping into Kebun Baru Kopitiam for a light bowl of clear fish soup (less salt)?',
    extracted_tastes: [
      { phrase: 'P. Ramlee', canonical: 'P. Ramlee', domain: 'music' },
      { phrase: 'Teresa Teng', canonical: 'Teresa Teng', domain: 'music' },
      { phrase: 'fish soup', canonical: 'Teochew fish porridge', domain: 'food' },
    ],
  });
}
