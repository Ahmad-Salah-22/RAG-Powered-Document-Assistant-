import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ChatStudio from './components/ChatStudio';
import DocumentLibrary from './components/DocumentLibrary';
import VisualPdfViewer from './components/VisualPdfViewer';
import ComparisonMatrix from './components/ComparisonMatrix';
import AnalyticsView from './components/AnalyticsView';
import { fetchHealth, fetchDocuments } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [health, setHealth] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedPdfView, setSelectedPdfView] = useState({ doc: '', page: 1 });

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [healthData, docsData] = await Promise.all([
        fetchHealth(),
        fetchDocuments().catch(() => ({ documents: [] }))
      ]);
      setHealth(healthData);
      setDocuments(docsData.documents || []);

      if (docsData.documents?.length && !selectedPdfView.doc) {
        setSelectedPdfView({ doc: docsData.documents[0].document_name, page: 1 });
      }
    } catch (err) {
      console.warn('Backend load error:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleViewDocument = (docName, pageNum = 1) => {
    setSelectedPdfView({ doc: docName, page: pageNum });
    setActiveTab('viewer');
  };

  return (
    <div className="app-container">
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        health={health} 
        onRefreshHealth={loadData}
        isRefreshing={isRefreshing}
      />

      <div className="main-content">
        {activeTab === 'chat' && (
          <ChatStudio 
            documents={documents} 
            onViewDocument={handleViewDocument}
            onNavigateToLibrary={() => setActiveTab('library')}
          />
        )}

        {activeTab === 'library' && (
          <DocumentLibrary 
            documents={documents} 
            onRefresh={loadData} 
            onViewDocument={handleViewDocument} 
          />
        )}

        {activeTab === 'viewer' && (
          <VisualPdfViewer 
            documents={documents} 
            initialDoc={selectedPdfView.doc} 
            initialPage={selectedPdfView.page} 
          />
        )}

        {activeTab === 'compare' && (
          <ComparisonMatrix 
            documents={documents} 
            onViewDocument={handleViewDocument} 
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsView />
        )}
      </div>
    </div>
  );
}
