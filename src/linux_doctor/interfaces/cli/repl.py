"""
Linux Doctor — Interactive Troubleshooting Agent (REPL)

Usage:
    linux-doctor          → Interactive shell
    linux-doctor "query"  → One-shot diagnosis (existing)

Commands:
    /explain      Show full reasoning chain for last diagnosis
    /history      Show session history
    /fix [n]      Apply fix step n (or list all)
    /safe         Toggle safe mode (require confirm for all commands)
    /help         Show help
    /exit         Exit
"""

from __future__ import annotations

import logging
import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from linux_doctor.cli.app import _detect_domain, _print_diagnosis
from linux_doctor.domain.models import Session
from linux_doctor.engines.rule_engine import RuleEngine
from linux_doctor.infrastructure.database.repository import SessionRepository
from linux_doctor.infrastructure.kb_loader import KnowledgeBaseLoader

logging.disable(logging.CRITICAL)

console = Console()
kb_loader = KnowledgeBaseLoader("data/kb")
db = SessionRepository("data/linux_doctor.db")

# ── Styles ────────────────────────────────────────────────────────
STYLE = Style.from_dict({
    "prompt": "bold cyan",
    "command": "bold yellow",
    "dim": "italic #888888",
})

# ── Session state ─────────────────────────────────────────────────
class AgentState:
    """Holds the current agent session state."""

    def __init__(self):
        self.session: Session | None = None
        self.last_diagnosis = None
        self.last_domain = None
        self.last_confidence = 0.0
        self.safe_mode = True
        self.history: list[dict] = []

    def reset_session(self):
        self.session = Session()
        self.last_diagnosis = None

agent = AgentState()


# ── Help ──────────────────────────────────────────────────────────
def show_help():
    console.print(Panel.fit(
        "[bold cyan]🐧 Linux Doctor Agent — Commands[/bold cyan]\n\n"
        "[bold]Natural language[/bold]\n"
        "  Just describe your Linux issue naturally\n"
        "  Examples:\n"
        "    nginx không chạy được\n"
        "    docker permission denied\n"
        "    ssh connection refused port 22\n"
        "    disk full no space left\n\n"
        "[bold]Slash commands[/bold]\n"
        "  [command]/explain[/command]   Show full reasoning chain\n"
        "  [command]/history[/command]   Show session history\n"
        "  [command]/fix[/command]       List available fix commands\n"
        "  [command]/fix [n][/command]   Execute fix step n\n"
        "  [command]/safe[/command]      Toggle safe mode\n"
        "  [command]/clear[/command]     Clear screen\n"
        "  [command]/help[/command]      Show this help\n"
        "  [command]/exit[/command]      Exit\n",
        border_style="cyan",
        width=72,
    ))


# ── Diagnosis ─────────────────────────────────────────────────────
def run_diagnosis(query: str) -> None:
    """Run full diagnosis pipeline on a query."""
    agent.reset_session()
    agent.session.user_query = query

    # Step 1: Detect domain
    domain, confidence, method = _detect_domain(query)
    agent.last_domain = domain
    agent.last_confidence = confidence

    if not domain:
        console.print("[yellow]Could not identify the domain. Try mentioning a service name (nginx, docker, ssh...)[/yellow]")
        return

    conf_str = f" ({confidence*100:.0f}%)" if confidence > 0 else ""
    console.print(f"[green]✓ Domain:[/green] [bold]{domain.upper()}[/bold]{conf_str}  [dim]{method}[/dim]")

    # Step 2: Load KB and run engine
    kb = kb_loader.load_domain(domain)
    if not kb:
        console.print(f"[yellow]No Knowledge Base for domain '{domain}'[/yellow]")
        return

    engine = RuleEngine(kb=kb)
    diagnosis = engine.diagnose(agent.session)

    if diagnosis:
        # Save to database
        try:
            saved = db.save_diagnosis(agent.session.session_id, diagnosis)
            db.save_recommendations(saved, diagnosis.recommended_fixes)
            db.cache_incident(query, domain, diagnosis.root_cause, diagnosis.root_cause, diagnosis.confidence)
        except Exception:
            pass

        agent.last_diagnosis = diagnosis
        agent.history.append({
            "query": query,
            "domain": domain,
            "root_cause": diagnosis.root_cause,
            "confidence": diagnosis.confidence,
            "conclusive": diagnosis.is_conclusive,
        })
        _print_diagnosis(diagnosis, domain, confidence, method)

        # Show interactive fix options
        if diagnosis.recommended_fixes:
            console.print("\n[bold]Options:[/bold] [dim]/fix[/dim] to see fixes  [dim]/explain[/dim] for details  [dim]/exit[/dim] to quit")
    else:
        console.print(Panel(
            "[yellow]No root cause confirmed. Try providing more details or the exact error message.[/yellow]",
            title="⚠ Inconclusive",
            border_style="yellow",
        ))


# ── Fix display ───────────────────────────────────────────────────
def show_fixes():
    """Show available fix commands with risk levels."""
    if not agent.last_diagnosis or not agent.last_diagnosis.recommended_fixes:
        console.print("[yellow]No fix commands available. Run a diagnosis first.[/yellow]")
        return

    table = Table(title="🔧 Available Fixes", box=None)
    table.add_column("#", style="dim", width=3)
    table.add_column("Command", style="bold yellow")
    table.add_column("Risk", width=10)
    table.add_column("Safe?", width=6, justify="center")

    for i, fix in enumerate(agent.last_diagnosis.recommended_fixes, 1):
        risk_color = "green" if fix.risk == "safe" else "yellow" if fix.risk == "moderate" else "red"
        safe_icon = "✅" if fix.is_safe_to_auto_run else "⚠️ "
        table.add_row(str(i), fix.command, f"[{risk_color}]{fix.risk}[/{risk_color}]", safe_icon)

    console.print(table)
    console.print("[dim]Run [command]/fix <number>[/command] to execute a fix step[/dim]")


# ── Fix execution ─────────────────────────────────────────────────
def execute_fix(step: int) -> None:
    """Execute a specific fix command with safety checks."""
    if not agent.last_diagnosis or not agent.last_diagnosis.recommended_fixes:
        console.print("[yellow]No fixes available[/yellow]")
        return

    if step < 1 or step > len(agent.last_diagnosis.recommended_fixes):
        console.print(f"[red]Invalid step {step}. Available: 1-{len(agent.last_diagnosis.recommended_fixes)}[/red]")
        return

    fix = agent.last_diagnosis.recommended_fixes[step - 1]
    from linux_doctor.infrastructure.shell.runner import SafetyError

    # Safety check (already done by ShellRunner, but double-check)
    if not fix.is_safe_to_auto_run and agent.safe_mode:
        console.print(Panel(
            f"[yellow]⚠ Command requires confirmation:[/yellow]\n"
            f"[bold]${fix.command}[/bold]\n\n"
            f"[dim]{fix.explanation}[/dim]",
            title="Safety Check",
            border_style="yellow",
        ))
        confirm = input("  Execute? (y/N): ").strip().lower()
        if confirm != "y":
            console.print("[dim]Cancelled[/dim]")
            return

    # Execute
    try:
        from linux_doctor.infrastructure.shell.runner import ShellRunner
        runner = ShellRunner(timeout=30)
        result = runner.run(fix.command)

        if result.success:
            console.print(f"[green]✅ {fix.explanation}[/green]")
            if result.stdout:
                console.print(f"[dim]{result.stdout[:500]}[/dim]")
        else:
            console.print(f"[red]❌ Failed: {result.stderr[:300]}[/red]")
    except SafetyError as e:
        console.print(f"[red]⛔ Blocked by safety: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# ── Show history ──────────────────────────────────────────────────
def show_history():
    """Show diagnosis history for this session."""
    if not agent.history:
        # Try loading from database
        try:
            sessions = db.list_sessions(limit=10)
            if sessions:
                table = Table(title="📋 Recent Sessions", box=None)
                table.add_column("Query", style="bold")
                table.add_column("Domain", width=12)
                table.add_column("Status", width=10)
                table.add_column("Date")
                for s in sessions:
                    table.add_row(s["query"][:50], s["domain"] or "-", s["status"], s["created_at"][:19] if s["created_at"] else "-")
                console.print(table)
                return
        except Exception:
            pass
        console.print("[yellow]No diagnosis history yet[/yellow]")
        return

    table = Table(title="📋 Current Session", box=None)
    table.add_column("#", style="dim", width=3)
    table.add_column("Query", style="bold")
    table.add_column("Domain", width=10)
    table.add_column("Root Cause", width=40)
    table.add_column("Confidence", width=10)

    for i, h in enumerate(agent.history, 1):
        rc = h["root_cause"][:40] if h["root_cause"] else "-"
        conf = f"{h['confidence']:.0%}" if h["confidence"] else "-"
        table.add_row(str(i), h["query"][:40], h["domain"], rc, conf)
    console.print(table)


# ── Clear screen ──────────────────────────────────────────────────
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# ── Key bindings ──────────────────────────────────────────────────
bindings = KeyBindings()


@bindings.add("c-c")
def _(event):
    """Ctrl+C to exit."""
    console.print("\n[yellow]Bye![/yellow]")
    sys.exit(0)


@bindings.add("c-d")
def _(event):
    """Ctrl+D to exit."""
    console.print("\n[yellow]Bye![/yellow]")
    sys.exit(0)


# ── REPL ──────────────────────────────────────────────────────────
def main():
    """Entry point for the interactive agent."""
    clear_screen()

    console.print(Panel.fit(
        "[bold cyan]🐧 Linux Doctor — Interactive Agent[/bold cyan]\n"
        "[dim]Classical AI · No LLMs · From Scratch ML[/dim]\n"
        "[dim]Describe any Linux issue in natural language[/dim]",
        border_style="cyan",
    ))
    console.print("  Type [command]/help[/command] for commands  |  [command]/exit[/command] to quit\n")

    history_path = os.path.expanduser("~/.linux_doctor_history")
    prompt_session = PromptSession(
        history=FileHistory(history_path) if os.path.exists(os.path.dirname(history_path) or ".") else None,
        style=STYLE,
        key_bindings=bindings,
        vi_mode=False,
    )

    while True:
        try:
            query = prompt_session.prompt([
                ("class:prompt", "🐧 "),
                ("class:dim", "ld"),
                ("class:prompt", "> "),
            ]).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Bye![/yellow]")
            break

        if not query:
            continue

        # ── Commands (with or without / prefix) ──
        # Commands: must start with / OR be a single-word command
        words = query.split()
        first_word = words[0].lower().lstrip("/")
        commands = {"exit", "quit", "help", "?", "explain", "history",
                     "fix", "safe", "clear", "cls"}

        if query.startswith("/") or (len(words) == 1 and first_word in commands):
            cmd = query.lstrip("/").split()

            match cmd[0]:
                case "exit" | "quit":
                    console.print("[yellow]Bye![/yellow]")
                    break
                case "help" | "?":
                    show_help()
                case "explain":
                    if agent.last_diagnosis:
                        console.print(Panel(
                            agent.last_diagnosis.explanation,
                            title="🧠 Reasoning Chain",
                            border_style="cyan",
                        ))
                    else:
                        console.print("[yellow]No diagnosis yet. Describe a Linux issue first.[/yellow]")
                case "history":
                    show_history()
                case "fix":
                    if len(cmd) > 1 and cmd[1].isdigit():
                        execute_fix(int(cmd[1]))
                    else:
                        show_fixes()
                case "safe":
                    agent.safe_mode = not agent.safe_mode
                    status = "ON" if agent.safe_mode else "OFF"
                    console.print(f"[green]Safe mode {status}[/green]")
                case "clear" | "cls":
                    clear_screen()
                case _:
                    console.print(f"[red]Unknown command: {cmd[0]}[/red]  [dim]Type /help for commands[/dim]")
            continue

        # ── Natural language ──
        if len(query) < 3:
            console.print("[dim]Please describe your issue in more detail[/dim]")
            continue
        # Ignore input that looks like copied terminal output (has multiple spaces or system paths)
        if query.count("  ") > 3 or "/usr/" in query or "/bin/" in query:
            console.print("[dim]⚠ That looks like terminal output, not an issue description. Tell me what went wrong.[/dim]")
            continue

        run_diagnosis(query)


if __name__ == "__main__":
    main()
