'use client';

import { useRef } from 'react';
import { useI18n } from '@/lib/i18n';
import { useApp } from '@/components/App';
import { BankFields, type SaveHandle } from '@/components/forms';

export function SettingsScreen() {
  const { t } = useI18n();
  const { state, openGuide } = useApp();
  const bank = state.bank;
  const first = bank === null;
  const ref = useRef<SaveHandle>(null);

  return (
    <>
      <div className="panel">
        <div className="headrow">
          <div>
            <h3>{t('guide.title')}</h3>
            <p className="meta">{t('guide.sub')}</p>
          </div>
          <button className="btn primary" onClick={openGuide}>{t('settings.guide')}</button>
        </div>
      </div>
      <div className="panel">
        <h3>{first ? t('settings.title.new') : t('settings.title')}</h3>
        <p className="meta">{first ? t('settings.sub.new') : t('settings.sub')}</p>
        <BankFields ref={ref} initial={bank} />
        <button className="btn primary" onClick={() => ref.current?.save()}>
          {first ? t('settings.save.cont') : t('settings.save')}
        </button>
      </div>
    </>
  );
}
