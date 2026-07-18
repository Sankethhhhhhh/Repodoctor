# 🩺 RepoDoctor

> Analyze, score, and improve GitHub repositories using automated quality metrics.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## Overview

RepoDoctor is a full-stack repository quality analysis platform that evaluates GitHub repositories using a comprehensive set of software engineering metrics.

It automates repository assessment by analyzing project structure, documentation, maintainability, code quality indicators, licensing, testing, dependency health, and other engineering best practices.

The goal is to help developers quickly identify weaknesses and improve the overall quality of their repositories.

---

## Features

### Repository Analysis

- Analyze any public GitHub repository
- Automated repository scoring
- Health status evaluation
- Repository metadata extraction
- Branch and commit statistics

### Quality Assessment

- Documentation analysis
- README quality checks
- License detection
- Dependency inspection
- Testing detection
- CI/CD workflow detection
- Project structure validation
- Code organization analysis

### Dashboard

- Repository health overview
- Quality score visualization
- Rule-by-rule breakdown
- Historical analysis
- Interactive charts

### Reports

- Save analysis reports
- Compare multiple reports
- View repository history
- Export reports
- Trend analysis

### User Experience

- Modern responsive UI
- Authentication
- Scheduler support
- Dark theme
- Interactive visualizations

---

# Tech Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Recharts
- React Router

## Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Alembic

## DevOps

- Docker
- Docker Compose
- Nginx

---

# Project Structure

```
RepoDoctor
│
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── scheduler/
│   ├── database/
│   └── migrations/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── services/
│
├── docker/
├── nginx/
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/Sankethhhhhhh/Repodoctor.git

cd RepoDoctor
```

---

## Backend

```bash
cd backend

python -m venv .venv

source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Frontend

```bash
cd frontend

npm install
```

or

```bash
pnpm install
```

---

## Environment Variables

Create a `.env` file inside the backend directory.

Example:

```env
DATABASE_URL=
REDIS_URL=
GITHUB_TOKEN=

SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

# Running Locally

Backend

```bash
uvicorn app.main:app --reload
```

Frontend

```bash
npm run dev
```

or

```bash
pnpm dev
```

Docker

```bash
docker compose up --build
```

---

---

# Roadmap

- AI-powered repository recommendations
- Multi-repository benchmarking
- GitHub App integration
- PDF report generation
- Team analytics
- Repository monitoring
- Custom scoring rules

---

# Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```
git checkout -b feature/my-feature
```

3. Commit your changes

```
git commit -m "feat: add new feature"
```

4. Push

```
git push origin feature/my-feature
```

5. Open a Pull Request

---

# License

This project is licensed under the MIT License.

---

# Author

**Sanketh**

Artificial Intelligence & Machine Learning Student

GitHub:
https://github.com/Sankethhhhhhh

---

## Support

If you found this project useful, consider giving it a ⭐ on GitHub.
