
# Example: Simple Feature - User Authentication

Complete specification example following current patterns.

## Requirements Document

**Metadata Management:**
```bash
# Initialize specification
./.spec-dev/scripts/spec-meta.sh init user-auth --author "Example Team"

# Update status after approval
./.spec-dev/scripts/spec-meta.sh update user-auth --status approved --phase design

# Check health
./.spec-dev/scripts/spec-health.sh user-auth --json
```

**Content (requirements.md):**
```markdown
# User Authentication Requirements

## Introduction
Simple user authentication system allowing account creation, login, and logout functionality.

## Requirements

### Requirement 1: Account Creation
**User Story (US-001):** As a new user, I want to create an account, so that I can access the application.

#### Acceptance Criteria
- **AC-001**: WHEN a user submits valid email and password THEN system SHALL create new account
- **AC-002**: IF email already exists THEN system SHALL display error message

### Requirement 2: User Login  
**User Story (US-002):** As a registered user, I want to log in, so that I can access my account.

#### Acceptance Criteria
- **AC-003**: WHEN user submits valid credentials THEN system SHALL authenticate user
- **AC-004**: IF credentials are invalid THEN system SHALL display error message

### Requirement 3: User Logout
**User Story (US-003):** As a logged-in user, I want to log out, so that I can secure my account.

#### Acceptance Criteria
- **AC-005**: WHEN user clicks logout THEN system SHALL end user session

## Structured Data (AI Consumption)
```json
[
  {"id": "AC-001", "user_story": "US-001", "type": "WHEN", "event": "user submits valid email and password", "response": "create new account"},
  {"id": "AC-002", "user_story": "US-001", "type": "IF", "precondition": "email already exists", "response": "display error message"},
  {"id": "AC-003", "user_story": "US-002", "type": "WHEN", "event": "user submits valid credentials", "response": "authenticate user"}
]
```
```

## Design Document

**Metadata Management:**
```bash
# Update to design phase
./.spec-dev/scripts/spec-meta.sh update user-auth --status approved --phase tasks

# Update health after design completion
./.spec-dev/scripts/health-update.sh user-auth --score 95 --compliance "EARS: ✓, Cross-refs: ✓, Structure: ✓"
```

**Content (design.md):**
```markdown
# User Authentication Design

## Overview
RESTful API authentication system with PostgreSQL storage and JWT tokens.

## Architecture
- **API Layer**: Express.js REST endpoints
- **Auth Service**: JWT token management
- **Data Layer**: PostgreSQL with bcrypt hashing

## Components
### AuthController
**Purpose**: Handle authentication requests
**Interface**: POST /api/auth/register, POST /api/auth/login, DELETE /api/auth/logout

### User Model
**Purpose**: User data management
**Interface**: User.create(), User.findByEmail(), User.validatePassword()

## Data Models
```typescript
interface User {
  id: string;
  email: string;
  password_hash: string;
  created_at: Date;
}
```

## Design Decisions (AI Consumption)
```json
[
  {"id": "DD-001", "decision": "JWT tokens for session management", "rationale": "Stateless and scalable", "impact": "No server-side session storage needed"},
  {"id": "DD-002", "decision": "bcrypt for password hashing", "rationale": "Industry standard security", "impact": "Secure password storage"}
]
```
```

## Tasks Document

**Metadata Management:**
```bash
# Update to implementation phase
./.spec-dev/scripts/spec-meta.sh update user-auth --status approved --phase implementation

# Update task progress
./.spec-dev/scripts/task-progress.sh user-auth T-001 completed
./.spec-dev/scripts/task-progress.sh user-auth T-002 in-progress

# Check progress
./.spec-dev/scripts/task-progress.sh user-auth --json
```

**Content (tasks.md):**
```markdown
# User Authentication Implementation Tasks

## Development Status
- ✅ **Completed**: 0 tasks
- 🚧 **In Progress**: 0 tasks
- ⏳ **Pending**: 6 tasks
- 📊 **Progress**: 0% complete

## Tasks

### Foundation Setup
- [ ] **T-001**: Create users table schema
  - Requirements: US-001
  - Implementation: PostgreSQL migration with email, password_hash fields
  - Verification: Table exists with proper constraints
  - Status: pending

- [ ] **T-002**: Implement User model
  - Requirements: US-001, US-002
  - Implementation: User class with validation and bcrypt methods
  - Verification: Model tests pass
  - Status: pending

### Authentication Implementation
- [ ] **T-003**: Create registration endpoint
  - Requirements: US-001
  - Implementation: POST /api/auth/register with validation
  - Verification: Can create new users successfully
  - Status: pending

- [ ] **T-004**: Create login endpoint
  - Requirements: US-002
  - Implementation: POST /api/auth/login with JWT generation
  - Verification: Returns valid JWT token
  - Status: pending

- [ ] **T-005**: Create logout endpoint
  - Requirements: US-003
  - Implementation: DELETE /api/auth/logout with token invalidation
  - Verification: Token becomes invalid after logout
  - Status: pending

### Testing & Validation
- [ ] **T-006**: Integration test suite
  - Requirements: All user stories
  - Implementation: End-to-end authentication flow tests
  - Verification: All authentication scenarios pass
  - Status: pending
```
