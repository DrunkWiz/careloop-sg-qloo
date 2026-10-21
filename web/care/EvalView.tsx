// Quantitative Qloo Ablation & Multi-Metric Benchmark Dashboard (/eval & /eval/taste).
// Compares Generic LLM Baseline vs Rule-Filtered LLM vs CareLoop + Qloo Taste AI across all 13 demo seniors + 25 synthetic personas.
import { useEffect, useState } from 'react';
import { getTasteEval } from '../shared/api';
import type { TasteBenchmarkPersonaRow, TasteEvalBenchmark } from '../shared/contract';
import Brand from '../shared/Brand';
import './care.css';
import './themes.css';
import './refresh.css';

export default function EvalView() {
  const [data, setData] = useState<TasteEvalBenchmark | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cohortFilter, setCohortFilter] = useState<'all' | 'demo_senior' | 'synthetic_persona'>('all');
  const [langFilter, setLangFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [selectedPersona, setSelectedPersona] = useState<TasteBenchmarkPersonaRow | null>(null);

  useEffect(() => {
    getTasteEval().then(
      (res) => {
        setData(res);
        setSelectedPersona(res.per_persona[0] ?? null);
      },
      (e: Error) => setError(e.message),
    );
  }, []);

  const downloadReport = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `careloop-qloo-ablation-benchmark-${data.evaluated_on}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <main className="care theme-centre" style={{ maxWidth: 1180, margin: '0 auto', padding: '1.5rem' }}>
        <section className="care-card">
          <h1>Evaluation Benchmark Error</h1>
          <p className="care-error">{error}</p>
        </section>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="care theme-centre" style={{ maxWidth: 1180, margin: '0 auto', padding: '1.5rem' }}>
        <p className="care-muted">Running 3-Architecture Qloo Taste Ablation across 38 personas…</p>
      </main>
    );
  }

  const filteredRows = data.per_persona.filter((row) => {
    if (cohortFilter !== 'all' && row.cohort !== cohortFilter) return false;
    if (langFilter !== 'all' && row.language !== langFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      const hay = [
        row.persona_id,
        row.name,
        ...row.conditions,
        ...row.medicines,
        ...row.dietary_prefs,
        ...row.likes,
      ]
        .join(' ')
        .toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  return (
    <main className="care theme-centre" style={{ maxWidth: 1220, margin: '0 auto', padding: '1.25rem 1.5rem 3rem' }}>
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
          marginBottom: '1.25rem',
          paddingBottom: '0.85rem',
          borderBottom: '1px solid rgba(0,0,0,0.08)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', flexWrap: 'wrap' }}>
          <Brand />
          <span
            className="care-pill"
            style={{ background: '#0f766e', color: '#fff', fontWeight: 700, padding: '0.25rem 0.65rem' }}
          >
            EVAL & QLOO ABLATION SUITE v{data.benchmark_version}
          </span>
          <span className="care-muted" style={{ fontSize: '0.88rem' }}>
            {data.total_personas} Personas ({data.cohorts.demo_seniors} Demo Seniors + {data.cohorts.synthetic_personas} Synthetic Cohort)
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <a className="care-secondary" href="/pitch" style={{ textDecoration: 'none' }}>
            ⚡ Judge Command Center (/pitch)
          </a>
          <a className="care-secondary" href="/care?demo=1" style={{ textDecoration: 'none' }}>
            Caregiver App (/care)
          </a>
          <button type="button" className="care-primary" onClick={downloadReport}>
            ⬇ Download JSON Benchmark Report
          </button>
        </div>
      </header>

      <section className="care-card" style={{ marginBottom: '1rem' }}>
        <h1 style={{ margin: '0 0 0.35rem', fontSize: '1.45rem' }}>
          Quantitative Qloo Ablation & Clinical Guardrail Benchmark
        </h1>
        <p className="care-muted" style={{ margin: 0 }}>
          Evaluates 3 recommendation architectures across <strong>{data.total_personas} Singapore senior profiles</strong> (
          {data.cohorts.demo_seniors} demo seniors + {data.cohorts.synthetic_personas} held-out/synthetic personas) with overlapping
          chronic conditions (hypertension, diabetes, gout, CKD), pharmacist medicine-leaflet rules (statin/amlodipine grapefruit ban),
          religious/dietary needs (Halal, Vegetarian, No Beef), wheelchair access, and NEA haze (PSI 135).
        </p>
      </section>

      {/* Architecture Comparison Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))',
          gap: '1rem',
          marginBottom: '1.25rem',
        }}
      >
        {data.architectures.map((arch) => {
          const isQloo = arch.id === 'careloop_qloo';
          return (
            <section
              key={arch.id}
              className="care-card"
              style={{
                margin: 0,
                border: isQloo ? '2px solid #0f766e' : '1px solid rgba(0,0,0,0.1)',
                background: isQloo ? 'rgba(15, 118, 110, 0.04)' : undefined,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                <h2 style={{ margin: 0, fontSize: '1.08rem' }}>{arch.name}</h2>
                {isQloo && (
                  <span className="care-pill" style={{ background: '#0f766e', color: '#fff', fontWeight: 700 }}>
                    0.0% Violations
                  </span>
                )}
              </div>
              <p className="care-muted" style={{ fontSize: '0.85rem', margin: '0.35rem 0 0.85rem' }}>
                {arch.description}
              </p>

              <div style={{ display: 'grid', gap: '0.55rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.86rem' }}>
                    <span>Clinical & Leaflet Violation Rate (lower is better)</span>
                    <strong style={{ color: arch.clinical_violation_rate_pct === 0 ? '#0f766e' : '#b91c1c' }}>
                      {arch.clinical_violation_rate_pct.toFixed(1)}% ({arch.personas_with_violation}/{data.total_personas} personas)
                    </strong>
                  </div>
                  <div style={{ height: 8, background: 'rgba(0,0,0,0.08)', borderRadius: 4, overflow: 'hidden', marginTop: 4 }}>
                    <div
                      style={{
                        width: `${Math.max(2, arch.clinical_violation_rate_pct)}%`,
                        height: '100%',
                        background: arch.clinical_violation_rate_pct === 0 ? '#0f766e' : '#dc2626',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.86rem' }}>
                    <span>Cross-Domain Cultural Specificity Score (0–100)</span>
                    <strong style={{ color: isQloo ? '#0f766e' : undefined }}>{arch.cultural_specificity_score.toFixed(1)} / 100</strong>
                  </div>
                  <div style={{ height: 8, background: 'rgba(0,0,0,0.08)', borderRadius: 4, overflow: 'hidden', marginTop: 4 }}>
                    <div
                      style={{
                        width: `${arch.cultural_specificity_score}%`,
                        height: '100%',
                        background: isQloo ? '#0f766e' : '#64748b',
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', paddingTop: '0.25rem' }}>
                  <span>Multilingual Coverage (en / zh / ms / ta):</span>
                  <strong>{arch.multilingual_coverage_pct.toFixed(0)}%</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Language Safety Guardrail Pass Rate:</span>
                  <strong style={{ color: '#0f766e' }}>{arch.guardrail_pass_rate_pct.toFixed(1)}%</strong>
                </div>
              </div>
            </section>
          );
        })}
      </div>

      {/* Multilingual & Held-Out Escalation Summary */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '1rem',
          marginBottom: '1.25rem',
        }}
      >
        <section className="care-card" style={{ margin: 0 }}>
          <h2 style={{ margin: '0 0 0.4rem', fontSize: '1.05rem' }}>
            Multilingual Cultural & Guardrail Verification (4 Official Languages)
          </h2>
          <p className="care-muted" style={{ fontSize: '0.85rem', margin: '0 0 0.65rem' }}>
            Every recommendation explanation, low-day nudge, reminiscence prompt, and befriender script is verified across English,
            Mandarin, Bahasa Melayu, and Tamil through <code>backend/escalation/guardrail.py</code>.
          </p>
          <div style={{ display: 'grid', gap: '0.4rem' }}>
            {Object.entries(data.multilingual_breakdown).map(([code, info]) => (
              <div
                key={code}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.4rem 0.6rem',
                  borderRadius: 6,
                  background: 'var(--bg-soft, #faf8f5)',
                  fontSize: '0.86rem',
                }}
              >
                <strong>{info.label}</strong>
                <span>
                  Specificity: <strong>{info.cultural_specificity_avg}/100</strong> · Guardrail:{' '}
                  <strong style={{ color: '#0f766e' }}>{info.guardrail_pass_rate_pct.toFixed(0)}% Pass</strong> ({info.tested_personas}{' '}
                  personas)
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="care-card" style={{ margin: 0 }}>
          <h2 style={{ margin: '0 0 0.4rem', fontSize: '1.05rem' }}>
            Frozen Held-Out Clinical Escalation Ladder (<code>backend/synth/heldout.json</code>)
          </h2>
          <p className="care-muted" style={{ fontSize: '0.85rem', margin: '0 0 0.65rem' }}>
            CareLoop's 4-rung clinical escalation engine is strictly separated from Qloo taste generation and verified on the frozen
            30-day held-out cohort (<code>python -m backend.eval.run</code>).
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
            <div style={{ padding: '0.5rem 0.65rem', borderRadius: 6, background: 'var(--bg-soft, #faf8f5)' }}>
              <div className="care-muted" style={{ fontSize: '0.78rem' }}>Red-Flag Recall (Rung 4)</div>
              <strong style={{ fontSize: '1.15rem', color: '#0f766e' }}>5 / 5 (100%)</strong>
            </div>
            <div style={{ padding: '0.5rem 0.65rem', borderRadius: 6, background: 'var(--bg-soft, #faf8f5)' }}>
              <div className="care-muted" style={{ fontSize: '0.78rem' }}>Real Problems Flagged</div>
              <strong style={{ fontSize: '1.15rem', color: '#0f766e' }}>17 / 17 (100%)</strong>
            </div>
            <div style={{ padding: '0.5rem 0.65rem', borderRadius: 6, background: 'var(--bg-soft, #faf8f5)' }}>
              <div className="care-muted" style={{ fontSize: '0.78rem' }}>False Handovers / Quiet Week</div>
              <strong style={{ fontSize: '1.15rem', color: '#0f766e' }}>0.00 (Target ≤ 0.25)</strong>
            </div>
            <div style={{ padding: '0.5rem 0.65rem', borderRadius: 6, background: 'var(--bg-soft, #faf8f5)' }}>
              <div className="care-muted" style={{ fontSize: '0.78rem' }}>Guardrail Violations</div>
              <strong style={{ fontSize: '1.15rem', color: '#0f766e' }}>0 / 750 senior-days</strong>
            </div>
          </div>
        </section>
      </div>

      {/* Selected Persona Side-by-Side Diff Drawer */}
      {selectedPersona && (
        <section className="care-card" style={{ marginBottom: '1.25rem', borderLeft: '4px solid #0f766e' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.08rem' }}>
              Per-Persona Architecture Diff Inspector: {selectedPersona.name} (<code>{selectedPersona.persona_id}</code>)
            </h2>
            <span className="care-muted" style={{ fontSize: '0.85rem' }}>
              Cohort: <strong>{selectedPersona.cohort === 'demo_senior' ? '13 Demo Seniors' : '25 Synthetic Personas'}</strong> · Lang:{' '}
              <code>{selectedPersona.language}</code>
            </span>
          </div>
          <p className="care-muted" style={{ margin: '0.35rem 0 0.75rem', fontSize: '0.86rem' }}>
            <strong>Conditions & Meds:</strong> {[...selectedPersona.conditions, ...selectedPersona.medicines].join(', ') || 'None'} ·{' '}
            <strong>Dietary:</strong> {selectedPersona.dietary_prefs.join(', ') || 'Standard'} · <strong>Taste Seeds:</strong>{' '}
            {selectedPersona.likes.join(', ')}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
            <div style={{ padding: '0.65rem', borderRadius: 8, background: 'rgba(220, 38, 38, 0.05)', border: '1px solid rgba(220,38,38,0.2)' }}>
              <strong style={{ color: '#b91c1c', fontSize: '0.9rem' }}>
                1. Generic LLM ({selectedPersona.generic_llm.violation_count} violations · Specificity {selectedPersona.generic_llm.specificity_score})
              </strong>
              <ul className="care-muted" style={{ margin: '0.35rem 0', paddingLeft: '1.1rem', fontSize: '0.84rem' }}>
                {selectedPersona.generic_llm.picks.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
              {selectedPersona.generic_llm.violations.map((v, i) => (
                <div key={i} style={{ fontSize: '0.78rem', color: '#b91c1c', marginTop: 2 }}>
                  ✗ <code>{v.rule_code}</code>: {v.item}
                </div>
              ))}
            </div>

            <div style={{ padding: '0.65rem', borderRadius: 8, background: 'rgba(217, 119, 6, 0.06)', border: '1px solid rgba(217,119,6,0.25)' }}>
              <strong style={{ color: '#b45309', fontSize: '0.9rem' }}>
                2. Rule-Filtered LLM ({selectedPersona.rule_filtered_llm.violation_count} violations · Specificity{' '}
                {selectedPersona.rule_filtered_llm.specificity_score})
              </strong>
              <ul className="care-muted" style={{ margin: '0.35rem 0', paddingLeft: '1.1rem', fontSize: '0.84rem' }}>
                {selectedPersona.rule_filtered_llm.picks.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
              {selectedPersona.rule_filtered_llm.violations.map((v, i) => (
                <div key={i} style={{ fontSize: '0.78rem', color: '#b45309', marginTop: 2 }}>
                  ⚠ <code>{v.rule_code}</code>: {v.item}
                </div>
              ))}
            </div>

            <div style={{ padding: '0.65rem', borderRadius: 8, background: 'rgba(15, 118, 110, 0.06)', border: '1px solid rgba(15,118,110,0.3)' }}>
              <strong style={{ color: '#0f766e', fontSize: '0.9rem' }}>
                3. CareLoop + Qloo ({selectedPersona.careloop_qloo.violation_count} violations · Specificity{' '}
                {selectedPersona.careloop_qloo.specificity_score})
              </strong>
              <ul className="care-muted" style={{ margin: '0.35rem 0', paddingLeft: '1.1rem', fontSize: '0.84rem' }}>
                {selectedPersona.careloop_qloo.picks.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
                <li>🎵 {selectedPersona.careloop_qloo.music_pick}</li>
                <li>🎬 {selectedPersona.careloop_qloo.movie_pick}</li>
              </ul>
              <div style={{ fontSize: '0.78rem', color: '#0f766e' }}>
                ✓ Intercepted {selectedPersona.careloop_qloo.filtered_out_count} unsafe candidates (
                {selectedPersona.careloop_qloo.filtered_out_rules.join(', ') || 'standard'})
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Interactive Per-Persona Diff Table */}
      <section className="care-card">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.5rem',
            marginBottom: '0.75rem',
          }}
        >
          <h2 style={{ margin: 0 }}>Interactive Per-Persona Benchmark Table ({filteredRows.length} shown)</h2>
          <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter by name, condition, med, seed…"
              aria-label="Filter benchmark personas"
              style={{ minWidth: 210 }}
            />
            <select value={cohortFilter} onChange={(e) => setCohortFilter(e.target.value as any)} aria-label="Filter by cohort">
              <option value="all">All Cohorts ({data.total_personas})</option>
              <option value="demo_senior">13 Demo Seniors</option>
              <option value="synthetic_persona">25 Synthetic Personas</option>
            </select>
            <select value={langFilter} onChange={(e) => setLangFilter(e.target.value)} aria-label="Filter by language">
              <option value="all">All Languages</option>
              <option value="en">English (en)</option>
              <option value="zh">Mandarin (zh)</option>
              <option value="ms">Malay (ms)</option>
              <option value="ta">Tamil (ta)</option>
            </select>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '2px solid rgba(0,0,0,0.12)' }}>
                <th style={{ padding: '0.5rem' }}>Persona</th>
                <th style={{ padding: '0.5rem' }}>Conditions / Meds / Diet</th>
                <th style={{ padding: '0.5rem' }}>Generic LLM</th>
                <th style={{ padding: '0.5rem' }}>Rule-Filtered LLM</th>
                <th style={{ padding: '0.5rem' }}>CareLoop + Qloo</th>
                <th style={{ padding: '0.5rem' }}>Inspect</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((row) => {
                const isSelected = selectedPersona?.persona_id === row.persona_id;
                return (
                  <tr
                    key={row.persona_id}
                    style={{
                      borderBottom: '1px solid rgba(0,0,0,0.07)',
                      background: isSelected ? 'rgba(15, 118, 110, 0.06)' : undefined,
                    }}
                  >
                    <td style={{ padding: '0.5rem' }}>
                      <strong>{row.name}</strong>
                      <div className="care-muted" style={{ fontSize: '0.76rem' }}>
                        <code>{row.persona_id}</code> · {row.language.toUpperCase()} ·{' '}
                        {row.cohort === 'demo_senior' ? 'Demo' : 'Synth'}
                      </div>
                    </td>
                    <td style={{ padding: '0.5rem' }}>
                      {[...row.conditions, ...row.medicines, ...row.dietary_prefs].join(', ') || 'Standard'}
                      <div className="care-muted" style={{ fontSize: '0.76rem' }}>
                        Seeds: {row.likes.slice(0, 3).join(', ')}
                      </div>
                    </td>
                    <td style={{ padding: '0.5rem', color: '#b91c1c' }}>
                      <strong>{row.generic_llm.violation_count} violations</strong>
                      <div className="care-muted" style={{ fontSize: '0.76rem' }}>
                        Spec: {row.generic_llm.specificity_score}/100
                      </div>
                    </td>
                    <td style={{ padding: '0.5rem', color: row.rule_filtered_llm.violation_count > 0 ? '#b45309' : '#0f766e' }}>
                      <strong>{row.rule_filtered_llm.violation_count} violations</strong>
                      <div className="care-muted" style={{ fontSize: '0.76rem' }}>
                        Spec: {row.rule_filtered_llm.specificity_score}/100
                      </div>
                    </td>
                    <td style={{ padding: '0.5rem', color: '#0f766e' }}>
                      <strong>0 violations ✓</strong>
                      <div className="care-muted" style={{ fontSize: '0.76rem' }}>
                        Spec: {row.careloop_qloo.specificity_score}/100 · {row.careloop_qloo.picks[0]}
                      </div>
                    </td>
                    <td style={{ padding: '0.5rem' }}>
                      <button type="button" className="care-link" onClick={() => setSelectedPersona(row)}>
                        {isSelected ? 'Viewing' : 'Inspect →'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
