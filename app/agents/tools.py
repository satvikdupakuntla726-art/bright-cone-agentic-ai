from crewai.tools import tool

@tool("Reset Password Tool")
def reset_password_tool(user_id: str) -> str:
    """Send a password reset link to the customer. This is a SAFE action. Input should be user_id."""
    return f"ACTION_PERFORMED: Password reset link successfully sent to {user_id}."

@tool("Fetch Invoice Tool")
def fetch_invoice_tool(user_id: str) -> str:
    """Retrieve a customer's recent invoice details. This is a SAFE action. Input should be user_id."""
    return f"ACTION_PERFORMED: Invoice details fetched for {user_id}."

@tool("Issue Refund Tool")
def issue_refund_tool(user_id: str) -> str:
    """Issue a financial refund. HIGH RISK ACTION."""
    return "BLOCKED: Direct refunds cannot be executed by AI. You must set escalation_status to 'Escalated' and abort action."

@tool("Get Customer Details")
def get_customer(user_id: str) -> str:
    """Retrieve customer tier and account details."""
    return f"Customer {user_id}: Tier=Enterprise, Account Status=Active, Support Level=Tier-2."

@tool("Get Billing History")
def get_billing_history(user_id: str) -> str:
    """Fetch customer's last settled billing and charges."""
    return "Transaction #TX-9042 settled for $49.00 on 01-Sep-2026 via Card-ending-4122."

@tool("Request Refund")
def request_refund(transaction_id: str) -> str:
    """Attempt automated customer refund (Intercepted by Safety Guardrails)."""
    # Guardrail Trigger: All financial deductions strictly require human level-2 review
    return "BLOCKED: HUMAN APPROVAL REQUIRED. Automated financial refund rejected by guardrail."