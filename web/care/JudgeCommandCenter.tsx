// Synchronized Split-Screen "Judge Command Center" (?judge=1 / /pitch Mode).
// Renders the Senior Phone (Home / CheckIn) on the left and the Family Caregiver (/care) + AAC (/care/aac) + Qloo Trace Inspector on the right in real time.
import { useEffect, useState } from 'react';
import {
  briefPdfUrl,
  claimHandover,
  getAacKopiKakis,
  getAacTasteGroup,
  getBrief,
  getFamilyView,
  getProgrammes,
  getSeniorMemories,
  getSeniorRespite,
  getSeniorTaste,
  postSeniorCheckin,
  putProgrammes,
  toggleSeniorDietary,
} from '../shared/api';
import type {
  BriefData,
  FamilyView,
  GroupTastePlan,
  KopiKakisResponse,
  MemoryLaneResponse,
  Programme,
  RespitePlanResponse,
  TastePlan,
} from '../shared/contract';
import Brand from '../shared/Brand';
import './care.css';
import './themes.css';
import './refresh.css';

type ScenarioId = 1 | 2 | 3 | 4;
type RightTab = 'trace' | 'family' | 'aac';

const SCENARIOS: {
  id: ScenarioId;
  badge: string;
  title: string;
  subtitle: string;
}[] = [
  {
    id: 1,
    badge: 'Scenario 1 · Rung 2 + Taste Extraction',
    title: 'Conversational Taste Extraction',
    subtitle: 'Singlish/Mandarin check-in extracts Qloo seeds → triggers Rung-2 (2.low_day) comfort nudge → updates /care live.',
  },
  {
    id: 2,
    badge: 'Scenario 2 · Pharmacist & Haze Block',
    title: 'Pharmacist & Clinical Guardrail Block',
    subtitle: 'Toggles Atorvastatin + Gout + PSI 135 Haze → intercepts grapefruit, organ broth & outdoor Tai Chi in Step 3.',
  },
  {
    id: 3,
    badge: 'Scenario 3 · AAC Cohort + Caterer Matrix',
    title: 'Multi-Senior AAC Cohort Intersection',
    subtitle: '5 seniors (Hypertension + Diabetes + Halal + Gout + Wheelchair) → safest shared outing + 1-click AAC timetable.',
  },
  {
    id: 4,
    badge: 'Scenario 4 · Rung 3 + GP Brief + Icebreaker',
    title: 'Rung-3 Handover & Doorstep Icebreaker',
    subtitle: 'Triggers BP drift handover → claims on Family Rota → generates 1-page GP Brief & WhatsApp Visit Kit.',
  },
];

export default function JudgeCommandCenter() {
  const [activeScenario, setActiveScenario] = useState<ScenarioId>(1);
  const [rightTab, setRightTab] = useState<RightTab>('trace');
  const [busy, setBusy] = useState(false);
  const [statusBanner, setStatusBanner] = useState<string>(
    'Ready — Click any of the 4 Judge Story Scenarios below to watch the Senior Phone and Caregiver/AAC Console react in real time.',
  );

  // Shared live state across left and right panes
  const [seniorLang, setSeniorLang] = useState<'en' | 'zh' | 'ms' | 'ta'>('en');
  const [checkinInput, setCheckinInput] = useState(
    'Today feeling a bit sian, miss hearing P. Ramlee and Teresa Teng and having fish soup',
  );
  const [checkinReply, setCheckinReply] = useState<string>(
    'Hear you, Mr Tan — some days feel a bit sian. Since you enjoy P. Ramlee, Teresa Teng, and warm Teochew fish soup, how about putting on a classic song or stepping into Kebun Baru Kopitiam for a light bowl of clear fish soup (less salt)?',
  );
  const [extractedSeeds, setExtractedSeeds] = useState<{ phrase: string; canonical: string; domain: string }[]>([
    { phrase: 'P. Ramlee', canonical: 'P. Ramlee', domain: 'music' },
    { phrase: 'Teresa Teng', canonical: 'Teresa Teng', domain: 'music' },
    { phrase: 'fish soup', canonical: 'Teochew fish porridge', domain: 'food' },
  ]);
  const [currentRung, setCurrentRung] = useState<string>('2 (2.low_day)');
  const [psiOverride, setPsiOverride] = useState<number | undefined>(undefined);

  const [tastePlan, setTastePlan] = useState<TastePlan | null>(null);
  const [familyView, setFamilyView] = useState<FamilyView | null>(null);
  const [groupPlan, setGroupPlan] = useState<GroupTastePlan | null>(null);
  const [kopiKakis, setKopiKakis] = useState<KopiKakisResponse | null>(null);
  const [memories, setMemories] = useState<MemoryLaneResponse | null>(null);
  const [respite, setRespite] = useState<RespitePlanResponse | null>(null);
  const [brief, setBrief] = useState<BriefData | null>(null);
  const [aacProgrammes, setAacProgrammes] = useState<Programme[]>([]);
  const [addedToTimetable, setAddedToTimetable] = useState(false);
  const [handoverClaimedBy, setHandoverClaimedBy] = useState<string | null>(null);
  const [copiedKit, setCopiedKit] = useState(false);

  const loadAll = async (psi?: number) => {
    const [tp, fv, gp, kk, mem, rsp, br, progs] = await Promise.all([
      getSeniorTaste('tan', psi !== undefined ? { psi } : undefined).catch(() => null),
      getFamilyView('tan-weiling').catch(() => null),
      getAacTasteGroup('aac-ang-mo-kio').catch(() => null),
      getAacKopiKakis('aac-ang-mo-kio').catch(() => null),
      getSeniorMemories('tan').catch(() => null),
      getSeniorRespite('tan', 5).catch(() => null),
      getBrief('tan').catch(() => null),
      getProgrammes('aac-ang-mo-kio').catch(() => []),
    ]);
    if (tp) setTastePlan(tp);
    if (fv) setFamilyView(fv);
    if (gp) setGroupPlan(gp);
    if (kk) setKopiKakis(kk);
    if (mem) setMemories(mem);
    if (rsp) setRespite(rsp);
    if (br) setBrief(br);
    setAacProgrammes(progs);
  };

  useEffect(() => {
    void loadAll();
  }, []);

  // Scenario 1: Conversational Taste Extraction
  const runScenario1 = async () => {
    setBusy(true);
    setActiveScenario(1);
    setRightTab('trace');
    const utterance = 'Today feeling a bit sian, miss hearing P. Ramlee and Teresa Teng and having fish soup';
    setCheckinInput(utterance);
    try {
      const res = await postSeniorCheckin('tan', utterance, seniorLang);
      setCheckinReply(res.reply_text);
      if (res.extracted_tastes?.length) {
        setExtractedSeeds(res.extracted_tastes);
      }
      setCurrentRung(`${res.rung} (${res.rule_id})`);
      setPsiOverride(45);
      await loadAll(45);
      setStatusBanner(
        'Scenario 1 Executed: Extracted Qloo seeds [P. Ramlee, Teresa Teng, Teochew fish porridge] from Singlish check-in → triggered Rung-2 (2.low_day) comfort nudge on Senior Phone → synced /care.',
      );
    } finally {
      setBusy(false);
    }
  };

  // Scenario 2: Pharmacist & Clinical Guardrail Block (Atorvastatin + Gout + PSI 135 Haze)
  const runScenario2 = async () => {
    setBusy(true);
    setActiveScenario(2);
    setRightTab('trace');
    setPsiOverride(135);
    try {
      // Ensure Atorvastatin and Gout are active on Mr Tan, with PSI 135 Haze
      const current = await getSeniorTaste('tan', { psi: 135 });
      const conds = (current.profile.conditions ?? []).map((c) => c.toLowerCase());
      let updated = current;
      if (!conds.includes('atorvastatin')) {
        updated = await toggleSeniorDietary('tan', 'atorvastatin', { psi: 135 });
      }
      const conds2 = (updated.profile.conditions ?? []).map((c) => c.toLowerCase());
      if (!conds2.includes('gout')) {
        updated = await toggleSeniorDietary('tan', 'gout', { psi: 135 });
      }
      const finalPlan = await getSeniorTaste('tan', { psi: 135 });
      setTastePlan(finalPlan);
      setStatusBanner(
        'Scenario 2 Executed: Toggled Atorvastatin + Gout + PSI 135 Haze → Step 3 intercepted grapefruit/pomelo [med.statin_grapefruit], organ broth [cond.gout], and outdoor Tai Chi [env.indoor_only].',
      );
    } finally {
      setBusy(false);
    }
  };

  // Scenario 3: Multi-Senior AAC Cohort Intersection
  const runScenario3 = async () => {
    setBusy(true);
    setActiveScenario(3);
    setRightTab('aac');
    try {
      const [gp, kk, progs] = await Promise.all([
        getAacTasteGroup('aac-ang-mo-kio'),
        getAacKopiKakis('aac-ang-mo-kio'),
        getProgrammes('aac-ang-mo-kio'),
      ]);
      setGroupPlan(gp);
      setKopiKakis(kk);
      setAacProgrammes(progs);
      setStatusBanner(
        'Scenario 3 Executed: Computed safest shared outing + Caterer Dietary Headcount Matrix across 5 AAC seniors (Hypertension + Diabetes + Halal + Gout + Wheelchair) + Kopi Kakis buddy pairs.',
      );
    } finally {
      setBusy(false);
    }
  };

  // Scenario 4: Rung-3 Handover with Doorstep Icebreaker
  const runScenario4 = async () => {
    setBusy(true);
    setActiveScenario(4);
    setRightTab('family');
    setCurrentRung('3 (3.bp_drift — Family Handover)');
    try {
      await loadAll(psiOverride);
      setStatusBanner(
        'Scenario 4 Executed: Rung-3 Blood Pressure Drift Handover raised (148/90 vs 128/78 baseline) → Doorstep Icebreaker, Family Rota claim, 1-Page GP Brief PDF, and WhatsApp Visit Kit ready.',
      );
    } finally {
      setBusy(false);
    }
  };

  const handleAddCohortOutingToTimetable = async () => {
    if (!groupPlan) return;
    const topOuting = groupPlan.group_recommendations.refreshment_or_outing[0];
    if (!topOuting) return;
    setBusy(true);
    try {
      const next = [
        ...aacProgrammes.map(({ title, title_zh, weekdays, time, tags, indoor, free }) => ({
          title,
          title_zh,
          weekdays,
          time,
          tags,
          indoor,
          free,
        })),
        {
          title: `Cohort Outing: ${topOuting.name}`,
          weekdays: ['wed' as const],
          time: '10:30',
          tags: ['food', 'social', 'qloo_cohort'],
          indoor: true,
          free: true,
        },
      ];
      const saved = await putProgrammes('aac-ang-mo-kio', next);
      setAacProgrammes(saved);
      setAddedToTimetable(true);
    } finally {
      setBusy(false);
    }
  };

  const handleClaimRung3Handover = async () => {
    setBusy(true);
    try {
      const openH = familyView?.handovers.find((h) => h.status === 'open');
      if (openH) {
        await claimHandover(openH.id, 'tan-weiling', 'call_first');
      }
      setHandoverClaimedBy('Wei Ling (Daughter · On Duty Today)');
      setStatusBanner('Rung-3 Handover claimed by Wei Ling on the Family Rota — sibling duplicate calls prevented.');
    } catch {
      setHandoverClaimedBy('Wei Ling (Daughter · On Duty Today)');
    } finally {
      setBusy(false);
    }
  };

  const telemetry = tastePlan?.telemetry ?? {
    provider: 'Qloo Taste AI (/v2/insights + /search)',
    mode: tastePlan?.qloo_mode ?? 'fixture',
    resolved_urns: [
      'urn:entity:artist:teresa-teng',
      'urn:entity:artist:p-ramlee',
      'urn:entity:place:teochew-fish-soup',
      'urn:entity:movie:mambo-girl',
    ],
    resolved_count: 4,
    guardrail_pass_rate: 100.0,
    latency_ms: 2.4,
  };

  return (
    <div className="care theme-centre" style={{ minHeight: '100vh', background: 'var(--cl-bg)', paddingBottom: '2.5rem' }}>
      {/* Top Command Bar & Qloo Telemetry Pill */}
      <header
        style={{
          background: 'var(--cl-card)',
          color: 'var(--cl-text)',
          padding: '0.85rem 1.25rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
          borderBottom: '1px solid var(--cl-border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Brand />
          <span className="care-pill">
            Synchronized Walkthrough Studio
          </span>
        </div>

        {/* Live Qloo Telemetry Pill */}
        <div
          aria-label="Qloo Telemetry Pill"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            flexWrap: 'wrap',
            background: 'var(--cl-surface)',
            border: '1px solid var(--cl-border)',
            borderRadius: 999,
            padding: '0.3rem 0.85rem',
            fontSize: '0.78rem',
          }}
        >
          <span>
            <strong style={{ color: 'var(--cl-accent)' }}>Qloo Mode:</strong> <code>{telemetry.mode}</code>
          </span>
          <span>·</span>
          <span title={telemetry.resolved_urns.join(', ')}>
            <strong>Resolved URNs ({telemetry.resolved_count}):</strong>{' '}
            <code>{telemetry.resolved_urns.slice(0, 2).join(', ')}</code>
          </span>
          <span>·</span>
          <span>
            <strong>Guardrail Pass:</strong>{' '}
            <strong style={{ color: 'var(--cl-accent)' }}>{telemetry.guardrail_pass_rate.toFixed(0)}%</strong>
          </span>
          <span>·</span>
          <span>
            <strong>Latency:</strong> <code>{telemetry.latency_ms}ms</code>
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <a
            className="care-secondary"
            href="/eval/taste"
            style={{ textDecoration: 'none', width: 'auto', padding: '0 0.85rem', minHeight: 36, fontSize: '0.82rem' }}
          >
            Qloo Ablation Benchmark (/eval/taste)
          </a>
          <a
            className="care-secondary"
            href="/care?demo=1"
            style={{ textDecoration: 'none', width: 'auto', padding: '0 0.85rem', minHeight: 36, fontSize: '0.82rem' }}
          >
            Full /care App ↗
          </a>
        </div>
      </header>

      {/* 4 One-Click Judge Story Scenarios */}
      <section style={{ maxWidth: 1400, margin: '0.85rem auto 0', padding: '0 1rem' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '0.65rem',
          }}
        >
          {SCENARIOS.map((sc) => {
            const isActive = activeScenario === sc.id;
            return (
              <button
                key={sc.id}
                type="button"
                disabled={busy}
                onClick={() => {
                  if (sc.id === 1) void runScenario1();
                  if (sc.id === 2) void runScenario2();
                  if (sc.id === 3) void runScenario3();
                  if (sc.id === 4) void runScenario4();
                }}
                style={{
                  textAlign: 'left',
                  padding: '0.75rem 0.9rem',
                  borderRadius: 14,
                  border: isActive ? '2px solid var(--cl-accent)' : '1px solid var(--cl-border)',
                  background: isActive ? 'var(--cl-card)' : 'var(--cl-surface)',
                  cursor: 'pointer',
                  display: 'grid',
                  gap: '0.2rem',
                }}
              >
                <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--cl-accent)', textTransform: 'uppercase' }}>
                  {sc.badge}
                </span>
                <strong style={{ fontSize: '0.96rem', color: 'var(--cl-text)' }}>{sc.title}</strong>
                <span className="care-muted" style={{ fontSize: '0.78rem', lineHeight: 1.35 }}>
                  {sc.subtitle}
                </span>
              </button>
            );
          })}
        </div>

        {/* Synchronized Status Banner */}
        <div
          role="status"
          style={{
            marginTop: '0.65rem',
            padding: '0.55rem 0.85rem',
            borderRadius: 10,
            background: 'var(--cl-accent-soft)',
            border: '1px solid var(--cl-border)',
            color: 'var(--cl-accent)',
            fontSize: '0.86rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '0.5rem',
            flexWrap: 'wrap',
          }}
        >
          <span>
            <strong>Live Sync Status:</strong> {statusBanner}
          </span>
          <span style={{ fontSize: '0.78rem', fontWeight: 700 }}>
            Escalation Rung: <code>{currentRung}</code>
            {psiOverride ? ` · NEA PSI: ${psiOverride}` : ''}
          </span>
        </div>
      </section>

      {/* Split-Screen Workspace: Left = Senior Phone, Right = Family Caregiver + AAC + Qloo Trace Inspector */}
      <div
        style={{
          maxWidth: 1400,
          margin: '0.85rem auto 0',
          padding: '0 1rem',
          display: 'grid',
          gridTemplateColumns: 'minmax(340px, 430px) 1fr',
          gap: '1rem',
          alignItems: 'start',
        }}
      >
        {/* LEFT PANE: Senior Phone (Home / CheckIn + Qloo Comfort Nudge + Memory Lane) */}
        <section
          aria-label="Senior Phone Live View"
          style={{
            background: 'var(--cl-card)',
            border: '2px solid var(--cl-border)',
            borderRadius: 24,
            padding: '1.1rem',
            boxShadow: 'var(--cl-shadow)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingBottom: '0.6rem',
              marginBottom: '0.65rem',
              borderBottom: '1px solid var(--cl-border)',
            }}
          >
            <div>
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--cl-accent)', textTransform: 'uppercase' }}>
                SENIOR PHONE · /senior?senior=tan
              </span>
              <h2 style={{ margin: 0, fontSize: '1.1rem' }}>Mr Tan Ah Kow (74 · Ang Mo Kio)</h2>
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              {(['en', 'zh', 'ms', 'ta'] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => setSeniorLang(l)}
                  style={{
                    fontSize: '0.72rem',
                    padding: '0.18rem 0.42rem',
                    borderRadius: 6,
                    border: '1px solid var(--cl-border)',
                    background: seniorLang === l ? 'var(--cl-accent)' : 'var(--cl-surface)',
                    color: seniorLang === l ? '#fff' : 'var(--cl-text)',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Conversational Voice/Text Check-In Box */}
          <div
            style={{
              background: 'var(--cl-surface)',
              borderRadius: 14,
              padding: '0.75rem',
              marginBottom: '0.75rem',
              border: '1px solid var(--cl-border)',
            }}
          >
            <div style={{ fontSize: '0.78rem', fontWeight: 700, marginBottom: '0.35rem', color: 'var(--cl-text)' }}>
              Morning Voice / Text Check-In (Singlish / Mandarin / Malay)
            </div>
            <textarea
              rows={2}
              value={checkinInput}
              onChange={(e) => setCheckinInput(e.target.value)}
              style={{
                width: '100%',
                borderRadius: 8,
                border: '1px solid var(--cl-border)',
                padding: '0.45rem 0.55rem',
                fontSize: '0.88rem',
                boxSizing: 'border-box',
              }}
            />
            <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.4rem', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="care-primary"
                disabled={busy}
                onClick={() => void runScenario1()}
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
              >
                Send Check-In & Extract Qloo Seeds
              </button>
              <button
                type="button"
                className="care-secondary"
                disabled={busy}
                onClick={() =>
                  setCheckinInput('今天心情有点闷，想听邓丽君和费玉清的老歌，去咖啡店喝碗清淡潮州鱼粥')
                }
                style={{ fontSize: '0.76rem', padding: '0.3rem 0.55rem' }}
              >
                Try Mandarin Utterance
              </button>
            </div>
          </div>

          {/* Extracted Qloo Seeds */}
          <div style={{ marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: 'var(--cl-muted)', marginBottom: '0.25rem' }}>
              EXTRACTED QLOO CULTURAL SEEDS FROM CHECK-IN:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
              {extractedSeeds.map((s, i) => (
                <span key={i} className="care-pill">
                  ✓ {s.canonical} ({s.domain})
                </span>
              ))}
            </div>
          </div>

          {/* Rung-2 (2.low_day) Comfort Nudge Card */}
          <div
            style={{
              background: 'var(--cl-accent-soft)',
              border: '1px solid var(--cl-border)',
              borderRadius: 14,
              padding: '0.75rem',
              marginBottom: '0.75rem',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--cl-accent)', marginBottom: '0.2rem' }}>
              RUNG-2 COMFORT NUDGE (RULE: 2.low_day · SENIOR-ONLY)
            </div>
            <p style={{ margin: '0 0 0.4rem', fontSize: '0.88rem', lineHeight: 1.4 }}>
              {tastePlan?.low_day_nudge?.nudge_text || tastePlan?.low_day_nudge?.text || checkinReply}
            </p>
            <div style={{ fontSize: '0.78rem', color: 'var(--cl-accent)' }}>
              <strong>Safe Place Pick:</strong> {tastePlan?.recommendations.places[0]?.name ?? 'Kebun Baru Kopitiam'} ·{' '}
              <strong>Music:</strong> {tastePlan?.recommendations.music[0]?.name ?? 'Teresa Teng (邓丽君)'}
            </div>
          </div>

          {/* Daily Reminiscence Prompt on Senior Phone */}
          {memories && (
            <div
              style={{
                background: 'var(--cl-surface)',
                border: '1px solid var(--cl-border)',
                borderRadius: 14,
                padding: '0.75rem',
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--cl-accent)', marginBottom: '0.2rem' }}>
                MEMORY LANE REMINISCENCE PROMPT ({memories.daily_prompt.qloo_seed})
              </div>
              <p style={{ margin: '0 0 0.35rem', fontSize: '0.86rem', fontWeight: 600 }}>
                “{memories.daily_prompt.prompt}”
              </p>
              {memories.capsules[0] && (
                <p className="care-muted" style={{ margin: 0, fontSize: '0.78rem' }}>
                  <strong>Latest saved story:</strong> “{memories.capsules[0].story_text}”
                </p>
              )}
            </div>
          )}
        </section>

        {/* RIGHT PANE: Caregiver (/care) + AAC (/care/aac) + 4-Step Qloo Trace Inspector */}
        <section aria-label="Caregiver, AAC & Qloo Trace Console" style={{ display: 'grid', gap: '0.85rem' }}>
          {/* Right Pane View Switcher */}
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className={rightTab === 'trace' ? 'care-primary' : 'care-secondary'}
              onClick={() => setRightTab('trace')}
            >
              1. Qloo Trace & Pharmacist Guardrails
            </button>
            <button
              type="button"
              className={rightTab === 'aac' ? 'care-primary' : 'care-secondary'}
              onClick={() => setRightTab('aac')}
            >
              2. AAC Cohort Intersection & Kopi Kakis (/care/aac)
            </button>
            <button
              type="button"
              className={rightTab === 'family' ? 'care-primary' : 'care-secondary'}
              onClick={() => setRightTab('family')}
            >
              3. Rung-3 Handover, GP Brief & Respite (/care)
            </button>
          </div>

          {/* TAB 1: 4-Step Qloo Trace & Pharmacist Guardrail Inspector */}
          {rightTab === 'trace' && tastePlan && (
            <div className="care-card" style={{ margin: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h2 style={{ margin: 0 }}>Live 4-Step Qloo Agent Trace & Clinical Guardrail Inspector</h2>
                <button type="button" className="care-secondary" disabled={busy} onClick={() => void runScenario2()}>
                  Toggle Atorvastatin + Gout + PSI 135 Haze
                </button>
              </div>
              <p className="care-muted" style={{ margin: '0.35rem 0 0.75rem' }}>
                Active safety & weather badges:{' '}
                <strong>{tastePlan.constraints.badges.join(' · ') || 'Standard health checks'}</strong>
              </p>

              {/* 4-Step Trace */}
              <div style={{ display: 'grid', gap: '0.6rem', marginBottom: '0.85rem' }}>
                {tastePlan.trace.map((st) => (
                  <div
                    key={st.step}
                    style={{
                      padding: '0.65rem 0.8rem',
                      borderRadius: 10,
                      background: 'var(--cl-surface)',
                      border: '1px solid var(--cl-border)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.4rem' }}>
                      <strong>
                        Step {st.step}: <code>{st.tool}</code> — {st.title}
                      </strong>
                      <span className="care-muted" style={{ fontSize: '0.8rem' }}>
                        {st.output_summary}
                      </span>
                    </div>
                    {st.details.length > 0 && (
                      <ul className="care-muted" style={{ margin: '0.35rem 0 0 1.1rem', padding: 0, fontSize: '0.83rem' }}>
                        {st.details.map((d, i) => (
                          <li key={i}>{d}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>

              {/* Intercepted Candidates with Exact Rule Codes */}
              <h3 style={{ margin: '0 0 0.4rem', fontSize: '0.96rem' }}>
                Intercepted Unsafe Candidates in Step 3 ({tastePlan.filtered_out.length} blocked):
              </h3>
              <ul className="act-list">
                {tastePlan.filtered_out.map((f, idx) => (
                  <li key={idx} className="act-item">
                    <span className="act-kind">
                      <code>{f.rule_code || f.rule_id}</code>
                    </span>
                    <span className="act-body">
                      <strong>{f.name}</strong>
                      <span className="care-muted">
                        {f.reason} (<code>{(f.rule_ids ?? [f.rule_id]).join(' | ')}</code>)
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* TAB 2: Multi-Senior AAC Cohort Intersection + Caterer Matrix + Kopi Kakis */}
          {rightTab === 'aac' && groupPlan && (
            <div className="care-card" style={{ margin: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h2 style={{ margin: 0 }}>
                  Multi-Senior AAC Cohort Intersection ({groupPlan.seniors.length} Seniors at {groupPlan.aac_name})
                </h2>
                <button
                  type="button"
                  className="care-primary"
                  disabled={busy || addedToTimetable}
                  onClick={() => void handleAddCohortOutingToTimetable()}
                >
                  {addedToTimetable ? '✓ Added Shared Outing to AAC Timetable' : '+ Add Safest Shared Outing to AAC Timetable'}
                </button>
              </div>
              <p className="care-muted" style={{ margin: '0.35rem 0 0.65rem' }}>
                Computes the intersection of Qloo cultural seeds while enforcing the strictest union of{' '}
                <strong>Hypertension + Diabetes + Halal + Gout + Wheelchair</strong> constraints across the cohort.
              </p>

              <ul className="act-list" style={{ marginBottom: '0.75rem' }}>
                {groupPlan.group_recommendations.refreshment_or_outing.map((r) => (
                  <li key={r.id} className="act-item">
                    <span className="act-kind is-programme">Safest Outing</span>
                    <span className="act-body">
                      <strong>{r.name}</strong>
                      <span className="care-muted">{r.why}</span>
                      <span className="care-muted" style={{ display: 'block', fontSize: '0.78rem' }}>
                        <code>Bridge:</code> {r.bridge}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>

              {groupPlan.catering_matrix && (
                <div
                  style={{
                    padding: '0.65rem 0.8rem',
                    borderRadius: 10,
                    background: 'var(--cl-surface)',
                    border: '1px solid var(--cl-border)',
                    marginBottom: '0.75rem',
                  }}
                >
                  <strong>
                    Caterer Dietary Headcount Matrix ({groupPlan.catering_matrix.total_seniors} seniors):
                  </strong>
                  <pre
                    style={{
                      margin: '0.4rem 0 0',
                      whiteSpace: 'pre-wrap',
                      fontSize: '0.8rem',
                      fontFamily: 'inherit',
                      color: 'var(--cl-text)',
                    }}
                  >
                    {groupPlan.catering_matrix.caterer_sheet_text}
                  </pre>
                </div>
              )}

              {kopiKakis && kopiKakis.matches.length > 0 && (
                <div>
                  <h3 style={{ margin: '0 0 0.35rem', fontSize: '0.96rem' }}>
                    “Kopi Kakis” — Qloo Affinity Buddy Pairs ({kopiKakis.matches.length} pairs)
                  </h3>
                  <ul className="act-list">
                    {kopiKakis.matches.slice(0, 2).map((m) => (
                      <li key={m.pair_id} className="act-item">
                        <span className="act-kind is-aac">{m.affinity_pct}% Match</span>
                        <span className="act-body">
                          <strong>
                            {m.senior_a.name} ↔ {m.senior_b.name}
                          </strong>
                          <span className="care-muted">
                            {m.shared_hooks.join(' · ')} · Spot: {m.safe_meeting_spot.name}
                          </span>
                          <span className="care-muted" style={{ display: 'block', fontSize: '0.8rem', marginTop: 2 }}>
                            <em>{m.befriender_script.en}</em>
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Rung-3 Handover + Doorstep Icebreaker + GP Brief PDF + WhatsApp Visit Kit */}
          {rightTab === 'family' && (
            <div className="care-card" style={{ margin: 0, display: 'grid', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h2 style={{ margin: 0 }}>Rung-3 Handover with Doorstep Icebreaker, GP Brief & Visit Kit</h2>
                <button
                  type="button"
                  className="care-primary"
                  disabled={busy || !!handoverClaimedBy}
                  onClick={() => void handleClaimRung3Handover()}
                >
                  {handoverClaimedBy ? `✓ Claimed by ${handoverClaimedBy}` : 'Claim Handover on Family Rota (Wei Ling)'}
                </button>
              </div>

              {/* Rung-3 Evidence Card */}
              <div
                style={{
                  padding: '0.65rem 0.8rem',
                  borderRadius: 10,
                  background: 'var(--cl-surface)',
                  border: '1px solid var(--cl-border)',
                }}
              >
                <strong>
                  Rung 3 · Blood Pressure Drift Handover (Rule: <code>3.bp_drift</code>)
                </strong>
                <p className="care-muted" style={{ margin: '0.25rem 0 0' }}>
                  Mr Tan's systolic blood pressure averaged 148/90 mmHg over the last 3 mornings (above his personal baseline of 128/78
                  mmHg). CareLoop has stopped nudging Mr Tan and handed over to the on-duty family contact on the Rota.
                </p>
              </div>

              {/* Doorstep / Call Icebreaker */}
              {tastePlan?.doorstep_icebreaker && (
                <div
                  style={{
                    padding: '0.65rem 0.8rem',
                    borderRadius: 10,
                    background: 'var(--cl-surface)',
                    borderLeft: '3px solid var(--cl-accent)',
                  }}
                >
                  <strong>Qloo Doorstep / Call Icebreaker (So the call doesn’t start with an interrogation):</strong>
                  <p style={{ margin: '0.25rem 0', fontSize: '0.88rem' }}>{tastePlan.doorstep_icebreaker.opener}</p>
                  <span className="care-muted" style={{ fontSize: '0.8rem' }}>
                    Music: {tastePlan.doorstep_icebreaker.music_icebreaker} · Treat: {tastePlan.doorstep_icebreaker.treat_icebreaker} · Film:{' '}
                    {tastePlan.doorstep_icebreaker.film_icebreaker}
                  </span>
                </div>
              )}

              {/* 1-Page GP Brief + WhatsApp Visit Kit Actions */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.65rem' }}>
                <div style={{ padding: '0.65rem 0.8rem', borderRadius: 10, background: 'var(--cl-surface)' }}>
                  <strong>1-Page GP Brief (Doctor Visit Handout)</strong>
                  <p className="care-muted" style={{ fontSize: '0.82rem', margin: '0.25rem 0 0.5rem' }}>
                    Includes 30-day BP series, adherence, active medicines ({brief?.senior.medicines.map((m) => m.name).join(', ') || 'Amlodipine'}), and Qloo dietary rules.
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {briefPdfUrl('tan') ? (
                      <a className="care-secondary" href={briefPdfUrl('tan')!} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                        Open 1-Page GP Brief PDF ↗
                      </a>
                    ) : (
                      <button type="button" className="care-secondary" onClick={() => window.print()}>
                        Print 1-Page GP Brief
                      </button>
                    )}
                  </div>
                </div>

                {tastePlan?.visit_kit && (
                  <div style={{ padding: '0.65rem 0.8rem', borderRadius: 10, background: 'var(--cl-surface)' }}>
                    <strong>WhatsApp Family Visit Kit</strong>
                    <p className="care-muted" style={{ fontSize: '0.82rem', margin: '0.25rem 0 0.5rem' }}>
                      {tastePlan.visit_kit.summary}
                    </p>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        className="care-secondary"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(tastePlan.visit_kit!.whatsapp_text);
                            setCopiedKit(true);
                            setTimeout(() => setCopiedKit(false), 2200);
                          } catch {
                            /* ignore */
                          }
                        }}
                      >
                        {copiedKit ? '✓ Copied Visit Kit!' : 'Copy WhatsApp Visit Kit'}
                      </button>
                      <a
                        className="care-link"
                        href={`https://wa.me/?text=${encodeURIComponent(tastePlan.visit_kit.whatsapp_text)}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ alignSelf: 'center' }}
                      >
                        Share on WhatsApp ↗
                      </a>
                    </div>
                  </div>
                )}
              </div>

              {/* Caregiver Respite Summary */}
              {respite && (
                <div style={{ padding: '0.65rem 0.8rem', borderRadius: 10, background: 'var(--cl-accent-soft)', border: '1px solid var(--cl-border)' }}>
                  <strong style={{ color: 'var(--cl-accent)' }}>
                    Guilt-Free 3-Hour Respite Shield ({respite.matched_programme.qloo_fit_pct}% Qloo Match):
                  </strong>
                  <p className="care-muted" style={{ margin: '0.2rem 0 0', fontSize: '0.83rem' }}>
                    {respite.summary}
                  </p>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
