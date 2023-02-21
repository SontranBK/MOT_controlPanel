from ui import Ui_App
from dashboardUI import UI_Dashboard
import os
import sys
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QLabel, QMainWindow, QTableWidgetItem,QPushButton,QListWidgetItem
from PyQt5 import QtCore, QtGui, QtWidgets,QtSql
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QFile,QTextStream,QSize,QEvent,QPoint,QRect
from PyQt5.QtGui import QColor,QImage, QPen
from threading import Thread
import cv2
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import firestore
import pyrebase
import queue
from collections import deque
cred = credentials.Certificate("firebaseAccount.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


Config = {
  'apiKey': "AIzaSyAGEyO4ZN7gdrvuqY4Vd1SMMCUVmt6UDno",
  'authDomain': "aaaa-dbb41.firebaseapp.com",
  'databaseURL': "https://aaaa-dbb41-default-rtdb.firebaseio.com",
  "projectId": "aaaa-dbb41",
  "storageBucket": "aaaa-dbb41.appspot.com",
  "messagingSenderId": "91945409393",
  "appId": "1:91945409393:web:1b17b16a8ad8d978bb74d0"
}

firebase = pyrebase.initialize_app(Config)
store = firebase.storage()
qp = QtGui.QPainter()
global rect
global lane_left, lane_center, lane_right
global direct_left, direct_center, direct_right
# get frame preview camera
def getFrame(linkcam, myFrameNumber):
    cap = cv2.VideoCapture(linkcam)#video_dir is video file or webcam
    cap.set(cv2.CAP_PROP_POS_FRAMES, myFrameNumber)
    cap.grab()
    return cap.retrieve(0)


def QtImage(screen, img):
    img_height, img_width, img_colors = img.shape
    scale = screen / img_height
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    height, width, bpc = img.shape
    bytesPerLine = 3 * width
    return QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)

class VideoStreamWidget(object):
    def __init__(self, src=0):
        # Create a VideoCapture object
        self.capture = cv2.VideoCapture(src)

        # Start the thread to read frames from the video stream
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
    def update(self):
        # Read the next frame from the stream in a different thread
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
    def show_frame(self):
        # Display frames in main program
        if self.status:
            self.frame = self.maintain_aspect_ratio_resize(self.frame, width=800)
            cv2.imshow('IP Camera Video preview', self.frame)

        # Press Q on keyboard to stop recording
        key = cv2.waitKey(1)
        if key == ord('q'):
            self.capture.release()
            cv2.destroyAllWindows()
            exit(1)

    # Resizes a image and maintains aspect ratio
    def maintain_aspect_ratio_resize(self, image, width=None, height=None, inter=cv2.INTER_AREA):
        # Grab the image size and initialize dimensions
        dim = None
        (h, w) = image.shape[:2]

        # Return original image if no need to resize
        if width is None and height is None:
            return image

        # We are resizing height if width is none
        if width is None:
            # Calculate the ratio of the height and construct the dimensions
            r = height / float(h)
            dim = (int(w * r), height)
        # We are resizing width if height is none
        else:
            # Calculate the ratio of the 0idth and construct the dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # Return the resized image
        return cv2.resize(image, dim, interpolation=inter)
class DrawObject(QWidget):
    def __init__(self, parent=None):
        super(DrawObject, self).__init__(parent)
        self.image = None
        self.flag = None
        self.direct = None
        self.img_holder = None
        self.screen = None
        global rect
        global lane_left, lane_center, lane_right
        global direct_left, direct_center, direct_right
        rect = []
        lane_left, lane_center, lane_right = [], [], []
        direct_left, direct_center, direct_right = [], [], []
        self.begin = QPoint()
        self.end = QPoint()
        self.show()

    def setImage(self, image):
        self.image = image
        img_size = image.size()
        self.setMinimumSize(img_size)
        self.update()

    def setMode(self, mode_flag, direct_flag):
        self.flag = mode_flag
        self.direct = direct_flag
        self.update()

    def goBack(self):
        if self.flag == 'rect' and len(rect) > 0:
            rect.pop()
        elif self.flag == 'lane' and self.direct == 'left' and len(lane_left) > 0:
            lane_left.pop()
        elif self.flag == 'lane' and self.direct == 'center' and len(lane_center) > 0:
            lane_center.pop()
        elif self.flag == 'lane' and self.direct == 'right' and len(lane_right) > 0:
            lane_right.pop()
        elif self.flag == 'direct' and self.direct == 'left' and len(direct_left) > 0:
            direct_left.pop()
        elif self.flag == 'direct' and self.direct == 'center' and len(direct_center) > 0:
            direct_center.pop()
        elif self.flag == 'direct' and self.direct == 'right' and len(direct_right) > 0:
            direct_right.pop()
        self.update()

    def paintEvent(self, event):
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        br = QtGui.QBrush(QColor(0, 252, 156, 40))
        qp.setBrush(br)
        global rect_redlight
        for item in rect:
            pen = QtGui.QPen(QColor(255, 255, 255), 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawRect(QRect(item[0], item[1]))
            rect_redlight = item

        global line_left1,line_left2,line_center1,line_center2,line_right1,line_right2
        for item in lane_left:
            pen = QtGui.QPen(QColor(255, 0, 0), 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawLine(item[0], item[1])
            qp.drawText(item[0], str("line left 1"))
            line_left1=item
         
        for item in lane_center:
            pen = QtGui.QPen(QColor(255, 255, 0), 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawLine(item[0], item[1])
            qp.drawText(item[0], str("line center 1"))
            line_center1=item
        
        for item in lane_right:
            pen = QtGui.QPen(QColor(0, 0, 255), 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawLine(item[0], item[1])
            qp.drawText(item[0], str("line right 1"))
            line_right1=item

        for item in direct_left:
            pen = QtGui.QPen(QColor(255, 0, 0), 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawLine(item[0], item[1])
            qp.drawText(item[0], str("line left 2"))
            line_left2=item

        for item in direct_center:
            pen = QtGui.QPen(QColor(255, 255, 0), 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawLine(item[0], item[1])
            qp.drawText(item[0], str("center line 2"))
            line_center2=item

        for item in direct_right:
            pen = QtGui.QPen(QColor(0, 0, 255), 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawLine(item[0], item[1])
            qp.drawText(item[0], str("right line 2"))
            line_right2=item
          
        qp.end()
    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        if self.direct == 'left':
            if self.flag == 'lane' and len(lane_left) == 1:
                lane_left.pop()
            elif self.flag == 'direct' and len(direct_left) == 1:
                direct_left.pop()
        elif self.direct == 'center':
            if self.flag == 'lane' and len(lane_center) == 1:
                lane_center.pop()
            elif self.flag == 'direct' and len(direct_center) == 1:
                direct_center.pop()
        elif self.direct == 'right':
            if self.flag == 'lane' and len(lane_right) == 1:
                lane_right.pop()
            elif self.flag == 'direct' and len(direct_right) == 1:
                direct_right.pop()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        self.update()
        if self.direct == 'left':
            if self.flag == 'lane':
                lane_left.append([self.begin, self.end])
            elif self.flag == 'direct':
                direct_left.append([self.begin, self.end])
        elif self.direct == 'center':
            if self.flag == 'lane':
                lane_center.append([self.begin, self.end])
            elif self.flag == 'direct':
                direct_center.append([self.begin, self.end])
        elif self.direct == 'right':
            if self.flag == 'lane':
                lane_right.append([self.begin, self.end])
            elif self.flag == 'direct':
                direct_right.append([self.begin, self.end])
        elif self.flag == 'rect':
            rect.append([self.begin, self.end])
# for Tab Draw <--
class MainApplication(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_App()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.show()
        # self.Login_App = Login()
        # self.Login_App.show()
        self.ui.pushButton.clicked.connect(lambda : self.functionLogin())
        self.ui.CloseBtn.clicked.connect(self.close)
        self.ui.MinimunBtn.clicked.connect(self.showMinimized)
        # self.ui.logoutButton.clicked.connect(lambda: self.functionLogout())
        self.ui.Showpassword.clicked.connect(lambda: self.showPass())
        self.ui.Hidepassword.clicked.connect(lambda: self.hidePass())
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.logout_btn.clicked.connect(lambda: self.functionLogout())
        # self.ui.home_btn_2.setChecked(True)
        self.ui.openaddcam_btn.clicked.connect(lambda: self.functionOpenaddcamera())
        # self.id =[]
        self.ui.addcam_btn.clicked.connect(lambda: self.functionAddcamera())
        self.ui.preview_btn.clicked.connect(lambda: self.functionPreviewcamera())
        self.ui.Line_left.clicked.connect(self.setLeftLane)
        self.ui.Line_Center.clicked.connect(self.setCenterLane)
        self.ui.Line_Right.clicked.connect(self.setRightLane)
        self.ui.Line_left_2.clicked.connect(self.setLeftDirect)
        self.ui.Line_Center_2.clicked.connect(self.setCenterDirect)
        self.ui.Line_Right_2.clicked.connect(self.setRightDirect)
        self.ui.Square.clicked.connect(self.setRect)
        self.ui.Delete.clicked.connect(self.GoBack)
        self.ui.Save_draw.clicked.connect(self.Updatefirebase)
        self.ui.Draw_line = DrawObject(self.ui.Draw_line)
        self.list_item_widgets =[] 
        
        self.screen = 720
        self.getlistitemcam_from_firbase()
        violationlistinformation = db.collection('violation').get()
        for a in violationlistinformation:
            self.violationinfor = QtWidgets.QWidget()
            self.violationinfor.setGeometry(QtCore.QRect(130, 60, 950, 80))
            self.violationinfor.setStyleSheet("background-color: rgb(255, 0, 0);\n"
    "border-radius:20px\n"
    "")
            self.violationinfor.setObjectName("violationinfor")
            self.licenseplate = QtWidgets.QLabel(self.violationinfor)
            self.licenseplate.setGeometry(QtCore.QRect(100, 15, 90, 16))
            self.licenseplate.setStyleSheet("color: rgb(255, 255, 255);")
            self.licenseplate.setObjectName("licenseplate")
            licensePlate = db.collection('violation').document(a.id).get().get("licenseplate")
            self.licenseplate.setText(licensePlate)
            self.downloadvideoviolation = QtWidgets.QPushButton(self.violationinfor)
            self.downloadvideoviolation.setGeometry(QtCore.QRect(710, 25, 93, 30))
            self.downloadvideoviolation.setText("")
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("C:/Users/xuanp/Downloads/icons8-downloading-updates-24.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.downloadvideoviolation.setIcon(icon)
            self.downloadvideoviolation.setObjectName("downloadvideoviolation")
            self.label_liscense = QtWidgets.QLabel(self.violationinfor)
            self.label_liscense.setGeometry(QtCore.QRect(10, 15, 70, 16))
            self.label_liscense.setStyleSheet("color: rgb(255, 255, 255);")
            self.label_liscense.setObjectName("label_liscense")
            self.label_violation = QtWidgets.QLabel(self.violationinfor)
            self.label_violation.setGeometry(QtCore.QRect(10, 45, 70, 16))
            self.label_violation.setStyleSheet("color: rgb(255, 255, 255);")
            self.label_violation.setObjectName("label_violation")
            self.violationoflicense = QtWidgets.QLabel(self.violationinfor)
            self.violationoflicense.setGeometry(QtCore.QRect(100, 45, 91, 16))
            self.violationoflicense.setStyleSheet("color: rgb(255, 255, 255);")
            self.violationoflicense.setObjectName("violationoflicense")
            violationinforlicenseplate = db.collection('violation').document(a.id).get().get("violation")
            self.violationoflicense.setText(violationinforlicenseplate)
            self.label_timestamp = QtWidgets.QLabel(self.violationinfor)
            self.label_timestamp.setGeometry(QtCore.QRect(220, 15, 70, 16))
            self.label_timestamp.setStyleSheet("color: rgb(255, 255, 255);")
            self.label_timestamp.setObjectName("label_timestamp")
            self.timestamp = QtWidgets.QLabel(self.violationinfor)
            self.timestamp.setGeometry(QtCore.QRect(300, 15, 145, 16))
            self.timestamp.setStyleSheet("color: rgb(255, 255, 255);")
            self.timestamp.setObjectName("timestamp")
            timeStamp = db.collection('violation').document(a.id).get().get("time")
            self.timestamp.setText("12:20:43 01/01/2023")
            self.label_local = QtWidgets.QLabel(self.violationinfor)
            self.label_local.setGeometry(QtCore.QRect(220, 45, 70, 16))
            self.label_local.setStyleSheet("color: rgb(255, 255, 255);")
            self.label_local.setObjectName("label_local")
            self.location = QtWidgets.QLabel(self.violationinfor)
            self.location.setGeometry(QtCore.QRect(300, 45, 145, 16))
            self.location.setStyleSheet("color: rgb(255, 255, 255);")
            self.location.setObjectName("location")
            locaTion = db.collection('violation').document(a.id).get().get("local")
            self.location.setText(locaTion)
            self.item = QListWidgetItem()
            self.item.setSizeHint(QSize(200,100))
            self.ui.listviolation.addItem(self.item)
            self.ui.listviolation.setItemWidget(self.item,self.violationinfor)
            self.id = a.id
            self.list_item_widgets.append((self.item,self.violationinfor,self.downloadvideoviolation,self.id))
            self.label_liscense.setText("Biến số xe:")
            self.label_violation.setText("Lỗi vi phạm:")
            self.label_timestamp.setText( "Thời gian :")
            self.label_local.setText( "Địa điểm :")
            self.violationinfor.installEventFilter(self)
        #video violation
        #user page
    ## Function for searching
    # def on_search_btn_clicked(self):
    #     self.ui.stackedWidget.setCurrentIndex(5)
    #     search_text = self.ui.search_input.text().strip()
    #     if search_text:
    #         self.ui.label_9.setText(search_text)
    def getlistitemcam_from_firbase(self):
        self.list_item_cam=[]
        listcam_setup = db.collection('cameraIp').get()
        try:
            for camera in listcam_setup:
                self.label_namecamonlist = QtWidgets.QPushButton()
                name_cam = db.collection('cameraIp').document(camera.id).get().get('namecam')
                self.label_namecamonlist.setText(name_cam)
                self.label_namecamonlist.setStyleSheet(
                    "background-color:#ffffff;\n"
        "border-radius:20px;\n"
        "border:none\n"
                )
                self.item_addcam = QListWidgetItem()
                self.item_addcam.setSizeHint(QSize(150,40))
                self.ui.listWidget_addcam.addItem(self.item_addcam)
                self.urlgetcam = db.collection('cameraIp').document(camera.id).get().get('Ipcamera')
                self.ui.listWidget_addcam.setItemWidget(self.item_addcam,self.label_namecamonlist)
                self.ui.listWidget_addcam.installEventFilter(self)
                self.camid = camera.id
                self.list_item_cam.append((self.item_addcam,self.label_namecamonlist,self.urlgetcam,self.camid))
                self.label_namecamonlist.installEventFilter(self)
                # try:
                #     item0_laneleft = db.collection('cameraIp').document(camera.id).get().get('point_left1_begin')
                #     item1_laneleft = db.collection('cameraIp').document(camera.id).get().get('point_left1_end')
                #     self.begin = QPoint(item0_laneleft[0],item0_laneleft[1])
                #     self.end = QPoint(item1_laneleft[0],item1_laneleft[1])
                #     pen = QtGui.QPen(QColor(255, 0, 0), 2, QtCore.Qt.SolidLine)
                #     qp.setPen(pen)
                #     qp.drawLine(self.begin, self.end)
                #     qp.drawText(self.begin, str("line left 1"))
                # except:
                #     print(1)
        except:
            print(1)
    ## Function for changing page to user page
    def on_user_btn_clicked(self):
        self.ui.stackedWidget.setCurrentIndex(5)
      
    ## Change QPushButton Checkable status when stackedWidget index changed
    def on_stackedWidget_currentChanged(self, index):
        btn_list = self.ui.full_menu_widget.findChildren(QPushButton)
        for btn in btn_list:
            if index in [5, 6]:
                btn.setAutoExclusive(False)
                btn.setChecked(False)
            else:
                btn.setAutoExclusive(True)
    
    ## functions for changing menu page
    # def on_home_btn_2_toggled(self):
    #     self.ui.stackedWidget.setCurrentIndex(0)
    def on_dashborad_btn_2_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(1)
    def on_listcam_btn_menu_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(2)
    def on_videoviolation_btn_menu_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(3)         
    # def get_list_camera(self):
    def on_statistic_btn_menu_toggled(self):
        self.ui.stackedWidget.setCurrentIndex(4)
    #login
    def functionLogin(self):
        global mail
        Email=''
        page = auth.list_users()
        while page:
            for user in page.users:
                if(self.ui.Email.text() == user.email):
                    #print(user.email)
                    Email = user.email
                    self.mail = Email
                    break
            page=page.get_next_page()
        passwords=''
        if(not Email):
            print('error')
        else:
            passwords = db.collection('account').document(Email).get().get("pass")
            if(passwords == self.ui.password.text()):
                self.ui.widget.hide()
                self.ui.centralapp.show()
                name = db.collection('account').document(Email).get().get("name")
                self.ui.nameInfor.setText(name)
                print("login successful")
                #user page
                nameuser = db.collection('account').document(self.mail).get().get("name")
                dateofbirth = db.collection('account').document(self.mail).get().get("dateofbirth")
                nphone = db.collection('account').document(self.mail).get().get("nphone")
                emailuser = db.collection('account').document(self.mail).get().get("email")
                self.ui.nameuser.setText(nameuser)
                self.ui.nametxt.setText(nameuser)
                self.ui.datetxt.setText(dateofbirth)
                self.ui.nphonetxt.setText(nphone)
                self.ui.emailtxt.setText(emailuser)
    def showPass(self):
        self.ui.Hidepassword.show()
        self.ui.Showpassword.hide()
        self.ui.password.setEchoMode(QtWidgets.QLineEdit.Normal)        
    def hidePass(self):
        self.ui.Hidepassword.hide()
        self.ui.Showpassword.show()
        self.ui.password.setEchoMode(QtWidgets.QLineEdit.Password)
    def functionLogout(self):
        self.ui.centralapp.hide()
        self.ui.widget.show()
    def eventFilter(self,obj,event):
        pointer_to_widget = obj
        if event.type() == QEvent.MouseButtonPress:
            for i in self.list_item_widgets:
                i[2].hide()
        if event.type() == QEvent.MouseButtonPress:
            for i in self.list_item_widgets:
                if pointer_to_widget == i[1]:
                    i[2].show()
                    vidid =i[3]
                    i[2].clicked.connect(lambda: self.download(vidid))
            for i in self.list_item_cam:
                if pointer_to_widget == i[1]:
                    self.ui.widget_setupcam.show()
                    link_cameraIp = str(i[2])
                    retval, img = getFrame(link_cameraIp, 1)
                    qImg = QtImage(self.screen, img)
                    self.ui.Draw_line.setImage(qImg)
                    self.id_camsetup = i[3]
                    cam_id = i[3]
                    # self.ui.removecam_btn.clicked.connet(lambda: self.functionremovecam(cam_id))
        return super(MainApplication,self).eventFilter(obj,event)
    # def funtionremovecam(self,id):
    #     db.collection('cameraIp').docment(id).delete()
    #     self.ui.listWidget_addcam.remove
    #     self.getlistitemcam_from_firbase()
    def download(self,id):
        licensePlate = db.collection('violation').document(id).get().get("licenseplate")
        violationinforlicenseplate = db.collection('violation').document(id).get().get("violation")
        timeStamp = db.collection('violation').document(id).get().get("time")
        locaTion = db.collection('violation').document(id).get().get("local")
        store.child("/"+id+".mp4").download(id+".mp4",licensePlate +"_"+locaTion+".mp4")
    def functionOpenaddcamera(self):
        self.ui.widget_addcam.show()
        self.ui.widget_setupcam.hide()
    def functionAddcamera(self):
        self.label_namecamonlist = QtWidgets.QPushButton()
        self.label_namecamonlist.setText(self.ui.namecam_inout.text())
        self.label_namecamonlist.setStyleSheet(
            "background-color:#ffffff;\n"
"border-radius:20px;\n"
"border:none\n"
        )
        self.item_addcam = QListWidgetItem()
        self.item_addcam.setSizeHint(QSize(150,40))
        self.ui.listWidget_addcam.addItem(self.item_addcam)
        self.urlgetcam = self.ui.linkcam_input.text()
        self.ui.listWidget_addcam.setItemWidget(self.item_addcam,self.label_namecamonlist)
        self.ui.listWidget_addcam.installEventFilter(self)
        data ={"Ipcamera":str(self.ui.linkcam_input.text()),"namecam":str(self.ui.namecam_inout.text()),"district":str(self.ui.district_input.text()),"ward":self.ui.wards_input.text()}
        update_time, id_onfirebase=db.collection("cameraIp").add(data)
        self.list_item_cam.append((self.item_addcam,self.label_namecamonlist,self.urlgetcam,id_onfirebase.id))
        self.label_namecamonlist.installEventFilter(self)
        
    def functionPreviewcamera(self):
        try:
            video_stream_widget = VideoStreamWidget(self.ui.linkcam_input.text())
            while True:
                try:
                    video_stream_widget.show_frame()
                except AttributeError:
                    pass
        except:
            print("link camera empty")
    def Updatefirebase(self):
        try:
            data={'point_left1_begin':[line_left1[0].x(),line_left1[0].y()],'point_left1_end':[line_left1[1].x(),line_left1[1].y()]}
            db.collection("cameraIp").document(self.id_camsetup).update(data)
        except:
            print(1)
        try:
            data={'point_left2_begin':[line_left2[0].x(),line_left2[0].y()],'point_left2_end':[line_left2[1].x(),line_left2[1].y()]}
            db.collection("cameraIp").document(self.id_camsetup).update(data)
        except:
            print(1)
        try:
            data={'point_center1_begin':[line_center1[0].x(),line_center1[0].y()],'point_center1_end':[line_center1[1].x(),line_center1[1].y()]}
            db.collection("cameraIp").document(self.id_camsetup).update(data)
        except:
            print(1)
        try:
            data={'point_center2_begin':[line_center2[0].x(),line_center2[0].y()],'point_center2_end':[line_center2[1].x(),line_center2[1].y()]}
            db.collection("cameraIp").document(self.id_camsetup).update(data)
        except:
            print(1)
        try:
            data={'point_right1_begin':[line_right1[0].x(),line_right1[0].y()],'point_right1_end':[line_right1[1].x(),line_right1[1].y()]}
            db.collection("cameraIp").document(self.id_camsetup).update(data)
        except:
            print(1)
        try:
            data={'point_right2_begin':[line_right2[0].x(),line_right2[0].y()],'point_right2_end':[line_right2[1].x(),line_right2[1].y()]}
            db.collection("cameraIp").document(self.id_camsetup).update(data)
        except:
            print(1)
        try:
            data={'point_rect1_begin':[rect_redlight[0].x(),rect_redlight[0].y()],'point_rect1_end':[rect_redlight[1].x(),rect_redlight[1].y()]}
            db.collection("cameraIp").document(self.id_camsetup).update(data)
        except:
            print(1)
        left_laneSettings ={
            'turn_left_leftlane':self.ui.turn_left_left_lane.isChecked(),
            'turn_right_leftlane':self.ui.turn_right_left_lane.isChecked(),
            'go_forward_leftlane':self.ui.go_forward_left_lane.isChecked(),
            'red_light_leftlane':self.ui.red_light_left.isChecked()
        }
        right_laneSettings ={
            'turn_left_rightlane':self.ui.turn_right_right_lane.isChecked(),
            'turn_right_rightlane':self.ui.turn_right_right_lane.isChecked(),
            'go_forward_rightlane':self.ui.go_forward_right_lane.isChecked(),
            'red_light_rightlane':self.ui.red_light_right.isChecked()
        }
        center_laneSettings ={
            'turn_left_centerlane':self.ui.turn_left_center_lane.isChecked(),
            'turn_right_centerlane':self.ui.turn_right_center_lane.isChecked(),
            'go_forward_centerlane':self.ui.go_forwar_center_lane.isChecked(),
            'red_light_centerlane':self.ui.red_light_center.isChecked()
        }
        db.collection("cameraIp").document(self.id_camsetup).update(left_laneSettings)
        db.collection("cameraIp").document(self.id_camsetup).update(right_laneSettings)
        db.collection("cameraIp").document(self.id_camsetup).update(center_laneSettings)


    #updat mode draw
    def setLeftLane(self):
        self.ui.Draw_line.setMode("lane", "left")

    def setCenterLane(self):
        self.ui.Draw_line.setMode("lane", "center")

    def setRightLane(self):
        self.ui.Draw_line.setMode("lane", "right")

    def setLeftDirect(self):
        self.ui.Draw_line.setMode("direct", "left")

    def setCenterDirect(self):
        self.ui.Draw_line.setMode("direct", "center")

    def setRightDirect(self):
        self.ui.Draw_line.setMode("direct", "right")

    def setRect(self):
        self.ui.Draw_line.setMode("rect", None)

    def GoBack(self):
        self.ui.Draw_line.goBack()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainApplication()
    sys.exit(app.exec_())

