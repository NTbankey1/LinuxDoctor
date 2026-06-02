"""CLI interface for Linux Doctor Hybrid AI — Mission Control 3-Column Layout."""

from __future__ import annotations

import sys

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from linux_doctor.domain.models import Diagnosis, Session
from linux_doctor.engines.rule_engine import RuleEngine
from linux_doctor.infrastructure.kb_loader import KnowledgeBaseLoader

console = Console()

# ──────────────────────────────────────────────────────────────────────────────
# Keyword fallback map
# ──────────────────────────────────────────────────────────────────────────────
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "docker":     ["docker", "container", "daemon", "docker.sock", "overlay2"],
    "nginx":      ["nginx", "vhost", "upstream", "proxy_pass", "sites-enabled"],
    "ssh":        ["ssh", "sshd", "publickey", "authorized_keys", "port 22"],
    "disk":       ["disk", "space left", "inode", "filesystem", "df -h", "mount"],
    "memory":     ["memory", "oom", "swap", "ram", "malloc", "out of memory"],
    "cpu":        ["cpu", "load average", "top", "htop", "process", "zombie"],
    "network":    ["network", "unreachable", "firewall", "iptables", "ufw", "route"],
    "dns":        ["dns", "nslookup", "dig", "resolv", "nxdomain", "nameserver"],
    "git":        ["git", "push rejected", "merge conflict", "github", "gitlab"],
    "systemd":    ["systemd", "systemctl", "journalctl", "service", "unit file"],
    "permission": ["permission", "access denied", "chmod", "chown", "sudo", "selinux"],
    "package":    ["apt", "yum", "dnf", "pip", "package", "dependency", "dpkg"],
}


def _keyword_route(query: str) -> str | None:
    q = query.lower()
    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in q)
        if hits:
            scores[domain] = hits
    return max(scores, key=scores.__getitem__) if scores else None


def _detect_domain(query: str) -> tuple[str | None, float, str]:
    try:
        from linux_doctor.ml.predictor import CONFIDENCE_THRESHOLD, IssueClassifier
        classifier = IssueClassifier()
        pred = classifier.predict(query)
        fallback = _keyword_route(query)
        keyword_override = False
        if fallback and pred.domain != fallback:
            query_lower = query.lower()
            if pred.confidence < 0.50 or fallback in query_lower:
                keyword_override = True
        if keyword_override:
            return fallback, pred.confidence, f"Keyword Override (ML→{pred.domain})"
        if pred.confidence >= CONFIDENCE_THRESHOLD:
            return pred.domain, pred.confidence, "ML Classifier"
        if fallback:
            return fallback, pred.confidence, "Keyword Fallback"
        return pred.domain, pred.confidence, "ML (low conf)"
    except FileNotFoundError:
        return _keyword_route(query), 0.0, "Keyword Fallback"
    except Exception:
        return _keyword_route(query), 0.0, "Keyword Fallback"


_HELP_TEXT = """[bold cyan]Usage:[/bold cyan]
  [yellow]linux-doctor "your problem description"[/yellow]
  [yellow]linux-doctor --help[/yellow]

[bold]Examples:[/bold]
  [dim]$ linux-doctor "nginx failed to start"[/dim]
  [dim]$ linux-doctor "disk is full on /var"[/dim]
  [dim]$ linux-doctor "port 80 already in use"[/dim]

[bold]Supported domains:[/bold]
  [cyan]docker  nginx  ssh  disk  memory  cpu
  network  dns  git  systemd  permission  package[/cyan]"""


# ──────────────────────────────────────────────────────────────────────────────
# Visual helpers
# ──────────────────────────────────────────────────────────────────────────────

def _conf_bar(val: float, width: int = 14) -> str:
    filled = int(val * width)
    bar = "█" * filled + "░" * (width - filled)
    color = "bold green" if val >= 0.8 else "bold yellow" if val >= 0.5 else "bold red"
    return f"[{color}]{bar}[/{color}] [bold]{val * 100:.0f}%[/bold]"


def _risk_badge(is_safe: bool) -> str:
    return "[bold green]✅ LOW[/bold green]" if is_safe else "[bold dark_orange]⚠ MOD[/bold dark_orange]"


def _shorten(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


# ──────────────────────────────────────────────────────────────────────────────
# Column builders (each returns a Rich renderable)
# ──────────────────────────────────────────────────────────────────────────────

def _col_causal_tree(session: Session, domain: str) -> Panel:
    """Column 1 — Causal Tree."""
    tree = Tree(
        f"[bold red]🔴 {domain.upper()}[/bold red]",
        guide_style="bright_blue",
    )
    q_node = tree.add(
        f"[bold yellow]Symptom[/bold yellow]\n[italic dim]{session.user_query}[/italic dim]"
    )

    if session.facts:
        ev = q_node.add("[bold cyan]Evidence[/bold cyan]")
        for f in session.facts:
            ev.add(
                f"[dim]{f.key}[/dim]\n"
                f"[bold bright_cyan]{f.value}[/bold bright_cyan]"
            )

    rc = q_node.add("[bold magenta]Root Cause[/bold magenta]")
    conf_bar = _conf_bar(session.diagnosis.confidence, width=14)
    rc.add(
        f"[bold red]{session.diagnosis.root_cause}[/bold red]\n"
        f"[dim]Conf:[/dim] {conf_bar}"
    )

    return Panel(
        tree,
        title="[bold cyan]① CAUSAL TREE[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
    )


def _col_ai_reasoning(session: Session) -> Panel:
    """Column 2 — AI Reasoning Stream."""
    from linux_doctor.engines.reasoning_chain import ReasoningChain

    if not session.reasoning_chain or not session.reasoning_chain.steps:
        return Panel(
            Text("No reasoning data.", style="dim"),
            title="[bold magenta]② AI REASONING[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED,
        )

    items: list[Panel | Text] = []
    for step in session.reasoning_chain.steps:
        icon      = ReasoningChain._icon_for_type(step.step_type)
        time_str  = step.timestamp.strftime("%H:%M:%S")
        outcome   = ""
        if step.output_data:
            for k, v in step.output_data.items():
                if v and k != "command":
                    outcome = _shorten(str(v), 22)
                    break
        desc = _shorten(step.description, 26)
        row = Text()
        row.append(f"{time_str} ", style="dim")
        row.append(f"{icon} ", style="")
        row.append(desc, style="white")
        if outcome:
            row.append(f"\n   └ ", style="dim")
            row.append(outcome, style="bright_cyan")
        items.append(row)

    return Panel(
        Group(*items),
        title="[bold magenta]② AI REASONING[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
    )


def _col_action_cards(diagnosis: Diagnosis) -> Panel:
    """Column 3 — Action Cards. Commands shown in full (no truncation)."""
    if not diagnosis.recommended_fixes:
        return Panel(
            Text("No actions available.", style="dim"),
            title="[bold green]③ ACTION CARDS[/bold green]",
            border_style="green",
            box=box.ROUNDED,
        )

    cards = []
    for i, fix in enumerate(diagnosis.recommended_fixes, 1):
        badge = _risk_badge(fix.is_safe_to_auto_run)

        card_tbl = Table(show_header=False, show_edge=False, box=None, padding=(0, 0))
        card_tbl.add_column("key", style="bold dim", width=5, no_wrap=True)
        # overflow="fold" wraps long commands onto next line instead of cutting
        card_tbl.add_column("val", overflow="fold")
        card_tbl.add_row("Risk", badge)
        card_tbl.add_row("Cmd",  f"[bold yellow]{fix.command}[/bold yellow]")
        card_tbl.add_row("Why",  f"[dim]{fix.explanation}[/dim]")

        cards.append(Panel(
            card_tbl,
            title=f"[bold green]Action {i}[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 1),
        ))

    return Panel(
        Group(*cards),
        title="[bold green]③ ACTION CARDS[/bold green]",
        border_style="green",
        box=box.ROUNDED,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Main diagnosis printer
# ──────────────────────────────────────────────────────────────────────────────

def _print_diagnosis(session: Session, domain: str, confidence: float, method: str) -> None:
    """3-Column Mission Control layout."""
    from rich.layout import Layout

    console.print()

    # ── Top Header ────────────────────────────────────────────────────────────
    conf_color = "green" if confidence >= 0.7 else "yellow" if confidence >= 0.4 else "red"
    # Two-line header: brand on first line, meta on second — avoids truncation
    header_text = (
        f"[bold bright_white]🐧 LINUX DOCTOR[/bold bright_white]  "
        f"[dim]Mission Control · AI-Native Incident Response[/dim]\n"
        f"[dim]Domain[/dim] [bold cyan]{domain.upper()}[/bold cyan]   "
        f"[{conf_color}]{confidence * 100:.1f}%[/{conf_color}]  "
        f"[dim]{method}[/dim]"
    )
    console.print(Panel(header_text, border_style="bright_blue", box=box.HEAVY))
    console.print(f"\n  [dim]›[/dim] [italic white]{session.user_query}[/italic white]\n")

    # ── 3-Column Body ─────────────────────────────────────────────────────────
    layout = Layout()
    layout.split_row(
        Layout(name="col1", ratio=1),
        Layout(name="col2", ratio=1),
        Layout(name="col3", ratio=1),
    )

    layout["col1"].update(_col_causal_tree(session, domain))
    layout["col2"].update(_col_ai_reasoning(session))
    layout["col3"].update(_col_action_cards(session.diagnosis))

    # Auto-size height: count rows needed
    n_steps  = len(session.reasoning_chain.steps) if session.reasoning_chain else 0
    n_facts  = len(session.facts)
    n_fixes  = len(session.diagnosis.recommended_fixes)
    height   = max(n_steps * 2 + 6, n_facts * 2 + 8, n_fixes * 6 + 6, 22)
    layout.size = height  # type: ignore[assignment]

    console.print(layout)
    console.print()


# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────────────────────────────────────

def run(query: str | None = None) -> None:
    """Main entrypoint for Linux Doctor CLI."""
    if not query and len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    if not query:
        from linux_doctor.interfaces.cli.repl import main as repl_main
        repl_main()
        return

    if query.strip() in ("--help", "-h", "help"):
        console.print(_HELP_TEXT)
        return

    console.print(f"\n[dim]Query:[/dim] '{query}'")

    domain, confidence, method = _detect_domain(query)
    if not domain:
        console.print(Panel(
            "[yellow]Could not identify the service or domain.\n"
            "Try mentioning the service name (e.g., 'docker', 'nginx', 'ssh').[/yellow]",
            title="Unknown Domain",
            border_style="yellow",
        ))
        return

    conf_str = f" ({confidence * 100:.0f}%)" if confidence > 0 else ""
    console.print(f"[green]✓ Domain:[/green] [bold]{domain.upper()}[/bold]{conf_str}  [dim]{method}[/dim]")

    loader = KnowledgeBaseLoader()
    kb = loader.load_domain(domain)
    if not kb:
        console.print(
            f"[yellow]No Knowledge Base for '{domain}'. "
            f"Available: {loader.list_available_domains()}[/yellow]"
        )
        return

    session = Session(user_query=query)
    engine  = RuleEngine(kb=kb)
    diagnosis = engine.diagnose(session)

    if diagnosis:
        _print_diagnosis(session, domain, confidence, method)
    else:
        console.print(Panel(
            "[yellow]The expert system matched the domain but could not confirm a specific root cause.\n"
            "Please provide the exact error message from your terminal for better results.[/yellow]",
            title="⚠ No Root Cause Confirmed",
            border_style="yellow",
        ))


if __name__ == "__main__":
    run()
