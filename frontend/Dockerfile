# Imagen del dashboard: se compila con Node y se sirve con Nginx
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG BUILD_VERSION=docker
ENV BUILD_VERSION=${BUILD_VERSION}
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
