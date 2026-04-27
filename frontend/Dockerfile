# Frontend Dockerfile - React + Vite Production Build
FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Set Build Arguments for Vite (must be available during npm run build)
ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

# Build production bundle
RUN npm run build

# Serve the static build with a lightweight server
RUN npm install -g serve

EXPOSE 8080

CMD ["serve", "-s", "dist", "-l", "8080"]
