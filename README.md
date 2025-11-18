## 02_ClerkAuth

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

- Basic setup and configuration of logged-in user routes to access the public and protected pages.
  Follow these docs: https://clerk.com/docs/nextjs/getting-started/quickstart
- Payload Structure
  Follow these docs: https://clerk.com/docs/guides/development/webhooks/overview#payload-structure
- **API Endpoint**
  - `/api/user/create`
