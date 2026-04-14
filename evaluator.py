import pandas as pd
import numpy as np
import warnings
from scipy.stats import ks_2samp

warnings.filterwarnings(
    "ignore",
    category=Warning,
    message=".*sample arguments is too small.*"
)

EPS = 1e-8

def get_numeric_columns(df):
    return df.select_dtypes(include=[np.number]).columns.tolist()

EXCLUDE_COLS = ["title"]

def get_categorical_columns(df):
    return [
        col for col in df.select_dtypes(exclude=[np.number]).columns
        if col not in EXCLUDE_COLS
    ]

def ensure_numeric(df, cols):
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# -------------------------------
# 1. RME (Relative Mean Error)
# -------------------------------

def compute_rme(real_df, syn_df, col):
    mu_real = real_df[col].mean()
    mu_syn = syn_df[col].mean()
    return abs(mu_real - mu_syn) / (abs(mu_real) + EPS)

# -------------------------------
# 2. RCV (Relative Coefficient of Variation)
# -------------------------------

def compute_rcv(real_df, syn_df, col):
    mu_real = real_df[col].mean()
    mu_syn = syn_df[col].mean()

    std_real = real_df[col].std()
    std_syn = syn_df[col].std()

    cv_real = std_real / (abs(mu_real) + EPS)
    cv_syn = std_syn / (abs(mu_syn) + EPS)

    return cv_syn / (cv_real + EPS)

# -------------------------------
# 3. Column Shape (KS Similarity)
# -------------------------------

def ks_similarity(real_df, syn_df, col):
    try:
        stat, _ = ks_2samp(real_df[col].dropna(), syn_df[col].dropna())
        return 1 - stat
    except Exception:
        return np.nan

# -------------------------------
# 4. TVD (Categorical Distribution)
# -------------------------------

def tvd_similarity(real_df, syn_df, col):

    def normalize(x):

        if isinstance(x, list):
            return str(x[0]) if len(x) > 0 else "EMPTY"
        return str(x)

    real_series = real_df[col].apply(normalize)
    syn_series = syn_df[col].apply(normalize)

    real_counts = real_series.value_counts(normalize=True)
    syn_counts = syn_series.value_counts(normalize=True)

    all_categories = set(real_counts.index).union(set(syn_counts.index))

    tvd = 0
    for cat in all_categories:
        tvd += abs(real_counts.get(cat, 0) - syn_counts.get(cat, 0))

    return 1 - (tvd * 0.5)

# -------------------------------
# 5. CPT (Correlation Similarity)
# -------------------------------

def correlation_similarity(real_df, syn_df):
    real_corr = real_df.corr(numeric_only=True)
    syn_corr = syn_df.corr(numeric_only=True)

    real_corr, syn_corr = real_corr.align(syn_corr, join="inner")

    diff = (real_corr - syn_corr).abs()

    mask = np.ones(diff.shape, dtype=bool)
    np.fill_diagonal(mask, 0)

    if mask.sum() == 0:
        return np.nan

    return float(1 - diff[mask].mean().mean())

# -------------------------------
# Report
# -------------------------------

def evaluate(real_df, syn_df):
    print("\n" + "="*60)
    print("QUALITY EVALUATION")
    print("="*60)

    numeric_cols = get_numeric_columns(real_df)
    
    real_df = ensure_numeric(real_df, numeric_cols)
    syn_df = ensure_numeric(syn_df, numeric_cols)
    
    categorical_cols = get_categorical_columns(real_df)

    results = []

    print(f"{"IDEAL SCORES":<25} RME=0.0–0.3 | RCV=0.8–1.2 | KS >0.8 | TVD >0.8 | CPT >0.8\n")

    for col in numeric_cols:
        if col not in syn_df.columns:
            continue

        rme = compute_rme(real_df, syn_df, col)
        rcv = compute_rcv(real_df, syn_df, col)
        ks = ks_similarity(real_df, syn_df, col)

        results.append((col, rme, rcv, ks))

        print(f"{col:<25} RME={rme:.3f}  |  RCV={rcv:.3f}  |  KS={ks:.3f}")
    
    corr_sim = correlation_similarity(real_df, syn_df)
    print(f"\nCPT={corr_sim:.3f}\n")

    for col in categorical_cols:
        if col not in syn_df.columns:
            continue

        tvd_sim = tvd_similarity(real_df, syn_df, col)

        print(f"{col:<25} TVD={tvd_sim:.3f}")

    return {
        "numeric": results,
        "correlation": corr_sim
    }
    