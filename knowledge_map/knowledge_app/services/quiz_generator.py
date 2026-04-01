"""
quiz generator logic
easy usage - # Generate quiz
    quiz = generate_quiz(example_topics, num_questions=8)
    
    # Display results
    print("=" * 80)
    print("GENERATED QUIZ (Template-Based, No LLM)")
    print("=" * 80)
    
    import json
    
    for i, question in enumerate(quiz, 1):
        print(f"\n{'=' * 80}")
        print(f"QUESTION {i} ({question['type'].upper()}) - Difficulty: {question['difficulty']}")
        print(f"{'=' * 80}")
        print(f"Q: {question['question']}")
        
        if question['type'] == 'multiple_choice':
            for j, choice in enumerate(question['choices'], 1):
                marker = "✓" if choice == question['answer'] else " "
            print(f"  {marker} {choice}")
            print(f"\nAnswer: {question['answer']}")
        
        elif question['type'] == 'fill_in_blank':
            print(f"Options: {', '.join(question['choices'])}")
            print(f"Answer: {question['answer']}")
        
        elif question['type'] == 'true_false':
            print(f"Answer: {question['answer']}")
        
        elif question['type'] == 'matching':
            print(f"Pairs:")
            for pair in question['pairs']:
                print(f"  • {pair['premise']}")
                print(f"    → {pair['response']}\n")

"""
import re
from typing import List, Dict, Any
import random
 
 
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