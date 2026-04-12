"""
Celery will run the OpenAI processing in the background
"""

from celery import shared_task
from .models import KnowledgeMap, TopicNode, SubtopicNode, NodeRelationship
from .processing import generate_knowledge_map_data


@shared_task
def generate_knowledge_map(knowledge_map_id):
    knowledge_map = None  # ← initialize before try block
    try:
        knowledge_map = KnowledgeMap.objects.get(id=knowledge_map_id)
        knowledge_map.status = 'processing'
        knowledge_map.save()

        text = knowledge_map.uploaded_file.extracted_text
        topics, relationships = generate_knowledge_map_data(text)

        topic_nodes = {}
        for topic in topics:
            node = TopicNode.objects.create(
                knowledge_map=knowledge_map,
                label=topic['label'],
                summary=topic['summary']
            )
            topic_nodes[topic['label']] = node

        for rel in relationships:
            source_node = topic_nodes.get(rel['source'])
            target_node = topic_nodes.get(rel['target'])
            if source_node and target_node:
                NodeRelationship.objects.create(
                    knowledge_map=knowledge_map,
                    source_topic=source_node,
                    target_topic=target_node,
                    relationship_label=rel['label']
                )

        knowledge_map.status = 'complete'
        knowledge_map.save()

        return f"Knowledge map {knowledge_map_id} generated successfully"

    except Exception as e:
        if knowledge_map is not None:  # ← guard against None
            knowledge_map.status = 'failed'
            knowledge_map.save()
        return str(e)