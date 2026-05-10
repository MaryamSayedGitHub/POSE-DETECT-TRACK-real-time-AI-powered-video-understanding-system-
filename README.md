# 🚀 PoseGuard v2.0  
### POSE · DETECT · TRACK

PoseGuard is a real-time AI-powered Computer Vision system for **pose estimation**, **object detection**, and **multi-object tracking** using **YOLOv8-Pose**, **OpenCV**, and **Flask**.

The system supports both uploaded videos and live webcam streams while generating annotated outputs, tracking IDs, and analytics reports.
<img width="1665" height="816" alt="Screenshot 2026-05-10 131428" src="https://github.com/user-attachments/assets/a4f65d18-866e-40ac-80ab-788029410a3a" />
![Uploading image.png…]()


---

# ✨ Features

- 🎯 Real-time Pose Estimation
- 🧍 Multi-Object Tracking with Persistent IDs
- 📹 Live Webcam Analysis
- 📂 Video Upload Support (MP4, AVI, MOV, MKV)
- 📊 Analytics Dashboard
- 📝 JSON Session Reports
- 🎥 Annotated Output Videos
- ⚡ Real-Time Inference Pipeline

---

# 🖥️ Demo Interface

## Home Page
- Upload videos
- Start live webcam tracking
- View analytics dashboard

## Video Analysis
- Frame-by-frame pose estimation
- Object detection & tracking
- Export annotated video results

## Live Feed
- Real-time webcam tracking
- Live counters & statistics
- Session monitoring

## Dashboard
- Activity breakdown
- Session summaries
- Tracking analytics

---

# 🛠️ Tech Stack

| Technology | Usage |
|------------|-------|
| Python | Core Programming |
| YOLOv8-Pose | Pose Estimation |
| OpenCV | Video Processing |
| Flask | Web Application |
| NumPy | Numerical Operations |

---

# 📂 Project Structure

```bash
pose-estimation-flask/
│
├── app.py                    # Flask application
├── pose_analyzer.py          # Pose analysis logic
├── requirements.txt          # Dependencies
├── yolo26m-pose.pt           # YOLO model
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── uploads/              # Uploaded videos
│
├── templates/
│   ├── index.html            # Home page
│   ├── upload.html           # Upload video
│   ├── live.html             # Live webcam
│   └── dashboard.html        # Analytics dashboard
│
└── data/
    ├── results/              # Processed videos
    └── analysis/             # JSON reports
```

---

# ⚙️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/pose-estimation-flask.git
cd pose-estimation-flask
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

#### Windows
```bash
venv\Scripts\activate
```

#### Linux / Mac
```bash
source venv/bin/activate
```

---

## 3️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Application

```bash
python app.py
```

Then open:

```bash
http://127.0.0.1:5000
```

---

# 📦 Requirements

```txt
flask
opencv-python
ultralytics
numpy
```

---

# 📸 Supported Formats

- MP4
- AVI
- MOV
- MKV

---

# 🧠 AI Capabilities

✅ Human Pose Estimation  
✅ Object Detection  
✅ Real-Time Tracking  
✅ Multi-Person Monitoring  
✅ Session Analytics  
✅ Movement Analysis  

---

# 📊 Output

The system generates:

- Annotated videos
- Tracking IDs
- JSON reports
- Session statistics
- Activity analytics

---

# 🔥 Future Improvements

- Face Recognition Integration
- Action Recognition
- Cloud Deployment
- Database Support
- Mobile Optimization
- Advanced Analytics

---

# 👩‍💻 Author

**Maryam Sayed Ahmed**  
Junior Computer Vision Engineer & AI Developer

---

# ⭐ If you like this project

Give the repository a ⭐ on GitHub!
