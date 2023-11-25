CONTAINER_NAME=iracing-result-fetcher

.PHONY: build start stop clean

build:
	docker build -t $(CONTAINER_NAME) -f build/Dockerfile .

start:
	docker compose -f deployment/compose.yml up -d

stop:
	docker compose -f deployment/compose.yml down

clean:
	docker image rm $(CONTAINER_NAME)
