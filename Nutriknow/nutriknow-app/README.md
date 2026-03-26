# Nutriknow

A cloud-based web application that analyzes nutrition labels and provides plain-language explanations, insights, and health scores.

## Features

-- Image upload processed by OpenAI Vision (server-side) and analyzed by the LLM
- Plain-language explanations of nutritional content
- Health scoring and insights generation
- Allergen detection and alerts
- Serving size normalization
- Visual breakdowns of nutritional data

## Tech Stack

- **Frontend:** Next.js, TypeScript, Tailwind CSS
- **Backend Services:** (To be implemented)
   - Vision + LLM Analysis Service
  - User Authentication
  - Data Storage

## Project Structure

```
src/
├── app/              # Next.js app router pages
├── components/       # React components
│   ├── ImageUploader.tsx
│   └── AnalysisResult.tsx
├── services/         # API and business logic
│   └── analysisService.ts
└── types/           # TypeScript type definitions
    └── nutrition.ts
```

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env.local` file with required environment variables
4. Start the development server:
   ```bash
   npm run dev
   ```

Visit [http://localhost:3000](http://localhost:3000) to view the application.

## Environment Variables

Create a `.env.local` file with:

```
NEXT_PUBLIC_LLM_API_ENDPOINT=http://localhost:3001/api/llm
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run type checking
npm run type-check
```

## Architecture

### Frontend (Current Implementation)

- **Next.js App Router** for page routing and server components
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **React** components with proper separation of concerns

### Backend (To Be Implemented)

- OCR processing service
- LLM integration for analysis
- User authentication and authorization
- Database for user data and history
- Cloud storage for temporary image files

## Security Considerations

- All API endpoints will require authentication
- Input sanitization for OCR results
- Secure handling of user data
- HTTPS-only communication
- Rate limiting on API endpoints
- Proper environment variable management

## Future Enhancements

1. User authentication and profiles
2. History tracking of scanned items
3. Comparison features
4. Enhanced allergen detection
5. Dietary preference profiles
6. Export and sharing capabilities

## License

MIT

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
