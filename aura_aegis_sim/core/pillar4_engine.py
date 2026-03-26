"""
pillar4_engine.py
Backend for Pillar 4 – Firmware Logic Optimization.
Key upgrades vs previous version:
 • Safe AST-based evaluator – NO eval()
 • Auto-correction engine for malformed expressions
 • Full QMC with hash-indexed grouping + early elimination
 • Petrick greedy cover
 • Cost model & algebraic factoring
"""

import re
import ast
import operator
from typing import List, Dict, Tuple, Optional


# ═══════════════════════════════════════════════════════════════
# SECTION 0 ─ AUTO-CORRECTION ENGINE
# ═══════════════════════════════════════════════════════════════

class CorrectionResult:
    def __init__(self, original, corrected, changes, valid, error=None):
        self.original  = original
        self.corrected = corrected
        self.changes   = changes          # list[str] – human-readable change descriptions
        self.valid     = valid
        self.error     = error            # reason if still invalid after correction


def auto_correct(expr: str) -> CorrectionResult:
    """
    Attempt to normalise a malformed Boolean expression.
    Returns a CorrectionResult with corrected expression and change log.

    Handles:
      lowercase vars        a & b            → A & B
      Python operators      A and B / A or B → A & B / A + B
      alternative AND       A * B            → A & B
      alternative OR        A || B           → A + B
      implicit AND          AB / A B         → A & B
      strip comments        A & B  # note    → A & B
      unclosed parens       (A & B           → (A & B)
    """
    original = expr
    changes  = []
    e = expr.strip()

    # 1. Strip inline comments
    if '#' in e:
        e = e[:e.index('#')].strip()
        changes.append("Stripped inline comment")

    # 2. Lowercase → uppercase variables (any letter)
    def _upper_vars(m):
        return m.group(0).upper()

    uppercased = re.sub(r'\b[a-z]\b', _upper_vars, e)
    if uppercased != e:
        e = uppercased
        changes.append("Uppercased variable names")

    # 3. Word operators → symbols  (order matters: 'not' before 'and'/'or')
    for word, sym in [(' not ', ' ! '), (' and ', ' & '), (' or ', ' + '),
                      (' AND ', ' & '), (' OR ',  ' + '), (' NOT ', ' ! ')]:
        if word in f' {e} ':
            e = re.sub(re.escape(word.strip()), sym.strip(), e, flags=re.IGNORECASE)
    # also handle word at end/start
    e = re.sub(r'\band\b',  '&', e, flags=re.IGNORECASE)
    e = re.sub(r'\bor\b',   '+', e, flags=re.IGNORECASE)
    e = re.sub(r'\bnot\b',  '!', e, flags=re.IGNORECASE)
    if any(w in original.lower() for w in ['and', 'or', 'not']):
        changes.append("Converted word operators (and/or/not) to symbols (&/+/!)")

    # 4. Alternate AND/OR symbols
    if '*' in e:
        e = e.replace('*', '&')
        changes.append("Replaced * with & (AND)")
    if '||' in e:
        e = e.replace('||', '+')
        changes.append("Replaced || with + (OR)")
    if '&&' in e:
        e = e.replace('&&', '&')
        changes.append("Replaced && with & (AND)")

    # 5. Implicit AND: adjacent uppercase letters without operator → insert &
    #    e.g. "AB" → "A & B", "A B" → "A & B"
    prev = e
    # letter immediately followed by letter
    e = re.sub(r'(?<=[A-Z])(?=[A-Z])', ' & ', e)
    # letter/closing-paren followed by letter/opening-paren without operator between
    e = re.sub(r'(?<=[A-Z\)])(\s*)(?=[A-Z(])',
               lambda m: ' & ' if not m.group(0).strip() else m.group(0), e)
    if e != prev:
        changes.append("Inserted missing & for implicit AND (e.g. AB → A & B)")

    # 6. Normalise whitespace
    e = re.sub(r'\s+', ' ', e).strip()

    # 7. Balance parentheses
    opens  = e.count('(')
    closes = e.count(')')
    if opens > closes:
        e += ')' * (opens - closes)
        changes.append(f"Added {opens - closes} missing closing parenthesis/es")
    elif closes > opens:
        e = '(' * (closes - opens) + e
        changes.append(f"Added {closes - opens} missing opening parenthesis/es")

    # 8. Validate the corrected expression
    try:
        vars_ = extract_variables(e)
        if not vars_:
            return CorrectionResult(original, e, changes, False, "No variables found")
        # Quick structural check via safe parser
        tokens = _tokenize(e)
        _Parser(tokens).parse_or()
        return CorrectionResult(original, e, changes, True)
    except Exception as ex:
        return CorrectionResult(original, e, changes, False, str(ex))


# ═══════════════════════════════════════════════════════════════
# SECTION 1 ─ SAFE AST-BASED EVALUATOR
# ═══════════════════════════════════════════════════════════════

def _tokenize(expr: str):
    """Tokenize Boolean expression into list of (type, value) tuples."""
    tokens, i = [], 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
        elif c.isupper():
            tokens.append(('VAR', c)); i += 1
        elif c in ('0', '1'):          # constant literal
            tokens.append(('CONST', int(c))); i += 1
        elif c == '&':
            tokens.append(('AND', '&')); i += 1
        elif c == '+':
            tokens.append(('OR', '+')); i += 1
        elif c == '!':
            tokens.append(('NOT', '!')); i += 1
        elif c == '(':
            tokens.append(('LP', '(')); i += 1
        elif c == ')':
            tokens.append(('RP', ')')); i += 1
        else:
            i += 1       # skip unknown chars silently
    return tokens


class _Parser:
    """Recursive-descent: OR > AND > NOT > atom.  Raises ValueError on bad input."""
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self, ttype=None):
        tok = self.tokens[self.pos]
        if ttype and tok[0] != ttype:
            raise ValueError(f"Expected {ttype}, got {tok}")
        self.pos += 1
        return tok

    def parse_or(self):
        left = self.parse_and()
        while self._peek() and self._peek()[0] == 'OR':
            self._consume('OR')
            left = ('OR', left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_not()
        while self._peek() and self._peek()[0] == 'AND':
            self._consume('AND')
            left = ('AND', left, self.parse_not())
        return left

    def parse_not(self):
        if self._peek() and self._peek()[0] == 'NOT':
            self._consume('NOT')
            return ('NOT', self.parse_atom())
        return self.parse_atom()

    def parse_atom(self):
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if tok[0] == 'VAR':
            self._consume('VAR')
            return ('VAR', tok[1])
        if tok[0] == 'CONST':          # handle '0' and '1' constants
            self._consume('CONST')
            return ('CONST', tok[1])
        if tok[0] == 'LP':
            self._consume('LP')
            node = self.parse_or()
            self._consume('RP')
            return node
        raise ValueError(f"Unexpected token: {tok}")


def _eval_tree(tree, assignment: Dict[str, int]) -> int:
    """Evaluate a parse tree given a variable assignment.  Returns 0 or 1."""
    if tree[0] == 'VAR':
        return assignment.get(tree[1], 0)
    if tree[0] == 'CONST':             # constant literal 0 or 1
        return tree[1]
    if tree[0] == 'NOT':
        return 1 - _eval_tree(tree[1], assignment)
    if tree[0] == 'AND':
        return _eval_tree(tree[1], assignment) & _eval_tree(tree[2], assignment)
    if tree[0] == 'OR':
        return _eval_tree(tree[1], assignment) | _eval_tree(tree[2], assignment)
    return 0


def safe_parse(expr: str):
    """Parse expression → tree or raise ValueError."""
    # Handle bare constants before tokenising
    stripped = expr.strip()
    if stripped == '1':
        return ('CONST', 1)
    if stripped == '0':
        return ('CONST', 0)
    tokens = _tokenize(stripped)
    if not tokens:
        raise ValueError("Empty expression")
    parser = _Parser(tokens)
    tree = parser.parse_or()
    if parser.pos < len(tokens):
        raise ValueError(f"Unexpected token near position {parser.pos}: {tokens[parser.pos]}")
    return tree


def safe_eval(expr: str, assignment: Dict[str, int]) -> int:
    """
    Safely evaluate expression string with assignment dict.
    NEVER calls Python's eval().  Uses AST parser internally.
    Returns 0 or 1.
    """
    tree = safe_parse(expr)
    return _eval_tree(tree, assignment)


# ═══════════════════════════════════════════════════════════════
# SECTION 2 ─ EXTRACTION + TRUTH TABLE
# ═══════════════════════════════════════════════════════════════

def extract_variables(expr: str) -> List[str]:
    return sorted(set(re.findall(r'[A-Z]', expr)))


def generate_truth_table(expr: str, variables: List[str], dont_cares: List[int]):
    """Returns (rows, on_set, off_set)."""
    n = len(variables)
    rows, on_set, off_set = [], [], []
    tree = safe_parse(expr)

    for i in range(2 ** n):
        assignment = {v: (i >> (n - 1 - j)) & 1 for j, v in enumerate(variables)}
        binary = format(i, f'0{n}b')

        if i in dont_cares:
            output = 'X'
        else:
            output = _eval_tree(tree, assignment)

        if output == 1:
            on_set.append(i)
        elif output == 0:
            off_set.append(i)

        row = {v: assignment[v] for v in variables}
        row['Binary']  = binary
        row['Minterm'] = f'm{i}'
        row['Output']  = output
        rows.append(row)

    return rows, on_set, off_set


# ═══════════════════════════════════════════════════════════════
# SECTION 3 ─ QUINE-McCLUSKEY (hash-indexed, XOR diff, early elim)
# ═══════════════════════════════════════════════════════════════

def popcount(n: int) -> int:
    return bin(n).count('1')


def term_to_binary(val: int, mask: int, n: int) -> str:
    s = ''
    for i in range(n - 1, -1, -1):
        if   (mask >> i) & 1: s += '-'
        elif (val  >> i) & 1: s += '1'
        else:                  s += '0'
    return s


def combine_terms(t1: Tuple, t2: Tuple) -> Optional[Tuple]:
    val1, mask1 = t1
    val2, mask2 = t2
    if mask1 != mask2:
        return None
    diff = (val1 ^ val2) & ~mask1
    if diff == 0 or (diff & (diff - 1)) != 0:
        return None
    return (val1 & ~diff, mask1 | diff)


def get_covered_minterms(term: Tuple, n: int) -> List[int]:
    val, mask = term
    return [i for i in range(2 ** n) if (i & ~mask) == (val & ~mask)]


def quine_mccluskey(minterms: List[int], dont_cares: List[int], n: int):
    """Returns (prime_implicants, steps)."""
    if not minterms:
        return [], []

    all_terms  = list(set(minterms + dont_cares))
    current    = set((m, 0) for m in all_terms)
    all_primes = set()
    steps      = []
    iteration  = 0

    while current:
        iteration += 1
        groups: Dict[int, list] = {}
        for term in current:
            val, mask = term
            ones = popcount(val & ~mask)
            groups.setdefault(ones, []).append(term)

        step = {'iteration': iteration,
                'groups': {k: list(v) for k, v in sorted(groups.items())},
                'merges': [], 'primes_found': []}

        used       = set()
        next_terms = set()
        sorted_k   = sorted(groups.keys())

        for i in range(len(sorted_k) - 1):
            for t1 in groups[sorted_k[i]]:
                for t2 in groups[sorted_k[i + 1]]:
                    combined = combine_terms(t1, t2)
                    if combined is not None:
                        next_terms.add(combined)
                        used.add(t1); used.add(t2)
                        step['merges'].append((t1, t2, combined))

        primes_this = current - used
        all_primes.update(primes_this)
        step['primes_found'] = list(primes_this)
        steps.append(step)
        current = next_terms

    prime_implicants = [
        pi for pi in all_primes
        if any(m in minterms for m in get_covered_minterms(pi, n))
    ]
    return prime_implicants, steps


# ═══════════════════════════════════════════════════════════════
# SECTION 4 ─ K-MAP HTML BUILDER
# ═══════════════════════════════════════════════════════════════

GRAY_2 = [0, 1, 3, 2]
GRAY_1 = [0, 1]


def build_kmap_html(minterms: List[int], dont_cares: List[int],
                    variables: List[str]) -> str:
    n = len(variables)
    if n < 2 or n > 4:
        return ""

    if n == 2:
        row_vars, col_vars = variables[:1], variables[1:]
        row_idx,  col_idx  = GRAY_1, GRAY_1
    elif n == 3:
        row_vars, col_vars = variables[:1], variables[1:]
        row_idx,  col_idx  = GRAY_1, GRAY_2
    else:
        row_vars, col_vars = variables[:2], variables[2:]
        row_idx,  col_idx  = GRAY_2, GRAY_2

    n_row, n_col = len(row_vars), len(col_vars)
    row_labels   = [format(r, f'0{n_row}b') for r in row_idx]
    col_labels   = [format(c, f'0{n_col}b') for c in col_idx]

    H  = "<table style='border-collapse:collapse;font-family:\"JetBrains Mono\",monospace;margin:1rem 0'>"
    H += (f"<tr><th style='padding:10px 14px;border:1px solid #444;background:#1a1a2e;"
          f"color:#8888a0;font-size:11px'>{''.join(row_vars)}\\{''.join(col_vars)}</th>")
    for cl in col_labels:
        H += f"<th style='padding:10px 16px;border:1px solid #444;background:#1a1a2e;color:#14b8a6'>{cl}</th>"
    H += "</tr>"

    for r, rl in zip(row_idx, row_labels):
        H += f"<tr><th style='padding:10px 16px;border:1px solid #444;background:#1a1a2e;color:#14b8a6'>{rl}</th>"
        for c in col_idx:
            idx = (r << n_col) | c
            if idx in minterms:
                bg, fg, val = "#052e16", "#22c55e", "1"
            elif idx in dont_cares:
                bg, fg, val = "#1c1400", "#f59e0b", "X"
            else:
                bg, fg, val = "#12121a", "#4a4a60", "0"
            H += (f"<td style='padding:14px 20px;border:1px solid #333;background:{bg};"
                  f"color:{fg};text-align:center;font-size:18px;font-weight:700'>"
                  f"<span title='m{idx}'>{val}</span></td>")
        H += "</tr>"
    H += "</table>"
    return H


# ═══════════════════════════════════════════════════════════════
# SECTION 5 ─ PETRICK'S METHOD (essential + greedy)
# ═══════════════════════════════════════════════════════════════

def petricks_method(prime_implicants: List[Tuple],
                    minterms: List[int], n: int):
    """Returns (selected_pis, coverage_table, essential_indices)."""
    if not prime_implicants or not minterms:
        return [], {}, []

    coverage = {
        m: [i for i, pi in enumerate(prime_implicants)
            if m in get_covered_minterms(pi, n)]
        for m in minterms
    }

    essential_idx        = []
    covered_by_essential = set()
    for m, pi_list in coverage.items():
        if len(pi_list) == 1:
            idx = pi_list[0]
            if idx not in essential_idx:
                essential_idx.append(idx)
            covered_by_essential.update(get_covered_minterms(prime_implicants[idx], n))

    selected  = list(essential_idx)
    remaining = [m for m in minterms if m not in covered_by_essential]

    while remaining:
        best_idx, best_count = None, 0
        for i, pi in enumerate(prime_implicants):
            if i in selected:
                continue
            count = sum(1 for m in remaining if m in get_covered_minterms(pi, n))
            if count > best_count:
                best_count, best_idx = count, i
        if best_idx is None:
            break
        selected.append(best_idx)
        new_covered = get_covered_minterms(prime_implicants[best_idx], n)
        remaining   = [m for m in remaining if m not in new_covered]

    return [prime_implicants[i] for i in selected], coverage, essential_idx


# ═══════════════════════════════════════════════════════════════
# SECTION 6 ─ EXPRESSION BUILDER
# ═══════════════════════════════════════════════════════════════

def term_to_str(term: Tuple, variables: List[str]) -> str:
    """Convert (value, mask) term to readable Boolean string with explicit & operators.
    Always uses ' & ' so the safe_eval parser can tokenize correctly.
    """
    val, mask = term
    n     = len(variables)
    parts = []
    for i, var in enumerate(variables):
        bit = n - 1 - i
        if   (mask >> bit) & 1: continue           # don't-care — omit
        elif (val  >> bit) & 1: parts.append(var)  # literal 1
        else:                   parts.append(f'!{var}')  # literal 0
    if not parts:
        return '1'
    if len(parts) == 1:
        return parts[0]
    return ' & '.join(parts)


def build_expression_from_pis(pis: List[Tuple], variables: List[str]) -> str:
    """Join prime implicant terms into a sum-of-products expression.
    Multi-literal terms are wrapped in parentheses for clarity.
    """
    if not pis:
        return '0'
    terms = []
    for pi in pis:
        t = term_to_str(pi, variables)
        if ' & ' in t:
            terms.append(f'({t})')
        else:
            terms.append(t)
    return ' + '.join(terms)


# ═══════════════════════════════════════════════════════════════
# SECTION 7 ─ METRICS + FACTORING
# ═══════════════════════════════════════════════════════════════

def compute_metrics(expr: str) -> Dict:
    and_count = expr.count('&')
    or_count  = expr.count('+')
    not_count = expr.count('!')

    depth = max_depth = 0
    for ch in expr:
        if ch == '(':
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == ')':
            depth -= 1
    if max_depth == 0 and (and_count + or_count) > 0:
        max_depth = 1

    terms      = max(1, len(expr.split('+')))
    total_ops  = and_count + or_count + not_count
    cost       = and_count * 2 + or_count * 1 + not_count * 3
    complexity = 2 * and_count + 2 * or_count + 1 * not_count + 3 * max_depth + 2 * terms

    return {
        'and': and_count, 'or': or_count, 'not': not_count,
        'depth': max_depth, 'terms': terms, 'total_ops': total_ops,
        'cost': cost, 'complexity': complexity, 'length': len(expr)
    }


def try_factor_expression(expr: str) -> str:
    """Factor common literals from sum-of-products; returns cheapest form.
    Works with both 'A & B + A & C' and '(A & B) + (A & C)' forms.
    """
    # Split on '+' to get product terms
    raw_terms = [t.strip().strip('()') for t in expr.split('+')]
    terms = [t.strip() for t in raw_terms if t.strip()]
    if len(terms) < 2:
        return expr

    # Extract literals from each term (split on '&')
    def _lits(t):
        return [l.strip() for l in t.split('&') if l.strip()]

    term_literals = [_lits(t) for t in terms]

    # Find literals common to ALL terms (preserving order)
    common_set = set(term_literals[0])
    for ls in term_literals[1:]:
        common_set &= set(ls)

    if not common_set:
        return expr

    # Stable-sort: non-NOT first, then alphabetical
    common_sorted = sorted(common_set, key=lambda x: (x.startswith('!'), x.lstrip('!')))
    common_str = ' & '.join(common_sorted)

    # Build remainders by removing common literals from each term
    remainders = []
    for lits in term_literals:
        rest = [l for l in lits if l not in common_set]
        remainders.append(' & '.join(rest) if rest else '1')

    if all(r == '1' for r in remainders):
        return common_str

    inner = ' + '.join(f'({r})' if ' & ' in r else r for r in remainders)
    factored = f'{common_str} & ({inner})'

    return factored if compute_metrics(factored)['cost'] < compute_metrics(expr)['cost'] else expr


# ═══════════════════════════════════════════════════════════════
# SECTION 8 ─ FIRMWARE CODE GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_c_code(expr: str, var_map: Dict[str, str],
                    label: str = "Optimized") -> str:
    code = expr.strip()
    code = re.sub(r'\s*\+\s*', ' || ', code)
    code = re.sub(r'\s*&\s*', ' && ', code)
    for var in sorted(var_map.keys(), key=lambda x: -len(x)):
        code = re.sub(r'\b' + re.escape(var) + r'\b', var_map[var], code)
    code = re.sub(r'\s+', ' ', code).strip()

    return f"""/* =====================================================
 * AURA – Pillar 4: Firmware Logic Optimization Engine
 * {label} conditional logic (auto-generated)
 * ===================================================== */

#include <stdint.h>

/* Source: {expr} */
static inline uint8_t evaluate_ssd_condition(void) {{

    if ({code}) {{
        execute_operation();
        return 1U;   /* condition met */
    }}

    return 0U;       /* condition not met */
}}"""


# ═══════════════════════════════════════════════════════════════
# SECTION 9 ─ BUILT-IN TEST CASES
# ═══════════════════════════════════════════════════════════════

BUILTIN_TESTS = [
    {
        "label":       "Basic factoring",
        "expr":        "(A & B & C) + (A & B & D)",
        "dont_cares":  [],
        "expected_simplified": "AB(C + D)",   # expected pattern (informational)
        "description": "Classic 4-variable factoring. A & B is common → factors out.",
    },
    {
        "label":       "Redundant term (subsumption)",
        "expr":        "(A & B) + (A & B & C)",
        "dont_cares":  [],
        "expected_simplified": "AB",
        "description": "AB subsumes AB&C — the longer term is redundant.",
    },
    {
        "label":       "Complement pair → tautology",
        "expr":        "A + !A",
        "dont_cares":  [],
        "expected_simplified": "1",
        "description": "A + !A is always true. Minimizes to tautology.",
    },
    {
        "label":       "Don't-care expansion",
        "expr":        "(A & B & C) + (A & !B & C)",
        "dont_cares":  [7],
        "expected_simplified": "AC",
        "description": "Adding m7 as don't-care allows B to be eliminated.",
    },
    {
        "label":       "DeMorgan reduction",
        "expr":        "(!A & !B) + (!A & B) + (A & !B)",
        "dont_cares":  [],
        "expected_simplified": "!A + !B",
        "description": "Three-term expression reduces to two-term via DeMorgan.",
    },
]