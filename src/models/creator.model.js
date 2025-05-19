const db = require('../services/database.service');

const CreatorModel = {
  // Get all creators
  async getAll() {
    const result = await db.query(
      'SELECT id, name, description, avatar_url, active FROM creators WHERE active = true'
    );
    return result.rows;
  },
  
  // Get creator by ID
  async getById(id) {
    const result = await db.query(
      'SELECT id, name, description, avatar_url, active FROM creators WHERE id = $1',
      [id]
    );
    return result.rows[0];
  },
  
  // Get creator with style
  async getWithStyle(id) {
    const creator = await this.getById(id);
    
    if (!creator) return null;
    
    const styleResult = await db.query(
      'SELECT * FROM creator_styles WHERE creator_id = $1',
      [id]
    );
    
    const examplesResult = await db.query(
      'SELECT id, fan_message, creator_responses FROM style_examples WHERE creator_id = $1 LIMIT 5',
      [id]
    );
    
    return {
      ...creator,
      style: styleResult.rows[0] || null,
      examples: examplesResult.rows || []
    };
  },
  
  // Create a new creator
  async create(name, description, avatarUrl) {
    const result = await db.query(
      'INSERT INTO creators (name, description, avatar_url) VALUES ($1, $2, $3) RETURNING *',
      [name, description, avatarUrl]
    );
    return result.rows[0];
  },
  
  // Update a creator
  async update(id, name, description, avatarUrl, active) {
    const result = await db.query(
      `UPDATE creators 
       SET name = COALESCE($2, name),
           description = COALESCE($3, description),
           avatar_url = COALESCE($4, avatar_url),
           active = COALESCE($5, active)
       WHERE id = $1
       RETURNING *`,
      [id, name, description, avatarUrl, active]
    );
    return result.rows[0];
  },
  
  // Update or create creator style
  async upsertStyle(creatorId, styleData) {
    // Check if style exists
    const existing = await db.query(
      'SELECT creator_id FROM creator_styles WHERE creator_id = $1',
      [creatorId]
    );
    
    if (existing.rows.length > 0) {
      // Update existing style
      const result = await db.query(
        `UPDATE creator_styles
         SET approved_emojis = COALESCE($2, approved_emojis),
             case_style = COALESCE($3, case_style),
             text_replacements = COALESCE($4, text_replacements),
             sentence_separators = COALESCE($5, sentence_separators),
             punctuation_rules = COALESCE($6, punctuation_rules),
             abbreviations = COALESCE($7, abbreviations),
             message_length_preference = COALESCE($8, message_length_preference),
             style_instructions = COALESCE($9, style_instructions),
             tone_range = COALESCE($10, tone_range)
         WHERE creator_id = $1
         RETURNING *`,
        [
          creatorId, 
          styleData.approved_emojis,
          styleData.case_style,
          styleData.text_replacements,
          styleData.sentence_separators,
          styleData.punctuation_rules,
          styleData.abbreviations,
          styleData.message_length_preference,
          styleData.style_instructions,
          styleData.tone_range
        ]
      );
      return result.rows[0];
    } else {
      // Create new style
      const result = await db.query(
        `INSERT INTO creator_styles (
           creator_id, approved_emojis, case_style, text_replacements,
           sentence_separators, punctuation_rules, abbreviations,
           message_length_preference, style_instructions, tone_range
         )
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
         RETURNING *`,
        [
          creatorId, 
          styleData.approved_emojis,
          styleData.case_style,
          styleData.text_replacements,
          styleData.sentence_separators,
          styleData.punctuation_rules,
          styleData.abbreviations,
          styleData.message_length_preference,
          styleData.style_instructions,
          styleData.tone_range
        ]
      );
      return result.rows[0];
    }
  },
  
  // Add style example
  async addExample(creatorId, fanMessage, creatorResponses) {
    const result = await db.query(
      'INSERT INTO style_examples (creator_id, fan_message, creator_responses) VALUES ($1, $2, $3) RETURNING *',
      [creatorId, fanMessage, creatorResponses]
    );
    return result.rows[0];
  }
};

module.exports = CreatorModel;