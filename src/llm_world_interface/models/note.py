from datetime import date

from pydantic import BaseModel, Field


class ObsidianNoteSchema(BaseModel):
    title: str = Field(..., description="A clean, alphanumeric title for the note.")
    folder: str = Field(default="/", description="Vault subdirectory path.")
    content: str = Field(..., description="Markdown formatted body content.")
    tags: list[str] = Field(
        default_factory=list,
        description="List of relevant tags without the '#' symbol.",
    )
    due_date: date | None = Field(
        None, description="Actionable deadline if applicable."
    )
    related_links: list[str] = Field(
        default_factory=list,
        description="Exact titles of related concepts to be linked.",
    )
