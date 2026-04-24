"""Human-readable error formatters for Pydantic validation and YAML parse errors."""
from pydantic import ValidationError


def format_validation_error(e: ValidationError, artifact_path: str) -> str:
    """Transform a Pydantic ValidationError into a hook-friendly explanatory block."""
    lines = [
        "═══════════════════════════════════════════════════════════════════",
        f" VALIDATION FAILED: {artifact_path}",
        f" {len(e.errors())} issue(s) found. Fix each and re-validate.",
        "═══════════════════════════════════════════════════════════════════",
        "",
    ]
    for i, err in enumerate(e.errors(), 1):
        path = ".".join(str(p) for p in err["loc"])
        lines.append(f"[{i}] Field:    {path}")
        lines.append(f"    Problem:  {err['msg']}")
        lines.append(f"    Got:      {err.get('input', '<unavailable>')!r}")
        if err["type"] == "literal_error":
            lines.append(f"    Expected: one of {err.get('ctx', {}).get('expected', '?')}")
        elif err["type"] == "missing":
            lines.append(f"    Expected: this field is required")
        if path == "schema_version" and err["type"] == "missing":
            lines.append(
                f"    Hint:     Add `schema_version: 1` as the first line of your YAML frontmatter."
            )
        lines.append("")
    lines.append("═══════════════════════════════════════════════════════════════════")
    return "\n".join(lines)


def format_yaml_error(yaml_err: Exception, artifact_path: str) -> str:
    """YAML parse errors use a distinct block -- separate layer from Pydantic."""
    lines = [
        "═══════════════════════════════════════════════════════════════════",
        f" YAML PARSE FAILED: {artifact_path}",
        " Your YAML frontmatter is syntactically invalid.",
        " Pydantic validation was not attempted — fix the YAML first.",
        "═══════════════════════════════════════════════════════════════════",
        "",
        f"  {type(yaml_err).__name__}: {yaml_err}",
        "",
        "═══════════════════════════════════════════════════════════════════",
    ]
    return "\n".join(lines)
