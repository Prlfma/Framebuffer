import mmap
import sys
import os
import cv2
import numpy as np
import time

def display_opencv_on_framebuffer(image_np, fb_device_path="/dev/fb0"):
    """
    Приймає зображення OpenCV (NumPy array) і відображає його безпосередньо 
    у вказаному пристрої буфера кадру Linux.

    Args:
        image_np (numpy.ndarray): Зображення у форматі BGR або BGRA (OpenCV формат).
        fb_device_path (str): Шлях до пристрою буфера кадру (зазвичай '/dev/fb0').
    """
    
    # 1. Визначаємо ім'я пристрою (наприклад, 'fb0' з '/dev/fb0')
    fbN = os.path.basename(fb_device_path)

    # 2. Отримання параметрів дисплея через sysfs
    try:
        with open(f"/sys/class/graphics/{fbN}/virtual_size", "r") as f:
            w_str, h_str = f.read().strip().split(',')
            w = int(w_str)
            h = int(h_str)
        
        with open(f"/sys/class/graphics/{fbN}/bits_per_pixel", "r") as f:
            bpp = int(f.read().strip())
        
        if bpp not in (24, 32):
            print(f"Warning: Only 24 or 32 bpp supported by this function's logic. Found {bpp}.")
            # 16-бітний BGR565 потребує окремої логіки пакування пікселів.
            # Для простоти, ця функція підтримує лише стандартні BGR/BGRA формати NumPy.
            return False
            
        bytes_per_pixel = bpp // 8
        screen_size_bytes = w * h * bytes_per_pixel

    except FileNotFoundError:
        print(f"Error: Framebuffer device {fb_device_path} or its sysfs entries not found.")
        print("Ensure you are on the console TTY and running with 'sudo'.")
        return False
    except Exception as e:
        print(f"Error reading framebuffer info: {e}")
        return False

    # 3. Перетворення зображення OpenCV у відповідний формат
    # OpenCV може бути 3-канальним (BGR) або 4-канальним (BGRA)
    if bytes_per_pixel == 4 and image_np.shape[2] == 3:
         # Якщо екран очікує RGBA/BGRA, але зображення лише BGR, додаємо альфа-канал
         image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2BGRA)
    elif bytes_per_pixel == 3 and image_np.shape[2] == 4:
         # Якщо екран очікує BGR, але зображення BGRA, видаляємо альфа-канал
         image_np = cv2.cvtColor(image_np, cv2.COLOR_BGRA2BGR)
         
    # Переконайтеся, що розміри зображення відповідають розмірам екрана
    if image_np.shape[0] != h or image_np.shape[1] != w:
        print(f"Resizing image to fit screen dimensions {w}x{h}")
        image_np = cv2.resize(image_np, (w, h), interpolation=cv2.INTER_AREA)

    # 4. Відкриття та мапінг буфера кадру
    try:
        fbdev = open(fb_device_path, mode='r+b')
        fb_mmap = mmap.mmap(fbdev.fileno(), screen_size_bytes, mmap.MAP_SHARED, mmap.PROT_WRITE)
        
        # Створення масиву NumPy, який використовує відображену пам'ять
        framebuffer_np = np.frombuffer(fb_mmap, dtype=np.uint8).reshape((h, w, bytes_per_pixel))
        
        # 5. Копіювання даних зображення у буфер кадру (найшвидший спосіб)
        framebuffer_np[:] = image_np[:] 
        
        print("Image successfully written to framebuffer.")
        
        # 6. Очищення
        fb_mmap.close()
        fbdev.close()
        return True

    except Exception as e:
        print(f"Error accessing framebuffer device {fb_device_path}: {e}")
        return False

# --- Приклад використання ---
if __name__ == "__main__":
    # Створіть тестове зображення OpenCV (наприклад, з текстом)
    screen_width, screen_height = 800, 640 # Припустімо такий розмір екрана
    test_image = np.zeros((screen_height, screen_width, 3), dtype=np.uint8) # 3 канали BGR
    cv2.rectangle(test_image, (100, 100), (924, 668), (255, 0, 0), -1) # Синій прямокутник
    cv2.putText(test_image, "Hello Framebuffer from OpenCV!", (150, 384), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

    # Запустіть функцію для відображення зображення
    # !!! Важливо: Запускайте цей скрипт з 'sudo' у консолі (TTY1) !!!
    success = display_opencv_on_framebuffer(test_image, fb_device_path="/dev/fb0")
    
    if success:
        print("Display successful. Image will remain until screen is redrawn by another process.")
        # Додайте input() або time.sleep() тут, якщо вам потрібна затримка перед завершенням скрипта
        time.sleep(5) 
