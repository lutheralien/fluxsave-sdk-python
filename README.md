# vaultsens-sdk

Python SDK for VaultSens. API key + secret authentication with file upload, folder management, and image transform helpers.

## Install

```bash
pip install vaultsens-sdk
```

## Quick start

```python
from vaultsens_sdk import VaultSensClient

client = VaultSensClient(
    base_url="https://api.vaultsens.com",
    api_key="your-api-key",
    api_secret="your-api-secret",
)

result = client.upload_file("./photo.png", name="hero", compression="low")
print(result["data"]["_id"])   # file ID
print(result["data"]["url"])   # public URL
```

---

## API reference

### `VaultSensClient(base_url, api_key, api_secret, timeout=30)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `base_url` | `str` | — | Your VaultSens API base URL |
| `api_key` | `str` | — | API key |
| `api_secret` | `str` | — | API secret |
| `timeout` | `int` | `30` | Request timeout in seconds |

---

### Files

#### `upload_file(file_path, name=None, compression=None, folder_id=None)`

Upload a single file.

```python
result = client.upload_file(
    "./photo.png",
    name="my-image",           # optional display name
    compression="medium",      # 'none' | 'low' | 'medium' | 'high'
    folder_id="folder-id",     # optional folder to place the file in
)
```

#### `upload_files(file_paths, name=None, compression=None, folder_id=None)`

Upload multiple files in one request.

```python
result = client.upload_files(
    ["./a.png", "./b.jpg"],
    compression="low",
    folder_id="folder-id",
)
```

#### `list_files(folder_id=None)`

List all files. Pass `folder_id` to filter by folder, or `"root"` for files not in any folder.

```python
all_files = client.list_files()
in_folder = client.list_files(folder_id="folder-id")
at_root   = client.list_files(folder_id="root")
```

#### `get_file_metadata(file_id)`

```python
meta = client.get_file_metadata("file-id")
```

#### `update_file(file_id, file_path, name=None, compression=None)`

Replace a file's content.

```python
client.update_file("file-id", "./new-photo.png", compression="high")
```

#### `delete_file(file_id)`

```python
client.delete_file("file-id")
```

#### `build_file_url(file_id, **options)`

Build a URL for dynamic image transforms.

```python
url = client.build_file_url("file-id", width=800, height=600, format="webp", quality=80)
```

---

### Folders

#### `list_folders()`

```python
result = client.list_folders()
folders = result["data"]
```

#### `create_folder(name, parent_id=None)`

```python
result = client.create_folder("Marketing")
folder_id = result["data"]["_id"]

# nested folder
client.create_folder("2024", parent_id=folder_id)
```

#### `rename_folder(folder_id, name)`

```python
client.rename_folder("folder-id", "New Name")
```

#### `delete_folder(folder_id)`

Deletes the folder and moves all its files back to root.

```python
client.delete_folder("folder-id")
```

---

### Metrics

```python
result = client.get_metrics()
data = result["data"]
# data["totalFiles"], data["totalStorageBytes"], data["storageUsedPercent"], ...
```

---

## Error handling

All API errors raise a `VaultSensError` with a `code`, `status`, and `message`.

```python
from vaultsens_sdk import VaultSensClient, VaultSensError

try:
    client.upload_file("./photo.png")
except VaultSensError as e:
    print(e.status)   # HTTP status code
    print(e.code)     # machine-readable error code
    print(e.message)  # human-readable message

    if e.code == "FILE_TOO_LARGE":
        print("File exceeds your plan limit")
    elif e.code == "STORAGE_LIMIT":
        print("Storage quota exceeded")
    elif e.code == "MIME_TYPE_NOT_ALLOWED":
        print("File type not allowed on your plan")
    elif e.code == "FOLDER_COUNT_LIMIT":
        print("Folder count limit reached")
    elif e.code == "SUBSCRIPTION_INACTIVE":
        print("Subscription is not active")
```

### Error codes

| Code | Status | Description |
|---|---|---|
| `FILE_TOO_LARGE` | 413 | File exceeds plan's `maxFileSizeBytes` |
| `STORAGE_LIMIT` | 413 | Total storage quota exceeded |
| `FILE_COUNT_LIMIT` | 403 | Plan's `maxFilesCount` reached |
| `MIME_TYPE_NOT_ALLOWED` | 415 | File type blocked by plan |
| `COMPRESSION_NOT_ALLOWED` | 403 | Compression level not permitted by plan |
| `SUBSCRIPTION_INACTIVE` | 402 | User subscription is not active |
| `FOLDER_COUNT_LIMIT` | 403 | Plan's `maxFoldersCount` reached |
| `EMAIL_ALREADY_REGISTERED` | 400 | Duplicate email on register |
| `EMAIL_NOT_VERIFIED` | 403 | Login attempted before verifying email |
| `INVALID_CREDENTIALS` | 400 | Wrong email or password |
| `INVALID_OTP` | 400 | Bad or expired verification code |
| `UNAUTHORIZED` | 401 | Missing or invalid credentials |
| `NOT_FOUND` | 404 | Resource not found |
| `UNKNOWN` | — | Any other error |

---

## License

MIT
