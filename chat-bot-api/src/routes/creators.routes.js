const express = require('express');
const router = express.Router();
const CreatorsController = require('../controllers/creators.controller');
const { authenticate } = require('../middleware/auth.middleware');

// Public routes (but still require authentication)
router.get('/', authenticate, CreatorsController.getAllCreators);
router.get('/:id', authenticate, CreatorsController.getCreatorById);

// Admin-only routes (would need additional middleware for admin check)
// For simplicity, we're just using the authenticate middleware for now
router.post('/', authenticate, CreatorsController.createCreator);
router.patch('/:id', authenticate, CreatorsController.updateCreator);
router.patch('/:id/style', authenticate, CreatorsController.updateCreatorStyle);
router.post('/:id/examples', authenticate, CreatorsController.addStyleExample);

module.exports = router;