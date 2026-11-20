# D18 (WP14): build SPA (node) -> serve (nginx). Base vuota: il bundle chiama
# fetch("/api/...") same-origin, prefisso unico; nginx lo proxya al service api
# del compose (frontend/nginx.conf). Il ?? del client tiene "" (non null).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80