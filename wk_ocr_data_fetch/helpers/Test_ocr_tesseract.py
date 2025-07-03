import cv2
import pytesseract
from io import BytesIO
from PIL import Image
import numpy as np
import re

# Required in the  case of Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SHAPE = {'RECTANGLE': 0}

DATA_TYPE = {'DICT': 0, 'STRING': 1}


# Image Pre processing helper functions Start
# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# noise removal
def remove_noise(image):
    return cv2.medianBlur(image, 5)


# thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


# dilation
def dilate(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)


# erosion
def erode(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.erode(image, kernel, iterations=1)


# opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)


# canny edge detection
def canny(image):
    return cv2.Canny(image, 100, 200)


# skew correction
def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


# template matching
def match_template(image, template):
    return cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
# Image Pre processing helper functions End


def get_string_from_image(img, lang='eng', oem=3, psm=6):
    custom_config = f'-l {lang} --oem {oem} --psm {psm}'
    return pytesseract.image_to_string(img, config=custom_config)


def get_data_from_image(img, lang='eng', oem=3, psm=6, output_type='DICT'):
    custom_config = f'-l {lang} --oem {oem} --psm {psm}'
    if hasattr(pytesseract.Output, output_type):
        output_type = getattr(pytesseract.Output, output_type)
    else:
        output_type = pytesseract.Output.DICT
    return pytesseract.image_to_data(img, output_type=output_type, config=custom_config)


def draw(image, data, shape='RECTANGLE', put_text=False, text=""):
    x = data["left"]
    y = data["top"]
    w = data["width"]
    h = data["height"]

    if SHAPE[shape] == 0:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if put_text:
        # strip out non-ASCII text so we can draw the text on the image
        # using OpenCV, then draw a bounding box around the text along
        # with the text itself
        text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
        cv2.putText(image, text, (x, y-10), cv2.FONT_HERSHEY_DUPLEX,
                    .5, (0, 0, 255), 1)

    return image


def process_retrieved_data(data, min_conf=50, image=None, draw_boxes=False):
    word_map = {}
    column = 0
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
        word_map[(row, column)] = data["text"][i]
        if image.any() and draw_boxes:
            word_data = {
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i]
            }
            image = draw(image, word_data, put_text=True, text=f"({row},{column})")
    return word_map, image


def search(data, data_type='DICT', row=False, column=False, min_conf=50, regex=r""):
    result = ""
    if DATA_TYPE[data_type] == 0:
        if not row or not column or not isinstance(row, int) or not isinstance(column, int):
            return ""

        column_counter = 0
        row_counter = 0

        next_line = False
        for i in range(0, len(data["conf"])):
            if row_counter > row or (row_counter == row and column_counter > column):
                break

            conf = int(float(data["conf"][i]))
            if conf <= min_conf:
                if not next_line and not data["text"][i]:
                    next_line = True
                continue

            if next_line:
                row_counter += 1
                column_counter = 0
                next_line = False

            column_counter += 1
            if column == column_counter and row == row_counter:
                result = data["text"][i]
                break
    elif DATA_TYPE[data_type] == 1:
        if not regex or not data:
            return ""

        string = data
        result = re.findall(regex, string)
    return result


if __name__ == "__main__":
    file = "test9.jpg"
    image_file = Image.open(
        file
    )
    if file.split(".")[1] == "png":
        image_file = image_file.convert('RGB')

    with BytesIO() as f:
        image_file.save(f, format="jpeg")
        image = f.getvalue()
        image = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_UNCHANGED)

        # Pre Processing Start
        # gray = get_grayscale(image)
        # cv2.imshow("gray", gray)
        # thresh = thresholding(gray)
        # cv2.imshow("thresh", thresh)
        # remove_noise = remove_noise(thresh)
        # cv2.imshow("remove_noise", remove_noise)
        # opening = opening(thresh)
        # cv2.imshow("opening", opening)
        # canny = canny(gray)
        # cv2.imshow("canny", canny)

        # dilate = dilate(image)
        # cv2.imshow("dilate", dilate)
        # gray = get_grayscale(image)
        # cv2.imshow("gray", gray)
        # remove_noise = remove_noise(image)
        # cv2.imshow("remove_noise", remove_noise)
        # thresholding = thresholding(image)
        # cv2.imshow("thresholding", thresholding)
        # erode = erode(image)
        # cv2.imshow("erode", erode)
        # opening = opening(image)
        # cv2.imshow("opening", opening)
        # canny = canny(image)
        # cv2.imshow("canny", canny)
        # deskew = deskew(image)
        # cv2.imshow("deskew", deskew)
        cv2.waitKey(0)
        # Pre Processing End

        string = get_string_from_image(image_file)
        data = get_data_from_image(image_file, output_type='DICT')
        # print(str)
        words, image = process_retrieved_data(data, image=image.copy(), draw_boxes=True)
        print(words)
        print(search(string, data_type='STRING', row=6, column=1, regex=r'[A-Z]'))
        cv2.imshow("Processed Image", image)
        cv2.waitKey(0)
    # print(final_str)
    # if final_str:
    #     pan_number = re.findall(r'[A-Z]{5}[0-9]{4}[A-Z]', final_str)
    #     print(pan_number)
