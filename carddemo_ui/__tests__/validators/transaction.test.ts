/**
 * Tests for transaction validators.
 * Derived from COTRN02C COBOL business rules.
 */
import { transactionCreateSchema } from '@/lib/validators/transaction';

describe('transactionCreateSchema — COTRN02C validation rules', () => {
  const validBase = {
    amount: '150.00',
    card_num: '4111111111111111',
    type_cd: '01',
  };

  describe('amount', () => {
    test('rejects zero amount (COTRN02C: amount must not be zero)', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, amount: '0' });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('Transaction amount must not be zero');
      }
    });

    test('rejects empty amount', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, amount: '' });
      expect(result.success).toBe(false);
    });

    test('accepts positive amount', () => {
      const result = transactionCreateSchema.safeParse(validBase);
      expect(result.success).toBe(true);
    });

    test('accepts negative amount (credits)', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, amount: '-50.00' });
      expect(result.success).toBe(true);
    });

    test('rejects non-numeric amount', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, amount: 'abc' });
      expect(result.success).toBe(false);
    });
  });

  describe('card_num', () => {
    test('rejects card_num shorter than 16 digits (PIC X(16))', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, card_num: '411111111111' });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toContain('16 digits');
      }
    });

    test('rejects card_num longer than 16 digits', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, card_num: '41111111111111111' });
      expect(result.success).toBe(false);
    });

    test('rejects non-numeric card_num', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, card_num: '411111111111ABCD' });
      expect(result.success).toBe(false);
    });

    test('accepts valid 16-digit card_num', () => {
      const result = transactionCreateSchema.safeParse(validBase);
      expect(result.success).toBe(true);
    });
  });

  describe('type_cd', () => {
    test('rejects empty type_cd', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, type_cd: '' });
      expect(result.success).toBe(false);
    });

    test('rejects type_cd exceeding 2 chars', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, type_cd: 'ABC' });
      expect(result.success).toBe(false);
    });

    test('accepts 1-char type_cd', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, type_cd: '1' });
      expect(result.success).toBe(true);
    });

    test('accepts 2-char type_cd', () => {
      const result = transactionCreateSchema.safeParse({ ...validBase, type_cd: '02' });
      expect(result.success).toBe(true);
    });
  });

  describe('optional fields', () => {
    test('accepts transaction with all optional fields', () => {
      const result = transactionCreateSchema.safeParse({
        ...validBase,
        cat_cd: 5411,
        source: 'POS TERM',
        description: 'WALMART PURCHASE',
        merchant_id: 999999999,
        merchant_name: 'WALMART',
        merchant_city: 'BENTONVILLE',
        merchant_zip: '72716',
      });
      expect(result.success).toBe(true);
    });
  });
});
