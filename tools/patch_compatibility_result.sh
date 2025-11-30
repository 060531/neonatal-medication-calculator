#!/usr/bin/env bash
set -euo pipefail

F="docs/compatibility_result.html"
[ -f "$F" ] || { echo "Missing $F"; exit 1; }

# Insert patch (idempotent)
if ! grep -q 'id="compat-lookup-patch"' "$F"; then
  perl -0777 -pi -e 's#</body>#<script id="compat-lookup-patch">\n(async function () {\n  function normDrug(s){\n    return String(s || \"\")\n      .replace(/\\+/g, \" \")\n      .trim()\n      .toLowerCase()\n      .replace(/\\s+/g, \" \");\n  }\n\n  const params = new URLSearchParams(location.search);\n  const drugA = params.get(\"drug_a\") || \"\";\n  const drugB = params.get(\"drug_b\") || \"\";\n\n  const a = normDrug(drugA);\n  const b = normDrug(drugB);\n  const k1 = a + \"|\" + b;\n  const k2 = b + \"|\" + a;\n\n  const sCodeEl  = document.querySelector(\"[data-status-code]\");\n  const sLabelEl = document.querySelector(\"[data-status-label]\");\n  if (!sCodeEl || !sLabelEl) return;\n\n  const map = { C:\"Compatible\", I:\"Incompatible\", U:\"Uncertain\", ND:\"Unknown\" };\n\n  const statusFromUrl = params.get(\"status\");\n  if (statusFromUrl) {\n    const code = String(statusFromUrl).toUpperCase();\n    sCodeEl.textContent = code;\n    sLabelEl.textContent = map[code] || \"Unknown\";\n    return;\n  }\n\n  try {\n    const res = await fetch(\"./static/compat_lookup.json?x=\" + Date.now(), { cache: \"no-store\" });\n    const lookup = await res.json();\n    const row = lookup[k1] || lookup[k2];\n    const code = (row && row.status ? String(row.status).toUpperCase() : \"ND\");\n    sCodeEl.textContent = code;\n    sLabelEl.textContent = map[code] || \"Unknown\";\n  } catch (e) {}\n})();\n</script>\n</body>#s' "$F"
fi

# Disable legacy mapper (idempotent marker)
if ! grep -q "disable legacy status mapping" "$F"; then
  perl -0777 -pi -e 's/(var\s+sCodeEl\s*=\s*document\.querySelector\("\[data-status-code\]"\);\s*var\s+sLabelEl\s*=\s*document\.querySelector\("\[data-status-label\]"\);\s*)/\1\n    \/\/ PATCH: disable legacy status mapping (use compat-lookup-patch)\n    return;\n/s' "$F"
fi

echo "patched: $F"
