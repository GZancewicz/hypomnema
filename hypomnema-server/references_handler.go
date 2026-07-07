package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"sort"
	"strconv"
	"strings"
)

func loadSectionDataForHandler(gospel string) (map[int]string, error) {
	sections, ok := sectionData[gospel]
	if !ok {
		return nil, fmt.Errorf("no section data for %s", gospel)
	}

	sectionMap := make(map[int]string)
	for _, s := range sections {
		sectionMap[s.Section] = s.Reference
	}

	return sectionMap, nil
}

func referencesHandler(w http.ResponseWriter, r *http.Request) {
	// Load harmony data
	harmonyData, err := ioutil.ReadFile("../texts/reference/eusebian_canons/harmony.json")
	if err != nil {
		http.Error(w, "Failed to load harmony data", http.StatusInternalServerError)
		return
	}

	var harmony []HarmonyEntry
	if err := json.Unmarshal(harmonyData, &harmony); err != nil {
		http.Error(w, "Failed to parse harmony data", http.StatusInternalServerError)
		return
	}

	// Load section data for each gospel
	matthewSections, _ := loadSectionDataForHandler("matthew")
	markSections, _ := loadSectionDataForHandler("mark")
	lukeSections, _ := loadSectionDataForHandler("luke")
	johnSections, _ := loadSectionDataForHandler("john")

	// Build HTML for Gospel Harmony
	html := `
	<div class="chapter-text" style="max-width: 1200px; margin: 0 auto;">
		<h2 style="text-align: center; margin-bottom: 30px;">HARMONY OF THE GOSPELS</h2>

		<p style="text-align: center; color: #666; margin-bottom: 30px;">
			The Eusebian Canons are a system of cross-references for the four Gospels,
			created by Eusebius of Caesarea in the early 4th century. Each canon groups
			passages that appear in different combinations of the Gospels.
		</p>

		<style>
			.canon-section {
				margin-bottom: 30px;
				border: 1px solid #ddd;
				border-radius: 8px;
				overflow: hidden;
			}
			.canon-header {
				background: #4a6da0;
				color: white;
				padding: 10px 15px;
				font-weight: bold;
				cursor: pointer;
				display: flex;
				justify-content: space-between;
				align-items: center;
			}
			.canon-header:hover {
				background: #3a5d90;
			}
			.canon-content {
				padding: 15px;
				display: none;
			}
			.canon-content.expanded {
				display: block;
			}
			.canon-header .arrow {
				transition: transform 0.3s;
			}
			.canon-header.expanded .arrow {
				transform: rotate(90deg);
			}
			.canon-table {
				width: 100%;
				border-collapse: collapse;
			}
			.canon-table th {
				background: #f5f5f5;
				text-align: left;
				padding: 8px;
				border: 1px solid #ddd;
				font-weight: bold;
			}
			.canon-table td {
				padding: 8px;
				border: 1px solid #ddd;
				vertical-align: top;
			}
			.canon-description {
				background: #f9f9f9;
				padding: 10px;
				margin-bottom: 10px;
				border-left: 3px solid #4a6da0;
			}
		</style>
		<script>
			function toggleCanon(canonNum) {
				const header = event.currentTarget;
				const content = header.nextElementSibling;
				header.classList.toggle('expanded');
				content.classList.toggle('expanded');
			}
		</script>

		<div class="canon-description">
			<strong>Canon I:</strong> Passages common to all four Gospels<br>
			<strong>Canon II:</strong> Passages in Matthew, Mark, and Luke<br>
			<strong>Canon III:</strong> Passages in Matthew, Luke, and John<br>
			<strong>Canon IV:</strong> Passages in Matthew, Mark, and John<br>
			<strong>Canon V:</strong> Passages in Matthew and Luke<br>
			<strong>Canon VI:</strong> Passages in Matthew and Mark<br>
			<strong>Canon VII:</strong> Passages in Matthew and John<br>
			<strong>Canon VIII:</strong> Passages in Luke and Mark<br>
			<strong>Canon IX:</strong> Passages in Luke and John<br>
			<strong>Canon X:</strong> Passages unique to each Gospel (subdivided by Gospel)
		</div>
	`

	// Group harmony entries by canon type
	canonGroups := make(map[string][]HarmonyEntry)
	for _, entry := range harmony {
		canonGroups[entry.Canon] = append(canonGroups[entry.Canon], entry)
	}

	// Sort canon types
	var canonTypes []string
	for ct := range canonGroups {
		canonTypes = append(canonTypes, ct)
	}

	// Custom sort for Roman numerals
	romanOrder := map[string]int{
		"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
		"VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
		"XI": 11, "XII": 12, "XIII": 13,
	}
	sort.Slice(canonTypes, func(i, j int) bool {
		orderI, okI := romanOrder[canonTypes[i]]
		orderJ, okJ := romanOrder[canonTypes[j]]
		if okI && okJ {
			return orderI < orderJ
		}
		return canonTypes[i] < canonTypes[j]
	})

	// Build sections for each canon type
	for _, canonType := range canonTypes {
		entries := canonGroups[canonType]

		html += fmt.Sprintf(`
		<div class="canon-section">
			<div class="canon-header" onclick="toggleCanon('%s')">
				<span>Canon %s (%d entries)</span>
				<span class="arrow">▶</span>
			</div>
			<div class="canon-content" id="canon-%s">
				<table class="canon-table">
					<thead>
						<tr>
							<th width="25%%">Matthew</th>
							<th width="25%%">Mark</th>
							<th width="25%%">Luke</th>
							<th width="25%%">John</th>
						</tr>
					</thead>
					<tbody>`, canonType, canonType, len(entries), canonType)

		for _, entry := range entries {
			matthew := ""
			mark := ""
			luke := ""
			john := ""

			// Get section numbers and verse references
			if sect, ok := entry.Sections["Matthew"]; ok && sect > 0 {
				if ref, exists := matthewSections[sect]; exists {
					matthew = fmt.Sprintf("(%d) %s", sect, ref)
				}
			}
			if sect, ok := entry.Sections["Mark"]; ok && sect > 0 {
				if ref, exists := markSections[sect]; exists {
					mark = fmt.Sprintf("(%d) %s", sect, ref)
				}
			}
			if sect, ok := entry.Sections["Luke"]; ok && sect > 0 {
				if ref, exists := lukeSections[sect]; exists {
					luke = fmt.Sprintf("(%d) %s", sect, ref)
				}
			}
			if sect, ok := entry.Sections["John"]; ok && sect > 0 {
				if ref, exists := johnSections[sect]; exists {
					john = fmt.Sprintf("(%d) %s", sect, ref)
				}
			}

			html += fmt.Sprintf(`
						<tr>
							<td>%s</td>
							<td>%s</td>
							<td>%s</td>
							<td>%s</td>
						</tr>`, matthew, mark, luke, john)
		}

		html += `
					</tbody>
				</table>
			</div>
		</div>`
	}

	html += buildGospelParallelTables(harmony, map[string]map[int]string{
		"Matthew": matthewSections,
		"Mark":    markSections,
		"Luke":    lukeSections,
		"John":    johnSections,
	})

	// Add statistics
	totalEntries := len(harmony)

	html += fmt.Sprintf(`
		<div style="margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
			<h4 style="margin-top: 0;">Statistics</h4>
			<p>Total Harmony Entries: <strong>%d</strong></p>
			<p>The Eusebian Canon system covers significant portions of the Gospel texts,
			facilitating comparison and study of parallel passages. Click on any canon section
			above to expand and view the specific verse references.</p>
		</div>
	</div>
	`, totalEntries)

	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(html))
}

func refChapter(ref string) int {
	if idx := strings.Index(ref, ":"); idx != -1 {
		if ch, err := strconv.Atoi(ref[:idx]); err == nil {
			return ch
		}
	}
	return 1
}

func parallelCell(gospel string, sect int, ref string) string {
	return fmt.Sprintf(`<span class="parallel-ref" onclick="loadChapterAndScroll('%s', %d)">(%d) %s</span>`,
		strings.ToLower(gospel), refChapter(ref), sect, ref)
}

func buildGospelParallelTables(harmony []HarmonyEntry, sectionMaps map[string]map[int]string) string {
	gospels := []string{"Matthew", "Mark", "Luke", "John"}

	var sb strings.Builder
	sb.WriteString(`
	<h2 style="text-align: center; margin: 50px 0 20px;">PARALLEL PASSAGES BY GOSPEL</h2>

	<p style="text-align: center; color: #666; margin-bottom: 20px;">
		Each table lists one Gospel in verse order. Find any verse in the first column
		to see its parallel passages in the other Gospels. Click any reference to open that chapter.
	</p>

	<style>
		.parallel-ref { color: #4a6da0; cursor: pointer; display: inline-block; }
		.parallel-ref:hover { text-decoration: underline; }
		.parallel-table td { white-space: nowrap; }
	</style>

	<div class="index-search-box" style="margin-bottom: 20px; padding: 12px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px;">
		<input type="text" id="parallelSearch" placeholder="Filter by verse (e.g. 5:3)" onkeyup="filterParallels()"
			style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;">
	</div>

	<script>
		function filterParallels() {
			const searchTerm = document.getElementById('parallelSearch').value.toLowerCase().trim();
			document.querySelectorAll('.parallel-section').forEach(section => {
				const rows = section.querySelectorAll('tbody tr');
				let visibleCount = 0;
				rows.forEach(row => {
					const text = row.cells[0].textContent.toLowerCase();
					if (!searchTerm || text.includes(searchTerm)) {
						row.style.display = '';
						visibleCount++;
					} else {
						row.style.display = 'none';
					}
				});
				if (visibleCount > 0 && searchTerm) {
					section.querySelector('.canon-content').classList.add('expanded');
					section.querySelector('.canon-header').classList.add('expanded');
				}
			});
		}
	</script>
	`)

	for _, anchor := range gospels {
		bySection := make(map[int][]HarmonyEntry)
		for _, e := range harmony {
			if s, ok := e.Sections[anchor]; ok && s > 0 {
				bySection[s] = append(bySection[s], e)
			}
		}

		var others []string
		for _, g := range gospels {
			if g != anchor {
				others = append(others, g)
			}
		}

		secs := append([]SectionEntry{}, sectionData[strings.ToLower(anchor)]...)
		sort.Slice(secs, func(i, j int) bool { return secs[i].Section < secs[j].Section })

		sb.WriteString(fmt.Sprintf(`
		<div class="canon-section parallel-section" id="parallels-%s">
			<div class="canon-header" onclick="toggleCanon('parallels-%s')">
				<span>%s (%d sections)</span>
				<span class="arrow">▶</span>
			</div>
			<div class="canon-content">
				<table class="canon-table parallel-table">
					<thead>
						<tr>
							<th width="25%%">%s</th>`,
			strings.ToLower(anchor), strings.ToLower(anchor), anchor, len(secs), anchor))

		for _, o := range others {
			sb.WriteString(fmt.Sprintf(`
							<th width="25%%">%s</th>`, o))
		}

		sb.WriteString(`
						</tr>
					</thead>
					<tbody>`)

		for _, se := range secs {
			cells := make(map[string][]string)
			seen := make(map[string]bool)
			for _, e := range bySection[se.Section] {
				for _, o := range others {
					if s, ok := e.Sections[o]; ok && s > 0 {
						if ref, found := sectionMaps[o][s]; found {
							key := fmt.Sprintf("%s|%d", o, s)
							if !seen[key] {
								seen[key] = true
								cells[o] = append(cells[o], parallelCell(o, s, ref))
							}
						}
					}
				}
			}

			sb.WriteString(fmt.Sprintf(`
						<tr>
							<td>%s</td>`, parallelCell(anchor, se.Section, se.Reference)))
			for _, o := range others {
				sb.WriteString(fmt.Sprintf(`
							<td>%s</td>`, strings.Join(cells[o], "<br>")))
			}
			sb.WriteString(`
						</tr>`)
		}

		sb.WriteString(`
					</tbody>
				</table>
			</div>
		</div>`)
	}

	return sb.String()
}