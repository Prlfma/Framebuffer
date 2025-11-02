import mmap
import sys
import os
import cv2
import numpy as np
import time

def display_opencv_on_framebuffer(image_np, fb_device_path="/dev/fb0", packing_mode="RGB565"):
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
        
    except Exception as e:
        # Don't print the error here, to avoid spamming the loop
        return False
    
    # We could print info here, but it would clutter the loop output
    # print(f"Framebuffer: {w}x{h}, BPP: {bpp}")
    
    # Resize image to match framebuffer dimensions
    if image_np.shape[0] != h or image_np.shape[1] != w:
        image_np = cv2.resize(image_np, (w, h), interpolation=cv2.INTER_AREA)
    
    if bpp == 16:
        # Extract color channels and EXPLICITLY CAST to a larger type
        # This prevents the uint8 overflow you found.
        B = image_np[:, :, 0].astype(np.uint32)
        G = image_np[:, :, 1].astype(np.uint32)
        R = image_np[:, :, 2].astype(np.uint32)
        
        # --- Mode selection logic starts here ---
        # All operations are now "safe" within the uint32 type
        
        if packing_mode == "RGB565":
            # Format: RRRRR GGGGGG BBBBB
            packed_image = ((R >> 3) << 11) | ((G >> 2) << 5) | (B >> 3)
        
        elif packing_mode == "BGR565":
            # Format: BBBBB GGGGGG RRRRR
            packed_image = ((B >> 3) << 11) | ((G >> 2) << 5) | (R >> 3)
        
        elif packing_mode == "RGB565_SWAP":
            # RGB565, but with swapped byte order (endianness)
            packed_image = ((R >> 3) << 11) | ((G >> 2) << 5) | (B >> 3)
            # Swap bytes: 0xAABB -> 0xBBAA
            packed_image = ((packed_image & 0xFF) << 8) | ((packed_image & 0xFF00) >> 8)
            
        elif packing_mode == "BGR565_SWAP":
            # BGR565, but with swapped byte order
            packed_image = ((B >> 3) << 11) | ((G >> 2) << 5) | (R >> 3)
            packed_image = ((packed_image & 0xFF) << 8) | ((packed_image & 0xFF00) >> 8)

        elif packing_mode == "RGB555":
            # Format: x RRRRR GGGGG BBBBB (uses 15 bits)
            packed_image = ((R >> 3) << 10) | ((G >> 3) << 5) | (B >> 3)
        
        elif packing_mode == "BGR555":
            # Format: x BBBBB GGGGG RRRRR (uses 15 bits)
            packed_image = ((B >> 3) << 10) | ((G >> 3) << 5) | (R >> 3)
            
        else:
            print(f"Error: Unknown packing mode: {packing_mode}.")
            return False
            
        # Finally, cast the result down to the 16-bit format the framebuffer needs
        framebuffer_data = packed_image.astype(np.uint16)
        
    elif bpp == 24 or bpp == 32:
        # This logic remains unchanged
        if bpp == 32 and image_np.shape[2] == 3:
            image_bgra = np.zeros((image_np.shape[0], image_np.shape[1], 4), dtype=np.uint8)
            image_bgra[:, :, 0] = image_np[:, :, 0]  # B
            image_bgra[:, :, 1] = image_np[:, :, 1]  # G
            image_bgra[:, :, 2] = image_np[:, :, 0]  # R
            image_bgra[:, :, 3] = 255                 # A
            framebuffer_data = image_bgra
        elif bpp == 24 and image_np.shape[2] == 4:
            framebuffer_data = cv2.cvtColor(image_np, cv2.COLOR_BGRA2BGR)
        else:
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
    
    # Create a test image (dimensions can be hardcoded or read from fb)
    try:
        with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
            w_str, h_str = f.read().strip().split(',')
            width = int(w_str)
            height = int(h_str)
    except Exception as e:
        print(f"Warning: Could not read /sys/class/graphics/fb0/virtual_size. Using 800x480. Error: {e}")
        height, width = 480, 800
        
    test_image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Define color regions (in BGR order for OpenCV)
    test_image[:, :width//3] = (255, 0, 0)        # Blue (left third)
    test_image[:, width//3:2*width//3] = (0, 255, 0)  # Green (middle third)  
    test_image[:, 2*width//3:] = (0, 0, 255)      # Red (right third)
    
    print("--- Testing 16-bit color packing modes ---")
    print(f"Expected result: [BLUE] [GREEN] [RED]")
    print("Find the mode that shows the colors correctly.")
    print("Press Ctrl+C to stop the test.")

    packing_modes = [
        "RGB565", 
        "BGR565", 
        "RGB565_SWAP", 
        "BGR565_SWAP",
        "RGB555",
        "BGR555"
    ]
    
    try:
        while True:
            for mode in packing_modes:
                # \r (carriage return) makes the console update the line in-place
                print(f" Current mode: {mode.ljust(15)}", end="\r")
                success = display_opencv_on_framebuffer(test_image, "/dev/fb0", mode)
                
                if not success:
                    print("\nDisplay error. Check permissions (sudo?) or bpp.")
                    raise KeyboardInterrupt # Exit loop if display failed
                
                time.sleep(1) # Wait 1 second, as you requested
                
    except KeyboardInterrupt:
        print("\n\nTest stopped by user.")
        
    finally:
        # Always restore the cursor and clear the screen on exit
        os.system("setterm -cursor on")
        os.system("clear")
        print("Terminal settings restored.")