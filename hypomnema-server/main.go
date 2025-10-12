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
	"sort"
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

// HarmonyEntry represents an entry in the harmony.json file
type HarmonyEntry struct {
	Canon    string         `json:"canon"`
	Sections map[string]int `json:"sections"`
}

// SectionEntry represents a section in a book's section file
type SectionEntry struct {
	Section   int    `json:"section"`
	Reference string `json:"reference"`
}

// Homily represents a Chrysostom homily reference
type Homily struct {
	ID      int    `json:"id"`
	Roman   string `json:"roman"`
	Passage string `json:"passage"`
	End     string `json:"end"`
}

// VerseToHomily holds the verse-to-homily mapping (multiple homilies per verse)
type VerseToHomily map[string][]Homily

// HomilyRange represents the coverage of a homily
type HomilyRange struct {
	ID     int    `json:"id"`
	Roman  string `json:"roman"`
	Title  string `json:"title"`
	Start  struct {
		Chapter int `json:"chapter"`
		Verse   int `json:"verse"`
	} `json:"start"`
	End struct {
		Chapter int `json:"chapter"`
		Verse   int `json:"verse"`
	} `json:"end"`
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

// ScriptureReference represents a scripture reference from the index
type ScriptureReference struct {
	ID        int    `json:"id"`
	Book      string `json:"book"`
	Reference string `json:"reference"`
	Homily    int    `json:"homily"`
	Section   string `json:"section"`
}

// Global data
var (
	verseToCanon VerseToCanon
	canonLookup CanonLookup
	harmonyData []HarmonyEntry
	sectionData map[string][]SectionEntry
	commentaries map[string]*Commentary
	chrysostomMatthewFootnotes AllFootnotes
	chrysostomJohnFootnotes    AllFootnotes
	scriptureReferences map[string][]ScriptureReference
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

	// Load harmony data
	loadHarmonyData()

	// Load section data
	loadSectionData()

	// Load all commentaries
	loadCommentary("chrysostom", "matthew", 
		"../texts/commentaries/chrysostom/matthew/verse_mapping.json",
		"../texts/commentaries/chrysostom/matthew/coverage.json")
	loadCommentary("chrysostom", "john",
		"../texts/commentaries/chrysostom/john/verse_mapping.json",
		"../texts/commentaries/chrysostom/john/coverage.json")
	loadCommentary("cyril", "luke",
		"../texts/commentaries/cyril/luke/verse_mapping.json",
		"../texts/commentaries/cyril/luke/coverage.json")

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

func loadHarmonyData() {
	file, err := os.Open("../texts/reference/eusebian_canons/harmony.json")
	if err != nil {
		log.Println("Warning: Could not load harmony data:", err)
		harmonyData = []HarmonyEntry{}
		return
	}
	defer file.Close()

	err = json.NewDecoder(file).Decode(&harmonyData)
	if err != nil {
		log.Println("Warning: Could not parse harmony data:", err)
		harmonyData = []HarmonyEntry{}
	}
}

func loadSectionData() {
	sectionData = make(map[string][]SectionEntry)
	gospels := []string{"matthew", "mark", "luke", "john"}

	for _, gospel := range gospels {
		filePath := fmt.Sprintf("../texts/reference/eusebian_canons/data/%s_sections.json", gospel)
		file, err := os.Open(filePath)
		if err != nil {
			log.Printf("Warning: Could not load %s section data: %v", gospel, err)
			continue
		}

		var sections []SectionEntry
		err = json.NewDecoder(file).Decode(&sections)
		file.Close()

		if err != nil {
			log.Printf("Warning: Could not parse %s section data: %v", gospel, err)
			continue
		}

		sectionData[gospel] = sections
	}
}

func getParallels(book string, chapter, verse int) string {
	sections, ok := sectionData[book]
	if !ok {
		return ""
	}

	verseNum := chapter*1000 + verse

	for _, section := range sections {
		startChap, startVerse, endChap, endVerse, err := parseVerseRef(section.Reference)
		if err != nil {
			continue
		}

		startNum := startChap*1000 + startVerse
		endNum := endChap*1000 + endVerse

		if verseNum >= startNum && verseNum <= endNum {
			sectionNum := section.Section

			for _, harmony := range harmonyData {
				bookKey := strings.Title(book)
				if sec, ok := harmony.Sections[bookKey]; ok && sec == sectionNum {
					var parallels []string
					gospelAbbr := map[string]string{
						"Matthew": "Mt",
						"Mark":    "Mk",
						"Luke":    "Lk",
						"John":    "Jn",
					}

					for _, gospel := range []string{"Matthew", "Mark", "Luke", "John"} {
						if gospel == bookKey {
							continue
						}
						if secNum, exists := harmony.Sections[gospel]; exists {
							if secRef, ok := sectionData[strings.ToLower(gospel)]; ok {
								for _, s := range secRef {
									if s.Section == secNum {
										parallels = append(parallels, fmt.Sprintf("%s %s", gospelAbbr[gospel], s.Reference))
										break
									}
								}
							}
						}
					}

					if len(parallels) > 0 {
						return strings.Join(parallels, "<br>")
					}
					return ""
				}
			}
			break
		}
	}

	return ""
}

func getCanonAndSection(book string, chapter, verse int) string {
	sections, ok := sectionData[book]
	if !ok {
		return ""
	}

	verseNum := chapter*1000 + verse

	for _, section := range sections {
		startChap, startVerse, endChap, endVerse, err := parseVerseRef(section.Reference)
		if err != nil {
			continue
		}

		startNum := startChap*1000 + startVerse
		endNum := endChap*1000 + endVerse

		if verseNum >= startNum && verseNum <= endNum {
			sectionNum := section.Section

			for _, harmony := range harmonyData {
				bookKey := strings.Title(book)
				if sec, ok := harmony.Sections[bookKey]; ok && sec == sectionNum {
					return fmt.Sprintf("%s.%d", harmony.Canon, sectionNum)
				}
			}
			break
		}
	}

	return ""
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
		var coverageData struct {
			Commentary    string         `json:"commentary"`
			TotalHomilies int            `json:"total_homilies"`
			Homilies      []HomilyRange  `json:"homilies"`
		}
		err = json.NewDecoder(file2).Decode(&coverageData)
		if err != nil {
			log.Printf("Warning: Could not parse %s %s homily coverage data: %v", author, book, err)
			commentary.Coverage = make(map[int]HomilyRange)
		} else {
			// Convert array to map indexed by ID
			commentary.Coverage = make(map[int]HomilyRange)
			for _, homily := range coverageData.Homilies {
				commentary.Coverage[homily.ID] = homily
			}
			log.Printf("Loaded %s %s coverage for %d homilies/sermons", author, book, len(commentary.Coverage))
		}
	}
	
	commentaries[key] = commentary
}

// loadAllFootnotes loads the pre-extracted footnotes for all homilies
func loadAllFootnotes() {
	// Footnotes are now loaded from metadata.json files in each homily/sermon folder
	// This function is kept for compatibility but doesn't need to do anything
}

// parseVerseRef parses a verse reference like "3.3" or "3.3-6" into chapter and verse numbers

func parseVerseRef(ref string) (startChap, startVerse, endChap, endVerse int, err error) {
	// Handle ranges like "3:3-6" or "3.3-6" or single verses like "3:3" or "3.3"
	parts := strings.Split(ref, "-")

	// Parse start reference - support both : and . separators
	var startParts []string
	if strings.Contains(parts[0], ":") {
		startParts = strings.Split(parts[0], ":")
	} else {
		startParts = strings.Split(parts[0], ".")
	}
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
	
	// Parse end reference - support both : and . separators
	if strings.Contains(parts[1], ".") || strings.Contains(parts[1], ":") {
		// Full reference like "3:6" or "3.6"
		var endParts []string
		if strings.Contains(parts[1], ":") {
			endParts = strings.Split(parts[1], ":")
		} else {
			endParts = strings.Split(parts[1], ".")
		}
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
		if (hr.Start.Chapter < endChap || (hr.Start.Chapter == endChap && hr.Start.Verse <= endVerse)) &&
		   (hr.End.Chapter > startChap || (hr.End.Chapter == startChap && hr.End.Verse >= startVerse)) {
			// Simple passage format - we'll format it properly when displaying
			passage := fmt.Sprintf("%d:%d-%d:%d", hr.Start.Chapter, hr.Start.Verse, hr.End.Chapter, hr.End.Verse)
			
			result = append(result, Homily{
				ID:     hr.ID,
				Roman:  hr.Roman,
				Passage: passage,
			})
		}
	}
	
	return result
}

func main() {
	// Initialize footnote maps (footnotes are loaded from metadata.json files)
	loadFootnotes()

	// Load scripture references
	loadScriptureReferences()

	// Serve static files
	http.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("./static"))))

	// Main page
	http.HandleFunc("/", indexHandler)

	// API endpoints
	http.HandleFunc("/api/chapter/", chapterHandler)
	http.HandleFunc("/api/canon/", canonHandler)
	http.HandleFunc("/api/about", aboutHandler)
	http.HandleFunc("/api/index", indexPageHandler)
	http.HandleFunc("/api/references", referencesHandler)
	http.HandleFunc("/api/scripture-references", scriptureReferencesHandler)
	http.HandleFunc("/api/homily/", homilyAPIHandler)
	http.HandleFunc("/api/homilies/", homiliesListHandler)
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
	
	// Get available Cyril sermons
	cyrilSermons := []struct {
		ID     int
		Roman  string
		Verses string
	}{}
	
	// Scan the Cyril content directory for available sermons
	contentDir := "../texts/commentaries/cyril/luke/content"
	files, err := os.ReadDir(contentDir)
	if err == nil {
		for _, file := range files {
			if file.IsDir() {
				// Parse directory name as sermon number
				sermonNum := 0
				fmt.Sscanf(file.Name(), "%03d", &sermonNum)
				if sermonNum > 0 {
					// Get the verse reference from coverage data if available
					verses := ""
					if cyrilComm, ok := commentaries["cyril-luke"]; ok {
						if coverage, ok := cyrilComm.Coverage[sermonNum]; ok {
							if coverage.Start.Chapter == coverage.End.Chapter {
								if coverage.Start.Verse == coverage.End.Verse {
									verses = fmt.Sprintf("(%d:%d)", coverage.Start.Chapter, coverage.Start.Verse)
								} else {
									verses = fmt.Sprintf("(%d:%d-%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Verse)
								}
							} else {
								verses = fmt.Sprintf("(%d:%d-%d:%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Chapter, coverage.End.Verse)
							}
						}
					}
					
					cyrilSermons = append(cyrilSermons, struct {
						ID     int
						Roman  string
						Verses string
					}{
						ID:     sermonNum,
						Roman:  intToRoman(sermonNum),
						Verses: verses,
					})
				}
			}
		}
	}
	
	// Sort by ID
	sort.Slice(cyrilSermons, func(i, j int) bool {
		return cyrilSermons[i].ID < cyrilSermons[j].ID
	})
	
	data := struct {
		Books        []Book
		CurrentBook  string
		CurrentChap  int
		CyrilSermons []struct {
			ID     int
			Roman  string
			Verses string
		}
	}{
		Books:        books,
		CurrentBook:  currentBook,
		CurrentChap:  currentChap,
		CyrilSermons: cyrilSermons,
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
	
	// Check if this is a request for all results
	showAll := r.URL.Query().Get("all") == "true"
	
	// Convert to lowercase for case-insensitive search
	searchTerm := strings.ToLower(query)
	
	// Define search result structure
	type SearchResult struct {
		BookID    string
		BookName  string
		Chapter   int
		VerseRef  string
		VerseText string
		IsGospel  bool
	}
	
	var allResults []SearchResult
	gospelBooks := map[string]bool{"matthew": true, "mark": true, "luke": true, "john": true}
	
	// Search through all books
	for _, book := range books {
		// Get book directory
		bookDir := filepath.Join("../texts/scripture/new_testament/english/kjv", book.ID)
		
		// Read all chapters for this book
		for chapter := 1; chapter <= book.Chapters; chapter++ {
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
				// Check if line contains search term
				if strings.Contains(strings.ToLower(line), searchTerm) {
					// Parse verse reference
					parts := strings.SplitN(line, " ", 2)
					if len(parts) == 2 {
						allResults = append(allResults, SearchResult{
							BookID:    book.ID,
							BookName:  book.Name,
							Chapter:   chapter,
							VerseRef:  parts[0],
							VerseText: parts[1],
							IsGospel:  gospelBooks[book.ID],
						})
					}
				}
			}
		}
	}
	
	// Build results HTML
	var results strings.Builder
	
	if showAll {
		// Return JSON for modal
		results.WriteString(`<div id="search-modal-content">`)
		for _, result := range allResults {
			highlightedText := result.VerseText
			re := regexp.MustCompile("(?i)" + regexp.QuoteMeta(query))
			highlightedText = re.ReplaceAllString(highlightedText, "<mark>$0</mark>")
			if len(highlightedText) > 200 {
				highlightedText = highlightedText[:200] + "..."
			}
			
			results.WriteString(fmt.Sprintf(`
				<div class="search-result-modal" 
					 style="padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; transition: background-color 0.2s;"
					 onmouseover="this.style.backgroundColor='#f5f5f5'" 
					 onmouseout="this.style.backgroundColor=''"
					 onclick="navigateFromModal('%s', %d); event.stopPropagation();">
					<div style="color: #3498db; font-weight: 500; margin-bottom: 4px; pointer-events: none;">%s %s</div>
					<div style="color: #666; font-size: 0.9em; line-height: 1.4; pointer-events: none;">%s</div>
				</div>
			`, result.BookID, result.Chapter, result.BookName, result.VerseRef, highlightedText))
		}
		results.WriteString(`</div>`)
	} else {
		// Regular search results - show all Gospel results
		results.WriteString(`<div class="search-results-list" style="max-height: 400px; overflow-y: auto; margin-top: 10px;">`)
		
		gospelCount := 0
		totalCount := len(allResults)
		
		// Show all Gospel results first
		for _, result := range allResults {
			if result.IsGospel {
				highlightedText := result.VerseText
				re := regexp.MustCompile("(?i)" + regexp.QuoteMeta(query))
				highlightedText = re.ReplaceAllString(highlightedText, "<mark>$0</mark>")
				if len(highlightedText) > 200 {
					highlightedText = highlightedText[:200] + "..."
				}
				
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
				`, result.BookID, result.Chapter, result.BookID, result.Chapter, result.BookName, result.VerseRef, highlightedText))
				
				gospelCount++
			}
		}
		
		// Show message based on results
		if totalCount == 0 {
			results.WriteString(`<div style="padding: 10px; color: #666;">No results found for "`)
			results.WriteString(html.EscapeString(query))
			results.WriteString(`"</div>`)
		} else if totalCount > gospelCount {
			// There are non-Gospel results
			results.WriteString(fmt.Sprintf(`
				<div style="padding: 10px; text-align: center; border-top: 1px solid #eee;">
					<div style="color: #666; margin-bottom: 8px;">Showing %d Gospel results</div>
					<a href="#" onclick="event.preventDefault(); showAllSearchResults('%s')" style="color: #3498db; text-decoration: none; font-weight: 500;">
						See all %d results from the New Testament →
					</a>
				</div>
			`, gospelCount, html.EscapeString(query), totalCount))
		}
		
		results.WriteString(`</div>`)
	}
	
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
						if homily.ID == lastNum {
							isDuplicate = true
							break
						}
					}
					if !isDuplicate {
						filteredHomilies = append(filteredHomilies, homily)
						currentHomilies = append(currentHomilies, homily.ID)
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
							if coverage, ok := comm.Coverage[homily.ID]; ok {
								if coverage.Start.Chapter == coverage.End.Chapter {
									if coverage.Start.Verse == coverage.End.Verse {
										passageRef = fmt.Sprintf(" (%d:%d)", coverage.Start.Chapter, coverage.Start.Verse)
									} else {
										passageRef = fmt.Sprintf(" (%d:%d-%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Verse)
									}
								} else {
									passageRef = fmt.Sprintf(" (%d:%d-%d:%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Chapter, coverage.End.Verse)
								}
							}
						}
						
						html.WriteString(fmt.Sprintf(`<a href="#" onclick="loadHomily(%d, '%s', '%s'); return false;" class="homily-ref" data-full-text="John Chrysostom, Homily %s on %s%s"></a>`, 
							homily.ID, homily.Roman, bookID, homily.Roman, bookTitle, passageRef))
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
						if homily.ID == -lastNum {
							isDuplicate = true
							break
						}
					}
					if !isDuplicate {
						filteredCyrilHomilies = append(filteredCyrilHomilies, homily)
						currentHomilies = append(currentHomilies, -homily.ID) // Store as negative to distinguish
					}
				}
				
				// Render Cyril's homilies
				if len(filteredCyrilHomilies) > 0 {
					html.WriteString(`<div class="homily-refs-container cyril">`)
					for _, homily := range filteredCyrilHomilies {
						// Get passage reference from coverage data
						passageRef := ""
						if comm, ok := commentaries["cyril-luke"]; ok {
							if coverage, ok := comm.Coverage[homily.ID]; ok {
								if coverage.Start.Chapter == coverage.End.Chapter {
									if coverage.Start.Verse == coverage.End.Verse {
										passageRef = fmt.Sprintf(" (%d:%d)", coverage.Start.Chapter, coverage.Start.Verse)
									} else {
										passageRef = fmt.Sprintf(" (%d:%d-%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Verse)
									}
								} else {
									passageRef = fmt.Sprintf(" (%d:%d-%d:%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Chapter, coverage.End.Verse)
								}
							}
						}
						
						html.WriteString(fmt.Sprintf(`<a href="#" onclick="loadCyrilHomily(%d, '%s', 'luke'); return false;" class="homily-ref cyril" data-full-text="Cyril of Alexandria, Sermon %s on Luke%s"></a>`, 
							homily.ID, homily.Roman, homily.Roman, passageRef))
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
			compareNum := homily.ID
			if author == "cyril" {
				compareNum = -homily.ID
			}
			if compareNum == lastNum {
				isDuplicate = true
				break
			}
		}
		if !isDuplicate {
			filteredHomilies = append(filteredHomilies, homily)
			if author == "cyril" {
				currentHomilies = append(currentHomilies, -homily.ID)
			} else {
				currentHomilies = append(currentHomilies, homily.ID)
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
					if coverage, ok := comm.Coverage[homily.ID]; ok {
						if coverage.Start.Chapter == coverage.End.Chapter {
							if coverage.Start.Verse == coverage.End.Verse {
								passageRef = fmt.Sprintf(" (%d:%d)", coverage.Start.Chapter, coverage.Start.Verse)
							} else {
								passageRef = fmt.Sprintf(" (%d:%d-%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Verse)
							}
						} else {
							passageRef = fmt.Sprintf(" (%d:%d-%d:%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Chapter, coverage.End.Verse)
						}
					}
				}
			}
			
			if author == "cyril" {
				onclick = fmt.Sprintf(`loadCyrilHomily(%d, '%s', '%s')`, homily.ID, homily.Roman, book)
				fullText = fmt.Sprintf("Cyril of Alexandria, Sermon %s on Luke%s", homily.Roman, passageRef)
			} else {
				onclick = fmt.Sprintf(`loadHomily(%d, '%s', '%s')`, homily.ID, homily.Roman, book)
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
	
	var html strings.Builder
	html.WriteString("<div class='canon-passages'>")

	// Order: Matthew, Mark, Luke, John
	gospelOrder := []string{"Matthew", "Mark", "Luke", "John"}
	for _, gospel := range gospelOrder {
		if verses, ok := passages[gospel]; ok {
			// Extract just the chapter.verse part from "section - chapter.verse"
			verseRef := verses
			if dashIdx := strings.Index(verses, " - "); dashIdx != -1 {
				verseRef = verses[dashIdx+3:]
			}

			// Convert chapter.verse format to chapter:verse
			verseRef = strings.ReplaceAll(verseRef, ".", ":")

			html.WriteString(fmt.Sprintf("<div class='passage'>"))
			html.WriteString(fmt.Sprintf("<h3>%s %s</h3>", gospel, verseRef))

			// Load the actual verse text
			verseText := loadVerseText(strings.ToLower(gospel), verses)
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
	// Parse verse reference like "8 - 3.3" or "1 - 1.1-16"
	// Format is: section_number - chapter.verse_range

	// Split on " - " to get the chapter.verse part
	dashParts := strings.Split(verseRef, " - ")
	if len(dashParts) != 2 {
		return ""
	}

	chapterVerse := dashParts[1]

	// Extract chapter and verse
	parts := strings.Split(chapterVerse, ".")
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
		// Extract homily text from pre-processed content files
		homilyText, verseRef, err = extractHomilyFromContent(author, book, homilyNum)
		if err != nil {
			log.Printf("Error extracting %s homily %d: %v", book, homilyNum, err)
			homilyText = "Error loading homily text."
		}
		authorName = "John Chrysostom"
	} else if author == "cyril" {
		// Extract sermon text from pre-processed content files
		homilyText, verseRef, err = extractHomilyFromContent(author, book, homilyNum)
		if err != nil {
			log.Printf("Error extracting Cyril sermon %d: %v", homilyNum, err)
			// Check if this is a missing sermon
			if strings.Contains(err.Error(), "no such file or directory") {
				homilyText = fmt.Sprintf("Sermon %s is not available in the current manuscript collection.", roman)
			} else {
				homilyText = "Error loading sermon text."
			}
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
	// Footnotes are now loaded from metadata.json files
	// Initialize empty maps for compatibility
	matthewFootnotesData = make(map[string]FootnoteData)
	johnFootnotesData = make(map[string]FootnoteData)
	cyrilLukeFootnotesData = make(map[string]FootnoteData)
	return nil
}

func loadScriptureReferences() {
	scriptureReferences = make(map[string][]ScriptureReference)

	// Load Matthew references
	matthewFile := "../texts/commentaries/chrysostom/matthew/references.json"
	if data, err := os.ReadFile(matthewFile); err == nil {
		var refs []ScriptureReference
		if err := json.Unmarshal(data, &refs); err == nil {
			scriptureReferences["matthew"] = refs
			log.Printf("Loaded %d scripture references for Matthew", len(refs))
		} else {
			log.Printf("Warning: Could not parse Matthew scripture references: %v", err)
		}
	} else {
		log.Printf("Warning: Could not load Matthew scripture references: %v", err)
	}

	// Load John references
	johnFile := "../texts/commentaries/chrysostom/john/references.json"
	if data, err := os.ReadFile(johnFile); err == nil {
		var refs []ScriptureReference
		if err := json.Unmarshal(data, &refs); err == nil {
			scriptureReferences["john"] = refs
			log.Printf("Loaded %d scripture references for John", len(refs))
		} else {
			log.Printf("Warning: Could not parse John scripture references: %v", err)
		}
	} else {
		log.Printf("Warning: Could not load John scripture references: %v", err)
	}
}


// extractHomilyFromContent reads from pre-processed content.json files
func extractHomilyFromContent(author, book string, homilyNum int) (string, string, error) {
	// Read from the new content structure
	contentPath := fmt.Sprintf("../texts/commentaries/%s/%s/content/%03d/content.json", author, book, homilyNum)
	
	contentData, err := os.ReadFile(contentPath)
	if err != nil {
		return "", "", fmt.Errorf("content not found for %s %s sermon/homily %d: %v", author, book, homilyNum, err)
	}
	log.Printf("Loading %s %s homily %d from JSON", author, book, homilyNum)
	
	var content struct {
		Title      string   `json:"title"`
		Subtitle   string   `json:"subtitle"`
		Paragraphs []string `json:"paragraphs"`
	}
	
	if err := json.Unmarshal(contentData, &content); err != nil {
		return "", "", err
	}
	
	// Load footnotes for this homily
	metadataPath := fmt.Sprintf("../texts/commentaries/%s/%s/content/%03d/metadata.json", author, book, homilyNum)
	metadataData, _ := os.ReadFile(metadataPath)
	
	var metadata struct {
		Footnotes map[string]string `json:"footnotes"`
	}
	json.Unmarshal(metadataData, &metadata)
	
	// Build HTML from paragraphs with proper footnote formatting
	var html strings.Builder
	for _, text := range content.Paragraphs {
		
		// Replace <sup>n</sup> with proper footnote formatting
		if metadata.Footnotes != nil {
			// Find all <sup>n</sup> tags and replace with proper attributes
			supPattern := regexp.MustCompile(`<sup>f?(\d+)</sup>`)
			text = supPattern.ReplaceAllStringFunc(text, func(match string) string {
				// Extract the number
				matches := supPattern.FindStringSubmatch(match)
				if len(matches) > 1 {
					num := matches[1]
					if footnote, ok := metadata.Footnotes[num]; ok {
						// Escape quotes in tooltip
						tooltip := strings.ReplaceAll(footnote, `"`, `&quot;`)
						tooltip = strings.ReplaceAll(tooltip, `<`, `&lt;`)
						tooltip = strings.ReplaceAll(tooltip, `>`, `&gt;`)
						return fmt.Sprintf(`<sup class="footnote-ref" data-tooltip="%s">%s</sup>`, tooltip, num)
					}
				}
				return match
			})
		}
		
		html.WriteString("<p>")
		html.WriteString(text)
		html.WriteString("</p>\n")
	}
	
	// Add endnotes section if there are footnotes
	if len(metadata.Footnotes) > 0 {
		html.WriteString(`<div class="footnotes">`)
		html.WriteString(`<h3>Notes</h3>`)
		html.WriteString(`<ul class="footnotes-list">`)
		
		// Sort footnote numbers
		var footnoteNums []int
		for numStr := range metadata.Footnotes {
			if num, err := strconv.Atoi(numStr); err == nil {
				footnoteNums = append(footnoteNums, num)
			}
		}
		sort.Ints(footnoteNums)
		
		// Add each footnote with manual numbering
		for _, num := range footnoteNums {
			numStr := strconv.Itoa(num)
			if footnote, ok := metadata.Footnotes[numStr]; ok {
				html.WriteString(fmt.Sprintf(`<li id="fn%d"><span class="footnote-number">%d.</span> %s</li>`, num, num, footnote))
			}
		}
		
		html.WriteString(`</ul>`)
		html.WriteString(`</div>`)
	}
	
	return html.String(), content.Subtitle, nil
}


// Removed extractHomilyFromXML and extractCyrilSermonFromHTML - server now uses only JSON files

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
	
	// First try to load verse reference from new metadata structure
	metadataPath := ""
	if author == "chrysostom" {
		metadataPath = fmt.Sprintf("../texts/commentaries/chrysostom/%s/content/%03d/metadata.json", book, homilyNum)
	} else if author == "cyril" {
		metadataPath = fmt.Sprintf("../texts/commentaries/cyril/%s/content/%03d/metadata.json", book, homilyNum)
	}
	
	// Try to load metadata for verse reference
	if metadataPath != "" {
		if metadataContent, err := os.ReadFile(metadataPath); err == nil {
			var metadata map[string]interface{}
			if err := json.Unmarshal(metadataContent, &metadata); err == nil {
				// Get verse reference from metadata
				if scriptureRef, ok := metadata["scripture_reference"].(map[string]interface{}); ok {
					if display, ok := scriptureRef["display"].(string); ok {
						verseRef = display
					}
				}
			}
		}
	}
	
	if author == "chrysostom" {
		// Extract homily text from pre-processed content files
		var xmlVerseRef string
		homilyText, xmlVerseRef, err = extractHomilyFromContent(author, book, homilyNum)
		// Use metadata verse ref if available, otherwise use extracted
		if verseRef == "" {
			verseRef = xmlVerseRef
		}
		if err != nil {
			log.Printf("Error extracting homily %d: %v", homilyNum, err)
			w.Header().Set("Content-Type", "text/html")
			w.Write([]byte("<p>Error loading homily text.</p>"))
			return
		}
	} else if author == "cyril" {
		// Extract sermon text from pre-processed content files
		var htmlVerseRef string
		homilyText, htmlVerseRef, err = extractHomilyFromContent(author, book, homilyNum)
		// Use metadata verse ref if available, otherwise use extracted
		if verseRef == "" {
			verseRef = htmlVerseRef
		}
		if err != nil {
			log.Printf("Error extracting Cyril sermon %d: %v", homilyNum, err)
			w.Header().Set("Content-Type", "text/html")
			// Check if this is a missing sermon
			if strings.Contains(err.Error(), "no such file or directory") {
				romanNum := intToRoman(homilyNum)
				w.Write([]byte(fmt.Sprintf("<div class=\"chapter-text\"><p style=\"text-align: center; color: #666;\">Sermon %s is not available in the current manuscript collection.</p></div>", romanNum)))
			} else {
				w.Write([]byte("<div class=\"chapter-text\"><p style=\"text-align: center; color: #666;\">Error loading sermon text.</p></div>"))
			}
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

func homiliesListHandler(w http.ResponseWriter, r *http.Request) {
	// Parse URL: /api/homilies/chrysostom/matthew or /api/homilies/cyril/luke
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/api/homilies/"), "/")
	if len(parts) != 2 {
		http.Error(w, "Invalid URL", http.StatusBadRequest)
		return
	}
	
	author := parts[0]
	book := parts[1]
	
	// Build the commentary key
	commKey := fmt.Sprintf("%s-%s", author, book)
	commentary, exists := commentaries[commKey]
	if !exists {
		http.Error(w, "Commentary not found", http.StatusNotFound)
		return
	}
	
	// Generate HTML for all homilies starting from 6 (since first 5 are shown)
	var html strings.Builder
	
	// Determine total count
	var total int
	if author == "chrysostom" && book == "matthew" {
		total = 90
	} else if author == "chrysostom" && book == "john" {
		total = 88
	} else if author == "cyril" && book == "luke" {
		total = 153
	} else {
		http.Error(w, "Unknown commentary", http.StatusNotFound)
		return
	}
	
	// For Cyril, get all available sermons dynamically
	availableSermons := []int{}
	if author == "cyril" {
		contentDir := "../texts/commentaries/cyril/luke/content"
		files, err := os.ReadDir(contentDir)
		if err == nil {
			for _, file := range files {
				if file.IsDir() {
					sermonNum := 0
					fmt.Sscanf(file.Name(), "%03d", &sermonNum)
					if sermonNum > 0 {
						availableSermons = append(availableSermons, sermonNum)
					}
				}
			}
		}
		sort.Ints(availableSermons)
		
		// Skip first 5 sermons (they're shown initially)
		if len(availableSermons) > 5 {
			availableSermons = availableSermons[5:]
		}
	} else {
		// For Chrysostom, generate all from 6 to total
		for i := 6; i <= total; i++ {
			availableSermons = append(availableSermons, i)
		}
	}
	
	// Generate HTML for each available sermon
	for _, i := range availableSermons {
		
		roman := intToRoman(i)
		
		// Get verse range from coverage data
		passageRef := ""
		if coverage, ok := commentary.Coverage[i]; ok {
			if coverage.Start.Chapter == coverage.End.Chapter {
				if coverage.Start.Verse == coverage.End.Verse {
					passageRef = fmt.Sprintf(" (%d:%d)", coverage.Start.Chapter, coverage.Start.Verse)
				} else {
					passageRef = fmt.Sprintf(" (%d:%d-%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Verse)
				}
			} else {
				passageRef = fmt.Sprintf(" (%d:%d-%d:%d)", coverage.Start.Chapter, coverage.Start.Verse, coverage.End.Chapter, coverage.End.Verse)
			}
		}
		
		// Generate the appropriate onclick handler
		if author == "cyril" {
			html.WriteString(fmt.Sprintf(`<li class="homily-item extra-item" onclick="loadCyrilHomily(%d, '%s', '%s'); return false;">Sermon %s%s</li>`,
				i, roman, book, roman, passageRef))
		} else {
			html.WriteString(fmt.Sprintf(`<li class="homily-item extra-item" onclick="loadHomily(%d, '%s', '%s'); return false;">Homily %s%s</li>`,
				i, roman, book, roman, passageRef))
		}
	}
	
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html.String()))
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
		<a href="https://www.ccel.org" target="_blank" style="white-space: nowrap;">Christian Classics Ethereal Library (CCEL)</a>.</p>
		
		<p><strong>Chrysostom Homilies on John</strong><br>
		The homilies of St. John Chrysostom on the Gospel of John are also sourced from the
		<em>Nicene and Post-Nicene Fathers</em> series, available through CCEL.</p>

		<p><strong>Cyril of Alexandria Sermons on Luke</strong><br>
		The 153 sermons of St. Cyril of Alexandria on the Gospel of Luke provide extensive
		patristic commentary on Luke's Gospel.</p>

		<p><strong>Gregory the Great's Forty Gospel Homilies</strong><br>
		Pope St. Gregory I's 40 homilies covering passages from all four Gospels, delivered
		in Rome during his papacy (590-604 AD).</p>

		<p><strong>Venerable Bede's Homilies on the Gospels</strong><br>
		The Venerable Bede's 50 homilies on the Gospels, organized in two books, covering
		passages from all four Gospels from the early medieval period in England.</p>

		<p><strong>Nikolai Velimirovich's Prologue of Ohrid</strong><br>
		St. Nikolai Velimirovich's daily meditations from the Prologue of Ohrid, featuring
		homilies on Scripture organized by calendar date (In progress).</p>

		<p><strong>Maximos the Confessor's On the Lord's Prayer</strong><br>
		St. Maximos the Confessor's treatise on the Lord's Prayer, providing spiritual
		commentary on both Matthew and Luke's accounts of the Our Father.</p>

		<h3>Features</h3>
		<ul>
			<li>Clean, distraction-free text reading</li>
			<li>Eusebian Canon references in the margins showing Gospel parallels</li>
			<li>Patristic commentary from John Chrysostom, Cyril of Alexandria, Gregory the Great, Venerable Bede, Nikolai Velimirovich, and Maximos the Confessor</li>
			<li>Commentary Index showing available homilies/sermons organized by Gospel book</li>
			<li>Cross-Gospel homily references via Eusebian canons</li>
			<li>Split-screen commentary viewing</li>
			<li>Responsive design for comfortable reading on any device</li>
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

func indexPageHandler(w http.ResponseWriter, r *http.Request) {
	// Make sure Eusebian Canon data is loaded
	if verseToCanon == nil {
		loadVerseToCanon()
	}

	type TableRow struct {
		Scripture     string
		Canon         string
		EusebianIndex string
		Parallels     string
		Father        string
		Work          string
		Section       string
		Book          string
		StartChapter  int
		StartVerse    int
		EndChapter    int
		EndVerse      int
		HomilyID      int
		Author        string
	}

	var tableRows []TableRow

	// Find all coverage.json files
	commentariesPath := "../texts/commentaries"
	authors := []struct {
		dir      string
		fullName string
		works    map[string]string
	}{
		{
			"chrysostom",
			"John Chrysostom",
			map[string]string{
				"matthew": "Homilies on Matthew",
				"john":    "Homilies on John",
			},
		},
		{
			"cyril",
			"Cyril of Alexandria",
			map[string]string{
				"luke": "Sermons on Luke",
			},
		},
		{
			"gregory_the_great",
			"Gregory the Great",
			map[string]string{
				"Forty Gospel Homilies": "Forty Gospel Homilies",
			},
		},
		{
			"bede",
			"Venerable Bede",
			map[string]string{
				"Homilies on the Gospels": "Homilies on the Gospels",
			},
		},
		{
			"nikolai",
			"Nikolai Velimirovich",
			map[string]string{
				"Prologue": "Prologue of Ohrid",
			},
		},
		{
			"maximos_the_confessor",
			"Maximos the Confessor",
			map[string]string{
				"On the Lord's Prayer": "On the Lord's Prayer",
			},
		},
	}

	for _, author := range authors {
		authorPath := filepath.Join(commentariesPath, author.dir)
		books, err := os.ReadDir(authorPath)
		if err != nil {
			continue
		}

		for _, book := range books {
			if book.IsDir() {
				coveragePath := filepath.Join(authorPath, book.Name(), "coverage.json")
				if _, err := os.Stat(coveragePath); err == nil {
					// Read coverage file
					data, err := os.ReadFile(coveragePath)
					if err != nil {
						continue
					}

					var coverage struct {
						Commentary string `json:"commentary"`
						Homilies   []struct {
							ID    int    `json:"id"`
							Roman string `json:"roman"`
							Title string `json:"title"`
							Start struct {
								Book    string `json:"book"`
								Chapter int    `json:"chapter"`
								Verse   int    `json:"verse"`
							} `json:"start"`
							End struct {
								Book    string `json:"book"`
								Chapter int    `json:"chapter"`
								Verse   int    `json:"verse"`
							} `json:"end"`
						} `json:"homilies"`
					}

					if err := json.Unmarshal(data, &coverage); err != nil {
						continue
					}

					work := author.works[book.Name()]

					// Add each homily/sermon as a row
					for _, h := range coverage.Homilies {
						// Determine book name from homily data if available, otherwise use directory name
						var bookNameLower string
						var bookName string
						if h.Start.Book != "" {
							bookNameLower = h.Start.Book
							bookName = strings.Title(h.Start.Book)
						} else {
							bookNameLower = strings.ToLower(book.Name())
							bookName = strings.Title(book.Name())
						}

						// Gospel abbreviations for Scripture column
						gospelAbbr := map[string]string{
							"Matthew": "Mt",
							"Mark":    "Mk",
							"Luke":    "Lk",
							"John":    "Jn",
						}
						bookAbbr := gospelAbbr[bookName]
						if bookAbbr == "" {
							bookAbbr = bookName
						}

						// Format scripture reference with abbreviations
						var scripture string
						if h.Start.Chapter == h.End.Chapter {
							if h.Start.Verse == h.End.Verse {
								scripture = fmt.Sprintf("%s %d:%d", bookAbbr, h.Start.Chapter, h.Start.Verse)
							} else {
								scripture = fmt.Sprintf("%s %d:%d-%d", bookAbbr, h.Start.Chapter, h.Start.Verse, h.End.Verse)
							}
						} else {
							scripture = fmt.Sprintf("%s %d:%d-%d:%d", bookAbbr, h.Start.Chapter, h.Start.Verse, h.End.Chapter, h.End.Verse)
						}

						eusebianIndex := getCanonAndSection(bookNameLower, h.Start.Chapter, h.Start.Verse)
						parallels := getParallels(bookNameLower, h.Start.Chapter, h.Start.Verse)

						tableRows = append(tableRows, TableRow{
							Scripture:     scripture,
							Canon:         "",
							EusebianIndex: eusebianIndex,
							Parallels:     parallels,
							Father:        author.fullName,
							Work:          work,
							Section:       h.Title,
							Book:          bookName,
							StartChapter:  h.Start.Chapter,
							StartVerse:    h.Start.Verse,
							EndChapter:    h.End.Chapter,
							EndVerse:      h.End.Verse,
							HomilyID:      h.ID,
							Author:        author.dir,
						})
					}
				}
			}
		}
	}

	// Sort by Bible book order, then chapter, then verse
	bookOrder := map[string]int{"Matthew": 1, "Mark": 2, "Luke": 3, "John": 4}
	sort.Slice(tableRows, func(i, j int) bool {
		// First sort by book order
		orderI, okI := bookOrder[tableRows[i].Book]
		orderJ, okJ := bookOrder[tableRows[j].Book]
		if okI && okJ && orderI != orderJ {
			return orderI < orderJ
		}
		// Then by start chapter
		if tableRows[i].StartChapter != tableRows[j].StartChapter {
			return tableRows[i].StartChapter < tableRows[j].StartChapter
		}
		// Then by start verse
		if tableRows[i].StartVerse != tableRows[j].StartVerse {
			return tableRows[i].StartVerse < tableRows[j].StartVerse
		}
		// Then by end chapter
		if tableRows[i].EndChapter != tableRows[j].EndChapter {
			return tableRows[i].EndChapter < tableRows[j].EndChapter
		}
		// Finally by end verse
		return tableRows[i].EndVerse < tableRows[j].EndVerse
	})

	// Build HTML with collapsible book sections
	html := `
	<div class="chapter-text" style="max-width: 900px; margin: 0 auto;">
		<style>
			.index-search-box {
				margin-bottom: 20px;
				padding: 12px;
				background: #f9f9f9;
				border: 1px solid #ddd;
				border-radius: 8px;
			}
			.index-search-box input {
				width: 100%;
				padding: 10px;
				border: 1px solid #ccc;
				border-radius: 4px;
				font-size: 14px;
			}
			.index-search-box input:focus {
				outline: none;
				border-color: #4a6da0;
			}
			.book-section {
				margin-bottom: 20px;
				border: 1px solid #ddd;
				border-radius: 8px;
				overflow: hidden;
			}
			.book-header {
				background: #4a6da0;
				color: white;
				padding: 12px 20px;
				cursor: pointer;
				display: flex;
				justify-content: space-between;
				align-items: center;
				font-size: 18px;
				font-weight: bold;
			}
			.book-header:hover {
				background: #3a5d90;
			}
			.book-header .arrow {
				transition: transform 0.3s;
			}
			.book-header.expanded .arrow {
				transform: rotate(90deg);
			}
			.book-content {
				display: none;
				overflow-x: auto;
			}
			.book-content.expanded {
				display: block;
			}
			.book-table {
				width: 100%;
				border-collapse: collapse;
			}
			.book-table th {
				background: #f5f5f5;
				text-align: left;
				padding: 10px;
				border: 1px solid #ddd;
				font-weight: bold;
			}
			.book-table td {
				padding: 10px;
				border: 1px solid #ddd;
			}
		</style>

		<div style="margin-bottom: 30px; padding: 20px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px;">
			<h3 style="margin-top: 0; margin-bottom: 15px;">Works Covered</h3>
			<table style="width: 100%; border-collapse: collapse;">
				<thead>
					<tr>
						<th style="text-align: left; padding: 8px; border-bottom: 2px solid #ddd;">Father</th>
						<th style="text-align: left; padding: 8px; border-bottom: 2px solid #ddd;"></th>
						<th style="text-align: left; padding: 8px; border-bottom: 2px solid #ddd;">Work</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">John Chrysostom</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">c. 347–407</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Homilies on Matthew</em></td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"></td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"></td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Homilies on John</em></td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">Cyril of Alexandria</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">c. 376–444</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Sermons on Luke</em></td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">Gregory the Great</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">c. 540–604</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Forty Gospel Homilies</em></td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">Maximos the Confessor</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">c. 580–662</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>On the Lord's Prayer</em></td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">Venerable Bede</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">c. 673–735</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Homilies on the Gospels</em></td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">Nikolai Velimirović</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">1880–1956</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Prologue of Ohrid</em> (in progress)</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div class="index-search-box">
			<input type="text" id="indexSearch" placeholder="Search for anything on this page" onkeyup="filterIndex()">
		</div>

		<script>
			function toggleBook(bookName) {
				const header = event.currentTarget;
				const content = header.nextElementSibling;
				header.classList.toggle('expanded');
				content.classList.toggle('expanded');
			}

			function filterIndex() {
				const searchTerm = document.getElementById('indexSearch').value.toLowerCase();
				const bookSections = document.querySelectorAll('.book-section');

				bookSections.forEach(section => {
					const rows = section.querySelectorAll('tbody tr');
					let visibleCount = 0;

					rows.forEach(row => {
						const text = row.textContent.toLowerCase();
						if (text.includes(searchTerm)) {
							row.style.display = '';
							visibleCount++;
						} else {
							row.style.display = 'none';
						}
					});

					// Show/hide entire book section based on whether it has visible rows
					if (visibleCount > 0) {
						section.style.display = '';
						// Auto-expand section if search is active and has results
						if (searchTerm.length > 0) {
							const header = section.querySelector('.book-header');
							const content = section.querySelector('.book-content');
							header.classList.add('expanded');
							content.classList.add('expanded');
						}
					} else {
						section.style.display = 'none';
					}
				});
			}
		</script>
	`

	// Group rows by book
	bookGroups := make(map[string][]TableRow)
	for _, row := range tableRows {
		bookGroups[row.Book] = append(bookGroups[row.Book], row)
	}

	// Sort books in canonical order
	bookOrderList := []string{"Matthew", "Mark", "Luke", "John"}
	for _, bookName := range bookOrderList {
		rows, exists := bookGroups[bookName]
		if !exists || len(rows) == 0 {
			continue
		}

		// Count unique commentaries for this book
		commentaryCount := len(rows)

		html += fmt.Sprintf(`
		<div class="book-section">
			<div class="book-header" onclick="toggleBook('%s')">
				<span>%s (%d commentaries)</span>
				<span class="arrow">▶</span>
			</div>
			<div class="book-content" id="book-%s">
				<table class="book-table">
					<thead>
						<tr>
							<th>Scripture</th>
							<th>Eusebian</th>
							<th>Parallel</th>
							<th>Father</th>
							<th>Work</th>
							<th>Section</th>
						</tr>
					</thead>
					<tbody>`, bookName, bookName, commentaryCount, bookName)

		for _, row := range rows {
			// Determine the homily/sermon link based on author
			var link string
			if row.Author == "gregory_the_great" || row.Author == "bede" || row.Author == "nikolai" || row.Author == "maximos_the_confessor" {
				// Gregory the Great, Bede, Nikolai, and Maximos - plain text, no link
				link = row.Section
			} else if row.Author == "cyril" {
				// Cyril sermons use negative IDs in the JavaScript
				link = fmt.Sprintf(`<a href="#" onclick="loadHomily(-%d, '%s', '%s'); return false;" style="color: #4a6da0; text-decoration: none;">%s</a>`,
					row.HomilyID, row.Section, strings.ToLower(row.Book), row.Section)
			} else {
				// Chrysostom homilies use positive IDs
				link = fmt.Sprintf(`<a href="#" onclick="loadHomily(%d, '%s', '%s'); return false;" style="color: #4a6da0; text-decoration: none;">%s</a>`,
					row.HomilyID, strings.TrimPrefix(row.Section, "Homily "), strings.ToLower(row.Book), row.Section)
			}

			html += fmt.Sprintf(`
						<tr>
							<td>%s</td>
							<td style="text-align: center;">%s</td>
							<td>%s</td>
							<td>%s</td>
							<td><i>%s</i></td>
							<td>%s</td>
						</tr>`, row.Scripture, row.EusebianIndex, row.Parallels, row.Father, row.Work, link)
		}

		html += `
					</tbody>
				</table>
			</div>
		</div>`
	}

	html += `

		<div style="margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
			<h4 style="margin-top: 0;">How to Use</h4>
			<p style="line-height: 1.6;">
				This page lists available Patristic commentaries organized by Scripture reference.
				References that are links are available to read online here (they also have blue markers
				next to passage in Scripture). Search for any Scripture reference, Church Father or
				available commentary using the search bar at top.
			</p>
		</div>
	</div>
	`

	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func scriptureReferencesHandler(w http.ResponseWriter, r *http.Request) {
	// Group references by book (only gospels)
	bookMap := make(map[string][]ScriptureReference)

	for _, refs := range scriptureReferences {
		for _, ref := range refs {
			if ref.Book == "Matthew" || ref.Book == "Mark" || ref.Book == "Luke" || ref.Book == "John" {
				bookMap[ref.Book] = append(bookMap[ref.Book], ref)
			}
		}
	}

	html := `
	<div class="chapter-text" style="max-width: 900px; margin: 0 auto;">
		<style>
			.index-search-box { margin-bottom: 20px; padding: 12px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; }
			.index-search-box input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }
			.index-search-box input:focus { outline: none; border-color: #4a6da0; }
			.book-section { margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
			.book-header { background: #4a6da0; color: white; padding: 12px 20px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-size: 18px; font-weight: bold; }
			.book-header:hover { background: #3a5d90; }
			.book-header .arrow { transition: transform 0.3s; }
			.book-header.expanded .arrow { transform: rotate(90deg); }
			.book-content { display: none; overflow-x: auto; }
			.book-content.expanded { display: block; }
			.book-table { width: 100%; border-collapse: collapse; }
			.book-table th { background: #f5f5f5; text-align: left; padding: 10px; border: 1px solid #ddd; font-weight: bold; }
			.book-table td { padding: 10px; border: 1px solid #ddd; }
		</style>

		<div style="margin-bottom: 30px; padding: 20px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px;">
			<h3 style="margin-top: 0; margin-bottom: 15px;">Works Covered</h3>
			<table style="width: 100%; border-collapse: collapse;">
				<thead>
					<tr>
						<th style="text-align: left; padding: 8px; border-bottom: 2px solid #ddd;">Father</th>
						<th style="text-align: left; padding: 8px; border-bottom: 2px solid #ddd;"></th>
						<th style="text-align: left; padding: 8px; border-bottom: 2px solid #ddd;">Work</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">John Chrysostom</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;">c. 347–407</td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Homilies on Matthew</em></td>
					</tr>
					<tr>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"></td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"></td>
						<td style="padding: 8px; border-bottom: 1px solid #eee;"><em>Homilies on John</em></td>
					</tr>
				</tbody>
			</table>
		</div>

		<div class="index-search-box">
			<input type="text" id="indexSearch" placeholder="Search for any verse or homily" onkeyup="filterIndex()">
		</div>

		<script>
			function toggleBook(bookName) {
				const header = event.currentTarget;
				const content = header.nextElementSibling;
				header.classList.toggle('expanded');
				content.classList.toggle('expanded');
			}

			function filterIndex() {
				const searchTerm = document.getElementById('indexSearch').value.toLowerCase();
				const bookSections = document.querySelectorAll('.book-section');
				bookSections.forEach(section => {
					const rows = section.querySelectorAll('tbody tr');
					let visibleCount = 0;
					rows.forEach(row => {
						const text = row.textContent.toLowerCase();
						if (text.includes(searchTerm)) {
							row.style.display = '';
							visibleCount++;
						} else {
							row.style.display = 'none';
						}
					});
					if (visibleCount > 0 && searchTerm) {
						section.querySelector('.book-content').classList.add('expanded');
						section.querySelector('.book-header').classList.add('expanded');
					}
				});
			}
		</script>
	`

	bookOrderList := []string{"Matthew", "Mark", "Luke", "John"}
	for _, bookName := range bookOrderList {
		refs, exists := bookMap[bookName]
		if !exists || len(refs) == 0 {
			continue
		}

		html += fmt.Sprintf(`
		<div class="book-section">
			<div class="book-header" onclick="toggleBook('%s')">
				<span>%s (%d references)</span>
				<span class="arrow">▶</span>
			</div>
			<div class="book-content" id="book-%s">
				<table class="book-table">
					<thead>
						<tr>
							<th>Scripture</th>
							<th>Father</th>
							<th>Work</th>
							<th>Section</th>
						</tr>
					</thead>
					<tbody>`, bookName, bookName, len(refs), bookName)

		for _, ref := range refs {
			work := "Homilies on Matthew"
			bookLower := "matthew"
			if strings.Contains(strings.ToLower(ref.Section), "john") {
				work = "Homilies on John"
				bookLower = "john"
			}

			link := fmt.Sprintf(`<a href="#" onclick="loadHomily(%d, '%s', '%s'); return false;" style="color: #4a6da0; text-decoration: none;">%s</a>`,
				ref.Homily, strings.TrimPrefix(ref.Section, "Homily "), bookLower, ref.Section)

			html += fmt.Sprintf(`
						<tr>
							<td>%s %s</td>
							<td>John Chrysostom</td>
							<td>%s</td>
							<td>%s</td>
						</tr>`, bookName, ref.Reference, work, link)
		}

		html += `
					</tbody>
				</table>
			</div>
		</div>
		`
	}

	html += `</div>`
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}


