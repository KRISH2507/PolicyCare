import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import ChatPanel from '../components/ChatPanel';
import '../styles/chat.css';

/* ─────────────────────────────────────────────
   Small presentational sub-components
───────────────────────────────────────────── */

const SectionLabel = ({ children }) => (
  <p className="rec-section-label">{children}</p>
);

const BestFitCard = ({ bestFit }) => {
  if (!bestFit) return null;
  return (
    <div className="rec-best-fit-card">
      <h2 className="rec-policy-name">{bestFit.policy_name}</h2>
      <p className="rec-insurer">{bestFit.insurer}</p>
      <div className="rec-meta-row">
        <div className="rec-meta-item">
          <span className="rec-meta-label">Annual Premium</span>
          <span className="rec-meta-value">{bestFit.premium}</span>
        </div>
        <div className="rec-meta-item">
          <span className="rec-meta-label">Cover Amount</span>
          <span className="rec-meta-value">{bestFit.cover_amount}</span>
        </div>
      </div>
    </div>
  );
};

const WhyCard = ({ text }) => {
  if (!text) return null;
  return <div className="rec-why">{text}</div>;
};

const CoverageCard = ({ coverage }) => {
  if (!coverage) return null;
  return (
    <>
      <div className="rec-coverage-grid">
        {coverage.inclusions?.length > 0 && (
          <div className="rec-coverage-box">
            <h4>Covered</h4>
            <ul>
              {coverage.inclusions.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        {coverage.exclusions?.length > 0 && (
          <div className="rec-coverage-box">
            <h4>Not covered</h4>
            <ul>
              {coverage.exclusions.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="rec-coverage-inline" style={{ marginTop: '12px' }}>
        {coverage.co_pay && (
          <div className="rec-inline-item">
            <span className="rec-inline-label">Co-pay</span>
            <span className="rec-inline-value">{coverage.co_pay}</span>
          </div>
        )}
        {coverage.sub_limits && (
          <div className="rec-inline-item">
            <span className="rec-inline-label">Sub-limits</span>
            <span className="rec-inline-value">{coverage.sub_limits}</span>
          </div>
        )}
        {coverage.claim_type && (
          <div className="rec-inline-item">
            <span className="rec-inline-label">Claim type</span>
            <span className="rec-inline-value">{coverage.claim_type}</span>
          </div>
        )}
      </div>
    </>
  );
};

const PeerCard = ({ peer }) => (
  <div className="rec-peer-card">
    <div className="rec-peer-info">
      <h4>{peer.policy_name}</h4>
      <p>{peer.insurer}</p>
      <span>
        {peer.premium} · {peer.cover_amount} cover · {peer.waiting_period} waiting
        {peer.key_benefit ? ` · ${peer.key_benefit}` : ''}
      </span>
    </div>
    <div className="rec-peer-score" title="Suitability score">
      {peer.suitability_score}
    </div>
  </div>
);

/* ─────────────────────────────────────────────
   Main page
───────────────────────────────────────────── */

const ResultsPage = () => {
  const { recommendationResult, userProfile } = useContext(SessionContext);
  const navigate = useNavigate();

  /* Guard — should not happen due to ProtectedRoute, but just in case */
  if (!recommendationResult) {
    return (
      <div style={{ padding: '48px 24px', textAlign: 'center' }}>
        <p style={{ color: '#6B6B6B', marginBottom: '16px' }}>
          No recommendation found. Please fill in your profile first.
        </p>
        <button className="rec-back-btn" onClick={() => navigate('/profile')}>
          ← Back to profile
        </button>
      </div>
    );
  }

  const { best_fit, peer_comparison, coverage_detail, why_this_policy, citations } =
    recommendationResult;

  const hasResult = !!best_fit;

  return (
    <div className="results-layout">
      {/* ── Left: Recommendation content ── */}
      <main className="results-main">
        <button
          className="rec-back-btn"
          onClick={() => navigate('/profile')}
          aria-label="Back to profile"
        >
          ← Back
        </button>

        {!hasResult ? (
          /* Empty / fallback state */
          <div className="rec-empty">
            {why_this_policy?.toLowerCase().includes("unable to generate") ||
            why_this_policy?.toLowerCase().includes("please try again") ? (
              <>
                <p style={{ fontWeight: 600, marginBottom: '8px', color: '#1A1A1A' }}>
                  Recommendation temporarily unavailable
                </p>
                <p>
                  We couldn&apos;t generate a personalized recommendation right now, but your
                  profile has been saved. Please try again in a moment.
                </p>
                <button
                  className="rec-back-btn"
                  style={{ marginTop: '16px' }}
                  onClick={() => navigate('/profile')}
                >
                  ← Try again
                </button>
              </>
            ) : (
              <>
                <p style={{ fontWeight: 600, marginBottom: '8px', color: '#1A1A1A' }}>
                  No matching plans found
                </p>
                <p>{why_this_policy}</p>
              </>
            )}
          </div>
        ) : (
          <>
            {/* Best fit */}
            <div className="rec-section">
              <SectionLabel>Best match for you</SectionLabel>
              <BestFitCard bestFit={best_fit} />
            </div>

            {/* Why this policy */}
            {why_this_policy && (
              <div className="rec-section">
                <SectionLabel>Why we picked this</SectionLabel>
                <WhyCard text={why_this_policy} />
              </div>
            )}

            {/* Coverage detail */}
            {coverage_detail && (
              <div className="rec-section">
                <SectionLabel>Coverage breakdown</SectionLabel>
                <CoverageCard coverage={coverage_detail} />
              </div>
            )}

            {/* Peer comparison */}
            {peer_comparison?.length > 0 && (
              <div className="rec-section">
                <SectionLabel>Other plans to consider</SectionLabel>
                {peer_comparison.map((peer, i) => (
                  <PeerCard key={i} peer={peer} />
                ))}
              </div>
            )}

            {/* Citations */}
            {citations?.length > 0 && (
              <div className="rec-section">
                <p className="rec-citations">
                  <strong>Sources: </strong>
                  {citations.join(' · ')}
                </p>
              </div>
            )}
          </>
        )}
      </main>

      {/* ── Right: Chat panel ── */}
      <aside className="results-chat-col" aria-label="Chat with policy assistant">
        <ChatPanel />
      </aside>
    </div>
  );
};

export default ResultsPage;
