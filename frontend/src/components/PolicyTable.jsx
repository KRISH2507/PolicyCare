import React, { useState, useEffect, useCallback } from 'react';
import { apiGet, apiPatch, apiDelete } from '../api/client';
import '../styles/admin.css';

/* ─────────────────────────────────────────────
   Helpers
───────────────────────────────────────────── */

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
};

const FileTypeBadge = ({ type }) => {
  const t = (type || '').toLowerCase().replace('.', '');
  const cls =
    t === 'pdf'  ? 'badge badge--pdf'  :
    t === 'json' ? 'badge badge--json' :
                   'badge badge--txt';
  return <span className={cls}>{t || '—'}</span>;
};

/* ─────────────────────────────────────────────
   Row sub-components
───────────────────────────────────────────── */

/** Normal (read) row */
const PolicyRow = ({ policy, onEdit, onDeleteRequest }) => (
  <tr>
    <td className="td-policy-name">{policy.name}</td>
    <td className="td-insurer">{policy.insurer}</td>
    <td><FileTypeBadge type={policy.file_type} /></td>
    <td className="td-date">{formatDate(policy.uploaded_at)}</td>
    <td>
      <span className="badge badge--active">Active</span>
    </td>
    <td className="td-actions">
      <button
        className="action-btn action-btn--edit"
        onClick={() => onEdit(policy)}
        aria-label={`Edit policy ${policy.name}`}
      >
        Edit
      </button>
      <button
        className="action-btn action-btn--delete"
        onClick={() => onDeleteRequest(policy.id)}
        aria-label={`Delete policy ${policy.name}`}
      >
        Delete
      </button>
    </td>
  </tr>
);

/** Inline-edit row */
const EditRow = ({ policy, onSave, onCancel }) => {
  const [name, setName]       = useState(policy.name);
  const [insurer, setInsurer] = useState(policy.insurer);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState(null);

  const handleSave = async () => {
    if (!name.trim() || !insurer.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await apiPatch(`/api/admin/policies/${policy.id}`, {
        name: name.trim(),
        insurer: insurer.trim(),
      });
      onSave(updated);
    } catch (err) {
      setError(err.message || 'Save failed.');
      setSaving(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSave();
    if (e.key === 'Escape') onCancel();
  };

  return (
    <>
      <tr style={{ background: '#FAFBFF' }}>
        <td>
          <input
            className="table-edit-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={saving}
            aria-label="Edit policy name"
            autoFocus
          />
        </td>
        <td>
          <input
            className="table-edit-input"
            value={insurer}
            onChange={(e) => setInsurer(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={saving}
            aria-label="Edit insurer name"
          />
        </td>
        <td><FileTypeBadge type={policy.file_type} /></td>
        <td className="td-date">{formatDate(policy.uploaded_at)}</td>
        <td><span className="badge badge--active">Active</span></td>
        <td className="td-actions">
          <button
            className="action-btn action-btn--save"
            onClick={handleSave}
            disabled={saving || !name.trim() || !insurer.trim()}
            aria-label="Save changes"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button
            className="action-btn action-btn--cancel"
            onClick={onCancel}
            disabled={saving}
            aria-label="Cancel edit"
          >
            Cancel
          </button>
        </td>
      </tr>
      {error && (
        <tr>
          <td colSpan={6} style={{ padding: '0 16px 10px' }}>
            <div className="table-error-bar" role="alert">{error}</div>
          </td>
        </tr>
      )}
    </>
  );
};

/** Inline delete-confirm row — rendered immediately below the target row */
const DeleteConfirmRow = ({ policy, onConfirm, onCancel, deleting }) => (
  <tr className="delete-confirm-row">
    <td colSpan={6}>
      <div className="delete-confirm-inner">
        <p className="delete-confirm-text">
          Delete <span>"{policy.name}"</span>? This removes it from recommendations.
        </p>
        <button
          className="action-btn action-btn--confirm-delete"
          onClick={onConfirm}
          disabled={deleting}
          aria-label={`Confirm delete ${policy.name}`}
        >
          {deleting ? 'Deleting…' : 'Confirm Delete'}
        </button>
        <button
          className="action-btn action-btn--cancel"
          onClick={onCancel}
          disabled={deleting}
          aria-label="Cancel delete"
        >
          Cancel
        </button>
      </div>
    </td>
  </tr>
);

/* ─────────────────────────────────────────────
   Main component
───────────────────────────────────────────── */

const PolicyTable = ({ refreshTrigger }) => {
  const [policies, setPolicies]     = useState([]);
  const [loading, setLoading]       = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [editingId, setEditingId]   = useState(null);   // policy id being edited
  const [deleteId, setDeleteId]     = useState(null);   // policy id pending delete confirm
  const [deleting, setDeleting]     = useState(false);

  /* ── Fetch policies ── */
  const fetchPolicies = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const data = await apiGet('/api/admin/policies');
      setPolicies(data);
    } catch (err) {
      setFetchError(err.message || 'Failed to load policies.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies, refreshTrigger]);

  /* ── Edit handlers ── */
  const handleEdit = (policy) => {
    setDeleteId(null);
    setEditingId(policy.id);
  };

  const handleSave = (updated) => {
    setPolicies((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p))
    );
    setEditingId(null);
  };

  const handleCancelEdit = () => setEditingId(null);

  /* ── Delete handlers ── */
  const handleDeleteRequest = (id) => {
    setEditingId(null);
    setDeleteId(id);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      await apiDelete(`/api/admin/policies/${deleteId}`);
      setPolicies((prev) => prev.filter((p) => p.id !== deleteId));
      setDeleteId(null);
    } catch (err) {
      // Show error inline — keep confirm row open
      setFetchError(err.message || 'Delete failed. Please try again.');
      setDeleteId(null);
    } finally {
      setDeleting(false);
    }
  };

  const handleCancelDelete = () => setDeleteId(null);

  /* ── Render ── */
  return (
    <div className="admin-card table-card">
      {/* Card header */}
      <div className="table-card-header">
        <h2 className="table-card-title">Policy Documents</h2>
        {!loading && (
          <span className="table-card-count">
            {policies.length} {policies.length === 1 ? 'policy' : 'policies'}
          </span>
        )}
      </div>

      {/* Fetch error banner */}
      {fetchError && (
        <div className="table-error-bar" role="alert">
          {fetchError}
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <table className="policy-table">
          <tbody>
            <tr className="table-loading-row">
              <td colSpan={6}>Loading policies…</td>
            </tr>
          </tbody>
        </table>
      ) : policies.length === 0 ? (
        /* Empty state */
        <div className="table-empty" role="status">
          <span className="table-empty-icon" aria-hidden="true">📂</span>
          <p className="table-empty-title">No policy documents uploaded yet.</p>
          <p className="table-empty-sub">
            Upload your first policy to power AI recommendations.
          </p>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="policy-table" aria-label="Uploaded policy documents">
            <thead>
              <tr>
                <th scope="col">Policy Name</th>
                <th scope="col">Insurer</th>
                <th scope="col">Type</th>
                <th scope="col">Uploaded</th>
                <th scope="col">Status</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {policies.map((policy) => {
                const isEditing  = editingId === policy.id;
                const isDeleting = deleteId  === policy.id;

                return (
                  <React.Fragment key={policy.id}>
                    {isEditing ? (
                      <EditRow
                        policy={policy}
                        onSave={handleSave}
                        onCancel={handleCancelEdit}
                      />
                    ) : (
                      <PolicyRow
                        policy={policy}
                        onEdit={handleEdit}
                        onDeleteRequest={handleDeleteRequest}
                      />
                    )}

                    {isDeleting && (
                      <DeleteConfirmRow
                        policy={policy}
                        onConfirm={handleConfirmDelete}
                        onCancel={handleCancelDelete}
                        deleting={deleting}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PolicyTable;
