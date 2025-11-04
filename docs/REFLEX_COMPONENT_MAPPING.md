# Streamlit to Reflex Component Mapping

## Navigation & Layout

| Streamlit | Reflex | Notes |
|-----------|--------|-------|
| `st.tabs()` | `rx.tabs.root()` + `rx.tabs.list()` + `rx.tabs.content()` | Reflex uses Radix UI tabs component |
| `st.sidebar` | `rx.box()` with fixed positioning or drawer component | Implement as collapsible drawer |
| `st.columns()` | `rx.hstack()` or `rx.grid()` | Use flex/grid layout |
| `st.expander()` | `rx.accordion()` | Radix UI accordion component |
| `st.container()` | `rx.box()` or `rx.container()` | Generic container |

## Input Components

| Streamlit | Reflex | Complexity | Notes |
|-----------|--------|-----------|-------|
| `st.file_uploader()` | `rx.upload()` | Medium | Use `rx.upload()` with `on_drop` handler |
| `st.text_input()` | `rx.input()` | Low | Direct mapping |
| `st.number_input()` | `rx.number_input()` | Low | Direct mapping |
| `st.slider()` | `rx.slider()` | Low | Radix UI slider |
| `st.select_slider()` | `rx.slider()` with discrete values | Medium | Customize with marks |
| `st.selectbox()` | `rx.select()` | Low | Direct mapping |
| `st.multiselect()` | `rx.multi_select()` | Medium | May need custom component |
| `st.checkbox()` | `rx.checkbox()` | Low | Direct mapping |
| `st.radio()` | `rx.radio_group()` | Low | Radix UI radio group |
| `st.date_input()` | `rx.date_picker()` | Medium | May require custom styling |
| `st.button()` | `rx.button()` | Low | Direct mapping with `on_click` |

## Data Display

| Streamlit | Reflex | Complexity | Notes |
|-----------|--------|-----------|-------|
| `st.dataframe()` | `rx.data_table()` | Medium | Good support for pandas DataFrames |
| `st.data_editor()` | `rx.data_editor()` or custom | **High** | **Critical challenge** - may need custom implementation |
| `st.table()` | `rx.table()` | Low | Static table display |
| `st.metric()` | `rx.stat()` or custom card | Medium | Create custom KPI card component |
| `st.json()` | `rx.code_block()` with JSON formatting | Medium | Use syntax highlighting |

## Visualizations

| Streamlit | Reflex | Complexity | Notes |
|-----------|--------|-----------|-------|
| `st.plotly_chart()` | `rx.plotly()` | Low | **Excellent support** - direct Plotly integration |
| Custom Plotly figures | `rx.plotly()` | Low | Pass Plotly figure objects directly |

## File Downloads

| Streamlit | Reflex | Complexity | Notes |
|-----------|--------|-----------|-------|
| `st.download_button()` | `rx.download()` or link with `download` prop | Medium | Generate file in backend, return download URL |

## Notifications & Feedback

| Streamlit | Reflex | Complexity | Notes |
|-----------|--------|-----------|-------|
| `st.success()` | `rx.toast.success()` | Low | Use toast notifications |
| `st.error()` | `rx.toast.error()` | Low | Use toast notifications |
| `st.warning()` | `rx.toast.warning()` | Low | Use toast notifications |
| `st.info()` | `rx.toast.info()` | Low | Use toast notifications |
| `st.spinner()` | `rx.spinner()` or loading state | Medium | Tie to async operations |
| `st.progress()` | `rx.progress()` | Low | Direct mapping |

## Session State

| Streamlit | Reflex | Complexity | Notes |
|-----------|--------|-----------|-------|
| `st.session_state.key` | `State.var_name` | **High** | Complete paradigm shift - requires State classes |
| Session state dict access | Computed vars and event handlers | **High** | All state must be typed and declared |
| Reactive rerun model | Reactive state updates | **High** | Event-driven vs continuous rerun |

## Authentication

| Streamlit | Reflex | Complexity | Notes |
|-----------|--------|-----------|-------|
| Manual JWT handling | Custom auth State class | Medium | Implement login/logout event handlers |
| Sidebar auth UI | Auth component with conditional rendering | Medium | Use `rx.cond()` for authenticated views |

## Critical Challenges

### 1. Interactive Data Editor (`st.data_editor()`)
**Challenge Level: HIGH**

Streamlit's `st.data_editor()` provides:
- Inline cell editing
- Column type validation
- Change tracking
- Clipboard operations

Reflex options:
- **Option A**: `rx.data_editor()` - Check if this component exists and meets needs
- **Option B**: Use `rx.data_table()` with custom edit handlers
- **Option C**: Build custom editable table with cell-level state management

**Recommendation**: Start with `rx.data_editor()` if available. If insufficient, build custom component using `rx.data_table()` with modal editors for cells.

**Implementation sketch:**
```python
class BidLineState(rx.State):
    edited_data: pd.DataFrame

    def update_cell(self, row_idx: int, col_name: str, new_value: Any):
        self.edited_data.at[row_idx, col_name] = new_value
        # Trigger validation

rx.data_table(
    data=BidLineState.edited_data,
    on_cell_edit=BidLineState.update_cell
)
```

### 2. File Uploads with Progress
**Challenge Level: MEDIUM**

Streamlit handles file upload state automatically. Reflex requires explicit handling:

```python
class UploadState(rx.State):
    upload_progress: int = 0
    uploaded_files: list[rx.UploadFile] = []

    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            data = await file.read()
            # Process PDF with existing backend modules
            # Update progress
            self.upload_progress = ...
```

### 3. PDF Generation & Downloads
**Challenge Level: MEDIUM**

Existing ReportLab code can be reused. Main challenge is serving generated files:

```python
class ExportState(rx.State):
    async def generate_pdf(self):
        # Use existing pdf_generation/ modules
        from pdf_generation import create_edw_pdf_report

        pdf_bytes = create_edw_pdf_report(...)

        # Save to temporary location or return as download
        return rx.download(data=pdf_bytes, filename="report.pdf")
```

### 4. JWT Session Handling for Supabase RLS
**Challenge Level: MEDIUM-HIGH**

Current approach in `database.py`:
```python
def get_supabase_client():
    jwt_token = st.session_state.get("jwt_token")
    client = create_client(url, key)
    if jwt_token:
        client.postgrest.auth(jwt_token)
    return client
```

Reflex approach:
```python
class AuthState(rx.State):
    jwt_token: str = ""
    user_email: str = ""

    def get_supabase_client(self):
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        if self.jwt_token:
            client.postgrest.auth(self.jwt_token)
        return client

    async def login(self, email: str, password: str):
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        self.jwt_token = response.session.access_token
        self.user_email = response.user.email
```

### 5. Pagination & Complex Queries
**Challenge Level: MEDIUM**

Database Explorer tab uses pagination. Reflex requires explicit page state management:

```python
class QueryState(rx.State):
    results: list[dict] = []
    current_page: int = 1
    page_size: int = 50
    total_records: int = 0

    @rx.var
    def total_pages(self) -> int:
        return (self.total_records + self.page_size - 1) // self.page_size

    @rx.var
    def paginated_results(self) -> list[dict]:
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.results[start:end]

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
```

---

## State Management Pattern

### Streamlit Session State Example:
```python
# Current approach
if 'edw_results' not in st.session_state:
    st.session_state.edw_results = None

if uploaded_file:
    results = parse_edw_pdf(uploaded_file)
    st.session_state.edw_results = results
```

### Reflex State Class Example:
```python
class EDWState(rx.State):
    # Typed state variables
    edw_results: Optional[Dict[str, Any]] = None
    uploaded_file_name: str = ""
    is_processing: bool = False
    error_message: str = ""

    # Computed vars (derived state)
    @rx.var
    def has_results(self) -> bool:
        return self.edw_results is not None

    @rx.var
    def total_trips(self) -> int:
        if self.edw_results:
            return len(self.edw_results.get('trips', []))
        return 0

    # Event handlers
    async def process_upload(self, files: list[rx.UploadFile]):
        self.is_processing = True
        try:
            for file in files:
                data = await file.read()
                # Use existing edw/ module
                from edw import run_edw_report
                self.edw_results = run_edw_report(data)
                self.uploaded_file_name = file.filename
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_processing = False
```

---

## Styling Approach

Reflex supports multiple styling approaches. Recommend using **inline style dictionaries** initially for consistency with existing UI, then migrate to Tailwind classes for performance.

### Example:
```python
# Inline styles (initial migration)
rx.box(
    rx.heading("EDW Pairing Analyzer", size="lg"),
    style={
        "background_color": "#1e3a8a",  # Navy from branding
        "padding": "2rem",
        "border_radius": "0.5rem"
    }
)

# Tailwind classes (optimization phase)
rx.box(
    rx.heading("EDW Pairing Analyzer", size="lg"),
    class_name="bg-navy-900 p-8 rounded-lg"
)
```

---

## Key Behavioral Differences

### 1. Rerun Model
- **Streamlit**: Entire script reruns on any interaction
- **Reflex**: Event-driven updates only affect changed state

**Implication**: Logic that depends on sequential reruns must be refactored into explicit event handlers.

### 2. File Uploads
- **Streamlit**: `st.file_uploader()` returns file object directly
- **Reflex**: `rx.upload()` triggers async handler with file list

**Implication**: PDF processing must be wrapped in async handlers.

### 3. Data Binding
- **Streamlit**: Two-way binding via session state
- **Reflex**: Explicit binding with `value=State.var` and `on_change=State.set_var`

**Implication**: All form inputs need explicit event handlers.

---

## Testing Considerations

### Component Testing Strategy:
1. **Unit tests**: Test State classes and event handlers independently
2. **Integration tests**: Test Supabase interactions with mock JWT tokens
3. **E2E tests**: Use Playwright to test critical workflows (upload → process → download)
4. **Visual regression**: Compare Streamlit and Reflex screenshots

### Critical Test Cases:
- [ ] PDF upload and parsing (both PyPDF2 and pdfplumber paths)
- [ ] Data editor validation and change tracking
- [ ] Multi-dimensional filtering with state updates
- [ ] JWT-based authentication and RLS policy enforcement
- [ ] Pagination with large result sets
- [ ] CSV/Excel/PDF export generation
- [ ] Responsive layout on mobile devices
- [ ] Concurrent user sessions (state isolation)

---

## Performance Considerations

### Reflex Performance Advantages:
- **Reactive updates**: Only changed components re-render (vs full page refresh)
- **WebSocket communication**: Faster than HTTP polling
- **Backend Python**: All business logic stays in Python (no JS bridge)

### Potential Bottlenecks:
- **Large DataFrames**: `rx.data_table()` performance with 1000+ rows
  - **Mitigation**: Implement virtual scrolling or pagination
- **PDF generation**: ReportLab is synchronous and blocking
  - **Mitigation**: Use background tasks with progress indicators
- **State serialization**: Large state objects increase WebSocket overhead
  - **Mitigation**: Use computed vars for derived data, keep state lean

---

## Recommended Component Library

Consider integrating **Radix UI components** (already supported by Reflex):
- `rx.accordion()` - Collapsible sections
- `rx.dialog()` - Modal dialogs for confirmations
- `rx.toast()` - Notifications
- `rx.tabs()` - Primary navigation
- `rx.dropdown_menu()` - Filter menus
- `rx.progress()` - Upload progress indicators

These provide accessible, well-tested UI patterns out of the box.
