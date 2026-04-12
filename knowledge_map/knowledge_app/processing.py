from sklearn.feature_extraction.text import CountVectorizer
from openai import OpenAI
from django.conf import settings

def generate_knowledge_map_data(text):
    """
    Takes extracted PDF text and uses OpenAI to generate
    topics, subtopics, summaries and relationship in one call
    """

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""
    Analyse the following text and extract a knowledge map.

    Return a JSON object in this exact format:
    {{
        "topics": [
            {{
                "label": "Topic label (max 5 words)",
                "summary": "One sentence summary",
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
        input=prompt
    )

    import json
    content = response.output_text.strip()
    # Strip markdown code fences if present
    content = content.replace('```json', '').replace('```', '').strip()
    data = json.loads(content)

    return data['topics'], data['relationships']