# main.py
import click
import os
from iac_diff.parser import parse_terraform
from iac_diff.graph import build_graph
from iac_diff.differ import diff_resources
from iac_diff.blast_radius import compute_blast_radius
from iac_diff.classifier import classify_all
from iac_diff.report import print_report, console

@click.command()
@click.argument('before', type=click.Path(exists=True))
@click.argument('after', type=click.Path(exists=True))
@click.option('--no-llm', is_flag=True, help='Skip LLM classification (faster)')
def main(before, after, no_llm):
    """Semantic diff engine for Terraform IaC files."""
    
    console.print(f"[dim]Parsing {before}...[/dim]")
    before_resources = parse_terraform(before)
    console.print(f"[dim]Parsing {after}...[/dim]")
    after_resources = parse_terraform(after)

    graph_before = build_graph(before_resources)
    graph_after = build_graph(after_resources)

    console.print(f"[dim]Found {len(before_resources)} → {len(after_resources)} resources[/dim]")

    changes = diff_resources(before_resources, after_resources)
    console.print(f"[dim]Detected {len(changes)} changes[/dim]")

    if not changes:
        console.print("[green]No changes detected.[/green]")
        return

    blast_results = compute_blast_radius(changes, graph_before, graph_after)

    if no_llm:
        classifications = [{"intent": "LLM skipped", "risk_level": "unknown",
                            "risk_reason": "", "security_flags": []}
                           for _ in blast_results]
    else:
        console.print(f"[dim]Classifying {len(changes)} changes with LLM...[/dim]")
        classifications = classify_all(blast_results)

    print_report(blast_results, classifications)


if __name__ == '__main__':
    main()