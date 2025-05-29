import os
import logging
import random
import streamlit as st
import pandas as pd
from typing import List, Tuple

# Configure logging
LOG_FILE = os.getenv("LOG_FILE", "prioritizer.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

@st.cache_data
# Use typing List and Tuple for compatibility with Python 3.8
def generate_pairs(n: int) -> List[Tuple[int, int]]:
    """
    Generate and shuffle all unique index pairs for n items.
    """
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    random.shuffle(pairs)
    return pairs


def reset_session() -> None:
    """
    Clear session state for a fresh run.
    """
    for key in ["goals", "pairs", "current", "results"]:
        if key in st.session_state:
            del st.session_state[key]


def record_choice(idx: int) -> None:
    """
    Increment win count for selected index and advance comparison.
    """
    st.session_state.results[idx] += 1
    st.session_state.current += 1


def download_df(df: pd.DataFrame, filename: str = "prioritized_goals.csv") -> None:
    """
    Provide a download button for the DataFrame as CSV.
    """
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )


def main() -> None:
    # Page configuration
    st.set_page_config(
        page_title="Goal Prioritizer",
        page_icon="✅",
        layout="wide"
    )

    # Sidebar with instructions
    st.sidebar.header("How it works")
    st.sidebar.markdown(
        """
        1. Enter 2–10 goals in the text box.
        2. Compare them one pair at a time.
        3. View and download your ranked list.
        """
    )

    # Initialize session state
    if "goals" not in st.session_state:
        reset_session()

    # Goal input form
    if "goals" not in st.session_state or not st.session_state.goals:
        with st.form(key="goal_input_form"):
            goals_text = st.text_area(
                label="Your Goals",
                placeholder="Goal 1\nGoal 2\n...",
                height=200,
                max_chars=1000
            )
            submit = st.form_submit_button("Start Comparisons")

        if submit:
            goals = [g.strip() for g in goals_text.splitlines() if g.strip()]
            if len(goals) < 2:
                st.warning("Enter at least 2 goals to compare.")
            elif len(goals) > 10:
                st.warning("Limit to 10 goals.")
            else:
                st.session_state.goals = goals
                st.session_state.pairs = generate_pairs(len(goals))
                st.session_state.results = {i: 0 for i in range(len(goals))}
                st.session_state.current = 0
                logging.info(f"Session started with goals: {goals}")
                st.experimental_rerun()
        return

    # Pairwise comparison stage
    total = len(st.session_state.pairs)
    idx = st.session_state.current
    progress = idx / total if total > 0 else 1
    st.sidebar.progress(progress)
    st.title("Compare to Prioritize")

    if idx < total:
        i, j = st.session_state.pairs[idx]
        a, b = st.session_state.goals[i], st.session_state.goals[j]
        st.subheader(f"Which goal is more important?  ({idx + 1}/{total})")
        col1, col2 = st.columns(2)
        if col1.button(a):
            record_choice(i)
            logging.info(f"Chosen '{a}' over '{b}'")
            st.experimental_rerun()
        if col2.button(b):
            record_choice(j)
            logging.info(f"Chosen '{b}' over '{a}'")
            st.experimental_rerun()
        return

    # Results stage
    st.success("Ranking complete!")
    results = sorted(
        st.session_state.results.items(), key=lambda x: x[1], reverse=True
    )
    df = pd.DataFrame([
        {"Rank": rank + 1, "Goal": st.session_state.goals[i], "Score": score}
        for rank, (i, score) in enumerate(results)
    ])
    st.table(df)
    download_df(df)

    if st.button("Restart"):
        logging.info("Session reset by user.")
        reset_session()
        st.experimental_rerun()


if __name__ == "__main__":
    main()
