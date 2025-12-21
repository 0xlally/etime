# Frontend Dockerfile
# Use Microsoft devcontainer image to avoid Docker Hub mirror issues
FROM mcr.microsoft.com/devcontainers/javascript-node:18

WORKDIR /app

# Install deps
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

EXPOSE 3000

# Vite dev server for testing; uses API_PROXY_TARGET to proxy /api
CMD ["npm", "run", "dev", "--", "--host", "--port", "3000"]
