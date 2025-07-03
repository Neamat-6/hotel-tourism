import cv2
import pytesseract
from io import BytesIO
from PIL import Image
import numpy as np
import re
from functools import wraps
import base64
import platform
# from . import image_pre_processing
import logging
_logger = logging.getLogger(__name__)

# Required in the  case of Windows
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SHAPE = {'RECTANGLE': 0}

DATA_TYPE = {'DICT': 0, 'STRING': 1}


def convert_image(func):
    """
    Convert base 64 image data to openCV numpy array
    :param func: function object
    :return: wrapper method object
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        im_bytes = base64.b64decode(args[0])
        img = cv2.imdecode(np.frombuffer(im_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
        return func(img, *args[1:], **kwargs)
    return wrapper


def b64_to_pil(im_b64):
    """
    Convert base 64 to pil image
    :param im_b64: base 64 image data
    :return: pil format image
    """
    im_bytes = base64.b64decode(im_b64)  # im_bytes is a binary image
    im_file = BytesIO(im_bytes)  # convert image to file-like object
    img = Image.open(im_file)  # img is now PIL Image object
    return img


def pil_to_b64(im_pil):
    """
    Convert pil image data to base 64
    :param im_pil: pil format image
    :return: base64 image data
    """
    with BytesIO() as f:
        im_pil.save(f, format="JPEG")
        im_bytes = f.getvalue()  # im_bytes: image in binary format.
        im_b64 = base64.b64encode(im_bytes)
    return im_b64


def opencv_to_pil(im_arr):
    """
    Convert openCV numpy array image data to pil format
    :param im_arr: opencv numpy array
    :return: pil image object
    """
    img = cv2.cvtColor(im_arr, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)
    return im_pil


def opencv_to_b64(im_arr):
    """
    Convert openCV numpy array image data to base 64
    :param im_arr: opencv numpy array
    :return: base64 image data
    """
    im_bytes = im_arr.tobytes()
    im_b64 = base64.b64encode(im_bytes)
    return im_b64


# def get_image_data(image):
#     # TODO complete this method and get the right output
#     return [dir(image), type(image)]


@convert_image
def get_string_from_image(img, lang='eng', oem=3, psm=6):
    custom_config = f'-l {lang} --oem {oem} --psm {psm}'
    return pytesseract.image_to_string(img, config=custom_config)


@convert_image
def get_data_from_image(img, lang='eng', oem=3, psm=6, output_type='DICT'):
    custom_config = f'-l {lang} --oem {oem} --psm {psm}'
    if hasattr(pytesseract.Output, output_type):
        output_type = getattr(pytesseract.Output, output_type)
    else:
        output_type = pytesseract.Output.DICT
    return pytesseract.image_to_data(img, output_type=output_type, config=custom_config)


@convert_image
def draw_words(img, data):
    for word in data:
        word_data = {
            "left": data[word]["left"],
            "top": data[word]["top"],
            "width": data[word]["width"],
            "height": data[word]["height"]
        }
        img = draw(img, word_data, put_text=False, text=f"({word[0]},{word[1]})")
    return img


def draw(img, data, shape='RECTANGLE', put_text=False, text="", b64=False):
    x = data["left"]
    y = data["top"]
    w = data["width"]
    h = data["height"]

    if SHAPE[shape] == 0:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if put_text:
        # strip out non-ASCII text so we can draw the text on the image
        # using OpenCV, then draw a bounding box around the text along
        # with the text itself
        text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
        cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_DUPLEX,
                    .5, (0, 0, 255), 1)
    if b64:
        img = opencv_to_b64(img)
    return img


def words_row_column(data, min_conf=50):
    word_map = {}
    column = 0
    max_column = column
    row = 0

    next_line = False
    for i in range(0, len(data["conf"])):
        conf = int(float(data["conf"][i]))
        if conf <= min_conf:
            if not next_line and not data["text"][i]:
                next_line = True
            continue

        if next_line:
            row += 1
            column = 0
            next_line = False

        column += 1
        if column > max_column:
            max_column = column
        word_data = {}
        for k in data:
            word_data[k] = data[k][i]
        word_map[(row, column)] = word_data

    return word_map, row, max_column


def search(data, data_type='DICT', row=False, column=False, regex=r""):
    result = ""
    if DATA_TYPE[data_type] == 0:
        if not isinstance(data, dict) or not row or not column or not isinstance(row, int) \
                or not isinstance(column, int):
            return ""
        result = data.get((row, column), "") and data[(row, column)]['text']
    elif DATA_TYPE[data_type] == 1:
        if not regex or not data:
            return ""
        string = data
        res = re.findall(regex, string)
        if res:
            result = " ".join(res)
    return result


if __name__ == "__main__":
    file = "test9.jpg"
    # image_file = Image.open(
    #     file
    # )
    with open(file, "rb") as f:
        image_file = base64.b64encode(f.read())
    if file.split(".")[1] == "png":
        image_file = image_file.convert('RGB')
    # print(image_file)
    # with BytesIO() as f:
    #     image_file.save(f, format="jpeg")
    #     image = f.getvalue()
    #     # image = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_UNCHANGED)
    #
    #     # Pre Processing Start
    #     # gray = get_grayscale(image)
    #     # cv2.imshow("gray", gray)
    #     # thresh = thresholding(gray)
    #     # cv2.imshow("thresh", thresh)
    #     # remove_noise = remove_noise(thresh)
    #     # cv2.imshow("remove_noise", remove_noise)
    #     # opening = opening(thresh)
    #     # cv2.imshow("opening", opening)
    #     # canny = canny(gray)
    #     # cv2.imshow("canny", canny)
    #
    #     # dilate = dilate(image)
    #     # cv2.imshow("dilate", dilate)
    #     # gray = get_grayscale(image)
    #     # cv2.imshow("gray", gray)
    #     # remove_noise = remove_noise(image)
    #     # cv2.imshow("remove_noise", remove_noise)
    #     # thresholding = thresholding(image)
    #     # cv2.imshow("thresholding", thresholding)
    #     # erode = erode(image)
    #     # cv2.imshow("erode", erode)
    #     # opening = opening(image)
    #     # cv2.imshow("opening", opening)
    #     # canny = canny(image)
    #     # cv2.imshow("canny", canny)
    #     # deskew = deskew(image)
    #     # cv2.imshow("deskew", deskew)
    #     # cv2.waitKey(0)
    #     # Pre Processing End
    #     print(get_image_data(image))
    #     string = get_string_from_image(image)
    #     data = get_data_from_image(image, output_type='DICT')
    #     # print(str)
    #     # words, image = process_retrieved_data(data, image=image, draw_boxes=True)
    #     # print(words)
    #     print(search(string, data_type='STRING', row=6, column=1, regex=r'[A-Z]'))
    #     # cv2.imshow("Processed Image", image)
    #     # cv2.waitKey(0)
    data = get_data_from_image(image_file)
    words_map = words_row_column(data)
    image = draw_words(image_file, words_map)
    print(opencv_to_b64(image))
    # print(string)

