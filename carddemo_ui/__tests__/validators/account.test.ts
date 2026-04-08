/**
 * Tests for account validators.
 * Derived from COACTUPC and COBIL00C COBOL business rules.
 *
 * Coverage target: 100%
 */
import { accountUpdateSchema, billPaymentSchema } from '@/lib/validators/account';

describe('accountUpdateSchema — COACTUPC validation rules', () => {
  describe('active_status', () => {
    test('accepts Y', () => {
      const result = accountUpdateSchema.safeParse({ active_status: 'Y' });
      expect(result.success).toBe(true);
    });

    test('accepts N', () => {
      const result = accountUpdateSchema.safeParse({ active_status: 'N' });
      expect(result.success).toBe(true);
    });

    test('rejects invalid values (only Y or N allowed)', () => {
      const result = accountUpdateSchema.safeParse({ active_status: 'X' });
      expect(result.success).toBe(false);
    });
  });

  describe('credit_limit', () => {
    test('accepts zero credit_limit', () => {
      const result = accountUpdateSchema.safeParse({ credit_limit: '0' });
      expect(result.success).toBe(true);
    });

    test('accepts positive decimal', () => {
      const result = accountUpdateSchema.safeParse({ credit_limit: '5000.00' });
      expect(result.success).toBe(true);
    });

    test('rejects negative credit_limit', () => {
      const result = accountUpdateSchema.safeParse({ credit_limit: '-100.00' });
      expect(result.success).toBe(false);
    });

    test('rejects non-numeric value', () => {
      const result = accountUpdateSchema.safeParse({ credit_limit: 'abc' });
      expect(result.success).toBe(false);
    });
  });

  describe('addr_zip — CSLKPCDY validation', () => {
    test('accepts 5-digit ZIP', () => {
      const result = accountUpdateSchema.safeParse({ addr_zip: '12345' });
      expect(result.success).toBe(true);
    });

    test('accepts ZIP+4 format', () => {
      const result = accountUpdateSchema.safeParse({ addr_zip: '12345-6789' });
      expect(result.success).toBe(true);
    });

    test('rejects invalid ZIP format', () => {
      const result = accountUpdateSchema.safeParse({ addr_zip: '1234' });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toContain('ZIP code must be 5 digits');
      }
    });

    test('rejects non-numeric ZIP', () => {
      const result = accountUpdateSchema.safeParse({ addr_zip: 'ABCDE' });
      expect(result.success).toBe(false);
    });

    test('rejects partial ZIP+4', () => {
      const result = accountUpdateSchema.safeParse({ addr_zip: '12345-678' });
      expect(result.success).toBe(false);
    });

    test('accepts empty string for ZIP', () => {
      const result = accountUpdateSchema.safeParse({ addr_zip: '' });
      expect(result.success).toBe(true);
    });
  });

  describe('date fields', () => {
    test('accepts valid ISO date', () => {
      const result = accountUpdateSchema.safeParse({ open_date: '2020-01-15' });
      expect(result.success).toBe(true);
    });

    test('rejects invalid date format', () => {
      const result = accountUpdateSchema.safeParse({ open_date: '01/15/2020' });
      expect(result.success).toBe(false);
    });

    test('accepts empty string for date', () => {
      const result = accountUpdateSchema.safeParse({ open_date: '' });
      expect(result.success).toBe(true);
    });
  });

  describe('empty update', () => {
    test('accepts empty object (all fields optional)', () => {
      const result = accountUpdateSchema.safeParse({});
      expect(result.success).toBe(true);
    });
  });
});

describe('billPaymentSchema — COBIL00C validation rules', () => {
  test('rejects empty payment amount', () => {
    const result = billPaymentSchema.safeParse({ payment_amount: '' });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.errors[0].message).toBe('Payment amount is required');
    }
  });

  test('rejects zero payment amount (must be positive)', () => {
    const result = billPaymentSchema.safeParse({ payment_amount: '0' });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.errors[0].message).toContain('greater than zero');
    }
  });

  test('rejects negative payment amount', () => {
    const result = billPaymentSchema.safeParse({ payment_amount: '-50.00' });
    expect(result.success).toBe(false);
  });

  test('accepts valid positive payment', () => {
    const result = billPaymentSchema.safeParse({ payment_amount: '150.00' });
    expect(result.success).toBe(true);
  });

  test('accepts payment with description', () => {
    const result = billPaymentSchema.safeParse({
      payment_amount: '200.00',
      description: 'Monthly payment',
    });
    expect(result.success).toBe(true);
  });

  test('rejects description exceeding 100 chars', () => {
    const result = billPaymentSchema.safeParse({
      payment_amount: '100.00',
      description: 'a'.repeat(101),
    });
    expect(result.success).toBe(false);
  });
});
