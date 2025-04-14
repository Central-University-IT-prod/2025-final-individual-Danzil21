from fastapi import APIRouter, UploadFile, File, HTTPException
from api.utils.upload_file import upload_cdn_fileobj
from api.schemas.upload import UploadResponse

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/photo", response_model=UploadResponse, summary="Загрузка фото")
async def upload_photo(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Только файлы изображений допускаются")

    filename = file.filename
    if not filename or '.' not in filename:
        raise HTTPException(status_code=400, detail="Неверное имя файла или отсутствует расширение")
    file_extension = filename.rsplit('.', 1)[1].lower()

    file_key = await upload_cdn_fileobj(file.file, file_extension)

    file_url = f"https://prodkekz.storage.yandexcloud.net/files/{file_key}"
    return UploadResponse(file_url=file_url)
