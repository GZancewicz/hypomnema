package main

import (
	"embed"
	"encoding/json"
	"fmt"
	"html"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
)

//go:embed templates/*
var templateFS embed.FS

// Book represents a Bible book
type Book struct {
	ID           string `json:"id"`
	Name         string `json:"name"`
	Chapters     int    `json:"chapters"`
	ChapterRange []int  `json:"-"` // For template use
}

// GetChapterRange returns a slice of chapter numbers for iteration
func (b Book) GetChapterRange() []int {
	chapters := make([]int, b.Chapters)
	for i := 0; i < b.Chapters; i++ {
		chapters[i] = i + 1
	}
	return chapters
}

// ParagraphBreak represents where a new paragraph starts
type ParagraphBreak struct {
	Chapter int `json:"chapter"`
	Verse   int `json:"verse"`
}

// VerseToCanon holds the verse-to-canon mapping for each gospel
type VerseToCanon map[string]map[string]string

// CanonLookup holds the canon lookup table with format "I.1": {gospel: verses}
type CanonLookup map[string]map[string]string

// Homily represents a Chrysostom homily reference
type Homily struct {
	Number int    `json:"homily_number"`
	Roman  string `json:"homily_roman"`
	Passage string `json:"passage"`
	End    string `json:"end"`
}

// VerseToHomily holds the verse-to-homily mapping (multiple homilies per verse)
type VerseToHomily map[string][]Homily

// HomilyRange represents the coverage of a homily
type HomilyRange struct {
	Number       int    `json:"homily_number"`
	Roman        string `json:"homily_roman"`
	StartChapter int    `json:"start_chapter"`
	StartVerse   int    `json:"start_verse"`
	EndChapter   int    `json:"end_chapter"`
	EndVerse     int    `json:"end_verse"`
}

// HomilyFootnote represents a single footnote in a homily
type HomilyFootnote struct {
	Homily         int    `json:"homily"`
	OriginalNumber string `json:"original_number"`
	Content        string `json:"content"`
	ID             string `json:"id"`
	DisplayNumber  int    `json:"display_number"`
}

// AllFootnotes holds all footnotes for all homilies
type AllFootnotes map[string][]HomilyFootnote

// Footnote represents a footnote for display
type Footnote struct {
	Number  string
	Content string
}

// Commentary represents a set of homilies/sermons for a book
type Commentary struct {
	Author        string
	Book          string
	VerseToHomily VerseToHomily
	Coverage      map[int]HomilyRange
}

// Global data
var (
	verseToCanon VerseToCanon
	canonLookup CanonLookup
	commentaries map[string]*Commentary
	chrysostomMatthewFootnotes AllFootnotes
	chrysostomJohnFootnotes    AllFootnotes
	books = []Book{
		{ID: "matthew", Name: "Matthew", Chapters: 28},
		{ID: "mark", Name: "Mark", Chapters: 16},
		{ID: "luke", Name: "Luke", Chapters: 24},
		{ID: "john", Name: "John", Chapters: 21},
		{ID: "acts", Name: "Acts", Chapters: 28},
		{ID: "romans", Name: "Romans", Chapters: 16},
		{ID: "1corinthians", Name: "1 Corinthians", Chapters: 16},
		{ID: "2corinthians", Name: "2 Corinthians", Chapters: 13},
		{ID: "galatians", Name: "Galatians", Chapters: 6},
		{ID: "ephesians", Name: "Ephesians", Chapters: 6},
		{ID: "philippians", Name: "Philippians", Chapters: 4},
		{ID: "colossians", Name: "Colossians", Chapters: 4},
		{ID: "1thessalonians", Name: "1 Thessalonians", Chapters: 5},
		{ID: "2thessalonians", Name: "2 Thessalonians", Chapters: 3},
		{ID: "1timothy", Name: "1 Timothy", Chapters: 6},
		{ID: "2timothy", Name: "2 Timothy", Chapters: 4},
		{ID: "titus", Name: "Titus", Chapters: 3},
		{ID: "philemon", Name: "Philemon", Chapters: 1},
		{ID: "hebrews", Name: "Hebrews", Chapters: 13},
		{ID: "james", Name: "James", Chapters: 5},
		{ID: "1peter", Name: "1 Peter", Chapters: 5},
		{ID: "2peter", Name: "2 Peter", Chapters: 3},
		{ID: "1john", Name: "1 John", Chapters: 5},
		{ID: "2john", Name: "2 John", Chapters: 1},
		{ID: "3john", Name: "3 John", Chapters: 1},
		{ID: "jude", Name: "Jude", Chapters: 1},
		{ID: "revelation", Name: "Revelation", Chapters: 22},
	}

	paragraphData map[string][]ParagraphBreak
	templates     *template.Template
)

func init() {
	// Initialize commentaries map
	commentaries = make(map[string]*Commentary)
	// Force rebuild - footnote tooltip positioning fix
	
	// Load paragraph data
	loadParagraphData()
	
	// Load verse-to-canon mapping
	loadVerseToCanon()
	
	// Load canon lookup data
	loadCanonLookup()
	
	// Load all commentaries
	loadCommentary("chrysostom", "matthew", 
		"../texts/commentaries/chrysostom/matthew/matthew_verse_to_homilies.json",
		"../texts/commentaries/chrysostom/matthew/homily_coverage.json")
	loadCommentary("chrysostom", "john",
		"../texts/commentaries/chrysostom/john/john_verse_to_homilies.json",
		"../texts/commentaries/chrysostom/john/homily_coverage.json")
	loadCommentary("cyril", "luke",
		"../texts/commentaries/cyril/luke/luke_verse_to_homilies.json",
		"../texts/commentaries/cyril/luke/homily_coverage.json")

	// Load footnotes
	loadAllFootnotes()

	// Parse templates from filesystem (not embedded) for development
	var err error
	templates, err = template.ParseGlob("templates/*.html")
	if err != nil {
		log.Fatal("Error parsing templates:", err)
	}
}

func loadParagraphData() {
	file, err := os.Open("../texts/reference/kjv_paragraphs/kjv_paragraph_divisions.json")
	if err != nil {
		log.Println("Warning: Could not load paragraph data:", err)
		paragraphData = make(map[string][]ParagraphBreak)
		return
	}
	defer file.Close()

	err = json.NewDecoder(file).Decode(&paragraphData)
	if err != nil {
		log.Println("Warning: Could not parse paragraph data:", err)
		paragraphData = make(map[string][]ParagraphBreak)
	}
}

func loadVerseToCanon() {
	file, err := os.Open("../texts/reference/eusebian_canons/verse_to_canon.json")
	if err != nil {
		log.Println("Warning: Could not load verse-to-canon data:", err)
		verseToCanon = make(VerseToCanon)
		return
	}
	defer file.Close()

	err = json.NewDecoder(file).Decode(&verseToCanon)
	if err != nil {
		log.Println("Warning: Could not parse verse-to-canon data:", err)
		verseToCanon = make(VerseToCanon)
	}
}

func loadCanonLookup() {
	file, err := os.Open("../texts/reference/eusebian_canons/canon_lookup.json")
	if err != nil {
		log.Println("Warning: Could not load canon lookup:", err)
		canonLookup = make(CanonLookup)
		return
	}
	defer file.Close()

	err = json.NewDecoder(file).Decode(&canonLookup)
	if err != nil {
		log.Println("Warning: Could not parse canon lookup:", err)
		canonLookup = make(CanonLookup)
	}
}

// loadCommentary loads both verse-to-homily mapping and coverage data for a commentary
func loadCommentary(author, book, homiliesPath, coveragePath string) {
	key := fmt.Sprintf("%s-%s", author, book)
	commentary := &Commentary{
		Author: author,
		Book:   book,
	}
	
	// Load verse-to-homily mapping
	file, err := os.Open(homiliesPath)
	if err != nil {
		log.Printf("Warning: Could not load %s %s verse-to-homily data: %v", author, book, err)
		commentary.VerseToHomily = make(VerseToHomily)
	} else {
		defer file.Close()
		err = json.NewDecoder(file).Decode(&commentary.VerseToHomily)
		if err != nil {
			log.Printf("Warning: Could not parse %s %s verse-to-homily data: %v", author, book, err)
			commentary.VerseToHomily = make(VerseToHomily)
		}
	}
	
	// Load coverage data
	file2, err := os.Open(coveragePath)
	if err != nil {
		log.Printf("Warning: Could not load %s %s homily coverage data: %v", author, book, err)
		commentary.Coverage = make(map[int]HomilyRange)
	} else {
		defer file2.Close()
		var tempCoverage map[string]HomilyRange
		err = json.NewDecoder(file2).Decode(&tempCoverage)
		if err != nil {
			log.Printf("Warning: Could not parse %s %s homily coverage data: %v", author, book, err)
			commentary.Coverage = make(map[int]HomilyRange)
		} else {
			// Convert string keys to int
			commentary.Coverage = make(map[int]HomilyRange)
			for k, v := range tempCoverage {
				if num, err := strconv.Atoi(k); err == nil {
					commentary.Coverage[num] = v
				}
			}
			log.Printf("Loaded %s %s coverage for %d homilies/sermons", author, book, len(commentary.Coverage))
		}
	}
	
	commentaries[key] = commentary
}

// loadAllFootnotes loads the pre-extracted footnotes for all homilies
func loadAllFootnotes() {
	// Load Chrysostom Matthew footnotes
	matthewFile, err := os.Open("../texts/commentaries/chrysostom/matthew/all_footnotes.json")
	if err != nil {
		log.Printf("Could not load Chrysostom Matthew footnotes: %v", err)
	} else {
		defer matthewFile.Close()
		decoder := json.NewDecoder(matthewFile)
		if err := decoder.Decode(&chrysostomMatthewFootnotes); err != nil {
			log.Printf("Error decoding Chrysostom Matthew footnotes: %v", err)
		} else {
			count := 0
			for _, footnotes := range chrysostomMatthewFootnotes {
				count += len(footnotes)
			}
			log.Printf("Loaded %d Chrysostom Matthew footnotes across %d homilies", count, len(chrysostomMatthewFootnotes))
		}
	}
	
	// Load Chrysostom John footnotes
	johnFile, err := os.Open("../texts/commentaries/chrysostom/john/all_footnotes.json")
	if err != nil {
		log.Printf("Could not load Chrysostom John footnotes: %v", err)
	} else {
		defer johnFile.Close()
		decoder := json.NewDecoder(johnFile)
		if err := decoder.Decode(&chrysostomJohnFootnotes); err != nil {
			log.Printf("Error decoding Chrysostom John footnotes: %v", err)
		} else {
			count := 0
			for _, footnotes := range chrysostomJohnFootnotes {
				count += len(footnotes)
			}
			log.Printf("Loaded %d Chrysostom John footnotes across %d homilies", count, len(chrysostomJohnFootnotes))
		}
	}
}

// parseVerseRef parses a verse reference like "3.3" or "3.3-6" into chapter and verse numbers

func parseVerseRef(ref string) (startChap, startVerse, endChap, endVerse int, err error) {
	// Handle ranges like "3.3-6" or single verses like "3.3"
	parts := strings.Split(ref, "-")
	
	// Parse start reference
	startParts := strings.Split(parts[0], ".")
	if len(startParts) != 2 {
		return 0, 0, 0, 0, fmt.Errorf("invalid verse reference: %s", ref)
	}
	
	startChap, err = strconv.Atoi(startParts[0])
	if err != nil {
		return 0, 0, 0, 0, err
	}
	
	// Remove any letter suffixes from verse number (e.g., "23B" -> "23")
	startVerseStr := strings.TrimRight(startParts[1], "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
	startVerse, err = strconv.Atoi(startVerseStr)
	if err != nil {
		return 0, 0, 0, 0, err
	}
	
	// If no range, end is same as start
	if len(parts) == 1 {
		return startChap, startVerse, startChap, startVerse, nil
	}
	
	// Parse end reference
	if strings.Contains(parts[1], ".") {
		// Full reference like "3.6"
		endParts := strings.Split(parts[1], ".")
		endChap, err = strconv.Atoi(endParts[0])
		if err != nil {
			return 0, 0, 0, 0, err
		}
		// Remove any letter suffixes from verse number
		endVerseStr := strings.TrimRight(endParts[1], "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
		endVerse, err = strconv.Atoi(endVerseStr)
		if err != nil {
			return 0, 0, 0, 0, err
		}
	} else {
		// Just verse number like "6"
		endChap = startChap
		// Remove any letter suffixes from verse number
		endVerseStr := strings.TrimRight(parts[1], "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
		endVerse, err = strconv.Atoi(endVerseStr)
		if err != nil {
			return 0, 0, 0, 0, err
		}
	}
	
	return startChap, startVerse, endChap, endVerse, nil
}

// findHomiliesForRange finds which homilies cover a given passage for a specific commentary
func findHomiliesForRange(author, book string, startChap, startVerse, endChap, endVerse int) []Homily {
	key := fmt.Sprintf("%s-%s", author, book)
	commentary, ok := commentaries[key]
	if !ok {
		return nil
	}
	
	var result []Homily
	for _, hr := range commentary.Coverage {
		// Check if the homily range overlaps with the requested range
		if (hr.StartChapter < endChap || (hr.StartChapter == endChap && hr.StartVerse <= endVerse)) &&
		   (hr.EndChapter > startChap || (hr.EndChapter == startChap && hr.EndVerse >= startVerse)) {
			// Simple passage format - we'll format it properly when displaying
			passage := fmt.Sprintf("%d:%d-%d:%d", hr.StartChapter, hr.StartVerse, hr.EndChapter, hr.EndVerse)
			
			result = append(result, Homily{
				Number: hr.Number,
				Roman:  hr.Roman,
				Passage: passage,
			})
		}
	}
	
	return result
}

func main() {
	// Load footnotes at startup
	if err := loadFootnotes(); err != nil {
		log.Printf("Warning: Failed to load footnotes: %v", err)
	}

	// Serve static files
	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("./static"))))

	// Main page
	http.HandleFunc("/", indexHandler)

	// API endpoints
	http.HandleFunc("/api/chapter/", chapterHandler)
	http.HandleFunc("/api/canon/", canonHandler)
	http.HandleFunc("/api/about", aboutHandler)
	http.HandleFunc("/api/homily/", homilyAPIHandler)
	http.HandleFunc("/api/search", searchHandler)
	
	// Homily page
	http.HandleFunc("/homily/", homilyHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	fmt.Printf("Server starting on http://localhost:%s (Cyril debug v15)\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	// Reload templates in development for hot reload - v5
	// Use absolute path since Air runs from tmp directory
	tmpl, err := template.ParseGlob("/Users/gregzancewicz/Documents/Other/Projects/hypomnema/hypomnema-server/templates/*.html")
	if err != nil {
		log.Printf("Template loading error from filesystem: %v", err)
		// Fallback to embedded templates
		tmpl = templates
	}
	
	// Handle direct book/chapter URLs like /matthew/1
	path := r.URL.Path
	currentBook := "matthew"
	currentChap := 1
	
	if path != "/" {
		parts := strings.Split(strings.Trim(path, "/"), "/")
		if len(parts) >= 1 {
			// Check if it's a valid book
			for _, book := range books {
				if book.ID == parts[0] {
					currentBook = parts[0]
					break
				}
			}
			
			// Get chapter if provided
			if len(parts) >= 2 {
				if chap, err := strconv.Atoi(parts[1]); err == nil {
					currentChap = chap
				}
			}
		}
	}
	
	data := struct {
		Books       []Book
		CurrentBook string
		CurrentChap int
	}{
		Books:       books,
		CurrentBook: currentBook,
		CurrentChap: currentChap,
	}

	err = tmpl.ExecuteTemplate(w, "index.html", data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	// Get search query
	query := r.URL.Query().Get("q")
	if query == "" {
		w.Write([]byte(""))
		return
	}
	
	// Convert to lowercase for case-insensitive search
	searchTerm := strings.ToLower(query)
	
	// Search results HTML
	var results strings.Builder
	results.WriteString(`<div class="search-results-list" style="max-height: 400px; overflow-y: auto; margin-top: 10px;">`)
	
	resultCount := 0
	maxResults := 20
	
	// Search through all books
	for _, book := range books {
		if resultCount >= maxResults {
			break
		}
		
		// Get book directory
		bookDir := filepath.Join("../texts/scripture/new_testament/english/kjv", book.ID)
		
		// Read all chapters for this book
		for chapter := 1; chapter <= book.Chapters; chapter++ {
			if resultCount >= maxResults {
				break
			}
			
			chapterDir := fmt.Sprintf("%02d", chapter)
			chapterFile := filepath.Join(bookDir, chapterDir, fmt.Sprintf("%s_%02d.txt", book.ID, chapter))
			
			// Read chapter file
			content, err := os.ReadFile(chapterFile)
			if err != nil {
				continue
			}
			
			// Search line by line
			lines := strings.Split(string(content), "\n")
			for _, line := range lines {
				if resultCount >= maxResults {
					break
				}
				
				// Check if line contains search term
				if strings.Contains(strings.ToLower(line), searchTerm) {
					// Parse verse reference
					parts := strings.SplitN(line, " ", 2)
					if len(parts) == 2 {
						verseRef := parts[0]
						verseText := parts[1]
						
						// Highlight search term
						highlightedText := verseText
						// Simple highlight - wrap matches in <mark> tags
						re := regexp.MustCompile("(?i)" + regexp.QuoteMeta(query))
						highlightedText = re.ReplaceAllString(highlightedText, "<mark>$0</mark>")
						
						// Truncate if too long
						if len(highlightedText) > 200 {
							highlightedText = highlightedText[:200] + "..."
						}
						
						// Create clickable result
						results.WriteString(fmt.Sprintf(`
							<div class="search-result" 
							     style="padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; transition: background-color 0.2s;"
							     onmouseover="this.style.backgroundColor='#f5f5f5'" 
							     onmouseout="this.style.backgroundColor=''"
							     hx-get="/api/chapter/%s/%d"
							     hx-target="#text-content"
							     hx-swap="innerHTML"
							     hx-push-url="/%s/%d"
							     hx-indicator="#loading-indicator">
								<div style="color: #3498db; font-weight: 500; margin-bottom: 4px; pointer-events: none;">%s %s</div>
								<div style="color: #666; font-size: 0.9em; line-height: 1.4; pointer-events: none;">%s</div>
							</div>
						`, book.ID, chapter, book.ID, chapter, book.Name, verseRef, highlightedText))
						
						resultCount++
					}
				}
			}
		}
	}
	
	if resultCount == 0 {
		results.WriteString(`<div style="padding: 10px; color: #666;">No results found for "`)
		results.WriteString(html.EscapeString(query))
		results.WriteString(`"</div>`)
	} else if resultCount >= maxResults {
		results.WriteString(fmt.Sprintf(`<div style="padding: 10px; color: #666; text-align: center;">Showing first %d results</div>`, maxResults))
	}
	
	results.WriteString(`</div>`)
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(results.String()))
}

func chapterHandler(w http.ResponseWriter, r *http.Request) {
	// Parse URL: /api/chapter/matthew/1
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/chapter/"), "/")
	if len(parts) != 2 {
		http.Error(w, "Invalid URL", http.StatusBadRequest)
		return
	}

	bookID := parts[0]
	chapter, err := strconv.Atoi(parts[1])
	if err != nil {
		http.Error(w, "Invalid chapter number", http.StatusBadRequest)
		return
	}

	// Read chapter text
	chapterStr := fmt.Sprintf("%02d", chapter)
	filePath := filepath.Join("../texts/scripture/new_testament/english/kjv", bookID, chapterStr, bookID+"_"+chapterStr+".txt")
	
	file, err := os.Open(filePath)
	if err != nil {
		http.Error(w, "Chapter not found", http.StatusNotFound)
		return
	}
	defer file.Close()

	content, err := io.ReadAll(file)
	if err != nil {
		http.Error(w, "Error reading chapter", http.StatusInternalServerError)
		return
	}

	// Get paragraph breaks for this chapter
	bookParagraphs := paragraphData[bookID]
	chapterParagraphs := []int{}
	for _, p := range bookParagraphs {
		if p.Chapter == chapter {
			chapterParagraphs = append(chapterParagraphs, p.Verse)
		}
	}

	// Get verse-to-canon mapping for this book
	bookCanons := verseToCanon[bookID]
	
	// Get homily mappings
	var homilyMap map[string][]Homily
	var cyrilHomilyMap map[string][]Homily
	if bookID == "matthew" {
		if comm, ok := commentaries["chrysostom-matthew"]; ok {
			homilyMap = comm.VerseToHomily
		}
	} else if bookID == "john" {
		if comm, ok := commentaries["chrysostom-john"]; ok {
			homilyMap = comm.VerseToHomily
		}
	} else if bookID == "luke" {
		// For Luke, we'll have both Chrysostom (from cross-references) and Cyril
		if comm, ok := commentaries["cyril-luke"]; ok {
			cyrilHomilyMap = comm.VerseToHomily
		}
	}
	
	// Format the text with paragraphs and canon numbers
	html := formatChapterHTML(string(content), chapterParagraphs, bookCanons, chapter, bookID, homilyMap, cyrilHomilyMap)
	
	// Check if this is an HTMX request
	isHTMX := r.Header.Get("HX-Request") == "true"
	
	// If it's an HTMX request, add out-of-band swaps
	if isHTMX {
		var response strings.Builder
		
		// Main content
		response.WriteString(html)
		
		// Out-of-band update for chapter title
		response.WriteString(fmt.Sprintf(`<h2 id="chapter-title" hx-swap-oob="true">Chapter %d</h2>`, chapter))
		
		// Get book display name
		bookName := bookID // default to ID
		for _, book := range books {
			if book.ID == bookID {
				bookName = book.Name
				break
			}
		}
		
		// Out-of-band update for browser title
		response.WriteString(fmt.Sprintf(`<title hx-swap-oob="true">%s %d - Hypomnema</title>`, bookName, chapter))
		
		// Find max chapters for this book
		maxChapters := 1
		for _, book := range books {
			if book.ID == bookID {
				maxChapters = book.Chapters
				break
			}
		}
		
		// Generate chapter selector out-of-band updates (both top and bottom)
		var chapterBoxes strings.Builder
		for i := 1; i <= maxChapters; i++ {
			activeClass := ""
			if i == chapter {
				activeClass = " active"
			}
			chapterBoxes.WriteString(fmt.Sprintf(`
				<div class="chapter-box%s"
				     onclick="loadChapterAndScroll('%s', %d)"
				     style="cursor: pointer;">%d</div>`,
				activeClass, bookID, i, i))
		}
		
		// Top chapter selector
		response.WriteString(`<div id="chapter-selector" class="chapter-selector" hx-ext="preload" hx-swap-oob="true">`)
		response.WriteString(chapterBoxes.String())
		response.WriteString(`</div>`)
		
		// Bottom chapter selector
		response.WriteString(`<div id="chapter-selector-bottom" class="chapter-selector" hx-ext="preload" hx-swap-oob="true">`)
		response.WriteString(chapterBoxes.String())
		response.WriteString(`</div>`)
		
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(response.String()))
	} else {
		// Regular response without OOB swaps
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte(html))
	}
}

func formatChapterHTML(text string, paragraphBreaks []int, bookCanons map[string]string, chapter int, bookID string, homilyMap map[string][]Homily, cyrilHomilyMap map[string][]Homily) string {
	lines := strings.Split(strings.TrimSpace(text), "\n")
	var html strings.Builder
	
	html.WriteString("<div class='chapter-text'>")
	
	inParagraph := false
	isFirstVerse := true
	lastCanonNum := ""
	lastHomilies := []int{} // Track homily numbers from previous verse
	
	for _, line := range lines {
		// Parse verse number and text - handle "1:1" format
		colonIndex := strings.Index(line, ":")
		if colonIndex == -1 {
			continue
		}
		
		// Extract verse number after the colon
		spaceIndex := strings.Index(line[colonIndex:], " ")
		if spaceIndex == -1 {
			continue
		}
		
		verseNumStr := line[colonIndex+1 : colonIndex+spaceIndex]
		verseNum, err := strconv.Atoi(verseNumStr)
		if err != nil {
			continue
		}
		verseText := line[colonIndex+spaceIndex+1:]
		
		// Check if this verse starts a new paragraph
		shouldStartParagraph := isFirstVerse || contains(paragraphBreaks, verseNum)
		
		if shouldStartParagraph && inParagraph {
			html.WriteString("</p>")
			inParagraph = false
		}
		
		if shouldStartParagraph {
			html.WriteString("<p>")
			inParagraph = true
		}
		
		// Check if this verse has a canon number
		verseKey := fmt.Sprintf("%d:%d", chapter, verseNum)
		canonNum := ""
		if bookCanons != nil {
			canonNum = bookCanons[verseKey]
		}
		
		// Only show canon number if it's different from the last one (new section)
		showCanon := canonNum != "" && canonNum != lastCanonNum
		if canonNum != "" {
			lastCanonNum = canonNum
		}
		
		// Add canon number if needed (before the verse)
		if showCanon {
			// canonNum is already in format "I.1", "XIII.3", etc.
			tooltip := getCanonTooltipFromKey(canonNum, bookID)
			html.WriteString(fmt.Sprintf(`<span class="canon-num" title="%s" onclick="showCanonModal('%s')">%s</span>`, tooltip, canonNum, canonNum))
		}
		
		// Check if this verse has homily references
		currentHomilies := []int{} // Track homilies for this verse
		
		if (bookID == "matthew" || bookID == "john") && homilyMap != nil {
			// Direct homily references
			verseKey := fmt.Sprintf("%d:%d", chapter, verseNum)
			if homilies, ok := homilyMap[verseKey]; ok {
				// Filter out consecutive duplicates
				var filteredHomilies []Homily
				for _, homily := range homilies {
					isDuplicate := false
					for _, lastNum := range lastHomilies {
						if homily.Number == lastNum {
							isDuplicate = true
							break
						}
					}
					if !isDuplicate {
						filteredHomilies = append(filteredHomilies, homily)
						currentHomilies = append(currentHomilies, homily.Number)
					}
				}
				
				// Only render if we have non-duplicate homilies
				if len(filteredHomilies) > 0 {
					html.WriteString(`<div class="homily-refs-container">`)
					for _, homily := range filteredHomilies {
						bookTitle := "Matthew"
						if bookID == "john" {
							bookTitle = "John"
						}
						
						// Get passage reference from coverage data
						passageRef := ""
						if comm, ok := commentaries["chrysostom-"+bookID]; ok {
							if coverage, ok := comm.Coverage[homily.Number]; ok {
								if coverage.StartChapter == coverage.EndChapter {
									if coverage.StartVerse == coverage.EndVerse {
										passageRef = fmt.Sprintf(" (%d:%d)", coverage.StartChapter, coverage.StartVerse)
									} else {
										passageRef = fmt.Sprintf(" (%d:%d-%d)", coverage.StartChapter, coverage.StartVerse, coverage.EndVerse)
									}
								} else {
									passageRef = fmt.Sprintf(" (%d:%d-%d:%d)", coverage.StartChapter, coverage.StartVerse, coverage.EndChapter, coverage.EndVerse)
								}
							}
						}
						
						html.WriteString(fmt.Sprintf(`<a href="#" onclick="loadHomily(%d, '%s', '%s'); return false;" class="homily-ref" data-full-text="John Chrysostom, Homily %s on %s%s"></a>`, 
							homily.Number, homily.Roman, bookID, homily.Roman, bookTitle, passageRef))
					}
					html.WriteString(`</div>`)
				}
			}
		} 
		
		// Check for cross-referenced homilies via canon tables
		if canonNum != "" {
			if canonData, ok := canonLookup[canonNum]; ok {
				// Get the current book's verse range from the canon
				currentBookCanonRange := ""
				if currentBookRef, ok := canonData[bookID]; ok {
					// Parse and format the current book's range for the tooltip
					startChap, startVerse, endChap, endVerse, err := parseVerseRef(currentBookRef)
					if err == nil {
						if startChap == endChap {
							if startVerse == endVerse {
								currentBookCanonRange = fmt.Sprintf("%d:%d", startChap, startVerse)
							} else {
								currentBookCanonRange = fmt.Sprintf("%d:%d-%d", startChap, startVerse, endVerse)
							}
						} else {
							currentBookCanonRange = fmt.Sprintf("%d:%d-%d:%d", startChap, startVerse, endChap, endVerse)
						}
					}
				}
				
				// Loop through all books mentioned in this canon
				for canonBook, canonRef := range canonData {
					// Skip the current book (don't show self-references)
					if canonBook == bookID {
						continue
					}
					
					// Parse the reference for this book
					startChap, startVerse, endChap, endVerse, err := parseVerseRef(canonRef)
					if err != nil {
						continue
					}
					
					// Check all available commentaries for this book
					for key := range commentaries {
						// Extract author and book from the key (format: "author-book")
						parts := strings.Split(key, "-")
						if len(parts) != 2 {
							continue
						}
						author := parts[0]
						commBook := parts[1]
						
						// Check if this commentary is for the canon's book
						if commBook == canonBook {
							// Find homilies that cover this passage
							homilies := findHomiliesForRange(author, commBook, startChap, startVerse, endChap, endVerse)
							if len(homilies) > 0 {
								renderedHTML, newHomilies := renderHomilyRefs(homilies, author, commBook, true, currentBookCanonRange, lastHomilies)
								html.WriteString(renderedHTML)
								currentHomilies = append(currentHomilies, newHomilies...)
							}
						}
					}
				}
			}
		}
		
		// Add Cyril's commentary for Luke
		if bookID == "luke" && cyrilHomilyMap != nil {
			verseKey := fmt.Sprintf("%d:%d", chapter, verseNum)
			if cyrilHomilies, ok := cyrilHomilyMap[verseKey]; ok {
				// Filter out consecutive duplicates
				var filteredCyrilHomilies []Homily
				for _, homily := range cyrilHomilies {
					isDuplicate := false
					for _, lastNum := range lastHomilies {
						// Use negative numbers to distinguish Cyril's homilies from Chrysostom's
						if homily.Number == -lastNum {
							isDuplicate = true
							break
						}
					}
					if !isDuplicate {
						filteredCyrilHomilies = append(filteredCyrilHomilies, homily)
						currentHomilies = append(currentHomilies, -homily.Number) // Store as negative to distinguish
					}
				}
				
				// Render Cyril's homilies
				if len(filteredCyrilHomilies) > 0 {
					html.WriteString(`<div class="homily-refs-container cyril">`)
					for _, homily := range filteredCyrilHomilies {
						// Get passage reference from coverage data
						passageRef := ""
						if comm, ok := commentaries["cyril-luke"]; ok {
							if coverage, ok := comm.Coverage[homily.Number]; ok {
								if coverage.StartChapter == coverage.EndChapter {
									if coverage.StartVerse == coverage.EndVerse {
										passageRef = fmt.Sprintf(" (%d:%d)", coverage.StartChapter, coverage.StartVerse)
									} else {
										passageRef = fmt.Sprintf(" (%d:%d-%d)", coverage.StartChapter, coverage.StartVerse, coverage.EndVerse)
									}
								} else {
									passageRef = fmt.Sprintf(" (%d:%d-%d:%d)", coverage.StartChapter, coverage.StartVerse, coverage.EndChapter, coverage.EndVerse)
								}
							}
						}
						
						html.WriteString(fmt.Sprintf(`<a href="#" onclick="loadCyrilHomily(%d, '%s', 'luke'); return false;" class="homily-ref cyril" data-full-text="Cyril of Alexandria, Sermon %s on Luke%s"></a>`, 
							homily.Number, homily.Roman, homily.Roman, passageRef))
					}
					html.WriteString(`</div>`)
				}
			}
		}
		
		// Update lastHomilies for next verse
		lastHomilies = currentHomilies
		
		// Add verse with superscript number and ID for anchor links
		html.WriteString(fmt.Sprintf(`<span class="verse" id="verse-%d"><sup class="verse-num">%d</sup>%s </span>`, verseNum, verseNum, verseText))
		
		isFirstVerse = false
	}
	
	if inParagraph {
		html.WriteString("</p>")
	}
	
	html.WriteString("</div>")
	return html.String()
}

// renderHomilyRefs generates HTML for homily references
// If isCrossRef is true and canonVerseRange is provided, it will use that range in the tooltip
func renderHomilyRefs(homilies []Homily, author, book string, isCrossRef bool, canonVerseRange string, lastHomilies []int) (string, []int) {
	var html strings.Builder
	var currentHomilies []int
	
	// Filter out consecutive duplicates
	var filteredHomilies []Homily
	for _, homily := range homilies {
		isDuplicate := false
		for _, lastNum := range lastHomilies {
			// For Cyril, use negative numbers to distinguish from Chrysostom
			compareNum := homily.Number
			if author == "cyril" {
				compareNum = -homily.Number
			}
			if compareNum == lastNum {
				isDuplicate = true
				break
			}
		}
		if !isDuplicate {
			filteredHomilies = append(filteredHomilies, homily)
			if author == "cyril" {
				currentHomilies = append(currentHomilies, -homily.Number)
			} else {
				currentHomilies = append(currentHomilies, homily.Number)
			}
		}
	}
	
	// Only render if we have non-duplicate homilies
	if len(filteredHomilies) > 0 {
		className := "homily-refs-container"
		refClass := "homily-ref"
		if isCrossRef {
			className += " cross-ref"
			refClass += " cross-ref"
		}
		if author == "cyril" {
			className += " cyril"
			refClass += " cyril"
		}
		
		html.WriteString(fmt.Sprintf(`<div class="%s">`, className))
		for _, homily := range filteredHomilies {
			var onclick, fullText string
			
			// Determine the verse range to show in the tooltip
			passageRef := ""
			if isCrossRef && canonVerseRange != "" {
				// For cross-references, use the canon's verse range from the current book
				passageRef = fmt.Sprintf(" (%s)", canonVerseRange)
			} else {
				// For direct references, get the homily's actual coverage
				commKey := fmt.Sprintf("%s-%s", author, book)
				if comm, ok := commentaries[commKey]; ok {
					if coverage, ok := comm.Coverage[homily.Number]; ok {
						if coverage.StartChapter == coverage.EndChapter {
							if coverage.StartVerse == coverage.EndVerse {
								passageRef = fmt.Sprintf(" (%d:%d)", coverage.StartChapter, coverage.StartVerse)
							} else {
								passageRef = fmt.Sprintf(" (%d:%d-%d)", coverage.StartChapter, coverage.StartVerse, coverage.EndVerse)
							}
						} else {
							passageRef = fmt.Sprintf(" (%d:%d-%d:%d)", coverage.StartChapter, coverage.StartVerse, coverage.EndChapter, coverage.EndVerse)
						}
					}
				}
			}
			
			if author == "cyril" {
				onclick = fmt.Sprintf(`loadCyrilHomily(%d, '%s', '%s')`, homily.Number, homily.Roman, book)
				fullText = fmt.Sprintf("Cyril of Alexandria, Sermon %s on Luke%s", homily.Roman, passageRef)
			} else {
				onclick = fmt.Sprintf(`loadHomily(%d, '%s', '%s')`, homily.Number, homily.Roman, book)
				bookTitle := "Matthew"
				if book == "john" {
					bookTitle = "John"
				}
				fullText = fmt.Sprintf("John Chrysostom, Homily %s on %s%s", homily.Roman, bookTitle, passageRef)
			}
			
			html.WriteString(fmt.Sprintf(`<a href="#" onclick="%s; return false;" class="%s" data-full-text="%s"></a>`,
				onclick, refClass, fullText))
		}
		html.WriteString(`</div>`)
	}
	
	return html.String(), currentHomilies
}

func contains(slice []int, val int) bool {
	for _, v := range slice {
		if v == val {
			return true
		}
	}
	return false
}

func getCanonTooltipFromKey(canonKey string, currentBook string) string {
	gospelAbbr := map[string]string{
		"matthew": "Mt",
		"mark": "Mk", 
		"luke": "Lk",
		"john": "Jn",
	}
	
	// canonKey is already in format "I.1", "XIII.3", etc.
	if passages, ok := canonLookup[canonKey]; ok {
		// Build list of passages, with current book first
		var result []string
		
		// Add current book first if present
		if verses, ok := passages[currentBook]; ok {
			result = append(result, fmt.Sprintf("%s %s", gospelAbbr[currentBook], verses))
		}
		
		// Then add other gospels in canonical order
		gospelOrder := []string{"matthew", "mark", "luke", "john"}
		for _, g := range gospelOrder {
			if g == currentBook {
				continue // Skip current book as we already added it
			}
			if verses, ok := passages[g]; ok {
				result = append(result, fmt.Sprintf("%s %s", gospelAbbr[g], verses))
			}
		}
		
		if len(result) > 0 {
			return strings.Join(result, "; ")
		}
	}
	
	// Fallback - shouldn't happen with complete data
	return fmt.Sprintf("Canon %s", canonKey)
}

func canonHandler(w http.ResponseWriter, r *http.Request) {
	// Parse URL: /api/canon/I.1
	canonKey := strings.TrimPrefix(r.URL.Path, "/api/canon/")
	if canonKey == "" {
		http.Error(w, "Canon key required", http.StatusBadRequest)
		return
	}
	
	// Look up the canon entry
	passages, ok := canonLookup[canonKey]
	if !ok {
		http.Error(w, "Canon not found", http.StatusNotFound)
		return
	}
	
	gospelAbbr := map[string]string{
		"matthew": "Mt",
		"mark": "Mk", 
		"luke": "Lk",
		"john": "Jn",
	}
	
	var html strings.Builder
	html.WriteString("<div class='canon-passages'>")
	
	// Order: Mt, Mk, Lk, Jn
	gospelOrder := []string{"matthew", "mark", "luke", "john"}
	for _, gospel := range gospelOrder {
		if verses, ok := passages[gospel]; ok {
			html.WriteString(fmt.Sprintf("<div class='passage'>"))
			html.WriteString(fmt.Sprintf("<h3>%s %s</h3>", gospelAbbr[gospel], verses))
			
			// Load the actual verse text
			verseText := loadVerseText(gospel, verses)
			if verseText != "" {
				html.WriteString(fmt.Sprintf("<p class='verse-text'>%s</p>", verseText))
			} else {
				html.WriteString("<p class='verse-text'><em>Text not available</em></p>")
			}
			html.WriteString("</div>")
		}
	}
	
	html.WriteString("</div>")
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html.String()))
}

func loadVerseText(gospel string, verseRef string) string {
	// Parse verse reference like "3.3" or "1.19-22"
	// For now, we'll implement a basic version that loads the first verse
	// This could be expanded to handle ranges properly
	
	// Extract chapter and verse
	parts := strings.Split(verseRef, ".")
	if len(parts) != 2 {
		return ""
	}
	
	chapter := parts[0]
	versePart := parts[1]
	
	// Handle ranges like "19-22" - just take the first verse for now
	if strings.Contains(versePart, "-") {
		versePart = strings.Split(versePart, "-")[0]
	}
	
	// Remove any letter suffixes like "A", "B"
	re := regexp.MustCompile(`[A-Z]+$`)
	versePart = re.ReplaceAllString(versePart, "")
	
	// Load the chapter file
	chapterNum, err := strconv.Atoi(chapter)
	if err != nil {
		return ""
	}
	
	chapterStr := fmt.Sprintf("%02d", chapterNum)
	filePath := filepath.Join("../texts/scripture/new_testament/english/kjv", gospel, chapterStr, gospel+"_"+chapterStr+".txt")
	
	file, err := os.Open(filePath)
	if err != nil {
		return ""
	}
	defer file.Close()
	
	content, err := io.ReadAll(file)
	if err != nil {
		return ""
	}
	
	// Find the verse
	lines := strings.Split(string(content), "\n")
	for _, line := range lines {
		if strings.HasPrefix(line, chapter+":"+versePart+" ") {
			// Extract just the text part
			spaceIndex := strings.Index(line, " ")
			if spaceIndex != -1 {
				return line[spaceIndex+1:]
			}
		}
	}
	
	return ""
}

func homilyHandler(w http.ResponseWriter, r *http.Request) {
	// Parse URL: /homily/chrysostom/matthew/1 or /homily/cyril/luke/1
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/homily/"), "/")
	if len(parts) != 3 {
		http.Error(w, "Invalid URL", http.StatusBadRequest)
		return
	}
	
	author := parts[0]
	book := parts[1]
	homilyNumStr := parts[2]
	
	if author == "chrysostom" && (book != "matthew" && book != "john") {
		http.Error(w, "Homily not found", http.StatusNotFound)
		return
	}
	if author == "cyril" && book != "luke" {
		http.Error(w, "Homily not found", http.StatusNotFound)
		return
	}
	if author != "chrysostom" && author != "cyril" {
		http.Error(w, "Author not found", http.StatusNotFound)
		return
	}
	
	homilyNum, err := strconv.Atoi(homilyNumStr)
	if err != nil {
		http.Error(w, "Invalid homily number", http.StatusBadRequest)
		return
	}
	
	// Convert to roman numeral
	roman := intToRoman(homilyNum)
	
	var homilyText, verseRef string
	var authorName string
	
	if author == "chrysostom" {
		// Extract homily text from XML
		homilyText, verseRef, err = extractHomilyFromXML(book, homilyNum)
		if err != nil {
			log.Printf("Error extracting %s homily %d: %v", book, homilyNum, err)
			homilyText = "Error loading homily text."
		}
		authorName = "John Chrysostom"
	} else if author == "cyril" {
		// Extract sermon text from HTML
		homilyText, verseRef, err = extractCyrilSermonFromHTML(homilyNum)
		if err != nil {
			log.Printf("Error extracting Cyril sermon %d: %v", homilyNum, err)
			homilyText = "Error loading sermon text."
		}
		authorName = "Cyril of Alexandria"
	}
	
	// Clean up verse reference - don't show if it contains "Homily" or is just a title
	if strings.Contains(verseRef, "Homily") || strings.Contains(verseRef, "Sermon") || verseRef == "Introduction" || verseRef == "" {
		verseRef = ""
	}
	
	data := struct {
		Author      string
		Book        string
		HomilyNum   int
		HomilyRoman string
		HomilyText  template.HTML
		VerseRef    string
	}{
		Author:      authorName,
		Book:        strings.Title(book),
		HomilyNum:   homilyNum,
		HomilyRoman: roman,
		HomilyText:  template.HTML(homilyText),
		VerseRef:    verseRef,
	}
	
	err = templates.ExecuteTemplate(w, "homily.html", data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func intToRoman(num int) string {
	values := []int{1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1}
	symbols := []string{"M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"}
	
	result := ""
	for i := 0; i < len(values); i++ {
		for num >= values[i] {
			num -= values[i]
			result += symbols[i]
		}
	}
	return result
}

// Footnote represents a footnote with its content

// FootnoteData represents the structure of footnotes.json
type FootnoteData struct {
	RomanNumeral string `json:"roman_numeral"`
	Footnotes    []struct {
		OriginalNumber int    `json:"original_number"`
		DisplayNumber  int    `json:"display_number"`
		Content        string `json:"content"`
	} `json:"footnotes"`
}

// Global variable to store footnotes
var matthewFootnotesData map[string]FootnoteData
var johnFootnotesData map[string]FootnoteData
var cyrilLukeFootnotesData map[string]FootnoteData

// Load footnotes from JSON file
func loadFootnotes() error {
	// Load Matthew footnotes
	matthewData, err := os.ReadFile("../texts/commentaries/chrysostom/matthew/footnotes.json")
	if err != nil {
		return err
	}
	
	matthewFootnotesData = make(map[string]FootnoteData)
	err = json.Unmarshal(matthewData, &matthewFootnotesData)
	if err != nil {
		return err
	}
	
	// Load John footnotes
	johnData, err := os.ReadFile("../texts/commentaries/chrysostom/john/footnotes.json")
	if err != nil {
		return err
	}
	
	johnFootnotesData = make(map[string]FootnoteData)
	err = json.Unmarshal(johnData, &johnFootnotesData)
	if err != nil {
		return err
	}
	
	// Load Cyril Luke footnotes
	cyrilData, err := os.ReadFile("../texts/commentaries/cyril/luke/footnotes.json")
	if err != nil {
		// Log but don't fail
		log.Printf("Warning: Could not load Cyril Luke footnotes: %v", err)
		cyrilLukeFootnotesData = make(map[string]FootnoteData)
	} else {
		var cyrilFootnotes map[string]struct {
			File   string `json:"file"`
			Number int    `json:"number"`
			Text   string `json:"text"`
		}
		err = json.Unmarshal(cyrilData, &cyrilFootnotes)
		if err != nil {
			log.Printf("Warning: Could not parse Cyril Luke footnotes: %v", err)
			cyrilLukeFootnotesData = make(map[string]FootnoteData)
		} else {
			// Convert Cyril footnotes to FootnoteData format
			cyrilLukeFootnotesData = make(map[string]FootnoteData)
			// Group footnotes by sermon number
			sermonFootnotes := make(map[int][]Footnote)
			for _, fn := range cyrilFootnotes {
				// Extract sermon number from filename
				var sermonNum int
				if _, err := fmt.Sscanf(fn.File, "cyril_on_luke_%d_sermons_", &sermonNum); err == nil {
					// Map file numbers to actual sermon numbers
					switch sermonNum {
					case 1: // File 01 contains sermons 1-11
						if fn.Number >= 1 && fn.Number <= 50 {
							// Approximate - need better mapping
							sermonFootnotes[1] = append(sermonFootnotes[1], Footnote{
								Number: strconv.Itoa(fn.Number),
								Content: fn.Text,
							})
						}
					}
				}
			}
			// Convert to FootnoteData format
			for sermonNum, footnotes := range sermonFootnotes {
				// Convert []Footnote to the expected structure
				var convertedFootnotes []struct {
					OriginalNumber int    `json:"original_number"`
					DisplayNumber  int    `json:"display_number"`
					Content        string `json:"content"`
				}
				
				for i, fn := range footnotes {
					noteNum, _ := strconv.Atoi(fn.Number)
					convertedFootnotes = append(convertedFootnotes, struct {
						OriginalNumber int    `json:"original_number"`
						DisplayNumber  int    `json:"display_number"`
						Content        string `json:"content"`
					}{
						OriginalNumber: noteNum,
						DisplayNumber:  i + 1,
						Content:        fn.Content,
					})
				}
				
				cyrilLukeFootnotesData[strconv.Itoa(sermonNum)] = FootnoteData{
					RomanNumeral: intToRoman(sermonNum),
					Footnotes:    convertedFootnotes,
				}
			}
		}
	}
	
	log.Printf("Loaded footnotes for %d Matthew homilies and %d John homilies", 
		len(matthewFootnotesData), len(johnFootnotesData))
	return nil
}

func extractHomilyFromXML(book string, homilyNum int) (string, string, error) {
	// Read the XML file
	xmlPath := fmt.Sprintf("../texts/commentaries/chrysostom/%s/chrysostom_%s_homilies.xml", book, book)
	content, err := os.ReadFile(xmlPath)
	if err != nil {
		return "", "", err
	}
	
	// Convert content to string for regex processing
	xmlContent := string(content)
	
	// Look for the specific homily using its roman numeral
	roman := intToRoman(homilyNum)
	
	// Pattern to find the homily div2
	// For John, we need to ensure we're getting John homilies, not Hebrews
	var pattern string
	var match string
	
	if book == "john" {
		// For John, we need a different approach because most homilies don't have n= attribute
		// Find all div2 homilies that are NOT Hebrews
		allHomiliesPattern := `(?s)<div2[^>]*type="Homily"[^>]*>.*?</div2>`
		allRe := regexp.MustCompile(allHomiliesPattern)
		allMatches := allRe.FindAllString(xmlContent, -1)
		
		// Filter to only John homilies (exclude Hebrews) and find the nth one
		johnHomilies := []string{}
		for _, m := range allMatches {
			if !strings.Contains(m, `title="Hebrews`) {
				johnHomilies = append(johnHomilies, m)
			}
		}
		
		// Get the homily by number (1-based index)
		if homilyNum > 0 && homilyNum <= len(johnHomilies) {
			match = johnHomilies[homilyNum-1]
		} else {
			return "", "", fmt.Errorf("John homily %d not found (only %d homilies available)", homilyNum, len(johnHomilies))
		}
	} else {
		// For Matthew, simpler pattern using Roman numerals
		pattern = fmt.Sprintf(`(?s)<div2[^>]*n="%s"[^>]*>.*?</div2>`, roman)
		re := regexp.MustCompile(pattern)
		match = re.FindString(xmlContent)
	}
	
	if match == "" {
		// Try alternative pattern for homilies without div2
		// Look for "Homily [Roman]." pattern
		altPattern := fmt.Sprintf(`(?s)Homily %s\.</span></p>.*?(?=Homily [IVX]+\.|</body>)`, roman)
		altRe := regexp.MustCompile(altPattern)
		match = altRe.FindString(xmlContent)
		
		if match == "" {
			return "", "", fmt.Errorf("homily %s not found", roman)
		}
	}
	
	// Extract verse reference
	verseRef := ""
	versePattern := `title="([^"]+)"`
	verseRe := regexp.MustCompile(versePattern)
	if verseMatch := verseRe.FindStringSubmatch(match); len(verseMatch) > 1 {
		verseRef = verseMatch[1]
	}
	
	// Clean up the text
	text := match
	
	// Debug logging for John Homily I
	if book == "john" && homilyNum == 1 {
		// Check if the text contains [1.]
		if strings.Contains(text, "[1.]") {
			log.Printf("DEBUG: Raw extracted text contains [1.]")
			idx := strings.Index(text, "[1.]")
			if idx > 0 && idx < len(text)-100 {
				log.Printf("DEBUG: Text around [1.]: %q", text[idx-20:idx+80])
			}
		} else {
			log.Printf("DEBUG: Raw extracted text does NOT contain [1.]")
			// Check for "They that are"
			if idx := strings.Index(text, "They that are"); idx >= 0 && idx < 1000 {
				log.Printf("DEBUG: Found 'They that are' at position %d", idx)
			}
		}
	}
	
	// Get footnotes from preloaded data
	var footnotesData AllFootnotes
	if book == "matthew" {
		footnotesData = chrysostomMatthewFootnotes
	} else if book == "john" {
		footnotesData = chrysostomJohnFootnotes
	}
	
	homilyFootnotes, hasFootnotes := footnotesData[strconv.Itoa(homilyNum)]
	var footnotes []Footnote
	footnoteMap := make(map[string]int)
	
	if hasFootnotes {
		for _, fn := range homilyFootnotes {
			footnotes = append(footnotes, Footnote{
				Number:  strconv.Itoa(fn.DisplayNumber),
				Content: fn.Content,
			})
			// Map original number to display number
			footnoteMap[fn.OriginalNumber] = fn.DisplayNumber
		}
	}
	
	// Replace footnote tags with superscript markers
	// Process note tags and remove scripRef tags within them
	notePattern := regexp.MustCompile(`(?s)<note\s+n="([^"]+)"[^>]*>.*?</note>`)
	text = notePattern.ReplaceAllStringFunc(text, func(match string) string {
		// First, remove any scripRef tags within this note to prevent orphaned content
		scripRefPattern := regexp.MustCompile(`<scripRef[^>]*>([^<]*)</scripRef>`)
		_ = scripRefPattern.ReplaceAllString(match, "") // cleanMatch not used
		
		// Extract note number from the original match (not the cleaned one)
		if m := notePattern.FindStringSubmatch(match); len(m) > 1 {
			originalNum := m[1]
			// Use the mapped sequential number
			if newNum, ok := footnoteMap[originalNum]; ok {
				// Check if the note tag is followed by a letter (needs space)
				needsSpace := ""
				afterNote := strings.Index(text, match)
				if afterNote != -1 && afterNote+len(match) < len(text) {
					nextChar := text[afterNote+len(match)]
					if (nextChar >= 'a' && nextChar <= 'z') || (nextChar >= 'A' && nextChar <= 'Z') {
						needsSpace = " "
					}
				}
				// Get the footnote content for the tooltip
				tooltipContent := ""
				for _, fn := range footnotes {
					if fn.Number == strconv.Itoa(newNum) {
						tooltipContent = fn.Content
						break
					}
				}
				
				
				// Escape quotes for HTML attribute
				tooltipContent = strings.ReplaceAll(tooltipContent, `"`, `&quot;`)
				tooltipContent = strings.ReplaceAll(tooltipContent, `<`, `&lt;`)
				tooltipContent = strings.ReplaceAll(tooltipContent, `>`, `&gt;`)
				
				// Use data-tooltip instead of title to avoid browser's default tooltip
				// Note: Using DATATOOLTIPATR placeholder to prevent hyphen replacement issues
				return fmt.Sprintf(`<sup class="XXXFOOTNOTEREFXXX" DATATOOLTIPATR="%s">%d</sup>%s`, 
					tooltipContent, newNum, needsSpace)
			}
		}
		// If we can't match/map the footnote, still remove the note tag to avoid displaying raw content
		return ""
	})
	
	// Remove any remaining scripRef tags that weren't inside notes
	scripRefPattern := regexp.MustCompile(`<scripRef[^>]*>([^<]*)</scripRef>`)
	text = scripRefPattern.ReplaceAllString(text, "")
	
	// Fix footnote placement according to Chicago Manual of Style
	// Move footnotes after punctuation marks
	punctuationPattern := regexp.MustCompile(`(<sup class="footnote-ref"[^>]*>.*?</sup>)([.,;:!?]+)`)
	text = punctuationPattern.ReplaceAllString(text, "$2$1")
	
	// Remove spaces before footnotes ONLY when they follow punctuation
	// This preserves the space after regular words
	text = regexp.MustCompile(`([.,;:!?])\s+(<sup class="footnote-ref")`).ReplaceAllString(text, "$1$2")
	
	// Remove the redundant header (appears in various formats)
	// This header appears before the actual homily content
	// Using multiple patterns to catch different formatting
	if book == "matthew" {
		text = regexp.MustCompile(`(?si)Homilies\s+of\s+St\.\s*John\s+Chrysostom[^.]*?gospel\s+according\s+to\s+st\.\s*matthew\.`).ReplaceAllString(text, "")
		text = regexp.MustCompile(`(?s)Homilies of St\. John Chrysostom.*?matthew\.`).ReplaceAllString(text, "")
		text = regexp.MustCompile(`(?s)on the\s*gospel according to st\. matthew\.`).ReplaceAllString(text, "")
	} else if book == "john" {
		// Remove John-specific headers
		text = regexp.MustCompile(`(?si)Homilies\s+of\s+St\.\s*John\s+Chrysostom[^.]*?gospel\s+according\s+to\s+st\.\s*john\.`).ReplaceAllString(text, "")
		text = regexp.MustCompile(`(?s)Homilies of St\. John Chrysostom.*?john\.`).ReplaceAllString(text, "")
		text = regexp.MustCompile(`(?s)on the\s*gospel according to st\. john\.`).ReplaceAllString(text, "")
		
		// Remove "gospel according to" and "st. john." that may appear on separate lines
		text = regexp.MustCompile(`(?si)gospel\s+according\s+to\s*(?:<[^>]+>)*\s*st\.\s*john\.`).ReplaceAllString(text, "")
		
		// Remove standalone fragments
		text = regexp.MustCompile(`(?si)gospel\s+according\s+to\s*$`).ReplaceAllString(text, "")
		text = regexp.MustCompile(`(?si)^\s*st\.\s*john\.`).ReplaceAllString(text, "")
		
		// Remove "Preface." header with various formatting
		text = regexp.MustCompile(`(?si)(?:<[^>]+>)*\s*Preface\.\s*(?:<[^>]+>)*`).ReplaceAllString(text, "")
	}
	
	// Remove any lingering header fragments
	text = regexp.MustCompile(`(?s)archbishop of constantinople,`).ReplaceAllString(text, "")
	
	// Remove multiple dashes that might appear after header removal
	text = regexp.MustCompile(`(?s)[-—]+\s*`).ReplaceAllString(text, "")
	
	// Remove "Homily [Roman]." patterns with various formatting
	// This handles cases like <span>Homily III.</span> inside paragraph tags
	homilyStartPattern := fmt.Sprintf(`(?si)<p[^>]*>\s*<span[^>]*>\s*Homily\s+%s\.\s*</span>\s*</p>`, roman)
	if book == "john" && homilyNum == 1 {
		log.Printf("DEBUG: Before first pattern removal, looking for: %s", homilyStartPattern)
		if strings.Contains(text, "Homily I.") {
			log.Printf("DEBUG: Text contains 'Homily I.'")
		}
	}
	text = regexp.MustCompile(homilyStartPattern).ReplaceAllString(text, "")
	
	// Also remove standalone pattern with word boundaries
	// For John Homily I (Preface), skip this to avoid removing "I" from content
	if !(book == "john" && homilyNum == 1) {
		homilyStartPattern2 := fmt.Sprintf(`\bHomily %s\.`, roman)
		text = regexp.MustCompile(homilyStartPattern2).ReplaceAllString(text, "")
	}
	
	// Remove the quoted verse text that often appears after the homily title
	// Pattern: paragraph containing quoted text in quotes
	quotedVersePattern := `(?si)<p[^>]*>\s*"[^"]+"\s*</p>`
	text = regexp.MustCompile(quotedVersePattern).ReplaceAllString(text, "")
	
	// Clean up any remaining "Homily [Roman]." text that wasn't inside complete paragraph tags
	// For John Homily I (Preface), skip this step to avoid removing "I" from content
	if !(book == "john" && homilyNum == 1) {
		homilySimplePattern := fmt.Sprintf(`\bHomily\s+%s\.`, roman)
		text = regexp.MustCompile(homilySimplePattern).ReplaceAllString(text, "")
	}
	if book == "john" && homilyNum == 1 {
		log.Printf("DEBUG: After removing pattern, text length %d", len(text))
		// Check if text starts with expected content
		if len(text) > 500 {
			// Find where actual content starts (after tags)
			plainTextStart := strings.Index(text, "the heathen")
			if plainTextStart > 0 && plainTextStart < 200 {
				preview := text[plainTextStart-10:plainTextStart+50]
				log.Printf("DEBUG: Text around 'the heathen': %q", preview)
			}
		}
	}
	
	// Also remove arabic numeral format
	verseStartPattern2 := `(?s)^[\s\p{Z}]*(?:Matt\.|Matthew)\s+\d+[:.]\s*\d+(?:\s*,\s*\d+)?\.?`
	text = regexp.MustCompile(verseStartPattern2).ReplaceAllString(text, "")
	
	// Also remove just remaining verse fragments like ", 5."
	verseFragmentPattern := `(?s)^[\s\p{Z}]*,\s*\d+\.?`
	text = regexp.MustCompile(verseFragmentPattern).ReplaceAllString(text, "")
	
	// Later we'll remove remaining XML tags but we need to process structured removals first
	
	// Also remove scripCom tags which contain scripture commentary metadata
	scripComPattern := regexp.MustCompile(`<scripCom[^>]*/>`)
	text = scripComPattern.ReplaceAllString(text, "")
	
	// Handle page breaks - first check if they split a word
	// Pattern: word fragment, optional whitespace/newline, <pb>, optional whitespace/newline, word fragment
	splitWordPattern := regexp.MustCompile(`(?s)(\w+)\s*\n*\s*<pb[^>]*>\s*\n*\s*(\w+)`)
	text = splitWordPattern.ReplaceAllString(text, "$1$2")
	
	// Then replace any remaining page break tags with a space
	text = regexp.MustCompile(`(?s)<pb[^>]*>`).ReplaceAllString(text, " ")
	
	// Remove XML tags but keep paragraph breaks
	text = regexp.MustCompile(`<p[^>]*>`).ReplaceAllString(text, "<p>")
	text = regexp.MustCompile(`</p>`).ReplaceAllString(text, "</p>\n")
	text = regexp.MustCompile(`<span[^>]*>`).ReplaceAllString(text, "")
	text = regexp.MustCompile(`</span>`).ReplaceAllString(text, "")
	text = regexp.MustCompile(`<div[^>]*>`).ReplaceAllString(text, "")
	text = regexp.MustCompile(`</div[^>]*>`).ReplaceAllString(text, "")
	
	// Remove any remaining XML tags except p tags, sup tags, and a tags
	// First, temporarily replace tags we want to keep with placeholders
	text = strings.ReplaceAll(text, "<p>", "{{P_OPEN}}")
	text = strings.ReplaceAll(text, "</p>", "{{P_CLOSE}}")
	// Preserve sup tags with their attributes (handle both with and without space)
	text = regexp.MustCompile(`<sup(\s+[^>]+)?>`).ReplaceAllString(text, "{{SUP_OPEN$1}}")
	text = strings.ReplaceAll(text, "</sup>", "{{SUP_CLOSE}}")
	// Preserve anchor tags with their attributes
	text = regexp.MustCompile(`<a\s+([^>]+)>`).ReplaceAllString(text, "{{A_OPEN:$1}}")
	text = strings.ReplaceAll(text, "</a>", "{{A_CLOSE}}")
	// Remove all remaining tags
	text = regexp.MustCompile(`<[^>]+>`).ReplaceAllString(text, "")
	
	// Debug for John Homily I - check after tag removal
	if book == "john" && homilyNum == 1 {
		if strings.Contains(text, "[1.]") {
			log.Printf("DEBUG: After tag removal, text still contains [1.]")
		} else {
			log.Printf("DEBUG: After tag removal, [1.] is GONE")
			// Check what's at the beginning
			if len(text) > 100 {
				log.Printf("DEBUG: First 100 chars after tag removal: %q", text[:100])
			}
		}
	}
	
	// Restore preserved tags
	text = strings.ReplaceAll(text, "{{P_OPEN}}", "<p>")
	text = strings.ReplaceAll(text, "{{P_CLOSE}}", "</p>")
	text = regexp.MustCompile(`{{SUP_OPEN([^}]*)}}`).ReplaceAllString(text, "<sup$1>")
	text = strings.ReplaceAll(text, "{{SUP_CLOSE}}", "</sup>")
	text = regexp.MustCompile(`{{A_OPEN:([^}]+)}}`).ReplaceAllString(text, "<a $1>")
	text = strings.ReplaceAll(text, "{{A_CLOSE}}", "</a>")
	
	// After all tag processing, remove any biblical references at the beginning of the text
	// This needs to happen AFTER tag removal so we're working with plain text
	if book == "matthew" {
		// Handle Matthew references like "Matt. I. 1." or "Matthew 1:1" or "Matt. II. 4, 5."
		verseStartPattern := `(?s)^[\s\p{Z}]*(?:Matt\.|Matthew)\s+[IVX]+\.\s*\d+(?:\s*,\s*\d+)?\.?\s*`
		text = regexp.MustCompile(verseStartPattern).ReplaceAllString(text, "")
	} else if book == "john" {
		// Special handling for John Homily I (Preface) - it doesn't have verse references to remove
		if homilyNum != 1 {
			// Remove ANY biblical reference at the beginning
			// Pattern for book name with Roman numerals (e.g., "Hebrews i. 3")
			verseStartPattern := `(?si)^[\s\p{Z}]*[A-Za-z]+\s+[ivxIVX]+\.\s*\d+(?:\s*[,-]\s*\d+)?\.?\s*`
			text = regexp.MustCompile(verseStartPattern).ReplaceAllString(text, "")
			
			// Pattern for book name with Arabic numerals (e.g., "John 1:1")
			verseStartPattern2 := `(?si)^[\s\p{Z}]*[A-Za-z]+\s+\d+[:\.] ?\d+(?:\s*[,-]\s*\d+)?\.?\s*`
			text = regexp.MustCompile(verseStartPattern2).ReplaceAllString(text, "")
		}
	}
	
	// Clean up extra whitespace
	text = regexp.MustCompile(`\s+`).ReplaceAllString(text, " ")
	text = regexp.MustCompile(`>\s+<`).ReplaceAllString(text, "><")
	
	// Ensure space after punctuation marks if missing
	// Add space after period, comma, semicolon, colon, exclamation, question mark if followed by a letter
	text = regexp.MustCompile(`([.,:;!?])([A-Za-z])`).ReplaceAllString(text, "$1 $2")
	
	text = strings.TrimSpace(text)
	
	// Ensure paragraphs are properly formatted
	paragraphs := strings.Split(text, "</p>")
	var cleanedParagraphs []string
	for _, p := range paragraphs {
		p = strings.TrimSpace(p)
		p = strings.TrimPrefix(p, "<p>")
		if p != "" {
			cleanedParagraphs = append(cleanedParagraphs, "<p>"+p+"</p>")
		}
	}
	
	text = strings.Join(cleanedParagraphs, "\n")
	
	// Final cleanup: if the text still starts with header fragments, remove them
	text = strings.TrimSpace(text)
	headerLines := []string{
		"Homilies of St. John Chrysostom",
		"archbishop of constantinople", 
		"on the",
		"gospel according to st. matthew",
	}
	
	// Check if text starts with any header lines and remove them
	lines := strings.Split(text, "\n")
	startIdx := 0
	for i, line := range lines {
		cleanLine := strings.TrimSpace(strings.TrimSuffix(line, "."))
		cleanLine = strings.TrimSuffix(cleanLine, ",")
		isHeader := false
		for _, header := range headerLines {
			if strings.Contains(strings.ToLower(cleanLine), strings.ToLower(header)) {
				isHeader = true
				break
			}
		}
		if !isHeader && cleanLine != "" && !strings.HasPrefix(cleanLine, "—") && !strings.HasPrefix(cleanLine, "-") {
			startIdx = i
			break
		}
	}
	
	if startIdx > 0 {
		text = strings.Join(lines[startIdx:], "\n")
	}
	
	// Final check: remove verse reference at the very beginning if it still exists
	text = strings.TrimSpace(text)
	// Remove patterns like "Matt. I. 1." or "Matthew 1:1" or ", 5." at the start
	if strings.HasPrefix(text, "<p>") {
		// Check within the first paragraph tag
		firstP := regexp.MustCompile(`^<p>[\s\p{Z}]*(?:Matt\.|Matthew)\s+[IVX]+\.\s*\d+(?:\s*,\s*\d+)?\.?[\s\p{Z}]*`).ReplaceAllString(text, "<p>")
		text = firstP
		firstP2 := regexp.MustCompile(`^<p>[\s\p{Z}]*(?:Matt\.|Matthew)\s+\d+[:.]\s*\d+(?:\s*,\s*\d+)?\.?[\s\p{Z}]*`).ReplaceAllString(text, "<p>")
		text = firstP2
		// Also check for verse fragments
		firstP3 := regexp.MustCompile(`^<p>[\s\p{Z}]*,\s*\d+\.?[\s\p{Z}]*`).ReplaceAllString(text, "<p>")
		text = firstP3
	}
	
	// Append footnotes section if any exist
	if len(footnotes) > 0 {
		text += "\n\n<div class='footnotes-section'><hr><h4>Notes</h4><ol class='footnotes'>"
		for _, fn := range footnotes {
			// Store content as data attribute for tooltip access
			escapedContent := strings.ReplaceAll(fn.Content, `"`, `&quot;`)
			text += fmt.Sprintf(`<li id="fn-%s" data-content="%s">%s</li>`, 
				fn.Number, escapedContent, fn.Content)
		}
		text += "</ol></div>"
	}
	
	
	// Final step: Replace our markers with the correct values
	text = strings.ReplaceAll(text, "XXXFOOTNOTEREFXXX", "footnote-ref")
	text = strings.ReplaceAll(text, "DATATOOLTIPATR", "data-tooltip")
	
	// Final cleanup - remove any remaining header text at the beginning after all processing
	if book == "john" {
		// Special handling for John homilies
		if homilyNum == 1 {
			// For John Homily I (Preface), just remove the header paragraphs
			// Split into paragraphs
			paragraphs := strings.Split(text, "</p>")
			newParagraphs := []string{}
			foundContent := false
			
			for _, p := range paragraphs {
				p = strings.TrimSpace(p)
				if p == "" {
					continue
				}
				
				// Remove <p> tag for checking
				content := strings.TrimPrefix(p, "<p>")
				content = strings.TrimSpace(content)
				
				// Skip header paragraphs
				if !foundContent {
					lowerContent := strings.ToLower(content)
					if strings.Contains(lowerContent, "homily i.") ||
					   strings.Contains(lowerContent, "preface.") ||
					   strings.Contains(lowerContent, "gospel according to") ||
					   strings.Contains(lowerContent, "st. john.") ||
					   strings.Contains(lowerContent, "archbishop of constantinople") ||
					   content == "" {
						continue
					}
					foundContent = true
				}
				
				// This is actual content, keep it
				if !strings.HasSuffix(p, "</p>") {
					p = p + "</p>"
				}
				newParagraphs = append(newParagraphs, p)
			}
			
			text = strings.Join(newParagraphs, "\n")
			text = strings.TrimSpace(text)
		} else {
			// For other homilies, use the line-based cleanup
			lines := strings.Split(text, "\n")
			startIdx := 0
			for i, line := range lines {
				trimmed := strings.TrimSpace(strings.ToLower(line))
				// Skip lines that are just headers
				if trimmed == "gospel according to" || trimmed == "st. john." || trimmed == "preface." ||
				   strings.Contains(trimmed, "gospel according to") && strings.Contains(trimmed, "john") && i < 5 {
					startIdx = i + 1
				} else if trimmed != "" && i >= startIdx {
					break
				}
			}
			if startIdx > 0 && startIdx < len(lines) {
				text = strings.Join(lines[startIdx:], "\n")
			}
		}
	}
	
	// Final debug check for John Homily I
	if book == "john" && homilyNum == 1 {
		// Look for where the content actually starts
		previewStart := strings.Index(text, "heathen")
		if previewStart > 0 && previewStart < 500 {
			start := previewStart - 50
			if start < 0 {
				start = 0
			}
			end := previewStart + 100
			if end > len(text) {
				end = len(text)
			}
			log.Printf("DEBUG: Final text around 'heathen': %q", text[start:end])
		}
		
		// Also check the very beginning
		if len(text) > 200 {
			log.Printf("DEBUG: First 200 chars of final text: %q", text[:200])
		}
	}
	
	return text, verseRef, nil
}

func extractCyrilSermonFromHTML(sermonNum int) (string, string, error) {
	// Map sermon numbers to files
	var filename string
	var sermonID string
	
	// Determine which file contains this sermon
	if sermonNum >= 1 && sermonNum <= 11 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_01_sermons_01_11.htm"
		sermonID = fmt.Sprintf("C%d", sermonNum)
	} else if sermonNum >= 12 && sermonNum <= 25 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_02_sermons_12_25.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 27 && sermonNum <= 38 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_03_sermons_27_38.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 39 && sermonNum <= 46 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_04_sermons_39_46.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 47 && sermonNum <= 56 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_05_sermons_47_56.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 57 && sermonNum <= 65 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_06_sermons_57_65.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 66 && sermonNum <= 80 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_07_sermons_66_80.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 81 && sermonNum <= 88 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_08_sermons_81_88.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 89 && sermonNum <= 98 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_09_sermons_89_98.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 99 && sermonNum <= 109 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_10_sermons_99_109.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 110 && sermonNum <= 123 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_11_sermons_110_123.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 124 && sermonNum <= 134 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_12_sermons_124_134.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 135 && sermonNum <= 145 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_13_sermons_135_145.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else if sermonNum >= 146 && sermonNum <= 156 {
		filename = "../texts/commentaries/cyril/luke/cyril_on_luke_14_sermons_146_156.htm"
		sermonID = fmt.Sprintf("SERMON %s", strings.ToUpper(intToRoman(sermonNum)))
	} else {
		return "", "", fmt.Errorf("invalid sermon number: %d", sermonNum)
	}
	
	// Read the HTML file
	content, err := os.ReadFile(filename)
	if err != nil {
		return "", "", err
	}
	
	html := string(content)
	
	// Get verse reference from homily coverage
	verseRef := ""
	if comm, ok := commentaries["cyril-luke"]; ok {
		if coverage, ok := comm.Coverage[sermonNum]; ok {
			if coverage.StartChapter == coverage.EndChapter {
				if coverage.StartVerse == coverage.EndVerse {
					verseRef = fmt.Sprintf("Luke %d:%d", coverage.StartChapter, coverage.StartVerse)
				} else {
					verseRef = fmt.Sprintf("Luke %d:%d-%d", coverage.StartChapter, coverage.StartVerse, coverage.EndVerse)
				}
			} else {
				verseRef = fmt.Sprintf("Luke %d:%d-%d:%d", coverage.StartChapter, coverage.StartVerse, coverage.EndChapter, coverage.EndVerse)
			}
		}
	}
	
	// Extract sermon text
	var sermonText string
	
	// For sermons 1-11, look for the sermon heading
	if sermonNum <= 11 {
		// Look for the pattern like <A NAME="C1"></A>
		pattern := fmt.Sprintf(`NAME="%s"`, sermonID)
		startIdx := strings.Index(html, pattern)
		if startIdx == -1 {
			return "", "", fmt.Errorf("sermon %d not found", sermonNum)
		}
		// Move to the start of the tag
		tagStart := strings.LastIndex(html[:startIdx], "<")
		if tagStart != -1 {
			startIdx = tagStart
		}
		
		// Find the next sermon or end of content
		var endIdx int
		if sermonNum < 11 {
			nextSermonID := fmt.Sprintf("C%d", sermonNum+1)
			endPattern := fmt.Sprintf(`NAME="%s"`, nextSermonID)
			endIdx = strings.Index(html[startIdx:], endPattern)
		} else {
			endPattern := `<hr>`
			endIdx = strings.Index(html[startIdx:], endPattern)
		}
		
		if endIdx == -1 {
			// Look for end of document or navigation
			endPattern := `<a href="cyril_on_luke_`
			endIdx = strings.Index(html[startIdx:], endPattern)
			if endIdx == -1 {
				sermonText = html[startIdx:]
			} else {
				sermonText = html[startIdx : startIdx+endIdx]
			}
		} else {
			sermonText = html[startIdx : startIdx+endIdx]
		}
		log.Printf("Extracted %d characters for sermon %d", len(sermonText), sermonNum)
	} else {
		// For later sermons, look for headers like <a name="SERMON XII">
		pattern := fmt.Sprintf(`<a name="%s"`, sermonID)
		startIdx := strings.Index(html, pattern)
		if startIdx == -1 {
			// Try alternate pattern
			pattern = fmt.Sprintf(`<h3>.*%s.*</h3>`, sermonID)
			re := regexp.MustCompile(pattern)
			match := re.FindStringIndex(html)
			if match == nil {
				return "", "", fmt.Errorf("sermon %d not found", sermonNum)
			}
			startIdx = match[0]
		}
		
		// Find the next sermon
		nextPattern := `<h3>.*SERMON.*</h3>`
		re := regexp.MustCompile(nextPattern)
		matches := re.FindAllStringIndex(html[startIdx+1:], -1)
		if len(matches) > 0 {
			endIdx := matches[0][0]
			sermonText = html[startIdx : startIdx+1+endIdx]
		} else {
			// Look for navigation links at end
			endPattern := `<a href="cyril_on_luke_`
			endIdx := strings.Index(html[startIdx:], endPattern)
			if endIdx == -1 {
				sermonText = html[startIdx:]
			} else {
				sermonText = html[startIdx : startIdx+endIdx]
			}
		}
	}
	
	// Use pre-loaded footnotes from JSON instead of parsing HTML
	// Get footnotes for this sermon
	homilyFootnotes, hasFootnotes := cyrilLukeFootnotesData[strconv.Itoa(sermonNum)]
	var footnotes []Footnote
	footnoteMap := make(map[string]string)
	
	// Debug: check what we have for this sermon
	if sermonNum == 1 {
		log.Printf("DEBUG: hasFootnotes=%v, sermonNum=%d", hasFootnotes, sermonNum)
		if hasFootnotes {
			log.Printf("DEBUG: Found %d footnotes for sermon 1", len(homilyFootnotes.Footnotes))
		}
	}
	
	if hasFootnotes {
		for _, fn := range homilyFootnotes.Footnotes {
			footnotes = append(footnotes, Footnote{
				Number:  strconv.Itoa(fn.DisplayNumber),
				Content: fn.Content,
			})
			// Map original footnote number to content for lookup
			footnoteMap[strconv.Itoa(fn.OriginalNumber)] = fn.Content
		}
	}
	
	// Match any <A HREF="#anything"><SUP>anything</SUP></A> pattern  
	footnotePattern := regexp.MustCompile(`(?i)<A\s+HREF="#([^"]+)"><SUP>[^<]*</SUP></A>`)
	
	// Collect footnotes for endnotes section
	var collectedFootnotes []Footnote
	
	footnoteNum := 1
	sermonText = footnotePattern.ReplaceAllStringFunc(sermonText, func(match string) string {
		// Extract the footnote ID from the match
		hrefMatch := footnotePattern.FindStringSubmatch(match)
		
		tooltipContent := ""
		if len(hrefMatch) > 1 {
			footnoteID := hrefMatch[1]
			
			// Look up content in pre-loaded footnotes
			// Try sequential lookup for Cyril footnotes (HTML uses #1, #2, #3...)
			if content, found := footnoteMap[footnoteID]; found {
				tooltipContent = content
			} else if hasFootnotes && len(footnotes) > 0 {
				// If direct lookup fails, try sequential mapping
				if footnoteIdx, err := strconv.Atoi(footnoteID); err == nil && footnoteIdx > 0 && footnoteIdx <= len(footnotes) {
					tooltipContent = footnotes[footnoteIdx-1].Content
				}
			}
			
			// If still no content, add a fallback for debugging
			if tooltipContent == "" {
				tooltipContent = fmt.Sprintf("Footnote %s (Sermon %d)", footnoteID, sermonNum)
			}
			
			// Escape for HTML
			tooltipContent = strings.ReplaceAll(tooltipContent, `"`, `&quot;`)
			tooltipContent = strings.ReplaceAll(tooltipContent, `<`, `&lt;`)
			tooltipContent = strings.ReplaceAll(tooltipContent, `>`, `&gt;`)
		}
		
		// Collect this footnote for endnotes section
		if tooltipContent != "" && !strings.HasPrefix(tooltipContent, "Footnote ") {
			// Unescape for display in endnotes
			displayContent := strings.ReplaceAll(tooltipContent, `&quot;`, `"`)
			displayContent = strings.ReplaceAll(displayContent, `&lt;`, `<`)
			displayContent = strings.ReplaceAll(displayContent, `&gt;`, `>`)
			
			collectedFootnotes = append(collectedFootnotes, Footnote{
				Number: strconv.Itoa(footnoteNum),
				Content: fmt.Sprintf("%d. %s", footnoteNum, displayContent),
			})
		}
		
		// Return the replacement with sequential number
		// Use data-tooltip instead of title to avoid browser's default tooltip
		// Note: Using DATATOOLTIPATR placeholder to prevent hyphen replacement issues
		replacement := fmt.Sprintf(`<sup class="XXXFOOTNOTEREFXXX" DATATOOLTIPATR="%s">%d</sup>`, tooltipContent, footnoteNum)
		footnoteNum++
		return replacement
	})
	
	// Clean up the HTML
	sermonText = regexp.MustCompile(`<script[^>]*>.*?</script>`).ReplaceAllString(sermonText, "")
	sermonText = regexp.MustCompile(`<style[^>]*>.*?</style>`).ReplaceAllString(sermonText, "")
	
	// Remove editorial content
	sermonText = regexp.MustCompile(`\[From Mai and Cramer\]`).ReplaceAllString(sermonText, "")
	sermonText = regexp.MustCompile(`\[From [^\]]+\]`).ReplaceAllString(sermonText, "")
	
	// Remove h3 headers that contain editorial patterns
	sermonText = regexp.MustCompile(`(?is)<h3[^>]*>.*?(SERMON\s+[IVXLCDM]+|From S\. Cyril|From the Syriac).*?</h3>`).ReplaceAllString(sermonText, "")
	
	// Remove centered editorial paragraphs (Syriac references and source notes)
	sermonText = regexp.MustCompile(`(?is)<p align="center">\s*\[?From the Syriac.*?</p>`).ReplaceAllString(sermonText, "")
	sermonText = regexp.MustCompile(`(?is)<p align="center">\s*From the Syriac.*?</p>`).ReplaceAllString(sermonText, "")
	sermonText = regexp.MustCompile(`(?is)<p align="center">\s*\[From [^]]+\]</p>`).ReplaceAllString(sermonText, "")
	
	// Remove chapter reference notations like "cc. 2:21-24."
	sermonText = regexp.MustCompile(`(?is)<p>\s*cc?\.\s*\d+:\d+[-\d]*\.\s*</p>`).ReplaceAllString(sermonText, "")
	
	// Remove entire blockquotes that contain editorial content
	sermonText = regexp.MustCompile(`(?is)<blockquote>.*?(SERMON\s+[IVXLCDM]+|From Aubert|From Mai|From the Syriac).*?</blockquote>`).ReplaceAllString(sermonText, "")
	
	// Remove any paragraph containing "From S. Cyril's Commentary"
	sermonText = regexp.MustCompile(`(?is)<p[^>]*>.*?From S\. Cyril's Commentary[^<]*</p>`).ReplaceAllString(sermonText, "")
	
	// Remove any paragraph containing "Sermon of S. Cyril" 
	sermonText = regexp.MustCompile(`(?is)<p[^>]*>.*?Sermon of S\. Cyril[^<]*</p>`).ReplaceAllString(sermonText, "")
	
	// Remove standalone sermon number markers
	sermonText = regexp.MustCompile(`(?i)SERMON\s+[IVXLC]+\.?\s*`).ReplaceAllString(sermonText, "")
	
	// Remove page markers
	sermonText = regexp.MustCompile(`<A NAME="p\d+"><SPAN CLASS=pb>\|\d+</SPAN></A>`).ReplaceAllString(sermonText, "")
	
	// Just trim whitespace
	sermonText = strings.TrimSpace(sermonText)
	
	// Clean up any fragments at the beginning that might remain after h3 removal
	// This specifically targets patterns like: <A NAME="C3"></A></SPAN><sup>16</sup></h3>
	sermonText = regexp.MustCompile(`(?s)^.*?</h3>\s*`).ReplaceAllString(sermonText, "")
	
	// Remove empty paragraphs at the beginning
	sermonText = regexp.MustCompile(`(?s)^<p[^>]*>\s*</p>\s*`).ReplaceAllString(sermonText, "")
	
	sermonText = strings.TrimSpace(sermonText)
	
	// Remove footnote definitions at bottom (we've already captured them for tooltips)
	sermonText = regexp.MustCompile(`<A NAME="\d+"></A>\d+\.\s*<sup>\w+</sup>[^<]*(?:<[^A][^>]*>[^<]*</[^>]+>[^<]*)*`).ReplaceAllString(sermonText, "")
	
	// Convert some tags
	sermonText = strings.ReplaceAll(sermonText, "<i>", "<em>")
	sermonText = strings.ReplaceAll(sermonText, "</i>", "</em>")
	sermonText = strings.ReplaceAll(sermonText, "<b>", "<strong>")
	sermonText = strings.ReplaceAll(sermonText, "</b>", "</strong>")
	
	// Replace the placeholders with the actual values (same as Chrysostom)
	sermonText = strings.ReplaceAll(sermonText, "XXXFOOTNOTEREFXXX", "footnote-ref")
	sermonText = strings.ReplaceAll(sermonText, "DATATOOLTIPATR", "data-tooltip")
	
	// Fix footnote placement according to Chicago Manual of Style
	// Move footnotes after punctuation marks
	punctuationPattern := regexp.MustCompile(`(<sup class="footnote-ref"[^>]*>.*?</sup>)([.,;:!?]+)`)
	sermonText = punctuationPattern.ReplaceAllString(sermonText, "$2$1")
	
	// Remove spaces before footnotes ONLY when they follow punctuation
	sermonText = regexp.MustCompile(`([.,;:!?])\s+(<sup class="footnote-ref")`).ReplaceAllString(sermonText, "$1$2")
	
	// Clean up the sermon text
	sermonText = strings.TrimSpace(sermonText)
	
	// Append footnotes section if any exist (same as Chrysostom)
	if len(collectedFootnotes) > 0 {
		sermonText += "\n\n<div class='footnotes-section'><hr><h4>Notes</h4><ol class='footnotes'>"
		for _, fn := range collectedFootnotes {
			// Store content as data attribute for tooltip access
			escapedContent := strings.ReplaceAll(fn.Content, `"`, `&quot;`)
			sermonText += fmt.Sprintf(`<li id="fn-%s" data-content="%s">%s</li>`, 
				fn.Number, escapedContent, fn.Content)
		}
		sermonText += "</ol></div>"
	}
	
	log.Printf("After cleaning: %d characters for sermon %d", len(sermonText), sermonNum)
	if len(sermonText) < 100 {
		log.Printf("Warning: Sermon %d content is very short: %s", sermonNum, sermonText)
	}
	
	return sermonText, verseRef, nil
}

func homilyAPIHandler(w http.ResponseWriter, r *http.Request) {
	// Parse URL: /api/homily/chrysostom/matthew/1 or /api/homily/cyril/luke/1
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/homily/"), "/")
	if len(parts) != 3 {
		http.Error(w, "Invalid URL", http.StatusBadRequest)
		return
	}
	
	author := parts[0]
	book := parts[1]
	homilyNumStr := parts[2]
	
	if author == "chrysostom" && (book != "matthew" && book != "john") {
		http.Error(w, "Homily not found", http.StatusNotFound)
		return
	}
	if author == "cyril" && book != "luke" {
		http.Error(w, "Homily not found", http.StatusNotFound)
		return
	}
	if author != "chrysostom" && author != "cyril" {
		http.Error(w, "Author not found", http.StatusNotFound)
		return
	}
	
	homilyNum, err := strconv.Atoi(homilyNumStr)
	if err != nil {
		http.Error(w, "Invalid homily number", http.StatusBadRequest)
		return
	}
	
	var homilyText, verseRef string
	
	if author == "chrysostom" {
		// Extract homily text from XML
		homilyText, verseRef, err = extractHomilyFromXML(book, homilyNum)
		if err != nil {
			log.Printf("Error extracting homily %d: %v", homilyNum, err)
			w.Header().Set("Content-Type", "text/html")
			w.Write([]byte("<p>Error loading homily text.</p>"))
			return
		}
	} else if author == "cyril" {
		// Extract sermon text from HTML
		homilyText, verseRef, err = extractCyrilSermonFromHTML(homilyNum)
		if err != nil {
			log.Printf("Error extracting Cyril sermon %d: %v", homilyNum, err)
			w.Header().Set("Content-Type", "text/html")
			w.Write([]byte("<p>Error loading sermon text.</p>"))
			return
		}
	}
	
	// Clean up verse reference
	if strings.Contains(verseRef, "Homily") || strings.Contains(verseRef, "Sermon") || verseRef == "Introduction" || verseRef == "" {
		verseRef = ""
	}
	
	// Return just the content HTML
	var html string
	if verseRef != "" {
		html = fmt.Sprintf(`
			<div class="chapter-text">
				<p class="verse-reference" style="text-align: center; color: #666; font-style: italic; margin-bottom: 20px;">%s</p>
				%s
			</div>
		`, verseRef, homilyText)
	} else {
		html = fmt.Sprintf(`
			<div class="chapter-text">
				%s
			</div>
		`, homilyText)
	}
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func aboutHandler(w http.ResponseWriter, r *http.Request) {
	html := `
	<div class="chapter-text" style="max-width: 600px; margin: 0 auto;">
		<h2 style="text-align: center; margin-bottom: 30px;">About Hypomnema</h2>
		
		<h3>What is Hypomnema?</h3>
		<p><strong>Hypomnema</strong> (ὑπόμνημα) is a Greek word meaning "reminder," "note," "commentary," 
		or "memorandum." In ancient times, a hypomnema was a notebook or commentary where readers would 
		record their thoughts, interpretations, and cross-references while studying texts. This application 
		embodies that tradition by providing integrated commentary and cross-references alongside the 
		biblical text.</p>
		
		<h3>Technology</h3>
		<p>This application is built with <strong>Go</strong> for the backend server and <strong>HTMX</strong> 
		for dynamic content loading, providing a fast and responsive user experience without the complexity 
		of a heavy JavaScript framework.</p>
		
		<h3>Data Sources & Attributions</h3>
		
		<p><strong>King James Version (KJV) Text</strong><br>
		The King James Version text is in the public domain.</p>
		
		<p><strong>Eusebian Canon Tables</strong><br>
		The Eusebian Canon data was compiled from historical sources to show Gospel parallels 
		as organized by Eusebius of Caesarea in the 4th century.</p>
		
		<p><strong>Chrysostom Homilies on Matthew</strong><br>
		The homilies of St. John Chrysostom on the Gospel of Matthew are sourced from the 
		<em>Nicene and Post-Nicene Fathers</em> series, available through the 
		<a href="https://www.ccel.org" target="_blank" style="white-space: nowrap;">Christian Classics Ethereal Library (CCEL)</a>. 
		Specifically from: <a href="https://www.ccel.org/ccel/schaff/npnf110.xml" target="_blank">https://www.ccel.org/ccel/schaff/npnf110.xml</a></p>
		
		<p><strong>Chrysostom Homilies on John</strong><br>
		The homilies of St. John Chrysostom on the Gospel of John are also sourced from the 
		<em>Nicene and Post-Nicene Fathers</em> series, available through CCEL. 
		Specifically from: <a href="https://www.ccel.org/ccel/schaff/npnf114.xml" target="_blank">https://www.ccel.org/ccel/schaff/npnf114.xml</a></p>
		
		<h3>Features</h3>
		<ul>
			<li>Clean, distraction-free text reading</li>
			<li>Eusebian Canon references in the margins showing Gospel parallels</li>
			<li>Chrysostom homily references for the Gospels of Matthew and John</li>
			<li>Cross-Gospel homily references via Eusebian canons</li>
			<li>Responsive design for comfortable reading</li>
		</ul>
		
		<h3>Contributing</h3>
		<p>This project is open source and available on <a href="https://github.com/GZancewicz/hypomnema" target="_blank">GitHub</a>. 
		Issues, suggestions, and pull requests are welcome.</p>
		
		<h3>Support</h3>
		<p>Please donate if you wish to help defer the costs of hosting this app. Excess donations will be converted to USD and donated to International Orthodox Christian Charities (IOCC).</p>
		<div style="display: flex; align-items: center; gap: 10px; margin: 15px 0;">
			<span style="font-size: 24px;">₿</span>
			<code style="background: #f5f5f5; padding: 8px 12px; border-radius: 4px; font-size: 14px;">397NxpMc8HAQxKW6CkSsgJP5kTuyFQ6R45</code>
			<button onclick="navigator.clipboard.writeText('397NxpMc8HAQxKW6CkSsgJP5kTuyFQ6R45').then(() => { this.textContent = 'Copied!'; setTimeout(() => this.textContent = 'Copy', 2000); })" style="padding: 6px 12px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;">Copy</button>
		</div>
	</div>
	`
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}


