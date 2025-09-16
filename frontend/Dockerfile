FROM node:22.11

WORKDIR /app

# Install deps first for better caching
COPY package*.json ./
# Use install for dev images when lockfile may be missing/out-of-sync.
# Switch back to `npm ci` once package-lock.json is committed and in sync.
RUN npm install --no-audit --no-fund


# Copy the rest of the app
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]