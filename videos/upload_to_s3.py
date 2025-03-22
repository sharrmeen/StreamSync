# import boto3
# import os

# # Configuration
# BUCKET_NAME = "streamsync-videos-<your-initials>"  # Replace <your-initials> with your unique identifier
# LOCAL_BASE_DIR = "."  # Current directory; change if folders are elsewhere
# VIDEO_FOLDERS = ["video1", "video2", "video3", "video4", "video5", "video6"]  # List of your 6 folders

# # Initialize S3 client
# s3_client = boto3.client("s3")

# def upload_folder_to_s3(local_folder, s3_prefix):
#     """
#     Uploads all files in a local folder to an S3 bucket recursively.
    
#     :param local_folder: Local folder path (e.g., 'video1')
#     :param s3_prefix: S3 destination prefix (e.g., 'videos/video1/')
#     """
#     print(f"Uploading {local_folder} to s3://{BUCKET_NAME}/{s3_prefix}")
    
#     # Walk through the local folder
#     for root, _, files in os.walk(local_folder):
#         for file in files:
#             # Full local path of the file
#             local_file_path = os.path.join(root, file)
            
#             # S3 key (path in the bucket), preserving folder structure
#             relative_path = os.path.relpath(local_file_path, local_folder)
#             s3_key = os.path.join(s3_prefix, relative_path).replace("\\", "/")  # Ensure forward slashes for S3
            
#             try:
#                 # Upload the file to S3
#                 s3_client.upload_file(local_file_path, BUCKET_NAME, s3_key)
#                 print(f"Uploaded {local_file_path} to s3://{BUCKET_NAME}/{s3_key}")
#             except Exception as e:
#                 print(f"Error uploading {local_file_path}: {e}")

# def main():
#     # Check if bucket exists (optional, for safety)
#     try:
#         s3_client.head_bucket(Bucket=BUCKET_NAME)
#         print(f"Bucket {BUCKET_NAME} exists and is accessible.")
#     except Exception as e:
#         print(f"Error: Bucket {BUCKET_NAME} may not exist or you lack access. {e}")
#         return

#     # Upload each video folder
#     for folder in VIDEO_FOLDERS:
#         if os.path.exists(folder) and os.path.isdir(folder):
#             s3_prefix = f"videos/{folder}/"  # Destination in S3 (e.g., 'videos/video1/')
#             upload_folder_to_s3(folder, s3_prefix)
#         else:
#             print(f"Warning: Local folder '{folder}' not found. Skipping.")

# if __name__ == "__main__":
#     main()``