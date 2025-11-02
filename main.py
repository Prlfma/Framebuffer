import cv2
import os
import sys
import time
# Import your function from the other file
from display_image import display_opencv_on_framebuffer



def main():
    test_image = np.ones((height, width, 3), dtype=np.uint8) * 255
    section_width = width // 3
    test_image[:, :section_width] = (255, 0, 0)        # Яскраво синій
    test_image[:, section_width:2*section_width] = (0, 255, 0)  # Яскраво зелений
    test_image[:, 2*section_width:] = (0, 0, 255)
    display_opencv_on_framebuffer(test_image)

if __name__ == "__main__":
    main()

