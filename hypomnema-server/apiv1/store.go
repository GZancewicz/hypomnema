package apiv1

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
)

type verseRef struct {
	Book    string `json:"book"`
	Chapter int    `json:"chapter"`
	Verse   int    `json:"verse"`
}

type homilyRange struct {
	ID    int      `json:"id"`
	Roman string   `json:"roman"`
	Title string   `json:"title"`
	Date  string   `json:"date"`
	Saint string   `json:"saint"`
	Start verseRef `json:"start"`
	End   verseRef `json:"end"`
}

type mappingEntry struct {
	ID    int    `json:"id"`
	Roman string `json:"roman"`
	Type  string `json:"type"`
}

// work is one commentary (author + work), matching a directory under texts/commentaries.
type work struct {
	Author      string // slug, e.g. "chrysostom"
	AuthorFull  string
	WorkSlug    string // url slug, e.g. "matthew", "forty-gospel-homilies"
	WorkTitle   string
	Dir         string // path under texts/commentaries, e.g. "gregory_the_great/Forty Gospel Homilies"
	DefaultBook string // book slug for single-book works; fallback for entries missing a book
	MultiBook   bool   // entries carry their own book field
	TextTier    bool   // true = full text retrievable
	Calendar    bool   // carries date/saint (Synaxarion)

	ranges  []homilyRange
	mapping map[string][]mappingEntry // "ch:vs" -> entries; only for single-book Tier-1 works
}

var catalog = []*work{
	{Author: "chrysostom", AuthorFull: "John Chrysostom", WorkSlug: "matthew", WorkTitle: "Homilies on Matthew", Dir: "chrysostom/matthew", DefaultBook: "matthew", TextTier: true},
	{Author: "chrysostom", AuthorFull: "John Chrysostom", WorkSlug: "john", WorkTitle: "Homilies on John", Dir: "chrysostom/john", DefaultBook: "john", TextTier: true},
	{Author: "cyril", AuthorFull: "Cyril of Alexandria", WorkSlug: "luke", WorkTitle: "Sermons on Luke", Dir: "cyril/luke", DefaultBook: "luke", TextTier: true},
	{Author: "gregory_the_great", AuthorFull: "Gregory the Great", WorkSlug: "forty-gospel-homilies", WorkTitle: "Forty Gospel Homilies", Dir: "gregory_the_great/Forty Gospel Homilies", MultiBook: true},
	{Author: "bede", AuthorFull: "Venerable Bede", WorkSlug: "homilies-on-the-gospels", WorkTitle: "Homilies on the Gospels", Dir: "bede/Homilies on the Gospels", MultiBook: true},
	{Author: "maximos_the_confessor", AuthorFull: "Maximos the Confessor", WorkSlug: "on-the-lords-prayer", WorkTitle: "On the Lord's Prayer", Dir: "maximos_the_confessor/On the Lord's Prayer", MultiBook: true},
	{Author: "theophylact", AuthorFull: "Theophylact of Ohrid", WorkSlug: "matthew", WorkTitle: "Explanation of the Holy Gospel According to Matthew", Dir: "theophylact/matthew", DefaultBook: "matthew"},
	// Nikolai: text on disk but licensing forbids distribution -> TextTier false, never served.
	{Author: "nikolai", AuthorFull: "Nikolai Velimirović", WorkSlug: "prologue", WorkTitle: "The Prologue of Ohrid", Dir: "nikolai/Prologue", MultiBook: true},
	{Author: "synaxarion", AuthorFull: "The Synaxarion", WorkSlug: "synaxarion", WorkTitle: "The Synaxarion", Dir: "synaxarion", MultiBook: true, Calendar: true},
}

var textsDir string

func resolveTextsDir() string {
	if d := os.Getenv("HYPOMNEMA_TEXTS_DIR"); d != "" {
		return d
	}
	return "../texts"
}

func loadStore() {
	textsDir = resolveTextsDir()
	for _, w := range catalog {
		loadWork(w)
	}
}

func loadWork(w *work) {
	base := filepath.Join(textsDir, "commentaries", w.Dir)

	covPath := filepath.Join(base, "coverage.json")
	data, err := os.ReadFile(covPath)
	if err != nil {
		log.Printf("warning: %s: could not read coverage: %v", w.Dir, err)
		return
	}
	var cov struct {
		Homilies []homilyRange `json:"homilies"`
	}
	if err := json.Unmarshal(data, &cov); err != nil {
		log.Printf("warning: %s: could not parse coverage: %v", w.Dir, err)
		return
	}
	w.ranges = cov.Homilies

	if w.TextTier && !w.MultiBook {
		mapPath := filepath.Join(base, "verse_mapping.json")
		if md, err := os.ReadFile(mapPath); err == nil {
			var m map[string][]mappingEntry
			if err := json.Unmarshal(md, &m); err == nil {
				w.mapping = m
			}
		}
	}
	log.Printf("loaded %s/%s: %d homilies (text=%v)", w.Author, w.WorkSlug, len(w.ranges), w.TextTier)
}

func rangeContains(r homilyRange, chapter, verse int) bool {
	if chapter < r.Start.Chapter || chapter > r.End.Chapter {
		return false
	}
	if chapter == r.Start.Chapter && verse < r.Start.Verse {
		return false
	}
	if chapter == r.End.Chapter && verse > r.End.Verse {
		return false
	}
	return true
}

func (w *work) entryBook(r homilyRange) string {
	if r.Start.Book != "" {
		return r.Start.Book
	}
	return w.DefaultBook
}

func coversDisplay(w *work, r homilyRange) string {
	disp := bookDisplay(w.entryBook(r))
	s, e := r.Start, r.End
	switch {
	case s.Chapter == e.Chapter && s.Verse == e.Verse:
		return fmt.Sprintf("%s %d:%d", disp, s.Chapter, s.Verse)
	case s.Chapter == e.Chapter:
		return fmt.Sprintf("%s %d:%d-%d", disp, s.Chapter, s.Verse, e.Verse)
	default:
		return fmt.Sprintf("%s %d:%d-%d:%d", disp, s.Chapter, s.Verse, e.Chapter, e.Verse)
	}
}

func (w *work) workByAuthorSlug(author, workSlug string) bool {
	return w.Author == author && w.WorkSlug == workSlug
}

func findWork(author, workSlug string) *work {
	for _, w := range catalog {
		if w.workByAuthorSlug(author, workSlug) {
			return w
		}
	}
	return nil
}

// coverageResult is one row of the /v1/coverage response.
type coverageResult struct {
	CommentaryID  string `json:"commentary_id"`
	Author        string `json:"author"`
	AuthorFull    string `json:"author_full"`
	Work          string `json:"work"`
	WorkSlug      string `json:"work_slug"`
	ID            int    `json:"id"`
	Roman         string `json:"roman"`
	Title         string `json:"title"`
	Covers        string `json:"covers"`
	MatchType     string `json:"match_type"`
	TextAvailable bool            `json:"text_available"`
	Date          string          `json:"date,omitempty"`
	Saint         string          `json:"saint,omitempty"`
	Text          *commentaryText `json:"text,omitempty"`
}

// coverageFor returns every commentary covering book/chapter/verse.
// When includeText is set, text-available results carry the full commentary.
func coverageFor(bookSlug string, chapter, verse int, includeText bool) []coverageResult {
	var out []coverageResult
	key := fmt.Sprintf("%d:%d", chapter, verse)

	for _, w := range catalog {
		// Primary IDs from verse_mapping (single-book Tier-1 works only).
		primary := map[int]bool{}
		if w.mapping != nil && w.DefaultBook == bookSlug {
			for _, e := range w.mapping[key] {
				primary[e.ID] = true
			}
		}
		for _, r := range w.ranges {
			if w.entryBook(r) != bookSlug {
				continue
			}
			if !rangeContains(r, chapter, verse) {
				continue
			}
			res := coverageResult{
				CommentaryID:  fmt.Sprintf("%s/%s/%d", w.Author, w.WorkSlug, r.ID),
				Author:        w.Author,
				AuthorFull:    w.AuthorFull,
				Work:          w.WorkTitle,
				WorkSlug:      w.WorkSlug,
				ID:            r.ID,
				Roman:         r.Roman,
				Title:         r.Title,
				Covers:        coversDisplay(w, r),
				MatchType:     "range",
				TextAvailable: w.TextTier,
			}
			if primary[r.ID] {
				res.MatchType = "primary"
			}
			if w.Calendar {
				res.Date = r.Date
				res.Saint = r.Saint
			}
			if includeText && w.TextTier {
				if c, err := loadContent(w, r.ID); err == nil {
					res.Text = &commentaryText{
						Subtitle:        c.Subtitle,
						Paragraphs:      c.Paragraphs,
						TotalParagraphs: c.TotalParagraphs,
						Footnotes:       c.Footnotes,
					}
				}
			}
			out = append(out, res)
		}
	}

	sort.SliceStable(out, func(i, j int) bool {
		if out[i].Author != out[j].Author {
			return out[i].Author < out[j].Author
		}
		if out[i].WorkSlug != out[j].WorkSlug {
			return out[i].WorkSlug < out[j].WorkSlug
		}
		return out[i].ID < out[j].ID
	})
	return out
}
