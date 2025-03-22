import boto3
import random
import ffmpeg
import os

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')  # Your region
table = dynamodb.Table('UserSequences')

# Directory where original .mp4 files are stored
video_folder = "./videos"  # Adjust if needed (e.g., "/Users/sharmeenkhan/StreamSync/videos")

# Automatically generate the videos list with durations in seconds
def get_video_data():
    videos = []
    if not os.path.exists(video_folder):
        print(f"Error: Directory '{video_folder}' does not exist!")
        return videos
    
    for filename in os.listdir(video_folder):
        if filename.endswith(".mp4"):
            video_id = filename.replace(".mp4", "")  # e.g., "video1.mp4" -> "video1"
            file_path = os.path.join(video_folder, filename)
            try:
                probe = ffmpeg.probe(file_path)
                duration_seconds = float(probe['format']['duration'])  # Duration in seconds
                # Round to nearest second, ensure at least 1 second
                duration = max(1, int(round(duration_seconds)))
                videos.append({"video_id": video_id, "duration": duration})
                print(f"Processed {filename}: {duration} seconds")
            except ffmpeg.Error as e:
                print(f"Error processing {filename}: {e}")
            except KeyError as e:
                print(f"Error: Could not find duration in {filename} metadata: {e}")
    return videos

# Function to generate a random sequence for a user
def generate_sequence(videos, num_videos):
    sequence = []
    current_start_time = 0
    selected_videos = random.sample(videos, min(num_videos, len(videos)))  # Avoid sampling more than available
    for video in selected_videos:
        sequence.append({
            "video_id": video["video_id"],
            "start_time": current_start_time,
            "duration": video["duration"]
        })
        current_start_time += video["duration"]
    return sequence

# Delete existing users to start fresh
for i in range(1, 11):  # user1 to user10
    user_id = f"user{i}"
    try:
        table.delete_item(Key={"user_id": user_id})
        print(f"Deleted {user_id} from DynamoDB")
    except Exception as e:
        print(f"Error deleting {user_id}: {e}")

# Main execution
videos = get_video_data()  # Get the video data automatically
if not videos:
    print("No videos found! Check your video_folder path or ensure .mp4 files exist.")
    exit()

num_users = 10
for i in range(1, num_users + 1):
    user_id = f"user{i}"
    sequence = generate_sequence(videos, random.randint(3, 5))  # 3-5 videos per user
    item = {
        "user_id": user_id,
        "sequence": sequence
    }
    try:
        table.put_item(Item=item)
        print(f"Added {user_id} to DynamoDB with sequence: {sequence}")
    except Exception as e:
        print(f"Error adding {user_id}: {e}")

# Verify one item
response = table.get_item(Key={"user_id": "user1"})
print("Sample item for user1:", response.get("Item"))

print("Done!")