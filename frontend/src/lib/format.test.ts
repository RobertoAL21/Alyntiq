import { describe, expect, it } from "vitest";

import { formatCurrency, formatPercent } from "./format";

describe("formatters", () => {
  it("formats USD values for presentation", () => {
    expect(formatCurrency(125430.72)).toBe("$125,431");
    expect(formatCurrency(125430.72, 2)).toBe("$125,430.72");
  });

  it("preserves the sign for percentage changes", () => {
    expect(formatPercent(0.0834)).toBe("+8.3%");
    expect(formatPercent(-0.0222)).toBe("-2.2%");
  });
});
