import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { InstallButton } from '@/components/InstallButton';

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('InstallButton (PWA install)', () => {
  it('shows nothing when not installable and not iOS', () => {
    render(<InstallButton />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('captures beforeinstallprompt and triggers the install prompt', async () => {
    const prompt = vi.fn().mockResolvedValue(undefined);
    const userChoice = Promise.resolve({ outcome: 'accepted' as const });
    const event = new Event('beforeinstallprompt');
    Object.defineProperty(event, 'prompt', { value: prompt });
    Object.defineProperty(event, 'userChoice', { value: userChoice });

    render(<InstallButton />);
    window.dispatchEvent(event);

    const btn = await screen.findByRole('button', { name: /install/i });
    fireEvent.click(btn);
    expect(prompt).toHaveBeenCalled();
    await waitFor(() => {
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });
  });
});
