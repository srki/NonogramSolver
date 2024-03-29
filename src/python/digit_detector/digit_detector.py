import cv2
from operator import itemgetter
import numpy as np
from util.benchmark import timeit


class DigitDetector:
    def __init__(self, classifier):
        self.classifier = classifier
        self.image = None
        self.lines = None

    def set_image(self, image):
        self.image = image

    def set_lines(self, lines, lines_vertical=None, lines_horizontal=None):
        if lines_vertical and lines_horizontal:
            self.lines = (lines_vertical, lines_horizontal)
        else:
            self.lines = lines

    @staticmethod
    def get_digits_sorted(digits, key_idx, value_idx=4):
        return [d[value_idx] for d in sorted(digits, key=lambda _d: _d[key_idx])]

    @staticmethod
    def append_number(numbers, digits):
        number = 0
        for digit in digits:
            number = number * 10 + digit

        if number != 0:
            numbers.append(number)

    @staticmethod
    def get_numbers_vertical(digits):
        numbers, number_digits, last_y = [], [], -1
        for digit in sorted(digits, key=itemgetter(1)):
            if digit[1] > last_y:
                DigitDetector.append_number(numbers, DigitDetector.get_digits_sorted(number_digits, 0))
                number_digits = []
            last_y = digit[1] + digit[3]
            number_digits.append(digit)

        DigitDetector.append_number(numbers, DigitDetector.get_digits_sorted(number_digits, 0))
        return numbers

    @staticmethod
    def get_numbers_horizontal(digits, eps):
        numbers, number_digits, last_x = [], [], -1
        for digit in sorted(digits, key=itemgetter(0)):
            if digit[0] - last_x > eps:
                DigitDetector.append_number(numbers, DigitDetector.get_digits_sorted(number_digits, 0))
                number_digits = []
            last_x = digit[0] + digit[2]
            number_digits.append(digit)

        DigitDetector.append_number(numbers, DigitDetector.get_digits_sorted(number_digits, 0))
        return numbers

    @timeit
    def get_result(self):
        lines_v = self.lines[0]
        lines_h = self.lines[1]

        img_gray = self.image
        self.image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2RGB)
        nonogram_values = ([], [])

        for i in xrange(0, len(lines_v) - 1):
            for j in xrange(0, len(lines_h) - 1):
                x1, x2 = lines_v[i] + 1, lines_v[i + 1] - 1
                y1, y2 = lines_h[j] + 1, lines_h[j + 1] - 1
                cv2.rectangle(self.image, (x1, y1), (x2, y2), (255, 0, 0))

                min_h = min(x2 - x1, y2 - y1) / 3.0
                min_w = min_h / 2.0

                region = 255 - img_gray[lines_h[j] + 1:  lines_h[j + 1] - 1, lines_v[i] + 1: lines_v[i + 1] - 1]
                _, contours, _ = cv2.findContours(region.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                region_digits = []
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    if 3 * min_h > h > min_h and 4 * min_w > w > min_w:
                        digit = region[y: y + h, x:x + w]
                        value = sorted(self.classifier.classify(255 - digit))[0][1]
                        cv2.putText(self.image, str(value), (x + x1, y + y1 + h), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), thickness=2)
                        region_digits.append((x, y, w, h, value))

                if i + j != 0:
                    if j == 0:
                        nums = self.get_numbers_vertical(region_digits)
                        if len(nums) != 0:
                            nonogram_values[0].append(nums)
                    if i == 0:
                        nums = self.get_numbers_horizontal(region_digits, min_w)
                        if len(nums) != 0:
                            nonogram_values[1].append(nums)

        sum0 = sum([sum(vals) for vals in nonogram_values[0]])
        sum1 = sum([sum(vals) for vals in nonogram_values[1]])

        if sum0 == sum1 and sum0 != 0:
            return self.image, nonogram_values
        else:
            return self.image, None
