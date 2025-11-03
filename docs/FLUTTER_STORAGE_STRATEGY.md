# Flutter Client Storage Strategy

## Project Context

### Two Separate Sparky Projects Exist

1. **Existing Sparky Backend Project**
   - Postgres database for conversation storage
   - Weaviate for vector search/semantic memory
   - Currently being re-engineered for memory management
   - Uses tools like MemOS and Langchain
   - At a turning point in development

2. **This Project: Voice/UI Client**
   - Flutter desktop application (Windows/Linux/macOS)
   - Voice interaction with wake word detection ("Hey Jarvis")
   - Text chat interface
   - WebSocket communication with orchestrator services
   - Focus: User interface and voice interaction

### Current Status

- Backend project is undergoing significant re-engineering
- Flutter client development should proceed independently
- Eventually the two projects will merge for production

## Development Strategy

### Phase 1: Independent Development (NOW)

**Objective**: Develop Flutter client without dependency on backend storage system

**Approach**: 
- Use **local storage** (Hive database) for conversation history
- Implement **Repository Pattern** for storage abstraction
- Client remains fully functional during backend re-engineering

**Benefits**:
- ✅ Fast Flutter development without backend blockers
- ✅ Backend team can re-engineer memory system independently
- ✅ No coordination overhead during development
- ✅ Clean separation of concerns

### Phase 2: Backend Integration (LATER)

**Objective**: Connect Flutter client to Postgres/Weaviate backend

**Approach**:
- Swap local repository implementation for API repository
- Add API endpoints to backend for conversation management
- Zero changes to UI code required

**Trigger**: When backend memory re-engineering is stable and ready

## Technical Implementation

### Repository Pattern Architecture

```dart
// Abstract interface - never changes
abstract class ConversationRepository {
  Future<List<Message>> getMessages();
  Future<void> addMessage(Message message);
  Future<void> clearHistory();
}

// LOCAL IMPLEMENTATION (Phase 1)
class LocalConversationRepository implements ConversationRepository {
  // Uses Hive database for local storage
  // Fast, lightweight, pure Dart
  // Perfect for development/temporary storage
}

// BACKEND IMPLEMENTATION (Phase 2)
class ApiConversationRepository implements ConversationRepository {
  // Makes HTTP/WebSocket calls to backend API
  // Integrates with Postgres/Weaviate storage
  // Enables multi-device sync, persistent history
}
```

### Application Code (Storage-Agnostic)

```dart
// Configuration layer decides which implementation to use
final conversationRepo = LocalConversationRepository(); 
// Later becomes: ApiConversationRepository()

// All app code uses the abstract interface
class ConversationProvider {
  final ConversationRepository _repo;
  
  Future<void> loadHistory() async {
    messages = await _repo.getMessages();  // Works with EITHER implementation
  }
  
  Future<void> saveMessage(Message msg) async {
    await _repo.addMessage(msg);  // Works with EITHER implementation
  }
}
```

### Migration Path

**Phase 1 → Phase 2 Migration Steps**:

1. Implement `ApiConversationRepository` class
2. Add backend API endpoints (GET/POST conversations)
3. Change ONE line in configuration:
   ```dart
   // Before
   final conversationRepo = LocalConversationRepository();
   
   // After
   final conversationRepo = ApiConversationRepository();
   ```
4. Done. Zero UI code changes required.

## Local Storage Technology: Hive

**Why Hive?**
- Pure Dart implementation (no native dependencies)
- Fast and lightweight
- NoSQL/key-value storage (simpler than SQLite)
- Perfect for temporary/development storage
- Easy to completely remove later

**Installation**: 
```yaml
dependencies:
  hive: ^2.2.3
  hive_flutter: ^1.1.0
```

**Usage Pattern**:
```dart
// Open storage box
var box = await Hive.openBox('conversations');

// Store message
box.put(messageId, messageObject);

// Retrieve messages
var messages = box.values.toList();
```

## Key Principles

1. **Storage abstraction is mandatory** - Never let UI code directly access storage
2. **Interface never changes** - Only implementations swap
3. **Local storage is temporary** - Design knowing it will be replaced
4. **Backend integration is trivial** - One configuration line change
5. **Development stays independent** - Backend and client teams work in parallel

## Future Integration Considerations

When backend is ready for integration:

- Backend API should match repository interface pattern
- Consider WebSocket vs HTTP for real-time message sync
- Plan for migration of any locally-stored development conversations (if needed)
- Ensure backend handles conversation context for AI (memory management)
- Multi-device support becomes possible with backend storage

## Decision Rationale

**Why not wait for backend?**
- Backend re-engineering timeline uncertain
- Flutter development can proceed immediately
- Pattern ensures clean integration later
- No technical debt created

**Why not integrate now?**
- Backend in flux (memory management re-engineering)
- Would slow down both teams
- Creates unnecessary coordination overhead
- Integration is trivial with repository pattern

## Success Criteria

**Phase 1 Complete When**:
- Flutter client fully functional with local storage
- Voice and text chat working end-to-end
- WebSocket communication with orchestrator stable
- UI polished and professional

**Phase 2 Complete When**:
- Backend API endpoints implemented
- Flutter client connected to Postgres/Weaviate
- Conversation history persists server-side
- Multi-device access possible

---

**Document Created**: 2025-11-02  
**Status**: Active Development Strategy  
**Review**: Update when transitioning from Phase 1 to Phase 2
