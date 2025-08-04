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

// Global data
var (
	verseToCanon VerseToCanon
	canonLookup CanonLookup
	verseToHomily VerseToHomily
	homilyCoverage map[int]HomilyRange
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
	
	// Load verse-to-homily mapping
	loadVerseToHomily()
	loadHomilyCoverage()

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

func loadVerseToHomily() {
	file, err := os.Open("../texts/commentaries/chrysostom/matthew/matthew_verse_to_homilies.json")
	if err != nil {
		log.Println("Warning: Could not load verse-to-homily data:", err)
		verseToHomily = make(VerseToHomily)
		return
	}
	defer file.Close()

	err = json.NewDecoder(file).Decode(&verseToHomily)
	if err != nil {
		log.Println("Warning: Could not parse verse-to-homily data:", err)
		verseToHomily = make(VerseToHomily)
		return
	}
}

func loadHomilyCoverage() {
	file, err := os.Open("../texts/commentaries/chrysostom/matthew/homily_coverage.json")
	if err != nil {
		log.Println("Warning: Could not load homily coverage data:", err)
		homilyCoverage = make(map[int]HomilyRange)
		return
	}
	defer file.Close()

	var tempCoverage map[string]HomilyRange
	err = json.NewDecoder(file).Decode(&tempCoverage)
	if err != nil {
		log.Println("Warning: Could not parse homily coverage data:", err)
		homilyCoverage = make(map[int]HomilyRange)
		return
	}
	
	// Convert string keys to int
	homilyCoverage = make(map[int]HomilyRange)
	for k, v := range tempCoverage {
		if num, err := strconv.Atoi(k); err == nil {
			homilyCoverage[num] = v
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

// findHomiliesForMatthewRange finds which homilies cover a given Matthew passage
func findHomiliesForMatthewRange(startChap, startVerse, endChap, endVerse int) []Homily {
	var result []Homily
	
	for _, hr := range homilyCoverage {
		// Check if the homily range overlaps with the requested range
		if (hr.StartChapter < endChap || (hr.StartChapter == endChap && hr.StartVerse <= endVerse)) &&
		   (hr.EndChapter > startChap || (hr.EndChapter == startChap && hr.EndVerse >= startVerse)) {
			result = append(result, Homily{
				Number: hr.Number,
				Roman:  hr.Roman,
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
	
	// Homily page
	http.HandleFunc("/homily/", homilyHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	fmt.Printf("Server starting on http://localhost:%s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
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
	
	// Get homily mappings (only for Matthew)
	var homilyMap map[string][]Homily
	if bookID == "matthew" {
		homilyMap = verseToHomily
	}
	
	// Format the text with paragraphs and canon numbers
	html := formatChapterHTML(string(content), chapterParagraphs, bookCanons, chapter, bookID, homilyMap)
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func formatChapterHTML(text string, paragraphBreaks []int, bookCanons map[string]string, chapter int, bookID string, homilyMap map[string][]Homily) string {
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
		
		if bookID == "matthew" && homilyMap != nil {
			// Direct homily references for Matthew
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
						html.WriteString(fmt.Sprintf(`<a href="#" onclick="loadHomily(%d, '%s'); return false;" class="homily-ref" data-full-text="John Chrysostom, Homily %s on Matthew">Homily %s</a>`, 
							homily.Number, homily.Roman, homily.Roman, homily.Roman))
					}
					html.WriteString(`</div>`)
				}
			}
		} else if bookID != "matthew" && canonNum != "" {
			// Cross-referenced homilies for other Gospels via canon tables
			if canonData, ok := canonLookup[canonNum]; ok {
				if matthewRef, ok := canonData["matthew"]; ok {
					// Parse the Matthew reference
					startChap, startVerse, endChap, endVerse, err := parseVerseRef(matthewRef)
					if err == nil {
						// Find homilies that cover this Matthew passage
						homilies := findHomiliesForMatthewRange(startChap, startVerse, endChap, endVerse)
						
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
							html.WriteString(`<div class="homily-refs-container cross-ref">`)
							for _, homily := range filteredHomilies {
								html.WriteString(fmt.Sprintf(`<a href="#" onclick="loadHomily(%d, '%s'); return false;" class="homily-ref cross-ref" data-full-text="John Chrysostom, Homily %s on Matthew">Homily %s</a>`, 
									homily.Number, homily.Roman, homily.Roman, homily.Roman))
							}
							html.WriteString(`</div>`)
						}
					}
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
	// Parse URL: /homily/chrysostom/matthew/1
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/homily/"), "/")
	if len(parts) != 3 {
		http.Error(w, "Invalid URL", http.StatusBadRequest)
		return
	}
	
	author := parts[0]
	book := parts[1]
	homilyNumStr := parts[2]
	
	if author != "chrysostom" || book != "matthew" {
		http.Error(w, "Homily not found", http.StatusNotFound)
		return
	}
	
	homilyNum, err := strconv.Atoi(homilyNumStr)
	if err != nil {
		http.Error(w, "Invalid homily number", http.StatusBadRequest)
		return
	}
	
	// Convert to roman numeral
	roman := intToRoman(homilyNum)
	
	// Extract homily text from XML
	homilyText, verseRef, err := extractHomilyFromXML(homilyNum)
	if err != nil {
		log.Printf("Error extracting homily %d: %v", homilyNum, err)
		homilyText = "Error loading homily text."
	}
	
	// Clean up verse reference - don't show if it contains "Homily" or is just a title
	if strings.Contains(verseRef, "Homily") || verseRef == "Introduction" || verseRef == "" {
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
		Author:      "John Chrysostom",
		Book:        "Matthew",
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
type Footnote struct {
	Number   string
	ID       string
	Content  string
}

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
var footnotesData map[string]FootnoteData

// Load footnotes from JSON file
func loadFootnotes() error {
	data, err := os.ReadFile("../texts/commentaries/chrysostom/matthew/footnotes.json")
	if err != nil {
		return err
	}
	
	footnotesData = make(map[string]FootnoteData)
	err = json.Unmarshal(data, &footnotesData)
	if err != nil {
		return err
	}
	
	log.Printf("Loaded footnotes for %d homilies", len(footnotesData))
	return nil
}

func extractHomilyFromXML(homilyNum int) (string, string, error) {
	// Read the XML file
	xmlPath := "../texts/commentaries/chrysostom/matthew/chrysostom_matthew_homilies.xml"
	content, err := os.ReadFile(xmlPath)
	if err != nil {
		return "", "", err
	}
	
	// Convert content to string for regex processing
	xmlContent := string(content)
	
	// Look for the specific homily using its roman numeral
	roman := intToRoman(homilyNum)
	
	// Pattern to find the homily div2
	// Handle both cases: with type="Homily" attribute and without
	pattern := fmt.Sprintf(`(?s)<div2[^>]*n="%s"[^>]*>.*?</div2>`, roman)
	re := regexp.MustCompile(pattern)
	
	match := re.FindString(xmlContent)
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
	
	// Get footnotes from preloaded data
	homilyFootnotes, hasFootnotes := footnotesData[strconv.Itoa(homilyNum)]
	var footnotes []Footnote
	footnoteMap := make(map[string]int)
	
	if hasFootnotes {
		for _, fn := range homilyFootnotes.Footnotes {
			footnotes = append(footnotes, Footnote{
				Number:  strconv.Itoa(fn.DisplayNumber),
				Content: fn.Content,
			})
			// Map original number to display number
			footnoteMap[strconv.Itoa(fn.OriginalNumber)] = fn.DisplayNumber
		}
	}
	
	// Replace footnote tags with superscript markers
	notePattern := regexp.MustCompile(`(?s)<note\s+n="([^"]+)"[^>]*>.*?</note>`)
	text = notePattern.ReplaceAllStringFunc(text, func(match string) string {
		// Extract note number
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
				
				// Use a unique marker to preserve the class name with hyphen
				return fmt.Sprintf(`<sup class="XXXFOOTNOTEREFXXX" title="%s">%d</sup>%s`, 
					tooltipContent, newNum, needsSpace)
			}
		}
		return ""
	})
	
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
	text = regexp.MustCompile(`(?si)Homilies\s+of\s+St\.\s*John\s+Chrysostom[^.]*?gospel\s+according\s+to\s+st\.\s*matthew\.`).ReplaceAllString(text, "")
	
	// Also try a more aggressive pattern with any characters between
	text = regexp.MustCompile(`(?s)Homilies of St\. John Chrysostom.*?matthew\.`).ReplaceAllString(text, "")
	
	// Remove any lingering header fragments
	text = regexp.MustCompile(`(?s)archbishop of constantinople,`).ReplaceAllString(text, "")
	text = regexp.MustCompile(`(?s)on the\s*gospel according to st\. matthew\.`).ReplaceAllString(text, "")
	
	// Remove multiple dashes that might appear after header removal
	text = regexp.MustCompile(`(?s)[-—]+\s*`).ReplaceAllString(text, "")
	
	// Also remove just "Homily [Roman]." at the beginning of the text
	homilyStartPattern := fmt.Sprintf(`(?s)Homily %s\.`, roman)
	text = regexp.MustCompile(homilyStartPattern).ReplaceAllString(text, "")
	
	// Remove verse references at the beginning (like "Matt. I. 1." or "Matthew 1:1" or "Matt. II. 4, 5.")
	// These are redundant since we show them in the subtitle
	// Handle comma-separated verses
	verseStartPattern := `(?s)^[\s\p{Z}]*(?:Matt\.|Matthew)\s+[IVX]+\.\s*\d+(?:\s*,\s*\d+)?\.?`
	text = regexp.MustCompile(verseStartPattern).ReplaceAllString(text, "")
	
	// Also remove arabic numeral format
	verseStartPattern2 := `(?s)^[\s\p{Z}]*(?:Matt\.|Matthew)\s+\d+[:.]\s*\d+(?:\s*,\s*\d+)?\.?`
	text = regexp.MustCompile(verseStartPattern2).ReplaceAllString(text, "")
	
	// Also remove just remaining verse fragments like ", 5."
	verseFragmentPattern := `(?s)^[\s\p{Z}]*,\s*\d+\.?`
	text = regexp.MustCompile(verseFragmentPattern).ReplaceAllString(text, "")
	
	// Extract scripture references from scripRef tags before removing them
	// Replace scripRef tags with their text content
	scripRefPattern := regexp.MustCompile(`<scripRef[^>]*>([^<]+)</scripRef>`)
	text = scripRefPattern.ReplaceAllString(text, "$1")
	
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
	// Restore preserved tags
	text = strings.ReplaceAll(text, "{{P_OPEN}}", "<p>")
	text = strings.ReplaceAll(text, "{{P_CLOSE}}", "</p>")
	text = regexp.MustCompile(`{{SUP_OPEN([^}]*)}}`).ReplaceAllString(text, "<sup$1>")
	text = strings.ReplaceAll(text, "{{SUP_CLOSE}}", "</sup>")
	text = regexp.MustCompile(`{{A_OPEN:([^}]+)}}`).ReplaceAllString(text, "<a $1>")
	text = strings.ReplaceAll(text, "{{A_CLOSE}}", "</a>")
	
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
			text += fmt.Sprintf(`<li id="fn-%s" data-content="%s">%s. %s</li>`, 
				fn.Number, escapedContent, fn.Number, fn.Content)
		}
		text += "</ol></div>"
	}
	
	
	// Final step: Replace our marker with the correct class name
	text = strings.ReplaceAll(text, "XXXFOOTNOTEREFXXX", "footnote-ref")
	
	return text, verseRef, nil
}


func homilyAPIHandler(w http.ResponseWriter, r *http.Request) {
	// Parse URL: /api/homily/chrysostom/matthew/1
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/homily/"), "/")
	if len(parts) != 3 {
		http.Error(w, "Invalid URL", http.StatusBadRequest)
		return
	}
	
	author := parts[0]
	book := parts[1]
	homilyNumStr := parts[2]
	
	if author != "chrysostom" || book != "matthew" {
		http.Error(w, "Homily not found", http.StatusNotFound)
		return
	}
	
	homilyNum, err := strconv.Atoi(homilyNumStr)
	if err != nil {
		http.Error(w, "Invalid homily number", http.StatusBadRequest)
		return
	}
	
	// Extract homily text from XML
	homilyText, verseRef, err := extractHomilyFromXML(homilyNum)
	if err != nil {
		log.Printf("Error extracting homily %d: %v", homilyNum, err)
		w.Header().Set("Content-Type", "text/html")
		w.Write([]byte("<p>Error loading homily text.</p>"))
		return
	}
	
	// Clean up verse reference
	if strings.Contains(verseRef, "Homily") || verseRef == "Introduction" || verseRef == "" {
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
		<a href="https://www.ccel.org" target="_blank">Christian Classics Ethereal Library (CCEL)</a>. 
		Specifically from: <a href="https://www.ccel.org/ccel/schaff/npnf110.xml" target="_blank">
		https://www.ccel.org/ccel/schaff/npnf110.xml</a></p>
		
		<h3>Features</h3>
		<ul>
			<li>Clean, distraction-free text reading</li>
			<li>Eusebian Canon references in the margins showing Gospel parallels</li>
			<li>Chrysostom homily references for the Gospel of Matthew</li>
			<li>Responsive design for comfortable reading</li>
		</ul>
	</div>
	`
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}


