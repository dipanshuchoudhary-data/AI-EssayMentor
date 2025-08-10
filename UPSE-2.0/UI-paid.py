import streamlit as st
from Backend import workflow, UPSEState

st.set_page_config(page_title="UPSC Essay Evaluator & Improver", layout="wide")

st.title("🖋️ UPSC Essay Evaluator & Improver")

st.markdown("""
This tool evaluates your UPSC essay on:
- **Language Quality**
- **Clarity of Thought**
- **Analytical Depth**

It iteratively improves your essay based on your subscription plan until it meets your quality threshold or maximum iterations.
""")

# --- Sidebar for subscription plan & settings ---
st.sidebar.header("⚙️ Settings & Subscription")

plan = st.sidebar.selectbox("Select Subscription Plan", options=["free", "basic", "premium"], index=0)

if plan == "free":
    threshold_default = 5.0
    max_iterations_default = 0
elif plan == "basic":
    threshold_default = 7.0
    max_iterations_default = 2
else:  # premium
    threshold_default = 9.0
    max_iterations_default = 4

threshold_score = st.sidebar.slider("Quality Threshold (0-10)", 0.0, 10.0, threshold_default, 0.1)
max_iterations = st.sidebar.number_input(
    "Max Improvement Iterations",
    min_value=0,
    max_value=10,
    value=max_iterations_default,
    help="Set to 0 for no improvement (only evaluation)."
)

# --- Essay Input ---
st.subheader("✏️ Paste Your Essay")
essay_text = st.text_area("Enter your essay below:", height=300, placeholder="Paste your essay here...")

# --- Run Evaluation ---
run_eval = st.button("▶️ Run Evaluation")

if run_eval:
    if not essay_text.strip():
        st.error("Please paste your essay before running evaluation.")
    else:
        with st.spinner("Running UPSC Essay Evaluation Workflow..."):
            initial_state: UPSEState = {
                'essay': essay_text.strip(),
                'language_feedback': "",
                'clarity_feedback': "",
                'overall_feedback': "",
                'analysis_feedback': "",
                'individual_scores': [],
                'improved_essay': "",
                'max_iterations': max_iterations,
                'avg_score': 0.0,
                'iteration_count': 0,
                'plan': plan,
                'threshold_score': threshold_score,
            }

            output = workflow.invoke(initial_state)

        # --- Display Results ---
        st.success("✅ Evaluation Completed!")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Final Average Score", f"{output['avg_score']:.2f} / 10")
            st.markdown("### 📊 Overall Feedback")
            st.write(output['overall_feedback'])

        with col2:
            st.markdown("### 📝 Final Essay (Improved if available)")
            st.text_area("Essay", value=output.get('essay', essay_text.strip()), height=400)

        # --- Download button ---
        st.download_button(
            label="📥 Download Final Essay",
            data=output.get('essay', essay_text.strip()),
            file_name="final_essay.txt",
            mime="text/plain"
        )

        # --- Conditional Improve Button ---
        if output.get('needs_improvements', False) and max_iterations > 0 and plan != "free":
            if st.button("🛠️ Improve Essay"):
                with st.spinner("Improving essay..."):
                    # Run improve_essay node manually
                    improved_state = initial_state.copy()
                    improved_state.update(output)
                    improved_state['iteration_count'] += 1

                    # Call improve_essay node (assuming you have a separate function)
                    # If not, you can invoke workflow with new state or call improve_essay directly
                    # For demo: just invoke workflow again with improved essay
                    improved_output = workflow.invoke(improved_state)

                st.success("✍️ Improvement Completed!")
                st.text_area("Improved Essay", value=improved_output.get('essay', ''), height=400)
                st.metric("Updated Average Score", f"{improved_output['avg_score']:.2f} / 10")
                
                st.download_button(
                    label="📥 Download Improved Essay",
                    data=improved_output.get('essay', ''),
                    file_name="improved_essay.txt",
                    mime="text/plain"
                )

