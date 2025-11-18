## 03_ProjectsPage

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

- Install the `clerk-backend-api` dependency
- `clerkAuth.py` - `get_user_clerk_id` function validates the user
- Refer to these docs for Clerk:
  - Visually simple explanation ~ https://clerk.com/changelog/2024-10-08-python-backend-sdk-beta
  - GitHub official docs ~ https://github.com/clerk/clerk-sdk-python?tab=readme-ov-file#request-authentication
- API endpoints:
  - GET `/api/projects/` ~ List all projects
  - POST `/api/projects/` ~ Create a new project
  - DELETE `/api/projects/{project_id}` ~ Delete a specific project
