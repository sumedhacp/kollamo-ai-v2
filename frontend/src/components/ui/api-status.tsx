import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { HealthStatus } from '@/types';
import { RefreshCw } from 'lucide-react';

export const ApiStatusIndicator: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isChecking, setIsChecking] = useState<boolean>(true);
  const [isError, setIsError] = useState<boolean>(false);

  const checkStatus = async () => {
    setIsChecking(true);
    try {
      const data = await api.checkHealth();
      setHealth(data);
      setIsError(false);
    } catch {
      setHealth(null);
      setIsError(true);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkStatus();
    // Periodically refresh health check every 45s
    const timer = setInterval(checkStatus, 45000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border font-medium transition-colors"
      data-testid="api-status-indicator"
      title={
        health
          ? `Backend API: ${health.status.toUpperCase()} | Model: ${health.ml_model} | DB: ${health.database} | Redis: ${health.redis}`
          : isChecking
          ? 'Checking backend connection...'
          : 'FastAPI Backend is currently unreachable'
      }
    >
      {isChecking ? (
        <>
          <RefreshCw className="w-3 h-3 text-amber-500 animate-spin" />
          <span className="text-amber-700 hidden sm:inline">Checking API</span>
        </>
      ) : isError || !health ? (
        <>
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
          </span>
          <span className="text-rose-700 font-medium">API Offline</span>
        </>
      ) : (
        <>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-emerald-700 hidden sm:inline">API Online</span>
        </>
      )}
    </div>
  );
};
