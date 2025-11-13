# Comprehensive Logging System

This document describes the comprehensive logging system implemented across the Lead Qualification Platform for error tracking, debugging, and monitoring.

## Overview

The platform implements structured logging at all levels:
- **Backend API**: Request/response logging with correlation IDs
- **AI Agents**: Execution tracking with timings and errors
- **Workers**: Stream processing and task logging
- **Frontend**: User actions, API calls, and error tracking
- **Error Boundaries**: React error catching and logging

## Backend Logging

### Request/Response Logging

Every API request is logged with:
- **Request ID**: Unique identifier for tracking (UUID)
- **Method & Path**: HTTP method and endpoint
- **Client Info**: IP address, user agent
- **Duration**: Request processing time
- **Status Code**: Response status
- **Errors**: Full stack traces for failures

Example log output:
```json
{
  "event": "incoming_request",
  "request_id": "abc123-def456",
  "method": "POST",
  "path": "/api/v1/signals/",
  "client_host": "192.168.1.100",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Middleware Components

**RequestLoggingMiddleware**
- Generates unique request ID
- Logs all incoming requests
- Tracks request duration
- Adds request ID to response headers (`X-Request-ID`)

**ErrorLoggingMiddleware**
- Catches unhandled exceptions
- Logs with full context
- Includes stack traces

### Error Handling

**Global Exception Handler**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Logs with request_id, error type, and full context
    # Returns JSON with request_id for frontend tracking
```

## AI Agent Logging

### Execution Tracking

Each agent execution is tracked with:
- **Execution ID**: Unique identifier (UUID)
- **Agent Name & Type**: Which agent is running
- **Company ID**: Context being processed
- **Start/End Times**: When execution began and completed
- **Duration**: Total execution time
- **Errors/Warnings**: Any issues encountered

Example:
```json
{
  "event": "agent_started",
  "execution_id": "exec-789xyz",
  "agent_name": "Enricher",
  "agent_type": "enricher",
  "company_id": 123,
  "start_time": "2024-01-15T10:30:00Z"
}
```

### Agent Methods

```python
# Log actions
self.log_action("discovered_urls", {"count": 10})

# Log warnings
self.log_warning("Incomplete data", {"field": "revenue"})

# Log errors
self.log_error("Failed to fetch", error=e, {"url": url})
```

### State Tracking

AgentState includes:
- `execution_id`: Tracks across agent chain
- `errors`: List of all errors
- `warnings`: List of all warnings
- `metadata`: Timing and execution data

## Frontend Logging

### Logger Utility (`lib/logger.ts`)

Centralized logging with levels:
- **DEBUG**: Development details
- **INFO**: General information
- **WARN**: Warning conditions
- **ERROR**: Error conditions

Features:
- Console logging with colored output
- Request ID tracking
- Context preservation
- Performance metrics
- User action tracking
- Automatic global error handlers

### Usage Examples

```typescript
import logger from '@/lib/logger'

// Basic logging
logger.info('User logged in', { userId: 123 })
logger.warn('Slow API response', { duration: 5000 })
logger.error('API call failed', error, { endpoint: '/api/...' })

// API calls
logger.logApiCall('POST', '/api/signals', 200, 150)

// User actions
logger.logUserAction('create_proposal', { companyId: 456 })

// Performance
logger.logPerformance('page_load', 1250, 'ms')

// Component lifecycle
logger.logComponentMount('Dashboard', { props })
logger.logComponentUnmount('Dashboard')
```

### Request ID Correlation

The logger extracts request IDs from API responses:
```typescript
const requestId = response.headers.get('X-Request-ID')
logger.setRequestId(requestId)
```

This allows correlating frontend errors with backend logs.

## Error Boundaries

React Error Boundary catches component errors:

```typescript
<ErrorBoundary onError={(error, info) => {
  // Custom error handling
}}>
  <YourComponent />
</ErrorBoundary>
```

Features:
- Catches React rendering errors
- Logs to logger with component stack
- Shows user-friendly error UI
- Provides retry/reload options
- Shows error details in development

## Log Levels

### Development
- All levels logged to console
- Detailed stack traces
- Component lifecycle tracking

### Production
- INFO and above logged
- WARN and ERROR sent to remote (future)
- Errors include minimal stack traces
- PII is redacted

## Structured Logging Format

All logs use JSON format:
```json
{
  "level": "error",
  "timestamp": "2024-01-15T10:30:00Z",
  "event": "api_call_failed",
  "request_id": "abc-123",
  "method": "POST",
  "path": "/api/v1/signals",
  "error_type": "HTTPException",
  "error_message": "Validation failed",
  "duration_seconds": 0.150,
  "stack_trace": "..."
}
```

## Monitoring & Debugging

### Finding Errors

**By Request ID:**
```bash
# Backend logs
docker-compose logs api | grep "abc-123"

# View all logs for a request
docker-compose logs -f | grep "abc-123"
```

**By Event Type:**
```bash
# Find all errors
docker-compose logs api | grep '"level":"error"'

# Find agent failures
docker-compose logs workers | grep "agent_execution_failed"
```

### Common Patterns

**Trace Request Flow:**
1. Frontend makes API call
2. RequestLoggingMiddleware logs `incoming_request` with `request_id`
3. Handler processes request
4. Any errors logged with same `request_id`
5. Response returns with `X-Request-ID` header
6. Frontend logger captures `request_id`
7. Frontend errors include `request_id`

**Trace Agent Execution:**
1. Agent run triggered with `execution_id`
2. `agent_started` event logged
3. Each action logged with `execution_id`
4. `agent_completed` or `agent_execution_failed` logged
5. All logs searchable by `execution_id`

## Performance Tracking

### Logged Metrics

- **API Response Times**: Every request duration
- **Agent Execution Times**: Each agent's runtime
- **Database Query Times**: (via SQLAlchemy logging)
- **External API Calls**: Third-party service latency
- **Frontend Load Times**: Page and component load

### Example Queries

```bash
# Slow API requests (>1s)
docker-compose logs api | grep "duration_seconds" | awk '$NF > 1'

# Agent performance
docker-compose logs workers | grep "agent_completed" | grep "duration_seconds"
```

## Log Retention

- **Console Logs**: Stored in Docker logs (default 7 days)
- **Structured Logs**: Can be exported to:
  - Elasticsearch/OpenSearch
  - CloudWatch
  - Datadog
  - Custom logging service

## Best Practices

### Do:
✅ Include request_id in all related logs
✅ Use structured fields (JSON keys)
✅ Log timing information
✅ Include error context
✅ Use appropriate log levels

### Don't:
❌ Log sensitive data (passwords, tokens, PII)
❌ Log in hot loops
❌ Use string concatenation in logs
❌ Log without context
❌ Forget to handle exceptions

## Troubleshooting

### No Logs Appearing

1. Check log level: `LOG_LEVEL=debug` in .env
2. Ensure service is running: `docker-compose ps`
3. Check Docker logs: `docker-compose logs <service>`

### Request ID Missing

- Ensure middleware is properly configured
- Check middleware order (logging middleware first)
- Verify CORS exposes `X-Request-ID` header

### Frontend Errors Not Logged

- Check browser console for logger errors
- Verify logger is imported correctly
- Ensure Error Boundary is wrapping components

## Future Enhancements

- [ ] Remote log aggregation
- [ ] Real-time log streaming dashboard
- [ ] Automated error alerting
- [ ] Log-based metrics and dashboards
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Log retention policies
- [ ] PII redaction automation

## Examples

### Complete Request Trace

1. Frontend logs API call
2. Backend logs incoming request
3. Service processes with database queries
4. External API called (logged)
5. Agent executed (logged)
6. Response returned (logged)
7. Frontend logs response

All linked by `request_id`!

### Debug Production Issue

```bash
# Get request ID from user
REQUEST_ID="abc-123"

# Find all logs for request
docker-compose logs -f | grep "$REQUEST_ID"

# Exports to file for analysis
docker-compose logs | grep "$REQUEST_ID" > debug.log
```

---

For questions or issues with logging, check:
- Service logs: `docker-compose logs <service>`
- Health endpoint: http://localhost:8080/health
- Metrics: http://localhost:9090 (Prometheus)
