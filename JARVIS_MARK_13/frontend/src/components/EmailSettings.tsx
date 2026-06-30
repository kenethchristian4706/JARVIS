import React, { useState, useEffect } from 'react';
import { Mail, Lock, RefreshCw, AlertCircle, CheckCircle2, Power, Key } from 'lucide-react';

interface EmailStatus {
  connected: boolean;
  email?: string;
}

interface EmailSettingsProps {
  onConnectSuccess?: () => void;
}

export const EmailSettings: React.FC<EmailSettingsProps> = ({ onConnectSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<EmailStatus>({ connected: false });
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const API_BASE = 'http://127.0.0.1:8000/api/email';

  // Fetch status on component mount
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch email connection status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleTestConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    const targetEmail = status.connected ? (status.email || '') : email;
    const targetPassword = password;

    if (!status.connected && (!targetEmail || !targetPassword)) {
      setMessage({ type: 'error', text: 'Please fill in both email and app password to test.' });
      return;
    }

    setTestLoading(true);
    setMessage(null);

    try {
      let res;
      if (status.connected) {
        // If already connected, test using connection endpoint validate_only or status check.
        // But since we want to verify SMTP/IMAP credentials, we require password for test.
        if (!password) {
          setMessage({ type: 'error', text: 'Enter app password to re-test connection.' });
          setTestLoading(false);
          return;
        }
        res = await fetch(`${API_BASE}/test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: targetEmail, password: targetPassword }),
        });
      } else {
        res = await fetch(`${API_BASE}/test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: targetEmail, password: targetPassword }),
        });
      }

      const data = await res.json();
      if (res.ok && data.success) {
        setMessage({ type: 'success', text: 'Connection validation successful! SMTP and IMAP servers are reachable.' });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Connection test failed. Please verify credentials.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to communicate with the backend server.' });
    } finally {
      setTestLoading(false);
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setMessage({ type: 'error', text: 'Please enter both your email address and app password.' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch(`${API_BASE}/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setMessage({ type: 'success', text: 'Successfully connected and saved credentials!' });
        setPassword('');
        fetchStatus();
        if (onConnectSuccess) {
          onConnectSuccess();
        }
      } else {
        setMessage({ type: 'error', text: data.detail || 'Connection failed. Please check credentials.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to communicate with the backend server.' });
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your email account and remove saved credentials?')) {
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch(`${API_BASE}/disconnect`, {
        method: 'POST',
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setMessage({ type: 'success', text: 'Email account successfully disconnected.' });
        setEmail('');
        setPassword('');
        setStatus({ connected: false });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Disconnection failed.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to communicate with the backend server.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-black/5 rounded-xl p-6 shadow-sm flex flex-col gap-6 max-w-2xl w-full">
      <div className="flex items-center justify-between border-b border-black/5 pb-4">
        <div className="flex flex-col gap-0.5 text-left">
          <h3 className="custom-font-heading text-lg font-bold text-[#141d26] flex items-center gap-2">
            <Mail className="w-5 h-5 text-[#141d26]/70" />
            Email Connection Configuration
          </h3>
          <p className="text-xs text-[#141d26]/50">
            Link your personal email account to enable AI mailing capabilities.
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold select-none">
          {status.connected ? (
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200/50 flex items-center gap-1.5 px-2.5 py-0.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              🟢 Connected
            </span>
          ) : (
            <span className="bg-red-50 text-red-700 border border-red-200/50 flex items-center gap-1.5 px-2.5 py-0.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-red-400"></span>
              🔴 Not Connected
            </span>
          )}
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-start gap-3 text-xs leading-relaxed text-left border ${
          message.type === 'success' 
            ? 'bg-emerald-50 border-emerald-200/60 text-emerald-800' 
            : 'bg-red-50 border-red-200/60 text-red-800'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {status.connected ? (
        /* Connected State */
        <div className="flex flex-col gap-5 text-left">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#f6f4ed] border border-black/5 rounded-xl p-4 flex flex-col gap-1.5">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#141d26]/40">Connected Account</span>
              <span className="text-sm font-semibold text-[#141d26] break-all">{status.email}</span>
            </div>
            <div className="bg-[#f6f4ed] border border-black/5 rounded-xl p-4 flex flex-col gap-1.5">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#141d26]/40">Connection Protocol</span>
              <span className="text-sm font-semibold text-[#141d26]">SMTP + IMAP (Auto-configured)</span>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200/50 rounded-xl p-4 flex items-start gap-3">
            <Key className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 leading-relaxed">
              <span className="font-semibold block mb-0.5">Secure Keyring Protected</span>
              Your connection credentials are encrypted and stored inside your system's hardware-backed keychain locker. They will be loaded automatically on application startup.
            </div>
          </div>

          <div className="flex flex-col gap-4 pt-2 border-t border-black/5">
            <h4 className="text-xs font-semibold text-[#141d26]/60">Re-test Connection Verification</h4>
            <form onSubmit={handleTestConnection} className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Lock className="absolute left-3 top-3 w-4 h-4 text-[#141d26]/40" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Verify App Password"
                  className="w-full pl-9 pr-4 py-2 border border-black/10 rounded-lg text-sm bg-white focus:outline-none focus:border-[#ecc870] font-mono"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={testLoading}
                className="px-4 py-2 bg-[#16202a] text-white hover:bg-[#232d38] disabled:bg-[#16202a]/60 text-xs font-bold rounded-lg transition-colors cursor-pointer flex items-center justify-center gap-1.5 shrink-0"
              >
                {testLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                Test Connection
              </button>
            </form>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-black/5">
            <button
              onClick={handleDisconnect}
              disabled={loading}
              className="px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white disabled:bg-red-400 text-xs font-bold rounded-lg transition-colors cursor-pointer flex items-center gap-1.5"
            >
              <Power className="w-4 h-4" />
              Disconnect Email
            </button>
          </div>
        </div>
      ) : (
        /* Disconnected State Form */
        <form onSubmit={handleConnect} className="flex flex-col gap-5 text-left">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-[#141d26]/70">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-4 h-4 text-[#141d26]/40" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@gmail.com"
                  className="w-full pl-9 pr-4 py-2.5 border border-black/10 rounded-lg text-sm bg-white focus:outline-none focus:border-[#ecc870]"
                  required
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-[#141d26]/70">App Password</label>
                <a 
                  href="https://support.google.com/accounts/answer/185833" 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-[10px] text-[#ecc870] font-semibold hover:underline"
                >
                  What is an App Password?
                </a>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-3 w-4 h-4 text-[#141d26]/40" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="•••• •••• •••• ••••"
                  className="w-full pl-9 pr-4 py-2.5 border border-black/10 rounded-lg text-sm bg-white focus:outline-none focus:border-[#ecc870] font-mono"
                  required
                />
              </div>
              <span className="text-[10px] text-[#141d26]/40 leading-relaxed mt-0.5">
                Note: Do not enter your primary account password. Use an application-specific app password generated from your mail provider settings.
              </span>
            </div>
          </div>

          <div className="flex justify-between items-center pt-4 border-t border-black/5">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testLoading || !email || !password}
              className="px-4 py-2.5 border border-[#232d38]/20 text-[#16202a] hover:bg-black/5 disabled:opacity-50 text-xs font-bold rounded-lg transition-colors cursor-pointer flex items-center gap-1.5"
            >
              {testLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              Test Connection
            </button>
            <button
              type="submit"
              disabled={loading || !email || !password}
              className="px-6 py-2.5 bg-[#ecc870] text-[#141d26] hover:bg-[#ecc870]/90 disabled:bg-[#ecc870]/50 text-xs font-extrabold rounded-lg shadow-sm transition-colors cursor-pointer flex items-center gap-1.5"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              Connect Account
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
