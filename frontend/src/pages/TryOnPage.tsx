import { useState, useRef, useEffect, useCallback } from 'react';
import { getItems, WardrobeItem } from '../api/wardrobe';
import { generateTryOn, getTryOnResult } from '../api/tryon';
import TryOnPreview from '../components/TryOnPreview';

export default function TryOnPage() {
  const [selfieB64, setSelfieB64] = useState('');
  const [clothingItems, setClothingItems] = useState<WardrobeItem[]>([]);
  const [selectedClothing, setSelectedClothing] = useState<string>('');
  const [jobId, setJobId] = useState('');
  const [status, setStatus] = useState('');
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load clothing items for selection
  useEffect(() => {
    async function load() {
      const tops = await getItems('top', 0, 50);
      const bottoms = await getItems('bottomwear', 0, 50);
      const outerwear = await getItems('outerwear', 0, 50);
      setClothingItems([...tops.items, ...bottoms.items, ...outerwear.items]);
    }
    load();
  }, []);

  // Poll for result
  useEffect(() => {
    if (!jobId || status !== 'processing') return;
    const interval = setInterval(async () => {
      try {
        const result = await getTryOnResult(jobId);
        setStatus(result.status);
        if (result.status === 'completed') {
          setResultUrl(result.result_image_url);
          clearInterval(interval);
        } else if (result.status === 'failed') {
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
        setStatus('failed');
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [jobId, status]);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
      setCameraStream(stream);
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch {
      alert('Could not access camera');
    }
  }

  function stopCamera() {
    cameraStream?.getTracks().forEach((t) => t.stop());
    setCameraStream(null);
  }

  function captureSelfie() {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')!.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    setSelfieB64(dataUrl.split(',')[1]);
    stopCamera();
  }

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      setSelfieB64(result.split(',')[1]);
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  }, []);

  async function handleGenerate() {
    if (!selfieB64 || !selectedClothing) {
      setError('Please provide a selfie and select a clothing item');
      return;
    }
    setError('');
    setStatus('processing');
    setResultUrl(null);

    try {
      const data = await generateTryOn(selfieB64, selectedClothing);
      setJobId(data.job_id);
      setStatus(data.status);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to start try-on');
      setStatus('failed');
    }
  }

  return (
    <div className="page tryon-page">
      <h1>Virtual Try-On</h1>

      <div className="tryon-layout">
        <div className="tryon-selfie-section">
          <h3>Your Photo</h3>
          {!selfieB64 && !cameraStream && (
            <div className="selfie-options">
              <button className="btn" onClick={startCamera}>
                Take Selfie
              </button>
              <button className="btn btn-secondary" onClick={() => fileInputRef.current?.click()}>
                Upload Photo
              </button>
              <input ref={fileInputRef} type="file" accept="image/*" hidden onChange={handleFileSelect} />
            </div>
          )}

          {cameraStream && (
            <div className="camera-view">
              <video ref={videoRef} autoPlay playsInline />
              <canvas ref={canvasRef} hidden />
              <div className="camera-controls">
                <button className="btn" onClick={captureSelfie}>Capture</button>
                <button className="btn btn-secondary" onClick={stopCamera}>Cancel</button>
              </div>
            </div>
          )}

          {selfieB64 && (
            <div className="selfie-preview">
              <img src={`data:image/jpeg;base64,${selfieB64}`} alt="Selfie" />
              <button className="btn btn-sm" onClick={() => setSelfieB64('')}>Retake</button>
            </div>
          )}
        </div>

        <div className="tryon-clothing-section">
          <h3>Select Garment</h3>
          <div className="clothing-picker">
            {clothingItems.map((item) => (
              <div
                key={item.id}
                className={`picker-item ${selectedClothing === item.id ? 'selected' : ''}`}
                onClick={() => setSelectedClothing(item.id)}
              >
                <img src={item.url} alt={item.subCategory || 'clothing'} loading="lazy" />
              </div>
            ))}
            {clothingItems.length === 0 && <p>No clothing items found. Upload some first!</p>}
          </div>
        </div>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <button
        className="btn btn-primary generate-btn"
        onClick={handleGenerate}
        disabled={!selfieB64 || !selectedClothing || status === 'processing'}
      >
        {status === 'processing' ? 'Generating...' : 'Generate Try-On'}
      </button>

      <TryOnPreview status={status} resultUrl={resultUrl} />
    </div>
  );
}
