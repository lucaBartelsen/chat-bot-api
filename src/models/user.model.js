const db = require('../services/database.service');
const { hashPassword } = require('../utils/encryption');

const UserModel = {
  // Create a new user
  async create(email, password) {
    const hashedPassword = await hashPassword(password);
    
    const result = await db.query(
      'INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email, created_at',
      [email, hashedPassword]
    );
    
    // Create default user preferences
    if (result.rows[0]) {
      await db.query(
        'INSERT INTO user_preferences (user_id) VALUES ($1)',
        [result.rows[0].id]
      );
    }
    
    return result.rows[0];
  },
  
  // Find user by email
  async findByEmail(email) {
    const result = await db.query(
      'SELECT * FROM users WHERE email = $1',
      [email]
    );
    return result.rows[0];
  },
  
  // Find user by ID
  async findById(id) {
    const result = await db.query(
      'SELECT id, email, created_at, last_login FROM users WHERE id = $1',
      [id]
    );
    return result.rows[0];
  },
  
  // Update last login time
  async updateLastLogin(id) {
    const result = await db.query(
      'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1 RETURNING id',
      [id]
    );
    return result.rows[0];
  },
  
  // Get user preferences
  async getPreferences(userId) {
    const result = await db.query(
      'SELECT * FROM user_preferences WHERE user_id = $1',
      [userId]
    );
    return result.rows[0];
  },
  
  // Update user preferences
  async updatePreferences(userId, preferences) {
    const { selected_creator_id, openai_api_key, model_name, num_suggestions } = preferences;
    
    const result = await db.query(
      `UPDATE user_preferences 
       SET selected_creator_id = COALESCE($2, selected_creator_id),
           openai_api_key = COALESCE($3, openai_api_key),
           model_name = COALESCE($4, model_name),
           num_suggestions = COALESCE($5, num_suggestions)
       WHERE user_id = $1
       RETURNING *`,
      [userId, selected_creator_id, openai_api_key, model_name, num_suggestions]
    );
    
    return result.rows[0];
  }
};

module.exports = UserModel;