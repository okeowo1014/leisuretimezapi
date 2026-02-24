import { useState, useEffect } from 'react';
import { wallet } from '../../api/endpoints';
import { formatCurrency, formatDateTime } from '../../utils/helpers';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import toast from 'react-hot-toast';
import {
  FiCreditCard, FiPlus, FiMinus, FiSend, FiDollarSign,
  FiArrowDownCircle, FiArrowUpCircle, FiRepeat, FiX,
  FiClock, FiCheckCircle, FiAlertCircle, FiRefreshCw
} from 'react-icons/fi';
import './WalletPage.css';

export default function WalletPage() {
  const [walletData, setWalletData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [txLoading, setTxLoading] = useState(false);
  const [activeModal, setActiveModal] = useState(null); // 'deposit' | 'withdraw' | 'transfer'
  const [actionLoading, setActionLoading] = useState(false);

  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [transferAmount, setTransferAmount] = useState('');
  const [transferEmail, setTransferEmail] = useState('');

  useEffect(() => {
    fetchWallet();
    fetchTransactions();
  }, []);

  const fetchWallet = async () => {
    setLoading(true);
    try {
      const { data } = await wallet.list();
      const w = Array.isArray(data) ? data[0] : data.results?.[0] || data;
      setWalletData(w);
    } catch (err) {
      toast.error('Failed to load wallet');
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    setTxLoading(true);
    try {
      const { data } = await wallet.getTransactions();
      const list = Array.isArray(data) ? data : data.results || data.transactions || [];
      setTransactions(list);
    } catch (err) {
      // Silently handle - transactions may not exist yet
    } finally {
      setTxLoading(false);
    }
  };

  const openModal = (type) => {
    setActiveModal(type);
    setDepositAmount('');
    setWithdrawAmount('');
    setTransferAmount('');
    setTransferEmail('');
  };

  const closeModal = () => {
    setActiveModal(null);
  };

  const handleDeposit = async () => {
    const amount = parseFloat(depositAmount);
    if (!amount || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setActionLoading(true);
    try {
      const { data } = await wallet.deposit({ amount });
      if (data.checkout_url || data.url || data.stripe_url) {
        const url = data.checkout_url || data.url || data.stripe_url;
        window.open(url, '_blank');
        toast.success('Redirecting to payment...');
      } else {
        toast.success(data.message || 'Deposit initiated successfully');
      }
      closeModal();
      fetchWallet();
      fetchTransactions();
    } catch (err) {
      const msg = err.response?.data?.detail ||
        err.response?.data?.error || 'Deposit failed';
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount);
    if (!amount || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    if (walletData && amount > parseFloat(walletData.balance || 0)) {
      toast.error('Insufficient balance');
      return;
    }

    setActionLoading(true);
    try {
      await wallet.withdraw(walletData?.id, { amount });
      toast.success('Withdrawal request submitted');
      closeModal();
      fetchWallet();
      fetchTransactions();
    } catch (err) {
      const msg = err.response?.data?.detail ||
        err.response?.data?.error || 'Withdrawal failed';
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransfer = async () => {
    const amount = parseFloat(transferAmount);
    if (!transferEmail.trim()) {
      toast.error('Please enter recipient email');
      return;
    }
    if (!amount || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(transferEmail)) {
      toast.error('Please enter a valid email address');
      return;
    }
    if (walletData && amount > parseFloat(walletData.balance || 0)) {
      toast.error('Insufficient balance');
      return;
    }

    setActionLoading(true);
    try {
      await wallet.transfer(walletData?.id, {
        recipient_email: transferEmail.trim(),
        amount,
      });
      toast.success('Transfer completed successfully');
      closeModal();
      fetchWallet();
      fetchTransactions();
    } catch (err) {
      const msg = err.response?.data?.detail ||
        err.response?.data?.error || 'Transfer failed';
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const getTransactionIcon = (type) => {
    const t = type?.toLowerCase();
    if (t === 'deposit' || t === 'credit') return <FiArrowDownCircle className="tx-icon tx-icon-deposit" />;
    if (t === 'withdrawal' || t === 'debit') return <FiArrowUpCircle className="tx-icon tx-icon-withdraw" />;
    if (t === 'transfer') return <FiRepeat className="tx-icon tx-icon-transfer" />;
    return <FiDollarSign className="tx-icon tx-icon-default" />;
  };

  const getTransactionStatusIcon = (status) => {
    const s = status?.toLowerCase();
    if (s === 'completed' || s === 'success') return <FiCheckCircle className="tx-status-icon tx-status-success" />;
    if (s === 'pending') return <FiClock className="tx-status-icon tx-status-pending" />;
    if (s === 'failed') return <FiAlertCircle className="tx-status-icon tx-status-failed" />;
    return null;
  };

  const getAmountClass = (type) => {
    const t = type?.toLowerCase();
    if (t === 'deposit' || t === 'credit') return 'tx-amount-positive';
    if (t === 'withdrawal' || t === 'debit') return 'tx-amount-negative';
    return 'tx-amount-neutral';
  };

  if (loading) return <LoadingSpinner message="Loading wallet..." />;

  return (
    <div className="wallet-page">
      {/* Balance Card */}
      <div className="wallet-balance-card">
        <div className="wallet-balance-content">
          <span className="wallet-balance-label">Wallet Balance</span>
          <h1 className="wallet-balance-amount">
            {formatCurrency(walletData?.balance || 0)}
          </h1>
          {walletData?.currency && (
            <span className="wallet-balance-currency">{walletData.currency}</span>
          )}
        </div>

        <div className="wallet-action-buttons">
          <button className="wallet-action-btn wallet-action-deposit" onClick={() => openModal('deposit')}>
            <FiPlus /> Deposit
          </button>
          <button className="wallet-action-btn wallet-action-withdraw" onClick={() => openModal('withdraw')}>
            <FiMinus /> Withdraw
          </button>
          <button className="wallet-action-btn wallet-action-transfer" onClick={() => openModal('transfer')}>
            <FiSend /> Transfer
          </button>
        </div>
      </div>

      {/* Transactions */}
      <div className="wallet-transactions-card">
        <div className="wallet-transactions-header">
          <h2 className="wallet-transactions-title">Transaction History</h2>
          <button
            className="wallet-refresh-btn"
            onClick={() => { fetchWallet(); fetchTransactions(); }}
            title="Refresh"
          >
            <FiRefreshCw />
          </button>
        </div>

        {txLoading ? (
          <LoadingSpinner size="small" message="Loading transactions..." />
        ) : !transactions.length ? (
          <EmptyState
            icon={FiCreditCard}
            title="No transactions yet"
            description="Your wallet transaction history will appear here."
          />
        ) : (
          <div className="wallet-transactions-list">
            <div className="wallet-tx-table-header">
              <span className="wallet-tx-col-type">Type</span>
              <span className="wallet-tx-col-desc">Description</span>
              <span className="wallet-tx-col-date">Date</span>
              <span className="wallet-tx-col-status">Status</span>
              <span className="wallet-tx-col-amount">Amount</span>
            </div>

            {transactions.map((tx) => (
              <div key={tx.id} className="wallet-tx-row">
                <div className="wallet-tx-col-type">
                  {getTransactionIcon(tx.transaction_type || tx.type)}
                  <span className="wallet-tx-type-label">
                    {tx.transaction_type || tx.type || 'Transaction'}
                  </span>
                </div>
                <div className="wallet-tx-col-desc">
                  <span className="wallet-tx-description">
                    {tx.description || tx.narration || tx.reference || '--'}
                  </span>
                </div>
                <div className="wallet-tx-col-date">
                  <span className="wallet-tx-date">
                    {formatDateTime(tx.created_at || tx.date || tx.timestamp)}
                  </span>
                </div>
                <div className="wallet-tx-col-status">
                  {getTransactionStatusIcon(tx.status)}
                  <span className="wallet-tx-status-label">
                    {tx.status || '--'}
                  </span>
                </div>
                <div className="wallet-tx-col-amount">
                  <span className={`wallet-tx-amount ${getAmountClass(tx.transaction_type || tx.type)}`}>
                    {(tx.transaction_type || tx.type)?.toLowerCase() === 'deposit' ||
                     (tx.transaction_type || tx.type)?.toLowerCase() === 'credit'
                      ? '+' : '-'}
                    {formatCurrency(tx.amount)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Modals */}
      {activeModal && (
        <div className="wallet-modal-overlay" onClick={closeModal}>
          <div className="wallet-modal" onClick={(e) => e.stopPropagation()}>
            <button className="wallet-modal-close" onClick={closeModal}>
              <FiX />
            </button>

            {activeModal === 'deposit' && (
              <>
                <div className="wallet-modal-icon wallet-modal-icon-deposit">
                  <FiPlus />
                </div>
                <h3 className="wallet-modal-title">Deposit Funds</h3>
                <p className="wallet-modal-text">
                  Add money to your wallet. You will be redirected to a secure payment page.
                </p>
                <div className="wallet-modal-field">
                  <label className="wallet-modal-label">Amount</label>
                  <div className="wallet-modal-input-wrapper">
                    <FiDollarSign className="wallet-modal-input-icon" />
                    <input
                      type="number"
                      className="wallet-modal-input"
                      placeholder="0.00"
                      value={depositAmount}
                      onChange={(e) => setDepositAmount(e.target.value)}
                      min="0"
                      step="0.01"
                      autoFocus
                    />
                  </div>
                </div>
                <button
                  className="wallet-modal-submit wallet-modal-submit-deposit"
                  onClick={handleDeposit}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Processing...' : 'Deposit'}
                </button>
              </>
            )}

            {activeModal === 'withdraw' && (
              <>
                <div className="wallet-modal-icon wallet-modal-icon-withdraw">
                  <FiMinus />
                </div>
                <h3 className="wallet-modal-title">Withdraw Funds</h3>
                <p className="wallet-modal-text">
                  Withdraw money from your wallet. Current balance: {formatCurrency(walletData?.balance || 0)}
                </p>
                <div className="wallet-modal-field">
                  <label className="wallet-modal-label">Amount</label>
                  <div className="wallet-modal-input-wrapper">
                    <FiDollarSign className="wallet-modal-input-icon" />
                    <input
                      type="number"
                      className="wallet-modal-input"
                      placeholder="0.00"
                      value={withdrawAmount}
                      onChange={(e) => setWithdrawAmount(e.target.value)}
                      min="0"
                      step="0.01"
                      autoFocus
                    />
                  </div>
                </div>
                <button
                  className="wallet-modal-submit wallet-modal-submit-withdraw"
                  onClick={handleWithdraw}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Processing...' : 'Withdraw'}
                </button>
              </>
            )}

            {activeModal === 'transfer' && (
              <>
                <div className="wallet-modal-icon wallet-modal-icon-transfer">
                  <FiSend />
                </div>
                <h3 className="wallet-modal-title">Transfer Funds</h3>
                <p className="wallet-modal-text">
                  Send money to another user. Current balance: {formatCurrency(walletData?.balance || 0)}
                </p>
                <div className="wallet-modal-field">
                  <label className="wallet-modal-label">Recipient Email</label>
                  <div className="wallet-modal-input-wrapper">
                    <FiSend className="wallet-modal-input-icon" />
                    <input
                      type="email"
                      className="wallet-modal-input"
                      placeholder="recipient@email.com"
                      value={transferEmail}
                      onChange={(e) => setTransferEmail(e.target.value)}
                      autoFocus
                    />
                  </div>
                </div>
                <div className="wallet-modal-field">
                  <label className="wallet-modal-label">Amount</label>
                  <div className="wallet-modal-input-wrapper">
                    <FiDollarSign className="wallet-modal-input-icon" />
                    <input
                      type="number"
                      className="wallet-modal-input"
                      placeholder="0.00"
                      value={transferAmount}
                      onChange={(e) => setTransferAmount(e.target.value)}
                      min="0"
                      step="0.01"
                    />
                  </div>
                </div>
                <button
                  className="wallet-modal-submit wallet-modal-submit-transfer"
                  onClick={handleTransfer}
                  disabled={actionLoading}
                >
                  {actionLoading ? 'Processing...' : 'Transfer'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
