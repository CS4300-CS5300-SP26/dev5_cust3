# Knowledge Map
## Description
### CS4300 Group project repo — dev5 → cust3

## [yourknowledgemap.me](https://yourknowledgemap.me)
Knowledge Map is a learning website powered by AI to find connections between ideas you never though possible. Users can upload or enter data which will be analyzed and turned into interactive maps. These maps will be composed of nodes (individual ideas) that are connected by actual relationships between information. Users will also be able to generate their own quizess based off of maps to test their understanding of concepts.

## Main Features
- User authentication
- Upload and store content
- Create map
- Generate quiz

## How to start redis and celery manually in local host
- In terminal start local host
- In a new terminal run:
cd dev5_cust3/knowledge_map,
sudo service redis-server start,
DJANGO_SETTINGS_MODULE=knowledge_map.settings.dev celery -A knowledge_map worker --loglevel=info

## Known issues and bugs
- Redis and celery need a manual start (will be implemented in future sprint)
- Testing
- Generate quiz not working in production

## AI Usage
### Sprint 1
We used AI to help troubleshoot some errors with the development server: https://claude.ai/share/a9005f00-2f88-4d50-954f-7479b75384b3

AI was also used to help debug the homepage and update the upload html https://chatgpt.com/c/69af37c5-c110-8328-b930-90787bdb6faa https://teams.microsoft.com/l/message/19:5d12d6ba-6adb-4421-a4e2-881e1efec1af_62343346-7f5d-4d44-a56a-6258299f8710@unq.gbl.spaces/1773712791692?context=%7B%22contextType%22%3A%22chat%22%7D

AI was also used to help debug some of the BDD testing: https://claude.ai/share/d964bd4d-4ed4-4af0-b6b3-4bc47ffda35b


### Sprint 2
For quiz generation:
AI was used for planning the architecture: https://claude.ai/chat/3568f0a1-296b-4ef9-a660-35450f651b48
AI was used for generating open api calls and quiz storage: https://claude.ai/chat/aa57fb28-2e9f-4e58-b2d1-0b3a84abed37
AI was used for debugging quiz selection switching: https://claude.ai/chat/fd1085a4-49ec-4298-84df-60b93059b570
and
For create map:
AI was used for writing and debugging tests: https://claude.ai/share/95dda967-781a-4ad1-9bee-275c14094519
AI was used for figuring out what to use for background processing: https://claude.ai/share/3f5f6f96-aca9-4cbf-bf52-4d3d34e43b2a
AI was used for debugging: https://claude.ai/share/9ee0d062-86c5-457c-90a0-0bc31cd81a12
AI was used for workflow: https://chatgpt.com/share/69d5db3c-9d78-83e8-8b66-2515d8487800

