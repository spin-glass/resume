#!/usr/bin/env python3
"""Visualize the LangGraph StateGraph workflow structure.

This script generates a visual representation of the resume review workflow
showing all nodes and edges in the graph.

Usage:
    python scripts/visualize_graph.py [--format mermaid|ascii|png|langsmith]
    python scripts/visualize_graph.py --format png --output workflow.png
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.workflow.graph import build_review_workflow


def generate_mermaid(workflow, xray: bool = False) -> str:
    """Generate mermaid diagram syntax using LangGraph's built-in method.

    Args:
        workflow: Compiled workflow
        xray: If True, use xray mode to show subgraph details
    """
    # Use LangGraph's native mermaid generation with xray option
    try:
        graph = workflow.get_graph(xray=xray) if xray else workflow.get_graph()
        mermaid_code = graph.draw_mermaid()
        return f"```mermaid\n{mermaid_code}\n```"
    except Exception as e:
        # Fallback to manual generation
        print(f"Warning: Using fallback mermaid generation: {e}", file=sys.stderr)
        graph = workflow.get_graph()
        lines = ["```mermaid", "graph TD;"]

        # Add edges
        for edge in graph.edges:
            source = edge.source
            target = edge.target

            # Use dotted line for conditional edges
            if hasattr(edge, 'conditional') and edge.conditional:
                lines.append(f"    {source} -.-> {target};")
            else:
                lines.append(f"    {source} --> {target};")

        lines.append("```")
        return "\n".join(lines)


def generate_ascii(workflow) -> str:
    """Generate ASCII art diagram using LangGraph's built-in method."""
    graph = workflow.get_graph()

    output = []
    output.append("=" * 70)
    output.append("Resume Review Workflow - Node and Edge Structure")
    output.append("=" * 70)

    # Try LangGraph's native ASCII representation first
    try:
        ascii_repr = graph.draw_ascii()
        output.append("\n=== LANGGRAPH NATIVE VISUALIZATION ===\n")
        output.append(ascii_repr)
        output.append("\n")
    except Exception as e:
        print(f"Note: LangGraph ASCII drawing not available: {e}", file=sys.stderr)

    # List nodes
    output.append("\n=== NODES ===")
    for node_name in sorted(graph.nodes.keys()):
        if node_name.startswith("__"):
            output.append(f"  • {node_name:<20} (automatic)")
        else:
            output.append(f"  • {node_name}")

    # List edges
    output.append("\n=== EDGES ===")
    edges = [(e.source, e.target) for e in graph.edges]
    for source, target in sorted(edges):
        output.append(f"  {source:<20} --> {target}")

    # Fan-out pattern
    output.append("\n=== FAN-OUT PATTERN (Parallel Execution) ===")
    fan_out = [e for e in graph.edges if e.source == 'router']
    for edge in fan_out:
        output.append(f"  router --> {edge.target}")

    # Fan-in pattern
    output.append("\n=== FAN-IN PATTERN (Convergence) ===")
    fan_in = [e for e in graph.edges if e.target == 'aggregator']
    for edge in fan_in:
        output.append(f"  {edge.source} --> aggregator")

    # Flow diagram
    output.append("\n=== EXECUTION FLOW ===")
    output.append("""
    START
      │
      ▼
    router ─────┬─────────┬─────────> (fan-out to 3 agents)
                │         │
      ┌─────────┘         └─────────┐
      ▼                   ▼         ▼
   recruiter        tech_writer  copywriter
      │                   │         │
      └─────────┬─────────┴─────────┘
                ▼
           aggregator ────> (calculate score)
                │
       ┌────────┴────────┐
       │                 │
       ▼ (retry)         ▼ (complete)
    revisor          portfolio
       │                 │
       └─> router   ┌────┴────┐
                    │         │
                    ▼         ▼ (no screenshot)
                 design       END
                    │
                    └────────> END
    """)

    output.append("=" * 70)
    return "\n".join(output)


def generate_png(workflow, output_path: Path) -> None:
    """Generate PNG image of the graph using LangGraph's draw_mermaid_png."""
    try:
        graph = workflow.get_graph()

        # LangGraph's native PNG generation (requires dependencies)
        png_data = graph.draw_mermaid_png()

        output_path.write_bytes(png_data)
        print(f"✓ PNG diagram saved to: {output_path}")
        print(f"  Open with: open {output_path}")
    except ImportError as e:
        print(f"Error: Missing dependencies for PNG generation", file=sys.stderr)
        print(f"Install with: pip install 'langgraph[png]'", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating PNG: {e}", file=sys.stderr)
        print("Note: PNG generation requires pygraphviz or similar.", file=sys.stderr)
        sys.exit(1)


def print_langsmith_url(workflow) -> None:
    """Print instructions for LangSmith visualization."""
    print("\n" + "=" * 70)
    print("LangSmith Visualization (Interactive Trace Viewer)")
    print("=" * 70)
    print("\nTo visualize this workflow with LangSmith's interactive trace viewer:")
    print("\n1. Set environment variables:")
    print("   export LANGSMITH_API_KEY=your-api-key")
    print("   export LANGSMITH_TRACING=true")
    print("\n2. Run the review workflow:")
    print("   pnpm review:dry --verbose")
    print("\n3. View traces at:")
    print("   https://smith.langchain.com/")
    print("\nLangSmith provides:")
    print("  • Real-time execution traces")
    print("  • Individual node timing and outputs")
    print("  • Parallel execution visualization")
    print("  • Per-agent LLM call inspection")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Visualize the LangGraph StateGraph workflow structure"
    )
    parser.add_argument(
        "--format",
        choices=["mermaid", "ascii", "png", "langsmith"],
        default="ascii",
        help="Output format (default: ascii)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (required for PNG format)"
    )

    args = parser.parse_args()

    # Build workflow
    print("Building workflow...", file=sys.stderr)
    workflow = build_review_workflow()
    print("✓ Workflow compiled successfully\n", file=sys.stderr)

    # Generate visualization
    if args.format == "mermaid":
        print(generate_mermaid(workflow))
    elif args.format == "ascii":
        print(generate_ascii(workflow))
    elif args.format == "png":
        if not args.output:
            print("Error: --output is required for PNG format", file=sys.stderr)
            sys.exit(1)
        generate_png(workflow, args.output)
    elif args.format == "langsmith":
        print_langsmith_url(workflow)


if __name__ == "__main__":
    main()
