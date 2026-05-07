# Skill: Add WebSocket Event

## When to apply
Adding a new real-time event that the server broadcasts to all connected clients (new task lifecycle event, new notification type, heartbeat, etc.).

## Steps

### Backend

1. **Broadcast from the right place**:
   - From an `async` context (route handler): use `await ws_manager.broadcast(payload)`
   - From the executor thread (sync): use `ws_manager.broadcast_sync(payload)`

2. **Payload shape** — always a JSON-serializable dict with a `type` key:
   ```python
   # In backend/app/core/ws_manager.py or wherever the event originates
   payload = {
       "type": "my_event",          # snake_case, unique name
       "task_id": task.id,
       "data": { ... }
   }
   await ws_manager.broadcast(payload)
   # or from executor.py:
   ws_manager.broadcast_sync(payload)
   ```

3. **Document the new event** in `CLAUDE.md` WebSocket Events table.

### Frontend

4. **Handle in the WS hook** at `frontend/src/hooks/useWebSocket.ts`:
   ```typescript
   case "my_event": {
     const { task_id, data } = msg;
     useStore.getState().someAction(task_id, data);
     break;
   }
   ```

5. **Add store action** in `frontend/src/store/index.ts` if state needs updating:
   ```typescript
   someAction: (taskId: string, data: MyData) =>
     set((s) => ({
       tasks: {
         ...s.tasks,
         [taskId]: { ...s.tasks[taskId], ...data },
       },
     })),
   ```

6. **Update TypeScript types** — add to the `Task` interface in `frontend/src/services/api.ts` or a types file if new fields are involved.

## What not to do
- Don't send raw strings over WebSocket — always JSON with a `type` field
- Don't create a new WebSocket connection for a new event type — reuse the single WS server on port 8765
- Don't handle WS events in component files — all WS logic stays in `useWebSocket.ts`
- Don't mutate store state outside of Zustand `set()` calls
