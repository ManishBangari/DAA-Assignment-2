import streamlit as st
import pandas as pd
import io
import logging
import sys, os
from typing import List, Dict

# Setup logging

LOG_DIR = "Logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "allocLogFile.log")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE, mode="a")
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

logger.info("Logger initialized successfully.")

def find_header_case_insensitive(df_cols, target):
    """Return actual column name matching target case-insensitively, or None."""
    for col in df_cols:
        if col.strip().lower() == target.strip().lower():
            return col
    return None

def build_faculty_list(df: pd.DataFrame, cgpa_col_name: str) -> List[str]:
    """Faculty columns are all columns after CGPA in CSV order."""
    cols = list(df.columns)
    cgpa_index = cols.index(cgpa_col_name)
    faculty_cols = cols[cgpa_index+1:]
    return faculty_cols

def compute_fac_pref_counts(df: pd.DataFrame, faculty_cols: List[str]) -> pd.DataFrame:
    """
    Create a DataFrame where each row is a faculty and columns are 'Count Pref 1'..'Count Pref n'
    indicating how many students placed that faculty at preference position p.
    We assume each cell in faculty_cols contains integer preference ranks 1..n.
    """
    n = len(faculty_cols)
    # initialize counts
    rows = []
    for fac in faculty_cols:
        counts = {f"Count Pref {i+1}": 0 for i in range(n)}
        rows.append({"Fac": fac, **counts})
    pref_df = pd.DataFrame(rows).set_index("Fac")
    # Count across all students
    for _, row in df.iterrows():
        for fac in faculty_cols:
            try:
                val = int(row[fac])
            except Exception:
                # if non-integer or missing, skip
                continue
            if 1 <= val <= n:
                pref_df.at[fac, f"Count Pref {val}"] += 1
    pref_df = pref_df.reset_index()
    return pref_df

def allocate_rounds(df_sorted: pd.DataFrame, faculty_cols: List[str]) -> pd.DataFrame:
    """
    Allocation per-cycle (n faculties per cycle).
    For each chunk of n students (in the sorted df order),
    allow each faculty at most one allocation per cycle.
    For each student, pick highest-ranked preference that is still available in that cycle.
    If none available, assign first faculty still available (to ensure each student is allocated).
    """
    n = len(faculty_cols)
    # Safety checks
    if n == 0:
        raise ValueError("No faculty columns detected.")
    # Prepare output
    allocated_rows = []
    total_students = len(df_sorted)
    # Iterate in chunks of n
    for start in range(0, total_students, n):
        chunk = df_sorted.iloc[start:start+n]
        available = set(faculty_cols)  # faculties available in current cycle
        for _, student in chunk.iterrows():
            assigned = None
            # Try preferences in order 1..n
            for pref_rank in range(1, n+1):
                # Find which faculty the student gave rank == pref_rank
                # (student[fac] holds the rank number)
                # iterate faculties to find the one with this rank
                for fac in faculty_cols:
                    try:
                        if int(student[fac]) == pref_rank:
                            if fac in available:
                                assigned = fac
                                break
                    except Exception:
                        # malformed or missing entry -> skip
                        continue
                if assigned is not None:
                    break
            # If no preferred faculty available (rare), assign first available faculty
            if assigned is None:
                if len(available) > 0:
                    # deterministic choice: sort faculty_cols and pick first in that order that is available
                    for fac in faculty_cols:
                        if fac in available:
                            assigned = fac
                            break
                else:
                    # This should not happen: no available faculties left in cycle (all taken).
                    # We'll wrap by selecting the faculty with fewest allocations so far (fallback).
                    assigned = None

            # mark allocated
            if assigned in available:
                available.remove(assigned)
            allocated_rows.append({
                "Roll": student.get(find_header_case_insensitive(df_sorted.columns, "Roll"), ""),
                "Name": student.get(find_header_case_insensitive(df_sorted.columns, "Name"), ""),
                "Email": student.get(find_header_case_insensitive(df_sorted.columns, "Email"), ""),
                "CGPA": student.get(find_header_case_insensitive(df_sorted.columns, "CGPA"), ""),
                "Allocated": assigned if assigned is not None else ""
            })
    allocated_df = pd.DataFrame(allocated_rows)
    return allocated_df

def process_dataframe(df: pd.DataFrame):
    try:
        # detect core columns case-insensitively
        cgpa_col = find_header_case_insensitive(df.columns, "CGPA")
        if cgpa_col is None:
            raise ValueError("CGPA column not found (case-insensitive search).")
        # Find faculty columns
        faculty_cols = build_faculty_list(df, cgpa_col)
        if len(faculty_cols) == 0:
            raise ValueError("No faculty columns found after CGPA.")

        # Convert CGPA column to numeric where possible, keep stable sort (kind='mergesort')
        df[cgpa_col] = pd.to_numeric(df[cgpa_col], errors='coerce')
        # Keep original order index to preserve stability for ties
        df["_orig_index"] = range(len(df))

        # Sort by CGPA descending, stable
        df_sorted = df.sort_values(by=[cgpa_col, "_orig_index"], ascending=[False, True], kind='mergesort').reset_index(drop=True)

        # Build fac preference count CSV (counts of how many students put each faculty at pref pos p)
        pref_counts_df = compute_fac_pref_counts(df, faculty_cols)

        # Allocation per cycle with conflict resolution
        allocated_df = allocate_rounds(df_sorted, faculty_cols)

        # Reorder columns and return
        return allocated_df, pref_counts_df

    except Exception as e:
        logger.exception("Error while processing dataframe: %s", e)
        raise

# Streamlit UI
st.set_page_config(page_title="Faculty Allocation", layout="wide")
st.title("Faculty Allocation — BTP/MTP allocation tool")

st.markdown("""
Upload the CSV with columns: `Roll,Name,Email,CGPA,<faculty columns...>`  
Faculty columns must contain integers 1..n denoting preference rank (1 = first choice).
The program:
- counts faculties dynamically,
- sorts by CGPA (descending),
- processes students in cycles of n (n = number of faculties) and within each cycle allocates highest-ranked available faculty to each student,
- outputs two CSVs: allocation and faculty preference counts.
""")

uploaded_file = st.file_uploader("Upload input CSV", type=["csv"])
if uploaded_file is not None:
    try:
        # read CSV (preserve exact column names as present)
        df_in = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded file:")
        st.dataframe(df_in.head(10))

        if st.button("Run allocation"):
            with st.spinner("Processing..."):
                allocated_df, pref_counts_df = process_dataframe(df_in)
            st.success("Processing done.")

            st.subheader("Allocation (first 20 rows)")
            st.dataframe(allocated_df.head(20))

            st.subheader("Faculty preference counts")
            st.dataframe(pref_counts_df.head(20))

            # prepare CSV bytes for download
            alloc_csv = allocated_df.to_csv(index=False).encode('utf-8')
            pref_csv = pref_counts_df.to_csv(index=False).encode('utf-8')

            st.download_button("Download allocation CSV", data=alloc_csv, file_name="output_btp_mtp_allocation.csv", mime="text/csv")
            st.download_button("Download faculty preference counts", data=pref_csv, file_name="fac_preference_count.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Failed to process file: {e}")
        logger.exception("Failed to process uploaded file")
else:
    st.info("Please upload the input CSV to run allocation.")
