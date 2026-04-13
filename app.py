# app.py

import streamlit as st
import pandas as pd
import io
from ollama_service import generate_rows

st.set_page_config(
    page_title="BGP Data Generator",
    page_icon="🔀",
    layout="wide"
)

st.title("BGP Synthetic Data Generator")
st.caption("Powered by LLaMA via Ollama — runs entirely on your machine")

# ─────────────────────────────────────────────
# STAGE 1 — Upload
# ─────────────────────────────────────────────
st.header("Step 1 — Upload your dataset")

uploaded_file = st.file_uploader(
    "Upload your BGP CSV file",
    type=["csv"],
    help="Upload the BGP Network dataset CSV"
)

n = st.number_input(
    "How many rows to generate?",
    min_value=1,
    max_value=50,
    value=10
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.success(f"Loaded {len(df)} rows and {len(df.columns)} columns")

    with st.expander("Preview original data (first 5 rows)"):
        st.dataframe(df.head())

    st.divider()

    # ─────────────────────────────────────────────
    # STAGE 2 — Generate
    # ─────────────────────────────────────────────
    st.header("Step 2 — Generate new rows with LLaMA")

    if st.button("Generate rows", type="primary", use_container_width=True):
        with st.spinner("LLaMA is analysing your data and generating rows... this may take 30–60 seconds"):
            try:
                valid_rows, rejected_rows = generate_rows(df, n)
                st.session_state["valid_rows"] = valid_rows
                st.session_state["rejected_rows"] = rejected_rows
                st.session_state["original_df"] = df
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()

    # ─────────────────────────────────────────────
    # STAGE 3 — Preview and approve
    # ─────────────────────────────────────────────
    if "valid_rows" in st.session_state:
        valid_rows = st.session_state["valid_rows"]
        rejected_rows = st.session_state["rejected_rows"]
        original_df = st.session_state["original_df"]

        st.divider()
        st.header("Step 3 — Review generated rows")

        col1, col2 = st.columns(2)
        col1.metric("Valid rows generated", len(valid_rows))
        col2.metric("Rejected (failed validation)", len(rejected_rows))

        if rejected_rows:
            with st.expander(f"See {len(rejected_rows)} rejected rows and reasons"):
                for item in rejected_rows:
                    st.error(f"Reason: {item['reason']}")
                    st.json(item["row"])

        if valid_rows:
            st.subheader("Select rows to include in your dataset")
            st.caption("Uncheck any rows you want to discard before downloading")

            approved_indices = []

            for i, row in enumerate(valid_rows):
                col_check, col_data = st.columns([0.5, 9.5])
                checked = col_check.checkbox(
                    "",
                    value=True,
                    key=f"row_{i}"
                )
                with col_data:
                    st.dataframe(
                        pd.DataFrame([row]),
                        use_container_width=True,
                        hide_index=True
                    )
                if checked:
                    approved_indices.append(i)

            approved_rows = [valid_rows[i] for i in approved_indices]

            st.info(f"{len(approved_rows)} rows selected for download")

            # ─────────────────────────────────────────────
            # STAGE 4 — Download
            # ─────────────────────────────────────────────
            st.divider()
            st.header("Step 4 — Download expanded dataset")

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Original rows", len(original_df))
            col_b.metric("Rows added", len(approved_rows))
            col_c.metric("Total rows", len(original_df) + len(approved_rows))

            if approved_rows:
                approved_df = pd.DataFrame(approved_rows)
                final_df = pd.concat(
                    [original_df, approved_df],
                    ignore_index=True
                )

                # convert to CSV in memory
                csv_buffer = io.StringIO()
                final_df.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue().encode()

                st.download_button(
                    label="Download BGP_expanded.csv",
                    data=csv_bytes,
                    file_name="BGP_expanded.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
            else:
                st.warning("No rows selected. Check at least one row to download.")