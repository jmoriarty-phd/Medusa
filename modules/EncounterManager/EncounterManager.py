"""
author: JGMonroe
date version notes
20200809 1.0.0 Initial release
"""
import csv
import os
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tkinter as tk


class EncounterPrep:
    @staticmethod
    def get_encounter_csv(multi_criteria='mod') -> str or None:
        """
        Looks for csv files in current directory that start with '@'. Returns path to file.
        If there are more than 1, will return file that was most recently modified if
        multi_criteria='mod' or one with highest number after @ if multi_criteria='num'.
        Assumes file name is of form, e.g., @KoboldAmbush.csv or @_1_KoboldAmbush.csv.
        Inside csv file shoudl be 2 columns; the first column is the source image name
        (without file extension), and the second column is the initiative of the character.
        A third column with dex is optional in case of tied initiative.
        Returns None if can't find a file.
        :param multi_criteria: how to choose what encounter file to use if multiple exist.
        :return: path to current encounter csv or None is not found.
        """
        look_dir = os.getcwd()
        cwd_files = [f for f in os.listdir(look_dir) if os.path.isfile(os.path.join(look_dir, f))]
        start_csv = [f for f in cwd_files if (os.path.basename(f)[0] == '@') and (os.path.basename(f)[-3:] == 'csv')]
        if len(start_csv) == 1:
            return start_csv[0]
        elif len(start_csv) == 0:
            pass
        else:
            assert type(multi_criteria) is str
            assert multi_criteria.lower() in ['num', 'mod']
            if multi_criteria.lower() == 'num':
                try:
                    start_csvs = [[f, int(os.path.basename(f).split('_')[1])] for f in start_csv
                                  if len(os.path.basename(f).split('_')) == 3]
                    if len(start_csvs) == 0:
                        multi_criteria = 'mod'
                    else:
                        start_csvs.sort(key=lambda x: x[1], reverse=True)
                        return start_csvs[0][0]
                except ValueError:  # couldn't convert into int
                    multi_criteria = 'mod'
            if multi_criteria.lower() == 'mod':
                start_csvs = [[f, os.path.getmtime(f)] for f in start_csv]
                start_csvs.sort(key=lambda x: x[1], reverse=True)
                return start_csvs[0][0]
        return None

    @staticmethod
    def get_encounter_order(csv_criteria='mod') -> tuple:
        """
        Using encounter csv, will calculate the correct turn order.
        :param csv_criteria: how to choose what encounter file to use if multiple exist.
        :return: tuple of names in correct turn order
        """
        # todo: add option where initiative will be automatically rolled if missing and given dex
        encounter_csv = EncounterPrep.get_encounter_csv(multi_criteria=csv_criteria)
        if encounter_csv is None:
            raise Exception('Could not find an encounter file.')
        with open(encounter_csv, newline='', mode='r') as f:
            data = list(csv.reader(f))
            if len(data[0]) == 3:
                data = [[c[0], int(c[1]), int(c[2])] if c[2] != '' else [c[0], c[1], 0] for c in data]
                data.sort(key=lambda x: int(x[2]), reverse=True)
            else:
                data = [[c[0], int(c[1])] for c in data]
        data.sort(key=lambda x: int(x[1]), reverse=True)
        return tuple(c[0] for c in data)

    @staticmethod
    def get_source_images(look_dir) -> tuple:
        """
        Returns tuple of paths of image files ('.jpeg', '.jpg', '.png') in a specified directory
        :param look_dir: where to look for images
        :return: image paths
        """
        source_files = [f for f in os.listdir(look_dir) if os.path.isfile(os.path.join(look_dir, f))]
        source_images = [os.path.join(look_dir, f) for f in source_files
                         if os.path.splitext(f)[1].lower() in ['.jpeg', '.jpg', '.png']]
        return tuple(source_images)

    @staticmethod
    def get_encounter_images(csv_criteria='mod') -> tuple:
        """
        Returns list of images base on encounter order from encounter csv. If a name in encounter order
        has no match in source images, will have [name].NAME instead of path.
        E.g., ('Harold.NAME', '.\\SourceImages\\Laserie.png', ...)
        :param csv_criteria: how to choose what encounter file to use if multiple exist.
        :return: encounter images or names in correct turn order
        """
        encounter_order = EncounterPrep.get_encounter_order(csv_criteria=csv_criteria)
        look_dir = os.path.join(os.getcwd(), 'SourceImages')
        source_images = EncounterPrep.get_source_images(look_dir)
        encounter_images = []
        for c in encounter_order:
            for i, img in enumerate(source_images):
                if c in os.path.basename(img):
                    encounter_images.append(img)
                    break
                elif i + 1 == len(source_images):  # didn't find match, use text name instead of image
                    encounter_images.append(str(c) + '.NAME')
        return tuple(encounter_images)

    @staticmethod
    def make_source_images_summary(look_dir) -> None:
        """
        Make csv file with names of all images (ignores file extension) in source directory
        """
        source_images = EncounterPrep.get_source_images(look_dir)
        with open(os.path.join(look_dir, '_SourceImagesSummary.csv'), 'w', newline='\n') as summary:
            writer = csv.writer(summary)
            for img in source_images:
                writer.writerow([os.path.splitext(img)[0]])

    @staticmethod
    def get_manager_config():
        """
        looks for config csv file with e.g.
        size_xy,600
        mins,1
        secs,30
        :return: dict of parameters. Returns default values if config csv not found
        """
        try:
            with open('manager_config.csv', newline='', mode='r') as f:
                data = list(csv.reader(f))
            data_dict = {r[0]: int(r[1]) for r in data}
            return data_dict
        except FileNotFoundError:
            return {'size_xy': 600, 'mins': 1, 'secs': 30}


class EncounterWindow(tk.Canvas):
    def __init__(self, master, mins=1, secs=30, size_xy=600):
        # from https://www.bitforestinfo.com/2017/02/how-to-create-image-viewer-using-python.html?m=1
        tk.Canvas.__init__(self, master)
        self.imagelist = list(EncounterPrep.get_encounter_images())
        self._max_img_idx = len(self.imagelist) - 1
        self._img_idx = -1
        self._size_xy = size_xy  # will be square window
        self._create_image_buttons()
        self.image = None

        self.master.title(" Encounter Manager")
        self.master.resizable(width=0, height=0)  # Not Resizable
        self._set_window_location()

        self.state = False
        self.minutes = mins  # stores original time for reset
        self.seconds = secs  # stores original time for reset
        self.mins = mins  # used to update time
        self.secs = secs  # used to update time
        self.display = None
        self.font_config = ("Courier", 24, 'bold')

        self._first_pass = True  # track if first time going forward

    @classmethod
    def run(cls, mins=1, secs=30, size_xy=600):
        root = tk.Tk()  # Creating Window

        # Creating Canvas Widget
        encounter = cls(root, mins=mins, secs=secs, size_xy=size_xy)
        encounter.pack(expand="yes", fill="both")

        root.mainloop()  # Window Mainloop

    def _set_window_location(self):
        ws = self.master.winfo_screenwidth()  # width of the screen
        hs = self.master.winfo_screenheight()  # height of the screen
        x = ws - self._size_xy - 10
        y = hs - self._size_xy - 25
        self.master.geometry('%dx%d+%d+%d' % (self._size_xy, self._size_xy, x, y))

    def _create_image_buttons(self):
        tk.Button(self, text=" > ", command=self.next_image).place(x=self._size_xy-40, y=int(self._size_xy/2))
        tk.Button(self, text=" < ", command=self.previous_image).place(x=20, y=int(self._size_xy/2))
        return

    def _create_timer_buttons(self):
        # see http://www.tcl.tk/man/tcl8.6/TkCmd/colors.htm for colors
        y_pos = self._size_xy-35
        x_pos = [self._size_xy - 47 * i - 10 for i in range(1, 4)]
        tk.Button(self, text="Reset", bg="light blue", height=1, width=5,
                  command=self.reset_timer).place(x=x_pos[2], y=y_pos)
        tk.Button(self, text="Start", bg="light green", height=1, width=5,
                  command=self.start).place(x=x_pos[1], y=y_pos)
        tk.Button(self, text="Pause", bg="light goldenrod", height=1, width=5,
                  command=self.pause).place(x=x_pos[0], y=y_pos)

    def _config_timer(self):
        self.display = tk.Label(self, height=1, width=7, textvariable="")
        self.display.place(x=self._size_xy-13, y=self._size_xy-36, anchor='se')
        self._create_timer_buttons()
        self._update_timer()

    def _update_timer(self, color='white'):
        self.display.config(text="%02d:%02d" % (self.mins, self.secs), bg=color, font=self.font_config)

    def _countdown(self):
        """Displays a clock starting at min:sec to 00:00, ex: 25:00 -> 00:00"""
        if self.state:
            if (self.mins == 0) and (10 < self.secs <= 30):
                color = 'yellow'
            elif (self.mins == 0) and (self.secs <= 10):
                color = 'red'
            else:
                color = 'white'

            if (self.mins == 0) and (self.secs == 0):
                self.display.config(text="--:--", background='red')
                self.state = False
            else:
                self._update_timer(color=color)
                if self.secs == 0:
                    self.mins -= 1
                    self.secs = 59
                else:
                    self.secs -= 1
                self.master.after(1000, self._countdown)

    def _tk_image(self, path):
        if '.NAME' not in path:
            img = Image.open(path)
            img = img.resize((self._size_xy, self._size_xy))
            return ImageTk.PhotoImage(img)
        else:
            img = Image.new('RGB', (750, 750), color=(73, 109, 137))
            fnt = ImageFont.truetype('Fonts/DUNGRG.TTF', 150)
            d = ImageDraw.Draw(img)
            name = path[0:-5]
            x_pos = 375 - int(len(name) * (375-240)/6)
            d.text((x_pos, 290), name, font=fnt, fill=(255, 255, 255))
            img = img.resize((self._size_xy, self._size_xy))
            return ImageTk.PhotoImage(img)

    def _show_image(self, path):
        self.image = self._tk_image(path)
        self.delete(self.find_withtag("bacl"))
        self.create_image(int(self._size_xy / 2), int(self._size_xy / 2),
                          image=self.image, anchor='center', tag="bacl")
        self.master.title(" Encounter Manager:{}{}".format(' ' * 3,
                                                           os.path.splitext(os.path.basename(path))[0]))
        return

    def reset_timer(self):
        self.mins = self.minutes
        self.secs = self.seconds
        self.state = False
        self._update_timer()

    def start(self):
        if not self.state:
            self.state = True
            self._countdown()

    def pause(self):
        if self.state:
            self.state = False

    def previous_image(self):
        if self._img_idx == -1:
            pass
        else:
            if self._img_idx == 0:
                self._img_idx = self._max_img_idx + 1
            self._img_idx -= 1
            self._show_image(self.imagelist[self._img_idx])
            self.reset_timer()
        return

    def next_image(self):
        if self._first_pass:  # make time label on first time forward
            self._config_timer()
            self._first_pass = False
        if self._img_idx == self._max_img_idx:
            self._img_idx = -1
        self._img_idx += 1
        self._show_image(self.imagelist[self._img_idx])
        self.reset_timer()
        return


# Main Function Trigger
if __name__ == '__main__':
    params = EncounterPrep.get_manager_config()
    EncounterWindow.run(mins=params['mins'], secs=params['secs'], size_xy=params['size_xy'])
