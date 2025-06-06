# Placeholder Dockerfile for React frontend
# Instructions for building the React app will be added in Step 1.2
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
