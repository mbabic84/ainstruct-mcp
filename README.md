# AI Document Memory MCP Server

Remote MCP server for storing and searching markdown documents with semantic embeddings. Each API key has isolated data via separate Qdrant collections.

## Quick Start

1. Copy environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
- `OPENROUTER_API_KEY` - Get from https://openrouter.ai
- `API_KEYS` - Comma-separated list of API keys for authentication
- `QDRANT_URL` - Point to your existing Qdrant instance (or use local via docker-compose)

3. Start the server:
```bash
docker-compose up -d
```

4. The MCP server is available at `http://localhost:8000/mcp`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_API_KEY` | - | Qdrant API key (if required) |
| `OPENROUTER_API_KEY` | - | **Required** - OpenRouter API key |
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-8B` | Embedding model |
| `EMBEDDING_DIMENSIONS` | `4096` | Embedding vector dimensions (4096 for Qwen3-Embedding-8B) |
| `API_KEYS` | - | Comma-separated API keys (each key gets isolated Qdrant collection) |
| `DB_PATH` | `./data/documents.db` | SQLite database path |
| `CHUNK_MAX_TOKENS` | `400` | Max tokens per chunk |
| `CHUNK_OVERLAP_TOKENS` | `50` | Token overlap between chunks |
| `SEARCH_MAX_RESULTS` | `5` | Default max search results |
| `SEARCH_MAX_TOKENS` | `2000` | Default token budget for responses |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

## MCP Tools

### store_document_tool
Store a markdown document with automatic chunking and embedding generation.

**Parameters:**
- `title` (string) - Document title
- `content` (string) - Markdown content
- `document_type` (string) - Type: markdown, pdf, docx, html, text, json
- `metadata` (object) - Optional custom metadata

**Returns:** `document_id`, `chunk_count`, `token_count`

---

### search_documents_tool
Semantic search across all documents using embeddings.

**Parameters:**
- `query` (string) - Search query
- `max_results` (int) - Max results (default: 5)
- `max_tokens` (int) - Token budget (default: 2000)

**Returns:** List of relevant chunks with source info, formatted as markdown

---

### get_document_tool
Retrieve full document by ID.

**Parameters:**
- `document_id` (string) - Document UUID

**Returns:** Full document content with metadata

---

### list_documents_tool
List all documents with pagination.

**Parameters:**
- `limit` (int) - Number of documents (default: 50)
- `offset` (int) - Pagination offset (default: 0)

**Returns:** List of documents

---

### delete_document_tool
Delete a document and all its chunks.

**Parameters:**
- `document_id` (string) - Document UUID

**Returns:** Success confirmation

## Authentication

API keys are passed via the `Authorization` header:
```
Authorization: Bearer <your_api_key>
```

**Two ways to configure API keys:**
1. **Environment variable** - Add to `API_KEYS` comma-separated list
2. **Database** - Store in `api_keys` table (each key gets unique Qdrant collection)

**Each API key gets complete data isolation:**
- Unique Qdrant collection (derived from key hash)
- Isolated document storage in SQLite (filtered by `api_key_id`)

## MCP Configuration for AI Agents

### Claude Desktop

Add to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`, Linux: `~/.config/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ainstruct-mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "--port", "8000"],
      "env": {
        "AINSTRUCT_URL": "http://localhost:8000/mcp",
        "AINSTRUCT_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Cursor

Add to Cursor settings (`.cursor/mcp.json` in project or global settings):

```json
{
  "mcpServers": {
    "ainstruct-mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "--port", "8000"],
      "env": {
        "AINSTRUCT_URL": "http://localhost:8000/mcp",
        "AINSTRUCT_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Other MCP Clients

For other MCP-compatible clients, use the HTTP server URL:

```
http://localhost:8000/mcp
```

Pass the API key via the `Authorization` header:
```
Authorization: Bearer your_api_key_here
```

## Docker Deployment

```yaml
services:
  mcp_server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=${QDRANT_URL}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - API_KEYS=${API_KEYS}
    volumes:
      - ./data:/app/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
```
