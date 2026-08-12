export function fmtCurrency(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function fmtMultiple(value) {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(2)}x`;
}

export function fmtPercent(value) {
  if (value === null || value === undefined) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}

export function fmtDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
  });
}
