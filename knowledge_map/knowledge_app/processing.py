from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

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