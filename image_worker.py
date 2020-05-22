from PIL import Image


def resize_image(attach):
    image = Image.open(attach)
    (width, height) = (image.width // 2, image.height // 2)
    image_resized = image.resize((width, height))
    image_resized.save(fp=attach)
    return attach


if __name__ == "__main__":
    resize_image()
