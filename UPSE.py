from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from typing import TypedDict, List
from typing_extensions import Annotated
import operator
import json

load_dotenv()
import os 

model = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
)

from pydantic import BaseModel, Field

class Schema(BaseModel):
    feedback: str = Field(description="Detailed feedback for the essay")
    score: float = Field(description="Score out of 10", ge=0, le=10)

str_model = model.with_structured_output(Schema)


class UPSEState(TypedDict):
    essay: str
    language_feedback: str
    clarity_feedback: str
    overall_feedback: str
    analysis_feedback: str
    individual_scores: Annotated[list[float], operator.add]
    improved_essay: str
    max_iterations: int
    avg_score: float
    iteration_count: int
    threshold_score: float


def llm_json(old_output):
    if isinstance(old_output,str):
        try:
            once = json.loads(old_output)
            if isinstance(once,str):
                once = json.loads(once)
            return once

        except json.JSONDecodeError:
            raise ValueError(f"Invaild JSON from model :{old_output}")
        
    return old_output


def evaluate_language(state: UPSEState):
    prompt = f"""You are a strict language quality evaluator.
    You have 20 + experience in checking UPSE exam (Largest and most important exam of India).
Analyze the essay below ONLY for language quality — focusing on grammar, clarity, coherence, adherence to a formal tone, and vocabulary richness. Do NOT assess content accuracy or factual correctness.

Essay to evaluate:
{state['essay']}

Instructions:
1. Provide constructive, detailed feedback explaining strengths and weaknesses in each of these areas:
   - Grammar and syntax
   - Clarity and readability
   - Logical flow and coherence
   - Consistency of formal tone
   - Vocabulary variety and precision
2. Assign a single numerical score for overall language quality on a scale from 0.0 to 10.0.
   - Use one decimal place (e.g., 8.5).
   - Higher scores mean better language quality.
3. Respond ONLY with valid JSON (not as a string), minified, no spaces or newlines outside of strings, no additional commentary. 
Do not escape quotation marks except inside string values.


Required JSON output format:
{{
  "feedback": "your detailed feedback here",
  "score": 0.0
}}
"""

    output = llm_json(str_model.invoke(prompt))
    return {'language_feedback': output.feedback, 'individual_scores': [output.score]}



def evaluate_analysis(state: UPSEState):
    prompt = f"""You are a strict evaluator of analytical depth in essays.
You have 20 + experience in checking UPSE exam (Largest and most important exam of India).
 Assess ONLY the depth and quality of analysis, not language or grammar.

Essay to evaluate:
{state['essay']}

Instructions:
1. Provide detailed, constructive feedback covering:
   - Quality of reasoning and argumentation
   - Use of evidence, data, or examples
   - Critical thinking and originality of ideas
   - Ability to connect points logically
2. Assign a single integer score from 0 to 10 for overall analytical depth.
   - 0 = no meaningful analysis
   - 10 = exceptionally deep, nuanced, and well-supported analysis
3. Respond ONLY with valid JSON (not as a string), minified, no spaces or newlines outside of strings, no additional commentary. 
Do not escape quotation marks except inside string values.


Required JSON output format:
{{
  "feedback": "your detailed feedback here",
  "score": 0.0
}}
"""

    output = llm_json(str_model.invoke(prompt))
    return {'analysis_feedback': output.feedback, 'individual_scores': [output.score]}



def evaluate_COT(state: UPSEState):
    prompt = f"""You are a strict evaluator of clarity of thought in essays.
    Assess ONLY the logical flow, organization, and ease of understanding — do not evaluate grammar, vocabulary, or analytical depth.
    You have 20 + experience in checking UPSE exam (Largest and most important exam of India).

Essay to evaluate:
{state['essay']}

Instructions:
1. Provide detailed, constructive feedback covering:
   - Logical sequencing of ideas
   - Smoothness of transitions between points
   - Avoidance of contradictions or confusion
   - Overall ease for the reader to follow the argument
2. Assign a single integer score from 0 to 10 for overall clarity of thought.
   - 0 = completely incoherent and confusing
   - 10 = exceptionally clear, logically structured, and easy to follow
3.Respond ONLY with valid JSON (not as a string), minified, no spaces or newlines outside of strings, no additional commentary. 
Do not escape quotation marks except inside string values.


Required JSON output format:
{{
  "feedback": "your detailed feedback here",
  "score": 0.0
}}
"""

    output = llm_json(str_model.invoke(prompt))
    return {'clarity_feedback': output.feedback, 'individual_scores': [output.score]}


# Function for final summary
def final_evaluation(state: UPSEState):
    prompt = f"""You are a summarization expert.
Based on the three feedback sections below, produce a concise, integrated summary that captures the most important improvement points and strengths from all of them.

Language feedback:
{state["language_feedback"]}

Analysis feedback:
{state["analysis_feedback"]}

Clarity feedback:
{state["clarity_feedback"]}

Instructions:
1. Identify and merge overlapping points from the three feedback types.
2.If the essay is too short to fully explore the topic, clearly state this and explain how adding more details/examples could improve the score.
3. Remove redundancy and keep the tone constructive.
4. Keep the summary between 2 and 3 sentences.
5. Talk about majorly on mistakes .Dont apply butter .Stay forward .Finds mistakes in essay.
6. Return ONLY the summarized feedback as plain text, without JSON, code fences, or additional commentary.
"""
    overall_feedback = model.invoke(prompt).content
    avg_score = sum(state['individual_scores']) / len(state['individual_scores']) if state['individual_scores'] else 0.0
    return {'overall_feedback': overall_feedback, 'avg_score': avg_score}



def check_quality(state: UPSEState):
    print(f" Quality Check: Score = {state['avg_score']:.2f}, Iteration = {state['iteration_count']}")
    

    return {}  

def should_continue(state: UPSEState) -> str:
    """Determines whether to continue improving or end the workflow"""
    if state['avg_score'] >= state['threshold_score']:
        print(f"✅ Quality threshold met! Average score: {state['avg_score']:.2f}")
        return "end"
    elif state['iteration_count'] >= state['max_iterations']:
        print(f" Max iterations reached ({state['max_iterations']}). Current score: {state['avg_score']:.2f}")
        return "end"
    else:
        print(f"🔄 Continuing improvement. Current score: {state['avg_score']:.2f}, Iteration: {state['iteration_count']}")
        return "improve_essay"
    


def improve_essay(state: UPSEState):
    prompt = f"""You are an expert UPSC essay writer with mastery in formal, persuasive, and logically coherent writing.

Task:
Rewrite the following essay to significantly enhance:
1. Clarity of thought (based on the provided feedback)
2. Language quality (based on the provided feedback)
3. Analytical depth (based on the provided feedback)

Feedback for reference:
- Clarity of Thought: {state["clarity_feedback"]}
- Language Quality: {state["language_feedback"]}
- Analytical Depth: {state["analysis_feedback"]}

Essay to improve:
{state["essay"]}

Guidelines:
- Preserve the original theme and key ideas.
- Organize arguments in a clear, logical flow.
- Use precise vocabulary, formal tone, and cohesive transitions.
- Deepen the analysis where relevant, with well-reasoned arguments and illustrative examples.
- Avoid unnecessary repetition or fluff.
- Do not shorten excessively; keep or slightly expand the word count if it improves quality.

Output Instructions:
Return ONLY the improved essay as plain text — no headings, notes, explanations, or JSON.
"""

    improved = model.invoke(prompt).content
    return {
        "essay": improved,
        "iteration_count": state.get("iteration_count", 0) + 1,
       
        "individual_scores": [],
        "language_feedback": "",
        "clarity_feedback": "",
        "analysis_feedback": "",
        "overall_feedback": ""
    }


graph = StateGraph(UPSEState)

# Add all nodes
graph.add_node('evaluate_COT', evaluate_COT)
graph.add_node('evaluate_analysis', evaluate_analysis)
graph.add_node('evaluate_language', evaluate_language)
graph.add_node('final_evaluation', final_evaluation)
graph.add_node('check_quality', check_quality)
graph.add_node('improve_essay', improve_essay)


graph.add_edge(START, 'evaluate_COT')
graph.add_edge('evaluate_COT', 'evaluate_analysis')
graph.add_edge('evaluate_analysis', 'evaluate_language')
graph.add_edge('evaluate_language', 'final_evaluation')
graph.add_edge('final_evaluation', 'check_quality')

graph.add_conditional_edges(
    'check_quality',
    should_continue,  # This function determines the routing
    {
        "end": END,
        "improve_essay": "improve_essay"
    }
)

graph.add_edge('improve_essay', 'evaluate_COT')

workflow = graph.compile()


# if __name__ == "__main__":
#     initial_state = {
#         'essay': """Artificial Intelligence (AI) is not just a technological breakthrough—it is a strategic imperative for nations in the 21st century. For India, AI presents a historic opportunity to drive inclusive growth, strengthen governance, and position itself as a global digital leader.

# India's strengths lie in its vast digital ecosystem, young tech-savvy population, and rich data reserves. Recognizing this, NITI Aayog's #AIForAll initiative identifies key sectors for AI deployment: agriculture, healthcare, education, smart mobility, and infrastructure.

# AI is already enhancing public service delivery through:

# Predictive analytics in healthcare (e.g., Aarogya Setu)
# Crop monitoring via satellite data and ML
# Chatbots in citizen services
# Facial recognition for law enforcement

# However, challenges remain—job displacement, data privacy, algorithmic bias, and lack of regulation demand immediate attention. India's future in AI must balance innovation with ethics, inclusion with efficiency, and automation with accountability.

# If harnessed responsibly, AI can transform India into a technology-driven welfare state, empowering citizens and ensuring efficient, transparent, and responsive governance""",
#         'language_feedback': "",
#         'clarity_feedback': "",
#         'overall_feedback': "",
#         'analysis_feedback': "",
#         'individual_scores': [],
#         'improved_essay': "",
#         'max_iterations': 3,
#         'avg_score': 0.0,
#         'iteration_count': 0,
#         'threshold_score': 7.0,
#     }

#     try:
#         print(" Starting UPSC Essay Evaluation Workflow...")
#         output = workflow.invoke(initial_state)
        
#         print("\n" + "="*80)
#         print(" FINAL RESULTS")
#         print("="*80)
#         print(f"Final Average Score: {output['avg_score']:.2f}/10")

        
#         print(f"\n Overall Feedback:\n{output['overall_feedback']}")
#         print(f"\n Final Essay:\n{output['essay']}")

        

