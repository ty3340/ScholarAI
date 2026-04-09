import React, { useState } from 'react';
import './App.css';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [collection, setCollection] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('search'); // search, summarize, review
  const [summaryResult, setSummaryResult] = useState('');
  const [reviewResult, setReviewResult] = useState('');
  const [citationResult, setCitationResult] = useState('');
  const [citationStyle, setCitationStyle] = useState('apa');
  const [saveResult, setSaveResult] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const API_BASE = 'http://localhost:8000';

  const clearMessages = () => {
    setErrorMessage('');
  };

  const isInCollection = (paperId) => collection.some((paper) => paper.arxiv_id === paperId);

  const addPaperToCollection = (paper) => {
    if (!isInCollection(paper.arxiv_id)) {
      setCollection((prev) => [...prev, paper]);
    }
  };

  const removePaperFromCollection = (paperId) => {
    setCollection((prev) => prev.filter((paper) => paper.arxiv_id !== paperId));
  };

  const clearReviewState = () => {
    setSummaryResult('');
    setReviewResult('');
    setCitationResult('');
    setSaveResult('');
  };

  const handleClearCollection = async () => {
    setLoading(true);
    clearMessages();
    try {
      const response = await fetch(`${API_BASE}/collection/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection: [],
          container_name: 'scholarai',
          blob_name: 'collection.json',
        }),
      });
      const data = await response.json();
      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || data.message || 'Clear collection failed.');
      }

      setCollection([]);
      clearReviewState();
      setSaveResult('Collection cleared locally and in storage.');
    } catch (error) {
      setErrorMessage(error.message || 'Error clearing collection.');
    }
    setLoading(false);
  };

  const renderTextBlocks = (text) => {
    if (!text) return null;
    return text.split('\n\n').map((block, index) => (
      <p key={index} className="text-block">
        {block.trim()}
      </p>
    ));
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    clearMessages();
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Search failed.');
      }
      setResults(Array.isArray(data.results) ? data.results : []);
      clearReviewState();
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
      setErrorMessage(error.message || 'Search failed. Make sure the backend is running.');
    }
    setLoading(false);
  };

  const handleSummarize = async (paper) => {
    setLoading(true);
    clearMessages();
    try {
      const response = await fetch(`${API_BASE}/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper_id: paper.arxiv_id, abstract: paper.summary || '' }),
      });
      const data = await response.json();
      const summaryText =
        data.summary?.summary || data.summary || 'No summary available';
      const sourceLabel = data.agent ? `Source: ${data.agent}` : 'Source: local summary';
      const messageLabel = data.message ? `\n\n${data.message}` : '';
      setSummaryResult(`${paper.title}\n\n${summaryText}\n\n${sourceLabel}${messageLabel}`);
      setActiveTab('summarize');
    } catch (error) {
      console.error('Summarize error:', error);
      setErrorMessage('Error generating summary.');
    }
    setLoading(false);
  };

  const handleReview = async () => {
    setLoading(true);
    clearMessages();
    try {
      const payload = {
        query: searchQuery,
        papers: collection.length ? collection : results,
      };
      const response = await fetch(`${API_BASE}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      setReviewResult(data.review || 'No review available');
      setCitationResult('');
      setActiveTab('review');
    } catch (error) {
      console.error('Review error:', error);
      setErrorMessage('Error generating review.');
    }
    setLoading(false);
  };

  const handleCitations = async () => {
    const sourcePapers = collection.length ? collection : results;
    if (sourcePapers.length === 0) {
      setErrorMessage('Run a search or load a collection before generating citations.');
      return;
    }

    setLoading(true);
    clearMessages();
    try {
      const response = await fetch(`${API_BASE}/citations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ papers: sourcePapers, style: citationStyle }),
      });
      const data = await response.json();
      const label = data.style ? `Style: ${data.style.toUpperCase()}\n\n` : '';
      const citationText = Array.isArray(data.citations)
        ? data.citations.map((citation, index) => `${index + 1}. ${citation}`).join('\n\n')
        : (data.formatted || 'No citations available.');
      setCitationResult(label + citationText);
      setActiveTab('review');
    } catch (error) {
      console.error('Citation error:', error);
      setErrorMessage('Error generating citations.');
    }
    setLoading(false);
  };

  const handleSaveCollection = async () => {
    if (collection.length === 0) {
      setErrorMessage('Add papers to the collection before saving.');
      return;
    }

    setLoading(true);
    clearMessages();
    try {
      const response = await fetch(`${API_BASE}/collection/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collection,
          container_name: 'scholarai',
          blob_name: 'collection.json',
        }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setSaveResult(data.message || 'Collection saved successfully.');
      } else {
        setSaveResult('');
        setErrorMessage(data.message || 'Save collection failed.');
      }
    } catch (error) {
      console.error('Save collection error:', error);
      setErrorMessage('Error saving collection.');
    }
    setLoading(false);
  };

  const handleLoadCollection = async () => {
    setLoading(true);
    clearMessages();
    try {
      const response = await fetch(`${API_BASE}/collection/load`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          container_name: 'scholarai',
          blob_name: 'collection.json',
        }),
      });
      const data = await response.json();
      if (data.status === 'success' && Array.isArray(data.data?.collection || data.data)) {
        const loaded = Array.isArray(data.data.collection) ? data.data.collection : data.data;
        setCollection(loaded);
        setSaveResult(`Loaded ${loaded.length} papers from persistent collection.`);
      } else {
        setSaveResult('');
        setErrorMessage(data.message || 'Load collection failed.');
      }
    } catch (error) {
      console.error('Load collection error:', error);
      setErrorMessage('Error loading collection.');
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <header className="header">
        <h1>ScholarAI</h1>
        <p>AI-Powered Research Paper Assistant</p>
      </header>

      <div className="container">
        {/* Tabs */}
        <div className="tabs">
          <button
            className={activeTab === 'search' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('search')}
          >
            Search
          </button>
          <button
            className={activeTab === 'summarize' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('summarize')}
          >
            Summarize
          </button>
          <button
            className={activeTab === 'review' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('review')}
          >
            Review & Cite
          </button>
        </div>

        {errorMessage && <div className="message error-message">{errorMessage}</div>}
        {saveResult && <div className="message success-message">{saveResult}</div>}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="tab-content">
            <form onSubmit={handleSearch}>
              <input
                type="text"
                placeholder="Search for research papers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <button type="submit" disabled={loading} className="btn">
                {loading ? 'Searching...' : 'Search'}
              </button>
            </form>

            <div className="results">
              {results.length > 0 ? (
                results.map((paper, index) => (
                  <div key={index} className="paper-card">
                    <div className="paper-info">
                      <h3>{paper.title}</h3>
                      <p className="authors">{paper.authors?.join(', ')}</p>
                      <p className="abstract">{paper.summary}</p>
                      <small>{paper.published}</small>
                      <div className="paper-actions">
                        <button
                          onClick={() => handleSummarize(paper)}
                          className="btn-small"
                        >
                          Summarize
                        </button>
                        {isInCollection(paper.arxiv_id) ? (
                          <button
                            onClick={() => removePaperFromCollection(paper.arxiv_id)}
                            className="btn-small secondary"
                          >
                            Remove from collection
                          </button>
                        ) : (
                          <button
                            onClick={() => addPaperToCollection(paper)}
                            className="btn-small secondary"
                          >
                            Add to collection
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p>No results yet. Search for papers to get started.</p>
              )}
            </div>

            {results.length > 0 && (
              <div className="actions-row">
                <div className="control-group">
                  <label htmlFor="citation-style-search" className="control-label">Citation style</label>
                  <select
                    id="citation-style-search"
                    value={citationStyle}
                    onChange={(e) => setCitationStyle(e.target.value)}
                    className="select-input"
                  >
                    <option value="apa">APA</option>
                    <option value="mla">MLA</option>
                  </select>
                </div>
                <button
                  onClick={handleReview}
                  disabled={!searchQuery || loading}
                  className="btn"
                >
                  {loading ? 'Working...' : 'Generate Review'}
                </button>
                <button
                  onClick={handleCitations}
                  disabled={results.length === 0 || loading}
                  className="btn"
                >
                  {loading ? 'Working...' : 'Generate Citations'}
                </button>
                <button
                  onClick={handleSaveCollection}
                  disabled={loading || collection.length === 0}
                  className="btn"
                >
                  {loading ? 'Working...' : 'Save Collection'}
                </button>
                <button
                  onClick={handleLoadCollection}
                  disabled={loading}
                  className="btn"
                >
                  {loading ? 'Working...' : 'Load Collection'}
                </button>
              </div>
            )}

            {collection.length > 0 && (
              <div className="output-panel collection-panel">
                <h2>Paper Collection</h2>
                <p>{collection.length} papers saved for review.</p>
                <ul className="collection-list">
                  {collection.map((paper) => (
                    <li key={paper.arxiv_id}>
                      <strong>{paper.title}</strong> ({paper.published?.slice(0, 4)})
                      <button
                        onClick={() => removePaperFromCollection(paper.arxiv_id)}
                        className="btn-small secondary"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={handleClearCollection}
                  className="btn"
                >
                  Clear collection
                </button>
              </div>
            )}
          </div>
        )}

        {/* Summarize Tab */}
        {activeTab === 'summarize' && (
          <div className="tab-content">
            <h2>Paper Summary</h2>
            <div className="output-panel">
              {summaryResult ? (
                <div className="text-output">{renderTextBlocks(summaryResult)}</div>
              ) : (
                <p>Select a paper and click Summarize.</p>
              )}
            </div>
          </div>
        )}

        {/* Review Tab */}
        {activeTab === 'review' && (
          <div className="tab-content">
            <p>Generate a literature review draft based on your search results, then create citations.</p>
            <div className="output-panel">
              {reviewResult ? (
                <div className="text-output">{renderTextBlocks(reviewResult)}</div>
              ) : (
                <p>Run a search, then generate a review.</p>
              )}
            </div>
            <div className="actions-row">
              <div className="control-group">
                <label htmlFor="citation-style-review" className="control-label">Citation style</label>
                <select
                  id="citation-style-review"
                  value={citationStyle}
                  onChange={(e) => setCitationStyle(e.target.value)}
                  className="select-input"
                >
                  <option value="apa">APA</option>
                  <option value="mla">MLA</option>
                </select>
              </div>
              <button
                onClick={handleReview}
                disabled={!searchQuery || loading}
                className="btn"
              >
                {loading ? 'Working...' : 'Generate Review'}
              </button>
              <button
                onClick={handleCitations}
                disabled={results.length === 0 || loading}
                className="btn"
              >
                {loading ? 'Working...' : 'Generate Citations'}
              </button>
            </div>
            <div className="output-panel">
              <h2>Citations</h2>
              {citationResult ? (
                <div className="text-output">{renderTextBlocks(citationResult)}</div>
              ) : (
                <p>Generate citations after your review draft.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
