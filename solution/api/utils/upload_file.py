import secrets

import aioboto3

from app.core.config import settings


async def upload_cdn_fileobj(binary_io, file_extension):
    session = aioboto3.Session()
    async with session.client(
            service_name="s3",
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_KEY_ID,
            aws_secret_access_key=settings.AWS_ACCESS_KEY,
    ) as s3:
        file_key_name = f"{secrets.token_hex(7)}.{file_extension.lower()}"
        await s3.upload_fileobj(binary_io, 'files', file_key_name)
        return file_key_name