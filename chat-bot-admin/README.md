# FanFix ChatAssist Admin Interface

This is the admin interface for the FanFix ChatAssist system, which allows administrators to manage creator profiles, writing styles, and conversation examples used by the AI suggestion system.

## Features

- **User Authentication**: Secure login and registration
- **Creator Management**: Add, edit, and deactivate creator profiles
- **Writing Style Configuration**: Detailed configuration of creator-specific writing styles
  - Text replacements (e.g., "you" → "u")
  - Approved emojis list
  - Case style preferences (lowercase, sentence case, etc.)
  - Punctuation rules
  - Abbreviation preferences
  - Message length preferences
  - And more...
- **Example Management**: Add and manage conversation examples to help the AI learn each creator's style
- **Responsive Design**: Works on desktop and mobile browsers

## Getting Started

### Prerequisites

- Node.js (v14+)
- npm or yarn

### Installation

1. Clone this repository
```
git clone https://github.com/yourusername/fanfix-admin.git
cd fanfix-admin
```

2. Install dependencies
```
npm install
```

3. Create a `.env` file in the root directory with the following content:
```
REACT_APP_API_URL=http://localhost:3000/api
```

4. Start the development server
```
npm start
```

## Project Structure

- `/src/components/auth` - Authentication components
- `/src/components/creators` - Creator management components
- `/src/components/dashboard` - Dashboard and overview components
- `/src/contexts` - React context providers
- `/src/services` - API services and utilities
- `/src/hooks` - Custom React hooks
- `/src/utils` - Utility functions

## Technologies Used

- **React** - Frontend framework
- **React Router** - Navigation and routing
- **Tailwind CSS** - Styling
- **Formik & Yup** - Form handling and validation
- **Axios** - API requests
- **React Toastify** - Notifications

## Connecting to the API

This admin interface is designed to work with the FanFix ChatAssist API. Make sure the API server is running and accessible at the URL specified in your `.env` file.

## Building for Production

```
npm run build
```

This creates an optimized production build in the `build` folder, ready for deployment.

## Deployment

The admin interface can be deployed to any static hosting service:

1. Build the project:
```
npm run build
```

2. Deploy the contents of the `build` directory to your hosting provider.

## Security Considerations

- The admin interface uses JWT authentication
- Tokens are stored in localStorage
- For production deployment, ensure the site is served over HTTPS
- Consider implementing additional security measures like rate limiting and IP restrictions on the API