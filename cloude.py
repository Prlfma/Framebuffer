import mmap
import sys
import os
import cv2
import numpy as np
import time

def display_opencv_on_framebuffer(image_np, fb_device_path="/dev/fb0"):
    fbN = os.path.basename(fb_device_path)
    try:
        with open(f"/sys/class/graphics/{fbN}/virtual_size", "r") as f:
            w_str, h_str = f.read().strip().split(',')
            w = int(w_str)
            h = int(h_str)
        with open(f"/sys/class/graphics/{fbN}/bits_per_pixel", "r") as f:
            bpp = int(f.read().strip())
        bytes_per_pixel = bpp // 8
        screen_size_bytes = w * h * bytes_per_pixel
        
        # Діагностика
        print(f"Framebuffer: {w}x{h}, {bpp} bpp")
        
    except Exception as e:
        print(f"Error reading framebuffer info: {e}")
        return False
    
    if image_np.shape[0] != h or image_np.shape[1] != w:
        image_np = cv2.resize(image_np, (w, h), interpolation=cv2.INTER_AREA)
    
    if bpp == 16:
        B = image_np[:, :, 0]
        G = image_np[:, :, 1]
        R = image_np[:, :, 2]
        
        # Спробуємо без byteswap
        packed_image = ((R >> 3) << 11) | ((G >> 2) << 5) | (B >> 3)
        framebuffer_data = packed_image.astype(np.uint16)
        # framebuffer_data.byteswap(inplace=True)  # Закоментовано
        
    elif bpp == 24 or bpp == 32:
        if bpp == 32 and image_np.shape[2] == 3:
            # Можливо треба RGBA замість BGRA
            image_bgra = np.zeros((image_np.shape[0], image_np.shape[1], 4), dtype=np.uint8)
            image_bgra[:, :, 0] = image_np[:, :, 2]  # R
            image_bgra[:, :, 1] = image_np[:, :, 1]  # G
            image_bgra[:, :, 2] = image_np[:, :, 0]  # B
            image_bgra[:, :, 3] = 255                 # A
            image_np = image_bgra
        elif bpp == 24 and image_np.shape[2] == 4:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_BGRA2BGR)
        framebuffer_data = image_np
    else:
        print(f"Error: Unsupported bpp found: {bpp}.")
        return False
    
    try:
        fbdev = open(fb_device_path, mode='r+b')
        fb_mmap = mmap.mmap(fbdev.fileno(), screen_size_bytes, mmap.MAP_SHARED, mmap.PROT_WRITE)
        
        if bpp == 16:
            fb_mmap.write(framebuffer_data.tobytes())
        else:
            framebuffer_np = np.frombuffer(fb_mmap, dtype=np.uint8).reshape((h, w, bytes_per_pixel))
            framebuffer_np[:] = framebuffer_data[:] 
        
        fb_mmap.close()
        fbdev.close()
        return True
    except Exception as e:
        print(f"Error accessing framebuffer device {fb_device_path}: {e}")
        return False

if __name__ == "__main__":
    os.system("setterm -cursor off")
    os.system("clear")
    
    test_image = np.zeros((200, 300, 3), dtype=np.uint8)
    # BGR формат
    test_image[:, :100] = (0, 0, 255)      # Червоний
    test_image[:, 100:200] = (0, 255, 0)   # Зелений  
    test_image[:, 200:] = (255, 0, 0)      # Голубий
    
    success = display_opencv_on_framebuffer(test_image, fb_device_path="/dev/fb0")
    
    if success:
        time.sleep(5) 
    
    os.system("setterm -cursor on")
    os.system("clear")