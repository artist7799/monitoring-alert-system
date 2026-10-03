import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import Toast from './Toast';

export const Layout = ({ title, sseStatus, toasts = [], removeToast, children }) => {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-wrapper">
        <Header title={title} sseStatus={sseStatus} />
        <main className="page-container">
          {children}
        </main>
      </div>

      {toasts.length > 0 && (
        <div className="toast-container">
          {toasts.map((toast) => (
            <Toast key={toast.id} toast={toast} onClose={removeToast} />
          ))}
        </div>
      )}
    </div>
  );
};

export default Layout;
