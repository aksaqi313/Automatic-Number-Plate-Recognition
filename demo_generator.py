"""
Generate a simple demo image with a sample license plate for testing.
"""

import cv2
import numpy as np
from pathlib import Path

def create_demo_image(output_path: str = "demo_image.jpg"):
    """Create a demo image with a sample license plate."""
    
    # Create a blank image (640x480) with road-like background
    height, width = 480, 640
    image = np.ones((height, width, 3), dtype=np.uint8) * 80  # Gray background
    
    # Add some texture/details to simulate a real street
    # Draw a simple road
    cv2.rectangle(image, (0, 250), (width, height), (100, 100, 100), -1)
    
    # Add lane markings
    for i in range(0, width, 50):
        cv2.line(image, (i, 280), (i + 30, 280), (255, 255, 255), 2)
    
    # Create a simple car shape (rectangle)
    car_x, car_y = 200, 150
    car_width, car_height = 300, 120
    
    # Car body (dark color)
    cv2.rectangle(image, (car_x, car_y), (car_x + car_width, car_y + car_height), 
                  (40, 40, 50), -1)
    
    # Car windows
    cv2.rectangle(image, (car_x + 40, car_y + 20), (car_x + 140, car_y + 60), 
                  (150, 180, 220), -1)
    cv2.rectangle(image, (car_x + 160, car_y + 20), (car_x + 260, car_y + 60), 
                  (150, 180, 220), -1)
    
    # Car wheels
    cv2.circle(image, (car_x + 60, car_y + car_height), 15, (30, 30, 30), -1)
    cv2.circle(image, (car_x + 240, car_y + car_height), 15, (30, 30, 30), -1)
    
    # License plate (white background)
    plate_x, plate_y = car_x + 240, car_y + 85
    plate_width, plate_height = 80, 35
    cv2.rectangle(image, (plate_x, plate_y), (plate_x + plate_width, plate_y + plate_height), 
                  (245, 245, 245), -1)
    
    # Add border to plate
    cv2.rectangle(image, (plate_x, plate_y), (plate_x + plate_width, plate_y + plate_height), 
                  (20, 20, 20), 2)
    
    # Add sample license plate text
    plate_text = "ABC1234"
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1.2
    font_color = (20, 20, 20)  # Dark color for text
    thickness = 2
    
    # Get text size to center it on the plate
    text_size = cv2.getTextSize(plate_text, font, font_scale, thickness)[0]
    text_x = plate_x + (plate_width - text_size[0]) // 2
    text_y = plate_y + (plate_height + text_size[1]) // 2
    
    cv2.putText(image, plate_text, (text_x, text_y), font, font_scale, font_color, thickness)
    
    # Save the image
    cv2.imwrite(output_path, image)
    print(f"✓ Demo image created: {output_path}")
    return output_path


if __name__ == "__main__":
    demo_path = Path(__file__).parent / "demo_images"
    demo_path.mkdir(exist_ok=True)
    create_demo_image(str(demo_path / "sample_plate.jpg"))
