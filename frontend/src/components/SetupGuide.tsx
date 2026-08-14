'use client';

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { guideUnlocks } from '@/state/reducer';
import type { GuideStatus } from '@/state/types';
import { useApp } from '@/components/App';
import { BankFields, ProjectFields, SourceFields, type SaveHandle } from '@/components/forms';

/**
 * 3-step setup guide (ticket 10). An overlay over any open screen — never a
 * separate screen, no outside-click close, no X close. Exits are Skip all and
 * Finish. Step 2 (Income Source) unlocks once Bank Settings exist; step 3
 * (Project) once at least one Income Source exists. Finish is available from
 * step 2, so a bank-only setup is a valid finish.
 */
export function SetupGuide({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useI18n();
  const { state, dispatch } = useApp();
  const [step, setStep] = useState(0);
  const unlocks = guideUnlocks(state);
  const stepList = [
    { key: 'guide.bank', on: unlocks.bank },
    { key: 'guide.income', on: unlocks.income },
    { key: 'guide.project', on: unlocks.project },
  ];

  useEffect(() => {
    if (open) setStep(0);
  }, [open]);

  if (!open) return null;

  const persist = async (guideStatus: 'done' | 'skipped') => {
    try {
      const res = await api.saveGuideStatus(guideStatus);
      dispatch({ type: 'SET_GUIDE_STATUS', guideStatus: res.guideStatus as GuideStatus });
    } finally {
      onClose();
    }
  };

  return (
    <div className="guide-backdrop">
      <div className="guide" role="dialog" aria-modal="true" aria-label={t('guide.title')}>
        <div className="guide-head">
          <h3>{t('guide.title')}</h3>
          <p className="meta">{t('guide.sub')}</p>
          <div className="guide-steps">
            {stepList.map((s, i) => (
              <button
                key={s.key}
                className={i === step ? 'active' : ''}
                disabled={!s.on}
                onClick={() => s.on && setStep(i)}
              >
                {i + 1}. {t(s.key)}
              </button>
            ))}
          </div>
        </div>

        <div className="guide-body">
          {step === 0 && <BankStep onAdvance={() => setStep(1)} />}
          {step === 1 && <SourceStep onAdvance={() => setStep(2)} />}
          {step === 2 && <ProjectStep />}
        </div>

        <div className="guide-actions">
          <button className="btn ghost" onClick={() => persist('skipped')}>{t('guide.skip')}</button>
          {/* One solid-accent primary per step: the primary action on each step
              lives in its body; Finish is the single primary only on the last step. */}
          {step >= 1 && (
            <button className={step === 2 ? 'btn primary' : 'btn'} onClick={() => persist('done')}>
              {t('guide.finish')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function BankStep({ onAdvance }: { onAdvance: () => void }) {
  const { t } = useI18n();
  const { state } = useApp();
  const ref = useRef<SaveHandle>(null);

  return (
    <>
      <BankFields ref={ref} initial={state.bank} />
      <button className="btn primary" onClick={async () => { if (await ref.current?.save()) onAdvance(); }}>
        {t('guide.add.income')}
      </button>
    </>
  );
}

function SourceStep({ onAdvance }: { onAdvance: () => void }) {
  const { t } = useI18n();
  const ref = useRef<SaveHandle>(null);

  return (
    <>
      <SourceFields ref={ref} />
      <button className="btn primary" onClick={async () => { if (await ref.current?.save()) onAdvance(); }}>
        {t('guide.add.project')}
      </button>
    </>
  );
}

function ProjectStep() {
  const { t } = useI18n();
  const { state } = useApp();
  const ref = useRef<SaveHandle>(null);
  const source = state.sources[0];

  if (!source) {
    return <p className="meta">{t('sources.empty.sub')}</p>;
  }

  return (
    <>
      <ProjectFields ref={ref} source={source} />
      <button className="btn" onClick={() => ref.current?.save()}>{t('guide.add.project')}</button>
    </>
  );
}
