const fs = require('fs');
const path = require('path');
const https = require('https');

const books = [
  { name: 'matthew', id: '40' },
  { name: 'mark', id: '41' },
  { name: 'luke', id: '42' },
  { name: 'john', id: '43' },
  { name: 'acts', id: '44' },
  { name: 'romans', id: '45' },
  { name: '1corinthians', id: '46' },
  { name: '2corinthians', id: '47' },
  { name: 'galatians', id: '48' },
  { name: 'ephesians', id: '49' },
  { name: 'philippians', id: '50' },
  { name: 'colossians', id: '51' },
  { name: '1thessalonians', id: '52' },
  { name: '2thessalonians', id: '53' },
  { name: '1timothy', id: '54' },
  { name: '2timothy', id: '55' },
  { name: 'titus', id: '56' },
  { name: 'philemon', id: '57' },
  { name: 'hebrews', id: '58' },
  { name: 'james', id: '59' },
  { name: '1peter', id: '60' },
  { name: '2peter', id: '61' },
  { name: '1john', id: '62' },
  { name: '2john', id: '63' },
  { name: '3john', id: '64' },
  { name: 'jude', id: '65' },
  { name: 'revelation', id: '66' }
];

async function fetchBook(book) {
  return new Promise((resolve, reject) => {
    const url = `https://www.kingjamesbibleonline.org/text-${book.name}.php`;
    
    https.get(url, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        // Extract verses from HTML
        const verseRegex = /<span class="verse">.*?<\/span>/g;
        const verses = data.match(verseRegex) || [];
        
        let bookText = '';
        let currentChapter = 1;
        let currentVerse = 1;
        
        verses.forEach((verseHtml) => {
          // Extract verse text
          const textMatch = verseHtml.match(/>([^<]+)</);
          if (textMatch) {
            const verseText = textMatch[1].trim();
            bookText += `${currentChapter}:${currentVerse} ${verseText}\n`;
            currentVerse++;
          }
        });
        
        resolve(bookText);
      });
    }).on('error', reject);
  });
}

async function main() {
  for (const book of books) {
    try {
      console.log(`Fetching ${book.name}...`);
      const content = await fetchBook(book);
      
      const filePath = path.join(__dirname, '..', 'texts', 'english', 'kjv', book.name, `${book.name}.txt`);
      fs.writeFileSync(filePath, content);
      
      console.log(`Saved ${book.name}`);
    } catch (error) {
      console.error(`Error fetching ${book.name}:`, error.message);
    }
  }
}

main();