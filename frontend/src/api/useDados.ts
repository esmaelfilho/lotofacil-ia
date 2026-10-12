import { useCallback, useEffect, useState } from 'react'

export interface Dados<T> {
  dados: T | null
  erro: string | null
  carregando: boolean
  recarregar: () => void
}

/**
 * Carrega dados da API e recarrega quando `dependencias` mudam.
 * Se uma resposta antiga chegar depois de uma nova, ela é descartada.
 */
export function useDados<T>(carregar: () => Promise<T>, dependencias: unknown[]): Dados<T> {
  const [dados, setDados] = useState<T | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [versao, setVersao] = useState(0)

  const carregarMemo = useCallback(carregar, dependencias)

  useEffect(() => {
    let atual = true
    setCarregando(true)
    setErro(null)
    carregarMemo()
      .then((resultado) => {
        if (atual) setDados(resultado)
      })
      .catch((e: unknown) => {
        if (atual) setErro(e instanceof Error ? e.message : String(e))
      })
      .finally(() => {
        if (atual) setCarregando(false)
      })
    return () => {
      atual = false
    }
  }, [carregarMemo, versao])

  const recarregar = useCallback(() => setVersao((v) => v + 1), [])
  return { dados, erro, carregando, recarregar }
}
