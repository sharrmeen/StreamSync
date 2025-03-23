# # import os
# # import subprocess
# # from pathlib import Path

# # # Configuration
# # VIDEO_DIR = "videos"
# # VIDEO_IDS = ["video1", "video2", "video3", "video4", "video5", "video6"]

# # def run_command(command, error_message):
# #     """Run a shell command and handle errors."""
# #     try:
# #         result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
# #         print(result.stdout)
# #         return True
# #     except subprocess.CalledProcessError as e:
# #         print(f"{error_message}: {e}")
# #         print(f"Error output: {e.stderr}")
# #         return False

# # def get_video_duration(video_path):
# #     """Get the duration of a video or segment using ffprobe."""
# #     command = f'ffprobe -i "{video_path}" -show_entries format=duration -v quiet -of csv="p=0"'
# #     try:
# #         result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
# #         duration = float(result.stdout.strip())
# #         return duration
# #     except subprocess.CalledProcessError as e:
# #         print(f"Error getting duration for {video_path}: {e}")
# #         return 0

# # def segment_video(video_id):
# #     """Segment a video into 2-second HLS segments without duration loss."""
# #     input_path = f"{VIDEO_DIR}/{video_id}.mp4"
# #     output_dir = f"{VIDEO_DIR}/{video_id}"
# #     segment_pattern = f"{output_dir}/segment_%03d.ts"
# #     playlist_path = f"{output_dir}/playlist.m3u8"

# #     # Create output directory if it doesn't exist
# #     Path(output_dir).mkdir(parents=True, exist_ok=True)

# #     # Verify input file exists
# #     if not os.path.exists(input_path):
# #         print(f"Input file {input_path} not found!")
# #         return False

# #     # Get original video duration
# #     original_duration = get_video_duration(input_path)
# #     if original_duration <= 0:
# #         print(f"Could not determine duration for {video_id}!")
# #         return False
# #     print(f"{video_id} original duration: {original_duration:.2f} seconds")

# #     # FFmpeg command to segment with forced keyframes and strict time splitting
# #     command = (
# #         f'ffmpeg -i "{input_path}" -force_key_frames "expr:gte(t,n_forced*2)" '
# #         f'-c:v libx264 -c:a aac -hls_time 2 -hls_strict 1 -hls_list_size 0 '
# #         f'-hls_flags +split_by_time -hls_segment_type mpegts -avoid_negative_ts 1 '
# #         f'-hls_segment_filename "{segment_pattern}" "{playlist_path}" -y'
# #     )
# #     if not run_command(command, f"Failed to segment {video_id}"):
# #         return False

# #     # Verify segment count
# #     expected_segments = int(original_duration // 2)
# #     if original_duration % 2 > 0:  # If there's a remainder, add one more segment
# #         expected_segments += 1
# #     actual_segments = len([f for f in os.listdir(output_dir) if f.startswith("segment_") and f.endswith(".ts")])
# #     print(f"{video_id}: Expected {expected_segments} segments, got {actual_segments} segments")
    
# #     if actual_segments != expected_segments:
# #         print(f"Warning: Segment count mismatch for {video_id}! Check FFmpeg output or video duration.")
# #         return False

# #     # Verify segment durations and total duration
# #     total_segment_duration = 0
# #     segment_durations = []
# #     for i in range(actual_segments):
# #         segment_path = f"{output_dir}/segment_{i:03d}.ts"
# #         duration = get_video_duration(segment_path)
# #         segment_durations.append(duration)
# #         total_segment_duration += duration
# #         if i == actual_segments - 1 and duration < 1.9:
# #             print(f"Last segment {segment_path} is {duration:.2f}s (shorter than 2s, which is expected)")
# #         elif not (1.95 <= duration <= 2.05):  # Tighter range to catch discrepancies
# #             print(f"Warning: Segment {segment_path} duration is {duration:.2f}s, expected ~2s")
# #             return False

# #     print(f"{video_id} segment durations: {[f'{d:.2f}' for d in segment_durations]}")
# #     print(f"{video_id} total segment duration: {total_segment_duration:.2f} seconds")
# #     duration_diff = abs(total_segment_duration - original_duration)
# #     if duration_diff > 0.1:  # Allow small variance due to timestamp rounding
# #         print(f"Error: Duration mismatch for {video_id}! Original: {original_duration:.2f}s, Segmented: {total_segment_duration:.2f}s")
# #         return False

# #     return True

# # def main():
# #     """Main function to segment all videos."""
# #     for video_id in VIDEO_IDS:
# #         print(f"\nProcessing {video_id}...")
        
# #         # Segment the video
# #         if not segment_video(video_id):
# #             print(f"Failed to segment {video_id}.")
# #             continue
        
# #         print(f"Successfully segmented {video_id}!")

# # if __name__ == "__main__":
# #     main()

# # import os
# # import subprocess
# # from pathlib import Path

# # # Configuration
# # VIDEO_DIR = "videos"
# # VIDEO_IDS = ["video1", "video2", "video3", "video4", "video5", "video6"]

# # def get_video_duration(video_path):
# #     """Get the duration of a video or segment using ffprobe."""
# #     command = f'ffprobe -i "{video_path}" -show_entries format=duration -v quiet -of csv="p=0"'
# #     try:
# #         result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
# #         duration = float(result.stdout.strip())
# #         return duration
# #     except subprocess.CalledProcessError as e:
# #         print(f"Error getting duration for {video_path}: {e}")
# #         return None
# #     except ValueError:
# #         print(f"Error: Could not parse duration for {video_path}")
# #         return None

# # def check_last_segment_duration(video_id):
# #     """Check the duration of the last segment for a given video."""
# #     output_dir = f"{VIDEO_DIR}/{video_id}"

# #     # Check if the directory exists
# #     if not os.path.exists(output_dir):
# #         print(f"Directory {output_dir} not found!")
# #         return False

# #     # Get the list of segment files
# #     segment_files = [f for f in os.listdir(output_dir) if f.startswith("segment_") and f.endswith(".ts")]
# #     if not segment_files:
# #         print(f"No segments found for {video_id}!")
# #         return False

# #     # Sort segments to find the last one
# #     segment_files.sort()
# #     last_segment_file = segment_files[-1]  # e.g., segment_022.ts
# #     last_segment_path = f"{output_dir}/{last_segment_file}"

# #     # Get the duration of the last segment
# #     duration = get_video_duration(last_segment_path)
# #     if duration is None:
# #         print(f"Failed to get duration for {last_segment_path}!")
# #         return False

# #     print(f"Last segment duration for {video_id} ({last_segment_file}): {duration:.2f} seconds")
# #     return True

# # def main():
# #     """Main function to check the last segment duration for all videos."""
# #     for video_id in VIDEO_IDS:
# #         print(f"\nChecking last segment for {video_id}...")
# #         if not check_last_segment_duration(video_id):
# #             print(f"Failed to check last segment duration for {video_id}.")
# #             continue
# #         print(f"Successfully checked {video_id}!")

# # if __name__ == "__main__":
# #     main()

# import os
# import boto3
# from pathlib import Path

# # Configuration
# VIDEO_DIR = "videos"
# S3_BUCKET = "streamsync-videos-meen"
# S3_REGION = "ap-south-1"
# VIDEO_IDS = ["video1", "video2", "video3", "video4", "video5", "video6"]

# # Initialize S3 client
# s3_client = boto3.client('s3', region_name=S3_REGION)

# def clear_s3_directory(video_id):
#     """Clear existing .ts files in the S3 directory for the given video."""
#     s3_prefix = f"videos/{video_id}/"
#     print(f"Clearing existing S3 contents for {s3_prefix}...")

#     try:
#         # List objects in the S3 prefix
#         response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=s3_prefix)
#         if 'Contents' not in response:
#             print(f"No existing files found in {s3_prefix}.")
#             return True

#         # Filter for .ts files and delete them
#         objects_to_delete = [
#             {'Key': obj['Key']}
#             for obj in response['Contents']
#             if obj['Key'].endswith('.ts')
#         ]
#         if not objects_to_delete:
#             print(f"No .ts files to delete in {s3_prefix}.")
#             return True

#         # Delete the objects
#         s3_client.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': objects_to_delete})
#         print(f"Deleted {len(objects_to_delete)} .ts files from {s3_prefix}.")
#         return True
#     except Exception as e:
#         print(f"Error clearing S3 contents for {s3_prefix}: {e}")
#         return False

# def upload_to_s3(video_id):
#     """Upload all .ts files from the video folder to S3."""
#     local_dir = f"{VIDEO_DIR}/{video_id}"
#     s3_prefix = f"videos/{video_id}"

#     # Check if the local directory exists
#     if not os.path.exists(local_dir):
#         print(f"Local directory {local_dir} not found!")
#         return False

#     # Get the list of .ts files
#     segment_files = [f for f in os.listdir(local_dir) if f.endswith('.ts') and f.startswith('segment_')]
#     if not segment_files:
#         print(f"No .ts files found in {local_dir}!")
#         return False

#     # Clear existing S3 contents
#     if not clear_s3_directory(video_id):
#         return False

#     # Upload each .ts file to S3
#     print(f"Uploading {len(segment_files)} .ts files to s3://{S3_BUCKET}/{s3_prefix}/...")
#     try:
#         for segment_file in segment_files:
#             local_path = f"{local_dir}/{segment_file}"
#             s3_path = f"{s3_prefix}/{segment_file}"
#             s3_client.upload_file(local_path, S3_BUCKET, s3_path)
#             print(f"Uploaded {local_path} to s3://{S3_BUCKET}/{s3_path}")
#     except Exception as e:
#         print(f"Error uploading files for {video_id}: {e}")
#         return False

#     # Verify the upload
#     try:
#         response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{s3_prefix}/")
#         uploaded_segments = sum(1 for obj in response.get('Contents', []) 
#                                if obj['Key'].endswith('.ts') and 'segment_' in obj['Key'])
#         print(f"S3 {video_id}: Expected {len(segment_files)} segments, got {uploaded_segments} segments")
#         if uploaded_segments != len(segment_files):
#             print(f"Error: S3 segment count mismatch for {video_id}!")
#             return False
#     except Exception as e:
#         print(f"Error verifying S3 contents for {video_id}: {e}")
#         return False

#     return True

# def main():
#     """Main function to upload all video folders to S3."""
#     for video_id in VIDEO_IDS:
#         print(f"\nProcessing {video_id}...")
        
#         # Upload to S3
#         if not upload_to_s3(video_id):
#             print(f"Failed to upload {video_id} to S3.")
#             continue
        
#         print(f"Successfully uploaded {video_id} to S3!")

# if __name__ == "__main__":
#     main()