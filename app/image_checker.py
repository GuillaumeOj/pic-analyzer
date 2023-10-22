import io
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, ImageCms
from PIL.Image import Image as PILImage

ImageSizePx = tuple[int, int]
ImageSizeCm = tuple[int, int]
ImageSizeIn = tuple[float, float]

ALLOWED_IMAGES_EXTENSIONS = ["jpg", "jpeg", "tiff"]
INCH_TO_CM = 2.54
MIN_DPI = 300
STANDARD_ASPECT_RATIOS = [2 / 3, 3 / 4, 1, 1 / 3]
STANDARD_PROFILE_DESCRIPTIONS = ["sRGB IEC61966-2.1"]
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

    def _round_aspect_ratio(self, aspect_ratio: float) -> float:
        return round(aspect_ratio, ndigits=2)

    def _check_aspect_ratio(self) -> bool:
        image_width_px, image_height_px = self.image_size_px

        image_aspect_ratio = self._round_aspect_ratio(image_width_px / image_height_px)
        rounded_standard_aspect_ratios = [
            self._round_aspect_ratio(aspect_ratio)
            for aspect_ratio in STANDARD_ASPECT_RATIOS
        ]

        if image_aspect_ratio not in rounded_standard_aspect_ratios:
            raise CheckError(
                f"The image aspect ratio ({image_aspect_ratio}) "
                f"is not one of {rounded_standard_aspect_ratios}.",
                "You may crop your image with a standard ratio.",
            )

        return True

    def _check_profile_description(self) -> bool:
        icc_profile_data = self.image.info.get("icc_profile")
        if not icc_profile_data:
            raise CheckError("The profile of the image is missing.")

        decoded_icc_profile = BytesIO(icc_profile_data)
        icc_profile = ImageCms.ImageCmsProfile(decoded_icc_profile)
        profile_description = icc_profile.profile.profile_description

        if profile_description not in STANDARD_PROFILE_DESCRIPTIONS:
            raise CheckError(
                f"The profile of the image ({profile_description}) is not "
                f"one of {str(STANDARD_PROFILE_DESCRIPTIONS)}"
            )

        return True

    def _get_print_sizes(self, max_print_size: ImageSizeCm) -> list[ImageSizeCm]:
        max_print_size_index = STANDARD_SIZES.index(max_print_size)

        return STANDARD_SIZES[: max_print_size_index + 1]

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

    def _load_image(self, image_data: bytes) -> None:
        try:
            self.image = Image.open(io.BytesIO(image_data))
        except OSError:
            raise ImageFileError("The given image is not correct.")

    def check_image(self, image_data: bytes) -> list[ImageSizeCm]:
        try:
            self._load_image(image_data)
        except ImageFileError as e:
            raise e

        # Rotate the image because with standard sizes, width is always the short side
        image_width_px, image_height_px = self.image_size_px
        if image_width_px > image_height_px:
            self.image = self.image.transpose(method=Image.Transpose.ROTATE_90)

        try:
            self._check_aspect_ratio()
            self._check_profile_description()
            max_print_size = self._get_max_print_size()
        except CheckError as e:
            raise e

        return self._get_print_sizes(max_print_size)

    @property
    def image_size_px(self) -> ImageSizePx:
        return self.image.size

    @staticmethod
    def get_size_cm_to_in(size_cm: ImageSizeCm) -> ImageSizeIn:
        width_cm, height_cm = size_cm
        return width_cm / INCH_TO_CM, height_cm / INCH_TO_CM
