// server.js — main Express entry point
const express = require('express');
const { authenticateToken } = require('./middleware/authGuard');
const checkoutRouter = require('./checkout');

const app = express();
app.use(express.json());

// Public routes
app.post('/auth/login', require('./auth').login);
app.post('/auth/refresh', require('./auth').refresh);

// Protected routes
app.use('/api', authenticateToken);
app.use('/api/checkout', checkoutRouter);

app.get('/api/profile', (req, res) => {
  res.json({ user: req.user });
});

app.listen(3001, () => {
  console.log('Server running on port 3001');
});
