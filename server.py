from flask import Flask, render_template, Response, request, redirect, url_for
import cv2, time 
from flask_sqlalchemy import SQLAlchemy
import os.path as path

db = SQLAlchemy()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///detected_faces.db'

db.init_app(app)

class Snapshots(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, unique=True, nullable=False)

#with app.app_context():
#    db.create_all()

def add_snapshot(path):
    if path:
        shot = Snapshots(
            url = path
        )
        with app.app_context():
            db.session.add(shot)
            db.session.commit()

camera = cv2.VideoCapture(0)

def gen_frames(camera):
    if not camera:
        camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        detector = cv2.CascadeClassifier('libcascades/lbpcascade_frontalface_improved.xml')
        faces = detector.detectMultiScale(frame, 1.2, 6)   
        for(x,y,w,h) in faces:
            frame_path = ''
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0),3)
            frame_path = 'static/frame_'+str(time.time())+'.jpg'
            cv2.imwrite(frame_path,frame)
            add_snapshot(frame_path)
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg',frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: iamge/jpeg\r\n\r\n' + frame + b'\r\n')
            
@app.route('/')
def index():
    return render_template('index.html',stream = {'video_feed':url_for('video_feed'),
                                                  'message':'Videofeed started'})

@app.route('/stopwebcam', methods=['POST'])
def stop_webcam():
    camera.release()
    return render_template('index.html',stream={'video_feed':None,
                                                'message':'Videofeed stopped'})

@app.route('/startwebcam',methods=['GET'])
def start_webcam():
    return redirect(url_for('index'))

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(camera), mimetype='multipart/x-mixed-replace; boundary=frame')     

@app.route('/frames')
def frames():   
    snapshots = db.session.execute(db.select(Snapshots).order_by(Snapshots.id)).scalars()
    return render_template('snapshots.html', pics = snapshots)

@app.route('/shot', methods=['POST'])
def web_cam_shot():
    camera = cv2.VideoCapture(0)
    success, frame = camera.read()
    shot = f'static/shot_{time.time()}.jpg'
    cv2.imwrite(shot,frame)
    add_snapshot(shot)
    camera.release()
    return render_template('shot.html',pic=shot)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)       

