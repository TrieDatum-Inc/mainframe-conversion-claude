# User Administration Frontend

Next.js frontend for the CardDemo User Administration module.

Converted from BMS screens:
- **COUSR0A** (COUSR00) — List Users (COUSR00C)
- **COUSR1A** (COUSR01) — Add User (COUSR01C)
- **COUSR2A** (COUSR02) — Update User (COUSR02C)
- **COUSR3A** (COUSR03) — Delete User (COUSR03C)

## BMS to UI Mapping

| BMS Attribute | UI Equivalent |
|--------------|---------------|
| UNPROT fields | Editable `<input>` |
| ASKIP fields | `readOnly` inputs (protected fields on delete screen) |
| DRK (password) | `type="password"` input |
| PF3 (Back/Save&Exit) | "Back (F3)" / "Save & Exit (F3)" buttons |
| PF4 (Clear) | "Clear (F4)" button — resets form |
| PF5 (Save/Delete) | "Save (F5)" / "Delete (F5)" confirm button |
| PF7 (Backward) | "F7 - Backward" pagination button |
| PF8 (Forward) | "F8 - Forward" pagination button |
| PF12 (Cancel) | "Cancel (F12)" button |
| ERRMSG (Row 23) | `StatusMessage` component (red=error, green=success, blue=info) |

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Install

```bash
npm install
```

### Configure

Copy `.env.local.example` to `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Run

```bash
npm run dev
```

Open http://localhost:3000/users

## Pages

| Route | COBOL Screen | Description |
|-------|-------------|-------------|
| `/users` | COUSR00C | Paginated user list with search |
| `/users/new` | COUSR01C | Add new user form |
| `/users/{id}/edit` | COUSR02C | Update existing user |
| `/users/{id}/delete` | COUSR03C | Delete user confirmation |

## Tests

```bash
npm test
```

19 tests covering API service layer and utility functions.

## Key Design Decisions

### Delete Confirmation (COUSR03C Two-Phase Pattern)
The delete flow matches COUSR03C exactly:
1. Navigate to `/users/{id}/delete` — fetches user data for read-only display (ENTER key)
2. Click "Delete (F5)" to confirm — issues DELETE API call (PF5 key)
3. Click "Back/Cancel (F3)" to abort without deleting (PF3 key)

Data fields (First Name, Last Name, User Type) are rendered as `readOnly` inputs, mirroring the ASKIP attribute in COUSR03 BMS map.

### Update Save-and-Exit (COUSR02C PF3 Behaviour)
COUSR02C's PF3 key saves before exiting (unlike PF12 which cancels).
The "Save & Exit (F3)" button calls the update API then redirects to the list.

### Password Handling
Passwords are never pre-populated in the Update form (DRK field in BMS — non-display).
A new password must be entered on every update to trigger a change.
