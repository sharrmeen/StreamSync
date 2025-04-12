
// // This is a mock implementation. In a real app, you would integrate with AWS MediaConvert, S3, CloudFront and AWS MediaLive.

// export interface Video {
//   id: string;
//   title: string;
//   description: string;
//   thumbnailUrl: string;
//   videoUrl: string;
//   duration: number; // in seconds
//   createdAt: string;
// }

// // Mock video data
// const MOCK_VIDEOS: Video[] = [
//   {
//     id: "1",
//     title: "Cinematic Nature Documentary",
//     description: "Explore the beauty of nature in this stunning documentary.",
//     thumbnailUrl: "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=800&q=60",
//     videoUrl: "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
//     duration: 60,
//     createdAt: "2023-01-15T12:00:00Z",
//   },
//   {
//     id: "2",
//     title: "Urban Architecture",
//     description: "A visual journey through modern architectural marvels.",
//     thumbnailUrl: "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=800&q=60",
//     videoUrl: "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
//     duration: 45,
//     createdAt: "2023-02-20T15:30:00Z",
//   },
//   {
//     id: "3",
//     title: "Ocean Mysteries",
//     description: "Dive deep into the mysteries of the ocean.",
//     thumbnailUrl: "https://images.unsplash.com/photo-1518398046578-8cca57782e17?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=800&q=60",
//     videoUrl: "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
//     duration: 75,
//     createdAt: "2023-03-10T09:15:00Z",
//   },
// ];

// // Mock live stream URL - in a real app, this would be an HLS stream from AWS MediaLive
// const MOCK_LIVE_STREAM = {
//   id: "live-1",
//   url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" // Example HLS test stream
// };

// // Simulate network delay
// const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// // Get all videos (for VOD)
// export const getVideos = async (): Promise<Video[]> => {
//   await delay(800);
//   return MOCK_VIDEOS;
// };

// // Get a specific video by ID (for VOD)
// export const getVideoById = async (videoId: string): Promise<Video> => {
//   await delay(500);
//   const video = MOCK_VIDEOS.find((v) => v.id === videoId);
  
//   if (!video) {
//     throw new Error("Video not found");
//   }
  
//   return video;
// };

// // Get current live stream
// export const getLiveStream = async (): Promise<{ id: string; url: string }> => {
//   await delay(1200); // Simulate longer loading time for live stream initialization
//   return MOCK_LIVE_STREAM;
// };

// // Get video for current timeline (in a real app, this would be based on user preferences and history)
// export const getRecommendedVideo = async (): Promise<Video> => {
//   await delay(600);
//   // Just return the first video for now
//   return MOCK_VIDEOS[0];
// };

// // Track video progress (for VOD)
// export const trackVideoProgress = async (videoId: string, progressSeconds: number): Promise<void> => {
//   await delay(300);
//   console.log(`Progress tracked for video ${videoId}: ${progressSeconds} seconds`);
//   // In a real app, this would save to a database
// };


// @/services/videoService.ts
export const getLiveStream = async (userId: string): Promise<{ id: string; url: string }> => {
  try {
    const encodedUserId = encodeURIComponent(userId); // Ensure special characters are handled
    const playlistUrl = `http://localhost:5001/playlist?user_id=${encodedUserId}`;
    const response = await fetch(playlistUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/vnd.apple.mpegurl', // Match Flask’s mimetype
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch playlist: ${response.status} - ${response.statusText}`);
    }

    // Since Flask returns a raw .m3u8 playlist, we return the URL for the player to fetch
    return {
      id: `${userId}-stream`, // Consistent unique ID
      url: playlistUrl, // HLS player will fetch this URL directly
    };
  } catch (error) {
    console.error("Error fetching live stream:", error);
    throw error; // Re-throw to let Dashboard handle it
  }
};

