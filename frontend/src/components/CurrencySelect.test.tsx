import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { CurrencySelect } from '@/components/CurrencySelect';

vi.mock('@/lib/api', () => ({
  api: {
    currencies: vi.fn().mockResolvedValue([
      { code: 'USD', name: 'US Dollar' },
      { code: 'MXN', name: 'Mexican Peso' },
      { code: 'SEK', name: 'Swedish Krona' },
    ]),
  },
}));

afterEach(cleanup);

describe('CurrencySelect (ticket 15)', () => {
  it('shows the current code and name', async () => {
    render(<CurrencySelect value="USD" onChange={() => {}} />);
    const trigger = await screen.findByRole('button', { name: /US Dollar/ });
    expect(trigger).toHaveTextContent('USD');
  });

  it('opens a searchable list and calls onChange with the picked code', async () => {
    const onChange = vi.fn();
    render(<CurrencySelect value="USD" onChange={onChange} />);
    fireEvent.click(await screen.findByRole('button', { name: /US Dollar/ }));
    fireEvent.click(await screen.findByRole('button', { name: /Swedish Krona/ }));
    expect(onChange).toHaveBeenCalledWith('SEK');
  });

  it('filters rows by code when searching', async () => {
    render(<CurrencySelect value="USD" onChange={() => {}} />);
    fireEvent.click(await screen.findByRole('button', { name: /US Dollar/ }));
    const search = screen.getByPlaceholderText('Search…');
    fireEvent.change(search, { target: { value: 'mxn' } });
    expect(screen.getByRole('button', { name: /Mexican Peso/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Swedish Krona/ })).not.toBeInTheDocument();
  });
});
