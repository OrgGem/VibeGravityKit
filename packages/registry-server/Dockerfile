FROM node:20-alpine

RUN apk add --no-cache git

WORKDIR /app
COPY package.json ./
COPY src ./src
COPY scripts ./scripts
COPY config.example.json ./config.example.json

ENV NODE_ENV=production
ENV PORT=7077
EXPOSE 7077

CMD ["node", "src/server.js"]
