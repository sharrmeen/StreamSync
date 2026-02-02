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

