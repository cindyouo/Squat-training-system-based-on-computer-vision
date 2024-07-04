import tkinter as tk
from tkinter import Frame, Label, Entry, Button, Toplevel
from tkinter import messagebox
from tkcalendar import DateEntry
import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import calendar
import numpy as np
from matplotlib.colors import ListedColormap

def show_start_screen():
    global root, sport_name
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.title("Exercise Program")

    frame = Frame(root)
    frame.pack(expand=True)
    
    # Input settings
    Label(frame, text="請輸入名字代碼:", font=("Helvetica", 24)).pack(pady=20)
    sport_name = Entry(frame, font=("Helvetica", 24))
    sport_name.pack(pady=10)

    Label(frame, text="管理員001~006，007其他", font=("Helvetica", 24)).pack(pady=20)

    
    # Start button
    start_button = Button(frame, text="開始", font=("Helvetica", 24), command=start_program,width=13)
    start_button.pack(side="left",padx=10)

    # Exit button
    exit_button = Button(frame, text="返回", font=("Helvetica", 24), command=root.quit)
    exit_button.pack(side="left")


    root.mainloop()

def start_program():
    user_id = sport_name.get()
    if not user_id:
        messagebox.showerror("Input Error", "請輸入名字代碼")
        return
    
    root.withdraw()  # Hide the root window
    show_graph_screen(user_id)

def show_graph_screen(user_id):
    global graph_window, date_entry, fig, ax, canvas, colorbar, colorbar_added
    colorbar_added = False
    colorbar = None
    graph_window = Toplevel(root)
    graph_window.attributes('-fullscreen', True)
    graph_window.title(f"Exercise Data for {user_id}")

    top_frame = Frame(graph_window)
    top_frame.pack(side=tk.TOP, pady=10)

    Label(top_frame, text="選擇日期:", font=("Helvetica", 24)).pack(side=tk.LEFT, padx=10)
    date_entry = DateEntry(top_frame, font=("Helvetica", 24), date_pattern='y-mm-dd')
    date_entry.pack(side=tk.LEFT, padx=10)

    show_day_button = Button(top_frame, text="Show Day", font=("Helvetica", 24), command=lambda: update_graph(user_id, date_entry.get_date(), 'day'))
    show_day_button.pack(side=tk.LEFT, padx=10)

    show_week_button = Button(top_frame, text="Show Week", font=("Helvetica", 24), command=lambda: update_graph(user_id, date_entry.get_date(), 'week'))
    show_week_button.pack(side=tk.LEFT, padx=10)

    show_month_button = Button(top_frame, text="Show Month", font=("Helvetica", 24), command=lambda: update_graph(user_id, date_entry.get_date(), 'month'))
    show_month_button.pack(side=tk.LEFT, padx=10)

    exit_button = Button(top_frame, text="Exit", font=("Helvetica", 24), command=close_graph_screen)
    exit_button.pack(side=tk.RIGHT, padx=10)

    # Initialize plot area
    fig, ax = plt.subplots(figsize=(16, 8))
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def close_graph_screen():
    global root, graph_window
    graph_window.destroy()
    root.deiconify()  # Show the root window again

def update_graph(user_id, selected_date, period):
    global fig, ax, canvas, colorbar, colorbar_added
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="92MySQLcindy",  #這邊請輸入自己的密碼
        database="sport_record_db"
    )
    cursor = conn.cursor()

    if period == 'day':
        query = """
        SELECT start_hour, SUM(count) 
        FROM ExerciseRecords 
        WHERE user_id = %s AND date = %s 
        GROUP BY start_hour 
        ORDER BY start_hour;
        """
        cursor.execute(query, (user_id, selected_date))
    elif period == 'week':
        start_date = selected_date - timedelta(days=selected_date.weekday())
        end_date = start_date + timedelta(days=6)
        query = """
        SELECT DATE(date), SUM(count) 
        FROM ExerciseRecords 
        WHERE user_id = %s AND date BETWEEN %s AND %s 
        GROUP BY DATE(date) 
        ORDER BY DATE(date);
        """
        cursor.execute(query, (user_id, start_date, end_date))
    elif period == 'month':
        start_date = selected_date.replace(day=1)
        end_date = selected_date.replace(day=calendar.monthrange(selected_date.year, selected_date.month)[1])
        query = """
        SELECT DATE(date), SUM(count) 
        FROM ExerciseRecords 
        WHERE user_id = %s AND date BETWEEN %s AND %s 
        GROUP BY DATE(date) 
        ORDER BY DATE(date);
        """
        cursor.execute(query, (user_id, start_date, end_date))

    result = cursor.fetchall()
    conn.close()

    # Clear and recreate figure and canvas
    if canvas:
        canvas.get_tk_widget().pack_forget()
        canvas.get_tk_widget().destroy()

    fig, ax = plt.subplots(figsize=(16, 8))
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    if colorbar_added and colorbar:
        colorbar.remove()
        colorbar = None
        colorbar_added = False

    if period == 'day':
        hours = list(range(24))
        counts = [0] * 24
        for hour, count in result:
            counts[hour] = count

        if all(count == 0 for count in counts):
            ax.text(0.5, 0.5, 'no record', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=32, color='red')

        ax.bar(hours, counts)
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Count')
        ax.set_title(f'Exercise Count for {user_id} on {selected_date}')
        ax.set_xticks(hours)
        ax.set_xticklabels([f'{h}' for h in hours])
        ax.yaxis.set_major_locator(plt.MultipleLocator(5))
        ax.set_xlim(0, 23)
        ax.set_ylim(0)
        
    elif period == 'week':
        days = [(selected_date - timedelta(days=selected_date.weekday()) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        counts = [0] * 7
        date_to_index = {days[i]: i for i in range(7)}

        for date, count in result:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in date_to_index:
                counts[date_to_index[date_str]] = count

        if all(count == 0 for count in counts):
            ax.text(0.5, 0.5, 'no record', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=32, color='red')

        ax.bar(days, counts)
        ax.set_xlabel('Date')
        ax.set_ylabel('Count')
        ax.set_title(f'Exercise Count for {user_id} (Week)')
        ax.set_xticks(range(len(days)))
        ax.set_xticklabels(days, rotation=45, ha='right')
        ax.yaxis.set_major_locator(plt.MultipleLocator(5))
        ax.set_ylim(0)

    elif period == 'month':
        days_in_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
        first_weekday = selected_date.replace(day=1).weekday()
        heatmap_data = np.zeros((5, 7))
        day_labels = np.full((5, 7), "", dtype=object)
        counts = np.zeros((5, 7))

        for day in range(1, days_in_month + 1):
            date = selected_date.replace(day=day)
            weekday = date.weekday()
            week_of_month = (day + first_weekday - 1) // 7
            if week_of_month < 5:  # 只顯示前五週
                day_labels[week_of_month, weekday] = str(day)

        for date, count in result:
            day = date.day
            weekday = date.weekday()
            week_of_month = (day + first_weekday - 1) // 7
            if week_of_month < 5:  # 只顯示前五週
                counts[week_of_month, weekday] = count

        # Define custom colormap
        colors = ["#add8e6", "#87ceeb", "#0000ff", "#00008b"]  # 淡藍色, 水藍色, 藍色, 深藍色
        cmap = ListedColormap(colors)

        bounds = [0, 1, 20, 40, np.max(counts) + 1] if np.max(counts) > 0 else [0, 1, 2, 3, 4]
        norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

        sns.heatmap(counts, annot=day_labels, fmt="", cmap=cmap, cbar=False, ax=ax, linewidths=.5, norm=norm, 
                    xticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 
                    yticklabels=['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'])

        ax.set_title(f'Exercise Heatmap for {user_id} ({selected_date.year}-{selected_date.month:02d})')

        # Always add the color bar when viewing the month
        colorbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)
        colorbar.set_label('Exercise Count')
        colorbar_added = True

    # Adjust layout
    fig.tight_layout()

    # Redraw canvas
    canvas.draw()

if __name__ == '__main__':
    show_start_screen()



if __name__ == '__main__':
    show_start_screen()
