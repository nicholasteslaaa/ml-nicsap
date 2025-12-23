import { useState, useRef, useEffect } from "react";
import CanvasMaskExport from "./drawingCanvas";
import type { CanvasMaskRef } from "./drawingCanvas";
import "./App.css";
import axios from "axios";

function App() {
  const canvasRef = useRef<CanvasMaskRef>(null);

  const [emoticon, setEmoticon] = useState("...");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);

  const [videoProgress, setVideoProgress] = useState(-1);
  const [outputPath, setOutputPath] = useState([]);
  // ⭐ NEW: brightness slider state
  const [brightness, setBrightness] = useState(100);
  // const [contrast, setContrast] = useState(100);
  

  // ⭐ draw the first frame with current brightness filter
  const drawFirstFrame = (video: HTMLVideoElement) => {
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // ⭐ Apply brightness controlled by slider
    ctx.filter = `brightness(${brightness}%)`;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) return;

      const imgURL = URL.createObjectURL(blob);

      if (canvasRef.current?.loadImage) {
        canvasRef.current.loadImage(imgURL);
      }
    }, "image/png");
  };

  // ⭐ redraw frame every time slider changes
  useEffect(() => {
    if (!videoFile) return;

    const video = document.createElement("video");
    video.src = URL.createObjectURL(videoFile);
    video.preload = "metadata";
    video.muted = true;

    video.onloadeddata = () => {
      video.currentTime = 0;
    };

    video.onseeked = () => drawFirstFrame(video);
  }, [brightness]);

  const fetchEmoticon = async () => {
    try {
      const res = await fetch("https://api.rosblok.shop/getRandomEmoticon");
      const data = await res.json();
      setEmoticon(data.emoticon);
    } catch (error) {
      console.error("Error fetching emoticon:", error);
    }
  };

  const fetchOutputPath = async () => {
    try {
      const res = await fetch("https://api.rosblok.shop/getOutputPath");
      const data = await res.json();
      setOutputPath(data.paths);
    } catch (error) {
      console.error("Error fetching output path:", error);
    }
  };

  const fetchVideoProgress = async () => {
    try {
      const res = await fetch("https://api.rosblok.shop/getVideoProgress");
      const data = await res.json();
      setVideoProgress(data.progress);
    } catch (error) {
      console.error("Error fetching video progress:", error);
    }
  };

  const uploadVideo = async () => {
    if (!videoFile) {
      alert("Select a video first");
      return;
    }

    console.log("UPLOAD STARTED ✅");
    setStatus("Uploading...");
    setProgress(0);

    const CHUNK_SIZE = 2 * 1024 * 1024; // 2MB
    const totalChunks = Math.ceil(videoFile.size / CHUNK_SIZE);

    try {
      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE;
        const end = Math.min(videoFile.size, start + CHUNK_SIZE);
        const chunk = videoFile.slice(start, end);

        const formData = new FormData();
        formData.append("file", chunk);
        formData.append("chunk_index", String(i));
        formData.append("total_chunks", String(totalChunks));
        formData.append("filename", videoFile.name);
        formData.append("overlay_mask", canvasRef.current?.getYoloText() || "");

        await axios.post("https://api.rosblok.shop/upload_chunk/", formData, {
          timeout: 0,
        });

        setProgress(Math.round(((i + 1) / totalChunks) * 100));
      }

      setStatus("✅ Upload complete & processing started");
    } catch (err) {
      console.error(err);
      setStatus("❌ Upload failed");
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setVideoFile(file);

    const video = document.createElement("video");
    video.preload = "metadata";
    video.src = URL.createObjectURL(file);
    video.muted = true;

    video.onloadeddata = () => {
      video.currentTime = 0;
    };

    video.onseeked = () => drawFirstFrame(video);
  };

  const getYoloCoor = () => {
    if (canvasRef.current) {
      return canvasRef.current.getYoloText();
    }
  };

  useEffect(() => {
    fetchEmoticon();
    fetchVideoProgress();
    fetchOutputPath();

    const interval = setInterval(() => {
      fetchEmoticon();
      fetchVideoProgress();
      fetchOutputPath();
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <h1>Radial Arm Analysis {emoticon}</h1>

      {/* ⭐ brightness slider */}
      <div style={{ margin: "20px 0" }}>
          <label>Brightness: {brightness}</label>
          <input
            type="range"
            min="0"
            max="10000"
            value={brightness}
            onInput={(e) => setBrightness(Number((e.target as HTMLInputElement).value))}
          />
      </div>

      <input type="file" accept="video/*" onChange={handleFileChange} />

      <center>
        <CanvasMaskExport ref={canvasRef} />
      </center>
      <p>{getYoloCoor()}</p>
      <button onClick={uploadVideo}>Upload Video</button>

      {progress > 0 && videoProgress < 0 && <p>Uploading: {progress}%</p>}
      <p>{status}</p>

      {videoProgress > -1 && <p>Progress: {videoProgress}%</p>}

      <div>
        {outputPath.map((path, index) => (
          <video key={index} controls width="400" style={{ margin: "10px" }}>
            <source src={path} type="video/mp4" />
          </video>
        ))}
      </div>
    </>
  );
}

export default App;
