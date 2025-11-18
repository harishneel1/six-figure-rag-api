## 01_Supabase

### Setup & Summary

- Ensure you have Docker and Node.js installed
- Run `npx supabase init` → This creates the **Supabase** folder
- Run `npx supabase start` → This spins up Docker containers with **Postgres**, **Auth**, **APIs**, etc. Everything needed to set up Supabase locally
- Install Python dependencies:
  ```bash
  poetry install
  ```
- Create a `.env` file with the following required variables:

  **Option 1:** Copy from example file (if available):

  ```bash
  cp .env.example .env
  ```

  Then update the values in `.env` file.

  **Option 2:** Create manually with the following variables:

  - `SUPABASE_API_URL=` - Your Supabase API URL
  - `SUPABASE_SECRET_KEY=` - Your Supabase secret key

  > ### **Note**: Supabase has updated their naming. The old variable `service_role key` from the video is now simply called `Secret Key`.
  >
  > 📸 [Reference screenshot](https://ik.imagekit.io/5wegcvcxp/HarishNeel/supabase-credentials.png)

- Run `npx supabase migration new [migration_name]` → This will generate a new migration file where you can define the database schema based on your Entity Relationship Diagram.
- Run `npx supabase db reset` → This command stops your local database, destroys the current one, creates a fresh database, and then runs **all migration files in order** from the beginning
- Install dependencies `python-dotenv` and `supabase` - These provide Supabase functions like `create_client()`, `.table()`, and `.insert()`
