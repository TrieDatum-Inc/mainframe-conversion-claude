/**
 * Tests for src/lib/api.ts — getErrorMessage helper.
 *
 * Full API call tests require a live server; these unit-tests cover
 * the error normalisation logic that maps axios errors to user strings.
 */
import { describe, expect, it, jest } from "@jest/globals";
import axios from "axios";

// We test getErrorMessage in isolation by importing it directly
// Mock axios to avoid real HTTP calls
jest.mock("axios", () => {
  const actual = jest.requireActual<typeof import("axios")>("axios");
  return {
    ...actual,
    create: jest.fn(() => ({
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
    })),
  };
});

import { getErrorMessage } from "../src/lib/api";

describe("getErrorMessage", () => {
  it("returns 'An unexpected error occurred' for non-axios errors", () => {
    expect(getErrorMessage(new Error("plain error"))).toBe(
      "An unexpected error occurred"
    );
  });

  it("returns string detail from axios response", () => {
    const err = new axios.AxiosError("Request failed");
    Object.assign(err, {
      response: { data: { detail: "User ID already exists" } },
    });
    expect(getErrorMessage(err)).toBe("User ID already exists");
  });

  it("joins array detail messages", () => {
    const err = new axios.AxiosError("Validation error");
    Object.assign(err, {
      response: {
        data: { detail: [{ msg: "Field required" }, { msg: "Too short" }] },
      },
    });
    expect(getErrorMessage(err)).toBe("Field required; Too short");
  });

  it("falls back to axios message when no response body", () => {
    const err = new axios.AxiosError("Network Error");
    expect(getErrorMessage(err)).toBe("Network Error");
  });
});
