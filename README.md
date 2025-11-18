## 02_ClerkAuth

### Setup

1. **Install Python Dependencies:**

   ```bash
   poetry install
   ```

2. **Set up Clerk Account:**

   - Create account at https://clerk.com
   - Create a new application
   - Get your Clerk API keys from the dashboard

3. **Start the Server:**

   ```bash
   sh start_server.sh
   ```

   Or manually: `poetry run uvicorn src.server:app --reload --host 0.0.0.0 --port 8000`

### Summary

- Basic setup and configuration of logged-in user routes to access the public and protected pages.
  Follow these docs: https://clerk.com/docs/nextjs/getting-started/quickstart
- Payload Structure
  Follow these docs: https://clerk.com/docs/guides/development/webhooks/overview#payload-structure
- **API Endpoint**
  - `/api/user/create`
