"""
Logic-only verification for AURA-AEGIS bug fixes.
Does NOT import streamlit — tests only pure Python logic.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} {detail}")
        failed += 1

print("=" * 60)
print("AURA-AEGIS Logic Bug Fix Verification (no-Streamlit)")
print("=" * 60)

# ── Test 1: FACTORY_BAD mutation fix ─────────────────────────────
print("\n[1] ssd_simulator — FACTORY_BAD must not be mutated")

# Manually parse the module-level FACTORY_BAD and the _apply_preset method
# without running the full import chain (which needs numpy)
with open('core/ssd_simulator.py', 'r', encoding='utf-8') as f:
    src = f.read()

# Must NOT contain the old mutation lines
has_bad_mutation = 'FACTORY_BAD.update(' in src
check("No FACTORY_BAD.update() mutation in ssd_simulator.py", not has_bad_mutation,
      "(old mutation line still present)")

# Must use union operator instead
has_union_fix = 'FACTORY_BAD | {11, 23}' in src
check("Uses set-union FACTORY_BAD | {11, 23} in middle_aged preset", has_union_fix,
      "(fix not found in source)")

# ── Test 2: section_p3_ecc_engine tier fix ───────────────────────
print("\n[2] section_p3_ecc_engine — _tier() logic")

with open('sections/section_p3_ecc_engine.py', 'r', encoding='utf-8') as f:
    src2 = f.read()

# Must not contain the duplicate Tier 1 return for the BCH range
has_dup_tier1 = ('elif ecc <= ECC_TIER2_BCH:\n'
                 '        return (1, "Tier 1 — Syndrome Zero Bypass"') in src2
check("No duplicate Tier-1 return for ECC 1-200 range", not has_dup_tier1,
      "(duplicate Tier-1 fix not applied)")

# Must contain the Tier 2a BCH fix
has_tier2a = 'Tier 2a — BCH Correction' in src2
check("Tier 2a BCH Correction label present for ECC 1-200 range", has_tier2a)

# Must NOT contain the old f-string backslash pattern
has_backslash_fstring = 'style=\\\\\\"background' in src2
check("No illegal backslashes inside f-string expression", not has_backslash_fstring,
      "(old backslash f-string still present)")

# status_badge variable pre-computation present
has_status_badge = 'status_badge' in src2
check("status_badge variable extracted before f-string", has_status_badge)

# ── Test 3: Section header fix ────────────────────────────────────
print("\n[3] section3_smart — Section header text")

with open('sections/section3_smart.py', 'r', encoding='utf-8') as f:
    src3 = f.read()

has_section3_header = 'SECTION 3' in src3
has_wrong_section1  = ('SECTION 1 \u2014' in src3 or
                       'SECTION 1 &' in src3 or
                       '"SECTION 1 ' in src3)
check("Header says 'SECTION 3'", has_section3_header)
check("Header does NOT say 'SECTION 1'", not has_wrong_section1,
      "(old SECTION 1 header still present)")

# ── Syntax check via py_compile ───────────────────────────────────
print("\n[4] Syntax — all .py files must compile cleanly")
import py_compile, glob

root = os.path.dirname(os.path.abspath(__file__))
compile_errors = []
for path in sorted(glob.glob(os.path.join(root, '**', '*.py'), recursive=True)):
    if '__pycache__' in path:
        continue
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        rel = os.path.relpath(path, root)
        compile_errors.append(f"{rel}: {e}")

check(f"All .py files compile without syntax errors", len(compile_errors) == 0,
      '\n' + '\n'.join(compile_errors) if compile_errors else "")

# ── Summary ───────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
