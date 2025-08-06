from connexion import request

from api.utils import prime_query_kwargs, bleach_body
from app.database import PostgresqlDB
from app.database.schemas import QueueSchema
from app.security import role_authorization
_LOADING_OPTIONS = {
    "requests": False,
    "managers": False,
    "user_profile": False,
    "manager_profiles": False
}


async def search(**kwargs):
    db: PostgresqlDB = request.state.db

    prime_query_kwargs(kwargs)

    queues = await db.get_queues(
        _loading_options=_LOADING_OPTIONS,
        **kwargs
    )
    queues_data = [
        QueueSchema.model_validate(queue).model_dump(
            exclude={"requests", "managers"}
        )
        for queue in queues
    ]

    return queues_data, 200


async def get(queue_id: int):
    db: PostgresqlDB = request.state.db

    queue = await db.get_queue(
        id=queue_id,
        _loading_options=_LOADING_OPTIONS,
    )

    if not queue:
        return {"message": f"Queue with ID '{queue_id}' not found"}, 404

    queue_data = QueueSchema.model_validate(queue).model_dump(
        exclude={"requests", "managers"}
    )

    return queue_data, 200


# @role_authorization(RoleName.ADMIN, override=matching_user_id_override, override_kwargs={"resource_user_id_lookup": "body.user_id"})  # Disable regular users from adding queues for now
@role_authorization(one_of={RoleName.PRIVILEGED, RoleName.ADMIN})
async def post(body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    body = bleach_body(
        body,
        whitelisted_keys=QueueSchema.model_fields.keys(),
        blacklisted_keys={"id", "created_at", "updated_at", "requests", "managers", "user_profile", "manager_profiles"}
    )
    await db.add_queue(**body)

    return {"message": "Queue added successfully!"}


@role_authorization(RoleName.ADMIN, override=queue_owner_override)
async def patch(queue_id: int, body: dict, **kwargs):
    db: PostgresqlDB = request.state.db

    body = bleach_body(
        body,
        whitelisted_keys=QueueSchema.model_fields.keys(),
        blacklisted_keys={"id", "user_id", "created_at", "updated_at", "requests", "managers", "user_profile", "manager_profiles"}
    )
    await db.update_queue(queue_id, **body)

    return {"message": "Queue updated successfully!"}, 200
