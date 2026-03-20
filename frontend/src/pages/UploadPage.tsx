import { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import { uploadFiles } from '../api/wardrobe';

export default function UploadPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState<Array<{ id: string; mainCategory: string; subCategory: string }>>([]);
  const [error, setError] = useState('');

  async function handleUpload(files: File[]) {
    setIsUploading(true);
    setError('');
    try {
      const data = await uploadFiles(files);
      setResults((prev) => [...prev, ...data.items]);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="page upload-page">
      <h1>Upload Clothing</h1>
      <ImageUploader onUpload={handleUpload} isUploading={isUploading} />

      {error && <div className="error-msg">{error}</div>}

      {results.length > 0 && (
        <div className="upload-results">
          <h3>Recently Uploaded</h3>
          {results.map((item, i) => (
            <div key={i} className="upload-result-item">
              Classified as <strong>{item.mainCategory}</strong> &rarr; {item.subCategory}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
