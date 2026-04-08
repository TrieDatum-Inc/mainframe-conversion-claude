/**
 * Application route constants.
 * Maps BMS screens to Next.js routes.
 *
 * BMS Screen -> Next.js Route mapping:
 *   COSGN00 (login)           -> /login
 *   COMEN01 (main menu)       -> /dashboard
 *   COACTVW (account view)    -> /accounts/[id]
 *   COACTUP (account update)  -> /accounts/[id]/edit
 *   COBIL00 (bill payment)    -> /accounts/[id]/payment
 *   COCRDLI (card list)       -> /cards
 *   COCRDSL (card select)     -> /cards/[cardNum]
 *   COCRDUP (card update)     -> /cards/[cardNum]/edit
 *   COTRN00 (txn list)        -> /transactions
 *   COTRN01 (txn view)        -> /transactions/[id]
 *   COTRN02 (txn add)         -> /transactions/new
 *   COADM01 (admin menu)      -> /admin
 *   COUSR00 (user list)       -> /admin/users
 *   COUSR01 (user add)        -> /admin/users/new
 *   COUSR02 (user update)     -> /admin/users/[id]/edit
 *   COUSR03 (user delete)     -> /admin/users/[id]/delete
 *   CORPT00 (reports)         -> /admin/reports
 *   COTRTLI (txn type list)   -> /admin/transaction-types
 *   COTRTU  (txn type update) -> /admin/transaction-types/[code]
 *   Authorization screens     -> /authorizations
 */

export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',

  // Accounts
  ACCOUNTS: '/accounts',
  ACCOUNT_VIEW: (id: number) => `/accounts/${id}`,
  ACCOUNT_EDIT: (id: number) => `/accounts/${id}/edit`,
  ACCOUNT_PAYMENT: (id: number) => `/accounts/${id}/payment`,
  BILL_PAYMENT: '/bill-payment',

  // Cards
  CARDS: '/cards',
  CARD_VIEW: (cardNum: string) => `/cards/${cardNum}`,
  CARD_EDIT: (cardNum: string) => `/cards/${cardNum}/edit`,

  // Transactions
  TRANSACTIONS: '/transactions',
  TRANSACTION_VIEW: (id: string) => `/transactions/${id}`,
  TRANSACTION_NEW: '/transactions/new',

  // Authorizations
  AUTHORIZATIONS: '/authorizations',
  AUTHORIZATION_DETAIL: (id: number) => `/authorizations/${id}`,
  AUTHORIZATION_BY_ACCOUNT: (acctId: number) => `/authorizations/accounts/${acctId}`,

  // Admin
  ADMIN: '/admin',
  ADMIN_USERS: '/admin/users',
  ADMIN_USER_NEW: '/admin/users/new',
  ADMIN_USER_EDIT: (id: string) => `/admin/users/${id}/edit`,
  ADMIN_REPORTS: '/admin/reports',
  ADMIN_TRANSACTION_TYPES: '/admin/transaction-types',
  ADMIN_TRANSACTION_TYPE_EDIT: (code: string) => `/admin/transaction-types/${code}`,
} as const;
