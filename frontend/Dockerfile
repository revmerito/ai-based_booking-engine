# Frontend Dockerfile - React + Vite Production Build
FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Build production bundle
# VITE_API_URL must be set as Railway environment variable
RUN npm run build

# Serve the static build with a lightweight server
RUN npm install -g serve

EXPOSE 8080

CMD ["serve", "-s", "dist", "-l", "8080"]
