# Six Figure RAG API

Hi 👋 I'm Harish Neel!

This project is well explained in my course. Check it out here:

👉 [Six Figure RAG Course](https://harishneel.com/six-figure-rag)

## 00_Setup

- Poetry initialization with FastAPI and Uvicorn
- Boilerplate code for FastAPI server
- Shell script to easily start the development server
- `.gitignore` file to exclude `__pycache__`, `poetry.lock`, and other unnecessary files

## 01_Supabase

- Ensure you have Docker and Node.js installed
- Run `npx supabase init` → This creates the **Supabase** folder
- Run `npx supabase start` → This spins up Docker containers with **Postgres**, **Auth**, **APIs**, etc. Everything needed to set up Supabase locally
- Create a `.env` file with the following required variables:

  - `API_URL=` - Your Supabase API URL
  - `SECRET_KEY=` - Your Supabase secret key

  > ⚠️ **Note**: Supabase has updated their naming. The old variable `service_role key` from the video is now simply called `Secret Key`.

  > 📸 [Reference screenshot](https://ik.imagekit.io/5wegcvcxp/HarishNeel/supabase-credentials.png)

- Run `npx supabase migration new [migration_name]` → This will generate a new migration file where you can define the database schema based on your Entity Relationship Diagram.
- Run `npx supabase db reset` → This command stops your local database, destroys the current one, creates a fresh database, and then runs **all migration files in order** from the beginning
- Install dependencies `python-dotenv` and `supabase` - These provide Supabase functions like `create_client()`, `.table()`, and `.insert()`

## 02_ClerkAuth

- Basic setup and configuration of logged-in user routes to access the public and protected pages.
  Follow these docs: https://clerk.com/docs/nextjs/getting-started/quickstart
- Payload Structure
  Follow these docs: https://clerk.com/docs/guides/development/webhooks/overview#payload-structure
- `/api/user/create`

## 03_ProjectsPage

- Install the `clerk-backend-api` dependency
- `clerkAuth.py` - `get_user_clerk_id` function validates the user
- Refer to these docs for Clerk:
  - Visually simple explanation ~ https://clerk.com/changelog/2024-10-08-python-backend-sdk-beta
  - GitHub official docs ~ https://github.com/clerk/clerk-sdk-python?tab=readme-ov-file#request-authentication
- API endpoints:
  - GET `/api/projects/` ~ List all projects
  - POST `/api/projects/` ~ Create a new project
  - DELETE `/api/projects/{project_id}` ~ Delete a specific project

## 04_SpecificProjectPage

**API endpoints:**

Project Routes

- GET `/api/projects/{projectId}` ~ Get specific project data
- GET `/api/projects/{projectId}/chats` ~ Get specific project chats
- GET `/api/projects/{projectId}/settings` ~ Get specific project settings

Project Files Routes

- GET `/api/projects/{projectId}/files`

Chat Routes

- POST `/api/chats/` ~ Create a new chat
- DELETE `/api/chats/{chat_id}` ~ Delete a specific chat

## 05_SpecificProjectSettings

- PUT `/api/projects/{projectId}/settings` ~ Update specific project settings

## 06_AWS-S3

- AWS S3 is hard to set up for beginners as it requires a credit card, can accidentally rack up charges, and has complex billing
- S3-compatible providers: Everything works exactly the same - **Tigris Data** - Free, no credit card required, works the same as S3
- To communicate with S3 in Python, use the `boto3` package
- Documentation for presigned URLs:
  - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
- Designed an architectural best practice to upload documents via presigned URLs
- Initialized AWS S3 service and API endpoints:
  - POST `/api/projects/{project_id}/files/upload-url` ~ Generate presigned URL for frontend file upload
  - POST `/api/projects/{project_id}/files/confirm` ~ Confirm file upload to S3
- Add Website URL
  - POST `/api/projects/{project_id}/urls`
- Delete Document API
  - DELETE `/api/projects/{project_id}/files/{file_id}` ~ To delete the document

## 07_RAG-Ingestion

- Complete Ingestion Pipeline Diagram: [https://ik.imagekit.io/5wegcvcxp/HarishNeel/image.png]
- Please make sure that you have watched the Multi-modal Pipelines video in the RAG foundation course:
  - Harish Neel LMS: https://academy.harishneel.com/web/lite/view/chapter/68f21ae4d0f42ae662da513b?course=68f218b8e28ae5601ab8cc84
  - GitHub: https://github.com/harishneel1/multi-modal-rag-pipeline/tree/main
- Ensure you install system dependencies as mentioned in the Jupyter notebook above: `Poppler`, `Tesseract`, and `libmagic`
- Will use Redis via Docker container with port mapping and easily start with `sh start_redis.sh`
- Install the `celery` `redis` `unstructured[all-docs]` dependencies.
- Initialize Celery Worker after file upload confirmation or website url to Start the background processing in `/api/projects/{project_id}/files/confirm` and `/api/projects/{project_id}/urls`
- For URLs, we are going to use a web scraper - the `scrapingbee` dependency. Ensure you initiate it.
- All updates will be shown on the frontend using short polling by making requests to `/api/projects/{project_id}/files`
- Initialize the LLM (OpenAI) for embeddings and chat functionality. Install: `langchain-openai`, `langchain`, `langchain-community`
- Whenever we make changes inside a task, we must **restart the Celery server**. Otherwise, the changes will **not be reflected**. Run shell script `sh start_worker.sh` Or in case want to stop all the services `sh stopAll.sh`.
- Display Specific Project File Chunks
  - GET `/api/projects/{project_id}/files/{file_id}/chunks` ~ Get project document chunks

## 08_Chat

- GET `/api/chats/{chat_id}` ~ Get a specific chat
- POST `/api/projects/{project_id}/chats/{chat_id}/messages` ~ Send a message to a chat

## 09_Retrieval

- Complete the Basic Retrieval Pipeline; every step is already well documented inside the code.
- Update the initial_schema by inserting changes before `(embedding vector_ip_ops);` and after `(embedding vector_cosine_ops);`
- Create a new migration file for the Postgres functions `vector_search_document_chunks` and `keyword_search_document_chunks`.
- Complete the Advanced Retrieval Pipeline.
