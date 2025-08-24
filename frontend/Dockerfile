FROM node:22.11

WORKDIR /app

# Install deps first for better caching
COPY package*.json ./
RUN npm install --no-audit --no-fund

# Copy the rest of the app
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]