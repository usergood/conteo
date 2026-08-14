import type { Language } from '@/lib/i18n';

/*
 * Renders a real flag icon. Emoji flag characters (🇬🇧/🇪🇸) are avoided because
 * Windows shows them as letter pairs ("ES"), not as flags. Adding a language
 * means adding a case here plus an entry in `LANGUAGES`.
 */
export function FlagIcon({ code }: { code: Language }) {
  switch (code) {
    case 'en':
      return (
        <svg className="langsel-flag" viewBox="0 0 60 30" aria-hidden="true">
          <rect width="60" height="30" fill="#012169" />
          <path d="M0 0 L60 30 M60 0 L0 30" stroke="#fff" strokeWidth="6" fill="none" />
          <path d="M0 0 L60 30 M60 0 L0 30" stroke="#C8102E" strokeWidth="3" fill="none" />
          <path d="M30 0 V30 M0 15 H60" stroke="#fff" strokeWidth="10" fill="none" />
          <path d="M30 0 V30 M0 15 H60" stroke="#C8102E" strokeWidth="6" fill="none" />
        </svg>
      );
    case 'es':
      return (
        <svg className="langsel-flag" viewBox="0 0 60 30" aria-hidden="true">
          <rect width="60" height="30" fill="#F1BF00" />
          <rect y="0" width="60" height="7.5" fill="#AA151B" />
          <rect y="22.5" width="60" height="7.5" fill="#AA151B" />
        </svg>
      );
  }
}
