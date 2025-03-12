import json
import numpy as np
import matplotlib.pyplot as plt
from re import sub

# Function obtained from https://www.w3resource.com/python-exercises/string/python-data-type-string-exercise-97.php
def snake_case(s):
    """Function that uses regex to convert a given string to snake case

    Args:
        s (str): String to be converted to snake case

    Returns:
        str: Snake case string
    """
    
    # Replace hyphens with spaces, then apply regular expression substitutions for title case conversion
    # and add an underscore between words, finally convert the result to lowercase
    return '_'.join(
        sub('([A-Z][a-z]+)', r' \1',
        sub('([A-Z]+)', r' \1',
        s.replace('-', ' '))).split()).lower()


def time_to_angle(time_str):
    """Function that converts a string of the format HHMM to an angle in radians

    Args:
        time_str (str): String of the format HHMM (0000 to 2399)

    Returns:
        float: Angle in radians
    """
    hours = int(time_str[:2])
    minutes = int(time_str[2:])
    total_minutes = hours * 60 + minutes
    return (total_minutes / 1440) * 2 * np.pi  # 1440 minutes in a day


def duration_str(interval):
    # Add duration labels in the middle of each interval (closer to the origin)
    # Extract hours and minutes from the "HHMM" format
    start_h, start_m = int(interval["start"][:2]), int(interval["start"][2:])
    end_h, end_m =     int(interval["end"][:2]),   int(interval["end"][2:])

    # Convert to total minutes for easy calculation
    start_total_minutes = start_h * 60 + start_m
    end_total_minutes = end_h * 60 + end_m

    # Handle midnight crossover
    if end_total_minutes < start_total_minutes:
        end_total_minutes += 24 * 60

    # Calculate duration in hours and minutes
    duration_minutes = end_total_minutes - start_total_minutes
    dur_h = duration_minutes // 60
    dur_m = duration_minutes % 60

    # Format the duration string
    return f"{dur_h}h{dur_m:02d}m"



# Create a clock plot from a given schedule
def plot_schedule(schedule):
    # Create a polar plot with a larger figure
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))

    # Configure the polar plot:
    ax.set_theta_direction(-1)           # Clockwise
    ax.set_theta_offset(np.pi/2)         # 0 (midnight) at the top
    ax.set_xticklabels([])               # Remove degree (theta) axis labels

    # Plot each interval as an arc with thick line (linewidth 36)
    arc_radius = 1
    arc_thickness = 36
    
    # interval_angles = []
    for interval in schedule["intervals"]:
        start_angle = time_to_angle(interval["start"])
        end_angle = time_to_angle(interval["end"])
        
        # Adjust for intervals that span midnight
        if end_angle <= start_angle:
            end_angle += 2 * np.pi

        # Plot the arc
        theta = np.linspace(start_angle, end_angle, 200)
        r = np.full_like(theta, arc_radius)
        ax.plot(theta, r, color=interval["color"], linewidth=arc_thickness, solid_capstyle='butt', label=interval["id"])
        
        # Save the mid-angle for placing the ID label (mod 2pi to keep it in [0,2pi))
        mid_angle = (start_angle + end_angle) / 2.0 % (2*np.pi)
        text_rot = (270 - np.degrees(mid_angle)) % 360
        if 90 <= text_rot <= 270:
            text_rot += 180  # Flip for the left half
            
        # Add ID labels in the middle of each interval
        ax.text(mid_angle, arc_radius, interval["id"], ha='center', va='center',
                fontsize=10, color='white', 
                bbox=dict(facecolor=interval["color"], edgecolor='white', boxstyle='round,pad=0.2'))
        
        ax.text(mid_angle, arc_radius - 0.30, duration_str(interval), ha='center', va='center',
                fontsize=8, color='white', rotation=text_rot, 
                bbox=dict(facecolor="grey", edgecolor='none', boxstyle='round,pad=0.2'))

    # Add markers for intersection times (if not exactly on the hour)
    # Intersection markers are at the boundaries of intervals.
    marker_times = set()
    for interval in schedule["intervals"]:
        marker_times.add(interval["start"])
        marker_times.add(interval["end"])

    # Place non-hour intersection labels at a radius of 1.15.
    intersection_radius = 1.15
    for time_str in sorted(marker_times):
        # Check if the minutes are "00" (i.e. an hour marker)
        if int(time_str[2:]) == 0:
            continue  # Skip; add hour ticks separately
        
        angle = time_to_angle(time_str)
        text_rot = (270 - np.degrees(angle)) % 360
        if 90 <= text_rot <= 270:
            text_rot += 180  # Flip for the left half
        
        time_str = time_str[:2] + ':' + time_str[2:]
        
        ax.plot(angle, intersection_radius + 0.05, marker='o', markersize=4, color='black', alpha=1)
        ax.text(angle, intersection_radius + 0.15, time_str, rotation=text_rot, ha='center', va='center',
                fontsize=8, color="black",
                bbox=dict(facecolor="none", edgecolor='none', boxstyle='round,pad=0.2'))

    # Add an hour tick and label for each hour (00 to 23)
    # We'll draw a short radial line (tick) and label them at a slightly further radius.
    tick_inner = 1.17
    tick_outer = 1.25
    for hour in range(24):
        # Convert hour to angle using the "HHMM" format.
        time_str = f"{hour:02d}00"
        angle = time_to_angle(time_str)
        # Draw a tick line from tick_inner to tick_outer
        ax.plot([angle, angle], [tick_inner, tick_outer], color='black', lw=2)
        # Label the hour just outside the tick
        ax.text(angle, tick_outer + 0.05, f"{hour:02d}", ha='center', va='center', fontsize=8)
    #     ax.text(angle, tick_outer, f"{hour:02d}", ha='center', va='bottom', fontsize=10)

    # Remove radial tick labels and set radius limits
    ax.set_yticklabels([])
    ax.set_ylim(0, 1.4)
    plt.title(schedule['title'], fontsize=14)

    # Save the updated plot as a PNG file
    plt.savefig(f"images/{snake_case(schedule["title"])}.png", dpi=300, bbox_inches='tight')
    plt.show()



if __name__ == "__main__":
    # open schedules file
    with open('schedules.json', 'r') as f:
        data = json.load(f)

    # data = data[0]

    # if only one plot selected, only plot one
    # otherwise plot all schedules in data
    try:
        data["title"]
        print('Plotting 1 of 1')
        plot_schedule(data)
    except TypeError:
        for schedule in data:
            plot_schedule(schedule)