import { formatExpiry } from "../src/lib/utils";
describe("formatExpiry", () => {
  test("formats month and year correctly", () => expect(formatExpiry(3, 2026)).toBe("03/2026"));
  test("pads single-digit month", () => expect(formatExpiry(1, 2028)).toBe("01/2028"));
  test("returns dash for null values", () => { expect(formatExpiry(null, null)).toBe("—"); expect(formatExpiry(3, null)).toBe("—"); expect(formatExpiry(null, 2026)).toBe("—"); });
});
