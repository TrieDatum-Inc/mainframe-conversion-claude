/**
 * Utility function tests.
 */
import { formatUserType, getErrorMessage } from '../src/lib/utils';
import { ApiError } from '../src/lib/api';

describe('formatUserType', () => {
  it("formats 'A' as Admin", () => {
    expect(formatUserType('A')).toBe('Admin');
  });

  it("formats 'U' as User", () => {
    expect(formatUserType('U')).toBe('User');
  });

  it('returns unknown values unchanged', () => {
    expect(formatUserType('X')).toBe('X');
  });
});

describe('getErrorMessage', () => {
  it('extracts message from Error', () => {
    expect(getErrorMessage(new Error('oops'))).toBe('oops');
  });

  it('extracts message from ApiError', () => {
    expect(getErrorMessage(new ApiError('not found', 404))).toBe('not found');
  });

  it('returns fallback for unknown type', () => {
    expect(getErrorMessage({ something: 'else' })).toBe('An unexpected error occurred');
  });
});
