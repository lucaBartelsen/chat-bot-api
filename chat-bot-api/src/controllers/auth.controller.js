const UserModel = require('../models/user.model');
const { comparePassword, generateToken, generateRefreshToken } = require('../utils/encryption');

const AuthController = {
  // Register a new user
  async register(req, res) {
    try {
      const { email, password } = req.body;
      
      // Validate input
      if (!email || !password) {
        return res.status(400).json({
          success: false,
          message: 'Email and password are required'
        });
      }
      
      // Check if user already exists
      const existingUser = await UserModel.findByEmail(email);
      if (existingUser) {
        return res.status(400).json({
          success: false,
          message: 'User with this email already exists'
        });
      }
      
      // Create new user
      const newUser = await UserModel.create(email, password);
      
      res.status(201).json({
        success: true,
        message: 'User registered successfully',
        user: {
          id: newUser.id,
          email: newUser.email,
          created_at: newUser.created_at
        }
      });
    } catch (error) {
      console.error('Registration error:', error);
      res.status(500).json({
        success: false,
        message: 'Error registering user'
      });
    }
  },
  
  // Login user
  async login(req, res) {
    try {
      const { email, password } = req.body;
      
      // Validate input
      if (!email || !password) {
        return res.status(400).json({
          success: false,
          message: 'Email and password are required'
        });
      }
      
      // Find user
      const user = await UserModel.findByEmail(email);
      if (!user) {
        return res.status(401).json({
          success: false,
          message: 'Invalid email or password'
        });
      }
      
      // Check password
      const isPasswordValid = await comparePassword(password, user.password_hash);
      if (!isPasswordValid) {
        return res.status(401).json({
          success: false,
          message: 'Invalid email or password'
        });
      }
      
      // Update last login time
      await UserModel.updateLastLogin(user.id);
      
      // Generate tokens
      const token = generateToken(user.id);
      const refreshToken = generateRefreshToken(user.id);
      
      // Get user preferences
      const preferences = await UserModel.getPreferences(user.id);
      
      res.status(200).json({
        success: true,
        message: 'Login successful',
        userId: user.id,
        email: user.email,
        token,
        refreshToken,
        preferences
      });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({
        success: false,
        message: 'Error logging in'
      });
    }
  },
  
  // Get current user
  async getMe(req, res) {
    try {
      const user = await UserModel.findById(req.userId);
      
      if (!user) {
        return res.status(404).json({
          success: false,
          message: 'User not found'
        });
      }
      
      // Get user preferences
      const preferences = await UserModel.getPreferences(user.id);
      
      res.status(200).json({
        success: true,
        user: {
          id: user.id,
          email: user.email,
          created_at: user.created_at,
          last_login: user.last_login,
          preferences
        }
      });
    } catch (error) {
      console.error('Get user error:', error);
      res.status(500).json({
        success: false,
        message: 'Error retrieving user information'
      });
    }
  },
  
  // Update user preferences
  async updatePreferences(req, res) {
    try {
      const { selected_creator_id, openai_api_key, model_name, num_suggestions } = req.body;
      
      const updatedPreferences = await UserModel.updatePreferences(
        req.userId,
        { selected_creator_id, openai_api_key, model_name, num_suggestions }
      );
      
      res.status(200).json({
        success: true,
        message: 'Preferences updated successfully',
        preferences: updatedPreferences
      });
    } catch (error) {
      console.error('Update preferences error:', error);
      res.status(500).json({
        success: false,
        message: 'Error updating preferences'
      });
    }
  }
};

module.exports = AuthController;