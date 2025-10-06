export interface ParsedTransaction {
  date: string;
  description: string;
  amount: number;
}

export function parseCSV(csvContent: string): ParsedTransaction[] {
  const lines = csvContent.trim().split('\n');
  if (lines.length === 0) return [];

  const headers = lines[0].toLowerCase().split(',').map(h => h.trim());

  const dateIndex = headers.findIndex(h => h.includes('date'));
  const descIndex = headers.findIndex(h => h.includes('description') || h.includes('narration') || h.includes('details'));
  const amountIndex = headers.findIndex(h => h.includes('amount') || h.includes('debit') || h.includes('withdrawal'));

  if (dateIndex === -1 || descIndex === -1 || amountIndex === -1) {
    throw new Error('CSV must contain date, description, and amount columns');
  }

  const transactions: ParsedTransaction[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const values = line.split(',').map(v => v.trim());

    const dateStr = values[dateIndex];
    const description = values[descIndex];
    const amountStr = values[amountIndex].replace(/[₹,]/g, '');

    const amount = parseFloat(amountStr);

    if (dateStr && description && !isNaN(amount) && amount > 0) {
      transactions.push({
        date: parseDate(dateStr),
        description,
        amount,
      });
    }
  }

  return transactions;
}

function parseDate(dateStr: string): string {
  const formats = [
    /(\d{4})-(\d{2})-(\d{2})/,
    /(\d{2})\/(\d{2})\/(\d{4})/,
    /(\d{2})-(\d{2})-(\d{4})/,
  ];

  for (const format of formats) {
    const match = dateStr.match(format);
    if (match) {
      if (match[1].length === 4) {
        return `${match[1]}-${match[2]}-${match[3]}`;
      } else {
        return `${match[3]}-${match[2]}-${match[1]}`;
      }
    }
  }

  const today = new Date();
  return today.toISOString().split('T')[0];
}
