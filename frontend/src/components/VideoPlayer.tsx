import React, { useState, useRef, useEffect } from "react";
import { Maximize, Volume2, VolumeX, Sun, Moon } from "lucide-react";
import Hls from "hls.js";
import { Slider } from "@/components/ui/slider";
import { trackVideoProgress } from "@/services/videoService";

interface VideoPlayerProps {
  videoUrl: string;
  videoId: string;
  isLive?: boolean;
  autoPlay?: boolean;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoUrl,
  videoId,
  isLive = false,
  autoPlay = true,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [brightness, setBrightness] = useState(100); // 100% brightness by default
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isControlsVisible, setIsControlsVisible] = useState(true);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (videoUrl.includes('.m3u8') && Hls.isSupported()) {
      const hls = new Hls({
        startLevel: 2,
        autoStartLoad: true,
      });

      hls.loadSource(videoUrl);
      hls.attachMedia(video);
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        if (autoPlay) {
          video.play().catch(error => {
            console.error("Autoplay prevented:", error);
          });
        }
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error("HLS error:", data);
        if (data.fatal) {
          switch(data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.log("Network error, trying to recover...");
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log("Media error, trying to recover...");
              hls.recoverMediaError();
              break;
            default:
              console.error("Fatal error, cannot recover");
              hls.destroy();
              break;
          }
        }
      });

      return () => {
        hls.destroy();
      };
    } else {
      if (autoPlay) {
        video.play().catch(error => {
          console.error("Autoplay prevented:", error);
        });
      }
    }
  }, [videoUrl, autoPlay]);

  useEffect(() => {
    const handleActivity = () => {
      setIsControlsVisible(true);
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = window.setTimeout(() => {
        if (isPlaying) {
          setIsControlsVisible(false);
        }
      }, 3000);
    };
    
    const container = containerRef.current;
    if (container) {
      container.addEventListener("mousemove", handleActivity);
      container.addEventListener("click", handleActivity);
    }
    
    return () => {
      if (container) {
        container.removeEventListener("mousemove", handleActivity);
        container.removeEventListener("click", handleActivity);
      }
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isPlaying]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  useEffect(() => {
    if (!isLive) {
      const interval = setInterval(() => {
        if (isPlaying && videoRef.current?.currentTime > 0) {
          trackVideoProgress(videoId, Math.floor(videoRef.current.currentTime));
        }
      }, 10000);

      return () => clearInterval(interval);
    }
  }, [videoId, isPlaying, isLive]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        if (!isLive) {
          videoRef.current.pause();
          setIsPlaying(false);
        }
      } else {
        videoRef.current.play().catch((error) => {
          console.error("Play failed:", error);
        });
        setIsPlaying(true);
        
        if (isLive && !isFullscreen) {
          enterFullscreen();
        }
      }
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleVolumeChange = (value: number[]) => {
    const newVolume = value[0];
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setVolume(newVolume);
      setIsMuted(newVolume === 0);
    }
  };

  const handleBrightnessChange = (value: number[]) => {
    setBrightness(value[0]);
  };

  const enterFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen().catch((err) => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    }
  };

  const exitFullscreen = () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  };

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      enterFullscreen();
    } else {
      exitFullscreen();
    }
  };

  return (
    <div 
      ref={containerRef} 
      className={`relative video-container bg-black group ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}
      onDoubleClick={toggleFullscreen}
    >
      <video
        ref={videoRef}
        src={!videoUrl.includes('.m3u8') ? videoUrl : undefined}
        className="w-full h-full"
        onClick={togglePlay}
        playsInline
        style={{
          filter: `brightness(${brightness}%)`,
          objectFit: "contain"
        }}
      />
      
      {!isLive && !isPlaying && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/30 animate-fade-in">
          <button 
            onClick={togglePlay}
            className="p-4 rounded-full bg-white/20 backdrop-blur-md hover:bg-white/30 transition-all duration-300"
          >
            <div className="h-12 w-12 text-white flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </button>
        </div>
      )}
      
      {isLive && (
        <div className="absolute top-4 left-4 bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
          LIVE
        </div>
      )}

      <div 
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-4 py-6 transition-opacity duration-300 ${
          isControlsVisible || !isPlaying ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <button onClick={toggleMute} className="text-white hover:text-white/80 transition-colors">
                {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
              </button>
              <div className="w-24">
                <Slider
                  value={[isMuted ? 0 : volume]}
                  min={0}
                  max={1}
                  step={0.01}
                  onValueChange={handleVolumeChange}
                  className="w-full"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button className="text-white hover:text-white/80 transition-colors">
                {brightness < 50 ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </button>
              <div className="w-24">
                <Slider
                  value={[brightness]}
                  min={10}
                  max={200}
                  step={1}
                  onValueChange={handleBrightnessChange}
                  className="w-full"
                />
              </div>
            </div>
          </div>
          
          <button 
            onClick={toggleFullscreen}
            className="text-white hover:text-white/80 transition-colors"
          >
            <Maximize className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
