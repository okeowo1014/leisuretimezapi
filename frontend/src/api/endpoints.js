import client from './client';

// Auth
export const auth = {
  register: (data) => client.post('/auth/register/', data),
  login: (data) => client.post('/auth/login/', data),
  logout: () => client.post('/auth/logout/'),
  changePassword: (data) => client.post('/change-password/', data),
  resetPassword: (data) => client.post('/reset-password/', data),
  resetPasswordConfirm: (utoken, token, data) =>
    client.post(`/reset-password-confirm/${utoken}/${token}/`, data),
  resendActivation: (data) => client.post('/resend-activation-email/', data),
  deleteAccount: (data) => client.delete('/delete-account/', { data }),
};

// Profile
export const profile = {
  get: () => client.get('/profile/'),
  update: (data) => client.post('/profile/', data),
  updatePartial: (data) => client.patch('/profile/', data),
  uploadImage: (formData) =>
    client.post('/profile/image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  updateDisplayPicture: (formData) =>
    client.post('/update_display_picture/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getCustomerProfile: () => client.get('/personal-booking/'),
  getAccountSettings: () => client.get('/account-settings/'),
  getBookingHistory: () => client.get('/booking-history/'),
};

// Packages
export const packages = {
  getIndex: () => client.get('/index/'),
  list: (params) => client.get('/packages/', { params }),
  get: (id) => client.get(`/packages/${id}/`),
  save: (id) => client.post(`/packages/${id}/save/`),
  unsave: (id) => client.post(`/packages/${id}/unsave/`),
  getSaved: () => client.get('/saved-packages/'),
  checkOffer: (id, params) => client.get(`/check-offer/${id}/`, { params }),
};

// Bookings
export const bookings = {
  create: (packageId, data) => client.post(`/book-package/${packageId}/`, data),
  list: () => client.get('/bookings/'),
  get: (id) => client.get(`/bookings/${id}/`),
  update: (id, data) => client.put(`/bookings/${id}/`, data),
  cancel: (id, data) => client.post(`/bookings/${id}/cancel/`, data),
  modify: (id, data) => client.post(`/bookings/${id}/modify/`, data),
  applyPromo: (id, data) => client.post(`/bookings/${id}/apply-promo/`, data),
  removePromo: (id) => client.post(`/bookings/${id}/remove-promo/`),
  confirm: (data) => client.post('/booking-confirm/', data),
  complete: (id) => client.get(`/bookings/complete/${id}/`),
  getPayment: (bookingId, mode) => client.get(`/booking-payment/${bookingId}/${mode}/`),
};

// Invoices & Payments
export const invoices = {
  preview: (id) => client.get(`/preview-invoice/${id}/`),
  makePayment: (id, data) => client.post(`/make-payment/${id}/`, data),
  download: (id) => client.get(`/invoices/${id}/download/`, { responseType: 'blob' }),
};

// Wallet
export const wallet = {
  list: () => client.get('/wallets/'),
  create: () => client.post('/wallets/'),
  get: (id) => client.get(`/wallets/${id}/`),
  deposit: (data) => client.post('/wallets/deposit/', data),
  withdraw: (id, data) => client.post(`/wallets/${id}/withdraw/`, data),
  transfer: (id, data) => client.post(`/wallets/${id}/transfer/`, data),
  verifyPayment: (sessionId) => client.get(`/verify-payment/${sessionId}/`),
  getTransactions: (params) => client.get('/transactions/', { params }),
};

// Reviews
export const reviews = {
  list: (packageId) => client.get(`/packages/${packageId}/reviews/`),
  create: (packageId, data) => client.post(`/packages/${packageId}/reviews/`, data),
  get: (id) => client.get(`/reviews/${id}/`),
  update: (id, data) => client.put(`/reviews/${id}/`, data),
  delete: (id) => client.delete(`/reviews/${id}/`),
};

// Blog
export const blog = {
  list: (params) => client.get('/blog/', { params }),
  get: (slug) => client.get(`/blog/${slug}/`),
  addComment: (slug, data) => client.post(`/blog/${slug}/comments/`, data),
  updateComment: (id, data) => client.put(`/blog/comments/${id}/`, data),
  deleteComment: (id) => client.delete(`/blog/comments/${id}/`),
  react: (slug, data) => client.post(`/blog/${slug}/react/`, data),
};

// Notifications
export const notifications = {
  list: () => client.get('/notifications/'),
  get: (id) => client.get(`/notifications/${id}/`),
  markRead: (id) => client.put(`/notifications/${id}/`),
  delete: (id) => client.delete(`/notifications/${id}/`),
};

// Support
export const support = {
  list: () => client.get('/support/'),
  create: (data) => client.post('/support/', data),
  get: (id) => client.get(`/support/${id}/`),
  update: (id, data) => client.put(`/support/${id}/`, data),
  reply: (id, data) => client.post(`/support/${id}/reply/`, data),
  close: (id) => client.post(`/support/${id}/close/`),
};

// Events
export const events = {
  list: (params) => client.get('/events/', { params }),
  get: (id) => client.get(`/events/${id}/`),
};

// Personalised Bookings
export const personalisedBookings = {
  list: () => client.get('/personalised-bookings/'),
  create: (data) => client.post('/personalised-bookings/', data),
  get: (id) => client.get(`/personalised-bookings/${id}/`),
  update: (id, data) => client.put(`/personalised-bookings/${id}/`, data),
  delete: (id) => client.delete(`/personalised-bookings/${id}/`),
};

// Cruise Bookings
export const cruiseBookings = {
  list: () => client.get('/cruise-bookings/'),
  create: (data) => client.post('/cruise-bookings/', data),
  get: (id) => client.get(`/cruise-bookings/${id}/`),
};

// Search & Location
export const search = {
  locations: (params) => client.get('/search-locations/', { params }),
  countriesLocations: (params) => client.get('/search-countries-locations/', { params }),
};

// Contact
export const contact = {
  submit: (data) => client.post('/contact/', data),
};

// Carousel
export const carousel = {
  list: () => client.get('/carousel/'),
};
