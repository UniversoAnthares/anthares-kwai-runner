FROM mcr.microsoft.com/playwright:v1.58.2-noble
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY server.mjs ./
ENV PORT=8080
EXPOSE 8080
CMD ["node", "server.mjs"]
