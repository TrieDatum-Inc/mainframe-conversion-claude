/**
 * Tests for StatusBadge component.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { StatusBadge, AuthBadge } from '@/components/ui/StatusBadge';

describe('StatusBadge', () => {
  test('shows Active for Y', () => {
    render(<StatusBadge status="Y" />);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  test('shows Inactive for N', () => {
    render(<StatusBadge status="N" />);
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  test('shows Unknown for null', () => {
    render(<StatusBadge status={null} />);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  test('uses custom labels', () => {
    render(<StatusBadge status="Y" activeLabel="Open" inactiveLabel="Closed" />);
    expect(screen.getByText('Open')).toBeInTheDocument();
  });

  test('applies green color for Y', () => {
    render(<StatusBadge status="Y" />);
    const badge = screen.getByText('Active');
    expect(badge.className).toContain('text-green-700');
  });

  test('applies red color for N', () => {
    render(<StatusBadge status="N" />);
    const badge = screen.getByText('Inactive');
    expect(badge.className).toContain('text-red-700');
  });
});

describe('AuthBadge', () => {
  test('shows Approved when isApproved=true', () => {
    render(<AuthBadge isApproved={true} />);
    expect(screen.getByText('Approved')).toBeInTheDocument();
  });

  test('shows Declined when isApproved=false', () => {
    render(<AuthBadge isApproved={false} />);
    expect(screen.getByText('Declined')).toBeInTheDocument();
  });
});
