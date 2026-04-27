from openai import OpenAI
from django.conf import settings
import json


def generate_knowledge_map_data(text):
    """
    Takes extracted PDF text and uses OpenAI to generate
    topics, summaries and relationships in one call.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""
    Analyse the following text and extract a knowledge map. 
    
    Extract AS MANY topics as the text contains. For a long text extract as many distinct topics as you can find.
    Each topic should represent a distinct concept or theme from the text. There MUST be at least 10
    topics for texts that are longer
    Make sure each topic and the summary makes logical sense

    IMPORTANT INSTRUCTIONS:
    - Each summary MUST be 3 to 10 sentences long
    - Each summary must explain the topic in detail, covering its key aspects, significance and how it relates to the document
    - Do not write one sentence summaries under any circumstances

    Return a JSON object in this exact format:
    {{
        "topics": [
            {{
                "label": "Topic label (max 5 words)",
                "summary": "A detailed 3-10 sentence summary explaing the topic in depth, covering its key aspects and significants. Provide examples as well if applicable",
                "keywords": ["keyword1", "keyword2", "keyword3"]
            }}
        ],
        "relationships": [
            {{
                "source": "Topic label",
                "target": "Topic label",
                "label": "relationship description"
            }}
        ]
    }}

    Text:
    {text[:8000]}
    """

    response = client.responses.create(
        model="gpt-5.1-codex-mini",
        instructions="You are a knowledge map generator. When writing topic summaries you MUST write exactly 3 to 10 sentences per summary. Never write a one sentence summary. Each summary must be detailed and thorough.",
        input=prompt,
        max_output_tokens=4000
    )

    content = response.output_text.strip()
    # Strip markdown code fences if present
    content = content.replace('```json', '').replace('```', '').strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        # Log errors and return empty structures so the task doesn't crash
        print(
            f"Failed to parse OpenAI response as JSON: {e}\nResponse was: {content}")
        return [], []

    # Validate and filter topics — skip any missing required fields
    raw_topics = data.get('topics', [])
    topics = []
    for topic in raw_topics:
        if not isinstance(topic, dict):
            print(f"Skipping malformed topic (not a dict): {topic}")
            continue
        if not all(k in topic for k in ('label', 'summary', 'keywords')):
            print(f"Skipping topic missing required fields: {topic}")
            continue
        if not isinstance(topic['keywords'], list):
            print(f"Skipping topic with invalid keywords field: {topic}")
            continue
        topics.append(topic)

    # Validate and filter relationships — skip any missing required fields
    raw_relationships = data.get('relationships', [])
    relationships = []
    for rel in raw_relationships:
        if not isinstance(rel, dict):
            print(f"Skipping malformed relationship (not a dict): {rel}")
            continue
        if not all(k in rel for k in ('source', 'target', 'label')):
            print(f"Skipping relationship missing required fields: {rel}")
            continue
        relationships.append(rel)

    return topics, relationships
