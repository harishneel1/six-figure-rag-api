# Logging Documentation

## Overview

This project uses **structlog** for structured logging with JSON output, designed for production deployments on AWS EKS Fargate. All logs are written to stdout for easy integration with container logging systems.

## Features

- **JSON formatted logs** for easy parsing and analysis
- **ISO UTC timestamps** for consistent time tracking across regions
- **Automatic context injection** via context variables:
  - `request_id`: Unique identifier for each request
  - `user_id`: Authenticated user identifier
  - `pod_name`: Kubernetes pod name (from `POD_NAME` env var)
  - `host_name`: Server hostname
- **Caller information**: Method name, file name, and line number
- **Exception tracking**: Full stack traces for errors
- **Log level filtering**: Configurable via `LOG_LEVEL` environment variable
- **FastAPI middleware**: Automatic request/response logging
- **Celery integration**: Automatic task logging with task_id as request_id

## Configuration

### Environment Variables

Set the following environment variable to control log verbosity:

```bash
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

For Kubernetes deployments, also set:

```bash
POD_NAME=${POD_NAME}  # Automatically set by Kubernetes
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error events that might still allow the application to continue
- **CRITICAL**: Severe error events that may cause the application to abort

## Usage

### Basic Logging

```python
from src.config.logging import get_logger

logger = get_logger(__name__)

# Simple log message
logger.info("user_logged_in", user_id="12345", email="user@example.com")

# Log with multiple fields
logger.info(
    "order_created",
    order_id="ord_123",
    user_id="user_456",
    total_amount=99.99,
    items_count=3
)

# Debug logging
logger.debug("processing_step", step=1, data={"key": "value"})

# Warning
logger.warning("rate_limit_approaching", current=95, limit=100)

# Error with exception
try:
    result = risky_operation()
except Exception as e:
    logger.error("operation_failed", operation="risky_operation", exc_info=True)
```

### Logging in FastAPI Routes

The logging middleware automatically injects `request_id` and `user_id` (if authenticated) into all logs within a request context.

```python
from fastapi import APIRouter, Depends
from src.config.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/items/")
async def create_item(item: Item, user_id: str = Depends(get_current_user)):
    logger.info("creating_item", item_name=item.name, price=item.price)

    try:
        # Your business logic here
        result = db.insert(item)

        logger.info("item_created_successfully", item_id=result.id)
        return result

    except Exception as e:
        logger.error("item_creation_failed", error=str(e), exc_info=True)
        raise
```

### Logging in Celery Tasks

Celery tasks automatically get logging configured with `task_id` set as `request_id`:

```python
from celery import Celery
from src.config.logging import get_logger

logger = get_logger(__name__)

@celery_app.task
def process_user_data(user_id: str):
    # task_id is automatically set as request_id by Celery signals
    logger.info("processing_user_data", user_id=user_id)

    try:
        result = expensive_operation(user_id)
        logger.info("user_data_processed", user_id=user_id, records=len(result))
        return result

    except Exception as e:
        logger.error("user_data_processing_failed", user_id=user_id, exc_info=True)
        raise
```

The Celery integration automatically:
- Initializes logging when worker starts (`worker_process_init` signal)
- Sets `task_id` as `request_id` before task execution (`task_prerun` signal)
- Logs task start with args/kwargs
- Logs task completion with result
- Logs task failures with full exception info
- Clears context after task completes (`task_postrun` signal)

### Manual Context Management

If you need to set context outside of HTTP requests or Celery tasks:

```python
from src.config.logging import set_request_id, set_user_id, clear_context, get_logger

logger = get_logger(__name__)

# Set context
set_request_id("task-12345")
set_user_id("user-67890")

logger.info("background_task_started", task_type="email_send")

# Your task logic here

# Clear context when done
clear_context()
```

## Log Output Format

### Example Log Entry

```json
{
  "timestamp": "2025-11-29T10:30:45.123456Z",
  "level": "INFO",
  "message": "creating_chat",
  "logger": "src.routes.chatRoutes",
  "func_name": "create_chat",
  "filename": "chatRoutes.py",
  "lineno": 31,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_12345",
  "pod_name": "api-deployment-6d4f8c9b7-xh2kq",
  "host_name": "ip-10-0-1-42",
  "title": "New Chat",
  "project_id": "proj_789"
}
```

### Exception Log Entry

```json
{
  "timestamp": "2025-11-29T10:31:12.456789Z",
  "level": "ERROR",
  "message": "chat_creation_error",
  "logger": "src.routes.chatRoutes",
  "func_name": "create_chat",
  "filename": "chatRoutes.py",
  "lineno": 70,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_12345",
  "pod_name": "api-deployment-6d4f8c9b7-xh2kq",
  "host_name": "ip-10-0-1-42",
  "error": "Database connection timeout",
  "project_id": "proj_789",
  "exception": "Traceback (most recent call last):\n  File \"/app/src/routes/chatRoutes.py\", line 45, in create_chat\n    ..."
}
```

### Request Logging

The middleware automatically logs all HTTP requests and responses:

**Request Log:**
```json
{
  "timestamp": "2025-11-29T10:30:45.000000Z",
  "level": "INFO",
  "message": "request_started",
  "logger": "src.middleware.logging_middleware",
  "func_name": "dispatch",
  "filename": "logging_middleware.py",
  "lineno": 50,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_12345",
  "pod_name": "api-deployment-6d4f8c9b7-xh2kq",
  "host_name": "ip-10-0-1-42",
  "method": "POST",
  "path": "/api/chats/",
  "query_params": {},
  "client_host": "192.168.1.100"
}
```

**Response Log:**
```json
{
  "timestamp": "2025-11-29T10:30:45.234000Z",
  "level": "INFO",
  "message": "request_completed",
  "logger": "src.middleware.logging_middleware",
  "func_name": "dispatch",
  "filename": "logging_middleware.py",
  "lineno": 65,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_12345",
  "pod_name": "api-deployment-6d4f8c9b7-xh2kq",
  "host_name": "ip-10-0-1-42",
  "method": "POST",
  "path": "/api/chats/",
  "status_code": 200,
  "duration_seconds": 0.234
}
```

### Celery Task Logs

**Task Start Log:**
```json
{
  "timestamp": "2025-11-29T10:35:10.000000Z",
  "level": "INFO",
  "message": "task_started",
  "logger": "src.services.celery",
  "func_name": "task_prerun_handler",
  "filename": "celery.py",
  "lineno": 34,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "pod_name": "worker-deployment-6d4f8c9b7-abc12",
  "host_name": "ip-10-0-2-10",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "task_name": "src.services.celery.perform_rag_ingestion_task",
  "args": ["doc_12345"],
  "kwargs": {}
}
```

**Task Within Execution:**
```json
{
  "timestamp": "2025-11-29T10:35:12.500000Z",
  "level": "INFO",
  "message": "processing_document",
  "logger": "src.services.celery",
  "func_name": "perform_rag_ingestion_task",
  "filename": "celery.py",
  "lineno": 92,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "pod_name": "worker-deployment-6d4f8c9b7-abc12",
  "host_name": "ip-10-0-2-10",
  "document_id": "doc_12345"
}
```

**Task Completion Log:**
```json
{
  "timestamp": "2025-11-29T10:35:45.800000Z",
  "level": "INFO",
  "message": "task_completed",
  "logger": "src.services.celery",
  "func_name": "task_postrun_handler",
  "filename": "celery.py",
  "lineno": 49,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "pod_name": "worker-deployment-6d4f8c9b7-abc12",
  "host_name": "ip-10-0-2-10",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "task_name": "src.services.celery.perform_rag_ingestion_task",
  "state": "SUCCESS",
  "result": "Document doc_12345 processed successfully"
}
```

## Best Practices

### 1. Use Descriptive Event Names

Use snake_case event names that describe the action:

```python
# Good
logger.info("user_login_successful", user_id="123")
logger.error("database_connection_failed", db_host="localhost")

# Avoid
logger.info("Login OK")
logger.error("DB error")
```

### 2. Include Relevant Context

Add key-value pairs for important context:

```python
logger.info(
    "payment_processed",
    payment_id="pay_123",
    amount=99.99,
    currency="USD",
    payment_method="card",
    customer_id="cust_456"
)
```

### 3. Use Appropriate Log Levels

- **DEBUG**: Verbose details for debugging
- **INFO**: Normal operations and business events
- **WARNING**: Unexpected but handled situations
- **ERROR**: Errors that need attention
- **CRITICAL**: System-threatening errors

### 4. Always Log Exceptions with Stack Traces

```python
try:
    dangerous_operation()
except Exception as e:
    logger.error("operation_failed", operation="dangerous", exc_info=True)
    raise
```

### 5. Avoid Logging Sensitive Data

Never log passwords, tokens, credit card numbers, or PII:

```python
# Bad
logger.info("user_created", password=password, ssn=ssn)

# Good
logger.info("user_created", user_id=user_id, email_domain=email.split('@')[1])
```

## Deployment Considerations

### AWS EKS Fargate

The logging configuration is optimized for EKS Fargate:

1. **Stdout/Stderr**: All logs go to stdout for container log collection
2. **JSON Format**: CloudWatch Logs can parse JSON for filtering
3. **Pod Name**: Set via Kubernetes downward API:

```yaml
env:
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: LOG_LEVEL
    value: "INFO"
```

### CloudWatch Logs Insights Queries

Example queries for CloudWatch Logs Insights:

**Find all errors for a specific user:**
```
fields @timestamp, message, error, exception
| filter user_id = "user_12345" and level = "ERROR"
| sort @timestamp desc
```

**Track request duration:**
```
fields @timestamp, path, duration_seconds, status_code
| filter message = "request_completed"
| stats avg(duration_seconds), max(duration_seconds) by path
```

**Trace a specific request:**
```
fields @timestamp, message, func_name, filename, lineno
| filter request_id = "550e8400-e29b-41d4-a716-446655440000"
| sort @timestamp asc
```

**Track Celery task performance:**
```
fields @timestamp, task_name, state, duration
| filter message = "task_completed"
| stats avg(duration), max(duration), count(*) by task_name, state
```

**Find failed Celery tasks:**
```
fields @timestamp, task_id, task_name, error, exception
| filter message = "task_failed"
| sort @timestamp desc
```

**Trace a specific Celery task:**
```
fields @timestamp, message, func_name, document_id
| filter request_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
| sort @timestamp asc
```

## Troubleshooting

### Logs Not Appearing

Check that logging is initialized in [src/server.py](src/server.py:11):
```python
configure_logging()
```

### Wrong Log Level

Verify `LOG_LEVEL` environment variable:
```bash
echo $LOG_LEVEL
```

### Missing Context Variables

Ensure the logging middleware is added first in [src/server.py](src/server.py:24):
```python
app.add_middleware(LoggingMiddleware)
```

### User ID Not Appearing

The middleware looks for `request.state.user_id` or `request.state.user.id`. Ensure your auth middleware sets one of these.

## Migration Guide

To add logging to existing code:

1. Import the logger:
   ```python
   from src.config.logging import get_logger
   logger = get_logger(__name__)
   ```

2. Replace print statements:
   ```python
   # Before
   print(f"Processing item {item_id}")

   # After
   logger.info("processing_item", item_id=item_id)
   ```

3. Add error logging:
   ```python
   # Before
   except Exception as e:
       print(f"Error: {e}")

   # After
   except Exception as e:
       logger.error("operation_failed", error=str(e), exc_info=True)
   ```

## Additional Resources

- [structlog Documentation](https://www.structlog.org/)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [AWS CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)