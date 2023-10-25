import io
from pathlib import Path

import pytest
from PIL import Image, ImageCms

from app.image_checker import CheckError, ImageChecker

Image.MAX_IMAGE_PIXELS = None

DEFAULT_PROFILE_PATH = Path(__file__).parent / "fixtures/icc_profile_adobe_srgb.icc"


def compute_image(
    mode: str = "RGB",
    size: tuple[int, int] = (1, 1),
    image_ext: str = "jpeg",
    profile_path: Path = DEFAULT_PROFILE_PATH,
) -> io.BytesIO:
    """This creates an image with Pillow for the tests
    and returns the str path of this image."""

    # Create the image
    image = Image.new(mode, size)

    # Load the profile
    icc_profile = ImageCms.getOpenProfile(str(profile_path))

    # Save the image and return the raw data of the image
    image_byte_array = io.BytesIO()
    image.save(image_byte_array, format=image_ext, icc_profile=icc_profile.tobytes())
    return image_byte_array


def load_image_checker(image_data: bytes) -> ImageChecker:
    image_checker = ImageChecker()
    image_checker._load_image(image_data)

    return image_checker


def test_check_aspect_ratio():
    # The aspect ratio is not one of the standard
    image_with_invalid_aspect_ratio = compute_image(size=(1, 5))
    image_checker = load_image_checker(image_with_invalid_aspect_ratio.getvalue())

    with pytest.raises(CheckError) as excinfo:
        image_checker._check_aspect_ratio()
    assert "The image aspect ratio (0.2) is not one of [0.67, 0.75, 1, 0.33]." in str(
        excinfo.value
    )

    # The aspect ratio is one of the standard
    image_with_valid_aspect_ratio = compute_image()
    image_checker = load_image_checker(image_with_valid_aspect_ratio.getvalue())
    assert image_checker._check_aspect_ratio() is True


def test_get_image_max_print_size():
    # The image is too small for printing
    image_too_small_for_printing = compute_image()
    image_checker = load_image_checker(image_too_small_for_printing.getvalue())

    with pytest.raises(CheckError) as excinfo:
        image_checker._get_max_print_size()
    assert "The image is not printable on standard sizes." in str(excinfo.value)

    # The image is printable with the minimum print size
    printable_image = compute_image(size=(2361, 2361))
    image_checker = load_image_checker(printable_image.getvalue())
    max_print_size = image_checker._get_max_print_size()
    assert max_print_size == (20, 20)

    # The image is printable on a bigger print size
    printable_image = compute_image(size=(14163, 21249))
    image_checker = load_image_checker(printable_image.getvalue())
    max_print_size = image_checker._get_max_print_size()
    assert max_print_size == (120, 180)


def test_check_profile_description():
    adobe_rgb_1998_icc_file = (
        Path(__file__).parent / "fixtures/icc_profile_adobe_rgb_1998.icc"
    )

    # The image as a non standard profile
    image_with_non_standard_profile = compute_image(
        profile_path=adobe_rgb_1998_icc_file
    )
    image_checker = load_image_checker(image_with_non_standard_profile.getvalue())

    with pytest.raises(CheckError) as excinfo:
        image_checker._check_profile_description()
    assert (
        "The profile of the image (Adobe RGB (1998)) is not "
        "one of ['sRGB IEC61966-2.1']" in str(excinfo.value)
    )

    # The image as a standard profile
    image_with_standard_profile = compute_image()
    image_checker = load_image_checker(image_with_standard_profile.getvalue())
    assert image_checker._check_profile_description() is True


def test_check_image():
    # The image is too small for printing
    small_image = compute_image()
    image_checker = ImageChecker()

    with pytest.raises(CheckError) as excinfo:
        image_checker.check_image(small_image.getvalue())
    assert "The image is not printable on standard sizes." in str(excinfo.value)

    # The image is valid for printing
    valid_image = compute_image(size=(2436, 2436))
    image_checker = ImageChecker()
    printable_sizes = image_checker.check_image(valid_image.getvalue())

    assert [(20, 20)] == printable_sizes
