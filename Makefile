.PHONY: up down ps logs test lint

up:
	docker-compose up -d

down:
	docker-compose down

ps:
	docker-compose ps

logs:
	docker-compose logs -f

test:
	npm run test

lint:
	npm run lint
