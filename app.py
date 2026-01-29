import streamlit as st
import pandas as pd

# =============================================================================
# DROPDOWN OPTIONS
# =============================================================================

MAPPING_TYPES = [
    "Earning", "Reimbursement", "Tax", "Benefit", "UnionBenefit",
    "PrevailingWageBenefit", "Payroll", "PostTaxDeduction",
    "UnionPostTaxDeduction"
]

PARENT_DESCRIPTIONS = [
    "Employee Gross Earnings", "Expenses", "Tax Expenses",
    "Benefit Expenses", "Liabilities", "Tax Liabilities",
    "Miscellaneous Liabilities", "Union Miscellaneous Liabilities",
    "Post-Tax Deduction Liabilities"
]

DESCRIPTIONS = [
    "Hourly", "Overtime", "Double Overtime", "Salaried", "Paid Holiday",
    "PTO", "Sick", "Bonus", "Commission", "Severance", "Other Imputed",
    "Non-Hourly Regular", "Reimbursement Expenses",
    "Employer Social Security Tax", "Employer Medicare Tax",
    "Federal Unemployment Tax", "Ohio State Unemployment Tax",
    "Social Security Tax", "Federal Income Tax", "Medicare",
    "Employee Additional Medicare", "Ohio State Tax",
    "Payroll Clearing", "Auto Loan", "Personal",
    "Child Support and Garnishment Liabilities"
]

GL_ACCOUNTS = [
    "11000", "22200", "24300", "24400", "24600", "24700", "25000",
    "25100", "25200", "25300", "25610", "25800", "31000", "31100",
    "31200", "31400", "71000", "71100", "71200", "72000", "92400"
]

EMPLOYEE_CATEGORIES = ["1000", "31000", "31100", "71000", "71100", "71200"]

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Payroll GL Mapping Tool — Enterprise",
    page_icon="💰",
    layout="wide"
)

# =============================================================================
# PREMIUM CSS
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #020617, #1e3a8a);
    padding: 1.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
    box-shadow: 0 12px 30px rgba(2,6,23,.5);
}

/* Cards */
.card {
    background: white;
    border-radius: 14px;
    padding: 1rem;
    box-shadow: 0 6px 20px rgba(0,0,0,.08);
    margin-bottom: 1rem;
}

/* Sticky Bar */
.sticky-bar {
    position: sticky;
    top: 0;
    z-index: 99;
    background: white;
    padding: .75rem;
    border-radius: 0 0 14px 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,.08);
}

/* Badge */
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: .75rem;
    font-weight: 600;
}

/* Floating Button */
.fab {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: linear-gradient(135deg, #2563eb, #020617);
    color: white;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    font-size: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 12px 30px rgba(37,99,235,.6);
}

/* Preview Table */
.preview-table {
    background: white;
    border-radius: 14px;
    padding: 1rem;
    box-shadow: 0 6px 20px rgba(0,0,0,.08);
    margin-top: 1.5rem;
}

.preview-table th {
    background: #020617 !important;
    color: white !important;
}

/* Validation */
.missing {
    background-color: #fee2e2 !important;
    color: #991b1b;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>💰 Payroll GL Mapping Tool</h1>
    <p>Enterprise UI · Live Preview · Validation · SQL Generator</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    batch_co_id = st.number_input("Company ID", value=1380, step=1)
    batch_prod_id = st.number_input("Product ID", value=1001, step=1)

    emp_opt = EMPLOYEE_CATEGORIES + ["Other (Custom)"]
    emp_sel = st.selectbox("Employee Category", emp_opt)

    if emp_sel == "Other (Custom)":
        batch_emp_cat = st.text_input("Custom Category")
    else:
        batch_emp_cat = emp_sel

    st.info("💡 Changes here apply to all rows")

# =============================================================================
# SESSION STATE
# =============================================================================

if "rows" not in st.session_state:
    st.session_state.rows = [0]

if "next_id" not in st.session_state:
    st.session_state.next_id = 1

def add_row():
    st.session_state.rows.append(st.session_state.next_id)
    st.session_state.next_id += 1

def remove_row(rid):
    if len(st.session_state.rows) > 1:
        st.session_state.rows.remove(rid)

def field(select, custom):
    if select == "Other (Custom)":
        return custom
    return "" if select == "-- Select --" else select

# =============================================================================
# PROGRESS
# =============================================================================

st.markdown("### 📊 Form Completion")

progress_placeholder = st.empty()

# =============================================================================
# ROW INPUTS
# =============================================================================

row_data = []

for rid in st.session_state.rows:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    cols = st.columns([1,1,1.5,2,2,1,.5])

    with cols[0]:
        trans = st.selectbox("Type", ["Debit", "Credit"], key=f"t_{rid}")
        color = "#dcfce7" if trans == "Debit" else "#fee2e2"
        text = "#166534" if trans == "Debit" else "#991b1b"
        st.markdown(
            f"<span class='badge' style='background:{color};color:{text}'>"
            f"{'➕' if trans=='Debit' else '➖'} {trans}</span>",
            unsafe_allow_html=True
        )

    with cols[1]:
        acc_sel = st.selectbox("GL Account", ["-- Select --"] + GL_ACCOUNTS + ["Other (Custom)"], key=f"a_{rid}")
        acc_cust = st.text_input("Custom", key=f"ac_{rid}") if acc_sel == "Other (Custom)" else ""
        acc = field(acc_sel, acc_cust)

    with cols[2]:
        map_sel = st.selectbox("Mapping", ["-- Select --"] + MAPPING_TYPES + ["Other (Custom)"], key=f"m_{rid}")
        map_cust = st.text_input("Custom", key=f"mc_{rid}") if map_sel == "Other (Custom)" else ""
        map_type = field(map_sel, map_cust)

    with cols[3]:
        p_sel = st.selectbox("Parent Desc", ["-- Select --"] + PARENT_DESCRIPTIONS + ["Other (Custom)"], key=f"p_{rid}")
        p_cust = st.text_input("Custom", key=f"pc_{rid}") if p_sel == "Other (Custom)" else ""
        parent = field(p_sel, p_cust)

    with cols[4]:
        d_sel = st.selectbox("Description", ["-- Select --"] + DESCRIPTIONS + ["Other (Custom)"], key=f"d_{rid}")
        d_cust = st.text_input("Custom", key=f"dc_{rid}") if d_sel == "Other (Custom)" else ""
        desc = field(d_sel, d_cust)

    with cols[5]:
        contrib = st.selectbox("By", ["", "company", "employee"], key=f"c_{rid}")

    with cols[6]:
        if st.button("🗑", key=f"x_{rid}"):
            remove_row(rid)
            st.rerun()

    row_data.append({
        "Transaction Type": trans,
        "Account ID": acc,
        "Mapping Type": map_type,
        "Parent Description": parent,
        "Description": desc,
        "Contributor Type": contrib
    })

    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# DATAFRAME + PROGRESS
# =============================================================================

df = pd.DataFrame(row_data)

filled = df.replace("", pd.NA).notna().sum().sum()
total = max(df.shape[0] * df.shape[1], 1)
progress = int((filled / total) * 100)

progress_placeholder.progress(progress / 100)
progress_placeholder.markdown(f"**Completion:** {progress}%")

# =============================================================================
# LIVE PREVIEW TABLE
# =============================================================================

st.markdown("### 🧾 Live Mapping Preview")

if df.empty:
    st.info("Start adding rows to see a live preview here")
else:
    def highlight(val):
        return "background-color:#fee2e2;color:#991b1b;" if val == "" else ""

    styled = df.style.applymap(highlight)

    st.markdown("<div class='preview-table'>", unsafe_allow_html=True)
    st.dataframe(styled, use_container_width=True, height=260)
    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# STICKY BAR
# =============================================================================

st.markdown("<div class='sticky-bar'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1,1,1])
with col2:
    generate = st.button("🚀 Generate SQL Script", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# SQL GENERATION
# =============================================================================

if generate:
    valid = df[df["Account ID"].str.strip() != ""]

    if valid.empty:
        st.error("⚠️ At least one row must contain a GL Account ID")
    else:
        def fmt(v):
            if not v:
                return "NULL"
            return "'" + str(v).replace("'", "''") + "'"

        values = []
        for _, r in valid.iterrows():
            values.append(
                f"({int(batch_co_id)}, {int(batch_prod_id)}, {fmt(r['Transaction Type'])}, "
                f"{fmt(batch_emp_cat)}, {fmt(r['Account ID'])}, {fmt(r['Mapping Type'])}, "
                f"{fmt(r['Parent Description'])}, {fmt(r['Description'])}, "
                f"{fmt(r['Contributor Type'])})"
            )

        sql = "WITH cte_gl_mapping AS (VALUES\n  " + ",\n  ".join(values) + "\n)\n"
        sql += """INSERT INTO prl_chart_of_account_mapping (
    internal_id, company_id, product_id, journal_entry_transaction_type,
    coa_mapping_type, employee_category, chart_of_account_id,
    parent_description, description, contributor_type,
    created_by_user_id, modified_by_user_id
)
SELECT
    gen_random_uuid(), company_id, product_id, transaction_type,
    coa_mapping_type, employee_category,
    (SELECT id FROM prl_chart_of_account
     WHERE company_id = data.company_id
     AND account_id = data.account_id),
    parent_description, description, contributor_type, 1, 1
FROM cte_gl_mapping AS data(
    company_id, product_id, transaction_type, employee_category,
    account_id, coa_mapping_type, parent_description,
    description, contributor_type
)
ON CONFLICT (
    company_id, product_id, coa_mapping_type, employee_category,
    COALESCE(contributor_type, ''),
    COALESCE(parent_description, ''),
    description
)
DO UPDATE SET
    chart_of_account_id = EXCLUDED.chart_of_account_id,
    modified_by_user_id = 1;
"""

        st.success(f"✅ Generated SQL for {len(valid)} row(s)")

        st.markdown(f"""
<div style="
background:#020617;
color:#e5e7eb;
padding:1.5rem;
border-radius:14px;
font-family:monospace;
max-height:400px;
overflow:auto;
">
<pre>{sql.replace("<","&lt;").replace(">","&gt;")}</pre>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# FLOATING ADD BUTTON
# =============================================================================

st.markdown("<div class='fab'>➕</div>", unsafe_allow_html=True)
if st.button("Add Row"):
    add_row()
    st.rerun()
