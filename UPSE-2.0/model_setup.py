# model_setup.py
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

load_dotenv()  # load environment variables once here

model = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
)
