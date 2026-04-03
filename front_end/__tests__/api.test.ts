/**
 * Frontend API service layer unit tests.
 *
 * Tests the TypeScript API client functions against mocked fetch responses.
 * Verifies that correct HTTP methods, URLs, headers, and bodies are sent.
 */
import { ApiError, createUser, deleteUser, getUser, listUsers, updateUser } from '../src/lib/api';

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  jest.clearAllMocks();
});

function mockResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

// ---------------------------------------------------------------------------
// listUsers — COUSR00C
// ---------------------------------------------------------------------------

describe('listUsers', () => {
  it('calls GET /api/users with admin header', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({
        users: [],
        page: 1,
        page_size: 10,
        total_count: 0,
        has_next_page: false,
        has_prev_page: false,
      }),
    );

    await listUsers({ page: 1, page_size: 10 });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/users'),
      expect.objectContaining({
        headers: expect.objectContaining({ 'X-User-Type': 'A' }),
      }),
    );
  });

  it('includes pagination params in query string', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ users: [], page: 2, page_size: 5, total_count: 10, has_next_page: true, has_prev_page: true }),
    );

    await listUsers({ page: 2, page_size: 5 });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('page=2');
    expect(url).toContain('page_size=5');
  });

  it('includes search_user_id when provided', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ users: [], page: 1, page_size: 10, total_count: 0, has_next_page: false, has_prev_page: false }),
    );

    await listUsers({ search_user_id: 'admin' });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('search_user_id=admin');
  });

  it('throws ApiError on 403', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ detail: 'Admin access required' }, 403));

    await expect(listUsers()).rejects.toThrow(ApiError);
  });
});

// ---------------------------------------------------------------------------
// getUser — COUSR02C/03C lookup
// ---------------------------------------------------------------------------

describe('getUser', () => {
  it('calls GET /api/users/{userId}', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({
        user_id: 'admin001',
        first_name: 'Alice',
        last_name: 'Administrator',
        user_type: 'A',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }),
    );

    const result = await getUser('admin001');

    expect(result.user_id).toBe('admin001');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/users/admin001'),
      expect.anything(),
    );
  });

  it('throws ApiError with 404 for not found', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ detail: 'User ID NOT found: notexist' }, 404),
    );

    await expect(getUser('notexist')).rejects.toThrow(ApiError);
    try {
      await getUser('notexist');
    } catch (err) {
      if (err instanceof ApiError) {
        expect(err.status).toBe(404);
        expect(err.message).toContain('NOT found');
      }
    }
  });
});

// ---------------------------------------------------------------------------
// createUser — COUSR01C
// ---------------------------------------------------------------------------

describe('createUser', () => {
  it('calls POST /api/users with correct body', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({
        user_id: 'newuser1',
        first_name: 'Carol',
        last_name: 'Smith',
        user_type: 'U',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }, 201),
    );

    const payload = {
      first_name: 'Carol',
      last_name: 'Smith',
      user_id: 'newuser1',
      password: 'password',
      user_type: 'U' as const,
    };
    const result = await createUser(payload);

    expect(result.user_id).toBe('newuser1');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/users'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    );
  });

  it('throws ApiError(409) on duplicate user_id', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ detail: 'User ID already exist: admin001' }, 409),
    );

    await expect(
      createUser({
        first_name: 'Dup',
        last_name: 'User',
        user_id: 'admin001',
        password: 'password',
        user_type: 'U',
      }),
    ).rejects.toThrow(ApiError);
  });

  it('does not include password in the URL', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ user_id: 'u1', first_name: 'A', last_name: 'B', user_type: 'U', created_at: '', updated_at: '' }, 201),
    );
    await createUser({ first_name: 'A', last_name: 'B', user_id: 'u1', password: 'secret', user_type: 'U' });
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).not.toContain('secret');
  });
});

// ---------------------------------------------------------------------------
// updateUser — COUSR02C
// ---------------------------------------------------------------------------

describe('updateUser', () => {
  it('calls PUT /api/users/{userId}', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({
        user_id: 'user0001',
        first_name: 'Updated',
        last_name: 'Smith',
        user_type: 'U',
        created_at: '',
        updated_at: '',
      }),
    );

    const result = await updateUser('user0001', {
      first_name: 'Updated',
      last_name: 'Smith',
      password: 'newpass',
      user_type: 'U',
    });

    expect(result.first_name).toBe('Updated');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/users/user0001'),
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('throws ApiError(422) when no changes made', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ detail: 'Please modify to update ...' }, 422),
    );

    await expect(
      updateUser('user0001', { first_name: 'Same', last_name: 'Same', password: 'same', user_type: 'U' }),
    ).rejects.toThrow(ApiError);
  });
});

// ---------------------------------------------------------------------------
// deleteUser — COUSR03C
// ---------------------------------------------------------------------------

describe('deleteUser', () => {
  it('calls DELETE /api/users/{userId}', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, status: 204, json: () => Promise.resolve(undefined) } as Response);

    await deleteUser('user0003');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/users/user0003'),
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('throws ApiError(404) for not found', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ detail: 'User ID NOT found: gone' }, 404),
    );

    await expect(deleteUser('gone')).rejects.toThrow(ApiError);
  });
});
