from typing import Any


def serialize_robot_version_catalog_item(
    version: Any,
    *,
    current_version: int,
    publisher: Any | None,
    source_project: Any | None,
) -> dict[str, object]:
    """Converte uma RobotVersion em contrato público sem expor storage paths."""

    return {
        "id": version.id,
        "version": version.version,
        "filename": version.filename,
        "file_hash": version.file_hash,
        "published_at": (
            version.published_at.isoformat()
            if version.published_at
            else None
        ),
        "created_at": version.created_at.isoformat(),
        "is_current": version.version == current_version,
        "publisher": (
            {
                "id": publisher.id,
                "name": publisher.name,
                "username": publisher.username,
            }
            if publisher
            else None
        ),
        "source_project": (
            {
                "id": source_project.id,
                "name": source_project.name,
            }
            if source_project
            else None
        ),
    }
