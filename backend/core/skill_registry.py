"""Skill registry — teach AGNI new procedures via the open SKILL.md format.

A *skill* is a folder with a ``SKILL.md`` file: YAML-ish frontmatter (``name``, ``description``)
plus markdown instructions. This is NOT model training — it's runtime capability injection. When a
request matches a skill's description, the soldier loads that skill's instructions into its prompt
and follows them. Drop a ``SKILL.md`` into ``backend/skills/<name>/`` and AGNI can use it — the same
files authored for Claude / Codex / ChatGPT agents work here too.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass
class Skill:
    name: str
    description: str
    body: str


def _parse(text: str) -> Skill:
    name, description, body = "", "", text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if m:
        front, body = m.group(1), m.group(2)
        for line in front.splitlines():
            low = line.lower()
            if low.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            elif low.startswith("description:"):
                description = line.split(":", 1)[1].strip()
    return Skill(name=name or "skill", description=description, body=body.strip())


class SkillRegistry:
    def __init__(self, root: str) -> None:
        self._root = root
        self.skills: list[Skill] = []
        self._load(root)

    def _load(self, root: str) -> None:
        if not os.path.isdir(root):
            return
        for entry in sorted(os.listdir(root)):
            path = os.path.join(root, entry, "SKILL.md")
            if os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8") as fh:
                        self.skills.append(_parse(fh.read()))
                except Exception:  # pragma: no cover - a bad skill file shouldn't crash startup
                    pass

    def names(self) -> list[str]:
        return [s.name for s in self.skills]

    def reload(self) -> None:
        """Re-scan the skills directory (after a new SKILL.md is added)."""
        self.skills = []
        self._load(self._root)

    def save_skill(self, name: str, content: str) -> "Skill":
        """Create/overwrite backend/skills/<slug>/SKILL.md from raw markdown, then reload.

        If the content has no frontmatter, a minimal ``name``/``description`` header is added so
        the skill is matchable. Returns the parsed Skill.
        """
        clean = (name or "skill").strip()
        slug = re.sub(r"[^a-z0-9]+", "-", clean.lower()).strip("-") or "skill"
        text = content if content.lstrip().startswith("---") else (
            f"---\nname: {clean or slug}\ndescription: {clean or slug}\n---\n\n{content.strip()}\n")
        folder = os.path.join(self._root, slug)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        self.reload()
        return _parse(text)

    def match(self, query: str, min_score: int = 2) -> Skill | None:
        """Return the best-matching skill for a request, or None if nothing fits well."""
        low = (query or "").lower()
        qwords = set(re.findall(r"[a-z]{4,}", low))
        best: Skill | None = None
        best_score = 0
        for skill in self.skills:
            text = (skill.name.replace("-", " ") + " " + skill.description).lower()
            dwords = set(re.findall(r"[a-z]{4,}", text))
            score = len(qwords & dwords)
            if skill.name.replace("-", " ") in low:
                score += 3
            if score > best_score:
                best, best_score = skill, score
        return best if best_score >= min_score else None


# Default registry: skills live in backend/skills/<name>/SKILL.md
_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
SKILLS = SkillRegistry(_ROOT)
