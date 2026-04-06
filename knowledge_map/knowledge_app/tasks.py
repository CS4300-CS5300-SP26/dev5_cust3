"""
Celery will run the BERTopic and OpenAI processing in the background
"""

from celery import shared_task
from .models import KnowledgeMap, TopicNode, SubtopicNode, NodeRelationship
from .processing import extract_topics, generate_labels, generate_relationships


@shared_task
def generate_knowledge_map(knowledge_map_id):
    """
    Background task that runs the full pipeline:
    1. Extract topics from PDF text using BERTopic
    2. Generate human-readable labels using OpenAI
    3. Generate relationships between topics using OpenAI
    4. Save everything to the database
    """
    try:
        # Get the knowledge map from the database
        knowledge_map = KnowledgeMap.objects.get(id=knowledge_map_id)

        # Update status to processing
        knowledge_map.status = 'processing'
        knowledge_map.save()

        # Get the extracted text from the uploaded PDF
        text = knowledge_map.uploaded_file.extracted_text

        # Step 1: Extract topics using BERTopic
        topics, error = extract_topics(text)
        if error:
            knowledge_map.status = 'failed'
            knowledge_map.save()
            return error

        # Step 2: Generate labels and summaries using OpenAI
        labeled_topics = generate_labels(topics)

        # Step 3: Generate relationships between topics using OpenAI
        relationships = generate_relationships(labeled_topics)

        # Step 4: Save topics to the database as TopicNodes
        topic_nodes = {}
        for topic in labeled_topics:
            node = TopicNode.objects.create(
                knowledge_map=knowledge_map,
                label=topic['label'],
                summary=topic['summary']
            )
            # Map label to node for relationship lookup
            topic_nodes[topic['label']] = node

        # Step 5: Save relationships to the database
        for rel in relationships:
            source_node = topic_nodes.get(rel['source'])
            target_node = topic_nodes.get(rel['target'])

            # Only save if both nodes exist
            if source_node and target_node:
                NodeRelationship.objects.create(
                    knowledge_map=knowledge_map,
                    source_topic=source_node,
                    target_topic=target_node,
                    relationship_label=rel['label']
                )

        # Update status to complete
        knowledge_map.status = 'complete'
        knowledge_map.save()

        return f"Knowledge map {knowledge_map_id} generated successfully"

    except Exception as e:
        # If anything fails, mark the map as failed
        knowledge_map.status = 'failed'
        knowledge_map.save()
        return str(e)