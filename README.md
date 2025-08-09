UPSC Essay Evaluation Workflow (LangGraph)
This project uses LangGraph to implement a modular, node-based essay evaluation system for UPSC (Union Public Service Commission) aspirants. The system evaluates essays, provides detailed feedback, and—depending on subscription plans—can improve essays through iterative LLM-based enhancements.

Features
Node-based LangGraph workflow for clarity and maintainability

Evaluation nodes for:

Language quality

Clarity of thought

Analytical depth

Dynamic scoring thresholds per subscription tier

Optional improvement branch triggered after evaluation

Structured JSON outputs for seamless integration

Subscription-aware iterations (Basic vs Premium) *

How It Works (LangGraph Flow)
User submits an essay → Start Node

Essay flows through Language Evaluation, Clarity Evaluation, and Analysis Evaluation nodes

Aggregate Score Node calculates final score and produces overall feedback

If score < plan threshold:

Free Plan → End

Basic Plan → Pass through Improve Essay Node (1 iteration)

Premium Plan → Pass through Improve Essay Node (up to 3 iterations)

End Node returns results in JSON format

* The feature of subscription is available in UPSE 2.0 folder.

