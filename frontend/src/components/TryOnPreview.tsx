interface Props {
  status: string;
  resultUrl: string | null;
}

export default function TryOnPreview({ status, resultUrl }: Props) {
  if (status === 'completed' && resultUrl) {
    return (
      <div className="tryon-preview">
        <h3>Result</h3>
        <img src={resultUrl} alt="Try-on result" />
      </div>
    );
  }

  if (status === 'processing') {
    return (
      <div className="tryon-preview">
        <p>Generating try-on... This may take a moment.</p>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="tryon-preview">
        <p className="error-msg">Try-on generation failed. Please try again.</p>
      </div>
    );
  }

  return null;
}
