import json
import numpy as np
import matplotlib.pyplot as plt
from re import sub


class SchedulePlotter:
    def __init__(self, save_image=False, schedule_data=None):
        """Initialize the SchedulePlotter with optional schedule data."""
        self.save_image = save_image
        self.schedule_data = schedule_data

    @staticmethod
    def snake_case(s):
        """Convert a string to snake_case."""
        return '_'.join(
            sub('([A-Z][a-z]+)', r' \1',
            sub('([A-Z]+)', r' \1',
            s.replace('-', ' '))).split()).lower()

    @staticmethod
    def time_to_angle(time_str):
        """Convert a time string (HHMM) to an angle in radians."""
        hours = int(time_str[:2])
        minutes = int(time_str[2:])
        total_minutes = hours * 60 + minutes
        return (total_minutes / 1440) * 2 * np.pi  # 1440 minutes in a day

    @staticmethod
    def duration_str(interval):
        """Convert two HHMM strings to a duration string in the format %d%dh%d%dm."""
        start_h, start_m = int(interval["start"][:2]), int(interval["start"][2:])
        end_h, end_m = int(interval["end"][:2]), int(interval["end"][2:])

        start_total_minutes = start_h * 60 + start_m
        end_total_minutes = end_h * 60 + end_m

        if end_total_minutes < start_total_minutes:
            end_total_minutes += 24 * 60

        duration_minutes = end_total_minutes - start_total_minutes
        dur_h = duration_minutes // 60
        dur_m = duration_minutes % 60

        return f"{dur_h}h{dur_m:02d}m"

    def plot_schedule(self, title, schedule):
        """Plot a clock plot for the given schedule."""
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8), facecolor='darkgrey')

        ax.set_theta_direction(-1)           # Clockwise
        ax.set_theta_offset(np.pi/2)         # 0 (midnight) at the top
        ax.set_xticklabels([])               # Remove degree (theta) axis labels

        arc_radius = 1
        arc_thickness = 36
        
        for interval in schedule:
            # Set the beginning and end arc angles based on the time
            start_angle = self.time_to_angle(interval["start"])
            end_angle = self.time_to_angle(interval["end"])

            # Handle if time goes past midnight
            if end_angle <= start_angle:
                end_angle += 2 * np.pi

            # Arc calculations
            theta = np.linspace(start_angle, end_angle, 200)
            r = np.full_like(theta, arc_radius)
            ax.plot(theta, r, color=interval["color"], linewidth=arc_thickness, solid_capstyle='butt', label=interval["id"])

            # Calculate middle angle for labelling
            mid_angle = (start_angle + end_angle) / 2.0 % (2 * np.pi)
            text_rot = (270 - np.degrees(mid_angle)) % 360
            
            # Flip if on left half for readability
            if 90 <= text_rot <= 270:
                text_rot += 180

            # Place activity label
            ax.text(mid_angle, arc_radius, interval["id"], ha='center', va='center',
                    fontsize=10, color='white', 
                    bbox=dict(facecolor=interval["color"], edgecolor='white', boxstyle='round,pad=0.2'))

            # Place duration label
            ax.text(mid_angle, arc_radius - 0.30, self.duration_str(interval), ha='center', va='center',
                    fontsize=8, color='white', rotation=text_rot, 
                    bbox=dict(facecolor="grey", edgecolor='none', boxstyle='round,pad=0.2'))

        # Plot intersection labels
        marker_times = set()
        for interval in schedule:
            marker_times.add(interval["start"])
            marker_times.add(interval["end"])

        intersection_radius = 1.15
        for time_str in sorted(marker_times):
            # If on an hour mark, skip to be plotted as a tick later
            if int(time_str[2:]) == 0:
                continue

            angle = self.time_to_angle(time_str)
            text_rot = (270 - np.degrees(angle)) % 360
            if 90 <= text_rot <= 270:
                text_rot += 180

            time_str = time_str[:2] + ':' + time_str[2:]
            ax.plot(angle, intersection_radius + 0.05, marker='o', markersize=4, color='black', alpha=1)
            ax.text(angle, intersection_radius + 0.15, time_str, rotation=text_rot, ha='center', va='center',
                    fontsize=8, color="black",
                    bbox=dict(facecolor="none", edgecolor='none', boxstyle='round,pad=0.2'))

        # Plot hour labels and ticks
        tick_inner = 1.17
        tick_outer = 1.25
        for hour in range(24):
            angle = self.time_to_angle(f"{hour:02d}00")
            ax.plot([angle, angle], [tick_inner, tick_outer], color='black', lw=2)
            ax.text(angle, tick_outer + 0.05, f"{hour:02d}", ha='center', va='center', fontsize=8)

        ax.set_yticklabels([])
        ax.set_ylim(0, 1.4)
        plt.title(title, fontsize=14)

        # Save image if set, then plot
        if self.save_image:
            filename = f"results/{self.snake_case(title)}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f'Saved clock plot to PNG at {filename}.')
            
        plt.show()

    def load_schedule_data(self, file_path):
        """Load schedule data from a JSON file."""
        with open(file_path, 'r', encoding='UTF-8') as f:
            self.schedule_data = dict()
            [self.schedule_data.update({schedule['title']: schedule['intervals']}) for schedule in json.load(f)['schedule_patterns']]

    def plot_all_schedules(self):
        """Plot all schedules."""
        for i, schedule in enumerate(self.schedule_data):
            print(f'Plotting {i+1} of {len(self.schedule_data)}')
            self.plot_schedule(schedule, self.schedule_data[schedule])
        

    def plot_one_schedule(self, schedule_title):
        """Plot single specified schedule."""
        if schedule_title in self.schedule_data:
            print('Plotting 1 of 1')
            self.plot_schedule(schedule_title, self.schedule_data[schedule_title])

if __name__ == "__main__":
    plotter = SchedulePlotter(True)
    plotter.load_schedule_data(file_path='config.json')
    plotter.plot_one_schedule('Night shift')
    # plotter.plot_all_schedules()
    