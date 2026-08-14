import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, within } from '@testing-library/react';
import { LanguageSelector } from '@/components/LanguageSelector';
import { LANGUAGES } from '@/lib/i18n';

afterEach(cleanup);

describe('LanguageSelector (ticket 8)', () => {
  it('shows an SVG flag + code for the current language on the trigger', () => {
    render(<LanguageSelector lang="en" onChange={() => {}} />);
    const trigger = screen.getByRole('button', { name: 'English' });
    expect(trigger).toHaveTextContent('EN');
    expect(trigger.querySelector('svg.langsel-flag')).not.toBeNull();
  });

  it('lists an SVG flag + code for every available language, with name backing aria-label', () => {
    render(<LanguageSelector lang="en" onChange={() => {}} />);
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    const menu = within(screen.getByRole('listbox'));
    for (const l of LANGUAGES) {
      const row = menu.getByRole('button', { name: l.name });
      expect(row).toHaveTextContent(l.code.toUpperCase());
      expect(row.querySelector('svg.langsel-flag')).not.toBeNull();
    }
  });

  it('calls onChange with the picked code and closes', () => {
    const onChange = vi.fn();
    render(<LanguageSelector lang="en" onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    fireEvent.click(within(screen.getByRole('listbox')).getByRole('button', { name: 'Español' }));
    expect(onChange).toHaveBeenCalledWith('es');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });
});
