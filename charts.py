"""
charts.py
Plotly and Seaborn chart functions for the survey visualizer dashboard.
All Plotly functions return a go.Figure ready to pass to st.plotly_chart().
"""

import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ── Colour palette ────────────────────────────────────────────────────────────
PALETTE = px.colors.qualitative.Set2
ACCENT  = "#636EFA"


# ── Bar chart ─────────────────────────────────────────────────────────────────

def bar_chart(df: pd.DataFrame, col: str, title: str = None) -> go.Figure:
    counts = df[col].value_counts().reset_index()
    counts.columns = [col, "Count"]
    fig = px.bar(
        counts, x=col, y="Count",
        title=title or f"Distribution — {col}",
        color=col,
        color_discrete_sequence=PALETTE,
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, xaxis_title=col, yaxis_title="Count",
                      plot_bgcolor="white", paper_bgcolor="white")
    return fig


# ── Pie chart ─────────────────────────────────────────────────────────────────

def pie_chart(df: pd.DataFrame, col: str, title: str = None) -> go.Figure:
    counts = df[col].value_counts().reset_index()
    counts.columns = [col, "Count"]
    fig = px.pie(
        counts, names=col, values="Count",
        title=title or f"Response Share — {col}",
        color_discrete_sequence=PALETTE,
        hole=0.3,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


# ── Histogram ─────────────────────────────────────────────────────────────────

def histogram(df: pd.DataFrame, col: str, bins: int = 20, title: str = None) -> go.Figure:
    fig = px.histogram(
        df, x=col, nbins=bins,
        title=title or f"Histogram — {col}",
        color_discrete_sequence=[ACCENT],
    )
    fig.update_layout(bargap=0.05, plot_bgcolor="white", paper_bgcolor="white",
                      yaxis_title="Count")
    return fig


# ── Box plot ──────────────────────────────────────────────────────────────────

def box_plot(df: pd.DataFrame, col: str, group_col: str = None,
             title: str = None) -> go.Figure:
    fig = px.box(
        df, y=col, x=group_col,
        title=title or f"Box Plot — {col}",
        color=group_col,
        color_discrete_sequence=PALETTE,
        points="outliers",
    )
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    return fig


# ── Likert grouped bar ────────────────────────────────────────────────────────

def likert_bar(df: pd.DataFrame, likert_cols: list[str], title: str = None) -> go.Figure:
    """Stacked bar showing response distribution for each Likert question."""
    if not likert_cols:
        return None

    # Determine scale range
    all_vals = pd.concat([df[c].dropna() for c in likert_cols])
    scale = sorted(all_vals.unique().astype(int).tolist())

    fig = go.Figure()
    colors = px.colors.sequential.Blues[2:]
    for i, val in enumerate(scale):
        counts = [round((df[col] == val).sum() / df[col].notna().sum() * 100, 1)
                  for col in likert_cols]
        fig.add_trace(go.Bar(
            name=str(val),
            x=likert_cols,
            y=counts,
            marker_color=colors[i % len(colors)],
            text=[f"{c}%" for c in counts],
            textposition="inside",
        ))

    fig.update_layout(
        barmode="stack",
        title=title or "Likert Scale Response Distribution (%)",
        xaxis_title="Question",
        yaxis_title="% of Responses",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title="Rating",
    )
    return fig


# ── Correlation heatmap (Seaborn → PNG buffer) ────────────────────────────────

def correlation_heatmap(df: pd.DataFrame, numeric_cols: list[str]) -> io.BytesIO | None:
    """Returns a PNG BytesIO buffer of a Seaborn correlation heatmap."""
    if len(numeric_cols) < 2:
        return None
    corr = df[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(max(6, len(numeric_cols)), max(5, len(numeric_cols) - 1)))
    sns.heatmap(
        corr, annot=True, fmt=".2f", cmap="coolwarm",
        linewidths=0.5, ax=ax, vmin=-1, vmax=1,
        annot_kws={"size": 9},
    )
    ax.set_title("Correlation Matrix", fontsize=13, fontweight="bold")
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


# ── Response rate bar (Plotly) ────────────────────────────────────────────────

def response_rate_chart(rate_df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        rate_df, x="Question", y="Response Rate (%)",
        title="Response Rate per Question",
        color="Response Rate (%)",
        color_continuous_scale="Blues",
        text="Response Rate (%)",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, plot_bgcolor="white",
                      paper_bgcolor="white", xaxis_tickangle=-30)
    return fig
