import React from 'react';
import { Link } from 'react-router-dom';
import { HelpCircle, ArrowLeft } from 'lucide-react';
import Layout from '../components/Layout';

export const NotFound = () => {
  return (
    <Layout title="404 Page Not Found">
      <div className="empty-state" style={{ padding: '4rem 1rem' }}>
        <HelpCircle size={64} color="var(--text-dim)" style={{ marginBottom: '1rem' }} />
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Page Not Found</h2>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          The requested route does not exist or has been moved.
        </p>
        <Link to="/dashboard" className="btn btn-primary">
          <ArrowLeft size={16} /> Return to Dashboard
        </Link>
      </div>
    </Layout>
  );
};

export default NotFound;
