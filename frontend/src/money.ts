/** Shows an API money string as is ("0.50" stays "0.50") — the UI never does money arithmetic. */
export function formatMoney(amount: string, currency: string): string {
  return `${amount} ${currency}`;
}
