from tkinter import Tk, Label, Button, Scale, HORIZONTAL
import ctypes
import os
import hashlib
import sqlite3
from PIL import Image
import numpy as np
from threading import Timer

class WallpaperChanger:
    def __init__(self, master):
        self.master = master
        master.title("Wallpaper Changer")

        self.label = Label(master, text="Click to change wallpaper!")
        self.label.pack()

        self.change_wallpaper_button = Button(master, text="Change Wallpaper", command=self.get_wallpaper)
        self.change_wallpaper_button.pack()

        self.rating = Scale(master, from_=0, to=10, length=450, tickinterval=1, orient=HORIZONTAL)
        self.rating.pack()

        self.rate_button = Button(master, text="Rate Image", command=self.rate_image)
        self.rate_button.pack()

        self.close_button = Button(master, text="Close", command=master.quit)
        self.close_button.pack()

        self.db_conn = sqlite3.connect('image_db.sqlite')
        self.cursor = self.db_conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS images (hash text, avg_color text, rating int)')

        self.image_data = None
        self.schedule_wallpaper_change()

    def get_wallpaper(self):
        # Generate the image data
        self.image_data = self.generate_image()

        # Calculate the hash of the image
        image_hash = hashlib.sha256(self.image_data.tobytes()).hexdigest()

        # Save the image to a file
        img = Image.fromarray(self.image_data, 'RGB')
        img.save('wallpaper.jpg')

        # Set the image as wallpaper
        if os.name == 'nt':  # If the system is windows
            ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath('wallpaper.jpg'), 3)

    def rate_image(self):
        if self.image_data is not None:
            image_hash = hashlib.sha256(self.image_data.tobytes()).hexdigest()
            avg_color = np.mean(self.image_data, axis=(0, 1)).tolist()
            rating = self.rating.get()
            self.cursor.execute('INSERT INTO images VALUES (?, ?, ?)', (image_hash, str(avg_color), rating))
            self.db_conn.commit()

    def generate_image(self):
        # Bias the generation towards the colors of the most highly rated images
        self.cursor.execute('SELECT avg_color FROM images WHERE rating >= 8')
        favored_colors = [eval(row[0]) for row in self.cursor.fetchall()]
        bias = np.mean(favored_colors, axis=0) if favored_colors else [128, 128, 128]

        # Generate the image with the bias
        return np.clip(np.random.normal(loc=bias, scale=64, size=(800, 600, 3)), 0, 255).astype(np.uint8)

    def schedule_wallpaper_change(self):
        self.get_wallpaper()
        self.timer = Timer(300, self.schedule_wallpaper_change)
        self.timer.start()

root = Tk()
my_gui = WallpaperChanger(root)
root.mainloop()
