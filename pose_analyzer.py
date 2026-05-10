from ultralytics import YOLO
import cv2
import numpy as np
from collections import deque
from datetime import datetime
import json

class PoseAnalyzer:
    """Advanced Pose Estimation and Activity Recognition System"""
    
    def __init__(self, model_path="yolo26m-pose.pt"):
        self.model = YOLO(model_path)
        self.prev_keypoints = {}
        self.motion_history = deque(maxlen=30)
        self.activity_stats = {
            'Standing': 0,
            'Walking': 0,
            'Squatting': 0,
            'Lifting': 0,
            'Unsafe_Posture': 0
        }
        self.person_tracks = {}
        self.alert_log = []
        
    def calculate_angle(self, p1, p2, p3):
        """Calculate angle between three points"""
        v1 = p1 - p2
        v2 = p3 - p2
        
        cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cosine, -1.0, 1.0))
        return np.degrees(angle)
    
    def detect_activity(self, keypoints, person_id=0):
        """Detect activity from keypoints"""
        if keypoints is None or len(keypoints) == 0:
            return "No Person", False, {}
        
        if person_id >= len(keypoints):
            return "No Person", False, {}
            
        kpts = keypoints[person_id]
        
        # Extract key points (x, y, confidence)
        nose = kpts[0][:2]
        left_shoulder = kpts[5][:2]
        right_shoulder = kpts[6][:2]
        left_elbow = kpts[7][:2]
        right_elbow = kpts[8][:2]
        left_wrist = kpts[9][:2]
        right_wrist = kpts[10][:2]
        left_hip = kpts[11][:2]
        right_hip = kpts[12][:2]
        left_knee = kpts[13][:2]
        right_knee = kpts[14][:2]
        left_ankle = kpts[15][:2]
        right_ankle = kpts[16][:2]
        
        # Calculate angles
        left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)
        
        # Calculate back angle (posture)
        shoulder_center = (left_shoulder + right_shoulder) / 2
        hip_center = (left_hip + right_hip) / 2
        back_angle = self.calculate_angle(nose, shoulder_center, hip_center)
        
        angles = {
            'left_elbow': left_elbow_angle,
            'right_elbow': right_elbow_angle,
            'left_knee': left_knee_angle,
            'right_knee': right_knee_angle,
            'back': back_angle
        }
        
        # Detect unsafe posture
        unsafe = False
        activity = "Standing"
        
        # Squatting detection
        if left_knee_angle < 110 or right_knee_angle < 110:
            activity = "Squatting"
            if back_angle < 140:  # Bad back posture while squatting
                unsafe = True
                activity = "Unsafe Squat"
        
        # Lifting detection
        elif (left_elbow_angle < 100 or right_elbow_angle < 100) and \
             (left_knee_angle > 140 and right_knee_angle > 140):
            activity = "Lifting"
            if back_angle < 150:  # Bending back while lifting
                unsafe = True
                activity = "Unsafe Lift"
        
        # Walking detection
        elif abs(left_knee_angle - right_knee_angle) > 30:
            activity = "Walking"
        
        # Standing
        elif left_knee_angle > 160 and right_knee_angle > 160:
            activity = "Standing"
        
        return activity, unsafe, angles
    
    def calculate_speed(self, curr_kpts, person_id):
        """Calculate movement speed"""
        if person_id not in self.prev_keypoints:
            return 0
        
        prev_kpts = self.prev_keypoints[person_id]
        
        # Calculate center point movement
        curr_center = np.mean(curr_kpts[:, :2], axis=0)
        prev_center = np.mean(prev_kpts[:, :2], axis=0)
        
        distance = np.linalg.norm(curr_center - prev_center)
        return distance
    
    def track_person(self, keypoints):
        """Simple person tracking based on position"""
        if keypoints is None or len(keypoints) == 0:
            return []
        
        person_ids = []
        
        for i, kpts in enumerate(keypoints):
            center = np.mean(kpts[:, :2], axis=0)
            
            # Find closest previous person
            min_dist = float('inf')
            matched_id = None
            
            for pid, prev_center in self.person_tracks.items():
                dist = np.linalg.norm(center - prev_center)
                if dist < min_dist and dist < 100:  # threshold
                    min_dist = dist
                    matched_id = pid
            
            if matched_id is None:
                matched_id = len(self.person_tracks)
            
            self.person_tracks[matched_id] = center
            person_ids.append(matched_id)
        
        return person_ids
    
    def analyze_frame(self, frame, frame_number=0):
        """Main analysis function"""
        results = self.model(frame, conf=0.5, verbose=False)
        
        annotated = results[0].plot()
        keypoints = results[0].keypoints.data.cpu().numpy() if results[0].keypoints is not None else None
        
        frame_info = {
            'frame': frame_number,
            'timestamp': datetime.now().isoformat(),
            'persons': []
        }
        
        if keypoints is not None and len(keypoints) > 0:
            person_ids = self.track_person(keypoints)
            
            for i, (kpts, pid) in enumerate(zip(keypoints, person_ids)):
                # Detect activity
                activity, unsafe, angles = self.detect_activity(keypoints, i)
                
                # Calculate speed
                speed = self.calculate_speed(kpts, pid)
                self.motion_history.append(speed)
                
                # Update statistics
                if activity in self.activity_stats:
                    self.activity_stats[activity] += 1
                if unsafe:
                    self.activity_stats['Unsafe_Posture'] += 1
                
                # Store person info
                person_info = {
                    'id': int(pid),
                    'activity': activity,
                    'unsafe': unsafe,
                    'speed': float(speed),
                    'angles': {k: float(v) for k, v in angles.items()}
                }
                frame_info['persons'].append(person_info)
                
                # Log alerts
                if unsafe:
                    alert = {
                        'frame': frame_number,
                        'person_id': int(pid),
                        'activity': activity,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.alert_log.append(alert)
                
                # Draw info on frame
                center = np.mean(kpts[:, :2], axis=0).astype(int)
                color = (0, 0, 255) if unsafe else (0, 255, 0)
                
                cv2.putText(annotated, f"ID:{pid} - {activity}", 
                           (center[0] - 50, center[1] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                if unsafe:
                    cv2.putText(annotated, "⚠ UNSAFE!", 
                               (center[0] - 50, center[1] - 40),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Update tracking
                self.prev_keypoints[pid] = kpts
        
        # Draw statistics on frame
        y_offset = 30
        avg_speed = np.mean(self.motion_history) if len(self.motion_history) > 0 else 0
        
        cv2.putText(annotated, f"Frame: {frame_number}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(annotated, f"Persons: {len(keypoints) if keypoints is not None else 0}", 
                   (10, y_offset + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(annotated, f"Avg Speed: {avg_speed:.2f}", (10, y_offset + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated, frame_info
    
    def get_report(self):
        """Generate final analysis report"""
        total_frames = sum(self.activity_stats.values())
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_frames': total_frames,
            'activity_statistics': self.activity_stats,
            'activity_percentages': {
                k: (v / total_frames * 100) if total_frames > 0 else 0 
                for k, v in self.activity_stats.items()
            },
            'total_alerts': len(self.alert_log),
            'alerts': self.alert_log[-10:],  # Last 10 alerts
            'safety_score': self._calculate_safety_score()
        }
        
        return report
    
    def _calculate_safety_score(self):
        """Calculate overall safety score (0-100)"""
        total = sum(self.activity_stats.values())
        if total == 0:
            return 100
        
        unsafe_ratio = self.activity_stats['Unsafe_Posture'] / total
        safety_score = max(0, 100 - (unsafe_ratio * 200))  # Penalty for unsafe postures
        
        return round(safety_score, 2)
    
    def reset(self):
        """Reset analyzer state"""
        self.prev_keypoints = {}
        self.motion_history.clear()
        self.activity_stats = {k: 0 for k in self.activity_stats}
        self.person_tracks = {}
        self.alert_log = []