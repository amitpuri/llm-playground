# Database Setup Scripts

This directory contains scripts to set up the PostgreSQL database for the MCP PostgreSQL client.

## Quick Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment (optional):**
   ```bash
   cp env_example.txt .env
   # Edit .env file to customize database connection if needed
   ```

3. **Run the setup script:**
   ```bash
   python setup_database.py
   ```

## What the Setup Creates

### Schema: `research_papers`

### Tables:
- **`ai_research_papers`** - Main table containing AI research papers
  - `id` (SERIAL PRIMARY KEY)
  - `title` (VARCHAR(500))
  - `authors` (TEXT[]) - Array of author names
  - `abstract` (TEXT)
  - `publication_date` (DATE)
  - `journal` (VARCHAR(200))
  - `doi` (VARCHAR(100))
  - `keywords` (TEXT[]) - Array of keywords
  - `citation_count` (INTEGER)
  - `created_at` (TIMESTAMP)
  - `updated_at` (TIMESTAMP)

- **`research_topics`** - Research topic categories
  - `id` (SERIAL PRIMARY KEY)
  - `name` (VARCHAR(200) UNIQUE)
  - `description` (TEXT)
  - `parent_topic_id` (INTEGER) - Self-referencing for hierarchical topics
  - `created_at` (TIMESTAMP)

- **`paper_topics`** - Junction table linking papers to topics
  - `paper_id` (INTEGER) - Foreign key to ai_research_papers
  - `topic_id` (INTEGER) - Foreign key to research_topics
  - Primary key: (paper_id, topic_id)

### Views:
- **`papers_with_topics`** - Convenient view showing papers with their associated topics

### Sample Data:
- **5 Research Topics:** Machine Learning, Natural Language Processing, Computer Vision, Deep Learning, Reinforcement Learning, AI Ethics, Large Language Models
- **5 Research Papers:** Including famous papers like "Attention Is All You Need", "BERT", "GANs", "ResNet", and "AlphaGo"

## Database Connection

The setup uses the following connection string by default:
```
postgresql://user:password@localhost:5432/dbname
```

**Note**: If your password contains special characters, URL-encode them. For example:
- `@` becomes `%40`
- `#` becomes `%23`
- `%` becomes `%25`
- `&` becomes `%26`

Example: `password@123` becomes `password%40123`

You can customize this by:
1. Creating a `.env` file with your own `DATABASE_URI`
2. Setting the `DATABASE_URI` environment variable
3. The script will fall back to the default if neither is provided

## Manual Setup (Alternative)

If you prefer to run the SQL manually:

1. Connect to your PostgreSQL database
2. Run the contents of `setup_schema.sql`

## Verification

After setup, you can verify the installation by running:

```sql
-- Check tables
SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'research_papers';

-- Check sample data
SELECT COUNT(*) FROM research_papers.ai_research_papers;
SELECT COUNT(*) FROM research_papers.research_topics;

-- View papers with topics
SELECT title, topics FROM research_papers.papers_with_topics LIMIT 3;
```

## Next Steps

After running the setup:

1. Start the PostgreSQL MCP server:
   ```bash
   # If you have a .env file, it will be loaded automatically
   # Otherwise, set the environment variable:
   export DATABASE_URI="postgresql://user:password@localhost:5432/dbname"
   postgres-mcp --access-mode=unrestricted --transport=sse
   ```

2. Run the MCP client:
   ```bash
   cd ../pg
   python main.py
   ```
