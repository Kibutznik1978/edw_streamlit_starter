# Reflex Migration Testing Strategy

## Testing Philosophy

The migration testing strategy follows a **multi-layered approach** to ensure functional parity, performance, and reliability:

1. **Backend Logic Testing**: Ensure shared modules work correctly (already mostly covered)
2. **State Unit Testing**: Test Reflex State classes in isolation
3. **Component Integration Testing**: Test UI components with mocked state
4. **End-to-End Testing**: Test complete user workflows
5. **Comparison Testing**: Validate Reflex output matches Streamlit
6. **Performance Testing**: Ensure acceptable performance under load
7. **Security Testing**: Validate authentication and authorization

---

## Test Pyramid

```
           /\
          /  \        E2E Tests (10%)
         /____\       - Critical user workflows
        /      \      - Cross-browser testing
       /        \
      /__________\    Integration Tests (30%)
     /            \   - State + Components
    /              \  - Database interactions
   /________________\
  /                  \ Unit Tests (60%)
 /____________________\ - Backend modules
                       - State methods
                       - Utility functions
```

---

## Phase-by-Phase Testing Plan

### Phase 0: Setup & POC Testing

**Goal**: Validate critical technical assumptions

**Test Cases**:
1. **Data Editor POC**:
   - [ ] Can create editable DataFrame
   - [ ] Cell edits update state
   - [ ] Validation rules can be applied
   - [ ] Changes can be tracked

2. **File Upload POC**:
   - [ ] Can upload PDF file
   - [ ] Async file read works correctly
   - [ ] File content accessible in State

3. **Plotly Integration POC**:
   - [ ] Plotly figure renders in `rx.plotly()`
   - [ ] Interactive features work (hover, zoom)
   - [ ] Charts are responsive

4. **JWT Auth POC**:
   - [ ] Can log in with Supabase
   - [ ] JWT token is accessible in State
   - [ ] JWT claims include custom fields

**Acceptance**: All 4 POCs demonstrate feasibility or have acceptable workarounds.

---

### Phase 1: Auth & Database Testing

**Goal**: Ensure authentication and database operations work correctly

#### Unit Tests (State Methods)

```python
# tests/test_auth_state.py
import pytest
from reflex_app.state.auth import AuthState

def test_login_success():
    """Test successful login sets JWT and user info"""
    state = AuthState()
    # Mock Supabase response
    with patch('supabase.auth.sign_in_with_password') as mock_login:
        mock_login.return_value = MockAuthResponse(
            access_token="mock_jwt",
            user={"email": "test@example.com"}
        )

        state.login("test@example.com", "password123")

        assert state.jwt_token == "mock_jwt"
        assert state.user_email == "test@example.com"
        assert state.is_authenticated is True

def test_login_failure():
    """Test failed login shows error"""
    state = AuthState()
    with patch('supabase.auth.sign_in_with_password') as mock_login:
        mock_login.side_effect = Exception("Invalid credentials")

        state.login("test@example.com", "wrongpassword")

        assert state.is_authenticated is False
        assert "Invalid credentials" in state.error_message

def test_jwt_claims_decoding():
    """Test JWT claims are correctly decoded"""
    state = AuthState()
    state.jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."  # Mock JWT

    claims = state.jwt_claims

    assert claims['user_id'] == "mock_user_id"
    assert claims['is_admin'] is False

def test_supabase_client_with_jwt():
    """Test Supabase client is configured with JWT"""
    state = AuthState()
    state.jwt_token = "mock_jwt"

    client = state.get_supabase_client()

    # Verify JWT was set in client
    assert client.postgrest.headers['Authorization'] == 'Bearer mock_jwt'
```

```python
# tests/test_database_state.py
import pytest
from reflex_app.state.database import DatabaseState

def test_save_pairing_data():
    """Test saving pairing data to database"""
    state = DatabaseState()
    state.jwt_token = "mock_jwt"
    state.user_id = "test_user"

    pairing_data = {
        'domicile': 'ONT',
        'aircraft': '757',
        'bid_period': '2507',
        'trips': [...]
    }

    with patch.object(state, 'get_supabase_client') as mock_client:
        state.save_pairing_data(pairing_data)

        # Verify database calls
        mock_client.return_value.table.assert_called()
        # Check audit fields populated
        assert 'created_by' in pairing_data

def test_query_pairings_with_filters():
    """Test querying pairings with filters"""
    state = DatabaseState()
    state.jwt_token = "mock_jwt"

    filters = {
        'domicile': 'ONT',
        'aircraft': '757',
        'bid_period': '2507'
    }

    results = state.query_pairings(filters)

    assert len(results) > 0
    assert all(r['domicile'] == 'ONT' for r in results)
```

#### Integration Tests (RLS Policies)

```python
# tests/integration/test_rls_policies.py
import pytest
from supabase import create_client

@pytest.fixture
def admin_client():
    """Supabase client with admin JWT"""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    # Login as admin
    response = client.auth.sign_in_with_password({
        'email': 'giladswerdlow@gmail.com',
        'password': os.getenv('ADMIN_PASSWORD')
    })
    client.postgrest.auth(response.session.access_token)
    return client

@pytest.fixture
def regular_user_client():
    """Supabase client with regular user JWT"""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    # Login as regular user
    response = client.auth.sign_in_with_password({
        'email': 'regular@example.com',
        'password': 'test_password'
    })
    client.postgrest.auth(response.session.access_token)
    return client

def test_admin_can_read_all_pairings(admin_client):
    """Admin can read all pairing records"""
    result = admin_client.table('pairings').select('*').execute()
    assert len(result.data) > 0

def test_regular_user_cannot_read_others_pairings(regular_user_client):
    """Regular user can only read own pairing records"""
    # Try to query all pairings
    result = regular_user_client.table('pairings').select('*').execute()

    # Should only see own records
    user_id = decode_jwt(regular_user_client.auth.current_user.access_token)['user_id']
    assert all(r['created_by'] == user_id for r in result.data)

def test_unauthenticated_cannot_access(unauthenticated_client):
    """Unauthenticated client cannot access data"""
    with pytest.raises(Exception) as exc_info:
        unauthenticated_client.table('pairings').select('*').execute()

    assert 'permission denied' in str(exc_info.value).lower()

def test_audit_fields_populate_correctly(admin_client):
    """Test audit fields are populated on insert/update"""
    # Insert test record
    data = {
        'domicile': 'TEST',
        'aircraft': '777',
        'bid_period': '9999'
    }
    result = admin_client.table('bid_periods').insert(data).execute()

    record = result.data[0]
    assert record['created_by'] is not None
    assert record['updated_by'] is not None
    assert record['created_at'] is not None
    assert record['updated_at'] is not None

    # Update record
    updated = admin_client.table('bid_periods').update({
        'domicile': 'TEST2'
    }).eq('id', record['id']).execute()

    assert updated.data[0]['updated_at'] > record['created_at']
```

#### E2E Tests (Critical Workflows)

```python
# tests/e2e/test_auth_flow.py
from playwright.sync_api import Page, expect

def test_login_flow(page: Page):
    """Test complete login workflow"""
    page.goto('http://localhost:3000')

    # Should redirect to login
    expect(page.locator('h1')).to_contain_text('Login')

    # Fill login form
    page.fill('input[name="email"]', 'test@example.com')
    page.fill('input[name="password"]', 'test_password')
    page.click('button[type="submit"]')

    # Should redirect to app
    expect(page.locator('.auth-header')).to_contain_text('test@example.com')

def test_logout_flow(page: Page):
    """Test logout clears session"""
    # Login first
    login(page, 'test@example.com', 'test_password')

    # Click logout
    page.click('button[aria-label="Logout"]')

    # Should redirect to login
    expect(page.locator('h1')).to_contain_text('Login')

def test_protected_route_redirects_unauthenticated(page: Page):
    """Test unauthenticated user cannot access protected pages"""
    page.goto('http://localhost:3000/database-explorer')

    # Should redirect to login
    expect(page.url).to_contain('/login')
```

**Acceptance Criteria**:
- [ ] All unit tests pass
- [ ] RLS policies enforce correctly
- [ ] E2E auth flow works

---

### Phase 2: Database Explorer Testing

**Goal**: Ensure query functionality works correctly

#### Unit Tests (Query State)

```python
# tests/test_query_state.py
def test_filter_state_initialization():
    """Test filter state initializes with defaults"""
    state = QueryState()

    assert state.selected_domiciles == []
    assert state.current_page == 1
    assert state.page_size == 50

def test_pagination_computed_vars():
    """Test pagination computed vars calculate correctly"""
    state = QueryState()
    state.total_records = 127
    state.page_size = 50

    assert state.total_pages == 3
    assert len(state.paginated_results) <= 50

def test_next_page():
    """Test next page increments correctly"""
    state = QueryState()
    state.current_page = 1
    state.total_records = 100
    state.page_size = 50

    state.next_page()

    assert state.current_page == 2

def test_next_page_at_end():
    """Test next page does not exceed total pages"""
    state = QueryState()
    state.current_page = 3
    state.total_records = 100
    state.page_size = 50  # 2 pages total

    state.next_page()

    assert state.current_page == 2  # Should not increment
```

#### Integration Tests (Database Queries)

```python
# tests/integration/test_database_queries.py
def test_query_pairings_no_filters():
    """Test querying pairings with no filters returns all records"""
    state = QueryState()
    state.data_type = "Pairings"

    state.execute_query()

    assert len(state.results) > 0

def test_query_pairings_with_domicile_filter():
    """Test filtering by domicile"""
    state = QueryState()
    state.selected_domiciles = ['ONT']
    state.data_type = "Pairings"

    state.execute_query()

    assert all(r['domicile'] == 'ONT' for r in state.results)

def test_query_pairings_with_date_range():
    """Test filtering by date range"""
    state = QueryState()
    state.date_range_start = datetime(2025, 1, 1)
    state.date_range_end = datetime(2025, 12, 31)
    state.data_type = "Pairings"

    state.execute_query()

    assert all(
        datetime(2025, 1, 1) <= parse_date(r['created_at']) <= datetime(2025, 12, 31)
        for r in state.results
    )

def test_query_bid_lines_switches_table():
    """Test switching data type queries correct table"""
    state = QueryState()
    state.data_type = "Bid Lines"

    state.execute_query()

    # Verify results have bid line fields
    assert all('line_number' in r for r in state.results)
```

#### E2E Tests (User Workflows)

```python
# tests/e2e/test_database_explorer.py
def test_filter_and_query_workflow(page: Page):
    """Test complete filter and query workflow"""
    login(page, 'test@example.com', 'test_password')
    page.goto('http://localhost:3000/database-explorer')

    # Select filters
    page.select_option('select[name="domicile"]', 'ONT')
    page.select_option('select[name="aircraft"]', '757')

    # Click search
    page.click('button:has-text("Search")')

    # Verify results
    expect(page.locator('.results-table tbody tr')).to_have_count_greater_than(0)

    # Verify filter summary
    expect(page.locator('.filter-summary')).to_contain_text('2 filters active')

def test_pagination_workflow(page: Page):
    """Test pagination controls work"""
    login(page, 'test@example.com', 'test_password')
    page.goto('http://localhost:3000/database-explorer')

    # Execute query
    page.click('button:has-text("Search")')

    # Click next page
    page.click('button[aria-label="Next page"]')

    # Verify page number changed
    expect(page.locator('.page-indicator')).to_contain_text('Page 2')

def test_export_csv_workflow(page: Page):
    """Test CSV export downloads file"""
    login(page, 'test@example.com', 'test_password')
    page.goto('http://localhost:3000/database-explorer')

    # Execute query
    page.click('button:has-text("Search")')

    # Click export CSV
    with page.expect_download() as download_info:
        page.click('button:has-text("Export CSV")')

    download = download_info.value
    assert download.suggested_filename.endswith('.csv')
```

**Acceptance Criteria**:
- [ ] All unit tests pass
- [ ] Database queries return correct results
- [ ] Pagination works correctly
- [ ] CSV export generates valid file
- [ ] E2E workflows complete successfully

---

### Phase 3: EDW Analyzer Testing

**Goal**: Ensure PDF upload, parsing, and analysis work correctly

#### Unit Tests (EDW State)

```python
# tests/test_edw_state.py
def test_edw_state_initialization():
    """Test EDW state initializes correctly"""
    state = EDWState()

    assert state.uploaded_file_name == ""
    assert state.is_processing is False
    assert state.trips == []

def test_filter_trips_by_duty_day():
    """Test filtering trips by duty day length"""
    state = EDWState()
    state.trips = [
        {'trip_id': 'A1', 'max_duty_day': 10.5, 'is_edw': True},
        {'trip_id': 'A2', 'max_duty_day': 8.0, 'is_edw': False},
        {'trip_id': 'A3', 'max_duty_day': 12.0, 'is_edw': True},
    ]
    state.filter_duty_day_min = 9.0

    filtered = state.filtered_trips

    assert len(filtered) == 2
    assert all(t['max_duty_day'] >= 9.0 for t in filtered)
```

#### Integration Tests (PDF Processing)

```python
# tests/integration/test_edw_pdf_processing.py
def test_process_valid_pairing_pdf():
    """Test processing valid pairing PDF"""
    state = EDWState()

    # Load test PDF
    with open('tests/fixtures/ONT_757_Bid2507.pdf', 'rb') as f:
        pdf_data = f.read()

    # Mock file upload
    mock_file = MockUploadFile(filename='test.pdf', content=pdf_data)

    # Process PDF
    state.process_pdf([mock_file])

    # Verify results
    assert state.domicile == 'ONT'
    assert state.aircraft == '757'
    assert state.bid_period == '2507'
    assert len(state.trips) == 120  # Known number in test PDF
    assert state.edw_statistics['total_trips'] == 120

def test_process_bid_line_pdf_shows_error():
    """Test uploading bid line PDF shows error"""
    state = EDWState()

    with open('tests/fixtures/bid_line.pdf', 'rb') as f:
        pdf_data = f.read()

    mock_file = MockUploadFile(filename='bid_line.pdf', content=pdf_data)

    state.process_pdf([mock_file])

    assert 'wrong PDF type' in state.error_message.lower()

def test_process_corrupted_pdf_shows_error():
    """Test processing corrupted PDF shows error"""
    state = EDWState()
    mock_file = MockUploadFile(filename='corrupted.pdf', content=b'corrupted data')

    state.process_pdf([mock_file])

    assert state.error_message != ""
    assert state.is_processing is False
```

#### Comparison Tests (Streamlit vs Reflex)

```python
# tests/comparison/test_edw_parity.py
def test_edw_statistics_match_streamlit():
    """Test Reflex EDW statistics match Streamlit version"""

    # Process same PDF in both apps
    with open('tests/fixtures/ONT_757_Bid2507.pdf', 'rb') as f:
        pdf_data = f.read()

    # Streamlit version (using shared backend)
    from shared.edw import run_edw_report
    streamlit_results = run_edw_report(pdf_data)

    # Reflex version
    reflex_state = EDWState()
    reflex_state.process_pdf([MockUploadFile('test.pdf', pdf_data)])

    # Compare statistics
    assert reflex_state.edw_statistics == streamlit_results['statistics']
    assert len(reflex_state.trips) == len(streamlit_results['trips'])

def test_excel_export_matches_streamlit():
    """Test Reflex Excel export matches Streamlit version"""

    # Generate Excel from both apps
    streamlit_excel = generate_streamlit_excel()
    reflex_excel = generate_reflex_excel()

    # Compare sheet names
    assert streamlit_excel.sheetnames == reflex_excel.sheetnames

    # Compare data in key sheets
    for sheet_name in ['EDW Statistics', 'Trip Length Distribution']:
        streamlit_df = pd.read_excel(streamlit_excel, sheet_name=sheet_name)
        reflex_df = pd.read_excel(reflex_excel, sheet_name=sheet_name)

        pd.testing.assert_frame_equal(streamlit_df, reflex_df)
```

#### E2E Tests

```python
# tests/e2e/test_edw_workflow.py
def test_edw_complete_workflow(page: Page):
    """Test complete EDW analysis workflow"""
    login(page, 'test@example.com', 'test_password')
    page.goto('http://localhost:3000')

    # Click EDW Analyzer tab
    page.click('button:has-text("EDW Pairing Analyzer")')

    # Upload PDF
    page.set_input_files('input[type="file"]', 'tests/fixtures/ONT_757_Bid2507.pdf')

    # Wait for processing
    page.wait_for_selector('.edw-results', timeout=30000)

    # Verify header info displayed
    expect(page.locator('.header-info')).to_contain_text('ONT')
    expect(page.locator('.header-info')).to_contain_text('757')

    # Verify statistics displayed
    expect(page.locator('.statistics')).to_contain_text('Total Trips')
    expect(page.locator('.statistics')).to_contain_text('EDW Trips')

    # Apply filter
    page.fill('input[name="filter_duty_day_min"]', '10')
    page.click('button:has-text("Apply Filters")')

    # Verify filtered results
    expect(page.locator('.filter-summary')).to_contain_text('1 filter active')

    # Download Excel
    with page.expect_download() as download_info:
        page.click('button:has-text("Download Excel")')

    download = download_info.value
    assert download.suggested_filename.endswith('.xlsx')

    # Save to database
    page.click('button:has-text("Save to Database")')
    expect(page.locator('.success-message')).to_be_visible()
```

**Acceptance Criteria**:
- [ ] All unit tests pass
- [ ] PDF processing produces correct results
- [ ] Reflex output matches Streamlit (comparison tests pass)
- [ ] Excel export is valid
- [ ] E2E workflow completes successfully

---

### Phase 4: Bid Line Analyzer Testing

**Goal**: Ensure data editor, validation, and pay period analysis work correctly

#### Unit Tests (Data Editor State)

```python
# tests/test_bid_line_state.py
def test_update_cell_tracks_change():
    """Test cell edit is tracked"""
    state = BidLineState()
    state.original_data = pd.DataFrame({'Line': [1], 'CT': [85.0]})
    state.edited_data = state.original_data.copy()

    state.update_cell(row_idx=0, col_name='CT', new_value=90.0)

    assert state.edited_data.at[0, 'CT'] == 90.0
    assert len(state.edited_cells) == 1
    assert state.edited_cells[0]['old'] == 85.0
    assert state.edited_cells[0]['new'] == 90.0

def test_validation_detects_bt_greater_than_ct():
    """Test validation detects BT > CT"""
    state = BidLineState()
    state.edited_data = pd.DataFrame({
        'Line': [1],
        'CT': [85.0],
        'BT': [90.0]  # Invalid: BT > CT
    })

    state.validate_edits()

    assert len(state.validation_errors) > 0
    assert any('BT > CT' in err for err in state.validation_errors)

def test_validation_detects_do_plus_dd_exceeds_31():
    """Test validation detects DO + DD > 31"""
    state = BidLineState()
    state.edited_data = pd.DataFrame({
        'Line': [1],
        'DO': [20],
        'DD': [15]  # 20 + 15 = 35 > 31
    })

    state.validate_edits()

    assert len(state.validation_errors) > 0
    assert any('DO + DD' in err for err in state.validation_errors)

def test_reset_edits_reverts_to_original():
    """Test reset restores original data"""
    state = BidLineState()
    state.original_data = pd.DataFrame({'Line': [1], 'CT': [85.0]})
    state.edited_data = state.original_data.copy()

    # Make edit
    state.update_cell(0, 'CT', 90.0)

    # Reset
    state.reset_edits()

    assert state.edited_data.at[0, 'CT'] == 85.0
    assert len(state.edited_cells) == 0
```

#### Integration Tests (Data Editor Component)

```python
# tests/integration/test_data_editor.py
def test_data_editor_renders_dataframe():
    """Test data editor renders DataFrame correctly"""
    state = BidLineState()
    state.edited_data = pd.DataFrame({
        'Line': [1, 2],
        'CT': [85.0, 88.0],
        'BT': [80.0, 82.0]
    })

    # Render component (may require test renderer)
    component = editable_table(state)

    # Verify columns displayed
    assert 'Line' in component
    assert 'CT' in component
    assert 'BT' in component

def test_data_editor_saves_edits():
    """Test data editor saves edits to state"""
    state = BidLineState()
    state.edited_data = pd.DataFrame({'Line': [1], 'CT': [85.0]})

    # Simulate cell edit event
    state.update_cell(0, 'CT', 90.0)

    assert state.edited_data.at[0, 'CT'] == 90.0
```

#### Comparison Tests

```python
# tests/comparison/test_bid_line_parity.py
def test_bid_line_statistics_match_streamlit():
    """Test Reflex bid line statistics match Streamlit"""

    with open('tests/fixtures/bid_lines.pdf', 'rb') as f:
        pdf_data = f.read()

    # Streamlit version
    from shared.bid_parser import parse_bid_lines
    streamlit_results = parse_bid_lines(pdf_data)

    # Reflex version
    reflex_state = BidLineState()
    reflex_state.process_pdf([MockUploadFile('test.pdf', pdf_data)])

    # Compare statistics
    streamlit_stats = calculate_statistics(streamlit_results['data'])
    reflex_stats = reflex_state.statistics

    assert streamlit_stats == reflex_stats

def test_pay_period_analysis_matches_streamlit():
    """Test pay period analysis produces same results"""

    # Process same PDF in both apps
    with open('tests/fixtures/bid_lines_with_pp.pdf', 'rb') as f:
        pdf_data = f.read()

    streamlit_pp_analysis = get_streamlit_pp_analysis(pdf_data)
    reflex_pp_analysis = get_reflex_pp_analysis(pdf_data)

    # Compare pay period 1 vs 2
    assert streamlit_pp_analysis['pp1'] == reflex_pp_analysis['pp1']
    assert streamlit_pp_analysis['pp2'] == reflex_pp_analysis['pp2']
```

#### E2E Tests

```python
# tests/e2e/test_bid_line_workflow.py
def test_bid_line_complete_workflow(page: Page):
    """Test complete bid line analysis workflow"""
    login(page, 'test@example.com', 'test_password')
    page.goto('http://localhost:3000')

    # Click Bid Line Analyzer tab
    page.click('button:has-text("Bid Line Analyzer")')

    # Upload PDF
    page.set_input_files('input[type="file"]', 'tests/fixtures/bid_lines.pdf')

    # Wait for processing
    page.wait_for_selector('.bid-line-results', timeout=30000)

    # Edit a cell in data editor
    page.click('td[data-row="0"][data-col="CT"]')
    page.fill('input[name="cell-edit"]', '90.0')
    page.press('input[name="cell-edit"]', 'Enter')

    # Verify change tracked
    expect(page.locator('.change-indicator')).to_contain_text('1 change')

    # Apply filter
    page.fill('input[name="filter_ct_min"]', '80')
    page.click('button:has-text("Apply Filters")')

    # Verify filtered results
    expect(page.locator('.filter-summary')).to_contain_text('1 filter active')

    # View pay period comparison
    page.click('button:has-text("Summary")')
    expect(page.locator('.pp-comparison')).to_be_visible()

    # Download CSV
    with page.expect_download() as download_info:
        page.click('button:has-text("Download CSV")')

    download = download_info.value
    assert download.suggested_filename.endswith('.csv')

    # Verify CSV contains edited data
    csv_content = download.path().read_text()
    assert '90.0' in csv_content  # Edited CT value
```

**Acceptance Criteria**:
- [ ] All unit tests pass
- [ ] Data editor allows inline editing
- [ ] Validation rules work correctly
- [ ] Change tracking works
- [ ] Pay period analysis matches Streamlit
- [ ] CSV export includes edits
- [ ] E2E workflow completes successfully

---

## Performance Testing

### Load Testing

**Goal**: Ensure app performs acceptably under realistic load

#### Test Scenarios

1. **Single User - Large PDF**:
   - Upload 10MB PDF
   - Measure processing time
   - **Target**: ≤ 30 seconds

2. **Concurrent Users - Small PDFs**:
   - 10 users upload 1MB PDFs simultaneously
   - Measure processing time per user
   - **Target**: No degradation vs single user

3. **Database Queries - Large Result Sets**:
   - Query 10,000 pairing records
   - Measure query + render time
   - **Target**: ≤ 3 seconds

4. **Data Editor - Large DataFrames**:
   - Render DataFrame with 500 rows
   - Measure initial render time
   - Measure cell edit latency
   - **Target**: Render ≤ 2 seconds, edit ≤ 500ms

#### Load Testing Tools

```bash
# Use Locust for load testing
# locustfile.py
from locust import HttpUser, task, between

class EDWUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def upload_pdf(self):
        with open('tests/fixtures/ONT_757_Bid2507.pdf', 'rb') as f:
            self.client.post('/api/upload_edw_pdf', files={'file': f})

    @task(2)
    def query_database(self):
        self.client.post('/api/query_pairings', json={
            'domicile': 'ONT',
            'aircraft': '757'
        })

# Run load test
locust -f locustfile.py --users 10 --spawn-rate 2 --host http://localhost:3000
```

**Acceptance Criteria**:
- [ ] All performance targets met
- [ ] No memory leaks detected
- [ ] No server crashes under load

---

## Security Testing

### Authentication & Authorization

**Test Cases**:
1. [ ] Unauthenticated user cannot access protected pages
2. [ ] JWT token expires after expected duration
3. [ ] Logout clears JWT from client
4. [ ] Regular user cannot access admin features
5. [ ] SQL injection attempts are prevented
6. [ ] XSS attacks are prevented
7. [ ] CSRF protection is enabled

### Data Privacy

**Test Cases**:
1. [ ] User A cannot see User B's data (RLS enforcement)
2. [ ] JWT claims do not leak sensitive information
3. [ ] Audit logs do not expose user passwords
4. [ ] Exported files do not contain sensitive metadata

### Penetration Testing

**Tools**:
- OWASP ZAP for automated security scanning
- Manual testing with common attack vectors

---

## Continuous Integration

### CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/reflex_ci.yml
name: Reflex App CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov playwright

    - name: Run unit tests
      run: pytest tests/unit --cov=reflex_app --cov-report=xml

    - name: Run integration tests
      run: pytest tests/integration

    - name: Install Playwright browsers
      run: playwright install

    - name: Run E2E tests
      run: pytest tests/e2e

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml

    - name: Run security scan
      run: bandit -r reflex_app/

  performance:
    runs-on: ubuntu-latest
    needs: test

    steps:
    - uses: actions/checkout@v2

    - name: Run performance tests
      run: pytest tests/performance --benchmark-only
```

---

## Test Coverage Goals

| Component | Coverage Target |
|-----------|----------------|
| Backend modules (shared/) | 90% |
| State classes | 85% |
| Event handlers | 80% |
| UI components | 70% |
| E2E critical paths | 100% |

**Overall Target**: 80% code coverage

---

## Regression Testing

### Test Maintenance

- **After each phase**: Add regression test suite for completed features
- **Before major releases**: Run full regression suite
- **On bug fixes**: Add test case to prevent recurrence

### Regression Test Checklist

- [ ] All comparison tests pass (Streamlit vs Reflex parity)
- [ ] All E2E critical workflows pass
- [ ] Performance benchmarks meet targets
- [ ] Security tests pass
- [ ] No new warnings or errors in logs

---

## Test Environment

### Local Development
- Reflex app running on `localhost:3000`
- Supabase local instance or staging project
- Test fixtures in `tests/fixtures/`

### CI/CD Environment
- GitHub Actions runners
- Supabase staging project
- Playwright headless browsers

### Staging Environment
- Deployed Reflex app
- Supabase staging project
- Real user testing

---

## Success Criteria

Migration testing is successful if:
- [ ] **Functional parity**: All comparison tests pass
- [ ] **Performance**: All performance targets met
- [ ] **Security**: All security tests pass
- [ ] **Coverage**: 80%+ code coverage achieved
- [ ] **E2E**: All critical workflows pass
- [ ] **Regression**: No regressions from Streamlit version

---

## Test Documentation

### Test Reports

Generate test reports after each phase:
- Unit test results
- Integration test results
- E2E test results
- Performance benchmarks
- Coverage report

### Example Report Format

```markdown
# Phase 3 Test Report

## Summary
- **Total Tests**: 127
- **Passed**: 125
- **Failed**: 2
- **Skipped**: 0
- **Coverage**: 83%

## Failed Tests
1. `test_excel_export_matches_streamlit` - Sheet name mismatch
2. `test_pdf_processing_timeout` - Exceeded 30s limit

## Performance
- Average PDF processing: 12.3s (target: ≤30s) ✅
- Average query time: 1.8s (target: ≤3s) ✅
- Average cell edit latency: 420ms (target: ≤500ms) ✅

## Action Items
- [ ] Fix excel export sheet name
- [ ] Optimize PDF processing for large files
```

---

## Tools & Libraries

### Testing Frameworks
- **pytest**: Unit and integration testing
- **pytest-cov**: Code coverage
- **pytest-benchmark**: Performance benchmarking

### E2E Testing
- **Playwright**: Browser automation
- **playwright-pytest**: Pytest integration

### Load Testing
- **Locust**: Load and stress testing

### Security Testing
- **bandit**: Python security linter
- **OWASP ZAP**: Security scanning

### Mocking
- **pytest-mock**: Mocking Supabase calls
- **unittest.mock**: Standard library mocking

---

## Appendix: Test Data

### Test Fixtures

**Test PDFs**:
- `tests/fixtures/ONT_757_Bid2507.pdf` - Valid pairing PDF (120 trips)
- `tests/fixtures/bid_lines.pdf` - Valid bid line PDF (258 lines)
- `tests/fixtures/bid_lines_with_pp.pdf` - Bid line with pay periods
- `tests/fixtures/corrupted.pdf` - Corrupted PDF for error handling
- `tests/fixtures/large.pdf` - 10MB PDF for performance testing

**Test Users**:
- `test@example.com` / `test_password` - Regular user
- `admin@example.com` / `admin_password` - Admin user
- `giladswerdlow@gmail.com` - Production admin

**Test Database Records**:
- Seed script to populate staging database with test data
- 1000+ pairing records across multiple bid periods
- 500+ bid line records
- Various domiciles, aircraft, seats

---

## Next Steps

1. **Phase 0**: Build POCs and write initial unit tests
2. **Phase 1**: Implement auth tests (unit + integration + E2E)
3. **Phase 2**: Implement query tests (all layers)
4. **Phase 3**: Implement EDW tests (including comparison tests)
5. **Phase 4**: Implement bid line tests (focus on data editor)
6. **Phase 6**: Run full regression suite and performance tests
