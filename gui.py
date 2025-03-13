import json
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QLabel,
                             QColorDialog, QComboBox, QFileDialog)
from PyQt6.QtGui import QColor
from schedule_spreadsheet_generator import SheetScheduler
from clock_plot import SchedulePlotter

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='UTF-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"workdays": [], "prev_week_night": False, "next_week_night": False, "colors": {}}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='UTF-8') as f:
        json.dump(data, f, indent=4)

class WorkScheduleApp(QWidget):
    def __init__(self):
        super().__init__()

        self.config = load_config()

        main_layout = QVBoxLayout()

        # Workdays and Colors Section (Side by Side)
        workdays_colors_layout = QHBoxLayout()

        # Workdays Section
        workdays_layout = QVBoxLayout()
        workdays_layout.addWidget(QLabel("Select Workdays:"))
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.day_checkboxes = {day: QCheckBox(day) for day in self.days}
        for day, checkbox in self.day_checkboxes.items():
            workdays_layout.addWidget(checkbox)

        workdays_colors_layout.addLayout(workdays_layout)

        # Colors Section
        colors_layout = QVBoxLayout()
        colors_layout.addWidget(QLabel("Select Colors:"))
        self.color_selectors = {}
        for category in ["awake", "asleep", "commute", "work"]:
            btn = QPushButton(f"Select {category.capitalize()} Color")
            btn.clicked.connect(lambda _, c=category: self.select_color(c))
            self.color_selectors[category] = btn
            colors_layout.addWidget(btn)

        workdays_colors_layout.addLayout(colors_layout)

        main_layout.addLayout(workdays_colors_layout)

        # Previous/Next Week Night Checkboxes
        self.prev_week_night = QCheckBox("Previous Week Night")
        self.next_week_night = QCheckBox("Next Week Night")
        main_layout.addWidget(self.prev_week_night)
        main_layout.addWidget(self.next_week_night)

        # Clock Plot and Dynamic Schedule Section (Side by Side)
        plot_schedule_layout = QHBoxLayout()

        # Generate Clock Plot Section
        clock_plot_layout = QVBoxLayout()
        clock_plot_layout.addWidget(QLabel("Generate Clock Plot:"))
        self.clock_plot_dropdown = QComboBox()
        self.clock_plot_dropdown.addItems(["Night shift", "Off day (Night → Night)", "Off day (Night → Off)",
                                           "Off day (Off → Night)", "Off day (Off → Off)"])
        clock_plot_layout.addWidget(self.clock_plot_dropdown)

        self.clock_plot_save_image = QCheckBox("Save Image")
        clock_plot_layout.addWidget(self.clock_plot_save_image)

        clock_plot_btn = QPushButton("Run")
        clock_plot_btn.clicked.connect(self.run_clock_plot)
        clock_plot_layout.addWidget(clock_plot_btn)

        plot_schedule_layout.addLayout(clock_plot_layout)

        # Generate Dynamic Schedule Section
        dynamic_schedule_layout = QVBoxLayout()
        dynamic_schedule_layout.addWidget(QLabel("Generate Dynamic Schedule:"))
        self.dynamic_schedule_save_image = QCheckBox("Save Image")
        dynamic_schedule_layout.addWidget(self.dynamic_schedule_save_image)

        dynamic_schedule_btn = QPushButton("Run")
        dynamic_schedule_btn.clicked.connect(self.run_dynamic_schedule)
        dynamic_schedule_layout.addWidget(dynamic_schedule_btn)

        plot_schedule_layout.addLayout(dynamic_schedule_layout)

        main_layout.addLayout(plot_schedule_layout)

        # Save and Exit Buttons
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        main_layout.addWidget(save_btn)

        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.close)
        main_layout.addWidget(exit_btn)

        self.setLayout(main_layout)
        self.load_settings()

    def load_settings(self):
        for day, checkbox in self.day_checkboxes.items():
            checkbox.setChecked(day in self.config.get("workdays", []))

        self.prev_week_night.setChecked(self.config.get("prev_week_night", False))
        self.next_week_night.setChecked(self.config.get("next_week_night", False))

        for category, color in self.config.get("colors", {}).items():
            if category in self.color_selectors:
                self.set_button_color(self.color_selectors[category], QColor(color))

    def save_settings(self):
        self.config["workdays"] = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
        self.config["prev_week_night"] = self.prev_week_night.isChecked()
        self.config["next_week_night"] = self.next_week_night.isChecked()
        self.config["colors"] = {category: self.color_selectors[category].palette().button().color().name() for category in self.color_selectors}
        save_config(self.config)

    def select_color(self, category):
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_button_color(self.color_selectors[category], color)

    def set_button_color(self, button, color):
        button.setStyleSheet(f"background-color: {color.name()};")

    def run_clock_plot(self):
        option = self.clock_plot_dropdown.currentText()
        save_image = self.clock_plot_save_image.isChecked()
        print(f"Running Clock Plot: {option}, Save Image: {save_image}")
        scheduler = SchedulePlotter(save_image)
        scheduler.load_schedule_data(file_path='config.json')
        scheduler.plot_one_schedule(option)

    def run_dynamic_schedule(self):
        save_image = self.dynamic_schedule_save_image.isChecked()
        print(f"Running Dynamic Schedule, Save Image: {save_image}")
        scheduler = SheetScheduler('config.json')
        scheduler.display_schedule()
        scheduler.plot_schedule()
        scheduler.save_to_csv()
        if save_image:
            scheduler.save_to_csv()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WorkScheduleApp()
    window.show()
    sys.exit(app.exec())
