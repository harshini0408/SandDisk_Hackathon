import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.pillar4_engine import (
    auto_correct, extract_variables, generate_truth_table,
    quine_mccluskey, petricks_method, build_expression_from_pis,
    try_factor_expression, safe_eval, compute_metrics, BUILTIN_TESTS
)

ok = fail = 0
for tc in BUILTIN_TESTS:
    cr = auto_correct(tc["expr"])
    expr = cr.corrected
    variables = extract_variables(expr)
    n = len(variables)
    rows, on_set, _ = generate_truth_table(expr, variables, tc["dont_cares"])
    pis, _ = quine_mccluskey(on_set, tc["dont_cares"], n)
    sel, cov, _ = petricks_method(pis, on_set, n)
    opt = build_expression_from_pis(sel, variables)
    final = try_factor_expression(opt)
    bdd_ok = True
    for i in range(2 ** n):
        if i in tc["dont_cares"]:
            continue
        asn = {v: (i >> (n - 1 - j)) & 1 for j, v in enumerate(variables)}
        if safe_eval(expr, asn) != safe_eval(final, asn):
            bdd_ok = False
            break
    mb = compute_metrics(expr)
    ma = compute_metrics(final)
    status = "PASS" if bdd_ok else "FAIL"
    if bdd_ok:
        ok += 1
    else:
        fail += 1
    print(f"{status}  {tc['label']}  |  cost {mb['cost']} -> {ma['cost']}  |  {final}")

print()
print(f"{ok} passed, {fail} failed")
sys.exit(0 if fail == 0 else 1)
