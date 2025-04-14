from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from api.database.models.models import Client as ClientModel
from api.schemas.client import ClientResponse, ClientUpsert

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/{clientId}", response_model=ClientResponse)
async def get_client_by_id(clientId: UUID, session: AsyncSession = Depends(get_session)):
    client = await session.get(ClientModel, clientId)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client

@router.post("/bulk", response_model=List[ClientResponse], status_code=status.HTTP_201_CREATED)
async def upsert_clients(clients: List[ClientUpsert], session: AsyncSession = Depends(get_session)):
    result_clients = []
    for client_data in clients:
        client = await session.get(ClientModel, client_data.id)
        if client:
            client.login = client_data.login
            client.age = client_data.age
            client.location = client_data.location
            client.gender = client_data.gender
        else:
            client = ClientModel(
                id=client_data.id,
                login=client_data.login,
                age=client_data.age,
                location=client_data.location,
                gender=client_data.gender
            )
            session.add(client)
        result_clients.append(client)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate client record") from e
    return result_clients
