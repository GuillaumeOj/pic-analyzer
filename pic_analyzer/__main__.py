from image_checker import ImageChecker

image_path = str(input("Give image path:"))
checker = ImageChecker(image_path)
checker.check_image()
