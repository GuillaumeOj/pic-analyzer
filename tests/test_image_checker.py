from pathlib import Path
from uuid import uuid4

from PIL import Image

from pic_analyzer.image_checker import ImageChecker


def compute_image(
    path: Path,
    mode: str = "RGB",
    size: tuple[int, int] = (1, 1),
    image_ext: str = "jpg",
) -> str:
    image = Image.new(mode, size)
    image_file_path = path / f"{ uuid4().hex }.{image_ext}"
    image.save(image_file_path)
    return str(image_file_path)


def test_image_checker(capsys, tmp_path_factory):
    images_dir = tmp_path_factory.mktemp("images")
    small_image_path = compute_image(images_dir)

    checker = ImageChecker(small_image_path)
    checker.check_image()

    captured = capsys.readouterr()
    assert (
        captured.out == "The image is not printable on standard sizes.\n"
        "You may upload an image with higher resolution, the current resolution "
        "is: 1px x 1px.\n"
    )
