# NBA MCP Server - Book Integration Guide

## Overview

This guide shows you how to add books to your NBA MCP server so Google Gemini (or any LLM) can read them and provide recommendations based on your project goals.

## 🎯 Design Decisions

### 1. Storage: **S3 with `books/` Prefix**
- Store books in your existing S3 bucket under `books/` prefix
- Organize by category: `books/technical/`, `books/business/`, `books/sports-analytics/`
- Supported formats: `.txt`, `.md`, `.pdf` (text-extracted), `.json`

### 2. Token Limit Handling: **Smart Chunking**
- Books split into manageable chunks (default: 50k characters)
- Configurable up to 200k characters for large context models like Gemini
- Sequential chunk reading with `chunk_number` parameter
- Metadata includes total chunks for navigation

### 3. Tools Provided:
- **`list_books`** - Browse available books
- **`read_book`** - Read books in chunks with metadata
- **`search_books`** - Full-text search across all books
- **`get_book_recommendations`** - AI-driven recommendations (via prompt)

### 4. Resources Provided:
- **`book://{path}`** - Direct URI access to books
- **`book://{path}/chunk/{number}`** - Access specific chunks

---

## 📦 Implementation Status

✅ **Completed**:
1. S3 Connector updated with `get_object()` and `list_objects()` methods
2. Book parameter models (`ListBooksParams`, `ReadBookParams`, `SearchBooksParams`)
3. Implementation plan documented

⏳ **Remaining** (I can implement these now if you want):
1. Book response models
2. Book tools in `fastmcp_server.py`
3. Book resource templates
4. Book recommendation prompt
5. Test script
6. Usage documentation

---

## 🚀 Quick Start (Once Implemented)

### Step 1: Upload Books to S3

```bash
# Using AWS CLI
aws s3 cp my-book.txt s3://your-bucket/books/my-book.txt
aws s3 cp technical-guide.pdf s3://your-bucket/books/technical/technical-guide.txt

# Or use boto3
import boto3
s3 = boto3.client('s3')
s3.upload_file('my-book.txt', 'your-bucket', 'books/my-book.txt')
```

### Step 2: List Available Books

```python
# In Claude Desktop (or via MCP client)
await mcp.call_tool("list_books", {
    "prefix": "books/",
    "max_keys": 100
})

# Response:
{
    "books": [
        {
            "path": "books/nba-analytics-bible.txt",
            "size": 524288,  # 512 KB
            "last_modified": "2025-10-10T12:00:00Z"
        },
        ...
    ],
    "count": 10,
    "success": true
}
```

### Step 3: Read a Book (in Chunks)

```python
# Read first chunk (50k characters by default)
await mcp.call_tool("read_book", {
    "book_path": "books/nba-analytics-bible.txt",
    "chunk_size": 50000,
    "chunk_number": 0
})

# Response:
{
    "book_path": "books/nba-analytics-bible.txt",
    "content": "Chapter 1: Introduction to NBA Analytics...",
    "chunk_number": 0,
    "chunk_size": 50000,
    "total_chunks": 11,
    "has_more": true,
    "metadata": {
        "total_size": 524288,
        "format": "txt"
    },
    "success": true
}

# Read next chunk
await mcp.call_tool("read_book", {
    "book_path": "books/nba-analytics-bible.txt",
    "chunk_number": 1
})
```

### Step 4: Search Across All Books

```python
await mcp.call_tool("search_books", {
    "query": "machine learning player prediction",
    "book_prefix": "books/",
    "max_results": 10
})

# Response:
{
    "results": [
        {
            "book_path": "books/ml-for-sports.txt",
            "excerpt": "...machine learning models for player prediction...",
            "match_score": 0.95,
            "chunk_number": 5
        },
        ...
    ],
    "count": 10,
    "query": "machine learning player prediction",
    "success": true
}
```

### Step 5: Get AI Recommendations

```python
# Use the book recommendation prompt
Use the "recommend_books_for_project" prompt with:
- project_goal: "Build NBA player performance prediction system"
- current_knowledge: "Basic SQL, Python, limited ML experience"
```

This prompt will:
1. Analyze available books
2. Match them to your project goal
3. Recommend reading order
4. Suggest specific chapters/sections
5. Estimate time investment

---

## 💡 Smart Token Management

### Problem: Books exceed token limits

A typical book is 100,000-500,000 characters. Most LLMs have context limits:
- GPT-4: 8k-128k tokens (~32k-512k characters)
- Claude: 100k-200k tokens (~400k-800k characters)
- **Gemini 1.5 Pro: 1M-2M tokens** (~4M-8M characters) ⭐

### Solution: Chunked Reading

```python
# For Gemini (large context)
chunk_size = 200000  # 200k characters per chunk

# For smaller models
chunk_size = 50000   # 50k characters per chunk

# Read sequentially
for chunk_num in range(total_chunks):
    chunk = await read_book(book_path, chunk_size, chunk_num)
    # Process chunk
    # LLM maintains context across chunks in conversation
```

### Best Practices:

1. **Start Small**: Read chapter 1 or summary first
2. **Search First**: Use `search_books` to find relevant sections
3. **Use Resources**: `book://path/chunk/5` for direct access
4. **Bookmark**: Track which chunks you've read
5. **Summarize**: Ask LLM to summarize each chunk before moving on

---

## 🎓 Example: Gemini Reading a Book

```
User: I want to build an NBA player performance prediction system.
      Can you recommend books and read them for me?

Claude (via MCP):
1. [Calls list_books] Found 15 books in library
2. [Calls recommend_books_for_project prompt]
   Recommendations:
   - "NBA Analytics Bible" (10 hours)
   - "Machine Learning for Sports" (8 hours)
   - "Python for Data Science" (6 hours)

3. [Calls read_book for "NBA Analytics Bible", chunk 0]
   Reading Chapter 1: Introduction...

   Summary: This book covers player tracking data,
   advanced metrics (PER, WS, BPM), and predictive modeling.
   Recommends starting with exploratory data analysis.

4. [Calls read_book, chunk 1]
   Reading Chapter 2: Data Collection...

5. [User asks: "How do they handle missing data?"]
   [Calls search_books with query="missing data handling"]
   Found in chunk 3, reading...
```

The LLM maintains conversation context, so it remembers:
- What it's read so far
- Your project goal
- Your questions

You can ask it to:
- Summarize chapters
- Find specific information
- Compare approaches from different books
- Generate implementation code based on book guidance

---

## 🔍 Advanced Features

### 1. Book Metadata via Resources

```python
# Get book info without reading full content
resource = await mcp.read_resource("book://books/my-book.txt")

# Returns:
{
    "path": "books/my-book.txt",
    "size": 524288,
    "format": "txt",
    "total_chunks": 11,
    "last_modified": "2025-10-10T12:00:00Z",
    "preview": "First 500 characters of the book..."
}
```

### 2. Category-Based Recommendations

```python
# List books by category
await list_books(prefix="books/sports-analytics/")
await list_books(prefix="books/machine-learning/")
await list_books(prefix="books/python/")

# Get recommendations for specific category
Use "recommend_books_for_project" with:
- category: "machine-learning"
- skill_level: "intermediate"
```

### 3. Cross-Book Analysis

```bash
# Search across all books for a concept
await search_books(query="ensemble methods", max_results=20)

# LLM can then:
# 1. Read relevant chunks from multiple books
# 2. Compare explanations
# 3. Synthesize best approach
# 4. Provide implementation guidance
```

---

## 📊 Book Formats

### Supported Formats:

1. **Plain Text (`.txt`)** - Best for reading
   - No preprocessing needed
   - Fast to load
   - Easy to search

2. **Markdown (`.md`)** - Great for technical docs
   - Preserves structure
   - Code blocks intact
   - Links work as references

3. **JSON (`.json`)** - Structured books
   - Chapter/section organization
   - Metadata embedded
   - Programmatic access

4. **PDF (`.pdf`)** - Requires text extraction
   - Use `pdfplumber` or `PyPDF2` to extract text
   - Save extracted text as `.txt` in S3
   - Preserve formatting where possible

### Conversion Example:

```python
# Convert PDF to text for MCP
import pdfplumber

with pdfplumber.open('book.pdf') as pdf:
    text = ''
    for page in pdf.pages:
        text += page.extract_text() + '\n\n'

    # Upload to S3
    s3.put_object(
        Bucket='your-bucket',
        Key='books/book.txt',
        Body=text.encode('utf-8')
    )
```

---

## 🎯 Use Cases

### Use Case 1: Learning New Technology

**Goal**: Learn TensorFlow for NBA predictions

**Steps**:
1. Upload "Deep Learning with TensorFlow" book
2. Ask: "I want to predict NBA player performance. Help me learn TensorFlow."
3. LLM reads book, suggests chapters 3, 5, 8
4. You work through examples
5. LLM answers questions by referencing book

### Use Case 2: Code Review Against Best Practices

**Goal**: Ensure your code follows best practices

**Steps**:
1. Upload "Clean Code" and "Python Best Practices" books
2. Share your code with LLM
3. LLM reads relevant chapters
4. LLM compares your code to book recommendations
5. LLM suggests improvements with citations

### Use Case 3: Research & Synthesis

**Goal**: Write a whitepaper on NBA analytics techniques

**Steps**:
1. Upload 5-10 analytics books
2. Ask: "Synthesize the main approaches to player valuation"
3. LLM searches all books for relevant content
4. LLM reads matching chapters
5. LLM creates structured summary with citations
6. You review and refine

---

## 🔐 Security & Best Practices

### Security:
- ✅ Path traversal protection (no `..` or absolute paths)
- ✅ Prefix-based access control
- ✅ Read-only access (no file modification)
- ✅ S3 permissions control who can upload books

### Best Practices:
1. **Organize Books**: Use clear folder structure
   ```
   books/
     technical/
       python-guide.txt
       sql-optimization.txt
     business/
       project-management.txt
     sports-analytics/
       nba-advanced-metrics.txt
   ```

2. **Name Files Clearly**: `nba-analytics-2024.txt` not `book1.txt`

3. **Add Metadata**: Include author, date in first few lines
   ```
   Title: NBA Analytics Bible
   Author: John Doe
   Date: 2024
   Version: 2.0

   Chapter 1: Introduction
   ...
   ```

4. **Test Chunking**: Ensure chunks break at logical points
   ```python
   # Read first chunk
   chunk0 = await read_book(path, chunk_size=50000, chunk_number=0)
   # Check if it ends mid-sentence
   # Adjust chunk_size if needed
   ```

5. **Index Books**: Keep a catalog of books with descriptions
   ```json
   {
     "books/nba-analytics.txt": {
       "title": "NBA Analytics Bible",
       "author": "John Doe",
       "topics": ["advanced metrics", "player tracking", "predictions"],
       "difficulty": "intermediate",
       "pages": 450
     }
   }
   ```

---

## 📈 Next Steps

### Option 1: I Can Implement Now
If you want, I can implement the complete book system right now:
- Book response models
- 3 book tools (list, read, search)
- 2 book resources (direct access, chunked access)
- Book recommendation prompt
- Test script
- Update documentation

**Estimated time**: 30-45 minutes

### Option 2: Try It Yourself
Use this guide to implement the features yourself. The parameters are ready, you just need to:
1. Add response models to `responses.py`
2. Add tools to `fastmcp_server.py`
3. Add resources
4. Add prompt

### Option 3: Wait and Plan More
We can discuss your specific use case more and refine the design before implementing.

---

## 🎓 FAQ

**Q: Can Google Gemini really read entire books?**
A: Yes! Gemini 1.5 Pro has a 2M token context (8M+ characters). That's about 10-15 average books in a single conversation.

**Q: How do I upload books?**
A: Use AWS CLI (`aws s3 cp`) or boto3. Or implement an upload tool in the MCP if you want.

**Q: Can I use local files instead of S3?**
A: Yes, but you'd need to modify the connector. S3 is recommended for production.

**Q: How does search work?**
A: Simple text search for now. We can add vector embeddings later for semantic search.

**Q: Can multiple users share books?**
A: Yes, all users with S3 access can read the same books.

**Q: How much does S3 storage cost?**
A: Very cheap. 1000 books (500MB each) = 500GB = ~$11.50/month in S3 Standard.

---

**Ready to implement? Just say the word!** 🚀