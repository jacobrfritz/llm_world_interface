import os
from typing import Any

from pydantic import BaseModel

from llm_world_interface.connectors.base import BaseConnector
from llm_world_interface.models.note import ObsidianNoteSchema


class ObsidianConnector(BaseConnector):
    @property
    def name(self) -> str:
        return "create_obsidian_note"

    @property
    def description(self) -> str:
        return (
            "Use this to create or update a research note, task, or "
            "mind map node in the user's Obsidian vault."
        )

    @property
    def args_schema(self) -> type[BaseModel]:
        return ObsidianNoteSchema

    def __init__(self, vault_root: str):
        self.vault_root = vault_root

    def _build_frontmatter(self, validated_data: ObsidianNoteSchema) -> str:
        # Internal method to format YAML block
        yaml = "---\n"
        if validated_data.due_date:
            yaml += f"due_date: {validated_data.due_date.isoformat()}\n"
        if validated_data.tags:
            yaml += f"tags: {validated_data.tags}\n"
        yaml += "---\n\n"
        return yaml

    def _inject_wikilinks(self, content: str, links: list[str]) -> str:
        # Appends formatted [[Links]] to the bottom of the document
        if not links:
            return content
        link_block = "\n\n## Related\n" + "\n".join([f"- [[{link}]]" for link in links])
        return content + link_block

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        validated_data = ObsidianNoteSchema(**kwargs)
        folder = validated_data.folder.strip("/")
        target_dir = (
            os.path.join(self.vault_root, folder) if folder else self.vault_root
        )
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, f"{validated_data.title}.md")

        full_content = self._build_frontmatter(validated_data) + self._inject_wikilinks(
            validated_data.content, validated_data.related_links
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return {"status": "success", "path": file_path}
