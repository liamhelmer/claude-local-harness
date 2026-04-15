"""Security scanner for catalog components.

Scans component content against known suspicious patterns and returns
a SecurityVerdict indicating whether the content is safe to catalog.
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SecurityVerdict:
    is_safe: bool
    findings: List[str] = field(default_factory=list)
    component_name: str = ""


# Each tuple: (regex_pattern, description, severity)
# severity is "critical" or "warning"
SUSPICIOUS_PATTERNS: List[Tuple[str, str, str]] = [
    # Code execution
    (r"\beval\s*\(", "eval() call detected — arbitrary code execution", "critical"),
    (r"\bexec\s*\(", "exec() call detected — arbitrary code execution", "critical"),
    # Pipe-to-shell patterns
    (r"curl\b.*\|\s*bash", "curl piped to bash — remote code execution", "critical"),
    (r"wget\b.*\|\s*bash", "wget piped to bash — remote code execution", "critical"),
    (
        r"base64\s+--decode\s*\|\s*(sh|bash)",
        "base64 decode piped to shell — obfuscated code execution",
        "critical",
    ),
    # Env-var exfiltration via HTTP
    (
        r"(curl|wget|http|https).*\$\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)\b",
        "HTTP request containing sensitive env var — potential exfiltration",
        "critical",
    ),
    # Known API key references
    (r"ANTHROPIC_API_KEY", "Reference to ANTHROPIC_API_KEY", "warning"),
    (r"OPENAI_API_KEY", "Reference to OPENAI_API_KEY", "warning"),
    (r"AWS_SECRET", "Reference to AWS_SECRET", "warning"),
    # Dangerous flags
    (
        r"--dangerously-skip-permissions",
        "--dangerously-skip-permissions flag — bypasses safety controls",
        "critical",
    ),
    (r"--no-verify", "--no-verify flag — skips verification hooks", "warning"),
    # Paste service raw URLs
    (
        r"(pastebin\.com|hastebin\.com|ghostbin\.com|paste\.ee)/raw/",
        "Paste service raw URL — potential obfuscated payload",
        "critical",
    ),
    # Direct IP address URLs
    (
        r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        "Direct IP address URL — potential C2 or exfiltration endpoint",
        "warning",
    ),
    # Destructive filesystem operations
    (
        r"rm\s+-rf\s+(/|~|\$HOME)\b",
        "rm -rf targeting root, home, or $HOME — destructive filesystem operation",
        "critical",
    ),
    # Insecure permissions
    (r"chmod\s+777", "chmod 777 — world-writable permissions", "warning"),
    # Network backdoors
    (r"nc\s+-l", "netcat listener — potential backdoor", "critical"),
    (
        r"/dev/tcp/",
        "/dev/tcp/ — bash network socket — potential data exfiltration",
        "critical",
    ),
]


def scan_component(content: str, comp_type: str, comp_name: str) -> SecurityVerdict:
    """Scan component content against all suspicious patterns.

    Args:
        content: The raw text content to scan.
        comp_type: Component type (e.g. "skill", "agent", "hook").
        comp_name: Human-readable component name.

    Returns:
        SecurityVerdict with is_safe flag and list of findings.
    """
    findings: List[str] = []
    critical_count = 0
    warning_count = 0

    for pattern, description, severity in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            tag = severity.upper()
            findings.append(f"[{tag}] {description}")
            if severity == "critical":
                critical_count += 1
            else:
                warning_count += 1

    is_safe = critical_count == 0 and warning_count < 3

    return SecurityVerdict(
        is_safe=is_safe,
        findings=findings,
        component_name=comp_name,
    )
