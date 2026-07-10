package apiv1

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// commentaryText is the full text embedded in a coverage result (include_text=true).
type commentaryText struct {
	Subtitle        string            `json:"subtitle,omitempty"`
	Paragraphs      []string          `json:"paragraphs"`
	TotalParagraphs int               `json:"total_paragraphs"`
	Footnotes       map[string]string `json:"footnotes,omitempty"`
}

type commentaryContent struct {
	CommentaryID    string            `json:"commentary_id"`
	Author          string            `json:"author"`
	AuthorFull      string            `json:"author_full"`
	Work            string            `json:"work"`
	ID              int               `json:"id"`
	Roman           string            `json:"roman"`
	Title           string            `json:"title"`
	Subtitle        string            `json:"subtitle,omitempty"`
	Covers          string            `json:"covers,omitempty"`
	Paragraphs      []string          `json:"paragraphs"`
	TotalParagraphs int               `json:"total_paragraphs"`
	Footnotes       map[string]string `json:"footnotes,omitempty"`
	TextAvailable   bool              `json:"text_available"`
}

var supPattern = regexp.MustCompile(`<sup>f?(\d+)</sup>`)

// loadContent reads content.json + metadata.json for a homily/sermon.
func loadContent(w *work, id int) (*commentaryContent, error) {
	base := filepath.Join(textsDir, "commentaries", w.Dir, "content", fmt.Sprintf("%03d", id))

	raw, err := os.ReadFile(filepath.Join(base, "content.json"))
	if err != nil {
		return nil, err
	}
	var c struct {
		Title      string   `json:"title"`
		Subtitle   string   `json:"subtitle"`
		Paragraphs []string `json:"paragraphs"`
	}
	if err := json.Unmarshal(raw, &c); err != nil {
		return nil, err
	}

	var meta struct {
		Footnotes map[string]string `json:"footnotes"`
	}
	if md, err := os.ReadFile(filepath.Join(base, "metadata.json")); err == nil {
		json.Unmarshal(md, &meta)
	}

	out := &commentaryContent{
		CommentaryID:    fmt.Sprintf("%s/%s/%d", w.Author, w.WorkSlug, id),
		Author:          w.Author,
		AuthorFull:      w.AuthorFull,
		Work:            w.WorkTitle,
		ID:              id,
		Title:           c.Title,
		Subtitle:        c.Subtitle,
		Paragraphs:      c.Paragraphs,
		TotalParagraphs: len(c.Paragraphs),
		Footnotes:       meta.Footnotes,
		TextAvailable:   true,
	}
	for _, r := range w.ranges {
		if r.ID == id {
			out.Roman = r.Roman
			if out.Title == "" {
				out.Title = r.Title
			}
			out.Covers = coversDisplay(w, r)
			break
		}
	}
	return out, nil
}

// slice applies 1-based inclusive paragraph paging, clamping to bounds.
func (c *commentaryContent) slice(start, end int) {
	n := len(c.Paragraphs)
	if start <= 0 && end <= 0 {
		return
	}
	if start <= 0 {
		start = 1
	}
	if end <= 0 || end > n {
		end = n
	}
	if start > n {
		c.Paragraphs = []string{}
		return
	}
	if end < start {
		end = start
	}
	c.Paragraphs = c.Paragraphs[start-1 : end]
}

// renderHTML reproduces the fragment the web app injects (format=html).
func (c *commentaryContent) renderHTML() string {
	var b strings.Builder
	b.WriteString(`<div class="chapter-text">`)
	if c.Subtitle != "" {
		b.WriteString(fmt.Sprintf(`<p class="verse-reference" style="text-align: center; color: #666; font-style: italic; margin-bottom: 20px;">%s</p>`, c.Subtitle))
	}
	for _, text := range c.Paragraphs {
		if c.Footnotes != nil {
			text = supPattern.ReplaceAllStringFunc(text, func(match string) string {
				m := supPattern.FindStringSubmatch(match)
				if len(m) > 1 {
					if fn, ok := c.Footnotes[m[1]]; ok {
						tip := strings.ReplaceAll(fn, `"`, `&quot;`)
						tip = strings.ReplaceAll(tip, `<`, `&lt;`)
						tip = strings.ReplaceAll(tip, `>`, `&gt;`)
						return fmt.Sprintf(`<sup class="footnote-ref" data-tooltip="%s">%s</sup>`, tip, m[1])
					}
				}
				return match
			})
		}
		b.WriteString("<p>")
		b.WriteString(text)
		b.WriteString("</p>\n")
	}
	if len(c.Footnotes) > 0 {
		b.WriteString(`<div class="footnotes"><h3>Notes</h3><ul class="footnotes-list">`)
		var nums []int
		for k := range c.Footnotes {
			if n, err := strconv.Atoi(k); err == nil {
				nums = append(nums, n)
			}
		}
		sort.Ints(nums)
		for _, n := range nums {
			k := strconv.Itoa(n)
			b.WriteString(fmt.Sprintf(`<li id="fn%d"><span class="footnote-number">%d.</span> %s</li>`, n, n, c.Footnotes[k]))
		}
		b.WriteString(`</ul></div>`)
	}
	b.WriteString(`</div>`)
	return b.String()
}
