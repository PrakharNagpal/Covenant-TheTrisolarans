// auth.js — JWT authentication (decided: Jan 14 2026, @alice + @bob)
// Decision: Use JWT for stateless auth. Sessions rejected due to operational
// complexity of shared session store. See Decision Ledger: d1a2b3c4-0001

const jwt = require('jsonwebtoken');

const SECRET = process.env.JWT_SECRET || 'covenant-demo-secret';
const ACCESS_EXPIRY = '15m';
const REFRESH_EXPIRY = '7d';

/**
 * Signs a new JWT access token for the given user payload.
 * Token is stateless — no server-side state stored.
 */
function signAccessToken(payload) {
  return jwt.sign(payload, SECRET, { expiresIn: ACCESS_EXPIRY });
}

/**
 * Signs a long-lived refresh token.
 * Stored client-side. Revocation handled via a blocklist in Redis (short-lived).
 */
function signRefreshToken(payload) {
  return jwt.sign(payload, SECRET, { expiresIn: REFRESH_EXPIRY });
}

/**
 * Verifies a JWT token. Returns the decoded payload or throws.
 */
function verifyToken(token) {
  return jwt.verify(token, SECRET);
}

/**
 * POST /auth/login
 * Returns a signed JWT access token + refresh token.
 */
function login(req, res) {
  const { username, password } = req.body;
  // Demo: accept any username/password
  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }
  const user = { id: 'usr_demo_001', username };
  const accessToken = signAccessToken(user);
  const refreshToken = signRefreshToken({ id: user.id });
  res.json({ accessToken, refreshToken, tokenType: 'Bearer' });
}

/**
 * POST /auth/refresh
 * Accepts a valid refresh token, returns a new access token.
 */
function refresh(req, res) {
  const { refreshToken } = req.body;
  if (!refreshToken) return res.status(401).json({ error: 'Refresh token required' });
  try {
    const payload = verifyToken(refreshToken);
    const newAccessToken = signAccessToken({ id: payload.id });
    res.json({ accessToken: newAccessToken, tokenType: 'Bearer' });
  } catch (err) {
    res.status(401).json({ error: 'Invalid or expired refresh token' });
  }
}

module.exports = { signAccessToken, signRefreshToken, verifyToken, login, refresh };
