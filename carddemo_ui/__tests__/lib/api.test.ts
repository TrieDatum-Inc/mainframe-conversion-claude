import { api, ApiError } from "@/lib/api";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

beforeEach(() => {
  mockFetch.mockReset();
  localStorageMock.clear();
});

describe("api.get", () => {
  it("makes a GET request and returns JSON", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 1, name: "Test" }),
    });

    const result = await api.get<{ id: number; name: string }>("/api/test");

    expect(result).toEqual({ id: 1, name: "Test" });
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/test",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("includes Authorization header when token exists", async () => {
    localStorageMock.setItem("token", "test-jwt-token");
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await api.get("/api/test");

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders["Authorization"]).toBe("Bearer test-jwt-token");
  });

  it("does not include Authorization header when no token", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    await api.get("/api/test");

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    expect(callHeaders["Authorization"]).toBeUndefined();
  });
});

describe("api.post", () => {
  it("makes a POST request with JSON body", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: "Created" }),
    });

    await api.post("/api/test", { name: "New" });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/test",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "New" }),
      }),
    );
  });
});

describe("api.put", () => {
  it("makes a PUT request with JSON body", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: "Updated" }),
    });

    await api.put("/api/test/1", { name: "Updated" });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/test/1",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ name: "Updated" }),
      }),
    );
  });
});

describe("api.delete", () => {
  it("makes a DELETE request", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: "Deleted" }),
    });

    await api.delete("/api/test/1");

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/test/1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});

describe("error handling", () => {
  it("throws ApiError with error_message from response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ error_message: "Invalid input", field: "name" }),
    });

    try {
      await api.get("/api/test");
      fail("Expected ApiError");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.message).toBe("Invalid input");
      expect(apiErr.status).toBe(400);
      expect(apiErr.field).toBe("name");
    }
  });

  it("throws ApiError with detail from response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Not found" }),
    });

    try {
      await api.get("/api/test");
      fail("Expected ApiError");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).message).toBe("Not found");
    }
  });

  it("throws ApiError with generic message when response is not JSON", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => { throw new Error("not json"); },
    });

    try {
      await api.get("/api/test");
      fail("Expected ApiError");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).message).toContain("500");
    }
  });
});
