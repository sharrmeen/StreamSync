import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Navbar from "@/components/Navbar";
import VideoPlayer from "@/components/VideoPlayer";
import { getLiveStream } from "@/services/videoService";
import { Loader2 } from "lucide-react";
import { toast } from "@/components/ui/use-toast";
// import VideoUpload from './VideoUpload';

const Dashboard: React.FC = () => {
  // <VideoUpload />

  const { userId } = useParams<{ userId: string }>(); // Extract userId from the route
  const navigate = useNavigate();
  const [currentStream, setCurrentStream] = useState<{ id: string; url: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Redirect to login if userId is not provided
    if (!userId) {
      toast({
        title: "User ID Required",
        description: "Please enter a valid User ID to access the stream.",
        variant: "destructive",
      });
      navigate("/login");
      return;
    }

    const initializeLiveStream = async () => {
      try {
        // Fetch the live stream URL with just userId (server handles time sync)
        const liveStream = await getLiveStream(userId);
        setCurrentStream(liveStream);
        toast({
          title: "Live Stream Ready",
          description: "The live stream is now available. Click to watch in fullscreen.",
        });
      } catch (error) {
        console.error("Error loading live stream:", error);
        toast({
          title: "Stream Error",
          description: "Unable to load the live stream. Please try again later.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    initializeLiveStream();
  }, [userId, navigate]); // Dependencies: userId and navigate

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto pt-32 pb-16 px-4 flex flex-col items-center justify-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="mt-4 text-muted-foreground">Connecting to the live stream...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background page-transition">
      <Navbar />
      <main className="container mx-auto pt-24 pb-16 px-4">
        <div className="max-w-screen-xl mx-auto">
          <header className="mb-8">
            <h1 className="text-3xl font-bold">Live Stream</h1>
            <p className="text-muted-foreground mt-2">
              Welcome, {userId}. Watch your personalized stream now.
            </p>
          </header>
          
          {/* Main video player */}
          <section className="mb-12">
            {currentStream ? (
              <VideoPlayer
                videoUrl={currentStream.url}
                videoId={currentStream.id}
                isLive={true}
                autoPlay={true}
              />
            ) : (
              <div className="video-container flex items-center justify-center bg-card border border-border">
                <p className="text-muted-foreground">No live stream available</p>
              </div>
            )}

            <div className="mt-4">
              <h2 className="text-2xl font-semibold">Live Now</h2>
              <p className="text-muted-foreground mt-1">
                Click the stream to view in fullscreen mode. Live streams cannot be paused or rewound.
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;