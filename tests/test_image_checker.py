from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image, ImageCms

from pic_analyzer.image_checker import CheckError, ImageChecker

Image.MAX_IMAGE_PIXELS = None

DEFAULT_PROFILE_PATH = Path(__file__).parent / "fixtures/icc_profile_adobe_srgb.icc"


@pytest.fixture
def tmp_path_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("images")


def compute_image(
    image_dir_path: Path,
    mode: str = "RGB",
    size: tuple[int, int] = (1, 1),
    image_ext: str = "jpg",
    profile_path: Path = DEFAULT_PROFILE_PATH,
) -> str:
    """This creates an image with Pillow for the tests
    and returns the str path of this image."""

    # Create the image
    image = Image.new(mode, size)
    image_file_path = image_dir_path / f"{ uuid4().hex }.{image_ext}"

    # Load the profile
    icc_profile = ImageCms.getOpenProfile(str(profile_path))

    # Save the image and return the path of the image
    image.save(image_file_path, icc_profile=icc_profile.tobytes())
    return str(image_file_path)


def load_image_checker(image_path: str) -> ImageChecker:
    image_checker = ImageChecker(image_path)
    image_checker._load_image()

    return image_checker


def test_check_aspect_ratio(tmp_path_dir):
    # The aspect ratio is not one of the standard
    image_with_invalid_aspect_ratio = compute_image(tmp_path_dir, size=(1, 5))
    image_checker = load_image_checker(image_with_invalid_aspect_ratio)
    with pytest.raises(CheckError):
        image_checker._check_aspect_ratio()

    # The aspect ratio is one of the standard
    image_with_valid_aspect_ratio = compute_image(tmp_path_dir)
    image_checker = load_image_checker(image_with_valid_aspect_ratio)
    assert image_checker._check_aspect_ratio() is True


def test_get_image_max_print_size(tmp_path_dir):
    # The image is too small for printing
    image_too_small_for_printing = compute_image(tmp_path_dir)
    image_checker = load_image_checker(image_too_small_for_printing)
    with pytest.raises(CheckError):
        image_checker._get_max_print_size()

    # The image is printable with the minimum print size
    printable_image = compute_image(tmp_path_dir, size=(2361, 2361))
    image_checker = load_image_checker(printable_image)
    max_print_size = image_checker._get_max_print_size()
    assert max_print_size == (20, 20)

    # The image is printable on a bigger print size
    printable_image = compute_image(tmp_path_dir, size=(14163, 21249))
    image_checker = load_image_checker(printable_image)
    max_print_size = image_checker._get_max_print_size()
    assert max_print_size == (120, 180)


def test_check_profile_description(tmp_path_dir):
    adobe_rgb_1998_icc_file = (
        Path(__file__).parent / "fixtures/icc_profile_adobe_rgb_1998.icc"
    )

    # The image as a non standard profile
    image_with_non_standard_profile = compute_image(
        tmp_path_dir, profile_path=adobe_rgb_1998_icc_file
    )
    image_checker = load_image_checker(image_with_non_standard_profile)
    with pytest.raises(CheckError):
        image_checker._check_profile_description()

    # The image as a standard profile
    image_with_standard_profile = compute_image(tmp_path_dir)
    image_checker = load_image_checker(image_with_standard_profile)
    assert image_checker._check_profile_description() is True


def test_check_image(capsys, tmp_path_dir):
    # The image is too small for printing
    small_image_path = compute_image(tmp_path_dir)
    image_checker = ImageChecker(small_image_path)
    image_checker.check_image()
    captured = capsys.readouterr()
    assert (
        captured.out == "The image is not printable on standard sizes.\n"
        "You may upload an image with higher resolution, the current resolution "
        "is: 1px x 1px.\n"
    )

    # The image is valid for printing
    valid_image = compute_image(tmp_path_dir, size=(2436, 2436))
    image_checker = ImageChecker(valid_image)
    image_checker.check_image()
    captured = capsys.readouterr()
    assert captured.out == "Your image is valid for printing.\n"
