/**
 * Tests for report validators.
 * Derived from CORPT00C COBOL business rules.
 */
import { reportSubmitSchema } from '@/lib/validators/report';

describe('reportSubmitSchema — CORPT00C validation rules', () => {
  describe('report_type', () => {
    test('accepts monthly', () => {
      const result = reportSubmitSchema.safeParse({ report_type: 'monthly' });
      expect(result.success).toBe(true);
    });

    test('accepts yearly', () => {
      const result = reportSubmitSchema.safeParse({ report_type: 'yearly' });
      expect(result.success).toBe(true);
    });

    test('accepts custom with valid dates', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        start_date: '2024-01-01',
        end_date: '2024-03-31',
      });
      expect(result.success).toBe(true);
    });

    test('rejects invalid report_type', () => {
      const result = reportSubmitSchema.safeParse({ report_type: 'weekly' });
      expect(result.success).toBe(false);
    });
  });

  describe('custom report type date validation (CORPT00C PROCESS-ENTER-KEY)', () => {
    test('rejects custom without start_date', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        end_date: '2024-03-31',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const paths = result.error.errors.map((e) => e.path.join('.'));
        expect(paths).toContain('start_date');
      }
    });

    test('rejects custom without end_date', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        start_date: '2024-01-01',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const paths = result.error.errors.map((e) => e.path.join('.'));
        expect(paths).toContain('end_date');
      }
    });

    test('rejects start_date after end_date (CORPT00C logical ordering check)', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        start_date: '2024-03-31',
        end_date: '2024-01-01',
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors[0].message).toContain('Start date must not be after end date');
      }
    });

    test('accepts same start and end date', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        start_date: '2024-06-15',
        end_date: '2024-06-15',
      });
      expect(result.success).toBe(true);
    });

    test('rejects invalid date format (CSUTLDTC equivalent)', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        start_date: '2024/01/01',
        end_date: '2024/03/31',
      });
      expect(result.success).toBe(false);
    });

    test('rejects month > 12 (CORPT00C: SDTMMI > 12 → error)', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        start_date: '2024-13-01',
        end_date: '2024-13-31',
      });
      expect(result.success).toBe(false);
    });

    test('rejects day > 31 (CORPT00C: SDTDDI > 31 → error)', () => {
      const result = reportSubmitSchema.safeParse({
        report_type: 'custom',
        start_date: '2024-01-32',
        end_date: '2024-02-28',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('monthly / yearly do not require dates', () => {
    test('monthly does not require start/end dates', () => {
      const result = reportSubmitSchema.safeParse({ report_type: 'monthly' });
      expect(result.success).toBe(true);
    });

    test('yearly does not require start/end dates', () => {
      const result = reportSubmitSchema.safeParse({ report_type: 'yearly' });
      expect(result.success).toBe(true);
    });
  });
});
