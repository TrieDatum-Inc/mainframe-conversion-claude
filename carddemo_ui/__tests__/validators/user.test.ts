/**
 * Tests for user management validators.
 * Derived from COUSR01C/COUSR02C COBOL business rules.
 */
import { userCreateSchema, userUpdateSchema } from '@/lib/validators/user';

describe('userCreateSchema — COUSR01C validation rules', () => {
  const validUser = {
    user_id: 'TESTUSER',
    password: 'Pass1234',
    user_type: 'U' as const,
  };

  describe('user_id', () => {
    test('rejects empty user_id', () => {
      const result = userCreateSchema.safeParse({ ...validUser, user_id: '' });
      expect(result.success).toBe(false);
    });

    test('rejects user_id exceeding 8 chars (PIC X(08))', () => {
      const result = userCreateSchema.safeParse({ ...validUser, user_id: 'TOOLONGID' });
      expect(result.success).toBe(false);
    });

    test('uppercases user_id (COSGN00C FUNCTION UPPER-CASE)', () => {
      const result = userCreateSchema.safeParse({ ...validUser, user_id: 'testuser' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.user_id).toBe('TESTUSER');
      }
    });

    test('accepts 8-char user_id', () => {
      const result = userCreateSchema.safeParse(validUser);
      expect(result.success).toBe(true);
    });
  });

  describe('password', () => {
    test('rejects empty password', () => {
      const result = userCreateSchema.safeParse({ ...validUser, password: '' });
      expect(result.success).toBe(false);
    });

    test('rejects password exceeding 8 chars (PIC X(08))', () => {
      const result = userCreateSchema.safeParse({ ...validUser, password: 'tolong123' });
      expect(result.success).toBe(false);
    });

    test('accepts valid password', () => {
      const result = userCreateSchema.safeParse(validUser);
      expect(result.success).toBe(true);
    });
  });

  describe('user_type', () => {
    test('accepts A (admin)', () => {
      const result = userCreateSchema.safeParse({ ...validUser, user_type: 'A' });
      expect(result.success).toBe(true);
    });

    test('accepts U (regular)', () => {
      const result = userCreateSchema.safeParse({ ...validUser, user_type: 'U' });
      expect(result.success).toBe(true);
    });

    test('rejects invalid user_type', () => {
      const result = userCreateSchema.safeParse({ ...validUser, user_type: 'X' });
      expect(result.success).toBe(false);
    });

    test('defaults to U when not provided', () => {
      const result = userCreateSchema.safeParse({ user_id: 'TEST', password: 'pass' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.user_type).toBe('U');
      }
    });
  });

  describe('name fields', () => {
    test('accepts optional first_name and last_name', () => {
      const result = userCreateSchema.safeParse({
        ...validUser,
        first_name: 'John',
        last_name: 'Doe',
      });
      expect(result.success).toBe(true);
    });

    test('rejects first_name exceeding 20 chars (PIC X(20))', () => {
      const result = userCreateSchema.safeParse({
        ...validUser,
        first_name: 'A'.repeat(21),
      });
      expect(result.success).toBe(false);
    });
  });
});

describe('userUpdateSchema — COUSR02C validation rules', () => {
  test('accepts empty update (all optional)', () => {
    const result = userUpdateSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  test('accepts partial update with password', () => {
    const result = userUpdateSchema.safeParse({ password: 'NewPass1' });
    expect(result.success).toBe(true);
  });

  test('rejects password update exceeding 8 chars', () => {
    const result = userUpdateSchema.safeParse({ password: 'tolong123' });
    expect(result.success).toBe(false);
  });

  test('accepts user_type change', () => {
    const result = userUpdateSchema.safeParse({ user_type: 'A' });
    expect(result.success).toBe(true);
  });
});
