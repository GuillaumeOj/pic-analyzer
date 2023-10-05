from pic_analyzer.image_checker import ImageChecker


def test_image_checker(capsys):
    checker = ImageChecker()

    checker.check_image()

    captured = capsys.readouterr()
    assert captured.out == "Your image is valid for printing.\n"
