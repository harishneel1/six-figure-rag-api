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
