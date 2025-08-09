import streamlit as st
import json
from UPSE import workflow 
from UPSE import UPSEState  

st.set_page_config(page_title="UPSC Essay Evaluator", layout="wide")

st.title("🖋️ UPSC Essay Evaluator & Improver")
st.markdown("""
This tool evaluates your UPSC essay on:
- **Language Quality**
- **Clarity of Thought**
- **Analytical Depth**

It will iteratively improve your essay until it meets your desired quality threshold or the maximum iterations are reached.
""")


st.sidebar.header("⚙️ Settings")
threshold_score = st.sidebar.slider("Quality Threshold (0-10)", 0.0, 10.0, 0.0, 0.5)
max_iterations = st.sidebar.number_input("Max Iterations", min_value=1, max_value=10, value=3)


# Essay input
st.subheader("✏️ Paste Your Essay")
essay_text = st.text_area(
    "Enter your essay below:",
    height=300,
    placeholder="Paste your essay here..."
)
run_button = st.button(" Run Evaluation")

# Display area for results
if run_button:
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
                'threshold_score': threshold_score,
            }

            # Run workflow
            output = workflow.invoke(initial_state)

        # Show results
        st.success("✅ Evaluation Completed!")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Final Average Score", f"{output['avg_score']:.2f} / 10")
            st.markdown("### 📊 Overall Feedback")
            st.write(output['overall_feedback'])

        with col2:
            st.markdown("### 📝 Final Improved Essay")
            st.text_area("Improved Essay", value=output['essay'], height=400)


        st.download_button(
            label="📥 Download Improved Essay",
            data=output['essay'],
            file_name="improved_essay.txt",
            mime="text/plain"
        )

