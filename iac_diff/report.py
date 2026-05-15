# report.py
from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

console = Console()

RISK_COLORS = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "green",
    "none": "dim",
    "unknown": "dim"
}

CHANGE_SYMBOLS = {
    "added": "[green]+[/green]",
    "removed": "[red]-[/red]",
    "modified": "[yellow]~[/yellow]",
}

def print_report(blast_results, classifications):
    console.print("\n[bold]IaC Semantic Diff Report[/bold] [dim](Intent and risk powered by Llama 3.1 via Groq)[/dim]\n")
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Change", width=4)
    table.add_column("Resource", min_width=30)
    table.add_column("Risk", width=10)
    table.add_column("Blast Radius", width=14)
    table.add_column("Intent", min_width=30)
    table.add_column("Flags", min_width=20)

    for blast, cls in zip(blast_results, classifications):
        c = blast.change
        risk = cls.get("risk_level", "unknown")
        color = RISK_COLORS.get(risk, "white")
        flags = ", ".join(cls.get("security_flags", [])) or "—"

        table.add_row(
            CHANGE_SYMBOLS[c.change_type],
            c.resource_id,
            f"[{color}]{risk.upper()}[/{color}]",
            f"{blast.affected_count()} resources",
            cls.get("intent", "—"),
            f"[red]{flags}[/red]" if flags != "—" else "—"
        )

    console.print(table)

    # Detail section for high/critical
    high_risk = [(b, c) for b, c in zip(blast_results, classifications)
                 if c.get("risk_level") in ("high", "critical")]
    if high_risk:
        console.print("\n[bold red]High-Risk Changes — Detail[/bold red]\n")
        for blast, cls in high_risk:
            console.print(f"  [red]>>>[/red] [bold]{blast.change.resource_id}[/bold]")
            console.print(f"      Risk: {cls['risk_reason']}")
            if blast.transitively_affected:
                console.print(f"      Transitively affects: {', '.join(blast.transitively_affected[:6])}")
            console.print()