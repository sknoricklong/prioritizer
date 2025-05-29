import os
import logging
import random
import streamlit as st
import pandas as pd
from typing import List, Tuple

# Personalization and Theming
CSS = """
<style>
:root {
  --primary-color: #DC143C;
  --background-color: #FFFFFF;
  --secondary-background-color: #FFE4E1;
  --text-color: #000000;
}
body {
  background-color: var(--secondary-background-color) !important;
}
.stApp {
  background-color: var(--background-color) !important;
}
h1, h2, h3, .css-1ilw2u2 {
  color: var(--primary-color) !important;
}
.css-1um9o0a, .css-1q8dd3e {
  background-color: var(--primary-color) !important;
}
button {
  background-color: var(--primary-color) !important;
}
</style>
"""

def generate_pairs(n: int) -> List[Tuple[int, int]]:
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    random.shuffle(pairs)
    return pairs


def reset_session() -> None:
    for key in ["goals", "pairs", "current", "results"]:
        st.session_state.pop(key, None)


def record_choice(idx: int) -> None:
    st.session_state.results[idx] += 1
    st.session_state.current += 1


def download_df(df: pd.DataFrame, filename: str = "prioritized_goals.csv") -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )


def main() -> None:
    # Inject custom CSS
    st.markdown(CSS, unsafe_allow_html=True)

    # Page config
    st.set_page_config(
        page_title="Paul Nolan's Prioritizer",
        page_icon="🔴",
        layout="wide"
    )

    # Logging setup
    LOG_FILE = os.getenv("LOG_FILE", "prioritizer.log")
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # Sidebar personalization
    st.sidebar.header("Welcome, Paul Nolan")
    st.sidebar.subheader("Crimson Theme Enabled")
    st.sidebar.markdown(
        """
        **How it works:**  
        1. Enter 2–10 goals.  
        2. Compare them pairwise.  
        3. Download your prioritized list.
        """
    )

    # Initialize session
    if "goals" not in st.session_state:
        reset_session()

    # Input step
    if "goals" not in st.session_state or not st.session_state.goals:
        with st.form("goals_form"):
            st.text_area("Your Goals",
                         placeholder="Goal 1\nGoal 2\n...",
                         height=200,
                         max_chars=1000,
                         key="goals_input")
            if st.form_submit_button("Start Comparisons"):
                goals = [g.strip() for g in st.session_state.goals_input.splitlines() if g.strip()]
                if not 2 <= len(goals) <= 10:
                    st.warning("Enter between 2 and 10 goals.")
                else:
                    st.session_state.goals = goals
                    st.session_state.pairs = generate_pairs(len(goals))
                    st.session_state.results = {i: 0 for i in range(len(goals))}
                    st.session_state.current = 0
                    logging.info(f"Paul Nolan started session with goals: {goals}")
                    st.experimental_rerun()
        return

    # Comparison step
    total = len(st.session_state.pairs)
    idx = st.session_state.current
    st.sidebar.progress(idx / total if total else 1)
    st.title("📊 Compare and Prioritize")

    if idx < total:
        i, j = st.session_state.pairs[idx]
        opt_a, opt_b = st.session_state.goals[i], st.session_state.goals[j]
        st.subheader(f"Which matters more? ({idx+1}/{total})")
        c1, c2 = st.columns(2)
        if c1.button(opt_a):
            record_choice(i)
            logging.info(f"Paul chose '{opt_a}' over '{opt_b}'")
            st.experimental_rerun()
        if c2.button(opt_b):
            record_choice(j)
            logging.info(f"Paul chose '{opt_b}' over '{opt_a}'")
            st.experimental_rerun()
        return

    # Results step
    st.success("Done! Here's your ranking:")
    ranked = sorted(st.session_state.results.items(), key=lambda x: x[1], reverse=True)
    df = pd.DataFrame([{"Rank": r+1, "Goal": st.session_state.goals[i], "Score": s}
                        for r, (i, s) in enumerate(ranked)])
    st.table(df)
    download_df(df)

    if st.button("Restart"):
        logging.info("Paul reset the session.")
        reset_session()
        st.experimental_rerun()


if __name__ == "__main__":
    main()
