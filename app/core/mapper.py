from app.database import models
from app.core import schemas


def to_project_out(project: models.Project) -> schemas.ProjectOut:
    """
    Convert Project ORM model into ProjectOut Pydantic schema.

    Maps database Project entity into API response schema, including
    nested owner profile information.

    Args:
        project: Project ORM instance with loaded owner and profile relations.

    Returns:
        ProjectOut schema ready for API response serialization.
    """
    return schemas.ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description,
        owner=schemas.ProfileOut(
            first_name=project.owner.profile.first_name,
            last_name=project.owner.profile.last_name,
            email=project.owner.profile.email
        )
    )