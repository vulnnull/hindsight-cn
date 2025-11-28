# Dockerfile for Hindsight Control Plane (standalone)
FROM node:20-alpine AS sdk-builder

WORKDIR /app/sdk

# Build TypeScript SDK
COPY hindsight-clients/typescript/package*.json ./
RUN npm ci

COPY hindsight-clients/typescript/ ./
RUN npm run build

# Build Control Plane
FROM node:20-alpine AS builder

WORKDIR /app

# Copy built SDK
COPY --from=sdk-builder /app/sdk /app/sdk

# Install Control Plane dependencies
COPY hindsight-control-plane/package*.json ./
RUN npm ci

# Copy Control Plane source
COPY hindsight-control-plane/ ./

# Link SDK for build
RUN cd /app/sdk && npm link && cd /app && npm link @hindsight/client

# Build the Next.js app
RUN npm run build

# Create public directory if it doesn't exist
RUN mkdir -p public

# Production image
FROM node:20-alpine

WORKDIR /app

# Copy built SDK
COPY --from=sdk-builder /app/sdk /app/sdk

# Copy package files and install production dependencies only
COPY hindsight-control-plane/package*.json ./
RUN npm ci --omit=dev

# Link SDK for runtime
RUN cd /app/sdk && npm link && cd /app && npm link @hindsight/client

# Copy built app from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

# Expose control plane port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV HINDSIGHT_CP_DATAPLANE_API_URL=http://localhost:8888

# Run the Next.js server
CMD ["npm", "start"]
