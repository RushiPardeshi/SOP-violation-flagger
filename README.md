# SOP-violation-flagger

## Notion polling

Polls Notion every 1 day and reads all documents the integration has access to.

```bash
pip install -r requirements.txt
# Set NOTION_API_KEY in .env
python main.py
```

**Setup:** Create an integration at [notion.so/my-integrations](https://www.notion.so/my-integrations), enable "Read content", and share your pages with the integration.

## Library usage

```python
from notion_connector import list_all_pages, read_page

# List all accessible pages
pages = list_all_pages()

# Read a specific page
content = read_page("page-id-or-url")
```