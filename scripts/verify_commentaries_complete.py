#!/usr/bin/env python3
"""
Verify completeness of all commentary files in the project.
Checks Chrysostom on Matthew & John, and Cyril on Luke.
"""

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

def check_chrysostom_matthew():
    """Check Chrysostom's 90 homilies on Matthew"""
    print("\n" + "="*60)
    print("CHRYSOSTOM ON MATTHEW (90 homilies expected)")
    print("="*60)
    
    issues = []
    homilies_found = {}
    
    # Check for XML source file
    xml_file = Path("texts/commentaries/chrysostom/matthew/chrysostom_matthew_homilies.xml")
    if xml_file.exists():
        print(f"✓ XML source file exists: {xml_file}")
        # Try to parse and count homilies in XML
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Count div2 elements with type="Homily"
            homily_count = content.count('type="Homily"')
            print(f"  Found {homily_count} homilies in XML")
        except Exception as e:
            print(f"  Warning: Could not parse XML: {e}")
    else:
        print(f"✗ XML source file missing")
        issues.append("Matthew XML source missing")
    
    # Check individual homily files
    homily_dir = Path("texts/commentaries/chrysostom/matthew")
    for i in range(1, 91):
        roman = int_to_roman(i)
        # Check for various file patterns
        patterns = [
            f"homily_{i:02d}.txt",
            f"homily_{i}.txt",
            f"homily_{roman}.txt",
            f"chrysostom_matthew_homily_{i:02d}.html",
            f"homily{i:02d}.html"
        ]
        
        found = False
        for pattern in patterns:
            file_path = homily_dir / pattern
            if file_path.exists():
                homilies_found[i] = file_path.name
                found = True
                break
        
        if not found:
            # Don't report as issue since we have XML
            pass
    
    # Check JSON data files
    json_files = {
        "homily_coverage.json": "Homily coverage data",
        "matthew_verse_to_homilies.json": "Verse-to-homily mapping",
        "all_footnotes.json": "Footnotes data",
        "matthew_verse_to_homily_clean.json": "Clean verse mapping"
    }
    
    for json_file, description in json_files.items():
        file_path = homily_dir / json_file
        if file_path.exists():
            print(f"✓ {description}: {json_file}")
            if "coverage" in json_file:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    print(f"  Contains {len(data)} homily entries")
                except:
                    pass
        else:
            print(f"✗ {description} missing: {json_file}")
            issues.append(f"Matthew {json_file} missing")
    
    if homilies_found:
        print(f"\nIndividual homily files found: {len(homilies_found)}/90")
    
    return issues

def check_chrysostom_john():
    """Check Chrysostom's 88 homilies on John"""
    print("\n" + "="*60)
    print("CHRYSOSTOM ON JOHN (88 homilies expected)")
    print("="*60)
    
    issues = []
    homilies_found = {}
    
    # Check for XML source file
    xml_file = Path("texts/commentaries/chrysostom/john/chrysostom_john_homilies.xml")
    if xml_file.exists():
        print(f"✓ XML source file exists: {xml_file}")
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            homily_count = content.count('type="Homily"')
            print(f"  Found {homily_count} homilies in XML")
        except Exception as e:
            print(f"  Warning: Could not parse XML: {e}")
    else:
        print(f"✗ XML source file missing")
        issues.append("John XML source missing")
    
    # Check JSON data files
    john_dir = Path("texts/commentaries/chrysostom/john")
    json_files = {
        "homily_coverage.json": "Homily coverage data",
        "john_verse_to_homilies.json": "Verse-to-homily mapping",
        "all_footnotes.json": "Footnotes data",
        "footnotes.json": "Footnotes data"
    }
    
    for json_file, description in json_files.items():
        file_path = john_dir / json_file
        if file_path.exists():
            print(f"✓ {description}: {json_file}")
            if "coverage" in json_file:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    print(f"  Contains {len(data)} homily entries")
                except:
                    pass
        else:
            print(f"✗ {description} missing: {json_file}")
            issues.append(f"John {json_file} missing")
    
    return issues

def check_cyril_luke():
    """Check Cyril's 156 sermons on Luke"""
    print("\n" + "="*60)
    print("CYRIL OF ALEXANDRIA ON LUKE (156 sermons expected)")
    print("="*60)
    
    issues = []
    sermons_found = {}
    
    luke_dir = Path("texts/commentaries/cyril/luke")
    
    # Check for HTML source files
    html_files = list(luke_dir.glob("*.htm")) + list(luke_dir.glob("*.html"))
    if html_files:
        print(f"✓ Found {len(html_files)} HTML source files")
        for f in sorted(html_files)[:5]:  # Show first 5
            print(f"  - {f.name}")
        if len(html_files) > 5:
            print(f"  ... and {len(html_files)-5} more")
    else:
        print(f"✗ No HTML source files found")
        issues.append("Luke HTML sources missing")
    
    # Check for individual sermon files
    for i in range(1, 157):
        patterns = [
            f"sermon_{i:03d}.txt",
            f"sermon_{i:02d}.txt",
            f"sermon_{i}.txt",
            f"cyril_luke_sermon_{i:03d}.html"
        ]
        
        found = False
        for pattern in patterns:
            file_path = luke_dir / pattern
            if file_path.exists():
                sermons_found[i] = file_path.name
                found = True
                break
    
    # Check JSON data files
    json_files = {
        "homily_coverage.json": "Sermon coverage data",
        "luke_verse_to_sermons.json": "Verse-to-sermon mapping",
        "cyril_luke_sermons.json": "Sermons data"
    }
    
    for json_file, description in json_files.items():
        file_path = luke_dir / json_file
        if file_path.exists():
            print(f"✓ {description}: {json_file}")
            if "coverage" in json_file:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    print(f"  Contains {len(data)} sermon entries")
                except:
                    pass
        else:
            print(f"✗ {description} missing: {json_file}")
            issues.append(f"Luke {json_file} missing")
    
    if sermons_found:
        print(f"\nIndividual sermon files found: {len(sermons_found)}/156")
    
    return issues

def check_unified_json():
    """Check unified JSON files"""
    print("\n" + "="*60)
    print("UNIFIED COMMENTARY JSON FILES")
    print("="*60)
    
    issues = []
    unified_dir = Path("texts/commentaries/unified_json")
    
    if not unified_dir.exists():
        print(f"✗ Unified JSON directory missing: {unified_dir}")
        issues.append("Unified JSON directory missing")
        return issues
    
    expected_files = {
        "chrysostom_matthew.json": "Chrysostom on Matthew unified data",
        "chrysostom_john.json": "Chrysostom on John unified data",
        "cyril_luke.json": "Cyril on Luke unified data"
    }
    
    for json_file, description in expected_files.items():
        file_path = unified_dir / json_file
        if file_path.exists():
            print(f"✓ {description}")
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Check structure
                if "commentary" in data:
                    commentary = data["commentary"]
                    print(f"  Author: {commentary.get('author', 'Unknown')}")
                    print(f"  Book: {commentary.get('book', 'Unknown')}")
                    
                    if "homilies" in commentary:
                        print(f"  Homilies: {len(commentary['homilies'])}")
                    elif "sermons" in commentary:
                        print(f"  Sermons: {len(commentary['sermons'])}")
                    
                    if "coverage" in commentary:
                        print(f"  Coverage entries: {len(commentary['coverage'])}")
            except Exception as e:
                print(f"  Warning: Could not parse JSON: {e}")
        else:
            print(f"✗ {description} missing")
            issues.append(f"Unified {json_file} missing")
    
    return issues

def int_to_roman(num):
    """Convert integer to Roman numeral"""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

def main():
    print("="*60)
    print("COMMENTARY COMPLETENESS VERIFICATION")
    print("="*60)
    print("\nChecking all commentary files in the project...")
    
    all_issues = []
    
    # Check each commentary
    issues = check_chrysostom_matthew()
    all_issues.extend(issues)
    
    issues = check_chrysostom_john()
    all_issues.extend(issues)
    
    issues = check_cyril_luke()
    all_issues.extend(issues)
    
    issues = check_unified_json()
    all_issues.extend(issues)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if all_issues:
        print(f"\n⚠️ Issues found ({len(all_issues)}):")
        for issue in all_issues:
            print(f"  • {issue}")
    else:
        print("\n✅ All commentary files appear to be complete!")
    
    # Generate report
    report = {
        "commentaries": {
            "chrysostom_matthew": {
                "expected_homilies": 90,
                "has_xml": Path("texts/commentaries/chrysostom/matthew/chrysostom_matthew_homilies.xml").exists(),
                "has_coverage_json": Path("texts/commentaries/chrysostom/matthew/homily_coverage.json").exists(),
                "has_footnotes": Path("texts/commentaries/chrysostom/matthew/all_footnotes.json").exists()
            },
            "chrysostom_john": {
                "expected_homilies": 88,
                "has_xml": Path("texts/commentaries/chrysostom/john/chrysostom_john_homilies.xml").exists(),
                "has_coverage_json": Path("texts/commentaries/chrysostom/john/homily_coverage.json").exists(),
                "has_footnotes": Path("texts/commentaries/chrysostom/john/all_footnotes.json").exists()
            },
            "cyril_luke": {
                "expected_sermons": 156,
                "has_html": len(list(Path("texts/commentaries/cyril/luke").glob("*.htm*"))) > 0,
                "has_coverage_json": Path("texts/commentaries/cyril/luke/homily_coverage.json").exists(),
                "has_sermons_json": Path("texts/commentaries/cyril/luke/cyril_luke_sermons.json").exists()
            }
        },
        "issues": all_issues
    }
    
    report_file = Path("texts/reference/commentary_verification_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    main()