from flask import Flask, render_template, request, jsonify, Response, send_file, send_from_directory
import cv2
import os
import json
from werkzeug.utils import secure_filename
from pose_analyzer import PoseAnalyzer
from datetime import datetime
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULTS_FOLDER'] = 'data/results'
app.config['ANALYSIS_FOLDER'] = 'data/analysis'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)

# Global variables
analyzer = None
camera = None
processing_status = {'active': False, 'progress': 0, 'current_file': None, 'output_file': None}

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Upload video page"""
    return render_template('upload.html')

@app.route('/live')
def live_page():
    """Live webcam page"""
    return render_template('live.html')

@app.route('/dashboard')
def dashboard_page():
    """Analytics dashboard"""
    # Get latest analysis files
    analysis_files = sorted(os.listdir(app.config['ANALYSIS_FOLDER']), reverse=True)
    latest_report = None
    
    if analysis_files:
        with open(os.path.join(app.config['ANALYSIS_FOLDER'], analysis_files[0]), 'r') as f:
            latest_report = json.load(f)
    
    return render_template('dashboard.html', report=latest_report)

@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload and process video"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)
        
        # Start processing in background
        thread = threading.Thread(target=process_video, args=(filepath, new_filename))
        thread.start()
        
        return jsonify({
            'success': True,
            'filename': new_filename,
            'message': 'Video uploaded successfully. Processing started.'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

def process_video(input_path, filename):
    """Process uploaded video"""
    global processing_status, analyzer
    
    processing_status['active'] = True
    processing_status['progress'] = 0
    processing_status['current_file'] = filename
    processing_status['output_file'] = None
    processing_status.pop('error', None)
    
    try:
        # Initialize analyzer
        analyzer = PoseAnalyzer("yolo26m-pose.pt")
        
        # Open video
        cap = cv2.VideoCapture(input_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_raw = cap.get(cv2.CAP_PROP_FPS)
        fps = int(fps_raw) if fps_raw and fps_raw > 0 else 25
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Some codecs require even dimensions (e.g., H.264). Keep output playable.
        out_w = width - (width % 2)
        out_h = height - (height % 2)
        if out_w <= 0 or out_h <= 0:
            out_w, out_h = width, height
        
        # Output video (force mp4 for browser compatibility)
        base_name, _ext = os.path.splitext(filename)
        output_filename = f'processed_{base_name}.mp4'
        output_path = os.path.join(app.config['RESULTS_FOLDER'], output_filename)

        # Try a few codecs; mp4v is not always supported on Windows builds.
        out = None
        for cc in ('avc1', 'H264', 'mp4v'):
            fourcc = cv2.VideoWriter_fourcc(*cc)
            candidate = cv2.VideoWriter(output_path, fourcc, fps, (out_w, out_h))
            if candidate is not None and candidate.isOpened():
                out = candidate
                break
            try:
                candidate.release()
            except Exception:
                pass

        if out is None:
            raise RuntimeError("Failed to open VideoWriter for MP4 output (tried avc1/H264/mp4v).")
        
        frame_count = 0
        all_data = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze frame
            annotated, frame_info = analyzer.analyze_frame(frame, frame_count)
            if annotated.shape[1] != out_w or annotated.shape[0] != out_h:
                annotated = cv2.resize(annotated, (out_w, out_h), interpolation=cv2.INTER_AREA)
            out.write(annotated)
            all_data.append(frame_info)
            
            frame_count += 1
            processing_status['progress'] = int((frame_count / total_frames) * 100)
        
        cap.release()
        out.release()
        
        # Generate report
        report = analyzer.get_report()
        report['timestamp'] = datetime.now().isoformat()
        report['input_file'] = filename
        report['output_file'] = output_filename
        report['total_frames_processed'] = frame_count
        report['video_duration_seconds'] = frame_count / fps
        report['frame_data'] = all_data
        
        # Save report
        report_filename = f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_path = os.path.join(app.config['ANALYSIS_FOLDER'], report_filename)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        processing_status['active'] = False
        processing_status['progress'] = 100
        processing_status['output_file'] = output_filename
        
    except Exception as e:
        processing_status['active'] = False
        processing_status['error'] = str(e)
        print(f"Error processing video: {e}")

@app.route('/api/status')
def get_status():
    """Get processing status"""
    return jsonify(processing_status)

@app.route('/api/reports')
def get_reports():
    """Get all analysis reports"""
    reports = []
    
    for filename in sorted(os.listdir(app.config['ANALYSIS_FOLDER']), reverse=True):
        filepath = os.path.join(app.config['ANALYSIS_FOLDER'], filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
            reports.append({
                'filename': filename,
                'timestamp': data.get('timestamp'),
                'safety_score': data.get('safety_score'),
                'total_alerts': data.get('total_alerts'),
                'input_file': data.get('input_file')
            })
    
    return jsonify(reports)

@app.route('/api/report/<filename>')
def get_report(filename):
    """Get specific report"""
    filepath = os.path.join(app.config['ANALYSIS_FOLDER'], filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return jsonify(json.load(f))
    
    return jsonify({'error': 'Report not found'}), 404

@app.route('/api/download/<filename>')
def download_video(filename):
    """Download processed video"""
    filepath = os.path.join(app.config['RESULTS_FOLDER'], filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/media/uploads/<path:filename>')
def serve_uploaded_video(filename):
    """Stream uploaded video for in-browser preview."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, conditional=True)

@app.route('/media/results/<path:filename>')
def serve_processed_video(filename):
    """Stream processed video for in-browser preview."""
    return send_from_directory(app.config['RESULTS_FOLDER'], filename, conditional=True)

def generate_webcam_frames():
    """Generate frames from webcam"""
    global analyzer, camera
    
    if analyzer is None:
        analyzer = PoseAnalyzer("yolo26m-pose.pt")
    
    camera = cv2.VideoCapture(0)
    frame_count = 0
    
    try:
        while True:
            success, frame = camera.read()
            if not success:
                break
            
            # Analyze frame
            annotated, _ = analyzer.analyze_frame(frame, frame_count)
            frame_count += 1
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', annotated)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    finally:
        if camera is not None:
            camera.release()

@app.route('/api/webcam_feed')
def webcam_feed():
    """Live webcam feed"""
    return Response(generate_webcam_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/webcam_stats')
def webcam_stats():
    """Get current webcam statistics"""
    global analyzer
    
    if analyzer is None:
        return jsonify({'error': 'Analyzer not initialized'}), 400
    
    report = analyzer.get_report()
    return jsonify(report)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)