/**
 * Tests for usePagination hook.
 * Maps to COBOL STARTBR/READNEXT/READPREV browse pattern.
 */
import { renderHook, act } from '@testing-library/react';
import { usePagination, useNumericPagination } from '@/hooks/usePagination';

describe('usePagination hook', () => {
  test('starts at page 1 with no cursor', () => {
    const { result } = renderHook(() => usePagination());
    expect(result.current.page).toBe(1);
    expect(result.current.cursor).toBeUndefined();
    expect(result.current.direction).toBe('forward');
  });

  test('goNext increments page and sets cursor (PF8 equivalent)', () => {
    const { result } = renderHook(() => usePagination());
    act(() => {
      result.current.goNext('cursor-abc');
    });
    expect(result.current.page).toBe(2);
    expect(result.current.cursor).toBe('cursor-abc');
    expect(result.current.direction).toBe('forward');
  });

  test('goPrev decrements page and sets backward direction (PF7 equivalent)', () => {
    const { result } = renderHook(() => usePagination());
    // Go forward first
    act(() => result.current.goNext('cursor-abc'));
    act(() => result.current.goNext('cursor-def'));
    // Then go back
    act(() => result.current.goPrev('cursor-abc'));
    expect(result.current.page).toBe(2);
    expect(result.current.direction).toBe('backward');
  });

  test('page does not go below 1 on goPrev', () => {
    const { result } = renderHook(() => usePagination());
    act(() => result.current.goPrev('cursor-abc'));
    expect(result.current.page).toBe(1);
  });

  test('goNext with null/undefined cursor does nothing', () => {
    const { result } = renderHook(() => usePagination());
    act(() => result.current.goNext(null));
    expect(result.current.page).toBe(1);
    expect(result.current.cursor).toBeUndefined();
  });

  test('reset returns to initial state', () => {
    const { result } = renderHook(() => usePagination());
    act(() => result.current.goNext('cursor-abc'));
    act(() => result.current.goNext('cursor-def'));
    act(() => result.current.reset());
    expect(result.current.page).toBe(1);
    expect(result.current.cursor).toBeUndefined();
    expect(result.current.direction).toBe('forward');
  });
});

describe('useNumericPagination hook', () => {
  test('starts at page 1 with no cursor', () => {
    const { result } = renderHook(() => useNumericPagination());
    expect(result.current.page).toBe(1);
    expect(result.current.cursor).toBeUndefined();
  });

  test('goNext accepts numeric cursor', () => {
    const { result } = renderHook(() => useNumericPagination());
    act(() => result.current.goNext(42));
    expect(result.current.cursor).toBe(42);
    expect(result.current.page).toBe(2);
  });

  test('goNext with null does nothing', () => {
    const { result } = renderHook(() => useNumericPagination());
    act(() => result.current.goNext(null));
    expect(result.current.page).toBe(1);
  });

  test('reset clears cursor and page', () => {
    const { result } = renderHook(() => useNumericPagination());
    act(() => result.current.goNext(100));
    act(() => result.current.reset());
    expect(result.current.cursor).toBeUndefined();
    expect(result.current.page).toBe(1);
  });
});
