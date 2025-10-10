# [Feature Name] Data Model

## Overview

Detailed data structures, schemas, and relationships for [feature name].

## Core Data Structures

### [Entity Name 1]
```typescript
interface EntityName {
  id: string;
  name: string;
  status: EntityStatus;
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

enum EntityStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  PENDING = 'pending'
}
```

**Purpose**: [What this entity represents]
**Usage**: [How it's used in the system]
**Validation**: [Key validation rules]

### [Entity Name 2]
```typescript
interface SecondEntity {
  id: string;
  entityId: string;  // Foreign key to EntityName
  data: EntityData;
  version: number;
}

interface EntityData {
  [key: string]: any;
}
```

**Purpose**: [What this entity represents]
**Relationships**: Links to EntityName via entityId
**Usage**: [How it's used in the system]

## Relationships

### Entity Relationships
```
EntityName (1) ←→ (many) SecondEntity
    ↓
  status: EntityStatus
    ↓
  metadata: Record<string, any>
```

### Relationship Rules
- **One-to-Many**: EntityName can have multiple SecondEntity records
- **Cascade**: Deleting EntityName removes related SecondEntity records
- **Validation**: SecondEntity.entityId must reference valid EntityName.id

## Database Schema

### Tables
```sql
-- EntityName table
CREATE TABLE entity_name (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'pending')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SecondEntity table
CREATE TABLE second_entity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entity_name(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_entity_name_status ON entity_name(status);
CREATE INDEX idx_entity_name_created_at ON entity_name(created_at);
CREATE INDEX idx_second_entity_entity_id ON second_entity(entity_id);
```

## API Data Formats

### Request/Response Formats
```typescript
// Create Entity Request
interface CreateEntityRequest {
  name: string;
  metadata?: Record<string, any>;
}

// Entity Response
interface EntityResponse {
  id: string;
  name: string;
  status: EntityStatus;
  metadata: Record<string, any>;
  createdAt: string;  // ISO date string
  updatedAt: string;  // ISO date string
}
```

### Validation Rules
- **name**: Required, 1-255 characters, alphanumeric and spaces only
- **status**: Must be valid EntityStatus enum value
- **metadata**: Optional object, max 10KB serialized size
- **id**: UUID format, auto-generated

## Data Flow

### Create Flow
```
Client Request → Validation → Database Insert → Response
     ↓              ↓             ↓            ↓
CreateEntityReq → Rules Check → entity_name → EntityResponse
```

### Update Flow
```
Client Request → Validation → Database Update → Response
     ↓              ↓             ↓            ↓
UpdateEntityReq → Rules Check → entity_name → EntityResponse
                                     ↓
                              updated_at = NOW()
```

## Migration Strategy

### Version History
- **v1.0**: Initial schema with basic entity structure
- **v1.1**: Added metadata field for extensibility
- **v1.2**: Added second_entity table for relationships

### Migration Scripts
```sql
-- v1.1 Migration: Add metadata field
ALTER TABLE entity_name ADD COLUMN metadata JSONB DEFAULT '{}';

-- v1.2 Migration: Add second_entity table
CREATE TABLE second_entity (
    -- schema definition above
);
```

## Performance Considerations

### Query Optimization
- Use indexes on frequently queried fields (status, created_at)
- Limit metadata field size to prevent performance issues
- Use pagination for large result sets

### Caching Strategy
- Cache frequently accessed entities by ID
- Cache status-based queries with TTL
- Invalidate cache on entity updates

## Related Documents

- **[Requirements](requirements.md)** - Data requirements and constraints
- **[Design](design.md)** - How data model fits into overall architecture
- **[API Specification](architecture/interfaces/)** - Detailed API definitions