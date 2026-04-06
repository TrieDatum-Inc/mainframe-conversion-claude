/**
 * Tests for FraudStatusBadge component.
 * Maps BMS AUTHFRDO field display logic from COPAUS1C/COPAU01.
 */

import { render, screen } from '@testing-library/react';
import { FraudStatusBadge } from '@/components/authorizations/FraudStatusBadge';

describe('FraudStatusBadge', () => {
  it('shows "No Fraud" for N status (no AUTHFRDO on original screen)', () => {
    render(<FraudStatusBadge status="N" />);
    expect(screen.getByText('No Fraud')).toBeInTheDocument();
  });

  it('shows "Fraud Confirmed" for F status (AUTHFRDO = FRAUD in RED)', () => {
    render(<FraudStatusBadge status="F" />);
    expect(screen.getByText('Fraud Confirmed')).toBeInTheDocument();
  });

  it('shows "Fraud Removed" for R status (AUTHFRDO = REMOVED in RED)', () => {
    render(<FraudStatusBadge status="R" />);
    expect(screen.getByText('Fraud Removed')).toBeInTheDocument();
  });

  it('renders compact version with status code', () => {
    render(<FraudStatusBadge status="F" compact />);
    expect(screen.getByText('F')).toBeInTheDocument();
  });

  it('applies red styling for fraud confirmed (BMS COLOR=RED equivalent)', () => {
    const { container } = render(<FraudStatusBadge status="F" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('red');
  });

  it('applies yellow styling for fraud removed', () => {
    const { container } = render(<FraudStatusBadge status="R" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('yellow');
  });

  it('applies green styling for no fraud', () => {
    const { container } = render(<FraudStatusBadge status="N" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('green');
  });
});
