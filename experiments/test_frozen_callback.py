#!/usr/bin/env python3
"""
Test script to verify that we don't modify frozen CallbackQuery attributes
"""

import ast
import sys

def check_frozen_attribute_modification(filename):
    """Check if code tries to modify callback.data"""
    with open(filename, 'r') as f:
        tree = ast.parse(f.read(), filename)

    violations = []

    for node in ast.walk(tree):
        # Check for assignments like callback.data = ...
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if isinstance(target.value, ast.Name):
                        if target.value.id == 'callback' and target.attr == 'data':
                            violations.append((node.lineno, "callback.data assignment"))

    return violations

if __name__ == "__main__":
    violations = check_frozen_attribute_modification("/tmp/gh-issue-solver-1766308723022/handlers.py")

    if violations:
        print("❌ Found violations:")
        for line, msg in violations:
            print(f"  Line {line}: {msg}")
        sys.exit(1)
    else:
        print("✅ No frozen attribute modifications found")
        sys.exit(0)
