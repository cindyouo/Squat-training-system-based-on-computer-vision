import cv2
import mediapipe as mp
import numpy as np
import time
import json
from datetime import datetime, timedelta
from tkinter import Tk, Entry, Button, Label, Frame
import mysql.connector

# 全局攝像頭變量
cam = None

# 初始化MediaPipe姿勢檢測
mppose = mp.solutions.pose
mpdraw = mp.solutions.drawing_utils
pose_estimator = mppose.Pose()

# 設置全局變量
h, w = 0, 0
start_time = 0
status = False
exercise_start = None
user_id = None

sport = {
    "name": "Squat",
    "count": 0,
    "calories": 0
}

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '92MySQLcindy', #這邊請輸入自己的密碼
    'database': 'sport_record_db'
}




# 建立數據庫連接
try:
    conn = mysql.connector.connect(**db_config)
    print("Database connection established")
except mysql.connector.Error as err:
    print("Error: ", err)


# 插入數據到數據库的函數
def insert_data_to_db(user_id, start_hour, start_minute, end_hour, end_minute, date, count):
    if conn:
        try:
            cursor = conn.cursor()

            # 插入數據的SQL語句
            insert_query = """
            INSERT INTO ExerciseRecords (user_id, start_hour, start_minute, end_hour, end_minute, date, count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            # 要插入的數據
            data = (user_id, start_hour, start_minute, end_hour, end_minute, date, count)

            # 執行插入操作
            cursor.execute(insert_query, data)

            # 提交事務
            conn.commit()

            print("Data inserted successfully")

        except mysql.connector.Error as err:
            print("Error: ", err)
        finally:
            # 關閉游標
            cursor.close()




# 啟动程序的函数
def start_program():
    global sport_name, cam, start_hour, start_minute, start_date, end_hour, end_minute, user_id

    user_id = sport_name.get()

    # 初始化運動計數
    sport['count'] = 0
    sport['calories'] = 0

    # 獲取開始時間
    start_time = datetime.now()
    start_hour = start_time.hour
    start_minute = start_time.minute
    start_date = start_time.date()

    root.destroy()

    # 初始化摄像頭
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Camera not open")
        return

    main()

# 日志紀錄
def logger(count, cals):
    with open("log.txt", 'a') as f:
        f.write(f"{time.ctime()} count: {count} cals: {cals}\n")

# 計算角度
def calc_angles(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle


# 獲取關節點位置
def get_landmark(landmarks, part_name):
    return [
        landmarks[mppose.PoseLandmark[part_name].value].x,
        landmarks[mppose.PoseLandmark[part_name].value].y,
        landmarks[mppose.PoseLandmark[part_name].value].z,
    ]


# 檢察關節點可見性
def get_visibility(landmarks):
    return (landmarks[mppose.PoseLandmark.RIGHT_HIP.value].visibility > 0.8 and
            landmarks[mppose.PoseLandmark.LEFT_HIP.value].visibility > 0.8)


# 計算身體比例
def get_body_ratio(landmarks):
    r_body = abs(landmarks[mppose.PoseLandmark.RIGHT_SHOULDER.value].y -
                 landmarks[mppose.PoseLandmark.RIGHT_HIP.value].y)
    l_body = abs(landmarks[mppose.PoseLandmark.LEFT_SHOULDER.value].y -
                 landmarks[mppose.PoseLandmark.LEFT_HIP.value].y)
    avg_body = (r_body + l_body) / 2
    r_leg = abs(landmarks[mppose.PoseLandmark.RIGHT_HIP.value].y -
                landmarks[mppose.PoseLandmark.RIGHT_ANKLE.value].y)
    l_leg = abs(landmarks[mppose.PoseLandmark.LEFT_HIP.value].y -
                landmarks[mppose.PoseLandmark.LEFT_ANKLE.value].y)
    return max(r_leg, l_leg) / avg_body

# 計算膝蓋角度
def get_knee_angle(landmarks):
    r_hip, l_hip = get_landmark(landmarks, "RIGHT_HIP"), get_landmark(landmarks, "LEFT_HIP")
    r_knee, l_knee = get_landmark(landmarks, "RIGHT_KNEE"), get_landmark(landmarks, "LEFT_KNEE")
    r_ankle, l_ankle = get_landmark(landmarks, "RIGHT_ANKLE"), get_landmark(landmarks, "LEFT_ANKLE")

    r_angle = calc_angles(r_hip, r_knee, r_ankle)
    l_angle = calc_angles(l_hip, l_knee, l_ankle)

    m_hip = [(r_hip[i] + l_hip[i]) / 2 for i in range(3)]
    m_knee = [(r_knee[i] + l_knee[i]) / 2 for i in range(3)]
    m_ankle = [(r_ankle[i] + l_ankle[i]) / 2 for i in range(3)]


    mid_angle = calc_angles(m_hip, m_knee, m_ankle)

    return [int(r_angle), int(l_angle), int(mid_angle)]




# 畫矩形框
def draw_fillrectangle(img):
    cv2.rectangle(img, (5, 10), (170, 50), (0, 0, 255), -1)
    return img




def draw_rectangle(img):
    cv2.rectangle(img, (5, 10), (170, 50), (82, 169, 255), 1)




def main():
    global h, w, start_time, status, exercise_start, cam, user_id, start_hour, start_minute, start_date




    exercise_start = None




    flag = False
    countdown_start = time.time()
    session_duration = 50 #設置運行時間50秒  #這段影響了原先的SLEEP




    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)




    try:
        while not flag and time.time() - countdown_start < session_duration:
            ret, frame = cam.read()
            if not ret:
                print("Read Error")
                break
            frame = cv2.flip(frame, 1)
            rgbframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            poseoutput = pose_estimator.process(rgbframe)
            h, w, _ = frame.shape
            preview = frame.copy()




            read_dir_key = cv2.waitKeyEx(1)
            if read_dir_key != -1:
                print(read_dir_key)
                if read_dir_key == 13:
                    sport['count'] = 0




            if poseoutput.pose_landmarks:
                mpdraw.draw_landmarks(preview, poseoutput.pose_landmarks, mppose.POSE_CONNECTIONS)
                knee_angles = get_knee_angle(poseoutput.pose_landmarks.landmark)
                body_ratio = get_body_ratio(poseoutput.pose_landmarks.landmark)
                avg_angle = int((knee_angles[0] + knee_angles[1]) // 2)




                if countdown_start + 16 > time.time():
                    countdown_text = f"prepared time: {int(16 - (time.time() - countdown_start))}"
                    cv2.putText(preview, countdown_text, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 2, cv2.LINE_AA)
                else:
                    exercise_start = time.time()
                   
                if exercise_start:
                    if countdown_start + 47 > time.time():
                        countdown_text = f"start time: {int(47 - (time.time() - countdown_start))}"
                        cv2.putText(preview, countdown_text, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 2, cv2.LINE_AA)




                        if status:
                            if avg_angle > 175:
                                status = False
                                pass_time = time.time() - start_time
                                start_time = 0
                                if 3000 > pass_time > 0.5:
                                    sport['count'] += 1
                                    sport['calories'] += int(0.66 * pass_time)
                                    logger(sport['count'], sport['calories'])
                                    tmp = f"a{sport['count']}\n"
                                    # ser.write(str.encode(tmp))
                                    tmp = f"b{sport['calories']}\n"
                                    # ser.write(str.encode(tmp))
                        else:
                            if avg_angle < 173 and body_ratio < 1.2:
                                start_time = time.time()
                                status = True
            else:
                start_time = 0




            draw_fillrectangle(preview)
            draw_rectangle(preview)
            cv2.putText(preview, f"count: {sport['count']}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 4, cv2.LINE_AA)
            cv2.putText(preview, f"count: {sport['count']}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
           
            cv2.imshow('frame', preview)




    finally:
        with open("sport_recorder.json", "w") as f:
            f.write(json.dumps(sport))




        end_time = datetime.now()
        end_hour = end_time.hour
        end_minute = end_time.minute




        insert_data_to_db(user_id, start_hour, start_minute, end_hour, end_minute, start_date, sport['count'])
       
        cam.release()
        cv2.destroyAllWindows()
        time.sleep(1)  # 短暂等待一秒
        show_start_screen()  # 返回初始畫面




def show_start_screen():
    global root, sport_name
    root = Tk()
    root.attributes('-fullscreen', True)
    root.title("Exercise Program")

    frame = Frame(root)
    frame.pack(expand=True)

    # 创建关闭按钮
    close_button = Button(root, text="✕", font=("Helvetica", 24), command=root.destroy)
    close_button.place(x=root.winfo_screenwidth()-70, y=10)  # 将按钮放置在右上角

    # Button settings
    Label(frame, text="請輸入名字代碼:", font=("Helvetica", 24)).pack(pady=20)
    sport_name = Entry(frame, font=("Helvetica", 24))
    sport_name.pack(pady=10)

    Label(frame, text="管理員001~006，007其他", font=("Helvetica", 24)).pack(pady=20)

    # 使用Frame來左右排列按鈕
    button_frame = Frame(frame)
    button_frame.pack(pady=20)

    history_button = Button(button_frame, text="歷史紀錄", font=("Helvetica", 24), command=show_history)
    history_button.pack(side="left", padx=10)

    main_button = Button(button_frame, text="主頁面", font=("Helvetica", 24), command=go_to_main)
    main_button.pack(side="left", padx=10)

    # 获取歷史紀錄和主頁面按钮的宽度总和
    root.update_idletasks()  # 更新所有的IDLE任務，這樣我們可以得到按鈕的寬度
    total_width = history_button.winfo_reqwidth() + main_button.winfo_reqwidth() + 20  # 加上兩個padx的寬度

    start_button = Button(frame, text="Start", font=("Helvetica", 24), command=start_program, width=total_width//18)
    start_button.pack(pady=20)

    root.mainloop()


def show_history():
    # 確保已經關閉攝像頭
    if cam:
        cam.release()
        cv2.destroyAllWindows()
   
    # 執行show.py來顯示歷史紀錄
    import subprocess
    subprocess.run(["python", "newshow.py"])


def go_to_main():
    if cam:
        cam.release()
        cv2.destroyAllWindows()  
   
    import subprocess
    subprocess.Popen(["python", "main.py"])

if __name__ == '__main__':
    show_start_screen()

    # 關閉資料庫連接
    if conn:
        conn.close()
        print("Database connection closed")





