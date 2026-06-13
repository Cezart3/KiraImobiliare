import { CONTACT_EMAIL, SITE_NAME } from '@/lib/site'
import { LegalLayout, LegalSection } from './LegalLayout'

/** /despre — referenced by the scraper's User-Agent. Explains the good-faith,
 *  link-back aggregation model and how a source site can ask to be excluded. */
export function AboutPage() {
  return (
    <LegalLayout title={`Despre ${SITE_NAME}`}>
      <LegalSection title="Ce este">
        <p>
          {SITE_NAME} este un instrument gratuit care rulează local pe calculatorul
          tău. Strânge într-un singur loc anunțuri de închiriere publicate pe site-uri terțe
          (Storia, OLX, Imobiliare, Publi24 și altele) și le face ușor de căutat, cu filtre pe
          care site-urile sursă nu le oferă. Nu este o agenție imobiliară și nu intermediază
          tranzacții.
        </p>
      </LegalSection>

      <LegalSection title="Cum tratează sursele">
        <p>
          Aplicația accesează doar paginile publice de listări și fiecare anunț trimite
          utilizatorul înapoi la pagina originală de pe site-ul sursă. Accesează politicos:
          respectă directivele din <code>robots.txt</code>, folosește întârzieri între cereri,
          limitează numărul de pagini și nu reîncearcă cererile eșuate. Robotul se identifică
          prin User-Agent „KiraBot”. Nu stochează date de contact (telefon, email) din anunțuri.
        </p>
        <p>
          Fiind un instrument local, fiecare utilizator alege ce surse rulează și este responsabil
          de respectarea Termenilor fiecărui site. Sursele se pot dezactiva ușor din configurație.
        </p>
      </LegalSection>

      <LegalSection title="De ce Kira?">
        <p>
          Kira e cățelușa mea 🐶 — partenera mea de frustrare în lunile în care căutam o chirie
          și jonglam cu 6 site-uri deschise în paralel. {SITE_NAME} rezolvă fix bătaia de cap prin
          care am trecut împreună, așa că poartă numele ei.
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
