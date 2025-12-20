# @kidyland/utils

Shared utilities for frontend apps.

## Features

- **Auth Store**: JWT token management and user state
- **API Client**: Authenticated HTTP requests with automatic token injection
- **WebSocket Client**: Real-time connections with exponential backoff reconnection

## Usage

### Auth

```typescript
import { login, logout, user, token, hasRole } from "@kidyland/utils";

// Login
await login("username", "password");

// Check role
if (hasRole("super_admin")) {
  // ...
}

// Logout
logout();
```

### API Client

```typescript
import { get, post, apiRequest } from "@kidyland/utils";

// GET request
const users = await get("/users");

// POST request
const sale = await post("/sales", { ... });
```

### WebSocket

```typescript
import { createTimerWebSocket } from "@kidyland/utils";

const ws = createTimerWebSocket(sucursalId, {
  onMessage: (data) => {
    console.log("Timer update:", data);
  }
});

ws.connect();
// ...
ws.disconnect();
```
































