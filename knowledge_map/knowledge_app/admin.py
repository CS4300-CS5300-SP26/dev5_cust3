from django.contrib import admin

from .models import (KnowledgeMap, NodeRelationship, SubtopicNode, TopicNode,
                     UploadedFile)

# Register your models here.


admin.site.register(UploadedFile)
admin.site.register(KnowledgeMap)
admin.site.register(TopicNode)
admin.site.register(SubtopicNode)
admin.site.register(NodeRelationship)
