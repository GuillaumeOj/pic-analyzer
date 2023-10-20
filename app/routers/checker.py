from fastapi import APIRouter, HTTPException, UploadFile

from app.image_checker import ALLOWED_IMAGES_EXTENSIONS

router = APIRouter()


@router.post("/checker/", tags=["checker"])
async def check_image(image_file: UploadFile):
    file_extension = ""
    if filename := image_file.filename:
        file_extension = filename.split(".")[-1].lower()

    if file_extension not in ALLOWED_IMAGES_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"The file type should be one of {ALLOWED_IMAGES_EXTENSIONS}",
        )

    return {"filename": image_file.filename, "headers": image_file.headers}
