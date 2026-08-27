FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npx vite build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000

# Custom nginx conf for SPA routing & port 3000
RUN echo 'server { listen 3000; location / { root /usr/share/nginx/html; index index.html index.htm; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
