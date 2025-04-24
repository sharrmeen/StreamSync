// import React, { useState } from 'react';
// import axios from 'axios';

// const VideoUpload: React.FC = () => {
//   const [file, setFile] = useState<File | null>(null);
//   const [videoId, setVideoId] = useState<string>('');
//   const [status, setStatus] = useState<string>('');
//   const [error, setError] = useState<string>('');

//   const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
//     if (event.target.files && event.target.files[0]) {
//       setFile(event.target.files[0]);
//     }
//   };

//   const handleVideoIdChange = (event: React.ChangeEvent<HTMLInputElement>) => {
//     setVideoId(event.target.value);
//   };

//   const handleUpload = async () => {
//     if (!file || !videoId) {
//       setError('Please select a video file and provide a video ID.');
//       return;
//     }

//     setStatus('Uploading...');
//     setError('');

//     const formData = new FormData();
//     formData.append('video', file);
//     formData.append('video_id', videoId);

//     try {
//       const response = await axios.post('http://localhost:5001/upload', formData, {
//         headers: {
//           'Content-Type': 'multipart/form-data',
//         },
//       });
//       setStatus(`Upload successful: ${response.data.message}`);
//     } catch (err: any) {
//       setError(`Upload failed: ${err.response?.data?.error || err.message}`);
//       setStatus('');
//     }
//   };

//   return (
//     <div style={{ padding: '20px', maxWidth: '500px', margin: 'auto' }}>
//       <h2>Video Upload</h2>
//       <div>
//         <label>Video ID: </label>
//         <input
//           type="text"
//           value={videoId}
//           onChange={handleVideoIdChange}
//           placeholder="e.g., video8"
//           style={{ width: '100%', marginBottom: '10px' }}
//         />
//       </div>
//       <div>
//         <label>Video File: </label>
//         <input
//           type="file"
//           accept="video/mp4"
//           onChange={handleFileChange}
//           style={{ marginBottom: '10px' }}
//         />
//       </div>
//       <button onClick={handleUpload} disabled={!file || !videoId}>
//         Upload Video
//       </button>
//       {status && <p style={{ color: 'green' }}>{status}</p>}
//       {error && <p style={{ color: 'red' }}>{error}</p>}
//     </div>
//   );
// };

// export default VideoUpload;