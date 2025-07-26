# Hypomnema

A modern biblical commentary application built with React, TypeScript, and Vite.

## Features

- Browse biblical books and chapters
- View verse-by-verse text
- Add and view commentary on individual verses
- Clean, responsive interface built with Tailwind CSS
- State management with Zustand

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hypomnema.git
cd hypomnema
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:5173](http://localhost:5173) in your browser

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm run preview` - Preview the production build
- `npm run lint` - Run ESLint

## Tech Stack

- **React** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Zustand** - State management

## Project Structure

```
hypomnema/
├── src/
│   ├── components/     # React components
│   │   ├── BookSelector.tsx
│   │   ├── ChapterSelector.tsx
│   │   ├── CommentaryPanel.tsx
│   │   └── VerseDisplay.tsx
│   ├── data/          # Static data (books, etc.)
│   ├── store/         # Zustand store
│   ├── types/         # TypeScript types
│   └── App.tsx        # Main app component
├── public/            # Static assets
└── package.json       # Dependencies and scripts
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.