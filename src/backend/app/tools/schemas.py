from __future__ import annotations

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated, Any


# =========================================================
# =                     Shared Enum                       =
# =========================================================

class EmailCategory(str, Enum):
    SPAM = "Spam"
    SCHOOL = "School"
    FINANCE = "Finance"
    CAREER = "Career"
    PERSONAL = "Personal"

class EmailPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class EmailStatus(str, Enum):
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

class BulkAction(str, Enum):
    DELETE = "Delete"
    MARK_READ = "mark_read"
    MARK_UNMARKED = "mark_unread"
    APPLY_LABEL = "apply_label"
    REMOVE_LABEL = "remove_label"


# =========================================================
# =               Shared Output Primitives                =
# =========================================================

class EmailSummary(BaseModel):
    """Lightweight email representation
    - Dùng trong list result, không kéo full body email
    """
    id: str
    thread_id: str
    sender: str
    subject: str
    recipient: list[str]
    date: datetime
    snippet: str        # Xem trước 200 từ
    is_read: bool
    labels: list[str] = []
    category: EmailCategory | None = None
    priority: EmailPriority | None = None
    status: EmailStatus | None = None

class EmailDetail(BaseModel):
    """Full Email
    - Dùng khi agent cần đọc nội dung để summarize hoặc reply
    """
    body_text: str
    body_html: str | None = None
    attachments: list[str] = []
    cc: list[str] = []
    bcc: list[str] = []

class ToolResult(BaseModel):
    """Base wrapper cho mọi tool output
    - Giúp tool_node serialize nhất quán
    """
    success: bool
    message: str = ""   # Human-readable summary cho LLM evaluate
    data: Any = None    # Payload thật



# =========================================================
# =                   READ tools I/O                      =
# =========================================================

class SearchEmailsInput(BaseModel):
    """Input for search_emails tool
    LLM điền các field này dựa vào user request
    """
    query: Annotated[str, Field(
        description="Natural language or Gmail search syntax query. "
                    "Examples: 'emails from boss this week', 'from:hr@company.com subject:offer'"
    )] = ""

    category: Annotated[EmailCategory | None, Field(
        description="Filter by auto-classified category. "
                    "Use when user mentions 'spam', 'school emails', 'finance', etc.",
    )] = None

    is_read: Annotated[bool | None, Field(
        description="True = read only, False = unread only, None = both.",
    )] = None

    limit: Annotated[int, Field(
        ge=1, le=50,
        description="Max number of emails to return. Default 10. "
                    "Use higher values for bulk operations.",
    )] = 10

    date_from: Annotated[datetime | None, Field(
        description="Start date filter (inclusive). ISO 8601 format.",
    )] = None

    date_to: Annotated[datetime | None, Field(
        description="End date filter (inclusive). ISO 8601 format.",
    )] = None

    @model_validator(mode="after")
    def validate_date_range(self) -> SearchEmailsInput:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be before date_to")
        return self


class SearchEmailsOutput(ToolResult):
    data: list[EmailSummary] = []
    total_found: int = 0


class GetEmailInput(BaseModel):
    email_id: Annotated[str, Field(
        description="Gmail message ID or Outlook message ID. "
                    "Get this from search_emails results.",
    )]


class GetEmailOutput(ToolResult):
    data: EmailDetail | None = None


class SummarizeEmailInput(BaseModel):
    email_id: Annotated[str, Field(
        description="ID of the email to summarize.",
    )]

    focus: Annotated[str, Field(
        description="What to focus on in the summary. "
                    "Examples: 'action items', 'deadlines', 'key decisions', 'tone and intent'",
    )] = "key points and action items"


class SummarizeEmailOutput(ToolResult):
    data: str | None = None   # The summary text


class ListLabelsInput(BaseModel):
    """No required params — trả về toàn bộ labels của user's mailbox."""
    pass


class ListLabelsOutput(ToolResult):
    data: list[str] = []



# =========================================================
# =                   WRITE tools I/O                     =
# =========================================================

class DraftEmailInput(BaseModel):
    """
    Tạo email draft — lưu vào Drafts folder, chưa gửi.
    Dùng cho: (1) email mới hoàn toàn, (2) draft reply để review trước khi send.
    Để send ngay lập tức, dùng send_email hoặc reply_email thay thế.
    """

    # ── Context: new mail hay reply/forward? ──────────────────────────────────
    # Ba trường này xác định "loại" draft. Agent phải điền đúng case.

    reply_to_id: Annotated[str | None, Field(
        description="Email ID being replied to. When set, 'to' field is optional — "
                    "recipients are inherited from the original thread. "
                    "Set reply_all=True to include all original recipients in To/Cc.",
    )] = None

    reply_all: Annotated[bool, Field(
        description="Only relevant when reply_to_id is set. "
                    "True = reply to all original recipients (To + Cc). "
                    "False = reply to sender only.",
    )] = False

    forward_from_id: Annotated[str | None, Field(
        description="Email ID being forwarded. When set, original email body is "
                    "quoted and attachments are included automatically. "
                    "Mutually exclusive with reply_to_id.",
    )] = None

    # ── Recipients ────────────────────────────────────────────────────────────

    to: Annotated[list[str], Field(
        description="Primary recipient email addresses. "
                    "REQUIRED for new emails. "
                    "OPTIONAL when reply_to_id is set — leave empty to use original sender. "
                    "Use when adding extra recipients beyond the original thread.",
    )] = []

    cc: Annotated[list[str], Field(
        description="Carbon copy recipients — receive the email but are not the primary audience. "
                    "Use when someone needs to be kept in the loop (e.g., a manager, a team). "
                    "LLM should infer from context: 'keep my manager in the loop' → add manager to cc.",
    )] = []

    bcc: Annotated[list[str], Field(
        description="Blind carbon copy — recipients hidden from each other and from To/Cc recipients. "
                    "Use for: mass emails, privacy-sensitive sends, or when user explicitly requests bcc.",
    )] = []

    # ── Content ───────────────────────────────────────────────────────────────

    subject: Annotated[str, Field(
        description="Email subject line. "
                    "REQUIRED for new emails. "
                    "OPTIONAL when reply_to_id or forward_from_id is set — "
                    "defaults to 'Re: <original subject>' or 'Fwd: <original subject>'.",
    )] = ""

    instructions: Annotated[str, Field(
        description="What the email should say. Bullet points, rough notes, or full prose. "
                    "Agent expands and polishes this into the final body.",
        min_length=1,
    )]

    tone: Annotated[str, Field(
        description="Desired tone: 'formal', 'casual', 'assertive', 'empathetic'. "
                    "Infer from context if not stated — academic/work context defaults to 'formal'.",
    )] = "formal"

    language: Annotated[str, Field(
        description="Language for the email body. 'vi' for Vietnamese, 'en' for English. "
                    "Infer from the language the user is writing in.",
    )] = "en"

    attachment_filenames: Annotated[list[str], Field(
        description="Filenames the user mentioned attaching. "
                    "Actual file content is resolved by email_service. "
                    "Example: ['Q3_report.pdf', 'invoice_oct.xlsx']",
    )] = []

    # ── Validators ────────────────────────────────────────────────────────────

    @model_validator(mode="after")
    def validate_draft_context(self) -> DraftEmailInput:
        is_reply = self.reply_to_id is not None
        is_forward = self.forward_from_id is not None

        # Mutually exclusive
        if is_reply and is_forward:
            raise ValueError("reply_to_id and forward_from_id are mutually exclusive")

        # New email phải có `to`
        if not is_reply and not is_forward and not self.to:
            raise ValueError(
                "to is required for new emails. "
                "Only omit 'to' when reply_to_id is set."
            )

        # New email phải có subject
        if not is_reply and not is_forward and not self.subject:
            raise ValueError(
                "subject is required for new emails. "
                "Only omit subject when reply_to_id or forward_from_id is set."
            )

        # reply_all chỉ có nghĩa khi có reply_to_id
        if self.reply_all and not is_reply:
            raise ValueError("reply_all=True requires reply_to_id to be set")

        return self

    @field_validator("to", "cc", "bcc", mode="before")
    @classmethod
    def normalize_addresses(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v]
        return v


class DraftEmailOutput(ToolResult):
    data: dict[str, Any] | None = None  # {subject, body, to, cc, bcc}


class SendEmailInput(BaseModel):
    to: Annotated[list[str], Field(
        description="Recipient email addresses.",
        min_length=1,
    )]

    subject: Annotated[str, Field(min_length=1)]

    body: Annotated[str, Field(
        description="Final email body to send. Must be the confirmed, polished version.",
        min_length=1,
    )]

    cc: list[str] = []
    bcc: list[str] = []

    @field_validator("to", "cc", "bcc", mode="before")
    @classmethod
    def normalize_addresses(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [v]
        return v


class SendEmailOutput(ToolResult):
    data: dict[str, str] | None = None  # {message_id, thread_id}


class ReplyEmailInput(BaseModel):
    email_id: Annotated[str, Field(
        description="ID of the email being replied to. Thread context is preserved automatically.",
    )]

    instructions: Annotated[str, Field(
        description="What the reply should say. Agent will generate full reply from this.",
    )]

    tone: str = "formal"
    reply_all: Annotated[bool, Field(
        description="True to reply-all, False to reply only to sender.",
    )] = False


class ReplyEmailOutput(ToolResult):
    data: dict[str, str] | None = None  # {message_id, thread_id}



# =========================================================
# =                 MANAGEMENT tools I/O                  =
# =========================================================

class ApplyLabelsInput(BaseModel):
    email_ids: Annotated[list[str], Field(
        description="List of email IDs to apply labels to.",
        min_length=1,
    )]

    labels_to_add: Annotated[list[str], Field(
        description="Label names to add. For category labels use: 'Spam', 'School', 'Career', "
                    "'Finance', 'Personal'. Can also use custom labels.",
    )] = []

    labels_to_remove: Annotated[list[str], Field(
        description="Label names to remove. Use exact label name as it appears "
                    "in the mailbox. Use list_labels to check available labels first.",
    )] = []

    @model_validator(mode="after")
    def at_least_one_action(self) -> ApplyLabelsInput:
        if not self.labels_to_add and not self.labels_to_remove:
            raise ValueError("Must specify at least one label to add or remove")
        return self


class ApplyLabelsOutput(ToolResult):
    data: dict[str, Any] | None = None  # {modified_count, failed_ids}


class BulkActionInput(BaseModel):
    email_ids: Annotated[list[str], Field(
        description="List of email IDs to perform the action on.",
        min_length=1,
        max_length=100,   # Hard limit — tránh LLM hallucinate xóa cả mailbox
    )]

    action: Annotated[BulkAction, Field(
        description="Action to perform: 'delete', 'mark_read', 'mark_unread', "
                    "'apply_label', 'remove_label'.",
    )]

    label_name: Annotated[str | None, Field(
        description="Required when action is 'apply_label' or 'remove_label'. "
                    "Use list_labels to verify label exists before bulk operations.",
    )] = None

    @model_validator(mode="after")
    def validate_label_required(self) -> BulkActionInput:
        if self.action in (BulkAction.APPLY_LABEL, BulkAction.REMOVE_LABEL) and not self.label_name:
            raise ValueError(f"label_name is required when action is '{self.action.value}'")
        return self


class BulkActionOutput(ToolResult):
    data: dict[str, Any] | None = None  # {success_count, failed_count, failed_ids}



# =========================================================
# =                  SYSTEM tools I/O                     =
# =========================================================

class ClarificationQuestion(BaseModel):
    """Một câu hỏi đơn lẻ trong một lần clarification."""
    question: Annotated[str, Field(
        description="The clarifying question. Be specific about what is needed and why.",
    )]

    options: Annotated[list[str], Field(
        description="Suggested quick-reply options. Empty for open-ended questions.",
    )] = []

    required: Annotated[bool, Field(
        description="True if this question must be answered before proceeding. "
                    "False if agent can make a reasonable default assumption.",
    )] = True


class AskClarificationInput(BaseModel):
    questions: Annotated[list[ClarificationQuestion], Field(
        description="One or more clarifying questions to ask the user in a single round-trip. "
                    "Batch all missing information into one call instead of asking "
                    "one question at a time.",
        min_length=1,
        max_length=5,
    )]

    context: Annotated[str, Field(
        description="Brief explanation of why clarification is needed. "
                    "Shown to user as preamble before the questions. "
                    "Example: 'I need a few details before drafting this email.'",
    )] = ""


class AskClarificationOutput(ToolResult):
    """Frontend renders question + options, waits for user reply."""
    data: dict[str, Any] | None = None  # {question, options}


class RequestConfirmationInput(BaseModel):
    action_summary: Annotated[str, Field(
        description="Human-readable summary of what will happen if user confirms. "
                    "Be explicit about scope and irreversibility. "
                    "Example: 'Delete 47 emails matching spam filter. This cannot be undone.'",
    )]

    affected_items: Annotated[list[str], Field(
        description="List of email IDs or descriptions of items affected by this action.",
    )]

    action_type: Annotated[str, Field(
        description="Type of action: 'delete', 'send', 'reply', 'bulk_delete', etc.",
    )]


class RequestConfirmationOutput(ToolResult):
    """
    Frontend renders confirmation dialog.
    Agent pauses — user response (yes/no) comes back as next chat message.
    """
    data: dict[str, Any] | None = None  # {action_summary, affected_items, action_type}