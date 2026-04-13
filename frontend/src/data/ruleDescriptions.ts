/**
 * Strip validator prefix (e.g. "native:L042" → "L042") for description lookup.
 */
export function bareRuleId(ruleId: string): string {
  const idx = ruleId.indexOf(":");
  if (idx > 0 && idx < ruleId.length - 1) return ruleId.slice(idx + 1);
  return ruleId;
}

/**
 * Look up a rule description, handling prefixed IDs like "native:L042".
 */
export function getRuleDescription(ruleId: string): string {
  return _descriptions[ruleId] ?? _descriptions[bareRuleId(ruleId)] ?? "";
}

/** Live descriptions populated from the Gateway /rules API. */
const _descriptions: Record<string, string> = {};

let _fetchStarted = false;

function _loadFromApi(): void {
  if (_fetchStarted) return;
  _fetchStarted = true;
  const base =
    (typeof import.meta !== "undefined" &&
      (import.meta as unknown as Record<string, Record<string, unknown>>).env
        ?.VITE_API_BASE) ||
    "/api/v1";
  fetch(`${base}/rules`)
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((rows: { rule_id: string; description: string }[]) => {
      if (!Array.isArray(rows)) return;
      for (const r of rows) {
        if (r.rule_id && r.description) {
          _descriptions[r.rule_id] = r.description;
        }
      }
    })
    .catch(() => {});
}

_loadFromApi();
