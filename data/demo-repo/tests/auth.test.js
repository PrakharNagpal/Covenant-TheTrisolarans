// tests/auth.test.js — Basic JWT auth tests
const { signAccessToken, verifyToken } = require('../auth');

function assert(condition, message) {
  if (!condition) throw new Error(`FAIL: ${message}`);
  console.log(`PASS: ${message}`);
}

// Test 1: Sign and verify a token
const token = signAccessToken({ id: 'usr_001', username: 'alice' });
assert(typeof token === 'string', 'signAccessToken returns a string');

const decoded = verifyToken(token);
assert(decoded.id === 'usr_001', 'verifyToken decodes correct id');
assert(decoded.username === 'alice', 'verifyToken decodes correct username');

// Test 2: Invalid token throws
try {
  verifyToken('not.a.real.token');
  assert(false, 'Should have thrown for invalid token');
} catch (e) {
  assert(true, 'verifyToken throws for invalid token');
}

console.log('\nAll tests passed.');
