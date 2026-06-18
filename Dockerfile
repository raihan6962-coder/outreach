# Root Dockerfile for Railway monorepo deployment
# Railway will detect services from docker-compose.yml
FROM alpine:latest
CMD ["echo", "Use docker-compose.yml for deployment"]
