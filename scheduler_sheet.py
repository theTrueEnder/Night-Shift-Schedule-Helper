import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

class SheetScheduler:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.time_slots = [f"{h:02}:{m:02}" for h in range(24) for m in (0, 30)]
        self.days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.config = self.load_config()
        self.schedule_patterns = self.generate_schedule_patterns()
        self.day_categories = {day: self.get_day_category(day) for day in self.days_of_week}
        self.schedule = pd.DataFrame({day: self.schedule_patterns[self.day_categories[day]] for day in self.days_of_week}, index=self.time_slots)
        self.activity_colors = self.get_activity_colors()

    def load_config(self):
        """Load configuration from a JSON file."""
        with open(self.config_path, 'r', encoding='UTF-8') as f:
            config = json.load(f)
        assert config, "Error: config.json not found."
        return config

    def generate_activity_list(self, intervals):
        """Create a 48-slot activity list based on defined intervals."""
        def time_to_index(time):
            hours, minutes = int(time[:2]), int(time[2:])
            return (hours * 60 + minutes) // 30

        activity_list = ["empty"] * 48

        for interval in intervals:
            start_index = time_to_index(interval["start"])
            end_index = time_to_index(interval["end"])

            if end_index <= start_index:
                end_index += 48

            for i in range(start_index, end_index):
                activity_list[i % 48] = interval["id"]

        return activity_list

    def generate_schedule_patterns(self):
        """Generate schedule patterns from the configuration."""
        patterns = {
            schedule['title']: self.generate_activity_list(schedule['intervals'])
            for schedule in self.config['schedule_patterns']
        }
        assert all(len(pattern) == 48 for pattern in patterns.values()), "Error: Incorrect pattern length."
        return patterns

    def get_day_category(self, day):
        """Determine the category of a given day based on workdays and transitions."""
        # If a work day
        if day in self.config['workdays']:
            previous_day = {
                "Monday": "Sunday",
                "Tuesday": "Monday",
                "Wednesday": "Tuesday",
                "Thursday": "Wednesday",
                "Friday": "Thursday",
                "Saturday": "Friday",
                "Sunday": "prev_week_night"  # Special case for Sunday
            }

            # Determine if the previous "work night" applies
            if previous_day[day] == "prev_week_night":
                previous_work_night = self.config.get("prev_week_night", False)
            else:
                previous_work_night = previous_day[day] in self.config['workdays']

            if previous_work_night:
                return "Night shift (Night-Any)"
            else:
                return "Night shift (Off-Any)"

        # If a day off
        else:
            day_idx = self.days_of_week.index(day)
            prev_day = self.days_of_week[day_idx - 1]
            next_day = self.days_of_week[(day_idx + 1) % 7]

            prev_night = self.config['prev_week_night'] if day == "Sunday" else prev_day in self.config['workdays']
            next_night = self.config['next_week_night'] if day == "Saturday" else next_day in self.config['workdays']

            if prev_night and next_night:
                return "Off day (Night-Night)"
            elif prev_night:
                return "Off day (Night-Off)"
            elif next_night:
                return "Off day (Off-Night)"
            else:
                return "Off day (Off-Off)"

    def get_activity_colors(self):
        """Extract activity colors from the configuration."""
        return self.config['colors']

    def display_schedule(self):
        """Print the generated schedule."""
        print(self.schedule)

    def save_to_csv(self, filename="results/dynamic_schedule.csv"):
        """Save the schedule to a CSV file."""
        self.schedule.to_csv(filename)
        print(f'Saved dynamic schedule to CSV at {filename}.')

    def save_to_png(self, filename="results/dynamic_schedule.png"):
        """Save the plotted schedule to a PNG file."""
        self.plot_schedule(save_path=filename)
        print(f'Saved dynamic schedule to PNG at {filename}.')

    def plot_schedule(self, save_path=None):
        """Visualize the schedule using a heatmap."""
        plt.figure(figsize=(12, 8), facecolor='darkgrey')

        for day_idx, day in enumerate(self.days_of_week):
            current_activity = None
            start_time = 0

            for time_idx, activity in enumerate(self.schedule[day]):
                if activity != current_activity:
                    if current_activity is not None:
                        plt.fill_between([day_idx, day_idx + 1], start_time, time_idx, color=self.activity_colors[current_activity])
                        plt.text(day_idx + 0.5, (start_time + time_idx) / 2, current_activity, ha="center", va="center", fontsize=12, color="white",
                                 bbox=dict(facecolor=self.activity_colors[current_activity], edgecolor='none', boxstyle='round,pad=0.11'))
                    current_activity = activity
                    start_time = time_idx

            plt.fill_between([day_idx, day_idx + 1.5], start_time, len(self.time_slots), color=self.activity_colors[current_activity])
            plt.text(day_idx + 0.5, (start_time + len(self.time_slots)) / 2, current_activity, ha="center", va="center", fontsize=12, color="white",
                     bbox=dict(facecolor=self.activity_colors[current_activity], edgecolor='none', boxstyle='round,pad=0.2'))

        # Add day category labels
        for day_idx, day in enumerate(self.days_of_week):
            plt.text(day_idx + 0.5, -0.7, self.day_categories[day], color="black", ha="center", fontsize=7, fontweight="bold")

        plt.yticks(np.arange(len(self.time_slots)), self.time_slots, fontsize=8)
        plt.xticks(np.arange(7) + 0.5, self.days_of_week)
        plt.gca().invert_yaxis()

        for x in range(1, 7):
            plt.axvline(x, color='black', linewidth=2)

        for y in range(len(self.time_slots)):
            plt.axhline(y, color='black', linestyle='dotted', linewidth=0.5)

        for y in range(0, len(self.time_slots), 2):
            plt.axhline(y, color='black', linewidth=1)

        plt.gca().set_xlim(0, 7)
        plt.ylim(len(self.time_slots), -2)  # Add white row at the top
        plt.title("Night Shift Weekly Schedule")
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

if __name__ == "__main__":
    scheduler = SheetScheduler('config-files/example-config.json')
    scheduler.display_schedule()
    scheduler.plot_schedule()
    scheduler.save_to_png()
    scheduler.save_to_csv()