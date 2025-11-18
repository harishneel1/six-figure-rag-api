## 07_RAG-Ingestion

### Setup

1. **Install System Dependencies:**

   These are required for document processing (PDFs, images, etc.)

   **macOS:**

   ```bash
   brew install poppler tesseract libmagic
   ```

   **Linux (Ubuntu/Debian):**

   ```bash
   sudo apt-get update
   sudo apt-get install poppler-utils tesseract-ocr libmagic1
   ```

2. **Install Python Dependencies:**

   ```bash
   poetry install
   ```

3. **Create a `.env` file:**

   ```bash
   cp .env.sample .env
   ```

   Then update the values in `.env` file with your configuration.

   > 💡 **Tip:** Get your Supabase credentials by running `npx supabase status` after starting Supabase locally.
   >
   > ⚠️ **Note:** Supabase has updated their naming. The old variable `service_role key` is now simply called `Secret Key`.  
   > 📸 [Reference screenshot](https://ik.imagekit.io/5wegcvcxp/HarishNeel/supabase-credentials.png)

4. **Start All Services:**

   You need to run **3 services** in separate terminal windows:

   **Terminal 1: Start Redis 🟥**

   ```bash
   sh start_redis.sh
   ```

   **Terminal 2: Start API Server 🟦**

   ```bash
   sh start_server.sh
   ```

   The server will run on `http://localhost:8000`

   **Terminal 3: Start Celery Worker 🟩**

   ```bash
   sh start_worker.sh
   ```

   This processes background tasks (document ingestion, embeddings, etc.)

5. **Stop All Services:**

   To stop everything at once:

   ```bash
   sh stopAll.sh
   ```

   This stops: Celery Worker, Redis Server, and API Server

### Summary

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
