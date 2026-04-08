/**
 * Tests for FormField component.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { FormField, Input } from '@/components/ui/FormField';

describe('FormField component', () => {
  test('renders label', () => {
    render(
      <FormField label="User ID" htmlFor="user_id">
        <input id="user_id" />
      </FormField>
    );
    expect(screen.getByText('User ID')).toBeInTheDocument();
  });

  test('renders required asterisk when required=true', () => {
    render(
      <FormField label="Password" htmlFor="password" required>
        <input id="password" />
      </FormField>
    );
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  test('renders error message', () => {
    render(
      <FormField label="Field" htmlFor="field" error="This field is required">
        <input id="field" />
      </FormField>
    );
    const error = screen.getByRole('alert');
    expect(error).toHaveTextContent('This field is required');
  });

  test('renders hint when no error', () => {
    render(
      <FormField label="Field" htmlFor="field" hint="Up to 8 characters">
        <input id="field" />
      </FormField>
    );
    expect(screen.getByText('Up to 8 characters')).toBeInTheDocument();
  });

  test('does not render hint when error is present', () => {
    render(
      <FormField
        label="Field"
        htmlFor="field"
        hint="Up to 8 characters"
        error="Required"
      >
        <input id="field" />
      </FormField>
    );
    expect(screen.queryByText('Up to 8 characters')).not.toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Required');
  });
});

describe('Input component', () => {
  test('renders with default class when no error', () => {
    render(<Input id="test" data-testid="input" />);
    const input = screen.getByTestId('input');
    expect(input.className).toContain('field-input');
    expect(input.className).not.toContain('field-input-error');
  });

  test('renders error class when hasError=true', () => {
    render(<Input id="test" data-testid="input" hasError />);
    const input = screen.getByTestId('input');
    expect(input.className).toContain('field-input-error');
  });
});
