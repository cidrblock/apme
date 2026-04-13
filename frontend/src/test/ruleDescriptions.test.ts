import { describe, it, expect } from "vitest";
import { bareRuleId, getRuleDescription } from "../data/ruleDescriptions";

describe("bareRuleId", () => {
  it("strips validator prefix", () => {
    expect(bareRuleId("native:L042")).toBe("L042");
    expect(bareRuleId("opa:L003")).toBe("L003");
  });

  it("returns the original if no prefix", () => {
    expect(bareRuleId("L042")).toBe("L042");
    expect(bareRuleId("SEC001")).toBe("SEC001");
  });

  it("handles edge cases", () => {
    expect(bareRuleId(":L042")).toBe(":L042");
    expect(bareRuleId("a:")).toBe("a:");
    expect(bareRuleId("")).toBe("");
  });
});

describe("getRuleDescription", () => {
  it("returns empty string when API has not loaded", () => {
    expect(getRuleDescription("L003")).toBe("");
  });

  it("returns empty string for unknown rules", () => {
    expect(getRuleDescription("ZZZZ999")).toBe("");
    expect(getRuleDescription("native:ZZZZ999")).toBe("");
  });
});
