My test task on NordClan


To run project, enter "docker-compose up"


dev - docker-compose -f docker-compose.dev.yml up --build

prod - docker-compose -f docker-compose.prod.yml up --build

line-p - uvicorn src.main:app --reload --port 8000 --env-file .env.dev

score-m - uvicorn src.main:app --reload --port 8001 --env-file .env.dev