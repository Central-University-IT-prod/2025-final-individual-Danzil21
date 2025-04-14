from pydantic import BaseModel, Field

class UploadResponse(BaseModel):
    file_url: str = Field(..., description="URL загруженного файла")