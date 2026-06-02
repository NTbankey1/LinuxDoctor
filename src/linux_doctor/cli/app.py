"""CLI interface for Linux Doctor Hybrid AI."""

from __future__ import annotations

import sys

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from linux_doctor.domain.models import Diagnosis, Session
from linux_doctor.engines.rule_engine import RuleEngine
from linux_doctor.infrastructure.kb_loader import KnowledgeBaseLoader

console = Console()

# Keyword fallback map (used if ML model not trained yet or low confidence)
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "docker":  ["docker", "container", "daemon", "docker.sock", "overlay2"],
    "nginx":   ["nginx", "vhost", "upstream", "proxy_pass", "sites-enabled"],
    "ssh":     ["ssh", "sshd", "publickey", "authorized_keys", "port 22"],
    "disk":    ["disk", "space left", "inode", "filesystem", "df -h", "mount"],
    "memory":  ["memory", "oom", "swap", "ram", "malloc", "out of memory"],
    "cpu":     ["cpu", "load average", "top", "htop", "process", "zombie"],
    "network": ["network", "unreachable", "firewall", "iptables", "ufw", "route"],
    "dns":     ["dns", "nslookup", "dig", "resolv", "nxdomain", "nameserver"],
    "git":     ["git", "push rejected", "merge conflict", "github", "gitlab"],
    "systemd": ["systemd", "systemctl", "journalctl", "service", "unit file"],
    "permission": ["permission", "access denied", "chmod", "chown", "sudo", "selinux"],
    "package": ["apt", "yum", "dnf", "pip", "package", "dependency", "dpkg"],
}


def _keyword_route(query: str) -> str | None:
    """Fallback keyword-based domain detection."""
    q = query.lower()
    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in q)
        if hits:
            scores[domain] = hits
    return max(scores, key=scores.__getitem__) if scores else None


def _detect_domain(query: str) -> tuple[str | None, float, str]:
    """
    Detect domain using ML classifier with keyword fallback.

    Returns:
        (domain, confidence, method)
    """
    try:
        from linux_doctor.ml.predictor import CONFIDENCE_THRESHOLD, IssueClassifier
        classifier = IssueClassifier()
        pred = classifier.predict(query)

        # Always prefer keyword match for short/ambiguous queries
        fallback = _keyword_route(query)
        keyword_override = False
        if fallback and pred.domain != fallback:
            # Keyword domain differs from ML domain — use fallback if:
            # 1. ML confidence is low (< 50%), OR
            # 2. Query contains explicit domain keyword
            query_lower = query.lower()
            if pred.confidence < 0.50 or fallback in query_lower:
                keyword_override = True

        if keyword_override:
            return fallback, pred.confidence, f"Keyword Override (ML said {pred.domain})"

        if pred.confidence >= CONFIDENCE_THRESHOLD:
            return pred.domain, pred.confidence, "ML Classifier"
        # Low confidence — try keyword fallback
        if fallback:
            return fallback, pred.confidence, "Keyword Fallback (low ML confidence)"
        return pred.domain, pred.confidence, "ML Classifier (low confidence)"
    except FileNotFoundError:
        domain = _keyword_route(query)
        return domain, 0.0, "Keyword Fallback (model not trained)"
    except Exception:
        domain = _keyword_route(query)
        return domain, 0.0, "Keyword Fallback"


def _print_header() -> None:
    console.print(Panel.fit(
        "[bold cyan]🐧 LINUX DOCTOR — Hybrid AI Troubleshooting[/bold cyan]\n"
        "[dim]Classical AI · No LLMs · 3 ML Algorithms from Scratch[/dim]",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
    ))


_HELP_TEXT = """[bold cyan]Usage:[/bold cyan]
  [yellow]linux-doctor "your problem description"[/yellow]
  [yellow]linux-doctor --help[/yellow]

[bold]Examples:[/bold]
  [dim]$ linux-doctor "nginx failed to start"[/dim]
  [dim]$ linux-doctor "disk is full on /var"[/dim]
  [dim]$ linux-doctor "port 80 already in use"[/dim]

[bold]Supported domains:[/bold] [cyan]docker, nginx, ssh, disk, memory, cpu, network, dns, git, systemd, permission, package[/cyan]

[bold]Notes:[/bold]
  - Describe your problem naturally, mention the service name
  - Run without arguments to start the interactive REPL
  - Confidence is shown as a percentage next to the domain"""


def _print_diagnosis(diagnosis: Diagnosis, domain: str, confidence: float, method: str) -> None:
    """Print formatted diagnosis report."""
    console.print()

    # Detection summary
    conf_color = "green" if confidence >= 0.7 else "yellow" if confidence >= 0.4 else "dim"
    console.print(f"[bold]Domain:[/bold]     [cyan]{domain.upper()}[/cyan]")
    if confidence > 0:
        console.print(f"[bold]Confidence:[/bold] [{conf_color}]{confidence*100:.1f}%[/{conf_color}]  [dim]({method})[/dim]")
    else:
        console.print(f"[bold]Routing:[/bold]    [dim]{method}[/dim]")

    # Root cause panel
    console.print(Panel(
        f"[bold red]{diagnosis.root_cause}[/bold red]",
        title="[bold]🔍 Root Cause Identified[/bold]",
        border_style="red",
    ))
    console.print(f"[dim]Rule: {diagnosis.explanation}[/dim]")

    # Recommended fixes
    if diagnosis.recommended_fixes:
        table = Table(
            title="🔧 Recommended Actions",
            box=box.ROUNDED,
            border_style="green",
            show_lines=True,
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Command", style="bold yellow", min_width=35)
        table.add_column("Explanation")
        table.add_column("Safe?", width=6, justify="center")

        for i, fix in enumerate(diagnosis.recommended_fixes, 1):
            safe_icon = "✅" if fix.is_safe_to_auto_run else "⚠️ "
            table.add_row(str(i), fix.command, fix.explanation, safe_icon)

        console.print()
        console.print(table)


def run(query: str | None = None) -> None:
    """Main entrypoint for the Linux Doctor CLI.

    - With argument: one-shot diagnosis
    - Without argument: start interactive REPL agent
    """
    # If called via command line (e.g., `linux-doctor "nginx failed"`)
    if not query and len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    if not query:
        # Start interactive REPL
        from linux_doctor.interfaces.cli.repl import main as repl_main
        repl_main()
        return

    # Intercept help flags before treating as diagnosis queries
    if query.strip() in ("--help", "-h", "help"):
        console.print(_HELP_TEXT)
        return

    console.print(f"\n[dim]Query:[/dim] '{query}'")

    # Step 1: Detect domain
    domain, confidence, method = _detect_domain(query)
    if not domain:
        console.print(Panel(
            "[yellow]Could not identify the service or domain.\n"
            "Try mentioning the service name (e.g., 'docker', 'nginx', 'ssh').[/yellow]",
            title="Unknown Domain",
            border_style="yellow",
        ))
        return

    conf_str = f" ({confidence*100:.0f}%)" if confidence > 0 else ""
    console.print(f"[green]✓ Domain:[/green] [bold]{domain.upper()}[/bold]{conf_str}  [dim]{method}[/dim]")

    # Step 2: Load KB
    loader = KnowledgeBaseLoader()
    kb = loader.load_domain(domain)
    if not kb:
        console.print(f"[yellow]No Knowledge Base for domain '{domain}'. "
                      f"Available: {loader.list_available_domains()}[/yellow]")
        return

    # Step 3: Run Rule Engine
    session = Session(user_query=query)
    engine = RuleEngine(kb=kb)
    diagnosis = engine.diagnose(session)

    # Step 4: Display
    if diagnosis:
        _print_diagnosis(diagnosis, domain, confidence, method)
    else:
        console.print(Panel(
            "[yellow]The expert system matched the domain but could not confirm a specific root cause.\n"
            "Please provide the exact error message from your terminal for better results.[/yellow]",
            title="⚠ No Root Cause Confirmed",
            border_style="yellow",
        ))


if __name__ == "__main__":
    run()
