"""Canonical YAML-1.1 coercion cases for handoff_spawn / spawn_policy (N83).

Ground truth captured 2026-08-04 against PyYAML 6.0.3 (yaml.safe_load).
Each entry: (raw_yaml_scalar, expected_python_value_after_safe_load).
"""

# What `handoff_spawn: <raw>` yields from yaml.safe_load, BEFORE any coercion.
YAML_SCALAR_CASES = [
    ("off", False),      # unquoted -> YAML 1.1 bool False  (the footgun)
    ('"off"', "off"),    # quoted   -> string, unchanged
    ("on", True),        # unquoted -> YAML 1.1 bool True    (invalid mode)
    ("auto", "auto"),
    ("ask", "ask"),
]

# What the coercion validators must produce from the parsed python value.
# False -> "off"; True -> ValueError; strings pass through unchanged.
COERCION_EXPECTATIONS = [
    (False, "off"),
    ("off", "off"),
    ("auto", "auto"),
    ("ask", "ask"),
    # True is handled separately (must raise), not in this pass-through table.
]
