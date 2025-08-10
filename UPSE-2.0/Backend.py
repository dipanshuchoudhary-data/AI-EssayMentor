import re
import json
import operator
from typing import TypedDict, List, Annotated
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from model_setup import model  


# Constants
BASIC_THRESHOLD = 7.0
PREMIUM_THRESHOLD = 9.0
BASIC_ITERATIONS = 2
PREMIUM_ITERATIONS = 4


# TypedDict for workflow state

class UPSEState(TypedDict):
    essay: str
    language_feedback: str
    clarity_feedback: str
    overall_feedback: str
    analysis_feedback: str
    individual_scores: Annotated[List[float], operator.add]
    improved_essay: str
    max_iterations: int
    avg_score: float
    iteration_count: int
    threshold_score: float
    plan: str
    needs_improvements: bool


def parse_json_response(raw_output: str):
    """
    Extract and parse the first JSON object from the raw model output.
    Raises ValueError if no valid JSON found.
    """
    match = re.search(r'\{.*\}', raw_output, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {raw_output}")

    json_str = match.group(0)

    try:
        data = json.loads(json_str)
        if isinstance(data, str):
            data = json.loads(data)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in extracted string: {json_str}\nOriginal output: {raw_output}") from e


def evaluate_language(state: UPSEState):
    prompt = f"""You are a strict language quality evaluator.
You have 20+ years experience checking UPSE exam essays.
Analyze ONLY language quality: grammar, clarity, coherence, tone, vocabulary.

Essay:
{state['essay']}

Instructions:
1. Provide detailed feedback on grammar, clarity, flow, tone, vocabulary.
2. Give one decimal place score (0.0-10.0).
3. Respond ONLY with minified valid JSON:
{{"feedback":"...","score":0.0}}
"""
    raw_output = model.invoke(prompt).content
    parsed = parse_json_response(raw_output)
    return {
        'language_feedback': parsed['feedback'],
        'individual_scores': [float(parsed['score'])]
    }


def evaluate_analysis(state: UPSEState):
    prompt = f"""You are a strict evaluator of analytical depth for UPSE essays.
Assess ONLY analytical quality: reasoning, evidence, critical thinking, logical connections.

Essay:
{state['essay']}

Instructions:
1. Provide detailed analytical feedback.
2. Score from 0 to 10 (integer).
3. Respond ONLY with minified valid JSON:
{{"feedback":"...","score":0.0}}
"""
    raw_output = model.invoke(prompt).content
    parsed = parse_json_response(raw_output)
    return {
        'analysis_feedback': parsed['feedback'],
        'individual_scores': [float(parsed['score'])]
    }


def evaluate_COT(state: UPSEState):
    prompt = f"""You are a strict evaluator of clarity of thought for UPSE essays.
Assess ONLY logical flow, organization, and ease of understanding.

Essay:
{state['essay']}

Instructions:
1. Provide detailed feedback on logical sequencing, transitions, contradictions, readability.
2. Score 0-10 integer.
3. Respond ONLY with minified valid JSON:
{{"feedback":"...","score":0.0}}
"""
    raw_output = model.invoke(prompt).content
    parsed = parse_json_response(raw_output)
    return {
        'clarity_feedback': parsed['feedback'],
        'individual_scores': [float(parsed['score'])]
    }


def final_evaluation(state: UPSEState):
    scores = state.get('individual_scores', [])
    avg_score = sum(scores) / len(scores) if scores else 0.0

    prompt = f"""You are a summarization expert.
Based on the feedback below, produce a concise, integrated summary emphasizing major mistakes without sugarcoating.

Language feedback:
{state['language_feedback']}

Analysis feedback:
{state['analysis_feedback']}

Clarity feedback:
{state['clarity_feedback']}

Instructions:
1. Merge overlapping points, focus on mistakes.
2. Mention if essay is too short to develop ideas.
3. Keep summary 2-3 sentences.
4. Return ONLY plain text, no JSON or commentary.
"""
    overall_feedback = model.invoke(prompt).content

    plan = state.get('plan', 'free')
    if plan == 'premium':
        threshold = PREMIUM_THRESHOLD
    elif plan == 'basic':
        threshold = BASIC_THRESHOLD
    else:
        threshold = float('inf')

    needs_improvements = (avg_score < threshold) and (plan in ('basic', 'premium'))

    return {
        'overall_feedback': overall_feedback,
        'avg_score': avg_score,
        'threshold_score': threshold,
        'needs_improvements': needs_improvements
    }


def check_quality(state: UPSEState):
    print(f"Quality Check: Score = {state.get('avg_score', 0):.2f}, Iteration = {state.get('iteration_count', 0)}")
    return {}


def should_continue(state: UPSEState) -> str:
    if state['avg_score'] >= state['threshold_score']:
        print(f"✅ Quality threshold met! Average score: {state['avg_score']:.2f}")
        return "end"
    elif state['iteration_count'] >= state['max_iterations']:
        print(f"Max iterations reached ({state['max_iterations']}). Current score: {state['avg_score']:.2f}")
        return "end"
    else:
        print(f"🔄 Continuing improvement. Current score: {state['avg_score']:.2f}, Iteration: {state['iteration_count']}")
        return "improve_essay"


def improve_essay(state: UPSEState):
    prompt = f"""You are an expert UPSC essay writer with mastery in formal, persuasive, and logically coherent writing.

Rewrite this essay improving clarity, language, and analysis, guided by feedback:

Clarity: {state['clarity_feedback']}
Language: {state['language_feedback']}
Analysis: {state['analysis_feedback']}

Original essay:
{state['essay']}

Guidelines:
- Keep original theme and ideas.
- Improve logical flow and vocabulary.
- Deepen analysis with examples.
- Avoid repetition or fluff.
- Slightly expand if quality improves.

Return ONLY the improved essay as plain text.
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


# Build the workflow graph
graph = StateGraph(UPSEState)

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
    should_continue,
    {
        "end": END,
        "improve_essay": "improve_essay"
    }
)

graph.add_edge('improve_essay', 'evaluate_COT')

workflow = graph.compile()
