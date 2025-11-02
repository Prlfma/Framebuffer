import mmap
import sys
import os
import cv2
import numpy as np
import time

def display_opencv_on_framebuffer(image_np, fb_device_path="/dev/fb0"):
    """
    Приймає зображення OpenCV (NumPy array) і відображає його безпосередньо 
    у вказаному пристрої буфера кадру Linux, включаючи підтримку 16bpp (RGB565).
    """
    
    fbN = os.path.basename(fb_device_path)

    # 1. Отримання параметрів дисплея
    try:
        with open(f"/sys/class/graphics/{fbN}/virtual_size", "r") as f:
            w_str, h_str = f.read().strip().split(',')
            w = int(w_str)
            h = int(h_str)
        
        with open(f"/sys/class/graphics/{fbN}/bits_per_pixel", "r") as f:
            bpp = int(f.read().strip())
            
        bytes_per_pixel = bpp // 8
        screen_size_bytes = w * h * bytes_per_pixel

    except Exception as e:
        print(f"Error reading framebuffer info: {e}")
        return False

    # 2. Підготовка зображення OpenCV до потрібного формату
    # Спочатку переконаємося, що розміри зображення відповідають розмірам екрана
    if image_np.shape[0] != h or image_np.shape[1] != w:
        print(f"Resizing image to fit screen dimensions {w}x{h}")
        image_np = cv2.resize(image_np, (w, h), interpolation=cv2.INTER_AREA)

    if bpp == 16:
        # **СПЕЦІАЛЬНА ОБРОБКА ДЛЯ 16-БІТНОГО RGB565**
        
        # Перетворюємо BGR (OpenCV) в RGB
        image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        
        # Ручне пакування пікселів у формат RGB565 (5R 6G 5B)
        # Це виконується за допомогою побітових операцій на масиві NumPy
        
        # Екстрагуємо канали R, G, B (припускаємо 8-бітні значення 0-255)
        R = image_rgb[:, :, 0]
        G = image_rgb[:, :, 1]
        B = image_rgb[:, :, 2]
        
        # Пакування в 16-бітний формат (uint16)
        # R (5 біт) << 11 | G (6 біт) << 5 | B (5 біт)
        # Ми зсуваємо і відсікаємо зайві біти, щоб вони помістилися
        packed_image = ((R >> 3) << 11) | ((G >> 2) << 5) | (B >> 3)
        
        # Перетворення до типу даних uint16 (2 байти)
        framebuffer_data = packed_image.astype(np.uint16)
        
    elif bpp == 24 or bpp == 32:
        # Стандартна обробка для 24/32 bpp
        if bpp == 32 and image_np.shape[2] == 3:
             image_np = cv2.cvtColor(image_np, cv2.COLOR_BGR2BGRA)
        elif bpp == 24 and image_np.shape[2] == 4:
             image_np = cv2.cvtColor(image_np, cv2.COLOR_BGRA2BGR)
             
        framebuffer_data = image_np

    else:
        print(f"Error: Unsupported bpp found: {bpp}.")
        return False

    # 3. Відкриття та мапінг буфера кадру
    try:
        fbdev = open(fb_device_path, mode='r+b')
        # Використовуємо dtype 'uint8' для мапінгу пам'яті незалежно від bpp
        fb_mmap = mmap.mmap(fbdev.fileno(), screen_size_bytes, mmap.MAP_SHARED, mmap.PROT_WRITE)
        
        # 4. Запис даних у буфер кадру
        # Якщо дані 16-бітні, ми перетворюємо їх назад у байти для запису mmap
        if bpp == 16:
            fb_mmap.write(framebuffer_data.tobytes())
        else:
            # Для 24/32 bpp numpy масив вже у правильному байтовому форматі
            framebuffer_np = np.frombuffer(fb_mmap, dtype=np.uint8).reshape((h, w, bytes_per_pixel))
            framebuffer_np[:] = framebuffer_data[:] 

        print(f"Image successfully written to framebuffer ({bpp} bpp mode).")
        
        # 5. Очищення
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
