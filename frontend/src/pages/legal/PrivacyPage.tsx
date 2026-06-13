import { CONTACT_EMAIL, OPERATOR, SITE_NAME } from '@/lib/site'
import { LegalLayout, LegalList, LegalSection } from './LegalLayout'

export function PrivacyPage() {
  return (
    <LegalLayout title="Politica de confidențialitate">
      <LegalSection title="Pe scurt">
        <p>
          {SITE_NAME} este o aplicație care rulează <strong>local, pe calculatorul tău</strong>.
          Nu există un cont, un server central sau o bază de date a noastră care să-ți colecteze
          datele. Tot ce vezi și salvezi rămâne pe dispozitivul tău. Nu folosim analytics,
          tracking sau publicitate.
        </p>
      </LegalSection>

      <LegalSection title="Ce date sunt prelucrate și unde">
        <LegalList
          items={[
            <>
              Anunțurile: aplicația descarcă anunțuri publice de pe site-uri terțe și le păstrează
              într-o bază de date <strong>locală</strong>, pe calculatorul tău. Eliminăm automat
              datele de contact (telefon, email) din textul anunțurilor; contactul rămâne pe
              anunțul original, la care fiecare card te redirecționează.
            </>,
            <>
              Preferințele tale (temă, anunțuri salvate la favorite, alegerea privind cookie-ul) se
              salvează în <strong>localStorage</strong>, în browserul tău. Nu ne sunt transmise.
            </>,
            <>
              Adresa pentru calculul distanței: dacă introduci o adresă/un reper, acel text este
              trimis către serviciul public de geocodare OpenStreetMap (Nominatim) ca să obținem
              coordonatele. Atât.
            </>,
          ]}
        />
      </LegalSection>

      <LegalSection title="Cui se transmit date">
        <LegalList
          items={[
            <>
              OpenStreetMap Foundation (Nominatim) — doar textul adresei introduse de tine pentru
              calculul distanței, fără alte date personale.
            </>,
            <>
              Site-urile sursă — când apeși pe un anunț, ești redirecționat către pagina lor
              (se aplică politicile lor).
            </>,
            <>
              În rest, nimic nu pleacă de pe calculatorul tău. Nu vindem și nu transmitem date
              nimănui.
            </>,
          ]}
        />
      </LegalSection>

      <LegalSection title="Ștergerea datelor">
        <p>
          Fiind o aplicație locală, controlezi complet datele: poți șterge baza de date locală
          (fișierul din folderul aplicației) și preferințele din browser (butonul din pagina de
          cookie-uri) oricând.
        </p>
      </LegalSection>

      <LegalSection title="Contact">
        <p>
          {SITE_NAME} este un proiect personal/educațional realizat de {OPERATOR}. Pentru întrebări:{' '}
          {CONTACT_EMAIL}. Poți depune o plângere și la Autoritatea Națională de Supraveghere a
          Prelucrării Datelor cu Caracter Personal (ANSPDCP — dataprotection.ro).
        </p>
      </LegalSection>
    </LegalLayout>
  )
}
