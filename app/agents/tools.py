from langchain.tools import Tool, tool

reset_password_tool = Tool(
    name="Reset Password Tool",
    func=lambda user_id: f"ACTION_PERFORMED: Password reset link successfully sent to {user_id}.",
    description="Use this tool to send a password reset link to the customer. This is a SAFE action. Input should be user_id."
)

fetch_invoice_tool = Tool(
    name="Fetch Invoice Tool",
    func=lambda user_id: f"ACTION_PERFORMED: Invoice details fetched for {user_id}.",
    description="Use this tool to retrieve a customer's recent invoice details. This is a SAFE action. Input should be user_id."
)

issue_refund_tool = Tool(
    name="Issue Refund Tool",
    func=lambda args: "BLOCKED: Direct refunds cannot be executed by AI. You must set escalation_status to 'Escalated' and abort action.",
    description="Use this tool to issue a financial refund. HIGH RISK ACTION. Input should be user_id."
)



@tool
def get_customer(user_id: str) -> str:
    """Retrieve customer tier and account details."""
    return f"Customer {user_id}: Tier=Enterprise, Account Status=Active, Support Level=Tier-2."

@tool
def get_billing_history(user_id: str) -> str:
    """Fetch customer's last settled billing and charges."""
    return "Transaction #TX-9042 settled for $49.00 on 01-Sep-2026 via Card-ending-4122."

@tool
def request_refund(transaction_id: str) -> str:
    """Attempt automated customer refund (Intercepted by Safety Guardrails)."""
    # Guardrail Trigger: All financial deductions strictly require human level-2 review
    return "BLOCKED: HUMAN APPROVAL REQUIRED. Automated financial refund rejected by guardrail."