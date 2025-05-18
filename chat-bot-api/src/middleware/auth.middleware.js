const { verifyToken } = require('../utils/encryption');

const authenticate = (req, res, next) => {
  // Get token from header
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ 
      success: false, 
      message: 'Access denied. No token provided.' 
    });
  }
  
  const token = authHeader.split(' ')[1];
  
  // Verify token
  const decoded = verifyToken(token);
  if (!decoded) {
    return res.status(401).json({ 
      success: false, 
      message: 'Invalid token or token expired.' 
    });
  }
  
  // Add user to request
  req.userId = decoded.id;
  next();
};

module.exports = { authenticate };