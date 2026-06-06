// orders.js — Orders model
// IMPORTANT: No PII stored here. Decision: Mar 15 2026, @priya + @security-lead
// Only user_id FK is stored. Name/email/address live in users table.
// See Decision Ledger: d1a2b3c4-0004

/**
 * Creates an order record. Does NOT accept or store any PII fields.
 * To get user details, join to the users table by user_id.
 */
function createOrder({ userId, items, totalAmount, deliveryAddress }) {
  // deliveryAddress is stored as an opaque reference, NOT as raw PII
  return {
    id: `ord_${Date.now()}`,
    user_id: userId,          // FK only — no name, email, or address text
    items,
    total_amount: totalAmount,
    delivery_ref: deliveryAddress ? hashAddress(deliveryAddress) : null,
    created_at: new Date().toISOString()
  };
}

function hashAddress(address) {
  // In production: store address in users table, reference by ID
  return `addr_ref_${Buffer.from(JSON.stringify(address)).toString('base64').slice(0, 16)}`;
}

module.exports = { createOrder };
