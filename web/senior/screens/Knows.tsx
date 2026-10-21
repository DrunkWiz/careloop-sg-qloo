// "What CareLoop knows about me": plain-language list, every item erasable, plus quick-pick favourite chips.
import { useEffect, useState } from 'react';
import { useT } from '../../shared/i18n';
import { api } from '../api';
import type { KnownFact } from '../types';
import { Screen } from '../ui';

const QUICK_FAVOURITES = [
  'Teresa Teng',
  'P. Ramlee',
  'T.M. Soundararajan',
  'Cliff Richard',
  'Teochew fish porridge',
  'Kopi-O kosong',
  'Mahjong',
  'Gardening',
];

export function Knows({ seniorId, onBack, toast }: { seniorId: string; onBack: () => void; toast: (s: string) => void }) {
  const t = useT();
  const [facts, setFacts] = useState<KnownFact[] | null>(null);
  const [adding, setAdding] = useState<string | null>(null);

  const load = () => {
    api.knows(seniorId).then(setFacts).catch(() => toast(t('common.offline')));
  };

  useEffect(() => {
    load();
  }, [seniorId]); // eslint-disable-line react-hooks/exhaustive-deps

  const erase = async (id: string) => {
    try {
      await api.forget(seniorId, id);
      setFacts((f) => f?.filter((x) => x.id !== id) ?? null);
      toast(t('knows.erased'));
    } catch {
      toast(t('common.offline'));
    }
  };

  const addQuickFavourite = async (seed: string) => {
    if (adding) return;
    setAdding(seed);
    try {
      await api.addTaste(seniorId, seed);
      load();
      toast(t('knows.added'));
    } catch {
      toast(t('common.offline'));
    } finally {
      setAdding(null);
    }
  };

  return (
    <Screen title={t('knows.title')} onBack={onBack}>
      <p className="sa-note">{t('knows.intro')}</p>
      <div className="sa-card" style={{ marginBottom: 14 }}>
        <p className="sa-card-label" style={{ marginBottom: 8 }}>{t('knows.quickAdd')}</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {QUICK_FAVOURITES.map((fav) => (
            <button
              key={fav}
              type="button"
              className="sa-chip"
              disabled={adding === fav}
              onClick={() => addQuickFavourite(fav)}
            >
              + {fav}
            </button>
          ))}
        </div>
      </div>
      {facts?.length === 0 && <p>{t('knows.empty')}</p>}
      <ul className="sa-knows">
        {facts?.map((f) => (
          <li key={f.id}>
            <span>{f.text}</span>
            <button className="sa-erase" onClick={() => erase(f.id)}>{t('knows.erase')}</button>
          </li>
        ))}
      </ul>
    </Screen>
  );
}
