from prefect.client.orchestration import PrefectClient
from prefect.client.schemas.filters import FlowRunNotificationPolicyFilter
from prefect.client.utilities import inject_client
from rich.console import Console
from uuid import UUID

import prefect.server.schemas as schemas


@inject_client
async def get_flow_run_notification_policies(
    client: "PrefectClient" = None,
) -> list[schemas.core.FlowRunNotificationPolicy]:
    active_policies = await client.read_flow_run_notification_policies(
        FlowRunNotificationPolicyFilter(is_active={"eq_": True})
    )
    inactive_policies = await client.read_flow_run_notification_policies(
        FlowRunNotificationPolicyFilter(is_active={"eq_": False})
    )

    return active_policies + inactive_policies


@inject_client
async def create_flow_run_notification_policy(
    block_document_id: UUID,
    is_active: bool = True,
    tags: list[str] = None,
    state_names: list[str] = None,
    overwrite: bool = False,
    client: "PrefectClient" = None,
    console: Console = None,
):
    existing = await get_flow_run_notification_policies(client=client)
    existing = [
        policy for policy in existing if policy.block_document_id == block_document_id
    ]

    if existing:
        if overwrite:
            for policy in existing:
                await client.update_flow_run_notification_policy(
                    id=policy.id,
                    block_document_id=block_document_id,
                    is_active=is_active,
                    tags=tags,
                    state_names=state_names,
                )
                if console:
                    console.print(
                        f"Updated flow run notification policy '{policy.id}' for block '{block_document_id}'",
                        style="green",
                    )
        else:
            if console:
                console.print(
                    f"Existing flow run notification policy found for block '{block_document_id}'",
                    style="green",
                )
    else:
        policy_id = await client.create_flow_run_notification_policy(
            block_document_id=block_document_id,
            is_active=is_active,
            tags=tags,
            state_names=state_names,
        )
        if console:
            console.print(
                f"Created flow run notification policy '{policy_id}' for block '{block_document_id}'",
                style="green",
            )
