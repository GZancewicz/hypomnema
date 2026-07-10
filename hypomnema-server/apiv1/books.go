package apiv1

import "strings"

type bookDef struct {
	Slug    string
	Display string
	Aliases []string
}

var bookDefs = []bookDef{
	{"matthew", "Matthew", []string{"mt", "matt", "matth"}},
	{"mark", "Mark", []string{"mk", "mr", "mrk"}},
	{"luke", "Luke", []string{"lk", "luk"}},
	{"john", "John", []string{"jn", "joh", "jhn"}},
	{"acts", "Acts", []string{"ac", "act"}},
	{"romans", "Romans", []string{"rom", "ro", "rm"}},
	{"1corinthians", "1 Corinthians", []string{"1cor", "1co", "1corinth", "icorinthians", "icor"}},
	{"2corinthians", "2 Corinthians", []string{"2cor", "2co", "2corinth", "iicorinthians", "iicor"}},
	{"galatians", "Galatians", []string{"gal", "ga"}},
	{"ephesians", "Ephesians", []string{"eph", "ephes"}},
	{"philippians", "Philippians", []string{"phil", "php", "pp"}},
	{"colossians", "Colossians", []string{"col", "co"}},
	{"1thessalonians", "1 Thessalonians", []string{"1thess", "1th", "1thes", "ithessalonians"}},
	{"2thessalonians", "2 Thessalonians", []string{"2thess", "2th", "2thes", "iithessalonians"}},
	{"1timothy", "1 Timothy", []string{"1tim", "1ti", "itimothy"}},
	{"2timothy", "2 Timothy", []string{"2tim", "2ti", "iitimothy"}},
	{"titus", "Titus", []string{"tit", "ti"}},
	{"philemon", "Philemon", []string{"philem", "phm", "phlm"}},
	{"hebrews", "Hebrews", []string{"heb", "hebr"}},
	{"james", "James", []string{"jas", "jm"}},
	{"1peter", "1 Peter", []string{"1pet", "1pe", "1pt", "ipeter"}},
	{"2peter", "2 Peter", []string{"2pet", "2pe", "2pt", "iipeter"}},
	{"1john", "1 John", []string{"1jn", "1jo", "1joh", "ijohn"}},
	{"2john", "2 John", []string{"2jn", "2jo", "2joh", "iijohn"}},
	{"3john", "3 John", []string{"3jn", "3jo", "3joh", "iiijohn"}},
	{"jude", "Jude", []string{"jud", "jd"}},
	{"revelation", "Revelation", []string{"rev", "re", "apoc", "apocalypse"}},
}

var bookLookup = func() map[string]bookDef {
	m := make(map[string]bookDef)
	add := func(k string, d bookDef) { m[normalizeKey(k)] = d }
	for _, d := range bookDefs {
		add(d.Slug, d)
		add(d.Display, d)
		for _, a := range d.Aliases {
			add(a, d)
		}
	}
	return m
}()

// normalizeKey lowercases and strips spaces, periods, and a leading "saint"/"st".
func normalizeKey(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	s = strings.ReplaceAll(s, ".", "")
	s = strings.ReplaceAll(s, " ", "")
	s = strings.TrimPrefix(s, "saint")
	s = strings.TrimPrefix(s, "st")
	return s
}

// normalizeBook resolves a full name, slug, or abbreviation to a canonical book.
func normalizeBook(input string) (slug, display string, ok bool) {
	d, found := bookLookup[normalizeKey(input)]
	if !found {
		return "", "", false
	}
	return d.Slug, d.Display, true
}

func validBookNames() []string {
	names := make([]string, len(bookDefs))
	for i, d := range bookDefs {
		names[i] = d.Display
	}
	return names
}

func bookDisplay(slug string) string {
	for _, d := range bookDefs {
		if d.Slug == slug {
			return d.Display
		}
	}
	return slug
}
