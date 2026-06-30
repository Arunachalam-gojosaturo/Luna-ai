# LUNA OS X - Memory Engine Report

## PostgreSQL & PGVector Migration
SQLite has been deprecated in favor of a robust async PostgreSQL pipeline using SQLAlchemy.

### Features
* **Semantic Search**: Every conversation turn is embedded and stored.
* **Async Engine**: Uses `asyncpg` for non-blocking database queries.
* **Data Models**: 
  - `Conversation`: Persistent logs of all user/assistant interactions.
  - `SystemGoal`: Dynamic tracking of background tasks and long-term objectives.

*(Note: Requires PostgreSQL instance running locally with pgvector extension).*
