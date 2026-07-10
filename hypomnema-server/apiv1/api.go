package apiv1

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
)

//go:embed openapi.yaml
var openapiYAML []byte

//go:embed docs.html
var docsHTML []byte

// Init loads the commentary indexes into memory. Call once at startup.
func Init() {
	loadStore()
}

// Handler returns the v1 API router. Mount it under the desired public prefix,
// e.g. http.Handle("/api/v1/", http.StripPrefix("/api/v1", apiv1.Handler())).
func Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/coverage", coverageHandler)
	mux.HandleFunc("/commentary/", commentaryHandler)
	mux.HandleFunc("/openapi.yaml", openapiHandler)
	mux.HandleFunc("/docs", docsHandler)
	return cors(mux)
}

func cors(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		if r.Method != http.MethodGet {
			writeError(w, http.StatusMethodNotAllowed, "method_not_allowed", "Only GET is supported.")
			return
		}
		h.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, code, msg string) {
	writeJSON(w, status, map[string]string{"error": code, "message": msg})
}

var refPattern = regexp.MustCompile(`^(.*?)(\d+)\s*[:.]\s*(\d+)\s*$`)

func parseRef(ref string) (book string, chapter, verse int, ok bool) {
	m := refPattern.FindStringSubmatch(strings.TrimSpace(ref))
	if m == nil {
		return "", 0, 0, false
	}
	book = strings.TrimSpace(m[1])
	chapter, _ = strconv.Atoi(m[2])
	verse, _ = strconv.Atoi(m[3])
	return book, chapter, verse, book != ""
}

func coverageHandler(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	bookInput := q.Get("book")
	chapterStr := q.Get("chapter")
	verseStr := q.Get("verse")

	if ref := q.Get("ref"); ref != "" && bookInput == "" {
		b, ch, vs, ok := parseRef(ref)
		if !ok {
			writeError(w, http.StatusBadRequest, "bad_ref", "Could not parse ref; expected e.g. 'John 3:16'.")
			return
		}
		bookInput = b
		chapterStr = strconv.Itoa(ch)
		verseStr = strconv.Itoa(vs)
	}

	if bookInput == "" {
		writeError(w, http.StatusBadRequest, "missing_book", "Provide 'book' (and chapter/verse) or 'ref'.")
		return
	}
	slug, display, ok := normalizeBook(bookInput)
	if !ok {
		writeError(w, http.StatusBadRequest, "unknown_book",
			fmt.Sprintf("Unknown book %q. Valid books: %s.", bookInput, strings.Join(validBookNames(), ", ")))
		return
	}
	chapter, err1 := strconv.Atoi(chapterStr)
	verse, err2 := strconv.Atoi(verseStr)
	if err1 != nil || err2 != nil || chapter < 1 || verse < 1 {
		writeError(w, http.StatusBadRequest, "bad_reference", "chapter and verse must be positive integers.")
		return
	}

	includeText := true
	if v := q.Get("include_text"); v != "" {
		if b, err := strconv.ParseBool(v); err == nil {
			includeText = b
		}
	}

	results := coverageFor(slug, chapter, verse, includeText)
	if results == nil {
		results = []coverageResult{}
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"query": map[string]interface{}{
			"book": slug, "book_display": display, "chapter": chapter, "verse": verse,
		},
		"count":   len(results),
		"results": results,
	})
}

func commentaryHandler(w http.ResponseWriter, r *http.Request) {
	rest := strings.TrimPrefix(r.URL.Path, "/commentary/")
	parts := strings.Split(rest, "/")
	if len(parts) != 3 || parts[0] == "" || parts[1] == "" || parts[2] == "" {
		writeError(w, http.StatusBadRequest, "bad_path", "Expected /commentary/{author}/{work}/{id}.")
		return
	}
	author, workSlug, idStr := parts[0], parts[1], parts[2]

	wk := findWork(author, workSlug)
	if wk == nil {
		writeError(w, http.StatusNotFound, "not_found", "No such commentary work.")
		return
	}
	id, err := strconv.Atoi(idStr)
	if err != nil || id < 1 {
		writeError(w, http.StatusBadRequest, "bad_id", "Commentary id must be a positive integer.")
		return
	}

	if !wk.TextTier {
		citation := map[string]interface{}{
			"commentary_id": fmt.Sprintf("%s/%s/%d", wk.Author, wk.WorkSlug, id),
			"author":        wk.Author,
			"author_full":   wk.AuthorFull,
			"work":          wk.WorkTitle,
			"work_slug":     wk.WorkSlug,
			"id":            id,
		}
		for _, rg := range wk.ranges {
			if rg.ID == id {
				citation["roman"] = rg.Roman
				citation["title"] = rg.Title
				citation["covers"] = coversDisplay(wk, rg)
			}
		}
		writeJSON(w, http.StatusNotFound, map[string]interface{}{
			"error":    "text_not_available",
			"message":  fmt.Sprintf("Full text for %s is not included in this dataset; only the citation is available.", wk.WorkTitle),
			"citation": citation,
		})
		return
	}

	content, err := loadContent(wk, id)
	if err != nil {
		writeError(w, http.StatusNotFound, "not_found", fmt.Sprintf("Commentary %s/%s/%d not found.", author, workSlug, id))
		return
	}

	q := r.URL.Query()
	start, _ := strconv.Atoi(q.Get("paragraph_start"))
	end, _ := strconv.Atoi(q.Get("paragraph_end"))
	content.slice(start, end)

	if q.Get("format") == "html" {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Write([]byte(content.renderHTML()))
		return
	}
	writeJSON(w, http.StatusOK, content)
}

func openapiHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/yaml; charset=utf-8")
	w.Write(openapiYAML)
}

func docsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write(docsHTML)
}
