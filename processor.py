"""
processor.py
Data cleaning, column type detection, and Likert/response-rate calculations.
"""

import pandas as pd
import numpy as np


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_file(uploaded_file) -> pd.DataFrame:
    """Load a Streamlit UploadedFile (CSV or Excel) into a DataFrame."""
    name = uploaded_file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
    df.columns = [c.strip() for c in df.columns]
    return df


# ── Column detection ──────────────────────────────────────────────────────────

def detect_numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()


def detect_categorical_cols(df: pd.DataFrame, max_unique: int = 30) -> list[str]:
    cats = []
    for col in df.select_dtypes(include=["object", "category"]).columns:
        if df[col].nunique() <= max_unique:
            cats.append(col)
    return cats


def detect_demographic_cols(df: pd.DataFrame) -> list[str]:
    """Heuristically find demographic columns by common keyword patterns."""
    keywords = ["age", "gender", "sex", "region", "country", "city",
                "education", "income", "occupation", "ethnicity", "race"]
    demos = []
    for col in df.columns:
        if any(kw in col.lower() for kw in keywords):
            demos.append(col)
    # Fall back to all low-cardinality categoricals if nothing found
    if not demos:
        demos = detect_categorical_cols(df)
    return demos


def detect_likert_cols(df: pd.DataFrame) -> list[str]:
    """Return numeric columns whose values all fall within 1-10 (Likert-like)."""
    likert = []
    for col in detect_numeric_cols(df):
        col_min = df[col].dropna().min()
        col_max = df[col].dropna().max()
        if col_min >= 1 and col_max <= 10 and df[col].nunique() <= 10:
            likert.append(col)
    return likert


# ── Cleaning ──────────────────────────────────────────────────────────────────

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Drop completely empty rows/columns
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)
    # Strip string whitespace
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


# ── Statistics ────────────────────────────────────────────────────────────────

def response_rate(df: pd.DataFrame, question_cols: list[str]) -> pd.DataFrame:
    """Return % of non-null responses per question column."""
    total = len(df)
    rows = []
    for col in question_cols:
        filled = df[col].notna().sum()
        rows.append({"Question": col, "Responses": int(filled),
                     "Response Rate (%)": round(filled / total * 100, 1)})
    return pd.DataFrame(rows)


def likert_summary(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Mean, median, and std for each Likert column."""
    rows = []
    for col in cols:
        s = df[col].dropna()
        rows.append({
            "Question": col,
            "Mean": round(s.mean(), 2),
            "Median": round(s.median(), 2),
            "Std Dev": round(s.std(), 2),
            "Count": int(s.count()),
        })
    return pd.DataFrame(rows)


def column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Quick overview: dtype, non-null count, unique values."""
    rows = []
    for col in df.columns:
        rows.append({
            "Column": col,
            "Type": str(df[col].dtype),
            "Non-Null": int(df[col].notna().sum()),
            "Unique Values": int(df[col].nunique()),
            "Sample": str(df[col].dropna().iloc[0]) if df[col].notna().any() else "—",
        })
    return pd.DataFrame(rows)
