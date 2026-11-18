"""Persistent user-managed Boots template storage."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2


@dataclass(frozen=True)
class BoostTemplateDefault:
    template_id: str
    label: str
    source_path: Path
    source_frame_size: tuple[int, int] | None = None


@dataclass(frozen=True)
class BoostTemplateInfo:
    template_id: str
    label: str
    filename: str
    source_frame_size: tuple[int, int] | None = None


class BoostTemplateManager:
    """Manage Boots templates and the selected template across restarts."""

    CONFIG_FILENAME = "boost_templates.json"

    def __init__(self, storage_dir, defaults=()):
        self.storage_dir = Path(storage_dir).resolve()
        self.config_path = self.storage_dir / self.CONFIG_FILENAME
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._templates = []
        self._selected_id = ""
        self._load(defaults)

    @property
    def templates(self) -> tuple[BoostTemplateInfo, ...]:
        return tuple(self._templates)

    @property
    def selected_id(self) -> str:
        return self._selected_id

    def path_for(self, template_info: BoostTemplateInfo) -> Path:
        return self.storage_dir / template_info.filename

    def select(self, template_id: str) -> BoostTemplateInfo:
        template = self._find(template_id)
        self._selected_id = template.template_id
        self._save()
        return template

    def add_from_file(self, source_path, label=None) -> BoostTemplateInfo:
        source = self._validate_source(source_path)
        template_id = f"boost_{uuid.uuid4().hex[:12]}"
        filename = f"{template_id}{source.suffix.lower()}"
        destination = self.storage_dir / filename
        shutil.copy2(source, destination)
        template = BoostTemplateInfo(
            template_id=template_id,
            label=(str(label).strip() if label else source.stem) or template_id,
            filename=filename,
        )
        previous = (list(self._templates), self._selected_id)
        self._templates.append(template)
        self._selected_id = template_id
        try:
            self._save()
        except Exception:
            self._templates, self._selected_id = previous
            try:
                destination.unlink()
            except OSError:
                pass
            raise
        return template

    def replace_from_file(self, template_id, source_path) -> BoostTemplateInfo:
        source = self._validate_source(source_path)
        old_template = self._find(template_id)
        new_filename = f"{old_template.template_id}_{uuid.uuid4().hex[:8]}{source.suffix.lower()}"
        new_path = self.storage_dir / new_filename
        shutil.copy2(source, new_path)
        replacement = BoostTemplateInfo(
            template_id=old_template.template_id,
            label=old_template.label,
            filename=new_filename,
        )
        index = self._templates.index(old_template)
        previous = (list(self._templates), self._selected_id)
        self._templates[index] = replacement
        try:
            self._save()
        except Exception:
            self._templates, self._selected_id = previous
            try:
                new_path.unlink()
            except OSError:
                pass
            raise
        try:
            self.path_for(old_template).unlink()
        except FileNotFoundError:
            pass
        return replacement

    def delete(self, template_id) -> BoostTemplateInfo:
        template = self._find(template_id)
        index = self._templates.index(template)
        previous = (list(self._templates), self._selected_id)
        self._templates.pop(index)
        if self._selected_id == template.template_id:
            self._selected_id = (
                self._templates[0].template_id if self._templates else ""
            )
        try:
            self._save()
        except Exception:
            self._templates, self._selected_id = previous
            raise
        try:
            self.path_for(template).unlink()
        except FileNotFoundError:
            pass
        return template

    def _find(self, template_id) -> BoostTemplateInfo:
        for template in self._templates:
            if template.template_id == template_id:
                return template
        raise KeyError(f"ไม่พบ Boots template id={template_id}")

    @staticmethod
    def _validate_source(source_path) -> Path:
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"ไม่พบไฟล์รูป: {source}")
        image = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            raise ValueError(f"ไฟล์นี้ไม่ใช่ภาพที่อ่านได้: {source}")
        return source

    def _load(self, defaults):
        if not self.config_path.is_file():
            self._migrate_defaults(defaults)
            self._save()
            return

        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"อ่านรายการ Boots templates ไม่สำเร็จ: {self.config_path}"
            ) from error

        raw_templates = payload.get("templates", []) if isinstance(payload, dict) else []
        for raw in raw_templates:
            if not isinstance(raw, dict):
                continue
            template_id = str(raw.get("template_id", "")).strip()
            label = str(raw.get("label", "")).strip()
            filename = str(raw.get("filename", "")).strip()
            if (
                not template_id
                or not label
                or not filename
                or Path(filename).name != filename
            ):
                continue
            source_size = raw.get("source_frame_size")
            if (
                isinstance(source_size, list)
                and len(source_size) == 2
                and all(isinstance(value, int) for value in source_size)
            ):
                source_size = tuple(source_size)
            else:
                source_size = None
            self._templates.append(
                BoostTemplateInfo(
                    template_id=template_id,
                    label=label,
                    filename=filename,
                    source_frame_size=source_size,
                )
            )

        selected_id = payload.get("selected_id") if isinstance(payload, dict) else ""
        if (
            isinstance(selected_id, str)
            and selected_id in {template.template_id for template in self._templates}
        ):
            self._selected_id = selected_id
        elif self._templates:
            self._selected_id = self._templates[0].template_id

    def _migrate_defaults(self, defaults):
        for default in defaults:
            source = Path(default.source_path)
            if not source.is_file():
                continue
            filename = f"{default.template_id}{source.suffix.lower()}"
            destination = self.storage_dir / filename
            shutil.copy2(source, destination)
            self._templates.append(
                BoostTemplateInfo(
                    template_id=default.template_id,
                    label=default.label,
                    filename=filename,
                    source_frame_size=default.source_frame_size,
                )
            )
        if self._templates:
            self._selected_id = self._templates[0].template_id

    def _save(self):
        payload = {
            "selected_id": self._selected_id,
            "templates": [asdict(template) for template in self._templates],
        }
        temporary_path = self.config_path.with_suffix(".json.tmp")
        try:
            temporary_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary_path, self.config_path)
        except OSError:
            try:
                temporary_path.unlink()
            except OSError:
                pass
            raise
