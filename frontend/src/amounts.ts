// Amount entry for invoice review. Reviewers read German-format invoices
// (1.234,56) but may also type 1234.56, so both are accepted — and anything
// that could mean two different numbers is refused rather than guessed.

const PATTERNS: [RegExp, (raw: string) => string][] = [
  // 1234 | 1234,5 | 1234,56
  [/^\d+(,\d{1,2})?$/, (raw) => raw.replace(',', '.')],
  // 1234.5 | 1234.56
  [/^\d+\.\d{1,2}$/, (raw) => raw],
  // 1.234,56 | 1.234.567 (German thousands; a single group needs decimals)
  [
    /^\d{1,3}(\.\d{3})+,\d{1,2}$|^\d{1,3}(\.\d{3}){2,}$/,
    (raw) => raw.replaceAll('.', '').replace(',', '.'),
  ],
  // 1,234.56 (English thousands)
  [/^\d{1,3}(,\d{3})+\.\d{1,2}$/, (raw) => raw.replaceAll(',', '')],
];

/**
 * Parses a typed amount, or returns null when it is not a number or is
 * ambiguous: "1.234" and "1,234" could each be read as 1234 or 1.234.
 */
export function parseAmount(input: string): number | null {
  const cleaned = input.replace(/[\s€]/g, '');
  const negative = cleaned.startsWith('-');
  const digits = negative ? cleaned.slice(1) : cleaned;
  for (const [pattern, normalise] of PATTERNS) {
    if (pattern.test(digits)) {
      const value = Number(normalise(digits));
      return negative ? -value : value;
    }
  }
  return null;
}
