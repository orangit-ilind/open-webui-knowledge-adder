# Open WebUI Knowledge Uploader

A Python application that interfaces with Open WebUI's REST API to programmatically upload files and documents to knowledge collections.

## Features

- Upload files to Open WebUI knowledge collections programmatically
- Create knowledge collections automatically if they don't exist
- Recursive directory scanning (configurable)
- Both CLI tool and importable Python library
- Comprehensive error handling with detailed logging
- Progress reporting and upload summaries

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### API Key

You can provide your Open WebUI API key in two ways:

1. **Environment variable** (recommended):
   ```bash
   export OPEN_WEBUI_API_KEY=your_api_key_here
   ```

2. **Command-line argument**:
   ```bash
   --api-key your_api_key_here
   ```

To get your API key:
1. Log into your Open WebUI instance
2. Go to Settings > Account
3. Copy your API key

## Usage

### Command Line Interface

#### Basic Usage

Upload files to an existing knowledge collection:

```bash
python cli.py \
  --endpoint http://localhost:3000 \
  --api-key YOUR_API_KEY \
  --knowledge "My Documents" \
  --path ./documents
```

#### Create Knowledge Collection

Create a knowledge collection if it doesn't exist:

```bash
python cli.py \
  --endpoint http://localhost:3000 \
  --api-key YOUR_API_KEY \
  --knowledge "New Collection" \
  --path ./documents \
  --create \
  --description "Collection description"
```

#### Non-Recursive Upload

Upload files from the specified directory only (no subdirectories):

```bash
python cli.py \
  --endpoint http://localhost:3000 \
  --api-key YOUR_API_KEY \
  --knowledge "My Documents" \
  --path ./documents \
  --no-recursive
```

#### Using Environment Variable

If you've set `OPEN_WEBUI_API_KEY` environment variable:

```bash
python cli.py \
  --endpoint http://localhost:3000 \
  --knowledge "My Documents" \
  --path ./documents
```

#### Verbose Logging

Enable detailed logging for debugging:

```bash
python cli.py \
  --endpoint http://localhost:3000 \
  --api-key YOUR_API_KEY \
  --knowledge "My Documents" \
  --path ./documents \
  --verbose
```

### Command Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--endpoint` | Yes | Open WebUI API endpoint (e.g., `http://localhost:3000`) |
| `--api-key` | Yes* | API key for authentication (*or set `OPEN_WEBUI_API_KEY` env var) |
| `--knowledge` | Yes | Name of the knowledge collection |
| `--path` | Yes | Path to directory containing files to upload |
| `--create` | No | Create knowledge collection if it doesn't exist |
| `--description` | No | Description for the knowledge collection (used when creating) |
| `--recursive` | No | Recursively scan subdirectories (default: True) |
| `--no-recursive` | No | Do not scan subdirectories |
| `--verbose` / `-v` | No | Enable verbose logging |

### Python Library

You can also use this as a Python library in your own code:

```python
from openwebui_uploader import OpenWebUIClient

# Initialize client
client = OpenWebUIClient(
    api_endpoint="http://localhost:3000",
    api_key="YOUR_API_KEY"
)

# Upload files to knowledge collection
results = client.upload_files_to_knowledge(
    knowledge_name="My Documents",
    file_paths=["file1.pdf", "file2.txt", "file3.docx"],
    create_if_missing=True,
    description="My document collection"
)

print(f"Uploaded {results['success']} files successfully")
print(f"Failed: {results['failed']} files")
```

#### Library Methods

##### `OpenWebUIClient(api_endpoint, api_key)`

Initialize the client with API endpoint and authentication key.

##### `list_knowledge_collections()`

List all knowledge collections.

Returns: `List[Dict[str, Any]]` - List of knowledge collection dictionaries

##### `get_knowledge_collection_id(name)`

Get the ID of a knowledge collection by name.

Parameters:
- `name` (str): Name of the knowledge collection

Returns: `Optional[str]` - Collection ID if found, None otherwise

##### `create_knowledge_collection(name, description='')`

Create a new knowledge collection.

Parameters:
- `name` (str): Name of the knowledge collection
- `description` (str): Optional description

Returns: `Optional[str]` - Collection ID if successful, None otherwise

##### `upload_file(file_path)`

Upload a file to Open WebUI.

Parameters:
- `file_path` (str): Path to the file to upload

Returns: `Optional[str]` - File ID if successful, None otherwise

##### `add_file_to_knowledge(knowledge_id, file_id)`

Associate an uploaded file with a knowledge collection.

Parameters:
- `knowledge_id` (str): ID of the knowledge collection
- `file_id` (str): ID of the uploaded file

Returns: `bool` - True if successful, False otherwise

##### `upload_files_to_knowledge(knowledge_name, file_paths, create_if_missing=False, description='')`

High-level method to upload multiple files to a knowledge collection.

Parameters:
- `knowledge_name` (str): Name of the knowledge collection
- `file_paths` (List[str]): List of file paths to upload
- `create_if_missing` (bool): Create collection if it doesn't exist
- `description` (str): Optional description for the collection

Returns: `Dict[str, Any]` - Dictionary with:
- `success` (int): Number of successfully uploaded files
- `failed` (int): Number of failed uploads
- `total` (int): Total number of files processed
- `errors` (List[str]): List of error messages

## API Endpoints

This application uses the following Open WebUI REST API endpoints:

- `GET /api/v1/knowledge` - List knowledge collections
- `POST /api/v1/knowledge/create` - Create knowledge collection
- `POST /api/v1/files/` - Upload file
- `POST /api/v1/knowledge/{knowledge_id}/file/add` - Add file to knowledge collection

## Error Handling

The application continues processing remaining files if one fails. Errors are logged and included in the final summary. The exit code will be:
- `0` if all files uploaded successfully
- `1` if any files failed to upload

## Examples

### Upload all PDFs from a directory

```python
from pathlib import Path
from openwebui_uploader import OpenWebUIClient

client = OpenWebUIClient(
    api_endpoint="http://localhost:3000",
    api_key="YOUR_API_KEY"
)

# Find all PDF files
pdf_files = [str(p) for p in Path("./documents").rglob("*.pdf")]

# Upload to knowledge collection
results = client.upload_files_to_knowledge(
    knowledge_name="PDF Documents",
    file_paths=pdf_files,
    create_if_missing=True
)
```

### Check if collection exists before uploading

```python
from openwebui_uploader import OpenWebUIClient

client = OpenWebUIClient(
    api_endpoint="http://localhost:3000",
    api_key="YOUR_API_KEY"
)

collection_id = client.get_knowledge_collection_id("My Documents")
if collection_id:
    print(f"Collection exists with ID: {collection_id}")
else:
    print("Collection does not exist")
    collection_id = client.create_knowledge_collection("My Documents", "Description")
```

## Troubleshooting

### Connection Errors

If you encounter connection errors:

1. Verify the API endpoint is correct and accessible
2. Check that Open WebUI is running
3. Ensure your API key is valid
4. Check firewall/network settings

### Authentication Errors

If you get authentication errors:

1. Verify your API key is correct
2. Check that the API key hasn't expired
3. Ensure you're using the correct format: `Bearer {api_key}`

### File Upload Errors

If file uploads fail:

1. Check file permissions
2. Verify file paths are correct
3. Ensure files are not corrupted
4. Check Open WebUI logs for server-side errors

## License

This project is provided as-is for use with Open WebUI.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## References

- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [Open WebUI Documentation](https://docs.openwebui.com/)

