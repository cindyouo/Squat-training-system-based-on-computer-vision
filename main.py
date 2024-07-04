
import tkinter as tk
import cv2
import PIL.Image, PIL.ImageTk
import subprocess


class VideoPlayer:
    def __init__(self, window, window_title, video_path):
        self.window = window
        self.window.title(window_title)
       
        self.window.attributes('-fullscreen', True)  # 设置窗口全屏


        # 创建关闭按钮（右上角）
        close_button = tk.Button(self.window, text="✕", font=("Helvetica", 24), command=self.window.destroy)
        close_button.pack(anchor='ne', padx=10, pady=10)


        # 创建左半边的框架
        self.left_frame = tk.Frame(self.window)
        self.left_frame.pack(side="left", fill="both", expand=True)


        # 创建右半边的框架
        self.right_frame = tk.Frame(self.window)
        self.right_frame.pack(side="right", fill="both", expand=True)


        # 左半边内容
        self.title_label = tk.Label(self.left_frame, text="深蹲競賽", font=("Arial", 30))
        self.title_label.pack(pady=20, padx=20, anchor="w")


        self.subtitle_label = tk.Label(self.left_frame, text="規則", font=("Arial", 20))
        self.subtitle_label.pack(pady=10, padx=20, anchor="w")


        rules_text = (
            "1.動作:維持雙足站穩，雙腳與肩同寬，雙手放在胸前或握拳，開始向下蹲，保持身體挺直，重心不前傾，"
            "膝蓋不超過腳尖，然後回到原來的姿勢\n"
            "\n "
            "2.人數3人，按下開始後倒數15秒去對準位置，計時30秒開始深蹲算次數\n"
            "\n"
            "3.判斷標準:膝蓋角度小於175度且身體比例不超過1.2"
        )


        self.rules_label = tk.Label(self.left_frame, text=rules_text, font=("Arial", 20), justify=tk.LEFT, wraplength=530)
        self.rules_label.pack(pady=10, padx=20, anchor="w")


        self.start_button = tk.Button(self.left_frame, text="開始", font=("Arial", 24), command=self.start_program)
        self.start_button.pack(pady=20, padx=20, anchor="w")


        # 右半边内容
        self.video_label = tk.Label(self.right_frame, text="觀看教學影片", font=("Arial", 20))
        self.video_label.pack(pady=(90, 20), padx=5, anchor="w")  # 调整观看教学影片标签的上下间距


        self.video_path = video_path
        self.video_source = cv2.VideoCapture(self.video_path)


        self.canvas = tk.Canvas(self.right_frame)
        self.canvas.pack(pady=10, padx=20, fill="both", expand=True)


        # 暫停/播放按鈕
        self.pause_button = tk.Button(self.right_frame, text="Pause", font=("Arial", 24), command=self.pause_video)
        self.pause_button.pack(pady=70)  # 修改这里调整暂停按钮的位置


        self.is_paused = False
        self.update()
        self.window.mainloop()


    def start_program(self):
        subprocess.call(['python', 'sql.py'])


    def pause_video(self):
        if self.is_paused:
            self.is_paused = False
            self.pause_button.config(text="Pause")
        else:
            self.is_paused = True
            self.pause_button.config(text="Play")


    def update(self):
        if not self.is_paused:
            ret, frame = self.video_source.read()
            if ret:
                frame = cv2.resize(frame, (560, 315))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            else:
                self.video_source.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重新播放
        self.window.after(15, self.update)


    def __del__(self):
        if self.video_source.isOpened():
            self.video_source.release()


# 创建主窗口
root = tk.Tk()
video_path = "squart.mp4"


app = VideoPlayer(root, "深蹲競賽", video_path)