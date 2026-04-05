import re
from typing import List, Dict, Any
import random
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

def generate_multiple_choice(topic: Dict[str, Any], topic_num: int) -> Dict[str, Any]:
    """
    Generate a multiple choice question from a topic.
    Format: "Which of these is related to [keywords]?"
    """
    if not topic['keywords'] or not topic['sentences']:
        return None
    
    keywords = topic['keywords'][:5]  # Top 5 keywords
    sentence = topic['sentences'][0]
    
    # Extract a keyword phrase from the sentence
    answer = keywords[0]
    
    # Use other keywords as distractors
    distractors = keywords[1:4] if len(keywords) > 3 else keywords[1:]
    
    # Pad with random keywords if needed
    while len(distractors) < 3:
        distractors.append(keywords[-1])
    
    choices = [answer] + distractors[:3]
    random.shuffle(choices)
    
    return {
        'id': f"q_{topic_num}_mc",
        'type': 'multiple_choice',
        'question': f"Which term is most relevant to: '{sentence[:80]}...'?",
        'choices': choices,
        'answer': answer,
        'topic_id': topic['topic_id'],
        'difficulty': 'easy'
    }
 
 
def generate_fill_in_blank(topic: Dict[str, Any], topic_num: int) -> Dict[str, Any]:
    """
    Generate a fill-in-the-blank question.
    Remove a keyword from a sentence and ask student to fill it in.
    """
    if not topic['sentences'] or not topic['keywords']:
        return None
    
    sentence = topic['sentences'][1] if len(topic['sentences']) > 1 else topic['sentences'][0]
    keywords = topic['keywords'][:5]
    
    # Find which keyword appears in the sentence
    for keyword in keywords:
        if keyword.lower() in sentence.lower():
            # Create blank version
            blank_sentence = re.sub(
                re.compile(re.escape(keyword), re.IGNORECASE),
                "_____",
                sentence,
                count=1
            )
            
            # Get distractors
            distractors = [kw for kw in keywords if kw != keyword][:3]
            
            choices = [keyword] + distractors
            random.shuffle(choices)
            
            return {
                'id': f"q_{topic_num}_fib",
                'type': 'fill_in_blank',
                'question': blank_sentence,
                'choices': choices,
                'answer': keyword,
                'topic_id': topic['topic_id'],
                'difficulty': 'medium'
            }
    
    # Fallback: use first keyword
    return {
        'id': f"q_{topic_num}_fib",
        'type': 'fill_in_blank',
        'question': f"The main concept in this topic is: _____",
        'choices': keywords[:4],
        'answer': keywords[0],
        'topic_id': topic['topic_id'],
        'difficulty': 'easy'
    }
 
 
def generate_true_false(topic: Dict[str, Any], topic_num: int) -> Dict[str, Any]:
    """
    Generate a true/false question.
    Use sentences as true statements, create false negations.
    """
    if not topic['sentences']:
        return None
    
    sentence = topic['sentences'][2] if len(topic['sentences']) > 2 else topic['sentences'][0]
    
    # Extract the main subject and predicate
    # Simple heuristic: split by common verbs
    verbs = ['enables', 'uses', 'requires', 'helps', 'creates', 'improves', 'prevents']
    negation_verbs = ['disables', 'avoids', 'forbids', 'prevents', 'stops', 'blocks']
    
    is_true = random.choice([True, True, False])  # 66% true statements
    
    if is_true:
        return {
            'id': f"q_{topic_num}_tf",
            'type': 'true_false',
            'question': sentence,
            'answer': True,
            'topic_id': topic['topic_id'],
            'difficulty': 'medium'
        }
    else:
        # Create a false statement by negation
        modified_sentence = sentence
        for verb in verbs:
            if verb in sentence.lower():
                opposite_verb = negation_verbs[verbs.index(verb)]
                modified_sentence = re.sub(
                    re.compile(verb, re.IGNORECASE),
                    opposite_verb,
                    sentence,
                    count=1
                )
                break
        
        return {
            'id': f"q_{topic_num}_tf",
            'type': 'true_false',
            'question': modified_sentence,
            'answer': False,
            'topic_id': topic['topic_id'],
            'difficulty': 'medium'
        }
 
 
def generate_matching(topics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a matching question across multiple topics.
    Match key terms to their topic descriptions.
    """
    if len(topics) < 2:
        return None
    
    selected_topics = random.sample(topics, min(4, len(topics)))
    
    # Create premise-response pairs
    pairs = []
    for topic in selected_topics:
        keyword = topic['keywords'][0]
        sentence = topic['sentences'][0][:100]
        pairs.append({
            'premise': keyword,
            'response': sentence
        })
    
    return {
        'id': 'q_matching',
        'type': 'matching',
        'question': 'Match the key terms with their descriptions:',
        'pairs': pairs,
        'answer_map': {p['premise']: p['response'] for p in pairs},
        'difficulty': 'hard'
    }
 
 
def generate_quiz(topics: List[Dict[str, Any]], num_questions: int = None) -> List[Dict[str, Any]]:
    """
    Generate a complete quiz from BERTopic output.
    
    Args:
        topics: Output from extract_topics()
        num_questions: Number of questions to generate (default: 2 per topic)
    
    Returns:
        List of quiz questions
    """
    if not topics:
        return []
    
    if num_questions is None:
        num_questions = len(topics) * 2
    
    quiz = []
    question_types = ['multiple_choice', 'fill_in_blank', 'true_false']
    topic_idx = 0
    q_count = 0
    
    # Generate questions cycling through types
    while q_count < num_questions and topic_idx < len(topics):
        topic = topics[topic_idx]
        question_type = question_types[q_count % len(question_types)]
        
        question = None
        if question_type == 'multiple_choice':
            question = generate_multiple_choice(topic, q_count)
        elif question_type == 'fill_in_blank':
            question = generate_fill_in_blank(topic, q_count)
        elif question_type == 'true_false':
            question = generate_true_false(topic, q_count)
        
        if question:
            quiz.append(question)
            q_count += 1
        
        topic_idx = (topic_idx + 1) % len(topics)
    
    # Add one matching question if we have enough topics
    if len(topics) >= 2:
        matching = generate_matching(topics)
        if matching:
            quiz.append(matching)
    
    return quiz


    # ------------------------- Raw PDF to OpenAi integration -----------------------------
def generate_quiz_from_text(quiz, text, num_questions=5, question_types=None, difficulty="medium"):
    """
    Generate quiz questions from raw text using OpenAI.
    Saves questions directly to the database.
    """
    # Don't generate if there is no text to work with
    if not text:
        return

    # Default to multiple choice and true/false if no types specified
    if question_types is None:
        question_types = ["multiple_choice", "true_false"]

    # Set up the OpenAI client using the API key from the environment
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Build the prompt telling OpenAI how many questions to generate and what format to return
    prompt = f"""
You are a quiz generator. Generate {num_questions} quiz questions from the following text.
Difficulty level: {difficulty}
Question types to use: {', '.join(question_types)}

Return ONLY a JSON array with no extra text or markdown. Each question should follow this format:

For multiple_choice:
{{
    "question_text": "...",
    "question_type": "multiple_choice",
    "choices": ["choice1", "choice2", "choice3", "choice4"],
    "correct_answer": "choice1"
}}

For fill_in_blank:
{{
    "question_text": "RAM is volatile _____ used during execution.",
    "question_type": "fill_in_blank",
    "choices": ["memory", "storage", "data", "hardware"],
    "correct_answer": "memory"
}}
IMPORTANT: fill_in_blank questions MUST always include exactly 4 choices including the correct answer.

For true_false:
{{
    "question_text": "...",
    "question_type": "true_false",
    "choices": ["True", "False"],
    "correct_answer": "True"
}}

For matching:
{{
    "question_text": "Match each term with its correct description:",
    "question_type": "matching",
    "choices": [],
    "correct_answer": "",
    "pairs": [
        {{"premise": "term1", "response": "description1"}},
        {{"premise": "term2", "response": "description2"}},
        {{"premise": "term3", "response": "description3"}}
    ]
}}

Text to generate questions from:
{text[:4000]}
"""

    try:
        # Send the prompt to OpenAI and get the response
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a helpful quiz generator. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
        )

        # Extract the raw text response from OpenAI
        raw = response.choices[0].message.content.strip()

        # Strip markdown code blocks if OpenAI wraps the JSON in them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        # Parse the JSON response into a list of question dictionaries
        questions_data = json.loads(raw)

        # Save each generated question to the database
        from ..models import Question
        for order, q_data in enumerate(questions_data, start=1):
            Question.objects.create(
                quiz=quiz,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                choices=q_data.get("choices", []),
                correct_answer=q_data.get("correct_answer", ""),
                pairs=q_data.get("pairs", []),
                order=order,
            )

    except Exception as e:
        # Log any errors without crashing the app
        print(f"Quiz generation error: {e}")