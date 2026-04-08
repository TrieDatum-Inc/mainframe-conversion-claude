/**
 * Tests for card validators.
 * Derived from COCRDUPC COBOL business rules.
 */
import { cardUpdateSchema } from '@/lib/validators/card';

describe('cardUpdateSchema — COCRDUPC validation rules', () => {
  test('accepts empty update (all optional)', () => {
    const result = cardUpdateSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  describe('active_status', () => {
    test('accepts Y (active)', () => {
      const result = cardUpdateSchema.safeParse({ active_status: 'Y' });
      expect(result.success).toBe(true);
    });

    test('accepts N (inactive)', () => {
      const result = cardUpdateSchema.safeParse({ active_status: 'N' });
      expect(result.success).toBe(true);
    });

    test('rejects invalid active_status', () => {
      const result = cardUpdateSchema.safeParse({ active_status: 'X' });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toContain("'Y' (active) or 'N' (inactive)");
      }
    });
  });

  describe('embossed_name', () => {
    test('accepts name within 50 chars (CARD-EMBOSSED-NAME PIC X(50))', () => {
      const result = cardUpdateSchema.safeParse({ embossed_name: 'JOHN DOE' });
      expect(result.success).toBe(true);
    });

    test('rejects name exceeding 50 chars', () => {
      const result = cardUpdateSchema.safeParse({ embossed_name: 'A'.repeat(51) });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toContain('50 characters');
      }
    });

    test('accepts exactly 50 chars', () => {
      const result = cardUpdateSchema.safeParse({ embossed_name: 'A'.repeat(50) });
      expect(result.success).toBe(true);
    });
  });

  test('accepts both fields together', () => {
    const result = cardUpdateSchema.safeParse({
      embossed_name: 'JANE DOE',
      active_status: 'Y',
    });
    expect(result.success).toBe(true);
  });
});
