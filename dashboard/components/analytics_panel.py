"""Analytics dashboard — KPIs, charts, and usage insights."""

import random
from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.ui_helpers import get_pipeline, render_stat_card

# ── Plotly theme constants ───────────────────────────────────────────────────
_BG      = "#04070f"
_SURFACE = "#080e1c"
_GRID    = "rgba(255,255,255,0.04)"
_TEXT    = "#94a3b8"
_FONT    = dict(family="Inter, sans-serif", color=_TEXT, size=12)

_PRIMARY  = "#6366f1"
_ACCENT   = "#a855f7"
_CYAN     = "#06b6d4"
_SUCCESS  = "#10b981"
_WARNING  = "#f59e0b"

_AXIS = dict(gridcolor=_GRID, zeroline=False, linecolor=_GRID)


def _ax(**kwargs):
    return {**_AXIS, **kwargs}


def _layout(height: int = 300, margin: dict | None = None, **kwargs) -> dict:
    """Build a Plotly layout dict — no key collisions possible."""
    return dict(
        template="plotly_dark",
        paper_bgcolor=_BG,
        plot_bgcolor=_SURFACE,
        font=_FONT,
        height=height,
        margin=margin or dict(l=8, r=8, t=42, b=8),
        **kwargs,
    )



def _demo_data():
    today = datetime.now()
    dates   = [(today - timedelta(days=i)).strftime("%b %d") for i in range(13, -1, -1)]
    qs      = [random.randint(4, 45) for _ in dates]
    rts     = [random.randint(600, 2800) for _ in dates]
    confs   = [round(random.uniform(0.52, 0.96), 2) for _ in range(60)]
    top_docs = {
        "company_policy.pdf":    42,
        "financial_report.pdf":  31,
        "hr_handbook.pdf":       25,
        "product_manual.pdf":    19,
        "technical_docs.pdf":    14,
    }
    return dates, qs, rts, confs, top_docs


def render_analytics() -> None:
    pipeline = get_pipeline()

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;gap:13px;margin-bottom:1.4rem;'
        'padding-bottom:1.1rem;border-bottom:1px solid rgba(255,255,255,0.055)">'
        '  <div style="width:42px;height:42px;border-radius:11px;background:'
        '    linear-gradient(135deg,rgba(99,102,241,0.18),rgba(168,85,247,0.18));'
        '    border:1px solid rgba(99,102,241,0.22);display:flex;align-items:center;'
        '    justify-content:center;font-size:1.15rem">&#x1F4CA;</div>'
        '  <div>'
        '    <div style="font-size:1.32rem;font-weight:750;color:#f1f5f9;letter-spacing:-0.025em">'
        '      Analytics</div>'
        '    <div style="font-size:0.78rem;color:#475569;margin-top:2px">'
        '      Usage metrics and performance insights &mdash; demo data</div>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )

    dates, qs, rts, confs, top_docs = _demo_data()

    # ── KPI row ──────────────────────────────────────────────────────────────
    vs_stats = pipeline.vector_store_manager.get_index_stats() if pipeline else {}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_card(str(sum(qs)),              "Total Questions",   "&#x1F4AC;")
    with c2:
        render_stat_card(f"{int(sum(rts)/len(rts))} ms", "Avg Response", "&#x26A1;")
    with c3:
        render_stat_card(f"{int(sum(confs)/len(confs)*100)}%", "Avg Confidence", "&#x1F3AF;")
    with c4:
        render_stat_card(str(vs_stats.get("total_vectors", 0)), "Indexed Vectors", "&#x1F9E9;")

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    # ── Row 1: Questions per day  +  Response times ──────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=qs, mode="lines+markers",
            line=dict(color=_PRIMARY, width=2.5, shape="spline"),
            marker=dict(size=5, color=_PRIMARY,
                        line=dict(color="rgba(255,255,255,0.3)", width=1)),
            fill="tozeroy",
            fillcolor="rgba(99,102,241,0.08)",
            name="Questions",
        ))
        fig.update_layout(**_layout(
            height=290,
            title=dict(text="Questions per Day", font=dict(size=13, color=_TEXT)),
            xaxis=_ax(tickangle=-35, tickfont=dict(size=10)),
            yaxis=_ax(),
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig = go.Figure(go.Bar(
            x=dates, y=rts,
            marker=dict(
                color=rts,
                colorscale=[[0, "rgba(6,182,212,0.6)"], [1, "rgba(6,182,212,1)"]],
                line=dict(width=0),
            ),
            name="Response ms",
        ))
        fig.update_layout(**_layout(
            height=290,
            title=dict(text="Response Time (ms)", font=dict(size=13, color=_TEXT)),
            xaxis=_ax(tickangle=-35, tickfont=dict(size=10)),
            yaxis=_ax(),
            bargap=0.25,
        ))
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 2: Confidence histogram  +  Top source docs ─────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        fig = go.Figure(go.Histogram(
            x=confs, nbinsx=16,
            marker=dict(
                color=confs,
                colorscale=[[0, "#5254a3"], [1, _ACCENT]],
                line=dict(color="rgba(0,0,0,0.4)", width=0.5),
            ),
            opacity=0.88, name="Confidence",
        ))
        fig.update_layout(**_layout(
            height=290,
            title=dict(text="Confidence Score Distribution", font=dict(size=13, color=_TEXT)),
            xaxis=_ax(title="Score"),
            yaxis=_ax(title="Count"),
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        names  = list(top_docs.keys())
        counts = list(top_docs.values())
        fig = go.Figure(go.Bar(
            x=counts, y=names, orientation="h",
            marker=dict(
                color=counts,
                colorscale=[[0, "#312e81"], [1, _CYAN]],
                line=dict(width=0),
            ),
            text=counts, textposition="outside",
            textfont=dict(color=_TEXT, size=11),
        ))
        fig.update_layout(**_layout(
            height=290,
            margin=dict(l=8, r=30, t=42, b=8),
            title=dict(text="Top Referenced Documents", font=dict(size=13, color=_TEXT)),
            xaxis=_ax(title="Times Referenced"),
            yaxis=_ax(),
        ))
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 3: Token usage area ──────────────────────────────────────────────
    token_usage = [q * random.randint(75, 210) for q in qs]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=token_usage, mode="lines",
        line=dict(color=_CYAN, width=2.2, shape="spline"),
        fill="tozeroy", fillcolor="rgba(6,182,212,0.07)",
        name="Tokens",
    ))
    ma = [sum(token_usage[max(0,i-2):i+3])/len(token_usage[max(0,i-2):i+3])
          for i in range(len(token_usage))]
    fig.add_trace(go.Scatter(
        x=dates, y=ma, mode="lines",
        line=dict(color=_WARNING, width=1.5, dash="dot"),
        name="3-day MA", opacity=0.7,
    ))
    fig.update_layout(**_layout(
        height=240,
        title=dict(text="Token Usage Over Time", font=dict(size=13, color=_TEXT)),
        xaxis=_ax(title="Date", tickangle=-35, tickfont=dict(size=10)),
        yaxis=_ax(title="Tokens Used"),
        legend=dict(orientation="h", x=0.01, y=1.12,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    ))
    st.plotly_chart(fig, use_container_width=True)

    # ── Row 4: Donut + Heatmap ───────────────────────────────────────────────
    col_e, col_f = st.columns([1, 2])

    with col_e:
        labels = ["MMR", "Similarity", "Hybrid", "Compressed"]
        vals   = [52, 28, 14, 6]
        colors = [_PRIMARY, _ACCENT, _CYAN, _SUCCESS]
        fig = go.Figure(go.Pie(
            labels=labels, values=vals, hole=0.58,
            marker=dict(colors=colors, line=dict(color=_BG, width=2)),
            textinfo="percent", textfont=dict(size=11),
            hoverinfo="label+value+percent",
        ))
        fig.add_annotation(text="Search<br>Methods", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=11, color=_TEXT))
        fig.update_layout(**_layout(
            height=280,
            margin=dict(l=8, r=60, t=42, b=8),
            title=dict(text="Search Method Usage", font=dict(size=13, color=_TEXT)),
            legend=dict(orientation="v", x=1.0, y=0.5,
                        bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col_f:
        hours = list(range(24))
        days  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        heat  = [[random.randint(0, 18) for _ in hours] for _ in days]
        fig = go.Figure(go.Heatmap(
            z=heat, x=[f"{h:02d}:00" for h in hours], y=days,
            colorscale=[[0, _SURFACE], [0.3, "#312e81"], [0.7, _PRIMARY], [1, "#c4b5fd"]],
            showscale=True,
            colorbar=dict(tickfont=dict(size=10, color=_TEXT), thickness=10, len=0.7),
            hovertemplate="Day: %{y}<br>Hour: %{x}<br>Queries: %{z}<extra></extra>",
        ))
        fig.update_layout(**_layout(
            height=280,
            title=dict(text="Activity Heatmap (queries / hour)", font=dict(size=13, color=_TEXT)),
            xaxis=_ax(tickangle=-45, tickfont=dict(size=9)),
            yaxis=_ax(tickfont=dict(size=10)),
        ))
        st.plotly_chart(fig, use_container_width=True)
