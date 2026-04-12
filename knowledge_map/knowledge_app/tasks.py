"""
Celery will run the OpenAI processing in the background
"""

from celery import shared_task
from .models import KnowledgeMap, TopicNode, SubtopicNode, NodeRelationship
from .processing import generate_knowledge_map_data


@shared_task
def generate_knowledge_map(knowledge_map_id):
    knowledge_map = None
    try:
        knowledge_map = KnowledgeMap.objects.get(id=knowledge_map_id)
        knowledge_map.status = 'processing'
        knowledge_map.save()

        text = knowledge_map.uploaded_file.extracted_text
        topics, relationships = generate_knowledge_map_data(text)

        topic_nodes = {}
        for topic in topics:

            label = topic.get('label', '').strip()
            summary = topic.get('summary', '').strip()

            # Skip if label is empty
            if not label:
                print(f"Skipping topic with empty label: {topic}")
                continue

            node = TopicNode.objects.create(
                knowledge_map=knowledge_map,
                label=label,
                summary=summary
            )
            topic_nodes[label] = node

        # Save relationships to database
        for rel in relationships:
            source = rel.get('source', '').strip()
            target = rel.get('target', '').strip()
            label = rel.get('label', '').strip()

            source_node = topic_nodes.get(source)
            target_node = topic_nodes.get(target)

            # Skip if node doesn't exist or label is empty
            if not source_node or not target_node or not label:
                print(f"Skipping relationship with missing data: {rel}")
                continue

            NodeRelationship.objects.create(
                knowledge_map=knowledge_map,
                source_topic=source_node,
                target_topic=target_node,
                relationship_label=label
            )

        knowledge_map.status = 'complete'
        knowledge_map.save()

        return f"Knowledge map {knowledge_map_id} generated successfully"

    except Exception as e:
        if knowledge_map is not None: 
            knowledge_map.status = 'failed'
            knowledge_map.save()
        return str(e)