from django.contrib import admin

# Register your models here.
from .models import (KnowledgeMap, NodeRelationship, SubtopicNode, TopicNode,
                     UploadedFile, CustomMap, CustomNode, CustomEdge)


admin.site.register(UploadedFile)
admin.site.register(KnowledgeMap)
admin.site.register(TopicNode)
admin.site.register(SubtopicNode)
admin.site.register(NodeRelationship)
admin.site.register(CustomMap)
admin.site.register(CustomNode)
admin.site.register(CustomEdge)
