import React, { useState, useRef } from 'react';
import { apiUpload } from '../api/client';
import '../styles/admin.css';

const ALLOWED_TYPES = ['.pdf', '.json', '.txt'];
const ALLOWED_MIME  = ['application/pdf', 'application/json', 'text/plain', 'text/json'];

/** Returns true if the file extension / mime is acceptable. */
const isAllowed = (file) => {
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  return ALLOWED_TYPES.includes(ext) || ALLOWED_MIME.includes(file.type);
};

const UploadCard = ({ onUploadSuccess }) => {
  const [file, setFile]         = useState(null);
  const [policyName, setPolicyName] = useState('');
  const [insurer, setInsurer]   = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading]   = useState(false);
  const [feedback, setFeedback]     = useState(null); // { type: 'success'|'error', message }

  const inputRef = useRef(null);

  /* ── File selection ── */
  const selectFile = (f) => {
    if (!f) return;
    if (!isAllowed(f)) {
      setFeedback({ type: 'error', message: 'Only PDF, JSON, and TXT files are allowed.' });
      return;
    }
    setFile(f);
    setFeedback(null);
  };

  const handleInputChange = (e) => selectFile(e.target.files[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    selectFile(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = ()  => setIsDragOver(false);

  const removeFile = () => {
    setFile(null);
    setFeedback(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  /* ── Submit ── */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !policyName.trim() || !insurer.trim()) return;

    setUploading(true);
    setFeedback(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', policyName.trim());
    formData.append('insurer', insurer.trim());

    try {
      await apiUpload('/api/admin/upload', formData);
      setFeedback({ type: 'success', message: 'Policy uploaded successfully.' });
      // Reset form
      setFile(null);
      setPolicyName('');
      setInsurer('');
      if (inputRef.current) inputRef.current.value = '';
      // Notify parent to refresh table
      onUploadSuccess?.();
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err.message?.includes('process document')
          ? 'Upload failed: could not vectorize document. Check the file format.'
          : 'Upload failed. Please try again.',
      });
    } finally {
      setUploading(false);
    }
  };

  const canSubmit = file && policyName.trim() && insurer.trim() && !uploading;

  return (
    <div className="admin-card upload-card">
      <p className="upload-card-title">Upload Policy</p>
      <p className="upload-card-sub">
        Add a new policy document for AI recommendations.
      </p>

      <form onSubmit={handleSubmit} noValidate>
        {/* Dropzone — only shown when no file selected */}
        {!file ? (
          <div
            className={`upload-dropzone${isDragOver ? ' upload-dropzone--active' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            role="button"
            tabIndex={0}
            aria-label="Upload file drop zone. Click or drag a file here."
            onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.json,.txt"
              onChange={handleInputChange}
              aria-label="Choose policy file"
              tabIndex={-1}
            />
            <span className="upload-dropzone-icon" aria-hidden="true">📄</span>
            <p className="upload-dropzone-text">
              Drag &amp; drop or{' '}
              <strong>click to browse</strong>
            </p>
            <p className="upload-dropzone-hint">PDF · JSON · TXT</p>
          </div>
        ) : (
          /* Selected file pill */
          <div className="upload-file-selected">
            <span className="upload-file-name" title={file.name}>
              📎 {file.name}
            </span>
            <button
              type="button"
              className="upload-file-remove"
              onClick={removeFile}
              aria-label={`Remove file ${file.name}`}
            >
              ✕
            </button>
          </div>
        )}

        {/* Policy name */}
        <div className="upload-field">
          <label htmlFor="upload-policy-name">Policy name</label>
          <input
            id="upload-policy-name"
            type="text"
            placeholder="e.g. Star Health Comprehensive"
            value={policyName}
            onChange={(e) => setPolicyName(e.target.value)}
            disabled={uploading}
            required
            autoComplete="off"
          />
        </div>

        {/* Insurer */}
        <div className="upload-field">
          <label htmlFor="upload-insurer">Insurer</label>
          <input
            id="upload-insurer"
            type="text"
            placeholder="e.g. Star Health Insurance"
            value={insurer}
            onChange={(e) => setInsurer(e.target.value)}
            disabled={uploading}
            required
            autoComplete="off"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          className="upload-submit-btn"
          disabled={!canSubmit}
          aria-busy={uploading}
        >
          {uploading ? 'Uploading…' : 'Upload Policy'}
        </button>

        {/* Feedback */}
        {feedback && (
          <div
            className={`upload-feedback upload-feedback--${feedback.type}`}
            role={feedback.type === 'error' ? 'alert' : 'status'}
          >
            {feedback.message}
          </div>
        )}
      </form>
    </div>
  );
};

export default UploadCard;
