from flask import Flask, render_template, Response, request, redirect, url_for
import cv2, pyaudio, time, numpy as np
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

def zoomin(x,y):
    while True:
        success, frame = camera.read()
        x1 = x -160
        if x1 < 0:
            x1 = 0
        x2 = x + 160
        if x2 > 640:
            x2 = 640
        y1 = y - 96
        if y1 < 0:
            y1 = 0
        y2 = y + 96
        if y2 > 480:
            y2 = 480
        
        points1 = np.float32([[x1,y1],[x2,y1],[x2,y1],[x2,y2]])
        points2 = np.float32([[0,0],[320,0],[0,192],[320,192]])

        m = cv2.getPerspectiveTransform(points1,points2)
        distance = cv2.warpPerspective(frame,m,(320,192))

        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg',distance)
            frame = distance.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: iamge/jpeg\r\n\r\n' + frame + b'\r\n')
            
camera = cv2.VideoCapture(1)

def gen_frames(camera):
    if not camera.isOpened():
        camera = cv2.VideoCapture(1)
    while True:
        success, frame = camera.read()
        #detector = cv2.CascadeClassifier('libcascades/lbpcascade_frontalface_improved.xml')
        #faces = detector.detectMultiScale(frame, 1.2, 6)   
        #for(x,y,w,h) in faces:
            #frame_path = ''
            #cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0),3)
            #face detection saving
            #frame_path = 'static/frame_'+str(time.time())+'.jpg'
            #cv2.imwrite(frame_path,frame)
            #add_snapshot(frame_path)
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg',frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: iamge/jpeg\r\n\r\n' + frame + b'\r\n')
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5

audio = pyaudio.PyAudio()

def genHeader(sample_rate, bits_per_sample, channels):
    datasize = 2000*10**6
    output = bytes("RIFF",'ascii')
    output += (datasize + 36).to_bytes(4, 'little')
    output += bytes("WAVE",'ascii')
    output += bytes("fmt ",'ascii')
    output += (16).to_bytes(4,'little')
    output += (1).to_bytes(2,'little')
    output += (channels).to_bytes(2,'little')
    output += (sample_rate).to_bytes(4,'little')
    output += (sample_rate * channels * bits_per_sample //8).to_bytes(4,'little')
    output += (channels * bits_per_sample //8).to_bytes(2,'little')
    output += (bits_per_sample).to_bytes(2,'little')
    output += bytes("data",'ascii')
    output += (datasize).to_bytes(4,'little')
    return output


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

@app.route('/audio_feed')
def audio_feed():
    def sound():
        CHUNK = 1024
        sampleRate = 44100
        bitPerSample = 16
        channels = 1
        wav_header = genHeader(sampleRate,bitPerSample,channels)
        stream = audio.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,input_device_index=1, frames_per_buffer=CHUNK)
        print('recording...')
        first_run = True
        while True:
            if first_run:
                data = wav_header +stream.read(CHUNK)
                first_run = False
            else:
                data = stream.read(CHUNK)
            yield(data)
    return Response(sound(), mimetype='audio/x-wav')

@app.route('/video_feed_zoom')
def video_feed_zoom():
    return Response(gen_frames(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/zoomed')
def zoomed():
    return render_template('zoomed.html')

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
    app.run(host='0.0.0.0',port=80, threaded=True)       

