## 04_SpecificProjectPage

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

Project Routes

- GET `/api/projects/{projectId}` ~ Get specific project data
- GET `/api/projects/{projectId}/chats` ~ Get specific project chats
- GET `/api/projects/{projectId}/settings` ~ Get specific project settings

Project Files Routes

- GET `/api/projects/{projectId}/files`

Chat Routes

- POST `/api/chats/` ~ Create a new chat
- DELETE `/api/chats/{chat_id}` ~ Delete a specific chat
