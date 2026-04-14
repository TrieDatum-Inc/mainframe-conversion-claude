/**
 * Frontend integration tests for the login page.
 *
 * COBOL origin: Tests map COSGN00C behaviour viewed from the user's perspective.
 * Each test corresponds to a user action / error condition in the COBOL program.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthContext } from "@/components/auth/AuthProvider";
import LoginPage from "@/app/login/page";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock the api module
jest.mock("@/lib/api", () => ({
  api: {
    post: jest.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public errorCode: string,
      message: string
    ) {
      super(message);
      this.name = "ApiError";
    }
  },
}));

// Mock AppHeader to avoid date/time rendering complexity
jest.mock("@/components/layout/AppHeader", () => ({
  AppHeader: () => <header data-testid="app-header" />,
}));

import { api, ApiError } from "@/lib/api";
const mockApiPost = api.post as jest.MockedFunction<typeof api.post>;
const mockRouterPush = jest.fn();

// Override next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockRouterPush, replace: jest.fn(), back: jest.fn() }),
}));

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

const mockLogin = jest.fn();

function renderLoginPage() {
  return render(
    <AuthContext.Provider
      value={{
        user: null,
        token: null,
        isAuthenticated: false,
        login: mockLogin,
        logout: jest.fn(),
      }}
    >
      <LoginPage />
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("LoginPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the User ID input field", () => {
      renderLoginPage();
      expect(screen.getByLabelText(/user id/i)).toBeInTheDocument();
    });

    it("renders the Password input field", () => {
      renderLoginPage();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it("renders the Sign On submit button", () => {
      renderLoginPage();
      expect(
        screen.getByRole("button", { name: /sign on/i })
      ).toBeInTheDocument();
    });

    it("renders the Exit action", () => {
      renderLoginPage();
      expect(screen.getByRole("button", { name: /exit/i })).toBeInTheDocument();
    });

    it("password field is of type password (DRK attribute equivalent)", () => {
      renderLoginPage();
      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveAttribute("type", "password");
    });

    it("User ID field has autoFocus (IC attribute equivalent)", () => {
      renderLoginPage();
      const userIdInput = screen.getByLabelText(/user id/i);
      // autoFocus is set on the element
      expect(userIdInput).toHaveAttribute("autofocus");
    });
  });

  describe("Validation — COBOL origin: COSGN00C blank field checks", () => {
    it("shows validation error when User ID is empty on submit", async () => {
      const user = userEvent.setup();
      renderLoginPage();

      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(screen.getByText(/user id is required/i)).toBeInTheDocument();
      });
    });

    it("shows validation error when Password is empty on submit", async () => {
      const user = userEvent.setup();
      renderLoginPage();

      await user.type(screen.getByLabelText(/user id/i), "ADMIN001");
      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
      });
    });

    it("does not call API when fields are empty", async () => {
      const user = userEvent.setup();
      renderLoginPage();

      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(mockApiPost).not.toHaveBeenCalled();
      });
    });
  });

  describe("Successful login", () => {
    const mockAdminResponse = {
      access_token: "mock.jwt.token",
      token_type: "bearer",
      expires_in: 3600,
      user_id: "ADMIN001",
      user_type: "A" as const,
      first_name: "John",
      last_name: "Admin",
      redirect_to: "/admin/menu",
    };

    const mockUserResponse = {
      ...mockAdminResponse,
      user_id: "USER0001",
      user_type: "U" as const,
      first_name: "Alice",
      last_name: "Smith",
      redirect_to: "/menu",
    };

    it("calls the login API with correct payload", async () => {
      mockApiPost.mockResolvedValueOnce(mockAdminResponse);
      const user = userEvent.setup();
      renderLoginPage();

      await user.type(screen.getByLabelText(/user id/i), "ADMIN001");
      await user.type(screen.getByLabelText(/password/i), "Admin01!");
      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(mockApiPost).toHaveBeenCalledWith(
          "/api/v1/auth/login",
          { user_id: "ADMIN001", password: "Admin01!" }
        );
      });
    });

    it("redirects to /admin/menu when user_type is A", async () => {
      mockApiPost.mockResolvedValueOnce(mockAdminResponse);
      const user = userEvent.setup();
      renderLoginPage();

      await user.type(screen.getByLabelText(/user id/i), "ADMIN001");
      await user.type(screen.getByLabelText(/password/i), "Admin01!");
      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(mockRouterPush).toHaveBeenCalledWith("/admin/menu");
      });
    });

    it("redirects to /menu when user_type is U", async () => {
      mockApiPost.mockResolvedValueOnce(mockUserResponse);
      const user = userEvent.setup();
      renderLoginPage();

      await user.type(screen.getByLabelText(/user id/i), "USER0001");
      await user.type(screen.getByLabelText(/password/i), "User001!");
      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(mockRouterPush).toHaveBeenCalledWith("/menu");
      });
    });

    it("calls login() on the AuthContext with the response", async () => {
      mockApiPost.mockResolvedValueOnce(mockAdminResponse);
      const user = userEvent.setup();
      renderLoginPage();

      await user.type(screen.getByLabelText(/user id/i), "ADMIN001");
      await user.type(screen.getByLabelText(/password/i), "Admin01!");
      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith(mockAdminResponse);
      });
    });
  });

  describe("Error handling — COBOL origin: COSGN00C ERRMSG display", () => {
    it("shows error message on 401 response", async () => {
      mockApiPost.mockRejectedValueOnce(
        new ApiError(401, "INVALID_CREDENTIALS", "Invalid User ID or Password")
      );
      const user = userEvent.setup();
      renderLoginPage();

      await user.type(screen.getByLabelText(/user id/i), "ADMIN001");
      await user.type(screen.getByLabelText(/password/i), "WrongPwd");
      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/invalid user id or password/i)
        ).toBeInTheDocument();
      });
    });

    it("shows rate-limit message on 429 response", async () => {
      mockApiPost.mockRejectedValueOnce(
        new ApiError(429, "RATE_LIMITED", "Too Many Requests")
      );
      const user = userEvent.setup();
      renderLoginPage();

      await user.type(screen.getByLabelText(/user id/i), "ADMIN001");
      await user.type(screen.getByLabelText(/password/i), "somepwd1");
      await user.click(screen.getByRole("button", { name: /sign on/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/too many login attempts/i)
        ).toBeInTheDocument();
      });
    });

    it("shows error when User ID is not found — same message as wrong password", async () => {
      // SECURITY: both 401 cases must show identical message (enumeration prevention)
      const errorNotFound = new ApiError(401, "INVALID_CREDENTIALS", "Invalid User ID or Password");
      const errorWrongPwd = new ApiError(401, "INVALID_CREDENTIALS", "Invalid User ID or Password");

      // First render: user not found scenario
      mockApiPost.mockRejectedValueOnce(errorNotFound);
      const user1 = userEvent.setup();
      const { unmount } = renderLoginPage();

      await user1.type(screen.getByLabelText(/user id/i), "NOPE9999");
      await user1.type(screen.getByLabelText(/password/i), "anythng1");
      await user1.click(screen.getByRole("button", { name: /sign on/i }));

      const errorText1 = await screen.findByText(/invalid user id or password/i);
      const message1 = errorText1.textContent;
      unmount();

      // Second render: wrong password scenario
      mockApiPost.mockRejectedValueOnce(errorWrongPwd);
      const user2 = userEvent.setup();
      renderLoginPage();

      await user2.type(screen.getByLabelText(/user id/i), "ADMIN001");
      await user2.type(screen.getByLabelText(/password/i), "WrongPw!");
      await user2.click(screen.getByRole("button", { name: /sign on/i }));

      const errorText2 = await screen.findByText(/invalid user id or password/i);
      const message2 = errorText2.textContent;

      // The messages must be identical — this is the enumeration-prevention test
      expect(message1).toBe(message2);
    });
  });
});
