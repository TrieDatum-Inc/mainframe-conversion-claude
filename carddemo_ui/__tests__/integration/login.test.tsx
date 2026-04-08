/**
 * Integration tests for the Login page.
 * Covers COSGN00C behavior end-to-end with mocked API.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
  usePathname: () => '/login',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock authService
jest.mock('@/services/authService', () => ({
  authService: {
    isAuthenticated: jest.fn().mockReturnValue(false),
    getCurrentUser: jest.fn().mockReturnValue(null),
    login: jest.fn(),
    logout: jest.fn(),
  },
}));

import LoginPage from '@/app/login/page';
import { authService } from '@/services/authService';

describe('Login page — COSGN00C', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
  });

  test('renders user ID and password fields (USERID, PASSWD BMS fields)', () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/user id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  test('USERID field has autofocus (IC attribute in BMS)', () => {
    render(<LoginPage />);
    const userIdInput = screen.getByLabelText(/user id/i);
    // React's autoFocus prop programmatically focuses the element in jsdom
    // rather than setting the HTML autofocus attribute — verify focus state instead
    expect(userIdInput).toHaveFocus();
  });

  test('password field is type=password (DRK attribute in BMS)', () => {
    render(<LoginPage />);
    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('shows validation error for empty user ID on submit', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('User ID cannot be blank')).toBeInTheDocument();
    });
  });

  test('shows validation error for empty password on submit', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/user id/i), 'ADMIN001');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText('Password cannot be blank')).toBeInTheDocument();
    });
  });

  test('calls login with uppercased user_id (FUNCTION UPPER-CASE)', async () => {
    const user = userEvent.setup();
    (authService.login as jest.Mock).mockResolvedValue({
      access_token: 'token123',
      token_type: 'bearer',
      user_id: 'ADMIN001',
      user_type: 'A',
      first_name: 'Admin',
      last_name: 'User',
    });

    render(<LoginPage />);

    await user.type(screen.getByLabelText(/user id/i), 'admin001');
    await user.type(screen.getByLabelText(/password/i), 'Pass1234');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        user_id: 'ADMIN001', // uppercased
        password: 'Pass1234',
      });
    });
  });

  test('shows API error in alert (ERRMSG BRT RED)', async () => {
    const user = userEvent.setup();
    (authService.login as jest.Mock).mockRejectedValue({
      response: { data: { detail: 'Wrong Password. Try again ...' } },
    });

    render(<LoginPage />);
    await user.type(screen.getByLabelText(/user id/i), 'ADMIN001');
    await user.type(screen.getByLabelText(/password/i), 'WrongPass');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      // The alert should display the error
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  test('submit button shows loading state during request', async () => {
    const user = userEvent.setup();
    let resolveLogin: (value: unknown) => void;
    const loginPromise = new Promise((resolve) => { resolveLogin = resolve; });
    (authService.login as jest.Mock).mockReturnValue(loginPromise);

    render(<LoginPage />);
    await user.type(screen.getByLabelText(/user id/i), 'ADMIN001');
    await user.type(screen.getByLabelText(/password/i), 'Pass1234');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // Button should be disabled during loading
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled();

    resolveLogin!({
      access_token: 'tok',
      token_type: 'bearer',
      user_id: 'ADMIN001',
      user_type: 'A',
      first_name: null,
      last_name: null,
    });
  });
});
