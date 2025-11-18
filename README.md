## 09_Retrieval

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

- Complete the Basic Retrieval Pipeline; every step is already well documented inside the code.
- Update the initial_schema by inserting changes before `(embedding vector_ip_ops);` and after `(embedding vector_cosine_ops);`
- Create a new migration file for the Postgres functions `vector_search_document_chunks` and `keyword_search_document_chunks`.
- Complete the Advanced Retrieval Pipeline.
