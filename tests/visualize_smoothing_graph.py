"""
Issue #4 DoD Verification: Graph showing smoothed vs raw angle data.
This script processes video files, calculates elbow angle, and plots the results.
"""
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import time

from src.processor.pose import PoseDetector
from src.utils.smoothing import LandmarkSmoother
from src.utils.geometry import calculate_angle


def visualize_smoothing_effect_from_video(video_path: str, output_prefix: str = "smoothing"):
    """
    Process video file and compare raw vs smoothed elbow angle over time.
    
    Args:
        video_path: Path to the video file (MP4)
        output_prefix: Prefix for output graph filename
    """
    # Validate video file exists
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"Error: Video file not found at {video_path}")
        return
    
    # Initialize components
    detector = PoseDetector(
        smooth_landmarks=False,  # Disable MediaPipe smoothing to see our filter's effect
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    smoother = LandmarkSmoother(window_size=5, min_visibility=0.5)
    
    # Data storage
    frame_numbers = []
    timestamps = []
    raw_angles = []
    smoothed_angles = []
    visibility_values = []  # Track visibility to see when landmarks are occluded
    
    # Video capture
    cap = cv2.VideoCapture(str(video_path))
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"Processing video: {video_file.name}")
    print(f"FPS: {fps:.2f}, Total frames: {total_frames}, Duration: {duration:.2f}s")
    print("Press 'q' to quit early.\n")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            current_time = frame_count / fps if fps > 0 else frame_count * 0.033
            
            # Detect landmarks
            raw_landmarks = detector.detect(frame)
            
            if raw_landmarks:
                # Apply smoothing
                smoothed_landmarks = smoother.update(raw_landmarks)
                
                # Calculate right elbow angle (landmarks: 12-shoulder, 14-elbow, 16-wrist)
                # MediaPipe Pose landmark indices:
                # https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md
                try:
                    # Check if elbow landmark is visible enough
                    elbow_visibility = raw_landmarks[14]['visibility']
                    
                    raw_angle = calculate_angle(
                        raw_landmarks[12],  # Right shoulder
                        raw_landmarks[14],  # Right elbow
                        raw_landmarks[16]   # Right wrist
                    )
                    
                    smoothed_angle = calculate_angle(
                        smoothed_landmarks[12],
                        smoothed_landmarks[14],
                        smoothed_landmarks[16]
                    )
                    
                    # Store data
                    frame_numbers.append(frame_count)
                    timestamps.append(current_time)
                    raw_angles.append(raw_angle)
                    smoothed_angles.append(smoothed_angle)
                    visibility_values.append(elbow_visibility)
                    
                    # Display on frame
                    cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(frame, f"Raw: {raw_angle:.1f}deg", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, f"Smoothed: {smoothed_angle:.1f}deg", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"Visibility: {elbow_visibility:.2f}", (10, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Show progress
                    if frame_count % 30 == 0:
                        progress = (frame_count / total_frames) * 100
                        print(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
                    
                except (KeyError, IndexError):
                    pass  # Landmarks not visible
            
            # Show video (scaled down if too large)
            display_frame = frame.copy()
            height, width = display_frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                display_frame = cv2.resize(display_frame, None, fx=scale, fy=scale)
            
            cv2.imshow('Smoothing Test - Processing Video', display_frame)
            
            # Allow early exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\nProcessing interrupted by user.")
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()
        
        processing_time = time.time() - start_time
        print(f"\nProcessing completed in {processing_time:.2f}s")
        print(f"Processed {frame_count} frames, captured {len(timestamps)} angle measurements")
    
    # Plot results
    if timestamps:
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
        
        # Plot 1: Angles comparison
        ax1.plot(timestamps, raw_angles, 'r-', alpha=0.4, label='Raw Angle', linewidth=1)
        ax1.plot(timestamps, smoothed_angles, 'g-', label='Smoothed Angle', linewidth=2)
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Elbow Angle (degrees)')
        ax1.set_title(f'Landmark Smoothing Effect - {video_file.name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Calculate and display jitter metrics
        if len(raw_angles) > 1:
            raw_jitter = sum(abs(raw_angles[i] - raw_angles[i-1]) 
                            for i in range(1, len(raw_angles))) / (len(raw_angles) - 1)
            smoothed_jitter = sum(abs(smoothed_angles[i] - smoothed_angles[i-1]) 
                                 for i in range(1, len(smoothed_angles))) / (len(smoothed_angles) - 1)
            
            jitter_reduction = ((raw_jitter - smoothed_jitter) / raw_jitter * 100) if raw_jitter > 0 else 0
            
            textbox = f'Raw Jitter: {raw_jitter:.2f}°/frame\n'
            textbox += f'Smoothed Jitter: {smoothed_jitter:.2f}°/frame\n'
            textbox += f'Reduction: {jitter_reduction:.1f}%'
            
            ax1.text(0.02, 0.98, textbox, transform=ax1.transAxes, 
                    verticalalignment='top', fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Plot 2: Angle difference (jitter visualization)
        if len(raw_angles) > 1:
            raw_diffs = [abs(raw_angles[i] - raw_angles[i-1]) for i in range(1, len(raw_angles))]
            smoothed_diffs = [abs(smoothed_angles[i] - smoothed_angles[i-1]) for i in range(1, len(smoothed_angles))]
            
            ax2.plot(timestamps[1:], raw_diffs, 'r-', alpha=0.5, label='Raw Jitter', linewidth=1)
            ax2.plot(timestamps[1:], smoothed_diffs, 'g-', label='Smoothed Jitter', linewidth=2)
            ax2.set_xlabel('Time (seconds)')
            ax2.set_ylabel('Frame-to-frame Angle Change (degrees)')
            ax2.set_title('Jitter Comparison (lower is better)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Visibility over time
        ax3.plot(timestamps, visibility_values, 'b-', linewidth=1.5, label='Elbow Visibility')
        ax3.axhline(y=0.5, color='orange', linestyle='--', linewidth=1, label='Visibility Threshold (0.5)')
        ax3.fill_between(timestamps, 0, visibility_values, alpha=0.3)
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Visibility Score')
        ax3.set_title('Landmark Visibility Over Time')
        ax3.set_ylim([0, 1.1])
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Highlight low-visibility regions
        for i in range(len(visibility_values)):
            if visibility_values[i] < 0.5:
                ax3.axvspan(timestamps[i] - 0.03, timestamps[i] + 0.03, 
                           color='red', alpha=0.1)
        
        plt.tight_layout()
        
        # Save graph
        output_filename = f'{output_prefix}_{video_file.stem}.png'
        plt.savefig(output_filename, dpi=150)
        print(f"\nGraph saved as '{output_filename}'")
        
        # Show plot
        plt.show()
        
        # Print summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)
        print(f"Video: {video_file.name}")
        print(f"Duration: {duration:.2f}s")
        print(f"Frames analyzed: {len(timestamps)}")
        print(f"Average visibility: {sum(visibility_values)/len(visibility_values):.3f}")
        print(f"Min visibility: {min(visibility_values):.3f}")
        print(f"Frames with low visibility (<0.5): {sum(1 for v in visibility_values if v < 0.5)}")
        
        if len(raw_angles) > 1:
            print(f"\nRaw angle jitter: {raw_jitter:.2f}°/frame")
            print(f"Smoothed angle jitter: {smoothed_jitter:.2f}°/frame")
            print(f"Jitter reduction: {jitter_reduction:.1f}%")
        print("="*60)
        
    else:
        print("No data captured. Ensure the video contains a visible person.")


def process_all_test_videos():
    """
    Process all test videos in the media/test_videos directory.
    """
    test_videos = [
        "media/test_videos/video_test_smoothing_1.mp4",
        "media/test_videos/video_test_smoothing_2.mp4"
    ]
    
    for video_path in test_videos:
        if Path(video_path).exists():
            print("\n" + "="*70)
            visualize_smoothing_effect_from_video(video_path, output_prefix="smoothing_verification")
            print("="*70 + "\n")
        else:
            print(f"Skipping {video_path} - file not found")


if __name__ == "__main__":
    # Process both test videos
    process_all_test_videos()
    
    # Or process a single video:
    # visualize_smoothing_effect_from_video(
    #     "media/test_videos/video_test_smoothing_1.mp4",
    #     output_prefix="smoothing_verification"
    # )