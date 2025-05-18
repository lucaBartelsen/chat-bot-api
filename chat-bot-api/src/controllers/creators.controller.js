const CreatorModel = require('../models/creator.model');

const CreatorsController = {
  // Get all creators
  async getAllCreators(req, res) {
    try {
      const creators = await CreatorModel.getAll();
      
      res.status(200).json({
        success: true,
        creators
      });
    } catch (error) {
      console.error('Get creators error:', error);
      res.status(500).json({
        success: false,
        message: 'Error retrieving creators'
      });
    }
  },
  
  // Get creator by ID
  async getCreatorById(req, res) {
    try {
      const { id } = req.params;
      
      const creator = await CreatorModel.getWithStyle(id);
      
      if (!creator) {
        return res.status(404).json({
          success: false,
          message: 'Creator not found'
        });
      }
      
      res.status(200).json({
        success: true,
        creator
      });
    } catch (error) {
      console.error('Get creator error:', error);
      res.status(500).json({
        success: false,
        message: 'Error retrieving creator'
      });
    }
  },
  
  // Create a new creator (admin only)
  async createCreator(req, res) {
    try {
      const { name, description, avatar_url } = req.body;
      
      // Validate input
      if (!name) {
        return res.status(400).json({
          success: false,
          message: 'Creator name is required'
        });
      }
      
      const newCreator = await CreatorModel.create(name, description, avatar_url);
      
      res.status(201).json({
        success: true,
        message: 'Creator created successfully',
        creator: newCreator
      });
    } catch (error) {
      console.error('Create creator error:', error);
      res.status(500).json({
        success: false,
        message: 'Error creating creator'
      });
    }
  },
  
  // Update a creator (admin only)
  async updateCreator(req, res) {
    try {
      const { id } = req.params;
      const { name, description, avatar_url, active } = req.body;
      
      const updatedCreator = await CreatorModel.update(id, name, description, avatar_url, active);
      
      if (!updatedCreator) {
        return res.status(404).json({
          success: false,
          message: 'Creator not found'
        });
      }
      
      res.status(200).json({
        success: true,
        message: 'Creator updated successfully',
        creator: updatedCreator
      });
    } catch (error) {
      console.error('Update creator error:', error);
      res.status(500).json({
        success: false,
        message: 'Error updating creator'
      });
    }
  },
  
  // Update or create creator style (admin only)
  async updateCreatorStyle(req, res) {
    try {
      const { id } = req.params;
      const styleData = req.body;
      
      // Check if creator exists
      const creator = await CreatorModel.getById(id);
      if (!creator) {
        return res.status(404).json({
          success: false,
          message: 'Creator not found'
        });
      }
      
      const style = await CreatorModel.upsertStyle(id, styleData);
      
      res.status(200).json({
        success: true,
        message: 'Creator style updated successfully',
        style
      });
    } catch (error) {
      console.error('Update creator style error:', error);
      res.status(500).json({
        success: false,
        message: 'Error updating creator style'
      });
    }
  },
  
  // Add style example (admin only)
  async addStyleExample(req, res) {
    try {
      const { id } = req.params;
      const { fan_message, creator_responses } = req.body;
      
      // Validate input
      if (!fan_message || !creator_responses || !Array.isArray(creator_responses)) {
        return res.status(400).json({
          success: false,
          message: 'Fan message and creator responses array are required'
        });
      }
      
      // Check if creator exists
      const creator = await CreatorModel.getById(id);
      if (!creator) {
        return res.status(404).json({
          success: false,
          message: 'Creator not found'
        });
      }
      
      const example = await CreatorModel.addExample(id, fan_message, creator_responses);
      
      res.status(201).json({
        success: true,
        message: 'Style example added successfully',
        example
      });
    } catch (error) {
      console.error('Add style example error:', error);
      res.status(500).json({
        success: false,
        message: 'Error adding style example'
      });
    }
  }
};

module.exports = CreatorsController;