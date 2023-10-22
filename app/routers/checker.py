from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.image_checker import (
    ALLOWED_IMAGES_EXTENSIONS,
    CheckError,
    ImageChecker,
    ImageFileError,
)

router = APIRouter()


class ImageSizeCm(BaseModel):
    width: float
    height: float


@router.post("/checker/", tags=["checker"])
async def check_image(image_file: UploadFile) -> list[ImageSizeCm]:
    file_extension = ""
    if filename := image_file.filename:
        file_extension = filename.split(".")[-1].lower()

    if file_extension not in ALLOWED_IMAGES_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"The file type should be one of {ALLOWED_IMAGES_EXTENSIONS}",
        )

    image = await image_file.read()

    try:
        print_sizes = ImageChecker().check_image(image)
    except ImageFileError:
        raise HTTPException(status_code=400, detail="The file seems incorrect")
    except CheckError as e:
        error_detail = " ".join(e.args)
        raise HTTPException(status_code=400, detail=error_detail)

    return [ImageSizeCm(width=width, height=height) for width, height in print_sizes]
