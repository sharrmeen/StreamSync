# # import boto3
# # import random
# # import ffmpeg
# # import os

# # # Connect to DynamoDB
# # dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')  # Your region
# # table = dynamodb.Table('UserSequences')

# # # Directory where original .mp4 files are stored
# # video_folder = "./videos"  # Adjust if needed (e.g., "/Users/sharmeenkhan/StreamSync/videos")

# # # Automatically generate the videos list with durations in seconds
# # def get_video_data():
# #     videos = []
# #     if not os.path.exists(video_folder):
# #         print(f"Error: Directory '{video_folder}' does not exist!")
# #         return videos
    
# #     for filename in os.listdir(video_folder):
# #         if filename.endswith(".mp4"):
# #             video_id = filename.replace(".mp4", "")  # e.g., "video1.mp4" -> "video1"
# #             file_path = os.path.join(video_folder, filename)
# #             try:
# #                 probe = ffmpeg.probe(file_path)
# #                 duration_seconds = float(probe['format']['duration'])  # Duration in seconds
# #                 # Round to nearest second, ensure at least 1 second
# #                 duration = max(1, int(round(duration_seconds)))
# #                 videos.append({"video_id": video_id, "duration": duration})
# #                 print(f"Processed {filename}: {duration} seconds")
# #             except ffmpeg.Error as e:
# #                 print(f"Error processing {filename}: {e}")
# #             except KeyError as e:
# #                 print(f"Error: Could not find duration in {filename} metadata: {e}")
# #     return videos

# # # Function to generate a random sequence for a user
# # def generate_sequence(videos, num_videos):
# #     sequence = []
# #     current_start_time = 0
# #     selected_videos = random.sample(videos, min(num_videos, len(videos)))  # Avoid sampling more than available
# #     for video in selected_videos:
# #         sequence.append({
# #             "video_id": video["video_id"],
# #             "start_time": current_start_time,
# #             "duration": video["duration"]
# #         })
# #         current_start_time += video["duration"]
# #     return sequence

# # # Delete existing users to start fresh
# # for i in range(1, 11):  # user1 to user10
# #     user_id = f"user{i}"
# #     try:
# #         table.delete_item(Key={"user_id": user_id})
# #         print(f"Deleted {user_id} from DynamoDB")
# #     except Exception as e:
# #         print(f"Error deleting {user_id}: {e}")

# # # Main execution
# # videos = get_video_data()  # Get the video data automatically
# # if not videos:
# #     print("No videos found! Check your video_folder path or ensure .mp4 files exist.")
# #     exit()

# # num_users = 10
# # for i in range(1, num_users + 1):
# #     user_id = f"user{i}"
# #     sequence = generate_sequence(videos, random.randint(3, 5))  # 3-5 videos per user
# #     item = {
# #         "user_id": user_id,
# #         "sequence": sequence
# #     }
# #     try:
# #         table.put_item(Item=item)
# #         print(f"Added {user_id} to DynamoDB with sequence: {sequence}")
# #     except Exception as e:
# #         print(f"Error adding {user_id}: {e}")

# # # Verify one item
# # response = table.get_item(Key={"user_id": "user1"})
# # print("Sample item for user1:", response.get("Item"))

# # print("Done!")

# import boto3
# import os
# import subprocess
# import tempfile
# import shutil

# # Configuration
# DYNAMODB_REGION = "ap-south-1"
# TABLE_NAME = "UserSequences"
# S3_BUCKET = "streamsync-videos-meen"
# S3_REGION = "ap-south-1"
# VIDEO_IDS = ["video1", "video2", "video3", "video4", "video5", "video6"]

# # Initialize AWS clients
# dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
# s3_client = boto3.client('s3', region_name=S3_REGION)
# table = dynamodb.Table(TABLE_NAME)

# def get_segment_duration(segment_path):
#     """Get the duration of a segment using ffprobe."""
#     command = f'ffprobe -i "{segment_path}" -show_entries format=duration -v quiet -of csv="p=0"'
#     try:
#         result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
#         duration = float(result.stdout.strip())
#         return duration
#     except (subprocess.CalledProcessError, ValueError) as e:
#         print(f"Error getting duration for {segment_path}: {e}")
#         return 0

# def calculate_video_duration(video_id):
#     """Calculate the total duration of a video by summing its segment durations from S3."""
#     prefix = f"videos/{video_id}/"
#     temp_dir = tempfile.mkdtemp()
#     total_duration = 0.0

#     try:
#         # List all .ts segments in S3
#         response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
#         if 'Contents' not in response:
#             print(f"No segments found for {video_id} in S3!")
#             return 0

#         segments = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.ts')]
#         if not segments:
#             print(f"No .ts files found for {video_id} in S3!")
#             return 0

#         print(f"Calculating duration for {video_id} ({len(segments)} segments)...")
#         for segment_key in segments:
#             # Download the segment to a temporary file
#             segment_filename = os.path.basename(segment_key)
#             local_path = os.path.join(temp_dir, segment_filename)
#             s3_client.download_file(S3_BUCKET, segment_key, local_path)

#             # Get the segment duration
#             duration = get_segment_duration(local_path)
#             total_duration += duration
#             print(f"Segment {segment_filename}: {duration:.2f}s")

#             # Clean up the temporary file
#             os.remove(local_path)

#         total_duration = round(total_duration, 2)
#         print(f"Total duration for {video_id}: {total_duration}s")
#         return total_duration

#     except Exception as e:
#         print(f"Error calculating duration for {video_id}: {e}")
#         return 0
#     finally:
#         # Clean up the temporary directory
#         shutil.rmtree(temp_dir)

# def update_sequence_durations_and_start_times(user_id, video_durations):
#     """Update durations and recalculate start times for a user's sequence."""
#     try:
#         # Fetch the user's sequence
#         response = table.get_item(Key={'user_id': user_id})
#         if 'Item' not in response:
#             print(f"No sequence found for user {user_id}!")
#             return False
        
#         sequence = response['Item'].get('sequence', [])
#         if not sequence:
#             print(f"Sequence is empty for user {user_id}!")
#             return False
        
#         # Update durations and recalculate start times
#         current_start_time = 0.0
#         updated_sequence = []
#         for entry in sequence:
#             video_id = entry['video_id']
#             # Update duration to the calculated value
#             if video_id in video_durations:
#                 old_duration = float(entry['duration'])
#                 new_duration = video_durations[video_id]
#                 entry['duration'] = str(new_duration)
#                 print(f"Updated duration for {video_id} in user {user_id}'s sequence: {old_duration} -> {new_duration}")
#             else:
#                 print(f"Warning: No duration calculated for {video_id} in user {user_id}'s sequence. Keeping duration as {entry['duration']}")
#                 new_duration = float(entry['duration'])
            
#             # Update start_time
#             old_start_time = float(entry['start_time'])
#             entry['start_time'] = str(round(current_start_time, 2))
#             print(f"Updated start_time for {video_id} in user {user_id}'s sequence: {old_start_time} -> {current_start_time}")
            
#             # Add to updated sequence and increment start_time
#             updated_sequence.append(entry)
#             current_start_time += new_duration
        
#         # Update the sequence in DynamoDB
#         table.update_item(
#             Key={'user_id': user_id},
#             UpdateExpression="SET #seq = :seq",
#             ExpressionAttributeNames={"#seq": "sequence"},
#             ExpressionAttributeValues={":seq": updated_sequence}
#         )
#         print(f"Successfully updated sequence for user {user_id} in DynamoDB.")
#         return True
    
#     except Exception as e:
#         print(f"Error updating sequence for user {user_id}: {e}")
#         return False

# def scan_and_update_all_users(video_durations):
#     """Scan all users in the UserSequences table and update their sequences."""
#     try:
#         # Scan the table to get all users
#         response = table.scan()
#         users = response.get('Items', [])
        
#         # Process each user
#         for user in users:
#             user_id = user['user_id']
#             print(f"\nProcessing user {user_id}...")
#             update_sequence_durations_and_start_times(user_id, video_durations)
        
#         # Handle pagination if the table has more items
#         while 'LastEvaluatedKey' in response:
#             response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
#             users = response.get('Items', [])
#             for user in users:
#                 user_id = user['user_id']
#                 print(f"\nProcessing user {user_id}...")
#                 update_sequence_durations_and_start_times(user_id, video_durations)
    
#     except Exception as e:
#         print(f"Error scanning table: {e}")

# def main():
#     """Main function to calculate durations and update all users."""
#     # Step 1: Calculate durations for all videos
#     video_durations = {}
#     for video_id in VIDEO_IDS:
#         duration = calculate_video_duration(video_id)
#         if duration > 0:
#             video_durations[video_id] = duration
    
#     # Step 2: Update DynamoDB for all users
#     if video_durations:
#         print("\nUpdating DynamoDB with calculated durations...")
#         scan_and_update_all_users(video_durations)
#     else:
#         print("No durations calculated. Aborting update.")

# if __name__ == "__main__":
#     main()
