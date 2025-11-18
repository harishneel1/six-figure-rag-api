## 06_AWS-S3

### Setup

1. **Install Python Dependencies:**

   ```bash
   poetry install
   ```

2. **Create a `.env` file:**

   ```bash
   cp .env.sample .env
   ```

   Then update the values in `.env` file with your configuration.

   > 💡 **Tip:** Get your Supabase credentials by running `npx supabase status` after starting Supabase locally.
   >
   > ⚠️ **Note:** Supabase has updated their naming. The old variable `service_role key` is now simply called `Secret Key`.  
   >  📸 [Reference screenshot](https://ik.imagekit.io/5wegcvcxp/HarishNeel/supabase-credentials.png)

3. **Start the Server:**

   ```bash
   sh start_server.sh
   ```

### Summary

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
