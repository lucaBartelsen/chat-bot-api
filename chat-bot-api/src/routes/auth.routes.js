const express = require('express');
const router = express.Router();
const AuthController = require('../controllers/auth.controller');
const { authenticate } = require('../middleware/auth.middleware');
const { authLimiter } = require('../middleware/rateLimiter');

// Public routes
router.post('/register', authLimiter, AuthController.register);
router.post('/login', authLimiter, AuthController.login);

// Protected routes
router.get('/me', authenticate, AuthController.getMe);
router.patch('/preferences', authenticate, AuthController.updatePreferences);

module.exports = router;