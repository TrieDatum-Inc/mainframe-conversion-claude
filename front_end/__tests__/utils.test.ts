/**
 * Tests for utility functions.
 * Maps COBOL formatting operations to TypeScript equivalents.
 */

import {
  formatAuthDate,
  formatAuthTime,
  formatCurrency,
  getApprovalConfig,
  getMatchStatusLabel,
} from '@/lib/utils';

describe('formatAuthDate', () => {
  it('formats ISO date to MM/DD/YY (COPAUS0C WS-AUTH-DATE PDATEnn format)', () => {
    // PA-AUTH-ORIG-DATE YYMMDD → MM/DD/YY display
    const result = formatAuthDate('2026-03-15');
    expect(result).toBe('03/15/26');
  });

  it('returns empty string for empty input', () => {
    expect(formatAuthDate('')).toBe('');
  });
});

describe('formatAuthTime', () => {
  it('formats HH:MM:SS time string (COPAUS0C WS-AUTH-TIME PTIMEnn format)', () => {
    // PA-AUTH-ORIG-TIME HHMMSS → HH:MM:SS display
    const result = formatAuthTime('10:25:33');
    expect(result).toBe('10:25:33');
  });

  it('returns empty string for empty input', () => {
    expect(formatAuthTime('')).toBe('');
  });
});

describe('formatCurrency', () => {
  it('formats positive amount with dollar sign', () => {
    // Replaces: COBOL PIC -zzzzzzz9.99 (WS-AUTH-AMT)
    const result = formatCurrency(125.50);
    expect(result).toContain('125.50');
  });

  it('formats zero amount', () => {
    expect(formatCurrency(0)).toContain('0.00');
  });

  it('handles string input', () => {
    const result = formatCurrency('1500.00');
    expect(result).toContain('1,500.00');
  });
});

describe('getApprovalConfig', () => {
  it("returns green styling for 'A' (COPAUS0C DFHGREEN for resp='00')", () => {
    const config = getApprovalConfig('A');
    expect(config.label).toBe('Approved');
    expect(config.className).toContain('green');
  });

  it("returns red styling for 'D' (COPAUS0C DFHRED for resp!='00')", () => {
    const config = getApprovalConfig('D');
    expect(config.label).toBe('Declined');
    expect(config.className).toContain('red');
  });
});

describe('getMatchStatusLabel', () => {
  it("maps 'P' to 'Pending' (PA-MATCH-PENDING from CIPAUDTY 88-level)", () => {
    expect(getMatchStatusLabel('P')).toBe('Pending');
  });

  it("maps 'D' to 'Declined' (PA-MATCH-DIRECT)", () => {
    expect(getMatchStatusLabel('D')).toBe('Declined');
  });

  it("maps 'E' to 'Expired' (PA-MATCH-EXACT)", () => {
    expect(getMatchStatusLabel('E')).toBe('Expired');
  });

  it("maps 'M' to 'Matched' (PA-MATCH-MANUAL)", () => {
    expect(getMatchStatusLabel('M')).toBe('Matched');
  });

  it('returns original code for unknown status', () => {
    expect(getMatchStatusLabel('X')).toBe('X');
  });
});
