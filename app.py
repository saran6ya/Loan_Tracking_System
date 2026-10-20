
import streamlit as st
import pandas as pd
import calendar
from datetime import date
from database import get_connection


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SKM Financial Services",
    page_icon="💰",
    layout="wide"
)

st.title("💰 SKM Financial Services")
st.caption("Loan Tracking and Payment Management System")


# --------------------------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------------------------

def add_months(start_date, months):
    """Add months to a date, handling month-end dates safely."""
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1

    day = min(
        start_date.day,
        calendar.monthrange(year, month)[1]
    )

    return date(year, month, day)


def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate the monthly EMI using the reducing-balance formula."""
    principal = float(principal)
    annual_rate = float(annual_rate)
    tenure_months = int(tenure_months)

    if principal <= 0 or tenure_months <= 0:
        return 0.0

    monthly_rate = annual_rate / 1200

    if monthly_rate == 0:
        return round(principal / tenure_months, 2)

    factor = (1 + monthly_rate) ** tenure_months

    emi = (
        principal
        * monthly_rate
        * factor
        / (factor - 1)
    )

    return round(emi, 2)


def calculate_outstanding_balance(
    principal,
    annual_rate,
    emi,
    completed_emi_count
):
    """
    Estimate outstanding principal after full EMI payments.

    Assumptions:
    - Each completed payment record represents one full EMI.
    - Payments are made monthly.
    - Interest is calculated on the remaining principal.
    - Partial and extra payments are not handled by this estimate.
    """

    balance = float(principal)
    annual_rate = float(annual_rate)
    emi = float(emi)
    completed_emi_count = int(completed_emi_count)

    if balance <= 0:
        return 0.0

    if completed_emi_count <= 0:
        return round(balance, 2)

    monthly_rate = annual_rate / 1200

    for _ in range(completed_emi_count):

        if balance <= 0:
            return 0.0

        interest = balance * monthly_rate
        principal_paid = emi - interest

        # EMI must cover the monthly interest.
        if principal_paid <= 0:
            return round(balance, 2)

        balance -= principal_paid

    return round(max(0.0, balance), 2)


def format_inr(amount):
    """Format a number as Indian rupees."""
    return f"₹{float(amount):,.2f}"


# --------------------------------------------------
# 3. SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose a page",
    [
        "Dashboard",
        "Customers",
        "Loans",
        "Payments",
        "Reports"
    ]
)


# ==================================================
# 4. DASHBOARD
# ==================================================

if page == "Dashboard":

    st.header("📊 Dashboard")

    conn = get_connection()

    if conn is None:
        st.error("Unable to connect to the database.")
        st.stop()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM customers"
        )
        total_customers = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM loans"
        )
        total_loans = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM payments"
        )
        total_payments = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COALESCE(SUM(loan_amount), 0) FROM loans"
        )
        total_loan_amount = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(amount_paid), 0)
            FROM payments
            WHERE payment_status = 'Completed'
        """)
        total_completed_payments = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM loans
            WHERE status = 'Active'
        """)
        active_loans = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM loans
            WHERE status = 'Closed'
        """)
        closed_loans = cursor.fetchone()[0]

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Customers", total_customers)
        col2.metric("Total Loans", total_loans)
        col3.metric("Total Payment Records", total_payments)

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Total Loan Amount",
            format_inr(total_loan_amount)
        )

        col5.metric(
            "Completed Payments",
            format_inr(total_completed_payments)
        )

        col6.metric("Active Loans", active_loans)

        st.divider()

        st.subheader("Loan Overview")

        col7, col8 = st.columns(2)

        col7.metric("Closed Loans", closed_loans)

        col8.metric(
            "Pending Payment Records",
            max(0, total_payments)
        )

        st.info(
            "Outstanding balances are calculated in the Reports "
            "section using the completed-EMI estimate."
        )

    except Exception as e:
        st.error(f"Dashboard error: {e}")

    finally:
        conn.close()


# ==================================================
# 5. CUSTOMERS
# ==================================================

elif page == "Customers":

    st.header("👥 Customer Management")

    st.subheader("Add New Customer")

    with st.form("customer_form"):

        customer_name = st.text_input("Customer Name")

        date_of_birth = st.date_input(
            "Date of Birth",
            value=date(2000, 1, 1),
            max_value=date.today()
        )

        income = st.number_input(
            "Monthly Income (₹)",
            min_value=0.0,
            step=1000.0
        )

        profession = st.text_input("Profession")

        contact_number = st.text_input("Contact Number")

        email = st.text_input("Email Address")

        address = st.text_area("Address")

        submit_customer = st.form_submit_button(
            "Add Customer"
        )

        if submit_customer:

            if not customer_name.strip():
                st.error("Please enter the customer name.")

            elif not contact_number.strip():
                st.error("Please enter the contact number.")

            else:
                conn = get_connection()

                if conn is None:
                    st.error("Unable to connect to the database.")

                else:
                    try:
                        cursor = conn.cursor()

                        cursor.execute("""
                            INSERT INTO customers
                            (
                                customer_name,
                                date_of_birth,
                                income,
                                profession,
                                contact_number,
                                Email,
                                address,
                                registration_date,
                                status
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s,
                                    %s, %s)
                        """, (
                            customer_name.strip(),
                            date_of_birth,
                            income,
                            profession.strip(),
                            contact_number.strip(),
                            email.strip(),
                            address.strip(),
                            date.today(),
                            "Active"
                        ))

                        conn.commit()

                        st.success(
                            "Customer added successfully!"
                        )

                    except Exception as e:
                        conn.rollback()
                        st.error(f"Unable to add customer: {e}")

                    finally:
                        conn.close()

    st.divider()

    st.subheader("Customer List")

    conn = get_connection()

    if conn is not None:
        try:
            customers_df = pd.read_sql(
                "SELECT * FROM customers ORDER BY customer_id",
                conn
            )

            st.dataframe(
                customers_df,
                use_container_width=True,
                hide_index=True
            )

        except Exception as e:
            st.error(f"Unable to load customers: {e}")

        finally:
            conn.close()


# ==================================================
# 6. LOANS
# ==================================================

elif page == "Loans":

    st.header("💳 Loan Management")

    conn = get_connection()

    if conn is None:
        st.error("Unable to connect to the database.")
        st.stop()

    try:
        customers_df = pd.read_sql("""
            SELECT customer_id, customer_name
            FROM customers
            WHERE status = 'Active'
            ORDER BY customer_name
        """, conn)

    except Exception as e:
        st.error(f"Unable to load customers: {e}")
        customers_df = pd.DataFrame()

    finally:
        conn.close()

    if customers_df.empty:

        st.warning(
            "No active customers found. Add a customer first."
        )

    else:

        customer_options = {
            f"{row['customer_name']} (ID: {row['customer_id']})":
            int(row["customer_id"])
            for _, row in customers_df.iterrows()
        }

        with st.form("loan_form"):

            selected_customer = st.selectbox(
                "Select Customer",
                list(customer_options.keys())
            )

            loan_amount = st.number_input(
                "Loan Amount (₹)",
                min_value=1.0,
                value=100000.0,
                step=1000.0
            )

            interest_rate = st.number_input(
                "Annual Interest Rate (%)",
                min_value=0.0,
                value=10.0,
                step=0.5
            )

            loan_tenure = st.number_input(
                "Loan Tenure (Months)",
                min_value=1,
                max_value=600,
                value=12,
                step=1
            )

            start_date = st.date_input(
                "Loan Start Date",
                value=date.today()
            )

            emi = calculate_emi(
                loan_amount,
                interest_rate,
                loan_tenure
            )

            end_date = add_months(
                start_date,
                int(loan_tenure)
            )

            st.info(
                f"**Estimated Monthly EMI:** {format_inr(emi)}"
            )

            st.write(f"Loan End Date: {end_date}")

            submit_loan = st.form_submit_button(
                "Add Loan"
            )

            if submit_loan:

                customer_id = customer_options[
                    selected_customer
                ]

                conn = get_connection()

                if conn is None:
                    st.error(
                        "Unable to connect to the database."
                    )

                else:
                    try:
                        cursor = conn.cursor()

                        cursor.execute("""
                            INSERT INTO loans
                            (
                                customer_id,
                                loan_amount,
                                interest_rate,
                                loan_tenure,
                                start_date,
                                end_date,
                                emi,
                                status
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            customer_id,
                            loan_amount,
                            interest_rate,
                            int(loan_tenure),
                            start_date,
                            end_date,
                            emi,
                            "Active"
                        ))

                        conn.commit()

                        st.success(
                            "Loan added successfully!"
                        )

                    except Exception as e:
                        conn.rollback()
                        st.error(f"Unable to add loan: {e}")

                    finally:
                        conn.close()

    st.divider()

    st.subheader("Loan Records")

    conn = get_connection()

    if conn is not None:
        try:
            loans_df = pd.read_sql("""
                SELECT
                    l.loan_id,
                    c.customer_name,
                    l.loan_amount,
                    l.interest_rate,
                    l.loan_tenure,
                    l.start_date,
                    l.end_date,
                    l.emi,
                    l.status
                FROM loans l
                JOIN customers c
                    ON l.customer_id = c.customer_id
                ORDER BY l.loan_id
            """, conn)

            st.dataframe(
                loans_df,
                use_container_width=True,
                hide_index=True
            )

        except Exception as e:
            st.error(f"Unable to load loans: {e}")

        finally:
            conn.close()


# ==================================================
# 7. PAYMENTS
# ==================================================


elif page == "Payments":

    st.header("💵 Payment Management")

    conn = get_connection()

    if conn is None:
        st.error("Unable to connect to the database.")
        st.stop()

    try:
        loans_df = pd.read_sql("""
            SELECT
                l.loan_id,
                c.customer_name,
                l.emi,
                l.loan_tenure,
                l.start_date,
                l.status
            FROM loans l
            JOIN customers c
                ON l.customer_id = c.customer_id
            WHERE l.status = 'Active'
            ORDER BY l.loan_id
        """, conn)

    except Exception as e:
        st.error(f"Unable to load active loans: {e}")
        loans_df = pd.DataFrame()

    finally:
        conn.close()

    if loans_df.empty:

        st.warning(
            "No active loans found. Add an active loan first."
        )

    else:

        loan_options = {
            (
                f"Loan ID: {int(row['loan_id'])} | "
                f"{row['customer_name']} | "
                f"EMI: {format_inr(row['emi'])}"
            ): int(row["loan_id"])
            for _, row in loans_df.iterrows()
        }

        with st.form("payment_form"):

            selected_loan = st.selectbox(
                "Select Loan",
                list(loan_options.keys())
            )

            loan_id = loan_options[selected_loan]

            selected_loan_row = loans_df[
                loans_df["loan_id"] == loan_id
            ].iloc[0]

            emi = round(float(selected_loan_row["emi"]), 2)
            tenure = int(selected_loan_row["loan_tenure"])

            installment_number = st.number_input(
                "Installment Number",
                min_value=1,
                max_value=tenure,
                value=1,
                step=1
            )

            payment_date = st.date_input(
                "Payment Date",
                value=date.today()
            )

            amount_paid = st.number_input(
                "Amount Paid (₹)",
                min_value=0.01,
                value=emi,
                step=100.0,
                format="%.2f"
            )

            payment_method = st.selectbox(
                "Payment Method",
                [
                    "Cash",
                    "UPI",
                    "Bank Transfer",
                    "Cheque",
                    "Other"
                ]
            )

            payment_status = st.selectbox(
                "Payment Status",
                ["Completed", "Pending"]
            )

            submit_payment = st.form_submit_button(
                "Record Payment"
            )

        if submit_payment:

            conn = get_connection()

            if conn is None:
                st.error("Unable to connect to the database.")

            else:
                try:
                    cursor = conn.cursor()

                    # Check how much has already been paid
                    # toward this installment.
                    cursor.execute("""
                        SELECT
                            COALESCE(SUM(amount_paid), 0)
                        FROM payments
                        WHERE loan_id = %s
                          AND installment_number = %s
                          AND payment_status = 'Completed'
                    """, (
                        loan_id,
                        int(installment_number)
                    ))

                    already_paid = float(cursor.fetchone()[0])

                    remaining_amount = round(
                        max(0.0, emi - already_paid),
                        2
                    )

                    # Stop duplicate or excessive payments.
                    if remaining_amount <= 0.009:

                        st.error(
                            "This installment is already fully paid. "
                            "Please select another installment."
                        )

                    elif amount_paid > remaining_amount + 0.001:

                        st.error(
                            "Payment exceeds the remaining amount "
                            f"for this installment. Remaining: "
                            f"{format_inr(remaining_amount)}"
                        )

                    else:

                        # Avoid creating multiple unresolved
                        # Pending records for one installment.
                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM payments
                            WHERE loan_id = %s
                              AND installment_number = %s
                              AND payment_status = 'Pending'
                        """, (
                            loan_id,
                            int(installment_number)
                        ))

                        pending_count = cursor.fetchone()[0]

                        if pending_count > 0:

                            st.error(
                                "A Pending payment already exists "
                                "for this installment. Review it "
                                "before adding another payment."
                            )

                        else:

                            cursor.execute("""
                                INSERT INTO payments
                                (
                                    loan_id,
                                    installment_number,
                                    payment_date,
                                    amount_paid,
                                    payment_method,
                                    payment_status
                                )
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                loan_id,
                                int(installment_number),
                                payment_date,
                                round(float(amount_paid), 2),
                                payment_method,
                                payment_status
                            ))

                            conn.commit()

                            st.success(
                                "Payment record added successfully!"
                            )

                            if payment_status == "Completed":

                                total_paid_for_installment = round(
                                    already_paid + float(amount_paid),
                                    2
                                )

                                remaining_after_payment = round(
                                    max(
                                        0.0,
                                        emi - total_paid_for_installment
                                    ),
                                    2
                                )

                                st.write(
                                    "Total completed payments for "
                                    "this installment:",
                                    format_inr(
                                        total_paid_for_installment
                                    )
                                )

                                st.write(
                                    "Remaining amount for this installment:",
                                    format_inr(
                                        remaining_after_payment
                                    )
                                )

                                if remaining_after_payment <= 0.009:
                                    st.success(
                                        "This installment is fully paid."
                                    )
                                else:
                                    st.info(
                                        "This installment is partially paid. "
                                        "Record the remaining amount using "
                                        "the same installment number."
                                    )

                except Exception as e:
                    conn.rollback()
                    st.error(f"Unable to record payment: {e}")

                finally:
                    conn.close()

    st.divider()

    st.subheader("Payment History")

    conn = get_connection()

    if conn is not None:
        try:
            payments_df = pd.read_sql("""
                SELECT
                    p.payment_id,
                    p.loan_id,
                    p.installment_number,
                    c.customer_name,
                    p.payment_date,
                    p.amount_paid,
                    p.payment_method,
                    p.payment_status
                FROM payments p
                JOIN loans l
                    ON p.loan_id = l.loan_id
                JOIN customers c
                    ON l.customer_id = c.customer_id
                ORDER BY
                    p.payment_date DESC,
                    p.payment_id DESC
            """, conn)

            st.dataframe(
                payments_df,
                use_container_width=True,
                hide_index=True
            )

        except Exception as e:
            st.error(f"Unable to load payment history: {e}")

        finally:
            conn.close()



# ==================================================
# 8. REPORTS
# ==================================================

elif page == "Reports":

    st.header("📈 Reports and Analytics")

    conn = get_connection()

    if conn is None:
        st.error("Unable to connect to the database.")
        st.stop()

    try:
        # ------------------------------------------
        # 1. Fetch overall summary information
        # ------------------------------------------

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM loans")
        total_loans = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(loan_amount), 0)
            FROM loans
        """)
        total_loan_amount = float(cursor.fetchone()[0] or 0)

        cursor.execute("""
            SELECT COALESCE(SUM(amount_paid), 0)
            FROM payments
            WHERE payment_status IN ('Completed', 'Paid')
        """)
        total_paid = float(cursor.fetchone()[0] or 0)

        cursor.execute("""
            SELECT COUNT(*)
            FROM loans
            WHERE status = 'Active'
        """)
        active_loans = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM loans
            WHERE status = 'Closed'
        """)
        closed_loans = cursor.fetchone()[0]

        cursor.close()

        # ------------------------------------------
        # 2. Display summary metrics
        # ------------------------------------------

        st.subheader("Overall Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Customers", total_customers)
        col2.metric("Total Loans", total_loans)
        col3.metric("Active Loans", active_loans)

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Total Loan Amount",
            format_inr(total_loan_amount)
        )

        col5.metric(
            "Total Payments Received",
            format_inr(total_paid)
        )

        col6.metric("Closed Loans", closed_loans)

        # ------------------------------------------
        # 3. Fetch individual loan details
        # ------------------------------------------

        loan_details = pd.read_sql("""
            SELECT
                l.loan_id,
                l.customer_id,
                c.customer_name,
                l.loan_amount,
                l.interest_rate,
                l.loan_tenure,
                l.emi,
                l.status,

                COALESCE((
                    SELECT SUM(p.amount_paid)
                    FROM payments p
                    WHERE p.loan_id = l.loan_id
                      AND p.payment_status IN ('Completed', 'Paid')
                ), 0) AS total_paid

            FROM loans l

            JOIN customers c
                ON l.customer_id = c.customer_id

            ORDER BY l.loan_id
        """, conn)

        # ------------------------------------------
        # 4. Fetch payments grouped by instalment
        # ------------------------------------------

        installment_payments = pd.read_sql("""
            SELECT
                loan_id,
                installment_number,
                SUM(amount_paid) AS installment_paid

            FROM payments

            WHERE payment_status IN ('Completed', 'Paid')
              AND installment_number IS NOT NULL

            GROUP BY loan_id, installment_number

            ORDER BY loan_id, installment_number
        """, conn)

        # ------------------------------------------
        # 5. Calculate fully paid instalments
        #    and estimated outstanding principal
        # ------------------------------------------

        report_rows = []

        for _, loan in loan_details.iterrows():

            loan_id = int(loan["loan_id"])
            principal = float(loan["loan_amount"] or 0)
            annual_rate = float(loan["interest_rate"] or 0)
            emi = float(loan["emi"] or 0)
            tenure = int(loan["loan_tenure"] or 0)
            total_loan_paid = float(loan["total_paid"] or 0)

            loan_installments = installment_payments[
                installment_payments["loan_id"] == loan_id
            ]

            fully_paid_count = 0

            for installment_no in range(1, tenure + 1):

                installment_rows = loan_installments[
                    loan_installments["installment_number"]
                    == installment_no
                ]

                installment_paid = float(
                    installment_rows["installment_paid"].sum()
                )

                if emi > 0 and installment_paid >= emi - 0.01:
                    fully_paid_count += 1

            # Estimate remaining principal based on fully paid EMIs.
            estimated_outstanding = calculate_outstanding_balance(
                principal=principal,
                annual_rate=annual_rate,
                emi=emi,
                completed_emi_count=fully_paid_count
            )

            report_rows.append({
                "loan_id": loan_id,
                "customer_id": int(loan["customer_id"]),
                "customer_name": loan["customer_name"],
                "loan_amount": principal,
                "interest_rate": annual_rate,
                "loan_tenure": tenure,
                "emi": emi,
                "fully_paid_installments": fully_paid_count,
                "total_paid": total_loan_paid,
                "estimated_outstanding": estimated_outstanding,
                "status": loan["status"]
            })

        report_df = pd.DataFrame(report_rows)

        # ------------------------------------------
        # 6. Display total estimated outstanding
        # ------------------------------------------

        total_estimated_outstanding = (
            report_df["estimated_outstanding"].sum()
            if not report_df.empty
            else 0.0
        )

        st.metric(
            "Estimated Outstanding Principal",
            format_inr(total_estimated_outstanding)
        )

        st.caption(
            "Outstanding principal is an estimate based on fully paid "
            "instalments. Partial payments are included in total received "
            "but do not reduce this estimate until an entire instalment "
            "is paid. Payments without an instalment number cannot be "
            "assigned to a specific instalment."
        )

        st.divider()

        # ------------------------------------------
        # 7. Customer Loan Report
        # ------------------------------------------

        st.subheader("Customer Loan Report")

        customers_report = pd.read_sql("""
            SELECT
                customer_id,
                customer_name,
                contact_number,
                status
            FROM customers
            ORDER BY customer_id
        """, conn)

        customer_report_rows = []

        for _, customer in customers_report.iterrows():

            customer_loans = report_df[
                report_df["customer_id"] == int(customer["customer_id"])
            ]

            customer_report_rows.append({
                "Customer ID": int(customer["customer_id"]),
                "Customer Name": customer["customer_name"],
                "Contact Number": customer["contact_number"],
                "Number of Loans": len(customer_loans),
                "Total Loan Amount": customer_loans[
                    "loan_amount"
                ].sum(),
                "Total Payments Received": customer_loans[
                    "total_paid"
                ].sum(),
                "Estimated Outstanding Principal": customer_loans[
                    "estimated_outstanding"
                ].sum(),
                "Customer Status": customer["status"]
            })

        customer_report_df = pd.DataFrame(customer_report_rows)

        st.dataframe(
            customer_report_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Loan Amount": st.column_config.NumberColumn(
                    format="₹%.2f"
                ),
                "Total Payments Received": st.column_config.NumberColumn(
                    format="₹%.2f"
                ),
                "Estimated Outstanding Principal":
                    st.column_config.NumberColumn(format="₹%.2f")
            }
        )

        st.divider()

        # ------------------------------------------
        # 8. Individual Loan Report
        # ------------------------------------------

        st.subheader("Individual Loan Report")

        if report_df.empty:

            st.info("No loan records are available yet.")

        else:

            individual_report = report_df[[
                "loan_id",
                "customer_name",
                "loan_amount",
                "interest_rate",
                "loan_tenure",
                "emi",
                "fully_paid_installments",
                "total_paid",
                "estimated_outstanding",
                "status"
            ]].copy()

            individual_report.columns = [
                "Loan ID",
                "Customer Name",
                "Original Loan Amount",
                "Annual Interest (%)",
                "Tenure (Months)",
                "Monthly EMI",
                "Fully Paid Instalments",
                "Total Payments Received",
                "Estimated Outstanding Principal",
                "Loan Status"
            ]

            st.dataframe(
                individual_report,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Original Loan Amount":
                        st.column_config.NumberColumn(format="₹%.2f"),
                    "Monthly EMI":
                        st.column_config.NumberColumn(format="₹%.2f"),
                    "Total Payments Received":
                        st.column_config.NumberColumn(format="₹%.2f"),
                    "Estimated Outstanding Principal":
                        st.column_config.NumberColumn(format="₹%.2f")
                }
            )

            # --------------------------------------
            # 9. Download report as CSV
            # --------------------------------------

            csv_data = individual_report.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="Download Individual Loan Report (CSV)",
                data=csv_data,
                file_name="individual_loan_report.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Reports error: {e}")

    finally:
        conn.close()
