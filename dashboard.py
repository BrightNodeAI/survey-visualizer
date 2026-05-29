"""
dashboard.py
Main Streamlit app — Survey Data Visualizer.

Run with:
    streamlit run dashboard.py
"""

import io
import pandas as pd
import streamlit as st
from PIL import Image

from processor import (
    load_file, clean_dataframe,
    detect_numeric_cols, detect_categorical_cols,
    detect_demographic_cols, detect_likert_cols,
    response_rate, likert_summary, column_summary,
)
from charts import (
    bar_chart, pie_chart, histogram, box_plot,
    likert_bar, correlation_heatmap, response_rate_chart,
)


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Survey Data Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Survey Data Visualizer")
st.markdown(
    "Upload any survey CSV or Excel file to instantly explore responses "
    "with interactive charts, demographic filters, and a downloadable summary."
)
st.divider()


# ── File upload ───────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drag and drop your survey file here",
    type=["csv", "xlsx", "xls"],
    help="Supports CSV and Excel. Any file with 2+ columns works.",
)

if uploaded is None:
    st.info("👆 Upload a CSV or Excel file to get started. "
            "No file yet? A sample dataset is included in `sample_data/sample_survey.csv`.")
    st.stop()


# ── Load & clean ──────────────────────────────────────────────────────────────
with st.spinner("Loading data …"):
    raw_df = load_file(uploaded)
    df = clean_dataframe(raw_df)

st.success(f"✅ Loaded **{len(df):,} rows** and **{len(df.columns)} columns**.")

num_cols   = detect_numeric_cols(df)
cat_cols   = detect_categorical_cols(df)
demo_cols  = detect_demographic_cols(df)
likert_cols = detect_likert_cols(df)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Controls")

    # Demographic filter
    st.subheader("Demographic Filter")
    demo_filter_col = st.selectbox(
        "Filter by column", options=["(none)"] + demo_cols
    )
    filtered_df = df.copy()
    if demo_filter_col != "(none)":
        values = sorted(df[demo_filter_col].dropna().unique().tolist())
        selected_vals = st.multiselect(
            f"Select {demo_filter_col}", options=values, default=values
        )
        filtered_df = df[df[demo_filter_col].isin(selected_vals)]

    st.caption(f"**{len(filtered_df):,}** rows after filter")
    st.divider()

    # Chart settings
    st.subheader("Chart Settings")
    chart_type = st.selectbox(
        "Chart type",
        ["Bar", "Pie", "Histogram", "Box Plot"],
    )
    selected_col = st.selectbox(
        "Column to visualise",
        options=cat_cols + num_cols,
    )
    group_col = None
    if chart_type == "Box Plot" and demo_cols:
        group_col = st.selectbox("Group by (optional)", ["(none)"] + demo_cols)
        if group_col == "(none)":
            group_col = None


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Charts", "📋 Summary Stats", "❓ Likert Analysis",
    "🔗 Correlations", "🗂 Raw Data"
])


# ── Tab 1 · Charts ────────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"{chart_type} — {selected_col}")
    if chart_type == "Bar":
        fig = bar_chart(filtered_df, selected_col)
    elif chart_type == "Pie":
        fig = pie_chart(filtered_df, selected_col)
    elif chart_type == "Histogram":
        fig = histogram(filtered_df, selected_col)
    else:
        fig = box_plot(filtered_df, selected_col, group_col)

    st.plotly_chart(fig, use_container_width=True)

    # Response rate
    if num_cols or cat_cols:
        st.subheader("Response Rate per Column")
        rr_df = response_rate(filtered_df, (cat_cols + num_cols)[:15])
        st.plotly_chart(response_rate_chart(rr_df), use_container_width=True)


# ── Tab 2 · Summary Stats ─────────────────────────────────────────────────────
with tab2:
    st.subheader("Column Overview")
    st.dataframe(column_summary(filtered_df), use_container_width=True)

    if num_cols:
        st.subheader("Numeric Statistics")
        st.dataframe(
            filtered_df[num_cols].describe().T.round(2),
            use_container_width=True,
        )


# ── Tab 3 · Likert Analysis ───────────────────────────────────────────────────
with tab3:
    if not likert_cols:
        st.info("No Likert-scale columns detected (numeric columns with values 1–10).")
    else:
        st.subheader("Likert Scale Summary")
        st.dataframe(likert_summary(filtered_df, likert_cols), use_container_width=True)
        st.subheader("Stacked Response Distribution")
        lf = likert_bar(filtered_df, likert_cols)
        if lf:
            st.plotly_chart(lf, use_container_width=True)


# ── Tab 4 · Correlations ──────────────────────────────────────────────────────
with tab4:
    if len(num_cols) < 2:
        st.info("Need at least 2 numeric columns to compute correlations.")
    else:
        st.subheader("Correlation Heatmap")
        buf = correlation_heatmap(filtered_df, num_cols)
        if buf:
            st.image(buf, use_column_width=True)


# ── Tab 5 · Raw Data ──────────────────────────────────────────────────────────
with tab5:
    st.subheader(f"Filtered Data ({len(filtered_df):,} rows)")
    st.dataframe(filtered_df, use_container_width=True)

    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_survey_data.csv",
        mime="text/csv",
    )
