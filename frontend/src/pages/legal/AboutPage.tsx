import { CONTACT_EMAIL, SITE_NAME } from '@/lib/site'
import { LegalLayout, LegalSection } from './LegalLayout'

/** /despre — referenced by the scraper's User-Agent. Explains the good-faith,
 *  link-back aggregation model and how a source site can ask to be excluded. */
export function AboutPage() {
  return (
    <LegalLayout title={`Despre ${SITE_NAME}`}>
      <LegalSection title="Ce facem">
        <p>
          {SITE_NAME} este un agregator de anunțuri de închiriere din România. Strângem
          într-un singur loc anunțuri publicate pe site-uri terțe (Storia, OLX, Imobiliare,
          Publi24 și altele) și le facem ușor de căutat, cu filtre pe care site-urile sursă
          nu le oferă. Nu suntem agenție imobiliară și nu intermediem tranzacții.
        </p>
      </LegalSection>

      <LegalSection title="Cum tratăm sursele">
        <p>
          Indexăm doar paginile publice de listări și fiecare anunț trimite utilizatorul
          înapoi la pagina originală de pe site-ul sursă — le trimitem trafic, nu îl preluăm.
          Accesăm politicos: respectăm directivele din <code>robots.txt</code>, folosim
          întârzieri între cereri, limităm numărul de pagini și nu reîncercăm cererile
          eșuate. Robotul nostru se identifică prin User-Agent „KiraBot”.
        </p>
        <p>
          Nu stocăm date de contact (numere de telefon, adrese de email) din anunțuri —
          acestea sunt eliminate automat; contactul rămâne disponibil pe anunțul original.
        </p>
      </LegalSection>

      <LegalSection title="Ești un site sursă și vrei să fii exclus?">
        <p>
          Respectăm dorința oricărei platforme. Dacă reprezinți un site sursă și nu dorești
          să fii inclus, scrie-ne la {CONTACT_EMAIL} și te excludem prompt.
        </p>
      </LegalSection>

      <LegalSection title="Contact">
        <p>
          Întrebări, sugestii sau probleme: {CONTACT_EMAIL}. Citim fiecare mesaj.
        </p>
      </LegalSection>
    </LegalLayout>
  )
}
