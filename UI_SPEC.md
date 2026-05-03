# Kitchen Food Waste Tracker — Full UI & Functionality Specification

This document describes every page, every button, every input, and every interaction
in the application. Use this as the single source of truth for what the app does.

---

## GLOBAL ELEMENTS (present on every authenticated page)

### Sidebar (240px, left)
| Element | Type | Action |
|---|---|---|
| Logo + "Kitchen Food Waste" | Display | — |
| Dashboard | Nav link | `page.go("/dashboard")` |
| Inventory | Nav link | `page.go("/inventory")` |
| Expiry Monitor | Nav link (inventory_staff + manager only) | `page.go("/expiry")` |
| Waste Logs | Nav link (inventory_staff + manager only) | `page.go("/waste-logs")` |
| Reports | Nav link (manager only) | `page.go("/reports")` |
| Categories | Nav link (manager only) | `page.go("/categories")` |
| Users & Staff | Nav link (manager only) | `page.go("/users")` |
| Sign Out | Button | Clears `page.session.store`, navigates to `/` |

Active page is highlighted orange with chevron arrow.
Settings is intentionally removed — not implemented.

### Top Bar
| Element | Type | Action |
|---|---|---|
| Search field | TextField | Currently decorative — does not filter globally |
| Notification bell icon | Icon | Decorative — no notification system |
| Username | Text | Shows `page.session.store.get("username")` |
| Role label | Text | Shows mapped role: chef→"Kitchen Staff", inventory_staff→"Inventory Manager", manager→"General Manager" |
| Avatar circle | Container | Shows first 2 letters of username |

### Footer
| Element | Type | Action |
|---|---|---|
| "© 2026 Kitchen Food Waste Tracker" | Text | Decorative |
| Privacy Policy / Terms / Help Center | Text links | Decorative — no pages behind them |

---

## PAGE 1: LOGIN (`/`)

**Purpose:** Authenticate users. No public registration.

### Elements
| Element | Type | Action |
|---|---|---|
| Logo + title "Kitchen Waste Tracker" | Display | — |
| Subtitle | Text | "Manage inventory, reduce waste, and optimize kitchen operations." |
| Email or Username field | TextField | Input for login |
| Password field | TextField | Password input with show/hide toggle |
| "Forgot password?" link | TextButton | **No-op** — placeholder only, no forgot flow |
| "Keep me logged in" checkbox | Checkbox | Decorative — session is in-memory only, clears on app restart |
| Sign In button (orange) | Button | Validates inputs → queries `users` table → on success: sets `is_logged_in`, `username`, `role` in session → `page.go("/dashboard")` |
| Error text (red) | Text | Shows validation errors: empty fields, wrong credentials, deactivated account |
| Authorized Personas chips | Display | Shows 3 role chips (Kitchen Staff, Inventory Mgr, General Mgr) — informational only |
| Light/Dark mode toggle | IconButton | Switches `page.theme_mode` between LIGHT and DARK |

### Login Logic
```
1. User enters username/email + password
2. Query: SELECT username, role FROM users WHERE (username=? OR email=?) AND password=?
3. Also check: is_active must be 1 (if 0 → "Account deactivated" error)
4. On success: store is_logged_in=True, username, role in session
5. Navigate to /dashboard
```

### Default Account
- Username: `manager` | Password: `1234` | Role: `manager`
- Seeded automatically on first app launch

---

## PAGE 2: DASHBOARD (`/dashboard`)

**Purpose:** Overview of kitchen status at a glance. Read-only summary — no data editing here.

### Stat Cards Row (4 cards)
| Card | Data Source | Shows |
|---|---|---|
| Total Items | `SELECT COUNT(*) FROM inventory` | Number of inventory rows |
| Near Expiry | Computed: items where `0 <= days_left <= 7` | Count + "needs attention" |
| Expired Today | Computed: items where `expiry_date < today` | Count |
| Waste Cost (Wk) | `SELECT SUM(cost_estimate) FROM waste_logs WHERE waste_date >= 7_days_ago` | Dollar amount |

Each card shows a trend indicator (arrow + percentage) — currently decorative.

### Waste Distribution Card
| Element | Data Source | Shows |
|---|---|---|
| Horizontal bars | `waste_logs JOIN inventory GROUP BY category, SUM(cost_estimate)` | Top 5 categories by waste cost |
| "..." menu icon | IconButton | No-op |

### Daily Waste Trend Card
| Element | Data Source | Shows |
|---|---|---|
| Line chart | `waste_logs last 7 days, SUM(cost_estimate) per day` | Cost trend line (orange) |
| "On Track" badge | Computed | Green badge if trend is declining |
| Day labels (x-axis) | Computed | Last 7 day names |

### Expiring Soon Card
| Element | Type | Action |
|---|---|---|
| Table (5 rows max) | DataTable | Shows items with `expiry_date` within 7 days, sorted by soonest |
| Columns: Item Name, Category, Expiry, Status | — | Status pill: "Near Expiry" (orange) or "Expired" (red) |
| "View Monitor >" link | TextButton | `page.go("/expiry")` |

### Recent Waste Logs Card
| Element | Type | Action |
|---|---|---|
| Table (5 rows max) | DataTable | Shows last 5 waste_logs joined with inventory |
| Columns: Item + qty, Reason, Cost, Recorded time | — | Reason has colored dot prefix |
| "All Logs >" link | TextButton | `page.go("/waste-logs")` |

### Action Buttons
| Button | Visibility | Action |
|---|---|---|
| Date range display "Oct 18 - Oct 25" | Always | **Should show current week dates** |
| "Record Waste" (orange) | Chef + Manager only | `page.go("/waste/new")` |

---

## PAGE 3: INVENTORY (`/inventory`)

**Purpose:** View, search, filter, and manage all food items in stock.

### Header
| Element | Type | Action |
|---|---|---|
| Title "Inventory" | Text | — |
| "+ Add Food Item" button (orange) | Button | Clears `edit_item_id` from session → `page.go("/add-item")` |

### Filter Row
| Element | Type | Action |
|---|---|---|
| Search field | TextField | Filters by `item_name` or `sku` (LIKE query) — live on keystroke |
| Category dropdown | Dropdown | Options: All Categories + Dairy/Meat/Produce/etc. — filters table |
| Status dropdown | Dropdown | Options: All Status / Fresh / Expiring Soon / Expired — computed filter |
| Storage dropdown | Dropdown | Options: All Storage + Walk-in Fridge/Freezer A/etc. — filters table |
| Refresh icon | IconButton | Resets all filters to default, page to 1 |

### Table
| Column | Data | Notes |
|---|---|---|
| Item Name + SKU | `item_name`, `sku` | Orange food icon + two-line cell |
| Category | `category` | Plain text |
| Quantity | `quantity` + `unit` | e.g. "12 L", "5 kg" |
| Storage | `storage` | e.g. "Walk-in Fridge" |
| Soonest Expiry | `expiry_date` | Date string YYYY-MM-DD |
| Status | Computed from `expiry_date` | Pill: Fresh (green) / Expiring Soon (orange) / Expired (red) |
| Actions | PopupMenuButton | Edit → sets `edit_item_id` in session + `page.go("/add-item")`. Delete → confirmation dialog → `DELETE FROM inventory` |

**Row click:** Entire row is clickable → `page.go(f"/item/{item_id}")`

### Pagination
- 6 items per page
- Shows "Showing 1-6 of N items"
- Previous / page numbers / Next buttons

### Bottom Stat Cards (4 cards)
| Card | Data Source |
|---|---|
| Total Categories | `SELECT COUNT(DISTINCT category) FROM inventory` |
| Near Expiry | Count of items with `0 <= days_left <= 7` |
| Expired Items | Count of items with `days_left < 0` |
| Stock Value | `SELECT SUM(quantity * 10) FROM inventory` — placeholder $10/unit rate |

---

## PAGE 4: ADD / EDIT FOOD ITEM (`/add-item`)

**Purpose:** Create a new inventory item, or edit an existing one.

**Mode detection:** If `edit_item_id` exists in session → Edit mode (pre-fills form). Otherwise → Add mode.

### "← Back to Inventory" link
Clears `edit_item_id` → `page.go("/inventory")`

### Form Section 1: Basic Details
| Field | Type | Required | Notes |
|---|---|---|---|
| Item Name | TextField | ✅ | e.g. "Organic Whole Milk" |
| Category | Dropdown | ✅ | 12 options: Dairy & Eggs, Meat, Produce, etc. Stored as short name (Dairy, Meat...) |
| Storage Location | Dropdown | ✅ | 8 options: Walk-in Cooler 1, Freezer A, etc. |

### Form Section 2: Inventory & Units
| Field | Type | Required | Notes |
|---|---|---|---|
| Quantity | TextField (number) | ✅ | Numeric input, e.g. "12.5" |
| Unit | Dropdown | ✅ | Kilograms/Liters/Pieces/Bags/Loaves/Cups/Bottles → stored as kg/L/pcs/etc. |
| Purchase Date | TextField | No | Defaults to today (YYYY-MM-DD) |
| Internal Notes | TextField (multiline) | No | e.g. "Grass-fed, supplier: Local Meadows Farm" |

### Form Section 3: Expiry Monitoring
| Field | Type | Required | Notes |
|---|---|---|---|
| Batch Number | TextField | No | e.g. "BATCH-2024-001" — for tracking shipments |
| Expiry Date | TextField | ✅ | YYYY-MM-DD — the actual expiration date of THIS specific batch |
| Alert Threshold (Days) | TextField (number) | No | Default 3. Days before expiry to flag as "Near Expiry" |

**Pro Tip card:** Shows "Most dairy items expire within 7 days" — static informational.

### Action Buttons
| Button | Action |
|---|---|
| Cancel | Clears `edit_item_id` → `page.go("/inventory")` |
| Save & Add Another (Add mode only) | Validates → INSERT → resets form → SnackBar "Item saved!" |
| Save Product / Update Product (orange) | Validates → INSERT or UPDATE → `page.go("/inventory")` |

### Validation Rules
- Item Name: not empty
- Quantity: numeric, not empty
- Expiry Date: valid YYYY-MM-DD format
- Alert Threshold: whole number

### SKU Generation
Auto-generated: `SKU-00001`, `SKU-00002`, etc. based on `MAX(id) + 1`.

---

## PAGE 5: ITEM DETAIL (`/item/{id}`)

**Purpose:** Full view of a single inventory item with batch info, waste history, and actions.

### "← Back to Inventory" link
`page.go("/inventory")`

### Header Row
| Element | Action |
|---|---|
| Item name (H1) | Display |
| "Record Waste" button (outlined) | `page.go("/waste/new")` |
| "Update Stock" button (orange) | Opens Update Stock modal |

### Summary Card
Shows in one row: item icon, Category, Storage, Purchase Date, Current Stock (quantity + unit), Status pill.
**Current Stock text is a named reference** — updates live after Update Stock modal saves.

### Tabs
#### Tab 1: Expiry Batches
| Column | Data |
|---|---|
| Batch Number | `batch_number` or "—" if blank |
| Expiry Date | `expiry_date` |
| Time Remaining | Computed: "12 days left" / "Expires today" / "4 days overdue" |
| Status | Pill: Fresh / Expiring Soon / Expired |
| Actions | PopupMenu: "Mark as Used" (no-op), "Record Waste" (no-op) |

Currently each inventory row = one batch. If item has no batch_number, shows "—".

#### Tab 2: Waste History
Queries `waste_logs WHERE item_id = this item's id`.
If records exist → shows table with: Date, Quantity, Reason, Cost.
If no records → shows "No waste history yet" with inbox icon.

#### Tab 3: Activity Timeline
Always shows "No activity recorded yet" — no data source for this.

### Bottom Info Cards (3 cards, hardcoded placeholders)
| Card | Content |
|---|---|
| Last Handled By | "Kitchen Staff / Inventory Specialist • Shift A" — placeholder |
| Supplier Info | "Local Supplier / ID: N/A / Lead Time: N/A" + "View Contract" link (no-op) |
| Usage Policy | Static text about food safety guidelines |

### UPDATE STOCK MODAL
Triggered by "Update Stock" button.

| Element | Type | Action |
|---|---|---|
| Info row | Display | Shows current quantity + unit and storage location |
| Restock (Add) toggle | Container | Sets mode to "restock" — highlighted orange when active |
| Withdraw (Subtract) toggle | Container | Sets mode to "withdraw" |
| Adjustment Amount field | TextField (number) | Input amount to add/subtract |
| Projected New Total | Live display | Recalculates on every keystroke: restock → current + amount, withdraw → max(0, current - amount) |
| Adjustment Note | TextField (multiline) | Optional note |
| Cancel | Button | Closes dialog, no changes |
| Save Changes (orange) | Button | Validates amount > 0 → UPDATE inventory SET quantity=new_qty → updates header card text → closes dialog |

---

## PAGE 6: RECORD FOOD WASTE (`/waste/new`)

**Purpose:** Log a waste event — an item was thrown away or couldn't be used.

### Left Column — Form
#### Item Selection Card
| Field | Type | Action |
|---|---|---|
| Item dropdown | Dropdown | Populated from `SELECT id, item_name, unit FROM inventory`. On select: auto-fills unit, updates Waste Impact panel |
| Unit display | Dropdown | Auto-filled from selected item's unit, but editable |

#### Logistics Card
| Field | Type | Notes |
|---|---|---|
| Quantity Wasted | TextField (number) | How much was wasted |
| Date | TextField | Defaults to today YYYY-MM-DD |
| Reason | Dropdown | Expired / Spoiled / Prep Waste / Overproduction / Damaged / Other |
| Cost Estimate (auto) | TextField (disabled) | `quantity × 10` — auto-calculated, read-only |

#### Additional Context Card
| Field | Type | Notes |
|---|---|---|
| Disposal Notes | TextField (multiline) | Optional: "Fridge power outage", "Prep station spill" |

### Right Column — Waste Impact Panel (300px)
| Element | Updates When |
|---|---|
| Projected Loss ($) | qty or item changes → recalculates `qty × 10` |
| Item name | Item selected from dropdown |
| Quantity display | qty field changes |
| Reason display | reason selected |
| "Cost estimated at $10.00/unit" | Static info note |

### Action Bar
| Button | Action |
|---|---|
| Cancel | `page.go("/inventory")` |
| Save Waste Record (orange) | Validates: item selected, qty > 0, reason selected → INSERT INTO waste_logs → `page.go("/waste-logs")` |

---

## PAGE 7: EXPIRY MONITOR (`/expiry`)

**Purpose:** Track items nearing or past expiration. Helps kitchen staff prioritize what to use first.

### Tabs
| Tab | Shows |
|---|---|
| Near Expiry | Items where `0 <= days_left <= threshold` |
| Expired | Items where `days_left < 0` |
| All Items | Everything regardless of status |

### Filter Controls
| Element | Type | Action |
|---|---|---|
| Search field | TextField | Filters by item_name, SKU, or batch_number |
| Threshold slider | Slider (1-14, default 3) | Changes what counts as "Near Expiry". Moving to 7 = items expiring within 7 days appear in Near Expiry tab |
| Threshold label | Text | "Threshold: 3 days" — updates with slider |

### Table
| Column | Data |
|---|---|
| Item Name + Category | Two-line cell |
| Batch ID | `batch_number` or "—" |
| Expiry Date | YYYY-MM-DD |
| Quantity | quantity + unit |
| Status | Two-line: pill (Expired/Expiring Soon/Fresh) + detail text ("Expired (2d ago)" / "Expiring Soon (1d left)") |
| Actions | PopupMenu: "Open Item" → `/item/{id}`, "Record Waste" → `/waste/new` |

**Row click:** `page.go(f"/item/{item_id}")`

### Bottom Info Cards (3 cards, static text)
| Card | Content |
|---|---|
| Waste Prevention | "Spot items before they expire and reduce unnecessary spoilage." |
| Staff Alerts | "Keep teams aware of near-expiry stock that needs attention." |
| Data Logging | "Track expiry status over time to support better kitchen decisions." |

---

## PAGE 8: WASTE LOGS (`/waste-logs`)

**Purpose:** Audit trail of all waste events. Filter, search, and analyze waste history.

### Summary Metric Cards (3 cards)
| Card | Data Source |
|---|---|
| Waste Cost Today | `SUM(cost_estimate) WHERE waste_date = today` |
| Volume MTD | `SUM(qty_wasted) WHERE waste_date >= first_of_month` |
| Avoidable Waste % | `SUM(cost WHERE reason IN ('prep_waste','overproduction')) / SUM(total_cost) × 100` |

### Filter Controls
| Element | Type | Action |
|---|---|---|
| Search field | TextField | Filters by item name, category, reason |
| Date From | TextField | YYYY-MM-DD — start of date range |
| Date To | TextField | YYYY-MM-DD — end of date range |
| Reason dropdown | Dropdown | All Reasons / Expired / Spoiled / Prep Waste / Overproduction / Damaged / Other |

### Table
| Column | Data |
|---|---|
| Date & Time | `waste_date` |
| Item & Category | Two-line: `item_name` + `category` (JOIN inventory) |
| Quantity | `qty_wasted` + `unit` |
| Reason | Colored badge: Expired (red), Spoiled (orange), Prep Waste (yellow), Overproduction (blue), Damaged/Other (gray) |
| Cost Estimate | `$XX.XX` format |
| Recorded By | Session username (no recorded_by column in DB yet) |
| Actions | PopupMenu: "Open Item" → `/item/{id}`, "Record Waste" → `/waste/new` |

### Pagination
8 rows per page.

### Bottom Insight Card
Shows dynamically: "Highest cost this month: [reason] at $[amount]"
If no data: "No waste logged this month"

---

## PAGE 9: REPORTS (`/reports`)

**Purpose:** Manager-only analytics dashboard. Deep dive into waste trends and financial impact.

### Period Toggle
| Button | Time Range |
|---|---|
| Daily (default) | Last 7 days |
| Weekly | Last 4 weeks |
| Monthly | Last 6 months |

Clicking re-queries all data and updates all charts.

### "Download CSV" Button
Currently: **no-op** — should show SnackBar "Export feature coming soon"

### Summary Metric Cards (3 cards)
| Card | Data Source |
|---|---|
| Total Financial Loss | `SUM(cost_estimate)` from waste_logs in selected period |
| Wasted Weight | `SUM(qty_wasted)` in selected period (shown as kg) |
| Kitchen Efficiency % | `100 - (avoidable_cost / total_cost × 100)`. Avoidable = prep_waste + overproduction |

### Waste Cost Trend (Line Chart)
- X-axis: dates in selected period
- Y-axis: SUM(cost_estimate) per day
- Uses `flet_charts.LineChart` with orange line and gradient fill below

### Waste by Reason (Bar Chart)
- Horizontal bars grouped by reason
- Each bar: reason label | colored bar proportional to cost | dollar amount
- Colors: Expired=red, Spoiled=orange, Prep Waste=gold, Overproduction=blue, Damaged/Other=gray

### Top Wasted Items by Cost (Bar Chart)
- Top 5 items by SUM(cost_estimate)
- Horizontal orange bars with item name and dollar amount
- Data: `waste_logs GROUP BY item_id JOIN inventory, ORDER BY SUM(cost_estimate) DESC LIMIT 5`

### Manager Insight Card
Dynamic text: "Highest-cost reason this period: [reason] at $[amount]. Focus controls on this area to reduce kitchen loss."

---

## PAGE 10: CATEGORIES (`/categories`)

**Purpose:** Manager-only. Define food categories with default shelf life values.

### Header
| Element | Action |
|---|---|
| Title "Categories Management" | — |
| "+ Add Category" button (orange) | Opens Add/Edit modal |

### Summary Metric Cards (3 cards)
| Card | Data Source |
|---|---|
| Total Categories | `SELECT COUNT(*) FROM categories` |
| Tracked Items | `SELECT COUNT(*) FROM inventory` |
| Avg Shelf Life | `SELECT AVG(shelf_life_days) FROM categories` → shown as "X Days" |

### Table
| Column | Data | Notes |
|---|---|---|
| Category Name | `category_name` + initial letter badge (colored circle) | Circle color varies by name hash |
| Shelf Life | `shelf_life_days` | Pill badge: orange if ≤3 days, green otherwise |
| Description | `description` | Plain text |
| Total Items | `SELECT COUNT(*) FROM inventory WHERE category = ?` | Per-category count |
| Actions | Edit (pencil) + Delete (trash) + PopupMenu | — |

### Add/Edit Category Modal
| Field | Type | Required |
|---|---|---|
| Category Name | TextField | ✅ (must be unique) |
| Description | TextField (multiline) | No |
| Shelf Life (Days) | TextField (number) | Yes (must be > 0) |

| Button | Action |
|---|---|
| Cancel | Closes dialog |
| Save Category | INSERT or UPDATE → refresh table |

### Delete Category Dialog
Confirmation: "Delete category '[name]'? This will remove it from the categories table."
Does NOT delete inventory items in that category — just the category definition.

### Management Tip Card
Static: "Shelf life defaults help the app suggest safer expiry dates..."

### Shelf Life vs Expiry Date — How They Relate
- `shelf_life_days` in categories = **template/default** for that food type
- `expiry_date` in inventory = **actual date** for a specific batch
- **Currently:** these are NOT connected. User manually types expiry_date.
- **Ideal future behavior:** when adding an item, if user selects category "Dairy & Eggs" (shelf_life=7), the expiry_date field auto-suggests `purchase_date + 7 days`. Not yet implemented.

---

## PAGE 11: USERS & STAFF (`/users`)

**Purpose:** Manager-only. Create, view, edit, and deactivate user accounts.

### Layout
- No tabs — single page showing all users as card grid
- Filter row: search field + role filter dropdown (All Roles / Chef / Inventory Staff / Manager)
- "+ New User" button inside page content (not in top bar)

### User Card Grid (3 columns)
Each card shows:
| Element | Data |
|---|---|
| Avatar circle | First 2 letters of username |
| Username | `username` |
| Email | `email` |
| Role badge | Colored text: "Chef", "Inventory Staff", "Manager" |
| Status badge | "Active" (green) or "Inactive" (red) |
| Edit icon | Opens Edit modal |
| Deactivate icon | Toggles `is_active` in DB |

### New User Modal
| Field | Type | Required |
|---|---|---|
| Username | TextField | ✅ |
| Email | TextField | ✅ |
| Password | TextField (password) | ✅ |
| Confirm Password | TextField (password) | ✅ (must match) |
| Role | Dropdown | ✅ (Chef / Inventory Staff / Manager) |

Save → INSERT INTO users → refresh grid.

### Edit User Modal
| Field | Type | Editable |
|---|---|---|
| Username | TextField | ❌ Display only |
| Email | TextField | ✅ |
| Role | Dropdown | ✅ |

Save → UPDATE users SET email=?, role=? → refresh grid.

### Manager Hierarchy Rules
| Actor | Can Edit | Cannot Edit |
|---|---|---|
| Head manager (`username='manager'`) | Everyone except self | Own account (hide edit/deactivate buttons) |
| Regular manager (any other manager) | Chef + Inventory Staff only | Other managers → SnackBar: "Only the head manager can modify manager accounts" |
| Chef / Inventory Staff | — | Cannot access this page at all (route-gated) |

### Deactivation
- Sets `is_active=0` in users table
- Card shows "Inactive" badge
- Deactivated user cannot log in (blocked at login with error message)
- Same hierarchy: regular managers cannot deactivate other managers

---

## DISABLED / PLACEHOLDER ELEMENTS

These exist in the UI but intentionally do nothing:

| Element | Location | Status |
|---|---|---|
| "Forgot password?" link | Login page | Placeholder — no forgot flow |
| Notification bell icon | Top bar (all pages) | Decorative — no notification system |
| "View Contract" link | Item Detail → Supplier Info card | Placeholder |
| "Mark as Used" menu item | Item Detail → Expiry Batches tab actions | No-op |
| Global search field | Top bar (all pages) | Decorative — no global search implemented |
| Privacy Policy / Terms / Help Center | Footer (all pages) | Decorative links |
| Download CSV | Reports page | Should show SnackBar "Export coming soon" |
| "Keep me logged in" checkbox | Login page | Decorative — session is in-memory only |