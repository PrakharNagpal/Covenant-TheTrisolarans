// checkout.js — 3-step checkout flow
// Decision: Feb 28 2026, @alice + @design-lead
// Steps: 1-CartReview, 2-DeliveryDetails, 3-Payment
// 4-step flow was prototyped and rejected (user research showed higher abandonment)

const express = require('express');
const router = express.Router();

const CHECKOUT_STEPS = ['cart_review', 'delivery_details', 'payment'];
const TOTAL_STEPS = 3;

/**
 * GET /api/checkout/session
 * Returns the current checkout session state.
 */
router.get('/session', (req, res) => {
  res.json({
    userId: req.user.id,
    currentStep: 1,
    totalSteps: TOTAL_STEPS,
    steps: CHECKOUT_STEPS
  });
});

/**
 * POST /api/checkout/step/1 — Cart review
 */
router.post('/step/1', (req, res) => {
  const { cartItems } = req.body;
  if (!cartItems || cartItems.length === 0) {
    return res.status(400).json({ error: 'Cart is empty' });
  }
  const total = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
  res.json({ step: 1, name: 'cart_review', total, nextStep: 2 });
});

/**
 * POST /api/checkout/step/2 — Delivery details
 */
router.post('/step/2', (req, res) => {
  const { address, city, postalCode } = req.body;
  if (!address || !city || !postalCode) {
    return res.status(400).json({ error: 'Delivery details incomplete' });
  }
  res.json({ step: 2, name: 'delivery_details', confirmed: true, nextStep: 3 });
});

/**
 * POST /api/checkout/step/3 — Payment (final step)
 */
router.post('/step/3', (req, res) => {
  const { paymentMethod, cardLast4 } = req.body;
  if (!paymentMethod) {
    return res.status(400).json({ error: 'Payment method required' });
  }
  res.json({
    step: 3,
    name: 'payment',
    status: 'confirmed',
    orderId: `ord_${Date.now()}`,
    message: 'Order placed successfully'
  });
});

module.exports = router;
