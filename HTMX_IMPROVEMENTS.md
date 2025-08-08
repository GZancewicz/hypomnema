# HTMX Improvements for Hypomnema

## Current HTMX Usage (Minimal)
- Basic AJAX loading with `htmx.ajax()` JavaScript calls
- One `hx-get` with `hx-trigger="load"` for initial content
- Using `htmx:afterSwap` event for post-load processing

## Missed HTMX Opportunities

### 1. **Declarative Navigation** (HIGH PRIORITY)
Instead of JavaScript onclick handlers:
```html
<!-- Current -->
<li class="book-item" onclick="selectBook('{{.ID}}', {{.Chapters}})">

<!-- Better with HTMX -->
<li class="book-item" 
    hx-get="/api/chapter/{{.ID}}/1"
    hx-target="#text-content"
    hx-push-url="/{{.ID}}/1"
    hx-indicator=".htmx-indicator">
```

### 2. **History Support with hx-push-url**
- Add proper browser history for navigation
- Enable back/forward buttons
- Bookmarkable URLs for specific chapters/homilies

### 3. **Partial Page Updates with hx-select**
```html
<!-- Load just the verse content, not the whole response -->
<button hx-get="/api/chapter/matthew/2" 
        hx-select=".chapter-text"
        hx-target="#text-content">
```

### 4. **Loading States with hx-indicator**
```html
<div class="htmx-indicator">
    <div class="spinner"></div>
    Loading commentary...
</div>
```

### 5. **Keyboard Shortcuts with hx-trigger**
```html
<div hx-get="/api/chapter/next" 
     hx-trigger="keyup[key=='ArrowRight'] from:body"
     hx-target="#text-content">
```

### 6. **Infinite Scroll for Long Texts**
```html
<div hx-get="/api/homily/{{.ID}}/more"
     hx-trigger="revealed"
     hx-swap="afterend">
```

### 7. **Out-of-Band Updates (hx-swap-oob)**
Update multiple parts of the page in one response:
```html
<!-- Server returns -->
<div id="text-content">...new content...</div>
<div id="chapter-title" hx-swap-oob="true">Chapter 2</div>
<nav id="chapter-nav" hx-swap-oob="true">...updated nav...</nav>
```

### 8. **Active Search with hx-trigger="keyup changed delay:500ms"**
```html
<input type="search" 
       hx-get="/api/search"
       hx-trigger="keyup changed delay:500ms"
       hx-target="#search-results">
```

### 9. **Preloading with hx-boost**
```html
<!-- Preload all navigation links -->
<nav hx-boost="true">
    <a href="/matthew/1">Matthew 1</a>
    <a href="/matthew/2">Matthew 2</a>
</nav>
```

### 10. **WebSocket/SSE Support**
For real-time features like collaborative reading sessions:
```html
<div hx-ext="sse" sse-connect="/api/reading-session">
    <div sse-swap="message">Latest annotations...</div>
</div>
```

### 11. **Form Enhancement**
For future features like note-taking:
```html
<form hx-post="/api/notes"
      hx-trigger="submit"
      hx-swap="outerHTML">
    <textarea name="note"></textarea>
    <button type="submit">Save Note</button>
</form>
```

### 12. **Lazy Loading with hx-trigger="intersect"**
```html
<div hx-get="/api/commentary/{{.ID}}"
     hx-trigger="intersect once"
     hx-swap="outerHTML">
    <div class="placeholder">Commentary will load when visible...</div>
</div>
```

## Implementation Priority

### Phase 1 (Quick Wins)
1. Replace JavaScript navigation with HTMX attributes
2. Add hx-push-url for browser history
3. Implement proper loading indicators

### Phase 2 (Enhanced UX)
1. Add keyboard navigation
2. Implement active search
3. Add preloading for adjacent chapters

### Phase 3 (Advanced Features)
1. Infinite scroll for long homilies
2. Out-of-band updates for complex state changes
3. WebSocket support for future collaborative features

## Benefits of Full HTMX Usage
- **Less JavaScript**: Remove most custom JS code
- **Better Performance**: Smaller payload, partial updates
- **Improved SEO**: Server-side rendering with progressive enhancement
- **Simpler Codebase**: Declarative HTML instead of imperative JS
- **Better Accessibility**: Works without JavaScript
- **Automatic Features**: History, loading states, error handling built-in