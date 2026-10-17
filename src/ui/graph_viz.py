"""Graph Visualization Module for NexusBrain UI.

Renders force-directed subgraphs using streamlit-agraph or interactive PyVis HTML.
Applies distinctive styling:
- Active decisions / standards: Vibrant emerald green glow
- Superseded decisions / outdated docs: Amber / Crimson dashed border
- Systems, People, Teams, Tickets: Curated modern palette
"""

from typing import Dict, Any, List
import streamlit as st

try:
    from streamlit_agraph import agraph, Node, Edge, Config
    AGRAPH_AVAILABLE = True
except ImportError:
    AGRAPH_AVAILABLE = False


# Theme styling palette
NODE_COLORS = {
    "Decision_active": {"bg": "#064e3b", "border": "#10b981", "color": "#a7f3d0"},
    "Decision_superseded": {"bg": "#450a0a", "border": "#ef4444", "color": "#fecaca"},
    "Document_active": {"bg": "#083344", "border": "#06b6d4", "color": "#cffafe"},
    "Document_outdated": {"bg": "#451a03", "border": "#f59e0b", "color": "#fef3c7"},
    "System": {"bg": "#1e3a8a", "border": "#3b82f6", "color": "#dbeafe"},
    "Person": {"bg": "#3b0764", "border": "#a855f7", "color": "#f3e8ff"},
    "Team": {"bg": "#500724", "border": "#ec4899", "color": "#fce7f3"},
    "Ticket": {"bg": "#431407", "border": "#f97316", "color": "#ffedd5"},
    "PullRequest": {"bg": "#1e1b4b", "border": "#6366f1", "color": "#e0e7ff"},
    "Playbook": {"bg": "#042f2e", "border": "#14b8a6", "color": "#ccfbf1"},
    "Default": {"bg": "#1f2937", "border": "#9ca3af", "color": "#f3f4f6"},
}


def get_node_style(node_type: str, status: str = "active") -> Dict[str, str]:
    """Resolve color scheme based on entity type and temporal status."""
    key = f"{node_type}_{status}"
    if key in NODE_COLORS:
        return NODE_COLORS[key]
    if node_type in NODE_COLORS:
        return NODE_COLORS[node_type]
    return NODE_COLORS["Default"]


def render_subgraph(subgraph_data: Dict[str, Any]) -> None:
    """Render interactive force-directed graph canvas."""
    nodes_data = subgraph_data.get("nodes", [])
    edges_data = subgraph_data.get("edges", [])

    if not nodes_data:
        st.info("ℹ️ No traversal subgraph to display for this turn.")
        return

    if AGRAPH_AVAILABLE:
        agraph_nodes: List[Node] = []
        agraph_edges: List[Edge] = []

        for n in nodes_data:
            nid = n.get("id", "")
            label = n.get("label", nid)
            ntype = n.get("type", "Default")
            nstatus = n.get("status", "active") or "active"
            style = get_node_style(ntype, nstatus)

            # Mark superseded nodes with visual indicator
            display_title = f"[{ntype}] {label} ({nstatus})" if nstatus else f"[{ntype}] {label}"
            agraph_nodes.append(
                Node(
                    id=nid,
                    label=label,
                    size=26 if "active" in nstatus else 20,
                    color=style["border"],
                    title=display_title,
                    font={"color": "#ffffff", "face": "Inter, sans-serif", "size": 12},
                    borderWidth=3 if nstatus == "active" else 2,
                )
            )

        for e in edges_data:
            agraph_edges.append(
                Edge(
                    source=e.get("source", ""),
                    target=e.get("target", ""),
                    label=e.get("relationship", ""),
                    color="#64748b",
                    font={"color": "#94a3b8", "size": 10, "align": "top"},
                    arrows="to",
                )
            )

        config = Config(
            width="100%",
            height=460,
            directed=True,
            physics=True,
            hierarchical=False,
            nodeHighlightBehavior=True,
            highlightColor="#38bdf8",
            collapsible=False,
        )

        agraph(nodes=agraph_nodes, edges=agraph_edges, config=config)
    else:
        # Fallback to PyVis HTML embedding
        import networkx as nx
        from pyvis.network import Network
        import streamlit.components.v1 as components

        net = Network(height="460px", width="100%", bgcolor="#090d16", font_color="#ffffff", directed=True)
        for n in nodes_data:
            nid = n.get("id", "")
            label = n.get("label", nid)
            ntype = n.get("type", "Default")
            nstatus = n.get("status", "active") or "active"
            style = get_node_style(ntype, nstatus)
            net.add_node(
                nid,
                label=label,
                color=style["border"],
                title=f"{ntype}: {label} ({nstatus})",
                size=22,
            )

        for e in edges_data:
            net.add_edge(
                e.get("source", ""),
                e.get("target", ""),
                label=e.get("relationship", ""),
                color="#475569",
            )

        net.set_options("""
        var options = {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -3000,
              "springLength": 95,
              "springConstant": 0.04
            }
          }
        }
        """)
        html_str = net.generate_html()
        components.html(html_str, height=480, scrolling=True)
