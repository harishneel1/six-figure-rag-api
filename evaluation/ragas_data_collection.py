"""
RAGAS Data Collection Script
Runs test questions through your RAG system and collects evaluation data.
"""

import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.retrieval.index import retrieve_context
from src.rag.retrieval.utils import prepare_prompt_and_invoke_llm

# Configuration
PROJECT_ID = "6d090d75-7c7c-428c-bba8-258cf3f45d2d"

TEST_QUESTIONS = [
    "What is the Big Bang theory?",
    "How many neurons does the human brain contain?",
    "Who invented cuneiform writing?",
    "What percentage of the universe is made up of dark matter?",
    "What are the main functions of dopamine in the brain?",
    "When was the Great Pyramid of Giza built?",
    "What are the three types of omega-3 fatty acids?",
    "What is the hippocampus responsible for?",
    "How much fiber should adults consume daily?",
    "What caused the Bronze Age Collapse?",
    "What is the difference between saturated and unsaturated fats?",
    "When were gravitational waves first detected?",
    "What are the two main divisions of the nervous system?",
    "What triggered the Arab Spring in 2011?",
    "Why is vitamin D important for bone health?",
    "How does cosmic inflation explain the uniformity of the universe?",
    "What role does the amygdala play in the brain?",
    "What were the main causes of World War I?",
    "How do probiotics and prebiotics differ?",
    "What happens to massive stars at the end of their lives?",
    "What is neuroplasticity and why is it important?",
    "What was the significance of the Code of Hammurabi?",
    "Why are trans fats considered unhealthy?",
    "What is the relationship between the thalamus and sensory information?",
    "How did the COVID-19 pandemic affect global economies?"
]


def collect_rag_data(project_id: str, questions: list) -> list:
    """Run questions through RAG pipeline and collect data."""
    dataset = []
    
    for question in questions:
        print(f"Processing: {question}")
        
        # Retrieve context
        texts, images, tables, citations = retrieve_context(project_id, question)
        
        # Prepare contexts for RAGAS
        contexts = texts + [f"[TABLE]\n{table}" for table in tables]
        
        # Generate answer
        answer = prepare_prompt_and_invoke_llm(question, texts, [], tables)
        
        dataset.append({
            "question": question,
            "contexts": contexts or ["No context found"],
            "answer": answer
        })
    
    return dataset


if __name__ == "__main__":
    # Collect and save data
    dataset = collect_rag_data(PROJECT_ID, TEST_QUESTIONS)
    
    output_path = Path(__file__).parent / "datasets" / "ragas_evaluation_dataset.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(dataset)} questions to {output_path}")