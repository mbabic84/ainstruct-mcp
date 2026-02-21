import re

import tiktoken

from ..config import settings


class ChunkingService:
    def __init__(self):
        self.max_tokens = settings.chunk_max_tokens
        self.overlap_tokens = settings.chunk_overlap_tokens
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        return len(text) // 4

    def chunk_markdown(self, content: str, title: str = "") -> list[dict]:
        chunks = []
        content = content.strip()
        if not content:
            return chunks

        header_pattern = r"(?=^#{1,6}\s+.+$)"
        sections = re.split(header_pattern, content, flags=re.MULTILINE)

        current_chunk = []
        current_tokens = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            section_tokens = self.count_tokens(section)

            if section_tokens > self.max_tokens:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, title, len(chunks)))
                    current_chunk = []
                    current_tokens = 0

                chunks.extend(self._chunk_large_section(section, title, len(chunks)))
                continue

            if current_tokens + section_tokens > self.max_tokens and current_chunk:
                chunks.append(self._create_chunk(current_chunk, title, len(chunks)))

                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = [overlap_text] if overlap_text else []
                current_tokens = self.count_tokens(overlap_text) if overlap_text else 0

            current_chunk.append(section)
            current_tokens += section_tokens

        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, title, len(chunks)))

        return chunks

    def _chunk_large_section(self, section: str, title: str, start_index: int) -> list[dict]:
        lines = section.split("\n")
        chunks = []
        current_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.count_tokens(line)

            if current_tokens + line_tokens > self.max_tokens and current_lines:
                chunks.append(self._create_chunk(current_lines, title, start_index + len(chunks)))

                overlap_lines = self._get_overlap_lines(current_lines)
                current_lines = overlap_lines if overlap_lines else []
                current_tokens = sum(self.count_tokens(line) for line in current_lines)

            current_lines.append(line)
            current_tokens += line_tokens

        if current_lines:
            chunks.append(self._create_chunk(current_lines, title, start_index + len(chunks)))

        return chunks

    def _create_chunk(self, content_parts: list[str], title: str, index: int) -> dict:
        content = "\n".join(content_parts)
        return {
            "content": content,
            "token_count": self.count_tokens(content),
            "title": title,
            "chunk_index": index,
        }

    def _get_overlap_text(self, chunks: list[str]) -> str:
        if not chunks or self.overlap_tokens == 0:
            return ""

        overlap_text = []
        tokens = 0

        for chunk in reversed(chunks):
            chunk_tokens = self.count_tokens(chunk)
            if tokens + chunk_tokens <= self.overlap_tokens:
                overlap_text.insert(0, chunk)
                tokens += chunk_tokens
            else:
                break

        return "\n".join(overlap_text)

    def _get_overlap_lines(self, lines: list[str]) -> list[str]:
        if not lines or self.overlap_tokens == 0:
            return []

        overlap_lines = []
        tokens = 0

        for line in reversed(lines):
            line_tokens = self.count_tokens(line)
            if tokens + line_tokens <= self.overlap_tokens:
                overlap_lines.insert(0, line)
                tokens += line_tokens
            else:
                break

        return overlap_lines


_chunking_service: ChunkingService = None


def get_chunking_service() -> ChunkingService:
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
