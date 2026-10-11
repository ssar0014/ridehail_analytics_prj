const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
const int = new Intl.NumberFormat('en-US')
const dateTime = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' })

export const fmtMoney = (v: string | number | null) => (v == null ? '—' : usd.format(Number(v)))
export const fmtInt = (v: number | null) => (v == null ? '—' : int.format(v))
export const fmtDateTime = (v: string | null) => (v == null ? '—' : dateTime.format(new Date(v)))
