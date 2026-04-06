from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from openai import OpenAI
from django.conf import settings

def extract_topics(text):
    """
    Takes extracted PDF text and returns topic clusters using BERTopic.
    Returns a list of topics with their keywords.
    """

    #Split text into sentences for BERTopic to process
    docs = [sent.strip() for sent in text.split('.') if len(sent.strip()) > 10]

    if len(docs) < 10:
        return None, "Not enough text to generate topics"

    # Vectorize removes commons English words
    vectorizer = CountVectorizer(stop_words="english")

    # Create BERTopic model
    topic_model = BERTopic(
        vectorizer_model=vectorizer,
        nr_topics="auto",               #determines number of topics
        min_topic_size=3                #minimum number of sentences per topic
        )

    # Fit the model and get topic assignments
    topics, probs = topic_model.fit_transform(docs)

    # Get topic info (id, count, keywords)
    topic_info = topic_model.get_topic_info()

    #Build result - skip topic -1 (outliers)
    result = []
    for _, row in topic_info.iterrows():
        topic_id = row['Topic']
        if topic_id == -1:
            continue

        # Get top keywords for this topic
        keywords = [word for word, _ in topic_model.get_topic(topic_id)]

        # Get sentences belonging to this topic
        topic_docs = [docs[i] for i, t in enumerate(topics) if t == topic_id]

        result.append({
            'topic_id': topic_id,
            'keywords': keywords,
            'sentences': topic_docs[:5]  # keep top 5 sentences per topic
        })

    return result, None

def generate_labels(topics):
    """
    Takes BERTopic clusters and uses OpenAI to generate
    human-readable labels, summaries and relationships.
    """

    # Connect to OpenAI using API key
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    labeled_topics = []

    # Loop through each topic cluster from BERTopic
    for topic in topics:
        # Join keywords and sentences into strings for the prompt
        keywords = ', '.join(topic['keywords'])
        sentences = ' '.join(topic['sentences'])

        # Build prompt asking OpenAI to generate label and summary
        prompt = f"""
        Given these keywords: {keywords}
        And these example sentences: {sentences}

        Generate:
        1. A short human-readable topic label (max 7 words)
        2. A one sentence summary of the topic

        Respond in this exact format:
        Label: <label>
        Summary: <summary>
        """

        # Send prompt to OpenAI & get response
        response = client.responses.create(
            model="gpt-5.1-codex-mini",
            input=prompt  # ← was messages=[{"role": "user", "content": prompt}]
        )

        # Extract text content from response
        content = response.output_text.strip()

        # Split response into lines to extract label and summary separately
        lines = content.split('\n')

        label = lines[0].replace('Label:', '').strip()
        summary = lines[1].replace('Summary:', '').strip()

        # Add the label and summary to the topic and append to results
        labeled_topics.append({
            **topic,                    # keep existing topic data
            'label': label,
            'summary': summary
        })

    return labeled_topics

def generate_relationships(labeled_topics):
    """
    Uses OpenAI to determine relationships between topics.
    """

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Extract just the labels from each topic
    labels = [t['label'] for t in labeled_topics]

    # format labels in numbered list
    labels_str = '\n'.join([f"{i+1}. {l}" for i, l in enumerate(labels)])

    # prompting OpenAI to find relationships between topics
    prompt = f"""
    Given these topics from a document:
    {labels_str}

    Identify relationships between them.
    Respond as a list in this exact format:
    <topic1> -> <topic2>: <relationship label>
    """

    # send prompt, get response
    response = client.responses.create(
        model="gpt-5.1-codex-mini",
        input=prompt  # ← was messages=[{"role": "user", "content": prompt}]
    )

    content = response.output_text.strip()

    # Parse each line of response to extract source, target, and label
    relationships = []
    for line in content.split('\n'):
    if '->' in line and ':' in line:
        arrow_parts = line.split('->')
        source = arrow_parts[0].strip()
        rest = arrow_parts[1]  # "Topic B: causes"
        colon_idx = rest.index(':')
        target = rest[:colon_idx].strip()
        rel_label = rest[colon_idx + 1:].strip()
        relationships.append({
            'source': source,
            'target': target,
            'label': rel_label
        })

    return relationships