from flask import Flask, Response, render_template, request, send_from_directory, jsonify, session
import cv2
import numpy as np
import imutils
import os
import smtplib
from email.message import EmailMessage
from ultralytics import YOLO
from datetime import datetime
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_session import Session

app = Flask(__name__)


app = Flask(__name__, template_folder='Templates')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#code for connection
app.config['MYSQL_HOST'] = 'localhost'#hostname
app.config['MYSQL_USER'] = 'root'#username
app.config['MYSQL_PASSWORD'] = ''#password
app.config['MYSQL_DB'] = 'shoplifting'#database name

mysql = MySQL(app)
@app.route('/')

def main():
    return render_template("index.html")

@app.route('/service', methods=['GET', 'POST'])
def service():
    if request.method == 'GET':
        return(render_template('service.html'))
    
@app.route('/history', methods=['GET', 'POST'])
def history():
    if request.method == 'GET':
        return(render_template('history.html'))
    
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
        return(render_template('admin.html'))
    
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'GET':
        return(render_template('contact.html'))
    
@app.route('/ourai', methods=['GET', 'POST'])
def ourai():
    if request.method == 'GET':
        return(render_template('ourai.html'))
    
@app.route('/joinus', methods=['GET', 'POST'])
def joinus():
    if request.method == 'GET':
        return(render_template('joinus.html'))
    
@app.route('/uploadpage', methods=['GET', 'POST'])
def uploadpage():
    if request.method == 'GET':
        return(render_template('uploadpage.html'))
    
@app.route('/livepage', methods=['GET', 'POST'])
def livepage():
    if request.method == 'GET':
        return(render_template('livepage.html'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone           = request.form['signphone']
        password        = request.form['signpassword']
        msg = 0
        con = mysql.connect
        con.autocommit(True)
        cursor = con.cursor(MySQLdb.cursors.DictCursor)
        
        qry = 'SELECT * FROM userdetail WHERE phone="'+phone+'" AND password="'+password+'"'
        result = cursor.execute(qry)
        result = cursor.fetchone()
        
        if result is not None:
            if result["adminapproved"] != 1:
                msg = "2"
            elif result["adminapproved"] == 1:
                msg = "1"
                session["userid"]   = result["userid"]
                session["username"]   = result["username"]
                session["usermail"]   = result["email"]
        else:
           msg = "0"           
    return jsonify(msg)


# Constants
WIDTH = 500
shoplifting_status = "Suspected Shoplifting"
not_shoplifting_status = "Not Shoplifting"
cls0_rect_color = (0, 255, 255)  # Not Shoplifting (Yellow)
cls1_rect_color = (0, 0, 255)    # Shoplifting (Red)
conf_color = (255, 255, 0)       # Confidence score color
status_color = (0, 0, 255)       # Status color

frame_name = "Shoplifting Detection"
input_source = 0  # Default webcam
output_folder = "static/output"
os.makedirs(output_folder, exist_ok=True)
alert_sent = False  # To ensure email is sent only once

# Load YOLO model
model = YOLO("shoplifting_wights.pt")

def send_email_alert(image_path):
    global alert_sent
    if alert_sent:
        return  # Ensure alert is sent only once

    sender_email = "prithivirajk2503@gmail.com"
    receiver_email = "prithivirajk2503@gmail.com"
    password = "truv nsqk vzfb gvrv"
    
    msg = EmailMessage()
    msg['Subject'] = "Shoplifting Alert – Camera ID 001"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = (
        f"Subject: Shoplifting Alert – Camera ID 001\n\n"
        f"Shoplifting activity has been detected by Camera ID 001 on {current_datetime}. "
        f"Please review the attached image for proof and refer to the relevant footage for further verification.\n\n"
        f"Immediate action is recommended.\n\n"
        f"Best regards,\n"
        f"[SLD]"
    )
    msg.set_content(message)
    
    with open(image_path, 'rb') as img_file:
        msg.add_attachment(img_file.read(), maintype='image', subtype='jpeg', filename='alert.jpg')
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.send_message(msg)
    
    with app.app_context():
        con = mysql.connect
        con.autocommit(True)
        cursor = con.cursor(MySQLdb.cursors.DictCursor)
        history = 'INSERT INTO history(userid, sample, prediction) VALUES("'+str(1)+'","'+str("CCTV01")+'","'+str('Shoplift')+'")'
        cursor.execute(history)
        mysql.connect.commit()
    
    alert_sent = True  # Mark alert as sent

def detect_shoplifting(frame, save_image=False):
    global alert_sent
    frame = imutils.resize(frame, width=WIDTH)
    result = model.predict(frame)
    detections = np.array(result[0].boxes.data)

    if len(detections) != 0:
        xywh = np.array(result[0].boxes.xywh).astype("int32")
        xyxy = np.array(result[0].boxes.xyxy).astype("int32")
        
        for (x1, y1, _, _), (_, _, w, h), (_, _, _, _, conf, clas) in zip(xyxy, xywh, detections):
            conf_percentage = np.round(conf * 100, 2)
            
            if clas == 1:
                if 35 < conf_percentage < 55 or conf_percentage > 75:
                    status = "Suspected Shoplifting"
                    cv2.rectangle(frame, (x1, y1), (x1 + w, y1 + h), cls1_rect_color, 2)
                    cv2.putText(frame, f"{conf_percentage}%", (x1 + 10, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cls1_rect_color, 2)
                    cv2.putText(frame, status, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cls1_rect_color, 2)
                    if save_image:
                        image_path = os.path.join(output_folder, "alert.jpg")
                        cv2.imwrite(image_path, frame)
                        send_email_alert(image_path)
                else:
                    status = "Have a doubt. Follow up!"
                    cv2.rectangle(frame, (x1, y1), (x1 + w, y1 + h), cls0_rect_color, 2)
                    cv2.putText(frame, status, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cls0_rect_color, 2)
                    cv2.putText(frame, f"{conf_percentage}%", (x1 + 10, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cls0_rect_color, 2)
    
    return frame

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    output_path = os.path.join(output_folder, "output.avi")
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    writer = None
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame = detect_shoplifting(frame)
        
        if writer is None:
            writer = cv2.VideoWriter(output_path, fourcc, 20, (frame.shape[1], frame.shape[0]))
        writer.write(frame)
    
    cap.release()
    writer.release()
    return output_path

def generate_frames():
    cap = cv2.VideoCapture(input_source)
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame = detect_shoplifting(frame, save_image=True)
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
    
    cap.release()


@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/upload_video", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        print("DEBUG: No file found in request.files")  # Debugging
        return "No file uploaded", 400
    
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    
    video_path = os.path.join(output_folder, file.filename)
    file.save(video_path)
    processed_video = process_video(video_path)
    
    return f"Video processed and saved at: {processed_video}", 200

@app.route('/updateuserrecord', methods=['GET', 'POST'])
def updateuserrecord():
    if request.method == 'POST':    
        userid    = request.form['userid']
        step      = request.form['step']
        
        con = mysql.connect
        con.autocommit(True)
        cursor = con.cursor(MySQLdb.cursors.DictCursor)
        qry = 'UPDATE userdetail SET adminapproved ='+step+' WHERE userid ='+userid
        cursor.execute(qry)
        msg = "1"
        mysql.connect.commit()
    return msg

#User Login   
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'GET':
        return(render_template('admin.html'))
    if request.method == 'POST':
        msg=''
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            con = mysql.connect
        con.autocommit(True)
        cursor = con.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin_details WHERE admin_name = % s and password = %s', (username, password,))
        result = cursor.fetchone()
        print(result)
        if result:
            msg = "1"
        else:
           msg = "0"
    return msg
    

@app.route('/getuserrecords', methods=['GET', 'POST'])
def getuserrecords():
    if request.method == 'POST':
        con = mysql.connect
        con.autocommit(True)
        cursor = con.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM userdetail WHERE adminapproved = 0')
        result = cursor.fetchall()
        
        return jsonify(result)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username  = request.form['regusername']
        phone        = request.form['regphone']
        email        = request.form['regemail']
        usedfor      = request.form['usingfor']
        password     = request.form['regpassword']
        
        con = mysql.connect
        con.autocommit(True)
        cursor = con.cursor(MySQLdb.cursors.DictCursor)
        
        qry = 'SELECT * FROM userdetail WHERE phone="'+phone+'" AND password="'+password+'"'
        result = cursor.execute(qry)
        result = cursor.fetchone()
        
        if result:
            msg = '2'
        else:
            cursor.execute('INSERT INTO userdetail VALUES (NULL, %s, %s, %s, %s, %s, %s, NULL)', (username, email, phone, usedfor, password, '0', ))
            mysql.connect.commit()
            msg = '1'
        
        return msg
    
@app.route('/gethistory', methods=['GET', 'POST'])
def gethistory():
    if request.method == 'POST':
        con = mysql.connect
        con.autocommit(True)
        cursor = con.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM history')
        result = cursor.fetchall()
        
        return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False)
