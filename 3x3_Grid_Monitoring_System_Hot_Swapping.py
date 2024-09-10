import sys
import cv2
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGridLayout, QListWidget, QListWidgetItem, QHBoxLayout, QPushButton
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtGui import QPixmap, QImage, QFont

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("摄像头 3x3 九宫格")
        self.setGeometry(100, 100, 1600, 900)

        # 创建一个主布局，包括摄像头列表和九宫格显示
        main_layout = QHBoxLayout(self)

        # 创建摄像头列表部分
        self.camera_list_widget = QListWidget(self)
        self.camera_list_widget.setFixedWidth(self.width() // 4)  # 列表宽度为窗口的四分之一
        self.camera_list_widget.itemDoubleClicked.connect(self.on_list_item_double_clicked)

        # 添加一个摄像头列表标题
        self.list_title_label = QLabel("摄像头列表", self)
        self.list_title_label.setAlignment(Qt.AlignCenter)
        self.list_title_label.setFont(QFont("Arial", 18))

        # 创建左侧的垂直布局，包括标题和列表
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.list_title_label)
        left_layout.addWidget(self.camera_list_widget)

        # 创建一个 3x3 的网格布局
        self.grid_layout = QGridLayout()

        # 创建九个 QLabel 来显示视频或 "No signal"
        self.labels = []
        for i in range(9):
            label = QLabel(self)
            label.setFixedSize(480, 320)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("background-color: black; color: red;")
            label.setFont(QFont("Arial", 24))
            label.mouseDoubleClickEvent = lambda event, idx=i: self.open_camera_window(idx)
            self.labels.append(label)
            self.grid_layout.addWidget(label, i // 3, i % 3)

        # 摄像头初始化
        self.caps = [None] * 9

        # 初始化两个摄像头
        for i in range(9): 
            self.caps[i] = cv2.VideoCapture(i) 

        # 定时器检测视频帧
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)

        # 添加布局到主窗口
        main_layout.addLayout(left_layout)
        main_layout.addLayout(self.grid_layout)
        self.setLayout(main_layout)
        
        self.camera_list_widget.clear()  # 清空列表
        for i, cap in enumerate(self.caps):
            if cap:
                ret, frame = cap.read()
                if ret:
                    # 获取摄像头的分辨率和帧率作为显示信息
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    camera_info = f"摄像头 {i}: {width}x{height} @ {fps} FPS"
                    list_item = QListWidgetItem(camera_info)
                    list_item.setData(Qt.UserRole, i)  # 保存摄像头索引
                    self.camera_list_widget.addItem(list_item)
            
        self.isclose=False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_list)
        self.timer.start(3000)
        
    def update_frames(self):
        for i, cap in enumerate(self.caps):
            if cap is not None:
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame_rgb.shape
                    bytes_per_line = ch * w
                    image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    self.labels[i].setPixmap(QPixmap.fromImage(image))
                else:
                    self.caps[i] = None
                    self.show_no_signal(i)
                    self.check_for_new_camera(i)
            else:
                self.caps[i] = None
                self.show_no_signal(i)
                self.check_for_new_camera(i)

    def check_for_new_camera(self, index):
        cap = cv2.VideoCapture(index)
        ret, frame = cap.read()
        if ret:
            print(f"检测到新的摄像头信号：索引 {index}")
            
            self.caps[index] = cap
            
            if self.isclose:
                for cap in self.caps:
                    if cap is not None:
                        cap.release()
        else:
            self.caps[index] = None
            cap.release()

    def update_camera_list(self):
        self.camera_list_widget.clear()  # 清空列表
        for i, cap in enumerate(self.caps):
            if cap:
                ret, frame = cap.read()
                if ret:
                    # 获取摄像头的分辨率和帧率作为显示信息
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    camera_info = f"摄像头 {i}: {width}x{height} @ {fps} FPS"
                    list_item = QListWidgetItem(camera_info)
                    list_item.setData(Qt.UserRole, i)  # 保存摄像头索引
                    self.camera_list_widget.addItem(list_item)

    def show_no_signal(self, index):
        self.labels[index].setText("No signal")

    def on_list_item_double_clicked(self, item):
        index = item.data(Qt.UserRole)
        cap = self.caps[index]
        if cap is not None and cap.isOpened():
            self.camera_window = CameraWindow(cap)
            self.camera_window.show()
        else:
            self.no_signal_window = NoSignalWindow()
            self.no_signal_window.show()
    
    def open_camera_window(self, index):
        # 双击九宫格时弹出窗口
        cap = self.caps[index]
        if cap is not None and cap.isOpened():
            self.camera_window = CameraWindow(cap)
            self.camera_window.show()
        else:
            
            self.no_signal_window = NoSignalWindow()
            self.no_signal_window.show()
    
    def closeEvent(self, event):
        self.isclose=True
        for cap in self.caps:
            if cap is not None:
                cap.release()
 
        cv2.destroyAllWindows() 
# 摄像头窗口，支持截屏和录像
class CameraWindow(QWidget):
    def __init__(self, cap):
        super().__init__()
        self.setWindowTitle("摄像头拍照和录屏")
        self.setGeometry(300, 300, 800, 600)
        self.cap = cap
        self.is_recording = False
        self.video_writer = None
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)

        # 添加截图和录像按钮
        self.snapshot_button = QPushButton("截屏", self)
        self.snapshot_button.clicked.connect(self.take_snapshot)
        self.record_button = QPushButton("开始录像", self)
        self.record_button.clicked.connect(self.toggle_recording)

        layout.addWidget(self.snapshot_button)
        layout.addWidget(self.record_button)

        self.setLayout(layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(image))

            if self.is_recording:
                self.video_writer.write(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))

    def take_snapshot(self):
        ret, frame = self.cap.read()
        if ret:
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
            filename = f"snapshot_{timestamp}.png"
            cv2.imwrite(filename, frame)
            print(f"截图已保存: {filename}")

    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.record_button.setText("开始录像")
            self.video_writer.release()
            print("录像结束")
        else:
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
            filename = f"recording_{timestamp}.avi"
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_writer = cv2.VideoWriter(filename, fourcc, 20, (width, height))
            self.is_recording = True
            self.record_button.setText("停止录像")
            print(f"开始录像: {filename}")

    def closeEvent(self, event):
        if self.is_recording:
            self.video_writer.release()

# 无信号窗口
class NoSignalWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("无信号")
        self.setGeometry(300, 300, 400, 300)
        label = QLabel("No signal", self)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 24))
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
