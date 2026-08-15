'use client';

import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';

/**
 * PWA install button (ticket: installable web app). On Android/Chrome the
 * `beforeinstallprompt` event surfaces when the app is installable; capturing
 * it lets us show a button that triggers the install prompt. On iOS Safari the
 * event never fires, so we show the "Add to Home Screen" hint instead.
 */
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function InstallButton({ compact = false }: { compact?: boolean }) {
  const { t } = useI18n();
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    window.addEventListener('beforeinstallprompt', onPrompt);
    const ua = navigator.userAgent;
    setIsIOS(/iphone|ipad|ipod/i.test(ua) && !('MSStream' in window));
    return () => window.removeEventListener('beforeinstallprompt', onPrompt);
  }, []);

  if (!deferred && !isIOS) return null;

  const install = async () => {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  };

  return deferred ? (
    <button className="iconbtn" onClick={install}>
      {t('pwa.install')}
    </button>
  ) : isIOS ? (
    <span className="install-hint" title={t('pwa.ios.hint')}>
      {t('pwa.ios')}
    </span>
  ) : null;
}
