## 05_SpecificProjectSettings

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

- PUT `/api/projects/{projectId}/settings` ~ Update specific project settings
