package main

import (
	"embed"
	"encoding/json"
	"fmt"
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
	ID       string `json:"id"`
	Name     string `json:"name"`
	Chapters int    `json:"chapters"`
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

// Global data
var (
	verseToCanon VerseToCanon
	canonLookup CanonLookup
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
	// Load paragraph data
	loadParagraphData()
	
	// Load verse-to-canon mapping
	loadVerseToCanon()
	
	// Load canon lookup data
	loadCanonLookup()

	// Parse templates
	var err error
	templates, err = template.ParseFS(templateFS, "templates/*.html")
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

func main() {
	// Serve static files
	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("./static"))))

	// Main page
	http.HandleFunc("/", indexHandler)

	// API endpoints
	http.HandleFunc("/api/chapter/", chapterHandler)
	http.HandleFunc("/api/canon/", canonHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	fmt.Printf("Server starting on http://localhost:%s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	data := struct {
		Books       []Book
		CurrentBook string
		CurrentChap int
	}{
		Books:       books,
		CurrentBook: "matthew",
		CurrentChap: 1,
	}

	err := templates.ExecuteTemplate(w, "index.html", data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
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
	
	// Format the text with paragraphs and canon numbers
	html := formatChapterHTML(string(content), chapterParagraphs, bookCanons, chapter, bookID)
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func formatChapterHTML(text string, paragraphBreaks []int, bookCanons map[string]string, chapter int, bookID string) string {
	lines := strings.Split(strings.TrimSpace(text), "\n")
	var html strings.Builder
	
	html.WriteString("<div class='chapter-text'>")
	
	inParagraph := false
	isFirstVerse := true
	lastCanonNum := ""
	
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
		
		// Add verse with superscript number
		html.WriteString(fmt.Sprintf(`<span class="verse"><sup class="verse-num">%d</sup>%s </span>`, verseNum, verseText))
		
		isFirstVerse = false
	}
	
	if inParagraph {
		html.WriteString("</p>")
	}
	
	html.WriteString("</div>")
	return html.String()
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