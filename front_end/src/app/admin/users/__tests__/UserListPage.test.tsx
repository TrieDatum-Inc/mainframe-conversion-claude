/**
 * Tests for the User List page (/admin/users).
 *
 * COBOL origin: COUSR00C browse screen behavior:
 *   - Shows up to 10 users per page
 *   - Pagination with Previous/Next buttons (PF7/PF8)
 *   - Filter field to browse from a specific user_id (USRIDINI)
 *   - Update/Delete action buttons per row (replaces 'U'/'D' selectors)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { UserTable } from '@/components/lists/UserTable';
import { MessageBar } from '@/components/ui/MessageBar';
import type { UserResponse } from '@/types';

// Sample user data
const makeUser = (n: number): UserResponse => ({
  user_id: `USER${n.toString().padStart(4, '0')}`,
  first_name: `First${n}`,
  last_name: `Last${n}`,
  user_type: n === 1 ? 'A' : 'U',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
});

const sampleUsers = Array.from({ length: 5 }, (_, i) => makeUser(i + 1));

describe('UserTable component', () => {
  it('renders user rows with all required columns', () => {
    render(<UserTable users={sampleUsers} />);

    // Check column headers
    expect(screen.getByText('User ID')).toBeInTheDocument();
    expect(screen.getByText('First Name')).toBeInTheDocument();
    expect(screen.getByText('Last Name')).toBeInTheDocument();
    expect(screen.getByText('User Type')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  it('renders correct number of user rows', () => {
    render(<UserTable users={sampleUsers} />);
    // Each user should have their user_id visible
    sampleUsers.forEach((user) => {
      expect(screen.getByText(user.user_id)).toBeInTheDocument();
    });
  });

  it('shows Admin badge for user_type A', () => {
    render(<UserTable users={[makeUser(1)]} />);
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('shows User badge for user_type U', () => {
    render(<UserTable users={[makeUser(2)]} />);
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  it('renders Update and Delete links per row', () => {
    render(<UserTable users={[makeUser(1)]} />);
    // Update button → links to edit page (replaces COUSR00C 'U' selector → XCTL COUSR02C)
    expect(screen.getByRole('link', { name: 'Update' })).toHaveAttribute(
      'href',
      '/admin/users/USER0001/edit'
    );
    // Delete button → links to delete page (replaces COUSR00C 'D' selector → XCTL COUSR03C)
    expect(screen.getByRole('link', { name: 'Delete' })).toHaveAttribute(
      'href',
      '/admin/users/USER0001/delete'
    );
  });

  it('shows empty state message when no users', () => {
    render(<UserTable users={[]} />);
    expect(screen.getByText(/No users found/)).toBeInTheDocument();
  });

  it('never renders a password field', () => {
    render(<UserTable users={sampleUsers} />);
    // Security: password must never appear in the table
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/hash/i)).not.toBeInTheDocument();
  });
});

describe('MessageBar component', () => {
  it('renders error variant with red styling', () => {
    render(<MessageBar message="User ID NOT found" variant="error" />);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('text-red-700');
    expect(alert).toHaveTextContent('User ID NOT found');
  });

  it('renders success variant with green styling', () => {
    render(<MessageBar message="User has been added successfully" variant="success" />);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('text-green-700');
  });

  it('renders info variant for neutral prompts', () => {
    render(<MessageBar message="Modify fields below and click Save" variant="info" />);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('text-gray-700');
  });

  it('renders nothing when message is empty', () => {
    const { container } = render(<MessageBar message="" />);
    expect(container.firstChild).toBeNull();
  });
});
