import { LegalLayout } from './LegalLayout'

export function CookiesPage() {
  return (
    <LegalLayout title="Politica de cookie-uri">
      <p>
        Folosim un singur cookie: rs_session — cookie esențial de autentificare (httpOnly),
        strict necesar funcționării contului; expiră după 30 de zile sau la deconectare. Pentru
        cookie-urile strict necesare nu este cerut consimțământul (Directiva ePrivacy).
        Preferința de temă (mod întunecat) se salvează local în browserul tău (localStorage) și
        nu ne este transmisă. Nu folosim cookie-uri de publicitate, tracking sau analytics. La
        plata prin Stripe, pagina de checkout aparține Stripe și folosește propriile cookie-uri
        (vezi politica Stripe).
      </p>
    </LegalLayout>
  )
}
