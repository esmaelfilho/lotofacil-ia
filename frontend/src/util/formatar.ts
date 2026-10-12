/** Dezena sempre com dois dígitos: 1 -> "01". */
export function formatarDezena(dezena: number): string {
  return String(dezena).padStart(2, '0')
}

/** "2026-10-10" -> "10/10/2026", sem passar por Date (evita erro de fuso horário). */
export function formatarData(iso: string): string {
  const [ano, mes, dia] = iso.slice(0, 10).split('-')
  return `${dia}/${mes}/${ano}`
}

/** "2026-10-12T20:59:00+00:00" -> "12/10/2026 17:59" no fuso do navegador. */
export function formatarDataHora(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

export function formatarNumero(valor: number): string {
  return valor.toLocaleString('pt-BR')
}
