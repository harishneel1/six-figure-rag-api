## 💻 Local-Setup Architecture

> 📊 Architecture diagrams in this guide contributed by [@rajatevencodes](https://github.com/rajatevencodes)

<p align="center">
  <img src="https://ik.imagekit.io/5wegcvcxp/Resume-Multi-modal-rag/Local-Architecture.png" alt="Local Setup Architecture" width="100%" height="100%">
</p>

### RAG Pipelines

_Ingestion | Retrieval | Generation_

<p align="center">
  <img src="https://ik.imagekit.io/5wegcvcxp/Resume-Multi-modal-rag/Indexing.png" alt="Ingestion Pipeline" width="100%">
</p>
<p align="center">
  <img src="https://ik.imagekit.io/5wegcvcxp/Resume-Multi-modal-rag/Retrieval.png" alt="Retrieval Pipeline" width="100%">
</p>
<p align="center">
  <img src="https://ik.imagekit.io/5wegcvcxp/Resume-Multi-modal-rag/Generation.png" alt="Generation Pipeline" width="100%">
</p>

<br>

# 🐳 **Local Docker Setup Guide**

<br>

Complete guide to set up and run the MultiModal RAG application locally using Docker.

<details>
<summary>📋 <strong>Prerequisites</strong></summary>

<br>

Before starting, ensure you have:

- **Docker** and **Docker Compose** installed
- **Node.js** and **npm** installed (for Supabase CLI)
- **Supabase CLI** installed globally:

```bash
npm install -g supabase
```

</details>

<hr>
<br>

🚀 **Setup Steps**
<br>

<details>
<summary><strong>Step 1: Initialize Supabase</strong></summary>
<br>

> ⚠️ **IMPORTANT**: Supabase must be initialized before starting Docker containers.

**1.1 Start Supabase**

Start the local Supabase instance: This spins up Docker containers with **Postgres**, **Auth**, **APIs**, etc. Everything needed to set up Supabase locally. It also provides **URLs** and **keys** to connect to your local database, so make sure to use them in your **.env** file.

```bash
npx supabase start
```

**1.2 Reset Database (Initialize with Migrations)**

Run the migration to create a fresh database with all migration files:

```bash
npx supabase db reset
```

> **What this does**:
>
> - Stops your local database
> - Destroys the current database
> - Creates a fresh database
> - Runs **all migration files in order** from the beginning
>
> **Verify in Dashboard**:
> Visit [http://127.0.0.1:54323/project/default/editor](http://127.0.0.1:54323/project/default/editor) to check your database tables.

**1.3 Verify Supabase**

Verify Supabase is running:

```bash
npx supabase status
```

</details>

<br>

<details>
<summary><strong>Step 2: Configure Environment Variables</strong></summary>
<br>

**2.1 Create `.env` file**

Copy the sample environment file:

```bash
cp .env.sample .env
```

**2.2 Configure Required Variables**

Open `.env` and configure the following **required** variables:

**Supabase (Required)**

```bash
# Auto-configured in Docker-compose file
SUPABASE_API_URL=http://host.docker.internal:54321
SUPABASE_SECRET_KEY=your_supabase_secret_key
```

**Clerk (Required)**

```bash
CLERK_SECRET_KEY=your_clerk_secret_key
DOMAIN=http://localhost:8000
```

**AWS S3 (Required - for document uploads)**

```bash
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

**OpenAI (Required)**

```bash
OPENAI_API_KEY=your_openai_api_key
```

**Redis(Required)**

```bash
# (Auto-configured in Docker-compose file)
REDIS_URL=redis://multimodal-rag-redis:6379/0
```

**2.3 Configure Optional Variables**

**ScrapingBee (Optional - for web scraping)**

```bash
SCRAPINGBEE_API_KEY=your_scrapingbee_api_key
```

**Tavily (Optional - for web search)**

```bash
TAVILY_API_KEY=your_tavily_api_key
```

**LangSmith (Optional - for tracing)**

```bash
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=multi-modal-rag
```

<br>

> 💡 **Important: Why `host.docker.internal`?**
>
> Docker containers are **isolated** (redis,worker,api-server) from your computer. Inside Docker, `localhost` means the container itself. To access services running on your machine (like Supabase), containers use `host.docker.internal` instead of `localhost`.
>
> **Common Mistakes to Avoid:**
>
> ```bash
> # ❌ WRONG - won't work in Docker
> SUPABASE_API_URL=http://localhost:54321
> REDIS_URL=redis://localhost:6379/0
>
> # ✅ CORRECT - use proper Docker networking
> SUPABASE_API_URL=http://host.docker.internal:54321
> REDIS_URL=redis://multimodal-rag-redis:6379/0
> ```

</details>

<br>

<details>
<summary><strong>Step 3: Start Docker Containers</strong></summary>
<br>

Use the Makefile commands to manage containers:

**Start all services**

```bash
make start
```

This command will:

1. Check if Supabase is running
2. Build and start all Docker containers in detached mode

**Stop all services**

```bash
make stop
```

**Restart all services**

```bash
make restart
```

**Clean everything (containers, volumes, images)**

```bash
make clean
```

</details>

<br>

<details>
<summary><strong>Step 4: Create Test Account (Clerk)</strong></summary>
<br>

> 🔐 **IMPORTANT**: All API endpoints are secured and require a valid user ID for authentication. You must create a user account first to access any API features.

**4.1 Start the API** (skip this if containers are already running)

```bash
make start
```

**4.2 Create User Account**

1. Navigate to: [http://localhost:8000/docs](http://localhost:8000/docs)
2. Go to the **`/create`** endpoint
3. Put data manually using the payload structure from [Clerk webhook documentation](https://clerk.com/docs/guides/development/webhooks/overview#payload-structure)

This step ensures your Supabase database is properly initialized and can handle user creation. **Without this, you cannot interact with any API endpoints.**

</details>

<br>
<hr>
<br>

<details>
<summary>📊 <strong>Viewing Logs</strong></summary>
<br>

Monitor logs for specific services:

**API Server logs**

```bash
make logs-api
```

**Redis logs**

```bash
make logs-redis
```

**Worker logs**

```bash
make logs-worker
```

> Press `Ctrl+C` to exit log viewing.

</details>

<br>

<details>
<summary>📖 <strong>Quick Reference</strong></summary>
<br>

| Command                 | Description                                |
| ----------------------- | ------------------------------------------ |
| `npx supabase start`    | Start local Supabase                       |
| `npx supabase status`   | Check Supabase status                      |
| `npx supabase db reset` | Reset database to clean state              |
| `make start`            | Start all Docker containers                |
| `make stop`             | Stop all Docker containers                 |
| `make restart`          | Restart all containers                     |
| `make clean`            | Remove all containers, volumes, and images |
| `make logs-api`         | View API server logs                       |
| `make logs-redis`       | View Redis logs                            |
| `make logs-worker`      | View worker logs                           |

</details>
