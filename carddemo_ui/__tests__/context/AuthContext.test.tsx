import { render, screen, act, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "@/context/AuthContext";

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock api
jest.mock("@/lib/api", () => ({
  api: {
    post: jest.fn(),
  },
}));

import { api } from "@/lib/api";

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

function TestConsumer() {
  const { user, token, isAdmin, loading, login, logout } = useAuth();
  return (
    <div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="user">{user ? user.user_id : "null"}</div>
      <div data-testid="token">{token ?? "null"}</div>
      <div data-testid="isAdmin">{String(isAdmin)}</div>
      <button onClick={() => login({ user_id: "admin1", password: "ADMIN123" })}>
        Login
      </button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

beforeEach(() => {
  localStorageMock.clear();
  mockPush.mockReset();
  (api.post as jest.Mock).mockReset();
});

describe("AuthContext", () => {
  it("starts with no user and loading=true then false", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });
    expect(screen.getByTestId("user").textContent).toBe("null");
    expect(screen.getByTestId("token").textContent).toBe("null");
  });

  it("restores user from localStorage on mount", async () => {
    localStorageMock.setItem("token", "stored-token");
    localStorageMock.setItem("user", JSON.stringify({ user_id: "admin1", user_type: "A" }));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });
    expect(screen.getByTestId("user").textContent).toBe("admin1");
    expect(screen.getByTestId("token").textContent).toBe("stored-token");
    expect(screen.getByTestId("isAdmin").textContent).toBe("true");
  });

  it("login stores token and user, navigates to /dashboard", async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({
      token: "new-token",
      user_id: "user1",
      user_type: "U",
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading").textContent).toBe("false");
    });

    await act(async () => {
      await userEvent.click(screen.getByText("Login"));
    });

    expect(api.post).toHaveBeenCalledWith("/api/auth/login", {
      user_id: "admin1",
      password: "ADMIN123",
    });
    expect(screen.getByTestId("user").textContent).toBe("user1");
    expect(screen.getByTestId("isAdmin").textContent).toBe("false");
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
    expect(localStorageMock.getItem("token")).toBe("new-token");
  });

  it("logout clears state and navigates to /login", async () => {
    localStorageMock.setItem("token", "stored-token");
    localStorageMock.setItem("user", JSON.stringify({ user_id: "admin1", user_type: "A" }));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("user").textContent).toBe("admin1");
    });

    await act(async () => {
      await userEvent.click(screen.getByText("Logout"));
    });

    expect(screen.getByTestId("user").textContent).toBe("null");
    expect(screen.getByTestId("token").textContent).toBe("null");
    expect(mockPush).toHaveBeenCalledWith("/login");
    expect(localStorageMock.getItem("token")).toBeNull();
  });

  it("throws error when useAuth is used outside AuthProvider", () => {
    const spy = jest.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<TestConsumer />)).toThrow(
      "useAuth must be used within an AuthProvider",
    );
    spy.mockRestore();
  });
});
