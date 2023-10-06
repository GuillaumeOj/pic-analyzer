from pathlib import Path

from PIL import Image
from PIL.Image import Image as PILImage

ImageSizePx = tuple[int, int]
ImageSizeCm = tuple[int, int]
ImageSizeIn = tuple[float, float]

INCH_TO_CM = 2.54
MIN_DPI = 300
STANDARD_ASPECT_RATIOS = [2 / 3, 3 / 4, 1, 1 / 3]
STANDARD_SIZES = [
    (20, 20),
    (20, 30),
    (21, 38),
    (24, 36),
    (25, 25),
    (30, 30),
    (35, 35),
    (30, 45),
    (30, 90),
    (40, 40),
    (40, 60),
    (45, 60),
    (50, 50),
    (50, 75),
    (50, 100),
    (50, 150),
    (60, 60),
    (60, 80),
    (60, 90),
    (70, 70),
    (80, 80),
    (80, 120),
    (90, 180),
    (100, 100),
    (100, 150),
    (120, 120),
    (120, 160),
    (120, 180),
]


class ImageFileError(Exception):
    pass


class CheckError(Exception):
    pass


class ImageChecker:
    image: PILImage

    def __init__(self, image_path: str) -> None:
        self.image_path = Path(image_path)
        try:
            expanded_path = self.image_path.expanduser()
        except RuntimeError:
            pass
        else:
            self.image_path = expanded_path

        return None

    def _check_aspect_ratio(self) -> bool:
        image_width_px, image_height_px = self.image_size_px

        if (
            image_aspect_ratio := image_width_px / image_height_px
        ) not in STANDARD_ASPECT_RATIOS:
            raise CheckError(
                f"The image aspect ratio ({image_aspect_ratio}) "
                f"is not one of {STANDARD_ASPECT_RATIOS}.",
                "You may crop your image with a standard ratio.",
            )

        return True

    def _get_max_print_size(self) -> ImageSizeCm:
        """This get the max print size for having at least a resolution of MIN_DPI.
        It only check with the standard sizes from STANDARD_SIZES"""
        image_width_px, image_height_px = self.image_size_px

        for standard_size in reversed(STANDARD_SIZES):
            image_short_side_in, image_long_side_in = self.get_size_cm_to_in(
                standard_size
            )
            # DPI is calculated for each side of the image with this formula:
            # DPI = image_width_px / print_width_inch
            # and
            # DPI = image_height_px / print_height_inch
            # It could be simplified by additioning both values
            is_max_print_size = MIN_DPI * 2 <= round(
                image_width_px / image_short_side_in
            ) + round(image_height_px / image_long_side_in)
            if is_max_print_size:
                return standard_size

        raise CheckError(
            "The image is not printable on standard sizes.",
            f"You may upload an image with higher resolution, the current resolution "
            f"is: {image_width_px}px x {image_height_px}px.",
        )

    def _load_image(self) -> None:
        try:
            self.image = Image.open(self.image_path)
        except FileNotFoundError:
            raise ImageFileError("The given image path is not correct.")

    def check_image(self) -> None:
        try:
            self._load_image()
        except ImageFileError as e:
            print(e)
            return None
        # Rotate the image because with standard sizes, width is always the short side
        image_width_px, image_height_px = self.image_size_px
        if image_width_px > image_height_px:
            self.image = self.image.transpose(method=Image.Transpose.ROTATE_90)

        try:
            self._check_aspect_ratio()
            self._get_max_print_size()
        except CheckError as e:
            [print(arg) for arg in e.args]
        else:
            print("Your image is valid for printing.")

        return None

    @property
    def image_size_px(self) -> ImageSizePx:
        return self.image.size

    @staticmethod
    def get_size_cm_to_in(size_cm: ImageSizeCm) -> ImageSizeIn:
        width_cm, height_cm = size_cm
        return width_cm / INCH_TO_CM, height_cm / INCH_TO_CM
