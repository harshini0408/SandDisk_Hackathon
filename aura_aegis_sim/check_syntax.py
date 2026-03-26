"""Compile-check all .py files in the project and report any syntax errors."""
import sys, os, py_compile, glob

root = os.path.dirname(os.path.abspath(__file__))
errors = []
ok = 0

# Check all Python files recursively, skip __pycache__
for path in sorted(glob.glob(os.path.join(root, '**', '*.py'), recursive=True)):
    if '__pycache__' in path:
        continue
    rel = os.path.relpath(path, root)
    try:
        py_compile.compile(path, doraise=True)
        ok += 1
    except py_compile.PyCompileError as e:
        errors.append((rel, str(e)))

print(f"\nCompile check complete: {ok} OK, {len(errors)} error(s)\n")
if errors:
    for rel, msg in errors:
        print(f"  FAIL  {rel}")
        # Print just the key line of the error message
        for line in msg.splitlines():
            if line.strip():
                print(f"        {line.strip()}")
        print()
    sys.exit(1)
else:
    print("  All files compile successfully.")
    sys.exit(0)
