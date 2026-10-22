# Fixture-optional occt gate (task)
Edit ONLY tests/test_occt_gate.mjs and .gitignore. Do not touch src/ or any other file. Do not commit, delete, or move files.
1. In tests/test_occt_gate.mjs, replace `const blinkMod = await import(blinkUrl);` with a dynamic import inside try/catch: `let blinkMod = null; try { blinkMod = await import(blinkUrl); } catch (e) { blinkMod = null; }`. If the fixture file does not exist (check with existsSync first, import only if present), blinkMod stays null.
2. Wrap the whole Blink block (from `const blinkPlan = blinkMod.blinkHolePlan(null);` through `console.log('blink dropped', ...)`) in `if (blinkMod) { ... } else { console.log('skipped, local fixture'); }`. Everything else must still run unchanged.
3. Append the line `tests/fixtures/blink.*` to .gitignore (keep existing content).
Do not run CTest. When finished, print exactly FIXOPT_DONE.
