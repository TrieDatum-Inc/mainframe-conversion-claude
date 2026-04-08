/**
 * Tests for auth validators.
 * Derived from COSGN00C COBOL business rules.
 *
 * Coverage target: 100%
 */
import { loginSchema } from '@/lib/validators/auth';

describe('loginSchema — COSGN00C validation rules', () => {
  describe('user_id', () => {
    test('rejects empty user_id (WHEN USERIDI = SPACES)', () => {
      const result = loginSchema.safeParse({ user_id: '', password: 'pass1234' });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('User ID cannot be blank');
      }
    });

    test('rejects whitespace-only user_id', () => {
      const result = loginSchema.safeParse({ user_id: '   ', password: 'pass1234' });
      expect(result.success).toBe(false);
    });

    test('rejects user_id exceeding 8 chars (PIC X(08))', () => {
      const result = loginSchema.safeParse({ user_id: 'TOOLONGID', password: 'pass' });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toContain('8 characters');
      }
    });

    test('uppercases user_id (FUNCTION UPPER-CASE)', () => {
      const result = loginSchema.safeParse({ user_id: 'admin001', password: 'pass1234' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.user_id).toBe('ADMIN001');
      }
    });

    test('trims whitespace from user_id', () => {
      const result = loginSchema.safeParse({ user_id: '  ADMIN  ', password: 'pass1234' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.user_id).toBe('ADMIN');
      }
    });

    test('accepts valid 8-char user_id', () => {
      const result = loginSchema.safeParse({ user_id: 'ADMIN001', password: 'pass1234' });
      expect(result.success).toBe(true);
    });
  });

  describe('password', () => {
    test('rejects empty password (WHEN PASSWDI = SPACES)', () => {
      const result = loginSchema.safeParse({ user_id: 'ADMIN001', password: '' });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toBe('Password cannot be blank');
      }
    });

    test('rejects password exceeding 8 chars (PIC X(08))', () => {
      const result = loginSchema.safeParse({ user_id: 'ADMIN001', password: 'toolong123' });
      expect(result.success).toBe(false);
    });

    test('accepts valid password', () => {
      const result = loginSchema.safeParse({ user_id: 'ADMIN001', password: 'Admin123' });
      expect(result.success).toBe(true);
    });
  });

  describe('valid submission', () => {
    test('accepts valid credentials and normalizes user_id', () => {
      const result = loginSchema.safeParse({ user_id: 'user0001', password: 'pass1234' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.user_id).toBe('USER0001');
        expect(result.data.password).toBe('pass1234');
      }
    });
  });
});
