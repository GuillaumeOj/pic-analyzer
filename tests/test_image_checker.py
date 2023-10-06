from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image

from pic_analyzer.image_checker import CheckError, ImageChecker

Image.MAX_IMAGE_PIXELS = None


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


def test_image_aspect_ratio(tmp_path_factory):
    images_dir = tmp_path_factory.mktemp("images")
    image_with_invalid_aspect_ratio = compute_image(images_dir, size=(1, 5))

    checker = ImageChecker(image_with_invalid_aspect_ratio)
    checker._load_image()

    # The aspect ratio is not one of the standard
    with pytest.raises(CheckError):
        checker._check_aspect_ratio()

    valid_aspect_ratio = compute_image(images_dir)
    checker = ImageChecker(valid_aspect_ratio)
    checker._load_image()
    assert checker._check_aspect_ratio() is True


def test_image_max_print_size(tmp_path_factory):
    images_dir = tmp_path_factory.mktemp("images")
    small_image_path = compute_image(images_dir)

    checker = ImageChecker(small_image_path)
    checker._load_image()

    # The image is too small for printing
    with pytest.raises(CheckError):
        checker._get_max_print_size()

    valid_image_path = compute_image(images_dir, size=(2361, 2361))
    checker = ImageChecker(valid_image_path)
    checker._load_image()

    max_print_size = checker._get_max_print_size()
    assert max_print_size == (20, 20)

    valid_image_path = compute_image(images_dir, size=(14163, 21249))
    checker = ImageChecker(valid_image_path)
    checker._load_image()

    max_print_size = checker._get_max_print_size()
    assert max_print_size == (120, 180)


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

    valid_image = compute_image(images_dir, size=(2436, 2436))
    checker = ImageChecker(valid_image)
    checker.check_image()
    captured = capsys.readouterr()
    assert captured.out == "Your image is valid for printing.\n"
